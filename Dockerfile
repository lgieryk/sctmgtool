FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install '.[web]' gunicorn

FROM python:3.13-slim

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    SCTMGTOOL_WEB_CACHE_DIR=/data/cache

RUN groupadd --system --gid 10001 sctmgtool \
    && useradd --system --uid 10001 --gid sctmgtool \
       --home-dir /nonexistent sctmgtool \
    && mkdir -p /data/cache /tmp/matplotlib \
    && chown -R sctmgtool:sctmgtool /data /tmp/matplotlib

COPY --from=builder /opt/venv /opt/venv

USER sctmgtool

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=1", "--threads=2", "--timeout=120", "--access-logfile=-", "--error-logfile=-", "sctmgtool.web.app:create_flask_app()"]
