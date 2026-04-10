# ═══════════════════════════════════════════════════════════════
#  Stage 1 — builder
#  Install deps in an isolated layer so they get cached properly.
#  If requirements.txt hasn't changed, Docker reuses this layer —
#  the most expensive step is skipped on every subsequent build.
# ═══════════════════════════════════════════════════════════════
FROM python:3.11-slim AS builder

WORKDIR /install

# Copy ONLY the requirements first (layer caching trick).
# Docker rebuilds from here only when requirements.txt changes.
COPY app/requirements.txt .

RUN pip install --upgrade pip \
    && pip install --prefix=/install/deps --no-cache-dir -r requirements.txt


# ═══════════════════════════════════════════════════════════════
#  Stage 2 — runtime
#  Starts from the same slim base but copies only the installed
#  packages + app code. No pip, no build tools, smaller image.
# ═══════════════════════════════════════════════════════════════
FROM python:3.11-slim AS runtime

# Create a non-root user — running as root inside a container is
# a security risk even though it's isolated.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Pull the compiled packages from the builder stage
COPY --from=builder /install/deps /usr/local

# Copy application source
COPY app/ .

# Switch to non-root
USER appuser

# Tell Docker this container listens on port 5000
EXPOSE 5000

# Healthcheck — Docker will mark the container unhealthy if /health
# returns non-2xx. Kubernetes liveness probes do the same thing.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# gunicorn is a production WSGI server. Never use Flask's built-in
# dev server (app.run) in production — it's single-threaded.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "main:app"]
