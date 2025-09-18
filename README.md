# recruitment-metrics-dashboard-18891-18915

Backend API
- Flask + flask-smorest (OpenAPI docs at /docs)
- PostgreSQL via SQLAlchemy
- Endpoints: /candidates, /interviews, /clients, /clients/<id>/positions, /metrics/summary, /metrics/notifications, /uploads/excel, and root / for health.

Environment
- Configure database using env vars (see backend_api/.env.example).

Development
- Start backend: python run.py
- Generate OpenAPI: python generate_openapi.py