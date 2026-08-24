from pathlib import Path
from uuid import uuid4
import pytest

from app.job_service import JobService, JobNotFoundError
from app.models import JobStatus
from app.job_store import JobStore


class TestJobService:
    def test_create_job(self, tmp_path: Path) -> None:
        store = JobStore()
        input_path = tmp_path / "input.png"
        job_service = JobService(store)
        job = job_service.create_job(input_path)
        assert store.get(job.id) is job
        assert job.status is JobStatus.PENDING
        assert input_path == job.input_path
        assert job_service.get_job(job.id) is job

    def test_unknown_job_id(self) -> None:
        store = JobStore()
        job_service = JobService(store)
        with pytest.raises(JobNotFoundError):
            job_service.get_job(uuid4())
