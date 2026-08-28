import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL


def build_database_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("FORGEQUEUE_DB_USER", "forgequeue_app"),
        password=os.environ["FORGEQUEUE_DB_PASSWORD"],
        host=os.getenv("FORGEQUEUE_DB_HOST", "localhost"),
        port=int(os.getenv("FORGEQUEUE_DB_PORT", "5432")),
        database=os.getenv("FORGEQUEUE_DB_NAME", "forgequeue_dev"),
    )


def create_database_engine() -> Engine:
    return create_engine(build_database_url())