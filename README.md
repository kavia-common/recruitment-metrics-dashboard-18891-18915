# recruitment-metrics-dashboard-18891-18915

Backend API
- Flask + flask-smorest (OpenAPI docs at /docs)
- PostgreSQL via SQLAlchemy
- Endpoints: /candidates, /interviews, /clients, /clients/<id>/positions, /metrics/summary, /metrics/notifications, /uploads/excel, and root / for health.

Run locally
- cd backend_api
- cp .env.example .env (and set variables to match database_postgresql container)
- python run.py (default port 3001)

OpenAPI
- cd backend_api
- python generate_openapi.py (writes interfaces/openapi.json)

Notes
- Ensure database_postgresql is running (port 5000 by default) and environment variables align with it.
