from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from app.job_store import JobStore
from app.models import Job, JobStatus


class TestJobStore:
    def test_add(self, tmp_path: Path) -> None:
        path = tmp_path / 'image.png'
        job_store = JobStore()
        job = Job(path)
        job_store.add_job(job)
        assert job_store.get(job.id) is job

    def test_get_nonexistent_job(self) -> None:
        job_store = JobStore()
        assert job_store.get(uuid4()) is None

    def test_two_job_stores_are_independent(self, tmp_path: Path) -> None:
        path = tmp_path / 'image.png'
        job_store1 = JobStore()
        job_store2 = JobStore()
        job1 = Job(path)
        job_store1.add_job(job1)
        assert job_store1.get(job1.id) is job1
        assert job_store2.get(job1.id) is None

    def test_update_existing_job(self, tmp_path: Path) -> None:
        job_store = JobStore()
        original_job = Job(tmp_path / "image.png")
        job_store.add_job(original_job)

        updated_job = replace(original_job, status=JobStatus.PROCESSING)
        job_store.update_job(updated_job)

        assert job_store.get(original_job.id) is updated_job

    def test_update_unknown_job_raises_key_error(self) -> None:
        job_store = JobStore()
        job = Job(Path("image.png"))

        with pytest.raises(KeyError) as exc_info:
            job_store.update_job(job)

        assert exc_info.value.args == (job.id,)