import json
from typing import Literal

import redis
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

from app.config import APP_NAME, DEFAULT_OWNER, REDIS_URL
from app.db import get_connection, init_db


Severity = Literal["SEV1", "SEV2", "SEV3", "SEV4"]
Status = Literal["open", "acknowledged", "resolved"]

INCIDENTS_CREATED = Counter("incidents_created_total", "Total incidents created", ["severity"])
INCIDENTS_RESOLVED = Counter("incidents_resolved_total", "Total incidents resolved")
OPEN_INCIDENTS = Gauge("open_incidents", "Current open or acknowledged incidents")

app = FastAPI(title=APP_NAME)
cache = redis.Redis.from_url(REDIS_URL, decode_responses=True)


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=4, max_length=120)
    service_name: str = Field(..., min_length=2, max_length=80)
    severity: Severity = "SEV3"
    owner: str = Field(default=DEFAULT_OWNER, min_length=2, max_length=80)
    summary: str = Field(..., min_length=8, max_length=1000)


class IncidentUpdate(BaseModel):
    status: Status


@app.on_event("startup")
def startup():
    init_db()
    refresh_open_incident_metric()


@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}


@app.get("/incidents")
def list_incidents():
    cached = cache.get("incidents:list")
    if cached:
        return {"source": "cache", "items": json.loads(cached)}

    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, title, service_name, severity, status, owner, summary, created_at, updated_at
                FROM incidents
                ORDER BY created_at DESC
                LIMIT 50
                """
            )
            incidents = cursor.fetchall()

    payload = [serialize_incident(incident) for incident in incidents]
    cache.setex("incidents:list", 15, json.dumps(payload))
    return {"source": "database", "items": payload}


@app.post("/incidents", status_code=201)
def create_incident(incident: IncidentCreate):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                INSERT INTO incidents (title, service_name, severity, status, owner, summary)
                VALUES (%s, %s, %s, 'open', %s, %s)
                RETURNING id, title, service_name, severity, status, owner, summary, created_at, updated_at
                """,
                (incident.title, incident.service_name, incident.severity, incident.owner, incident.summary),
            )
            created = cursor.fetchone()
        connection.commit()

    cache.delete("incidents:list")
    cache.lpush("incident_jobs", created["id"])
    INCIDENTS_CREATED.labels(severity=incident.severity).inc()
    refresh_open_incident_metric()
    return serialize_incident(created)


@app.patch("/incidents/{incident_id}")
def update_incident(incident_id: int, update: IncidentUpdate):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                UPDATE incidents
                SET status = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING id, title, service_name, severity, status, owner, summary, created_at, updated_at
                """,
                (update.status, incident_id),
            )
            incident = cursor.fetchone()
        connection.commit()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if update.status == "resolved":
        INCIDENTS_RESOLVED.inc()

    cache.delete("incidents:list")
    refresh_open_incident_metric()
    return serialize_incident(incident)


@app.get("/metrics")
def metrics():
    refresh_open_incident_metric()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def refresh_open_incident_metric():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM incidents WHERE status IN ('open', 'acknowledged')")
            OPEN_INCIDENTS.set(cursor.fetchone()[0])


def serialize_incident(incident):
    return {
        "id": incident["id"],
        "title": incident["title"],
        "service_name": incident["service_name"],
        "severity": incident["severity"],
        "status": incident["status"],
        "owner": incident["owner"],
        "summary": incident["summary"],
        "created_at": incident["created_at"].isoformat(),
        "updated_at": incident["updated_at"].isoformat(),
    }
