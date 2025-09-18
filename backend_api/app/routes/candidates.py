from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Candidate
from ..schemas import CandidateSchema, PaginationSchema
from ..services import paginate, apply_candidate_filters

blp = Blueprint(
    "Candidates",
    "candidates",
    url_prefix="/candidates",
    description="Operations related to candidates"
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
    @blp.response(201, CandidateSchema, description="Created candidate")
    def post(self, json_data):
        """Create a candidate."""
        cand = Candidate(**json_data)
        db.session.add(cand)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")
        return cand

@blp.route("/<int:candidate_id>")
class CandidateDetail(MethodView):
    @blp.response(200, CandidateSchema, description="Get candidate")
    def get(self, candidate_id: int):
        """Retrieve candidate by ID."""
        cand = Candidate.query.get_or_404(candidate_id)
        return cand

    @blp.arguments(CandidateSchema(partial=True))
    @blp.response(200, CandidateSchema, description="Updated candidate")
    def patch(self, json_data, candidate_id: int):
        """Update candidate by ID."""
        cand = Candidate.query.get_or_404(candidate_id)
        for k, v in json_data.items():
            setattr(cand, k, v)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")
        return cand

    @blp.response(204)
    def delete(self, candidate_id: int):
        """Delete candidate by ID."""
        cand = Candidate.query.get_or_404(candidate_id)
        db.session.delete(cand)
        db.session.commit()
        return ""
