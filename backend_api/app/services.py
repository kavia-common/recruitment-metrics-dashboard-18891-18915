import io
from typing import Tuple, Dict, Any, List, Optional
from sqlalchemy import or_
from werkzeug.datastructures import FileStorage
import pandas as pd
from zipfile import BadZipFile
from .extensions import db
from .models import Candidate, Client, Position, Interview, CandidateStatus, PositionStatus, InterviewStage

# PUBLIC_INTERFACE
def paginate(query, page: int, page_size: int):
    """Paginate a SQLAlchemy query."""
    page = max(1, int(page or 1))
    page_size = min(200, max(1, int(page_size or 20)))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    meta = {
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "page": page,
        "page_size": page_size,
    }
    return items, meta

# PUBLIC_INTERFACE
def apply_candidate_filters(query, args: Dict[str, Any]):
    """Apply filter params to candidate query."""
    status = args.get("status")
    q = args.get("q")
    position_id = args.get("position_id")

    if status:
        query = query.filter(Candidate.status == CandidateStatus(status))
    if position_id:
        query = query.filter(Candidate.position_id == int(position_id))
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(or_(Candidate.full_name.ilike(like), Candidate.email.ilike(like), Candidate.source.ilike(like)))
    return query

# PUBLIC_INTERFACE
def apply_interview_filters(query, args: Dict[str, Any]):
    """Apply filters for interviews."""
    stage = args.get("stage")
    result = args.get("result")
    if stage:
        query = query.filter(Interview.stage == InterviewStage(stage))
    if result:
        query = query.filter(Interview.result == result)
    return query

# PUBLIC_INTERFACE
def apply_client_filters(query, args: Dict[str, Any]):
    """Apply filters for clients."""
    status = args.get("status")
    q = args.get("q")
    if status:
        query = query.filter(Client.status == PositionStatus(status))
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(Client.name.ilike(like))
    return query

def _validate_required_columns(df: pd.DataFrame, required: List[str], sheet_name: str, errors: List[str]) -> bool:
    """Helper: ensure required columns exist; append error and return False if missing."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Sheet '{sheet_name}' is missing required columns: {', '.join(missing)}")
        return False
    return True

def _safe_enum(enum_cls, value: Optional[str], default_value: str, field: str, errors: List[str]):
    """Helper: parse a case-insensitive enum value; if invalid, append error and return default."""
    val = (value or default_value).lower()
    try:
        return enum_cls(val)
    except Exception:
        errors.append(f"Invalid value '{value}' for '{field}'. Using default '{default_value}'.")
        return enum_cls(default_value)

# PUBLIC_INTERFACE
def process_excel_upload(file: FileStorage) -> Tuple[int, int, list]:
    """Parse Excel file and upsert clients, positions, and candidates.

    Expected sheets (optional but at least one required):
    - candidates: columns [full_name, email, phone, status, source, position_title, client_name, applied_on]
    - clients: [name, industry, account_manager, status]
    - positions: [title, status, client_name, location, salary_min, salary_max]

    Returns:
        (inserted, updated, errors): Counts and a list of human-readable error messages.
    """
    inserted, updated = 0, 0
    errors: List[str] = []
    try:
        content = file.read()
        # pd.read_excel will use openpyxl engine for xlsx by default (given requirements).
        df_map = pd.read_excel(io.BytesIO(content), sheet_name=None)
    except BadZipFile:
        return 0, 0, ["The uploaded file is not a valid .xlsx workbook (corrupt or wrong format)."]
    except ValueError as e:
        # Typically raised if no sheet found or wrong engine
        return 0, 0, [f"Failed to parse Excel: {e}"]
    except Exception as e:
        return 0, 0, [f"Failed to parse Excel: {e}"]

    if not df_map:
        return 0, 0, ["No sheets found in the uploaded workbook. Expected 'clients', 'positions', or 'candidates'."]

    # Track if at least one sheet is processed
    any_processed = False

    # Upsert clients
    clients_df = df_map.get("clients")
    if clients_df is not None:
        any_processed = True
        # Validate required columns
        if _validate_required_columns(clients_df, ["name", "status"], "clients", errors):
            for _, r in clients_df.iterrows():
                name = str(r.get("name") or "").strip()
                if not name:
                    # Skip empty row
                    continue
                status_enum = _safe_enum(PositionStatus, str(r.get("status") or "open"), "open", "clients.status", errors)
                client = Client.query.filter_by(name=name).one_or_none()
                if client:
                    client.industry = r.get("industry")
                    client.account_manager = r.get("account_manager")
                    client.status = status_enum
                    updated += 1
                else:
                    client = Client(
                        name=name,
                        industry=r.get("industry"),
                        account_manager=r.get("account_manager"),
                        status=status_enum,
                    )
                    db.session.add(client)
                    inserted += 1
            db.session.flush()

    # Upsert positions
    positions_df = df_map.get("positions")
    client_cache = {c.name: c for c in Client.query.all()}
    if positions_df is not None:
        any_processed = True
        if _validate_required_columns(positions_df, ["title", "status", "client_name"], "positions", errors):
            for _, r in positions_df.iterrows():
                title = str(r.get("title") or "").strip()
                client_name = str(r.get("client_name") or "").strip()
                if not title or not client_name:
                    continue
                client = client_cache.get(client_name) or Client.query.filter_by(name=client_name).one_or_none()
                if not client:
                    # Create missing client as OPEN by default
                    client = Client(name=client_name, status=PositionStatus.OPEN)
                    db.session.add(client)
                    db.session.flush()
                    client_cache[client_name] = client
                    inserted += 1
                status_enum = _safe_enum(PositionStatus, str(r.get("status") or "open"), "open", "positions.status", errors)
                position = Position.query.filter_by(title=title, client_id=client.id).one_or_none()
                if position:
                    position.status = status_enum
                    position.location = r.get("location")
                    position.salary_min = r.get("salary_min")
                    position.salary_max = r.get("salary_max")
                    updated += 1
                else:
                    position = Position(
                        title=title,
                        status=status_enum,
                        client_id=client.id,
                        location=r.get("location"),
                        salary_min=r.get("salary_min"),
                        salary_max=r.get("salary_max"),
                    )
                    db.session.add(position)
                    inserted += 1
            db.session.flush()

    # Upsert candidates
    cands_df = df_map.get("candidates")
    position_cache: Dict[tuple, Position] = {}
    if cands_df is not None:
        any_processed = True
        if _validate_required_columns(cands_df, ["full_name", "status"], "candidates", errors):
            for _, r in cands_df.iterrows():
                full_name = str(r.get("full_name") or "").strip()
                if not full_name:
                    continue
                email = r.get("email")
                status_enum = _safe_enum(CandidateStatus, str(r.get("status") or "applied"), "applied", "candidates.status", errors)
                pos_title = str(r.get("position_title") or "").strip()
                client_name = str(r.get("client_name") or "").strip()

                pos = None
                if pos_title and client_name:
                    key = (pos_title, client_name)
                    pos = position_cache.get(key)
                    if pos is None:
                        cli = client_cache.get(client_name) or Client.query.filter_by(name=client_name).one_or_none()
                        if cli:
                            pos = Position.query.filter_by(title=pos_title, client_id=cli.id).one_or_none()
                            if pos:
                                position_cache[key] = pos

                cand = None
                if email:
                    cand = Candidate.query.filter_by(email=email).one_or_none()

                if cand:
                    cand.full_name = full_name
                    cand.phone = r.get("phone")
                    cand.status = status_enum
                    cand.source = r.get("source")
                    cand.position_id = pos.id if pos else None
                    cand.applied_on = r.get("applied_on")
                    updated += 1
                else:
                    cand = Candidate(
                        full_name=full_name,
                        email=email,
                        phone=r.get("phone"),
                        status=status_enum,
                        source=r.get("source"),
                        position_id=pos.id if pos else None,
                        applied_on=r.get("applied_on"),
                    )
                    db.session.add(cand)
                    inserted += 1

    if not any_processed:
        errors.append("Workbook contains none of the expected sheets: 'clients', 'positions', or 'candidates'.")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        errors.append(f"Database commit failed: {e}")

    return inserted, updated, errors
