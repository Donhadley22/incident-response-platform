import os


APP_NAME = os.getenv("APP_NAME", "Incident Response Platform")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://incident_app:incident_password@postgres:5432/incident_response")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DEFAULT_OWNER = os.getenv("DEFAULT_OWNER", "platform-team")
