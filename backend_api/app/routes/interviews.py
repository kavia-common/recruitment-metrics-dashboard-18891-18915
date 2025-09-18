from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Interview
from ..schemas import InterviewSchema
from ..services import paginate, apply_interview_filters

blp = Blueprint(
    "Interviews",
    "interviews",
    url_prefix="/interviews",
    description="Operations related to interviews"
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
    @blp.response(201, InterviewSchema, description="Created interview")
    def post(self, json_data):
        """Create interview."""
        obj = Interview(**json_data)
        db.session.add(obj)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")
        return obj

@blp.route("/<int:interview_id>")
class InterviewDetail(MethodView):
    @blp.response(200, InterviewSchema, description="Get interview")
    def get(self, interview_id: int):
        """Retrieve interview by ID."""
        obj = Interview.query.get_or_404(interview_id)
        return obj

    @blp.arguments(InterviewSchema(partial=True))
    @blp.response(200, InterviewSchema, description="Updated interview")
    def patch(self, json_data, interview_id: int):
        """Update interview by ID."""
        obj = Interview.query.get_or_404(interview_id)
        for k, v in json_data.items():
            setattr(obj, k, v)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")
        return obj

    @blp.response(204)
    def delete(self, interview_id: int):
        """Delete interview by ID."""
        obj = Interview.query.get_or_404(interview_id)
        db.session.delete(obj)
        db.session.commit()
        return ""
