from pathlib import Path
from uuid import UUID

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.database_models import JobRecord
from app.models import Job, JobStatus


def job_to_record(job: Job) -> JobRecord:
    return JobRecord(
        id=job.id,
        status=job.status.value,
        input_path=str(job.input_path),
        output_path=str(job.output_path) if job.output_path is not None else None,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def record_to_job(record: JobRecord) -> Job:
    return Job(
        id=record.id,
        status=JobStatus(record.status),
        input_path=Path(record.input_path),
        output_path=Path(record.output_path) if record.output_path is not None else None,
        error=record.error,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


class DatabaseJobStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add_job(self, job: Job) -> None:
        record = job_to_record(job)

        with Session(self._engine) as session:
            with session.begin():
                session.add(record)

    def get(self, job_id: UUID) -> Job | None:
        with Session(self._engine) as session:
            record = session.get(JobRecord, job_id)
            if record is None:
                return None
            return record_to_job(record)

    def update_job(self, job: Job) -> None:
        record = job_to_record(job)

        with Session(self._engine) as session:
            with session.begin():
                existing = session.get(JobRecord, job.id)
                if existing is None:
                    raise KeyError(job.id)

                existing.status = record.status
                existing.input_path = record.input_path
                existing.output_path = record.output_path
                existing.error = record.error
                existing.created_at = record.created_at
                existing.updated_at = record.updated_at
