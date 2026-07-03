from contextlib import contextmanager

import psycopg

from app.config import DATABASE_URL


SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    service_name TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('SEV1', 'SEV2', 'SEV3', 'SEV4')),
    status TEXT NOT NULL CHECK (status IN ('open', 'acknowledged', 'resolved')),
    owner TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
"""


@contextmanager
def get_connection():
    with psycopg.connect(DATABASE_URL) as connection:
        yield connection


def init_db():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA)
        connection.commit()
