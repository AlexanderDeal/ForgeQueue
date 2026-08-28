from pathlib import Path
from uuid import UUID
from datetime import timezone

import pytest

from app.models import InvalidJobTransitionError, Job, JobStatus


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

    def test_pending_to_processing(self, tmp_path: Path) -> None:
        path = tmp_path / 'image.png'
        job = Job(path)
        initial_updated_at = job.updated_at

        job.transition_to(new_status=JobStatus.PROCESSING)

        assert job.status == JobStatus.PROCESSING
        assert job.updated_at != initial_updated_at

    def test_processing_to_completed(self, tmp_path: Path) -> None:
        job = Job(tmp_path / 'image.png')
        job.transition_to(new_status=JobStatus.PROCESSING)

        job.transition_to(new_status=JobStatus.COMPLETED)

        assert job.status == JobStatus.COMPLETED

    def test_processing_to_failed(self, tmp_path: Path) -> None:
        job = Job(tmp_path / 'image.png')
        job.transition_to(new_status=JobStatus.PROCESSING)

        job.transition_to(new_status=JobStatus.FAILED)

        assert job.status == JobStatus.FAILED

    def test_pending_to_completed_raises_and_preserves_status(
        self, tmp_path: Path
    ) -> None:
        job = Job(tmp_path / 'image.png')

        with pytest.raises(InvalidJobTransitionError):
            job.transition_to(new_status=JobStatus.COMPLETED)

        assert job.status == JobStatus.PENDING

    def test_completed_to_processing_raises(self, tmp_path: Path) -> None:
        job = Job(tmp_path / 'image.png')
        job.transition_to(new_status=JobStatus.PROCESSING)
        job.transition_to(new_status=JobStatus.COMPLETED)

        with pytest.raises(InvalidJobTransitionError):
            job.transition_to(new_status=JobStatus.PROCESSING)

        assert job.status == JobStatus.COMPLETED
