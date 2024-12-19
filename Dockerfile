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
