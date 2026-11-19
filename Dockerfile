# syntax=docker/dockerfile:1
FROM python:3.12-slim as builder

ARG PORT 17581

WORKDIR /app

RUN apt-get clean && \
    apt-get -y update && \
    apt-get install -y --no-install-recommends \
    cmake \
    build-essential && \
    apt-get clean && \
    addgroup --system appuser && \
    adduser --system appuser --disabled-login && \
    chown -R appuser:appuser /app && \
    pip install --upgrade pip && \
    pip install uv

COPY api/ ./api/
COPY requirements.txt ./
COPY static/ ./static/

# Country lookup stays on the server: DB-IP's free country database (CC BY 4.0),
# this month's edition or, early in the month, last month's.
RUN mkdir -p /app/geo && python - <<'PY'
import datetime, gzip, urllib.request
today = datetime.date.today()
last_month = (today.replace(day=1) - datetime.timedelta(days=1))
for month in (today, last_month):
    url = f"https://download.db-ip.com/free/dbip-country-lite-{month:%Y-%m}.mmdb.gz"
    try:
        # DB-IP answers 403 to the default Python-urllib user agent
        request = urllib.request.Request(url, headers={"User-Agent": "nillebco-analytics-build"})
        data = urllib.request.urlopen(request, timeout=60).read()
    except Exception as error:
        print(f"{url}: {error}")
        continue
    open("/app/geo/dbip-country-lite.mmdb", "wb").write(gzip.decompress(data))
    print(f"country database: {url}")
    break
else:
    raise SystemExit("no DB-IP country database could be downloaded")
PY

USER appuser

RUN cd /app && \
    uv venv --no-cache-dir && \
    . .venv/bin/activate && \
    uv pip install --no-cache -r requirements.txt && \
    mkdir data secrets

FROM python:3.12-slim as runner
COPY --from=builder /app/ /app/
RUN apt-get -y update && \
    apt-get install -y --no-install-recommends \
    apt-get clean && \
    addgroup --system appuser && \
    adduser --system appuser --disabled-login \
    chown -R appuser:appuser /app/data /app/secrets && \
    --ingroup appuser --no-create-home \
    --home /nonexistent --gecos "nonroot user" --shell /bin/false || true

USER appuser

WORKDIR /app
VOLUME [ "/app/data", "/app/secrets" ]
ENV NUMBA_CACHE_DIR=/app/data
ENV PORT=$PORT
EXPOSE $PORT
CMD ["/bin/sh", "-c", "echo $DATABASE_URL && .venv/bin/uvicorn api.app:app --host 0.0.0.0 --port $PORT"]
