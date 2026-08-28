from app.database_models import JobRecord


def test_job_record_has_expected_columns():
    assert set(JobRecord.__table__.columns.keys()) == {
        "id",
        "status",
        "input_path",
        "output_path",
        "error",
        "created_at",
        "updated_at",
    }


def test_job_record_column_constraints():
    table = JobRecord.__table__

    assert table.c.id.primary_key is True
    assert table.c.id.nullable is False
    assert table.c.status.nullable is False
    assert table.c.input_path.nullable is False
    assert table.c.output_path.nullable is True
    assert table.c.error.nullable is True
    assert table.c.created_at.nullable is False
    assert table.c.updated_at.nullable is False
    assert table.c.created_at.type.timezone is True
    assert table.c.updated_at.type.timezone is True


def test_job_record_has_status_check_constraint():
    constraint_names = {
        constraint.name for constraint in JobRecord.__table__.constraints
    }

    assert "ck_jobs_status" in constraint_names
