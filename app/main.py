import os
import time
import logging
import redis
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
metrics = PrometheusMetrics(app)          # auto-exposes /metrics for Prometheus

# ── Redis connection ──────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


def get_redis():
    """Create a Redis client with a simple retry on startup."""
    for attempt in range(5):
        try:
            client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            client.ping()
            log.info("Connected to Redis at %s:%s", REDIS_HOST, REDIS_PORT)
            return client
        except redis.ConnectionError:
            log.warning("Redis not ready, retrying (%d/5)...", attempt + 1)
            time.sleep(2)
    raise RuntimeError("Could not connect to Redis after 5 attempts")


r = get_redis()

# ── Routes ────────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return jsonify({
        "app": "devops-project1",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "endpoints": ["/health", "/count", "/metrics"],
    })


@app.route("/health")
def health():
    """Liveness probe — used by Docker and Kubernetes."""
    try:
        r.ping()
        redis_status = "ok"
    except redis.ConnectionError:
        redis_status = "unreachable"

    status = "ok" if redis_status == "ok" else "degraded"
    code = 200 if status == "ok" else 503
    return jsonify({"status": status, "redis": redis_status}), code


@app.route("/count", methods=["GET", "POST"])
def count():
    """
    GET  → return current visit count.
    POST → increment visit count, return new value.
    """
    if request.method == "POST":
        visits = r.incr("visit_count")      # atomic — safe under concurrency
        log.info("Visit count incremented to %d", visits)
        return jsonify({"visits": visits, "action": "incremented"}), 200

    visits = int(r.get("visit_count") or 0)
    return jsonify({"visits": visits, "action": "read"}), 200


@app.route("/reset", methods=["POST"])
def reset():
    """Reset the counter. Useful for demos."""
    r.set("visit_count", 0)
    log.info("Visit count reset to 0")
    return jsonify({"visits": 0, "action": "reset"}), 200


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
