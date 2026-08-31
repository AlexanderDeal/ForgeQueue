from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.database_job_store import job_to_record, record_to_job
from app.models import Job, JobStatus


def test_job_round_trip_database_record() -> None:
    original = Job(
        id=uuid4(),
        status=JobStatus.COMPLETED,
        input_path=Path("storage/uploads/input.png"),
        output_path=Path("storage/results/output.png"),
        error=None,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    record = job_to_record(original)
    restored = record_to_job(record)

    assert restored == original


def test_pending_job_round_trip_preserves_none() -> None:
    original = Job(input_path=Path("storage/uploads/input.png"))

    record = job_to_record(original)
    restored = record_to_job(record)

    assert record.output_path is None
    assert restored == original