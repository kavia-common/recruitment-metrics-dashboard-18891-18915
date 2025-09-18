import datetime as dt

def _valid_candidate_payload():
    return {
        "full_name": "Jane Roe",
        "email": "jane.roe@example.com",
        "phone": "555-2222",
        "status": "applied",
        "source": "LinkedIn",
        "position_id": None,
        "applied_on": dt.date.today().isoformat(),
    }


def test_list_candidates_empty(client):
    res = client.get("/candidates/")
    assert res.status_code == 200
    data = res.get_json()
    assert "items" in data and "meta" in data
    assert data["items"] == []
    assert data["meta"]["page"] == 1


def test_create_candidate_ok(client):
    payload = _valid_candidate_payload()
    res = client.post("/candidates/", json=payload)
    assert res.status_code == 201, res.get_data(as_text=True)
    data = res.get_json()
    assert data["id"] > 0
    assert data["full_name"] == payload["full_name"]
    assert data["status"] == payload["status"]


def test_create_candidate_duplicate_email(client):
    payload = _valid_candidate_payload()
    res1 = client.post("/candidates/", json=payload)
    assert res1.status_code == 201
    # Duplicate by email should raise integrity error due to unique constraint
    payload2 = _valid_candidate_payload()
    payload2["full_name"] = "Another Name"
    res2 = client.post("/candidates/", json=payload2)
    assert res2.status_code == 400
    data = res2.get_json()
    assert "Integrity error" in data.get("message", "")


def test_get_update_delete_candidate_flow(client):
    # Create
    res = client.post("/candidates/", json=_valid_candidate_payload())
    cid = res.get_json()["id"]

    # Get
    g = client.get(f"/candidates/{cid}")
    assert g.status_code == 200
    assert g.get_json()["id"] == cid

    # Patch
    p = client.patch(f"/candidates/{cid}", json={"status": "hired"})
    assert p.status_code == 200
    assert p.get_json()["status"] == "hired"

    # Delete
    d = client.delete(f"/candidates/{cid}")
    assert d.status_code == 204

    # 404 after delete
    g2 = client.get(f"/candidates/{cid}")
    assert g2.status_code == 404


def test_candidate_filters_and_pagination(client):
    # seed several candidates
    for i in range(25):
        payload = {
            "full_name": f"User {i}",
            "email": f"user{i}@example.com",
            "phone": None,
            "status": "applied" if i % 2 == 0 else "rejected",
            "source": "Referral" if i % 3 == 0 else "Job Board",
            "position_id": None,
            "applied_on": dt.date.today().isoformat(),
        }
        client.post("/candidates/", json=payload)

    # page 2 with page_size 10
    r = client.get("/candidates/?page=2&page_size=10&status=applied&q=user")
    assert r.status_code == 200
    data = r.get_json()
    assert data["meta"]["page"] == 2
    assert "items" in data
    # All names contain 'User', filtered status=applied, ensure we have items
    assert len(data["items"]) >= 1
