def _client_payload():
    return {
        "name": "Globex Inc",
        "industry": "Finance",
        "account_manager": "Gary",
        "status": "open",
    }


def _position_payload(client_id):
    return {
        "title": "Backend Developer",
        "status": "open",
        "client_id": client_id,
        "location": "NYC",
        "salary_min": 80000,
        "salary_max": 120000,
    }


def test_clients_crud_and_positions(client):
    # List empty
    r0 = client.get("/clients/")
    assert r0.status_code == 200
    assert r0.get_json()["items"] == []

    # Create client
    r1 = client.post("/clients/", json=_client_payload())
    assert r1.status_code == 201
    client_id = r1.get_json()["id"]

    # Get client
    rg = client.get(f"/clients/{client_id}")
    assert rg.status_code == 200
    assert rg.get_json()["name"] == "Globex Inc"

    # Update client
    rp = client.patch(f"/clients/{client_id}", json={"industry": "FinTech"})
    assert rp.status_code == 200
    assert rp.get_json()["industry"] == "FinTech"

    # Add position under client
    rpos = client.post(f"/clients/{client_id}/positions", json=_position_payload(client_id))
    assert rpos.status_code == 201
    pos_id = rpos.get_json()["id"]

    # List client positions
    rplist = client.get(f"/clients/{client_id}/positions")
    assert rplist.status_code == 200
    items = rplist.get_json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == pos_id

    # Get position
    rpget = client.get(f"/clients/positions/{pos_id}")
    assert rpget.status_code == 200
    assert rpget.get_json()["title"] == "Backend Developer"

    # Update position
    rpp = client.patch(f"/clients/positions/{pos_id}", json={"status": "closed"})
    assert rpp.status_code == 200
    assert rpp.get_json()["status"] == "closed"

    # Delete position
    rpd = client.delete(f"/clients/positions/{pos_id}")
    assert rpd.status_code == 204

    # Delete client
    rd = client.delete(f"/clients/{client_id}")
    assert rd.status_code == 204

    # Confirm gone
    rgone = client.get(f"/clients/{client_id}")
    assert rgone.status_code == 404


def test_client_duplicate_name_error(client):
    # Create client
    r1 = client.post("/clients/", json=_client_payload())
    assert r1.status_code == 201
    # Duplicate name should fail with integrity error as name is unique
    r2 = client.post("/clients/", json=_client_payload())
    assert r2.status_code == 400
    assert "Integrity error" in r2.get_json().get("message", "")
