# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------------------
# Multi-stage Dockerfile for the django-db-mailer demo project.
#
# Stages:
#   builder      — install deps into an isolated venv at /opt/venv
#   base         — slim runtime, copies venv from builder, non-root user
#   development  — base + dev/test/demo extras + reload-friendly defaults
#   production   — base + collectstatic, gunicorn entrypoint
#
# Build:
#   docker build --target development -t dbmail-demo:dev .
#   docker build --target production  -t dbmail-demo:3.0 .
# ---------------------------------------------------------------------------

ARG PYTHON_VERSION=3.12

# ===========================================================================
# 1) builder stage — venv with all runtime + demo deps
# ===========================================================================
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        libpq-dev \
        gettext && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy only the metadata first so the dep layer caches across source edits.
COPY pyproject.toml MANIFEST.in README.md LICENSE ./
COPY dbmail/__init__.py ./dbmail/__init__.py

RUN pip install --upgrade pip wheel && \
    pip install -e ".[demo]"

# ===========================================================================
# 2) base — slim runtime image
# ===========================================================================
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=demo.settings

# Runtime deps only (no compilers).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        libffi8 \
        libssl3 \
        gettext \
        curl \
        tini && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    groupadd -g 1000 django && \
    useradd -u 1000 -g django -s /bin/sh -m django

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=django:django . .

RUN mkdir -p /app/static /app/media && chown -R django:django /app

USER django

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/admin/login/ || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]

# ===========================================================================
# 3) development — reload server, dev/test extras
# ===========================================================================
FROM base AS development

USER root

# Add dev/test extras on top of the demo install.
RUN pip install -e ".[dev,test,demo,celery,apns]"

USER django

ENV DJANGO_DEBUG=1

# Default command runs the migrate+runserver pipeline; compose can override.
CMD ["sh", "-c", \
     "python demo/manage.py migrate --noinput && \
      python demo/manage.py runserver 0.0.0.0:8000"]

# ===========================================================================
# 4) production — collectstatic + gunicorn
# ===========================================================================
FROM base AS production

ENV DJANGO_DEBUG=0

# collectstatic must run as a writable user.
USER root
RUN cd demo && python manage.py collectstatic --noinput && \
    chown -R django:django /app/static
USER django

CMD ["gunicorn", "demo.wsgi:application", \
     "--chdir", "demo", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
