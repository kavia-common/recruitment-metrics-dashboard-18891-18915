# Backend API - Recruitment Metrics

This backend provides a secure API for the React dashboard to communicate with the PostgreSQL database.

Tech stack:
- Flask 3 + flask-smorest (OpenAPI at /docs)
- SQLAlchemy + psycopg3 for PostgreSQL
- CORS enabled for development
- Pandas + openpyxl for Excel uploads
- Optional SMTP email notifications

Key endpoints
- GET /            -> Health check
- /candidates      -> List, create, get, update, delete
- /interviews      -> List, create, get, update, delete
- /clients         -> List, create, get, update, delete
- /clients/<id>/positions and /clients/positions/<id>
- /metrics/summary -> KPI metrics for dashboard
- /metrics/notifications -> Simple notification feed
- POST /uploads/excel -> Upload Excel workbook to upsert data

Environment
- Use the following environment variables to configure PostgreSQL:
  - POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT
- Optional SMTP:
  - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS, SMTP_USE_SSL, NOTIFY_EMAIL_FROM, NOTIFY_EMAIL_TO

Run
- python run.py (binds 0.0.0.0:3001 by default; override PORT)
- Generate OpenAPI spec: python generate_openapi.py

Notes
- For CI/tests, the app uses SQLite via test fixtures and does not require a running Postgres.
- Ensure the database_postgresql container has started and that env variables match its configuration.
