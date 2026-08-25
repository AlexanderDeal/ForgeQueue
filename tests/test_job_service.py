from pathlib import Path
from uuid import uuid4
import pytest
from PIL import Image

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

    def test_process_job_creates_resized_output(self, tmp_path: Path) -> None:
        store = JobStore()
        input_path = tmp_path / "input.png"
        Image.new("RGB", (400, 400), color="blue").save(input_path)
        job_service = JobService(store)
        job = job_service.create_job(input_path)
        output_path = tmp_path / f"{job.id}.png"
        processed_job = job_service.process_job(job.id, output_path, (200, 200))
        assert job is processed_job
        assert processed_job.status is JobStatus.COMPLETED
        assert processed_job.output_path == output_path
        assert processed_job.output_path.exists()
        with Image.open(processed_job.output_path) as output_image:
            assert output_image.size == (200, 200)
        assert processed_job.updated_at >= processed_job.created_at

    def test_process_job_records_failure(self, tmp_path: Path) -> None:
        store = JobStore()
        job_service = JobService(store)
        job = job_service.create_job(tmp_path / "nonexistent" / "input.png")
        output_path = tmp_path / f"{job.id}.png"
        with pytest.raises(FileNotFoundError):
            job_service.process_job(job_id=job.id, output_path=output_path, max_size=(200, 200))

        assert job.status is JobStatus.FAILED
        assert job.error
        assert job.output_path is None
        assert job.updated_at >= job.created_at