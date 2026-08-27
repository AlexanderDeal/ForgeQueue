from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.job_service import JobService
from app.job_store import JobStore
from app.main import app, get_job_service, get_upload_dir, MAX_UPLOAD_BYTES


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


def test_valid_png(tmp_path: Path) -> None:
    image_buffer = BytesIO()

    with Image.new("RGB", (1, 1), color="white") as image:
        image.save(image_buffer, format="PNG")

    image_buffer.seek(0)

    job_store = JobStore()
    job_service = JobService(job_store=job_store)

    app.dependency_overrides[get_job_service] = lambda: job_service
    app.dependency_overrides[get_upload_dir] = lambda: tmp_path

    response = client.post(
        "/jobs",
        files={
            "uploaded_file": (
                "input.png",
                image_buffer,
                "image/png",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["status"] == "PENDING"

    input_path = Path(body["input_path"])

    assert input_path.exists()
    assert input_path.parent == tmp_path


def test_format_mismatch_returns_400(tmp_path: Path) -> None:
    image_buffer = BytesIO()

    with Image.new("RGB", (1, 1), color="white") as image:
        image.save(image_buffer, format="PNG")

    image_buffer.seek(0)

    job_store = JobStore()
    job_service = JobService(job_store=job_store)

    app.dependency_overrides[get_job_service] = lambda: job_service
    app.dependency_overrides[get_upload_dir] = lambda: tmp_path

    response = client.post(
        "/jobs",
        files={
            "uploaded_file": (
                "input.png",
                image_buffer,
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Declared content type does not match the image bytes"
    )
    assert list(tmp_path.iterdir()) == []


def test_invalid_image_returns_400(tmp_path: Path) -> None:
    job_store = JobStore()
    job_service = JobService(job_store=job_store)

    app.dependency_overrides[get_job_service] = lambda: job_service
    app.dependency_overrides[get_upload_dir] = lambda: tmp_path

    response = client.post(
        "/jobs",
        files={
            "uploaded_file": (
                "fake.png",
                b"this is not an image",
                "image/png",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Uploaded file is not a valid image"
    )
    assert list(tmp_path.iterdir()) == []


def test_unsupported_media_type_returns_415(tmp_path: Path) -> None:
    job_store = JobStore()
    job_service = JobService(job_store=job_store)

    app.dependency_overrides[get_job_service] = lambda: job_service
    app.dependency_overrides[get_upload_dir] = lambda: tmp_path

    response = client.post(
        "/jobs",
        files={
            "uploaded_file": (
                "notes.txt",
                b"plain text content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
    assert list(tmp_path.iterdir()) == []


def test_oversized_upload_returns_413(tmp_path: Path) -> None:
    job_store = JobStore()
    job_service = JobService(job_store=job_store)

    app.dependency_overrides[get_job_service] = lambda: job_service
    app.dependency_overrides[get_upload_dir] = lambda: tmp_path

    oversized_contents = b"x" * (MAX_UPLOAD_BYTES + 1)

    response = client.post(
        "/jobs",
        files={
            "uploaded_file": (
                "large.png",
                oversized_contents,
                "image/png",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "Uploaded file exceeds the 5 MB limit"
    )

    assert list(tmp_path.iterdir()) == []