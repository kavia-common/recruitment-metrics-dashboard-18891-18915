from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Interview
from ..schemas import InterviewSchema
from ..services import paginate, apply_interview_filters
from ..email_utils import send_email, get_default_notification_recipients

blp = Blueprint(
    "Interviews",
    "interviews",
    url_prefix="/interviews",
    description="Operations related to interviews. Creates will optionally send email notifications to default recipients."
)

@blp.route("/")
class InterviewsList(MethodView):
    @blp.response(200, InterviewSchema(many=True), description="List interviews")
    def get(self):
        """List interviews with filters and pagination."""
        query = Interview.query
        query = apply_interview_filters(query, request.args)
        items, meta = paginate(query.order_by(Interview.scheduled_at.desc()), request.args.get("page", 1), request.args.get("page_size", 20))
        return {"items": InterviewSchema(many=True).dump(items), "meta": meta}

    @blp.arguments(InterviewSchema)
    @blp.response(201, InterviewSchema, description="Created interview and optionally notifies via email")
    def post(self, json_data):
        """Create interview.

        Notification behavior:
        - If SMTP configured, sends notification about scheduled interview (stage and time).
        """
        obj = Interview(**json_data)
        db.session.add(obj)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")

        recipients = get_default_notification_recipients()
        if recipients:
            subject = f"Interview scheduled (stage: {obj.stage.value}) for candidate #{obj.candidate_id}"
            body = (
                f"An interview has been scheduled.\n\n"
                f"Candidate ID: {obj.candidate_id}\n"
                f"Stage: {obj.stage.value}\n"
                f"Scheduled At: {obj.scheduled_at}\n"
                f"Interviewer: {obj.interviewer or 'N/A'}\n"
            )
            send_email(subject, body, recipients)

        return obj

@blp.route("/<int:interview_id>")
class InterviewDetail(MethodView):
    @blp.response(200, InterviewSchema, description="Get interview")
    def get(self, interview_id: int):
        """Retrieve interview by ID."""
        obj = Interview.query.get_or_404(interview_id)
        return obj

    @blp.arguments(InterviewSchema(partial=True))
    @blp.response(200, InterviewSchema, description="Updated interview (may notify on stage/result changes)")
    def patch(self, json_data, interview_id: int):
        """Update interview by ID.

        Notification behavior:
        - If stage or result changes and SMTP is configured, notify default recipients.
        """
        obj = Interview.query.get_or_404(interview_id)
        old_stage = obj.stage
        old_result = obj.result
        for k, v in json_data.items():
            setattr(obj, k, v)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")

        changed = []
        if old_stage != obj.stage:
            changed.append(f"stage: {old_stage.value if old_stage else 'N/A'} -> {obj.stage.value if obj.stage else 'N/A'}")
        if old_result != obj.result:
            changed.append(f"result: {old_result or 'N/A'} -> {obj.result or 'N/A'}")

        if changed:
            recipients = get_default_notification_recipients()
            if recipients:
                subject = f"Interview updated for candidate #{obj.candidate_id}"
                body_lines = [
                    "Interview fields updated:",
                    *[f"- {line}" for line in changed],
                    "",
                    f"Scheduled At: {obj.scheduled_at}",
                    f"Interviewer: {obj.interviewer or 'N/A'}",
                ]
                body = "\n".join(body_lines)
                send_email(subject, body, recipients)

        return obj

    @blp.response(204)
    def delete(self, interview_id: int):
        """Delete interview by ID."""
        obj = Interview.query.get_or_404(interview_id)
        db.session.delete(obj)
        db.session.commit()
        return ""
