from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Candidate, CandidateStatus
from ..schemas import CandidateSchema, PaginationSchema
from ..services import paginate, apply_candidate_filters
from ..email_utils import send_email, get_default_notification_recipients

blp = Blueprint(
    "Candidates",
    "candidates",
    url_prefix="/candidates",
    description="Operations related to candidates. Creates will trigger optional email notifications when configured (SMTP_HOST, NOTIFY_EMAIL_FROM)."
)

@blp.route("/")
class CandidatesList(MethodView):
    @blp.response(200, CandidateSchema(many=True), description="List candidates")
    @blp.alt_response(200, schema=PaginationSchema, description="Pagination metadata injected in headers")
    def get(self):
        """List candidates with filters and pagination."""
        query = Candidate.query
        query = apply_candidate_filters(query, request.args)
        items, meta = paginate(query.order_by(Candidate.created_at.desc()), request.args.get("page", 1), request.args.get("page_size", 20))
        # Flask-smorest can't return headers via schema easily; include meta in X-Pagination header-like JSON field
        return {"items": CandidateSchema(many=True).dump(items), "meta": meta}

    @blp.arguments(CandidateSchema)
    @blp.response(201, CandidateSchema, description="Created candidate and optionally notifies via email")
    def post(self, json_data):
        """Create a candidate.

        Notification behavior:
        - If email settings are configured, sends an email to NOTIFY_EMAIL_TO (if set) announcing a new application.
        """
        cand = Candidate(**json_data)
        db.session.add(cand)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")

        # Attempt email notification (non-blocking failure)
        recipients = get_default_notification_recipients()
        if recipients:
            subject = f"New candidate applied: {cand.full_name}"
            body = (
                f"A new candidate has applied.\n\n"
                f"Name: {cand.full_name}\n"
                f"Email: {cand.email or 'N/A'}\n"
                f"Status: {cand.status.value}\n"
                f"Source: {cand.source or 'N/A'}\n"
            )
            send_email(subject, body, recipients)

        return cand

@blp.route("/<int:candidate_id>")
class CandidateDetail(MethodView):
    @blp.response(200, CandidateSchema, description="Get candidate")
    def get(self, candidate_id: int):
        """Retrieve candidate by ID."""
        cand = Candidate.query.get_or_404(candidate_id)
        return cand

    @blp.arguments(CandidateSchema(partial=True))
    @blp.response(200, CandidateSchema, description="Updated candidate (may trigger email on key status changes)")
    def patch(self, json_data, candidate_id: int):
        """Update candidate by ID.

        Notification behavior:
        - If status changes to 'hired' or 'rejected' and email is configured, notify default recipients.
        """
        cand = Candidate.query.get_or_404(candidate_id)
        old_status = cand.status
        for k, v in json_data.items():
            setattr(cand, k, v)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")

        # Email on key status changes
        new_status = cand.status
        if old_status != new_status and new_status in (CandidateStatus.HIRED, CandidateStatus.REJECTED):
            recipients = get_default_notification_recipients()
            if recipients:
                status_text = new_status.value
                subject = f"Candidate {status_text}: {cand.full_name}"
                body = (
                    f"Candidate status updated.\n\n"
                    f"Name: {cand.full_name}\n"
                    f"Email: {cand.email or 'N/A'}\n"
                    f"New Status: {status_text}\n"
                )
                send_email(subject, body, recipients)

        return cand

    @blp.response(204)
    def delete(self, candidate_id: int):
        """Delete candidate by ID."""
        cand = Candidate.query.get_or_404(candidate_id)
        db.session.delete(cand)
        db.session.commit()
        return ""
