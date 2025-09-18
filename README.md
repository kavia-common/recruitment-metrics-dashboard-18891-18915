# recruitment-metrics-dashboard-18891-18915

Backend API
- Flask + flask-smorest (OpenAPI docs at /docs)
- PostgreSQL via SQLAlchemy
- Endpoints: /candidates, /interviews, /clients, /clients/<id>/positions, /metrics/summary, /metrics/notifications, /uploads/excel, and root / for health.
- Optional email notifications via SMTP for key events (new candidate, interview scheduled, position closed)

Environment
- Configure database using env vars (see backend_api/.env.example).
- Optional SMTP settings for notifications (see backend_api/.env.example): SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS, SMTP_USE_SSL, NOTIFY_EMAIL_FROM, NOTIFY_EMAIL_TO

Development
- Start backend: python run.py
  - The API binds on 0.0.0.0:3001 by default (override with PORT env var).
  - CORS is enabled for all origins for development convenience.
- Generate OpenAPI: python generate_openapi.py