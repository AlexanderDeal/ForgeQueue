import os

from redis import Redis


def create_redis_client() -> Redis:
    return Redis.from_url(
        os.getenv("FORGEQUEUE_REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )
