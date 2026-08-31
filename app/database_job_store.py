from pathlib import Path

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
