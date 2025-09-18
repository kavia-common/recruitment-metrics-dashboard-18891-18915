from flask.views import MethodView
from flask_smorest import Blueprint

from ..extensions import db
from ..models import metrics_summary, Position, PositionStatus, Candidate, CandidateStatus
from ..schemas import MetricsSchema, NotificationSchema

blp = Blueprint(
    "Metrics",
    "metrics",
    url_prefix="/metrics",
    description="KPI metrics and notifications"
)

@blp.route("/summary")
class MetricsSummary(MethodView):
    @blp.response(200, MetricsSchema)
    def get(self):
        """Return KPI summary for dashboard."""
        return metrics_summary(db.session)

@blp.route("/notifications")
class Notifications(MethodView):
    @blp.response(200, NotificationSchema(many=True))
    def get(self):
        """Return simple notifications regarding open/closed positions and hiring."""
        notifs = []

        open_positions = db.session.query(Position).filter(Position.status == PositionStatus.OPEN).count()
        if open_positions > 0:
            notifs.append({"type": "info", "message": f"{open_positions} positions currently open", "meta": {"count": open_positions}})

        closed_positions = db.session.query(Position).filter(Position.status == PositionStatus.CLOSED).count()
        if closed_positions > 0:
            notifs.append({"type": "success", "message": f"{closed_positions} positions closed", "meta": {"count": closed_positions}})

        pending_offers = db.session.query(Candidate).filter(Candidate.status == CandidateStatus.OFFERED).count()
        if pending_offers > 0:
            notifs.append({"type": "warning", "message": f"{pending_offers} offers pending response", "meta": {"count": pending_offers}})

        return notifs
