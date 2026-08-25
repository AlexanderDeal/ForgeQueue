from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from app.api_models import JobResponse
from app.models import Job, JobStatus


def test_job_converts_to_job_response_with_json_compatible_dump() -> None:
    job_id = uuid4()
    created_at = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    job = Job(
        id=job_id,
        status=JobStatus.PENDING,
        created_at=created_at,
        input_path=Path("/var/lib/forgequeue/input.txt"),
        output_path=None,
        error=None,
    )

    response = JobResponse.model_validate(job)

    assert isinstance(response.id, UUID)
    assert response.id == job_id
    assert isinstance(response.status, JobStatus)
    assert response.status is JobStatus.PENDING
    assert response.output_path is None
    assert response.error is None

    dumped = response.model_dump(mode="json")

    assert dumped["id"] == str(job_id)
    assert dumped["status"] == JobStatus.PENDING.value
    assert dumped["created_at"] == created_at.isoformat().replace("+00:00", "Z")
    assert dumped["input_path"] == str(job.input_path)
    assert dumped["output_path"] is None
    assert dumped["error"] is None
