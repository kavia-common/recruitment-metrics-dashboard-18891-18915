from datetime import datetime
import enum
from sqlalchemy import Enum, UniqueConstraint, Index, func
from .extensions import db

class CandidateStatus(enum.Enum):
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"

class InterviewStage(enum.Enum):
    HR = "hr"
    TECHNICAL = "technical"
    MANAGERIAL = "managerial"
    FINAL = "final"

class PositionStatus(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    ON_HOLD = "on_hold"

class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Client(db.Model, TimestampMixin):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    industry = db.Column(db.String(120), nullable=True)
    account_manager = db.Column(db.String(120), nullable=True)
    status = db.Column(Enum(PositionStatus), nullable=False, default=PositionStatus.OPEN)

    positions = db.relationship("Position", backref="client", lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_clients_status", "status"),
    )

class Position(db.Model, TimestampMixin):
    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    status = db.Column(Enum(PositionStatus), nullable=False, default=PositionStatus.OPEN)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    location = db.Column(db.String(120), nullable=True)
    salary_min = db.Column(db.Numeric(asdecimal=False), nullable=True)
    salary_max = db.Column(db.Numeric(asdecimal=False), nullable=True)

    candidates = db.relationship("Candidate", backref="position", lazy=True)

    __table_args__ = (
        Index("ix_positions_client_status", "client_id", "status"),
    )

class Candidate(db.Model, TimestampMixin):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    status = db.Column(Enum(CandidateStatus), nullable=False, default=CandidateStatus.APPLIED)
    source = db.Column(db.String(120), nullable=True)
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    applied_on = db.Column(db.Date, nullable=True)

    interviews = db.relationship("Interview", backref="candidate", lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("email", name="uq_candidates_email"),
        Index("ix_candidates_status", "status"),
    )

class Interview(db.Model, TimestampMixin):
    __tablename__ = "interviews"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    stage = db.Column(Enum(InterviewStage), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    result = db.Column(db.String(120), nullable=True)  # pass/fail/no_show/pending
    interviewer = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    __table_args__ = (
        Index("ix_interviews_stage", "stage"),
        Index("ix_interviews_scheduled_at", "scheduled_at"),
    )

# PUBLIC_INTERFACE
def metrics_summary(session):
    """Return a dict of KPI metrics across entities for dashboard."""
    total_candidates = session.query(func.count(Candidate.id)).scalar() or 0
    hired_candidates = session.query(func.count(Candidate.id)).filter(Candidate.status == CandidateStatus.HIRED).scalar() or 0
    open_positions = session.query(func.count(Position.id)).filter(Position.status == PositionStatus.OPEN).scalar() or 0
    closed_positions = session.query(func.count(Position.id)).filter(Position.status == PositionStatus.CLOSED).scalar() or 0
    upcoming_interviews = session.query(func.count(Interview.id)).filter(Interview.scheduled_at >= func.now()).scalar() or 0

    return {
        "total_candidates": total_candidates,
        "hired_candidates": hired_candidates,
        "open_positions": open_positions,
        "closed_positions": closed_positions,
        "upcoming_interviews": upcoming_interviews,
    }
