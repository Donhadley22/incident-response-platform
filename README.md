# Incident Response Platform

This project is a seven-service Docker Compose application for managing operational incidents. It models a common production architecture used by platform, SRE, and DevOps teams: a user-facing web app, an API, background processing, persistent storage, cache/queue infrastructure, edge routing, and monitoring.

## What problem it solves

Engineering teams need a reliable way to capture outages, assign ownership, track severity, move work from open to resolved, and expose operational metrics. This sample keeps the scope small enough for learning Docker Compose, but the pattern maps to real systems such as internal incident portals, support escalation tools, and service reliability dashboards.

## Services

1. `edge` - Nginx reverse proxy. It exposes one public entry point on port `8081` and routes browser traffic to the frontend and API traffic to the backend.
2. `frontend` - Static web UI served by Nginx. Operators can open, acknowledge, and resolve incidents.
3. `api` - FastAPI backend. It validates requests, stores incidents, exposes health checks, and publishes Prometheus metrics.
4. `worker` - Background processor. It consumes queued incident jobs from Redis and simulates notifying the owning team.
5. `postgres` - PostgreSQL database. It stores durable incident records.
6. `redis` - Redis cache and lightweight queue. It caches incident lists and queues background notification jobs.
7. `prometheus` - Metrics server. It scrapes the API metrics endpoint for operational visibility.

## Run it

From this directory:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

- App: http://localhost:8081
- API health: http://localhost:8081/api/health
- API docs: http://localhost:8081/api/docs
- Prometheus: http://localhost:9090

Stop the stack:

```powershell
docker compose down
```

Remove local data volumes:

```powershell
docker compose down -v
```

## Why this is industry standard

- Uses one public ingress service instead of exposing every internal service.
- Separates frontend, API, worker, database, cache, and monitoring concerns.
- Adds health checks for stateful dependencies and the API.
- Uses named Docker volumes so database and monitoring data survive container restarts.
- Keeps services on a private Docker network.
- Provides Prometheus-compatible metrics for observability.
- Uses environment variables for runtime configuration.

## Suggested exercises

- Add Grafana as an eighth service and build a dashboard from Prometheus metrics.
- Add authentication to protect incident management endpoints.
- Replace the simulated worker notification with email, Slack, or Microsoft Teams integration.
- Add CI/CD to build and scan the containers before deployment.
