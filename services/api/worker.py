import logging
import time

import redis
from psycopg.rows import dict_row

from app.config import REDIS_URL
from app.db import get_connection, init_db


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
queue = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def main():
    init_db()
    logging.info("incident worker started")

    while True:
        _, incident_id = queue.brpop("incident_jobs")
        process_incident(int(incident_id))


def process_incident(incident_id: int):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, title, service_name, severity, owner
                FROM incidents
                WHERE id = %s
                """,
                (incident_id,),
            )
            incident = cursor.fetchone()

    if not incident:
        logging.warning("incident %s was queued but no longer exists", incident_id)
        return

    time.sleep(2)
    logging.info(
        "notified %s for %s incident %s affecting %s",
        incident["owner"],
        incident["severity"],
        incident["id"],
        incident["service_name"],
    )


if __name__ == "__main__":
    main()
