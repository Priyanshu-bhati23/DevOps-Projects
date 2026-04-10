# DevOps Project 1 — Flask + Redis + Docker + CI/CD

A production-grade containerized web service built to teach core DevOps skills
from the ground up. Every file is annotated with explanations of *why*, not just *what*.

## Stack

| Layer | Technology | Purpose |
|---|---|---|
| App | Python / Flask | REST API |
| Cache/DB | Redis | Persistent visit counter |
| Container | Docker (multi-stage) | Reproducible builds |
| Orchestration | Docker Compose | Multi-container local dev |
| CI/CD | GitHub Actions | Lint → Test → Build → Push |
| Metrics | Prometheus | Scrape /metrics endpoint |
| Dashboards | Grafana | Visualise request rate, latency |

---

## Quick start

```bash
# 1. Clone and enter the project
git clone <your-repo-url> devops-project1
cd devops-project1

# 2. Create your .env from the template
cp .env.example .env

# 3. Build and start all services
docker compose up --build

# 4. Hit the endpoints
curl http://localhost:5000/          # app info
curl http://localhost:5000/health    # liveness check
curl -X POST http://localhost:5000/count   # increment counter
curl http://localhost:5000/count     # read counter
curl -X POST http://localhost:5000/reset   # reset counter

# 5. Open dashboards
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000  (admin / admin)
```

---

## Project structure

```
devops-project1/
├── app/
│   ├── main.py              ← Flask app with Redis + Prometheus metrics
│   └── requirements.txt     ← Pinned dependencies (reproducible builds)
│
├── tests/
│   └── test_app.py          ← Integration tests (run against real Redis in CI)
│
├── monitoring/
│   ├── prometheus.yml       ← Scrape config (targets flask-app:5000/metrics)
│   └── grafana/dashboards/  ← Auto-provisioned Grafana dashboards
│
├── .github/workflows/
│   └── ci-cd.yml            ← GitHub Actions: lint → test → build → push
│
├── Dockerfile               ← Multi-stage build (builder + slim runtime)
├── docker-compose.yml       ← Flask + Redis + Prometheus + Grafana
├── .env.example             ← Template — copy to .env, never commit .env
└── .gitignore
```

---

## Key concepts explained

### Why multi-stage Dockerfile?
Stage 1 (builder) installs all build tools and compiles packages.
Stage 2 (runtime) copies only the compiled output into a clean slim image.
Result: the final image has no pip, no compilers — smaller attack surface, smaller size.

### Why pin dependency versions?
`flask==3.0.3` guarantees that a build today and one in 6 months produce
identical behaviour. Unpinned deps silently break when upstream releases a major version.

### Why named volumes for Redis?
Without a volume, all Redis data lives inside the container's writable layer.
`docker compose down` destroys it. A named volume persists independently of containers.

### Why REDIS_HOST is an env var?
- Local dev without Docker: `REDIS_HOST=localhost`
- Docker Compose: `REDIS_HOST=redis` (service name resolves on the shared network)
- Kubernetes: `REDIS_HOST=redis-service` (ClusterIP service name)
Same code, different environments — no code changes needed.

### Why GitHub Actions tags images with the git SHA?
`sha-abc1234` lets you trace exactly which commit is running in any environment.
`latest` is a convenience tag but tells you nothing about what version it actually is.

---

## GitHub Actions setup

Add these secrets to your repo (Settings → Secrets → Actions):

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (not your password) |

The pipeline runs automatically on every push to `main`.

---

## Useful Docker commands

```bash
# See running containers and their health status
docker compose ps

# Follow logs from a specific service
docker compose logs -f flask-app

# Exec into the running container (like SSH)
docker compose exec flask-app sh

# Rebuild only the app (after code changes)
docker compose up --build flask-app

# Stop everything and remove containers (volumes preserved)
docker compose down

# Nuclear option — stop and delete volumes too
docker compose down -v
```

---

## What to build next

- **Project 2:** Deploy this to AWS ECS Fargate with Terraform
- **Project 3:** Move to Kubernetes (kubeadm or minikube), add HPA
- **Project 4:** Add AlertManager — get a Slack ping when error rate spikes
