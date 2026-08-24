from pathlib import Path
from uuid import UUID
from datetime import timezone

from app.models import Job, JobStatus


class TestJob:
    def test_job_initialization(self, tmp_path: Path) -> None:
        path = tmp_path / 'image.png'
        job = Job(path)
        assert isinstance(job.id, UUID)
        assert job.status == JobStatus.PENDING
        assert job.created_at is not None
        assert job.updated_at is not None
        assert job.input_path is not None
        assert job.output_path is None
        assert job.error is None
        assert job.created_at.tzinfo is timezone.utc
        assert job.updated_at.tzinfo is timezone.utc

    def test_unique_job_ids(self, tmp_path: Path) -> None:
        path1 = tmp_path / 'image1.png'
        path2 = tmp_path / 'image2.png'
        job1 = Job(path1)
        job2 = Job(path2)
        assert job1.id != job2.id
