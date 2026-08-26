from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.job_service import JobService
from app.job_store import JobStore
from app.main import app, get_job_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None, None, None]:
    yield
    app.dependency_overrides.clear()


def test_read_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_known_job(tmp_path: Path) -> None:
    job_store = JobStore()
    job_service = JobService(job_store=job_store)
    input_path = tmp_path / "input.png"
    job = job_service.create_job(input_path)

    app.dependency_overrides[get_job_service] = lambda: job_service
    response = client.get(f"/jobs/{job.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(job.id)
    assert body["status"] == job.status.value
    assert body["input_path"] == str(input_path)


def test_unknown_job() -> None:
    missing_id = uuid4()
    response = client.get(f"/jobs/{missing_id}")
    assert response.status_code == 404
    assert str(missing_id) in response.json()["detail"]