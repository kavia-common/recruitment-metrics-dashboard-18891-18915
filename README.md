# recruitment-metrics-dashboard-18891-18915

Backend API
- Flask + flask-smorest (OpenAPI docs at /docs)
- PostgreSQL via SQLAlchemy
- Endpoints: 
  - /candidates, /candidates/<id>
  - /clients, /clients/<id>, /clients/<client_id>/positions, /clients/positions/<position_id>
  - /interviews, /interviews/<id>
  - /metrics/summary, /metrics/notifications
  - /uploads/excel (multipart/form-data with `file`)
  - root `/` for health.
- Optional email notifications via SMTP for key events (new candidate, interview scheduled, position closed)

Environment
- Configure database using env vars (see backend_api/.env.example).
- Optional SMTP settings for notifications (see backend_api/.env.example): SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS, SMTP_USE_SSL, NOTIFY_EMAIL_FROM, NOTIFY_EMAIL_TO

Quick Start (Preview)
1) Ensure PostgreSQL is available. This repository provides a helper in:
   recruitment-metrics-dashboard-18891-18913/database_postgresql
   - Run `startup.sh` there to start a local Postgres on port 5000 and create DB/user.
   - The connection string is written to db_connection.txt:
     psql postgresql://appuser:dbuser123@localhost:5000/myapp

2) Configure backend environment:
   - Copy backend_api/.env.example to backend_api/.env (if supported by your runner) and ensure:
       POSTGRES_URL=localhost
       POSTGRES_USER=appuser
       POSTGRES_PASSWORD=dbuser123
       POSTGRES_DB=myapp
       POSTGRES_PORT=5000
     Alternatively, export these environment variables in your shell or CI.

3) Install backend dependencies:
   cd backend_api
   pip install -r requirements.txt

4) Run the API:
   python run.py
   - The API binds on 0.0.0.0:3001 by default (override with PORT env var).
   - CORS is enabled for all origins for development convenience.

5) Explore API docs:
   http://localhost:3001/docs

6) Generate OpenAPI (optional, writes interfaces/openapi.json):
   python generate_openapi.py

Notes
- Tests use SQLite via runtime patching of the configuration for isolation (no Postgres required in tests).
- For Excel uploads, POST multipart/form-data to /uploads/excel with form field `file`.
- Email notifications are no-ops unless SMTP_HOST and NOTIFY_EMAIL_FROM are configured.