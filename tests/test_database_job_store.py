from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database_job_store import DatabaseJobStore, job_to_record, record_to_job
from app.database_models import Base, JobRecord
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


def test_add_job_persists_record() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    store = DatabaseJobStore(engine)
    job = Job(input_path=Path("storage/uploads/input.png"))

    store.add_job(job)

    with Session(engine) as session:
        record = session.get(JobRecord, job.id)

        assert record is not None
        assert record.id == job.id
        assert record.status == JobStatus.PENDING.value
        assert record.input_path == str(job.input_path)

    engine.dispose()


def test_get_job_returns_saved_job() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    store = DatabaseJobStore(engine)
    job = Job(input_path=Path("storage/uploads/input.png"))

    store.add_job(job)

    saved = store.get(job.id)

    assert saved is not None
    assert saved.id == job.id
    assert saved.status == job.status
    assert saved.input_path == job.input_path
    assert saved.output_path == job.output_path
    assert saved.error == job.error

    engine.dispose()


def test_get_job_returns_none_for_unknown_uuid() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    store = DatabaseJobStore(engine)

    assert store.get(uuid4()) is None

    engine.dispose()


def test_update_job_persists_new_state() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    store = DatabaseJobStore(engine)

    original = Job(input_path=Path("storage/uploads/input.png"))
    store.add_job(original)

    updated = replace(original)
    updated.transition_to(JobStatus.PROCESSING)

    store.update_job(updated)

    refreshed = store.get(original.id)

    assert refreshed is not None
    normalized_refreshed = replace(
        refreshed,
        created_at=refreshed.created_at.replace(tzinfo=timezone.utc),
        updated_at=refreshed.updated_at.replace(tzinfo=timezone.utc),
    )
    assert normalized_refreshed == updated

    engine.dispose()


def test_update_job_for_unpersisted_job_raises_key_error_with_uuid() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    store = DatabaseJobStore(engine)
    job = Job(input_path=Path("storage/uploads/input.png"))

    with pytest.raises(KeyError) as exc_info:
        store.update_job(job)

    assert exc_info.value.args == (job.id,)

    engine.dispose()
