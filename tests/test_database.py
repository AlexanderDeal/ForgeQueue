import pytest

from app.database import build_database_url


def test_build_database_url_from_environment(monkeypatch):
    monkeypatch.setenv("FORGEQUEUE_DB_HOST", "db.example.com")
    monkeypatch.setenv("FORGEQUEUE_DB_PORT", "5432")
    monkeypatch.setenv("FORGEQUEUE_DB_NAME", "forgequeue")
    monkeypatch.setenv("FORGEQUEUE_DB_USER", "appuser")
    monkeypatch.setenv("FORGEQUEUE_DB_PASSWORD", "p@ss word!/")

    url = build_database_url()

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "appuser"
    assert url.password == "p@ss word!/"
    assert url.host == "db.example.com"
    assert url.port == 5432
    assert url.database == "forgequeue"


def test_build_database_url_missing_password_raises(monkeypatch):
    monkeypatch.delenv("FORGEQUEUE_DB_PASSWORD", raising=False)
    monkeypatch.setenv("FORGEQUEUE_DB_HOST", "db.example.com")
    monkeypatch.setenv("FORGEQUEUE_DB_PORT", "5432")
    monkeypatch.setenv("FORGEQUEUE_DB_NAME", "forgequeue")
    monkeypatch.setenv("FORGEQUEUE_DB_USER", "appuser")

    with pytest.raises(KeyError):
        build_database_url()


def test_build_database_url_does_not_connect(monkeypatch):
    monkeypatch.setenv("FORGEQUEUE_DB_HOST", "db.example.com")
    monkeypatch.setenv("FORGEQUEUE_DB_PORT", "5432")
    monkeypatch.setenv("FORGEQUEUE_DB_NAME", "forgequeue")
    monkeypatch.setenv("FORGEQUEUE_DB_USER", "appuser")
    monkeypatch.setenv("FORGEQUEUE_DB_PASSWORD", "secret")

    called = {"value": False}

    def fake_create_engine(*args, **kwargs):
        called["value"] = True
        raise AssertionError("create_engine should not be called when building the URL")

    monkeypatch.setattr("sqlalchemy.create_engine", fake_create_engine)

    url = build_database_url()
    assert url is not None
    assert called["value"] is False

