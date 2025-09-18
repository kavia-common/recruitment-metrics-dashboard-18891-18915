# Tests for backend_api

- Test suite uses pytest.
- Database is mocked to SQLite via patched Config.sqlalchemy_uri for isolated testing.
- Use Flask's test client to hit endpoints.

Run:
    cd backend_api
    pytest -q
