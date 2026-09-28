import logging
import os
import signal
import socket
import time
from pathlib import Path

from app.database import create_database_engine
from app.database_job_store import DatabaseJobStore
from app.job_queue import RedisJobQueue
from app.job_service import JobService
from app.models import JobStatus
from app.redis_client import create_redis_client


logging.basicConfig(
    level=os.getenv("FORGEQUEUE_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("forgequeue.worker")


def output_path_for(input_path: Path, job_id: object) -> Path:
    suffix = ".jpg" if input_path.suffix.lower() in {".jpg", ".jpeg"} else ".png"
    return Path(os.getenv("FORGEQUEUE_RESULT_DIR", "storage/results")) / f"{job_id}{suffix}"


def run_worker() -> None:
    engine = create_database_engine()
    redis_client = create_redis_client()
    queue = RedisJobQueue(redis_client)
    service = JobService(DatabaseJobStore(engine))
    consumer = os.getenv("FORGEQUEUE_WORKER_NAME", socket.gethostname())
    max_attempts = int(os.getenv("FORGEQUEUE_MAX_ATTEMPTS", "3"))
    stopping = False

    def request_stop(signum: int, frame: object) -> None:
        nonlocal stopping
        del signum, frame
        stopping = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    logger.info("worker_started consumer=%s", consumer)
    try:
        while not stopping:
            message = queue.dequeue(consumer)
            if message is None:
                message = queue.recover_stale(consumer)
                if message is None:
                    continue
            try:
                job = service.get_job(message.job_id)
                if job.status is JobStatus.COMPLETED:
                    queue.acknowledge(message.message_id)
                    logger.info("duplicate_job_ignored job_id=%s", job.id)
                    continue
                if job.status in {JobStatus.PROCESSING, JobStatus.FAILED}:
                    job = service.retry_job(job.id)
                output_path = output_path_for(job.input_path, job.id)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                service.process_job(job.id, output_path, (200, 200))
                queue.acknowledge(message.message_id)
                logger.info("job_completed job_id=%s", job.id)
            except Exception:
                logger.exception(
                    "job_failed job_id=%s attempt=%s",
                    message.job_id,
                    message.attempt + 1,
                )
                if message.attempt + 1 < max_attempts:
                    service.retry_job(message.job_id)
                    time.sleep(min(2 ** message.attempt, 30))
                    queue.enqueue(message.job_id, message.attempt + 1)
                queue.acknowledge(message.message_id)
    except KeyboardInterrupt:
        logger.info("worker_stopping")
    finally:
        redis_client.close()
        engine.dispose()


if __name__ == "__main__":
    run_worker()
