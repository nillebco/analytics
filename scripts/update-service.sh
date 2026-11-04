#!/bin/bash
# Keep the deployed analytics service patched.
#
#   scripts/update-service.sh            upgrade pins, audit, smoke test, then rebuild + redeploy
#                                        when the pins or the python base image changed
#   scripts/update-service.sh --deploy   build + deploy the current version as is
#
# The server runs the image through a podman Quadlet (~/.config/containers/systemd/analytics.container).
# Required env: ANALYTICS_SSH (user@host), ANALYTICS_SSH_KEY (private key path).
set -euo pipefail

: "${ANALYTICS_SSH:?set ANALYTICS_SSH=user@host}"
: "${ANALYTICS_SSH_KEY:?set ANALYTICS_SSH_KEY=/path/to/key}"
PYTHON_VERSION=3.12
BASE_IMAGE=python:$PYTHON_VERSION-slim
PORT=8018
QUADLET='~/.config/containers/systemd/analytics.container'
REPO=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d)
trap 'pkill -f "uvicorn api.app:app --port 17999" 2>/dev/null || true; rm -rf "$WORK"' EXIT
cd "$REPO"

log() { echo "[$(date '+%F %T')] $*"; }
remote() { ssh -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=20 -i "$ANALYTICS_SSH_KEY" "$ANALYTICS_SSH" "$@"; }
version() { sed -n 's/^__version__ = "\(.*\)"/\1/p' api/version.py; }

ensure_docker() {
    docker info >/dev/null 2>&1 && return
    log "starting colima"
    colima start >/dev/null
}

upgrade_pins() {
    uv pip compile -q --python-version $PYTHON_VERSION --upgrade requirements.in -o requirements.txt
    uv pip compile -q --python-version $PYTHON_VERSION --upgrade requirements.in dev-requirements.in -o dev-requirements.txt
}

audit() {
    # plain `uvx pip-audit` builds a venv with the newest python, whose ensurepip can crash
    uvx --python $PYTHON_VERSION pip-audit -r requirements.txt --no-deps --disable-pip
}

# no test suite yet: boot the app on in-memory SQLite (copy without .env) and hit each route
smoke_test() {
    uv venv -q --python $PYTHON_VERSION "$WORK/venv"
    VIRTUAL_ENV="$WORK/venv" uv pip sync -q requirements.txt
    mkdir "$WORK/app" && cp -R api static "$WORK/app/"
    (cd "$WORK/app" && env -u DATABASE_URL "$WORK/venv/bin/uvicorn" api.app:app --port 17999 >"$WORK/uvicorn.log" 2>&1 &)
    local base=http://127.0.0.1:17999 pid i
    for i in $(seq 20); do curl -fsS "$base/api/v1" >/dev/null 2>&1 && break; sleep 0.5; done
    pid=$(cd "$WORK/app" && "$WORK/venv/bin/python" -c "from api.constants import DEFAULT_PROPERTY_ID; print(DEFAULT_PROPERTY_ID)" 2>/dev/null | tail -1)
    curl -fsS "$base/api/v1" | grep -q '"status":"ok"'
    curl -fsS "$base/simple.js?pid=$pid" | grep -q 'document.referrer'
    curl -fsS -o /dev/null -H 'x-forwarded-for: 127.0.0.1' "$base/"
    curl -fsS -X POST "$base/api/v1/analytics/collect?property_id=$pid" \
        -H 'x-forwarded-for: 127.0.0.1' -H 'user-agent: Mozilla/5.0 (smoke test)' -H 'content-type: application/json' \
        -d '{"page_url":"https://example.com/","referrer":"https://example.org/"}' | grep -q success \
        || { tail -40 "$WORK/uvicorn.log"; return 1; }
    log "smoke test passed"
}

base_digest() {
    docker pull -q "$BASE_IMAGE" >/dev/null
    docker image inspect "$BASE_IMAGE" --format '{{index .RepoDigests 0}}'
}

deployed_image() { remote "sed -n 's/^Image=//p' $QUADLET"; }

deployed_base() {
    remote "podman image inspect $(deployed_image) --format '{{index .Labels \"org.nillebco.base\"}}'" 2>/dev/null || true
}

bump_patch() {
    local v next
    v=$(version)
    next="${v%.*}.$(( ${v##*.} + 1 ))"
    sed -i.bak "s/__version__ = \"$v\"/__version__ = \"$next\"/" api/version.py && rm api/version.py.bak
}

build() {
    local v=$1 base=$2
    docker build -q --pull --no-cache --build-arg PORT=$PORT \
        --label "org.opencontainers.image.ref.name=analytics:$v" --label "org.nillebco.base=$base" \
        -t "nillebco/analytics:$v" . >/dev/null
    docker save "nillebco/analytics:$v" | gzip >"$WORK/analytics.tar.gz"
    log "built nillebco/analytics:$v"
}

deploy() {
    local v=$1 image=docker.io/nillebco/analytics:$1 previous
    previous=$(deployed_image)
    scp -q -o IdentitiesOnly=yes -o BatchMode=yes -i "$ANALYTICS_SSH_KEY" "$WORK/analytics.tar.gz" "$ANALYTICS_SSH:apps/analytics.tar.gz"
    remote "set -e
        gunzip -c ~/apps/analytics.tar.gz | podman load -q
        podman logs analytics > ~/apps/analytics-${previous##*:}-pre.log 2>&1 || true
        cp $QUADLET $QUADLET.previous
        sed -i 's#^Image=.*#Image=$image#' $QUADLET
        systemctl --user daemon-reload && systemctl --user restart analytics"
    if remote "for i in \$(seq 30); do curl -fsS localhost:$PORT/api/v1 2>/dev/null | grep -q '\"version\":\"$v\"' && exit 0; sleep 1; done; exit 1"; then
        log "deployed $image (was $previous)"
        # keep the running image and the previous one for rollback
        remote "podman images --format '{{.Repository}}:{{.Tag}}' docker.io/nillebco/analytics | grep -vxF -e $image -e $previous | xargs -r podman rmi" >/dev/null 2>&1 || true
    else
        log "health check failed, rolling back to $previous"
        remote "podman logs --tail 30 analytics; cp $QUADLET.previous $QUADLET; systemctl --user daemon-reload && systemctl --user restart analytics"
        return 1
    fi
}

publish() {
    git add requirements.txt dev-requirements.txt api/version.py
    git commit -q -m "chore(deps): scheduled update to $1"
    git push -q origin HEAD
    log "pushed $1"
}

main() {
    ensure_docker
    if [[ "${1:-}" == "--deploy" ]]; then
        smoke_test
        build "$(version)" "$(base_digest)"
        deploy "$(version)"
        return
    fi

    [[ "$(git rev-parse --abbrev-ref HEAD)" == main ]] || { log "not on main"; return 1; }
    git diff --quiet HEAD -- requirements.in requirements.txt dev-requirements.txt api/version.py \
        || { log "uncommitted changes to the pinned files, refusing to run"; return 1; }
    git pull -q --no-rebase --ff-only

    upgrade_pins
    audit
    local pins_changed=false base deployed
    git diff --quiet -- requirements.txt || pins_changed=true
    base=$(base_digest)
    deployed=$(deployed_base)
    if [[ $pins_changed == false && "$base" == "$deployed" ]]; then
        git checkout -- dev-requirements.txt
        log "up to date ($(version), $base)"
        return
    fi
    log "pins changed: $pins_changed; base image: ${deployed:-unknown} -> $base"

    smoke_test
    bump_patch
    build "$(version)" "$base"
    deploy "$(version)" || { git checkout -- requirements.txt dev-requirements.txt api/version.py; return 1; }
    publish "$(version)"
}

main "$@"
