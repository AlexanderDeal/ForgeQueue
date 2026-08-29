from uuid import UUID
from typing import Protocol

from app.models import Job


class JobStoreProtocol(Protocol):
    def add_job(self, job: Job) -> None:
        ...

    def get(self, job_id: UUID) -> Job | None:
        ...

    def update_job(self, job: Job) -> None:
        ...



class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}

    def add_job(self, job: Job) -> None:
        self._jobs[job.id] = job

    def get(self, job_id: UUID) -> Job | None:
        return self._jobs.get(job_id)

    def update_job(self, job: Job) -> None:
        if job.id in self._jobs:
            self._jobs[job.id] = job
        else:
            raise KeyError(job.id)