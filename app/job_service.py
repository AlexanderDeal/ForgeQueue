from pathlib import Path
from uuid import UUID

from app.job_store import JobStore
from app.models import Job


class JobNotFoundError(Exception):
    def __init__(self, job_id: UUID) -> None:
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


class JobService:
    def __init__(self, job_store: JobStore) -> None:
        self._store = job_store

    def create_job(self, input_path: Path) -> Job:
        job = Job(input_path=input_path)
        self._store.add_job(job)
        return job

    def get_job(self, job_id: UUID) -> Job:
        job = self._store.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        return job
