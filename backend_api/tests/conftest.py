import os
import io
import datetime as dt
import pytest
from flask import Flask

# Ensure test env
os.environ.setdefault("FLASK_ENV", "test")
# Point SQLAlchemy to in-memory sqlite so we don't need a running Postgres for tests
os.environ["POSTGRES_URL"] = ""
os.environ["POSTGRES_USER"] = ""
os.environ["POSTGRES_PASSWORD"] = ""
os.environ["POSTGRES_DB"] = ""
os.environ["POSTGRES_PORT"] = "5432"

# Patch Config.sqlalchemy_uri to use sqlite for tests
from app.config import Config  # noqa: E402
from app.extensions import db  # noqa: E402
from app import app as flask_app  # noqa: E402

def _sqlite_uri(_: Config) -> str:
    # Use a local sqlite database file (not memory) so separate app contexts share the same DB during tests
    return "sqlite:///test.db"

Config.sqlalchemy_uri = _sqlite_uri  # type: ignore[method-assign]


@pytest.fixture(scope="session")
def app() -> Flask:
    """
    Create a Flask app configured for testing.

    Uses sqlite database and creates all tables.
    """
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=Config().sqlalchemy_uri(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
    yield flask_app
    # Teardown once per session
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
        # clean sqlite file if created
        try:
            os.remove("test.db")
        except OSError:
            pass


@pytest.fixture()
def client(app: Flask):
    """
    Provide a Flask test client.
    """
    return app.test_client()


@pytest.fixture()
def db_session(app: Flask):
    """
    Provide a clean database session per test with rollback.
    """
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        options = dict(bind=connection, binds={})
        sess = db.create_scoped_session(options=options)  # type: ignore[attr-defined]
        db.session = sess  # type: ignore[assignment]
        yield sess
        transaction.rollback()
        connection.close()
        sess.remove()


@pytest.fixture()
def seed_basic_data(db_session):
    """
    Seed a small set of clients/positions/candidates/interviews for tests that need data.
    """
    from app.models import Client, Position, Candidate, Interview, CandidateStatus, PositionStatus, InterviewStage

    acme = Client(name="Acme Corp", industry="Manufacturing", account_manager="Amy", status=PositionStatus.OPEN)
    db_session.add(acme)
    db_session.flush()

    dev = Position(title="Software Engineer", status=PositionStatus.OPEN, client_id=acme.id, location="Remote")
    db_session.add(dev)
    db_session.flush()

    cand = Candidate(
        full_name="John Doe",
        email="john@example.com",
        phone="555-0000",
        status=CandidateStatus.APPLIED,
        source="LinkedIn",
        position_id=dev.id,
        applied_on=dt.date.today(),
    )
    db_session.add(cand)
    db_session.flush()

    iv = Interview(
        candidate_id=cand.id,
        stage=InterviewStage.HR,
        scheduled_at=dt.datetime.utcnow() + dt.timedelta(days=1),
        result=None,
        interviewer="HR Bot",
    )
    db_session.add(iv)
    db_session.commit()

    return {
        "client": acme,
        "position": dev,
        "candidate": cand,
        "interview": iv,
    }


def make_excel_bytes():
    """
    Create a simple Excel file in-memory matching expected sheets for upload tests.
    """
    import pandas as pd

    clients_df = pd.DataFrame(
        [
            {"name": "Widget Co", "industry": "Tech", "account_manager": "Wendy", "status": "open"},
        ]
    )
    positions_df = pd.DataFrame(
        [
            {"title": "Data Analyst", "status": "open", "client_name": "Widget Co", "location": "SF", "salary_min": 60000, "salary_max": 90000},
        ]
    )
    candidates_df = pd.DataFrame(
        [
            {
                "full_name": "Alice Smith",
                "email": "alice@example.com",
                "phone": "555-1111",
                "status": "applied",
                "source": "Referral",
                "position_title": "Data Analyst",
                "client_name": "Widget Co",
                "applied_on": pd.Timestamp(dt.date.today()),
            }
        ]
    )

    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        clients_df.to_excel(writer, sheet_name="clients", index=False)
        positions_df.to_excel(writer, sheet_name="positions", index=False)
        candidates_df.to_excel(writer, sheet_name="candidates", index=False)
    bio.seek(0)
    return bio
