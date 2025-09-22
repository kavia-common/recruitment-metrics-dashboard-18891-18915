from flask import Flask, request
from flask_cors import CORS
from flask_smorest import Api, Blueprint
from .config import Config
from .extensions import db, ma
from .routes.health import blp as health_blp
from .routes.candidates import blp as candidates_blp
from .routes.interviews import blp as interviews_blp
from .routes.clients import blp as clients_blp
from .routes.metrics import blp as metrics_blp
from .routes.uploads import blp as uploads_blp

# Optional: verify psycopg2 import availability early for clearer startup diagnostics.
try:
    import psycopg2  # type: ignore  # noqa: F401
except Exception:
    # Do not hard fail; tests may use SQLite override. This ensures import path is exercised.
    pass

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})

# OpenAPI / Ocean Professional metadata
app.config["API_TITLE"] = "Recruitment Metrics API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
# Serve docs under /api/docs so that API base can live under /api
app.config["OPENAPI_URL_PREFIX"] = "/api/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Database configuration
cfg = Config()
app.config["SQLALCHEMY_DATABASE_URI"] = cfg.sqlalchemy_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
ma.init_app(app)

# Register API (existing routes kept without /api prefix for tests/back-compat)
api = Api(app)
api.register_blueprint(health_blp)
api.register_blueprint(candidates_blp)
api.register_blueprint(interviews_blp)
api.register_blueprint(clients_blp)
api.register_blueprint(metrics_blp)
api.register_blueprint(uploads_blp)

# Add a thin '/api' shim blueprint that forwards to existing logic expected by the frontend.
api_blp = Blueprint(
    "APIPrefixShim",
    "api_prefix",
    url_prefix="/api",
    description="Shim endpoints under /api to match frontend expectations",
)

# PUBLIC_INTERFACE
@api_blp.route("/health")
def api_health():
    """Health check under /api/health to match frontend."""
    return {"message": "Healthy"}

# Provide /api/candidates mapping that mirrors GET /candidates behavior.
from .models import Candidate
from .schemas import CandidateSchema
from .services import paginate, apply_candidate_filters

# PUBLIC_INTERFACE
@api_blp.route("/candidates", methods=["GET"])
def api_candidates_list():
    """List candidates via /api/candidates (shim). Supports the same query params."""
    query = Candidate.query
    query = apply_candidate_filters(query, request.args)
    items, meta = paginate(query.order_by(Candidate.created_at.desc()), request.args.get("page", 1), request.args.get("page_size", 20))
    return {"items": CandidateSchema(many=True).dump(items), "meta": meta}

api.register_blueprint(api_blp)

# Ensure tables exist (simple bootstrap for this project)
with app.app_context():
    try:
        db.create_all()
    except Exception:
        # If database is not reachable, app will still start; operations will fail with proper errors.
        pass
