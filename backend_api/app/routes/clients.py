from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Client, Position
from ..schemas import ClientSchema, PositionSchema
from ..services import paginate, apply_client_filters

blp = Blueprint(
    "Clients",
    "clients",
    url_prefix="/clients",
    description="Operations related to clients and positions"
)

@blp.route("/")
class ClientsList(MethodView):
    def get(self):
        """List clients with filters and pagination."""
        query = Client.query
        query = apply_client_filters(query, request.args)
        items, meta = paginate(query.order_by(Client.created_at.desc()), request.args.get("page", 1), request.args.get("page_size", 20))
        return {"items": ClientSchema(many=True).dump(items), "meta": meta}

    @blp.arguments(ClientSchema)
    @blp.response(201, ClientSchema)
    def post(self, json_data):
        """Create client."""
        obj = Client(**json_data)
        db.session.add(obj)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")
        return obj

@blp.route("/<int:client_id>")
class ClientDetail(MethodView):
    @blp.response(200, ClientSchema)
    def get(self, client_id: int):
        """Get client by ID."""
        return Client.query.get_or_404(client_id)

    @blp.arguments(ClientSchema(partial=True))
    @blp.response(200, ClientSchema)
    def patch(self, json_data, client_id: int):
        """Update client by ID."""
        obj = Client.query.get_or_404(client_id)
        for k, v in json_data.items():
            setattr(obj, k, v)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            blp.abort(400, message=f"Integrity error: {e.orig}")
        return obj

    @blp.response(204)
    def delete(self, client_id: int):
        """Delete client by ID."""
        obj = Client.query.get_or_404(client_id)
        db.session.delete(obj)
        db.session.commit()
        return ""

@blp.route("/<int:client_id>/positions")
class ClientPositions(MethodView):
    def get(self, client_id: int):
        """List positions for a client."""
        positions = Position.query.filter_by(client_id=client_id).order_by(Position.created_at.desc()).all()
        return {"items": PositionSchema(many=True).dump(positions)}

    @blp.arguments(PositionSchema)
    @blp.response(201, PositionSchema)
    def post(self, json_data, client_id: int):
        """Create position for a client."""
        json_data["client_id"] = client_id
        obj = Position(**json_data)
        db.session.add(obj)
        db.session.commit()
        return obj

@blp.route("/positions/<int:position_id>")
class PositionDetail(MethodView):
    @blp.response(200, PositionSchema)
    def get(self, position_id: int):
        """Get position by ID."""
        return Position.query.get_or_404(position_id)

    @blp.arguments(PositionSchema(partial=True))
    @blp.response(200, PositionSchema)
    def patch(self, json_data, position_id: int):
        """Update position by ID."""
        obj = Position.query.get_or_404(position_id)
        for k, v in json_data.items():
            setattr(obj, k, v)
        db.session.commit()
        return obj

    @blp.response(204)
    def delete(self, position_id: int):
        """Delete position by ID."""
        obj = Position.query.get_or_404(position_id)
        db.session.delete(obj)
        db.session.commit()
        return ""
