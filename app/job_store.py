from uuid import UUID

from app.models import Job


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}

    def add_job(self, job: Job) -> None:
        self._jobs[job.id] = job

    def get(self, job_id: UUID) -> Job | None:
        return self._jobs.get(job_id)