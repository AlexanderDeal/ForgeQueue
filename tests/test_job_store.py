from uuid import uuid4
from pathlib import Path

from app.job_store import JobStore
from app.models import Job


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



