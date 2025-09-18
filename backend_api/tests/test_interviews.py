import datetime as dt

def _interview_payload(candidate_id):
    return {
        "candidate_id": candidate_id,
        "stage": "technical",
        "scheduled_at": (dt.datetime.utcnow() + dt.timedelta(days=2)).isoformat() + "Z",
        "result": None,
        "interviewer": "Tech Lead",
        "notes": "Bring laptop",
    }


def _create_candidate(client):
    payload = {
        "full_name": "Mark Brown",
        "email": "mark@example.com",
        "phone": "555-3333",
        "status": "applied",
        "source": "Referral",
        "position_id": None,
        "applied_on": dt.date.today().isoformat(),
    }
    res = client.post("/candidates/", json=payload)
    return res.get_json()["id"]


def test_interviews_crud_and_filters(client):
    # Prepare candidate id
    cid = _create_candidate(client)

    # List empty
    r0 = client.get("/interviews/")
    assert r0.status_code == 200
    assert r0.get_json()["items"] == []

    # Create
    r1 = client.post("/interviews/", json=_interview_payload(cid))
    assert r1.status_code == 201
    iv_id = r1.get_json()["id"]

    # Get
    rg = client.get(f"/interviews/{iv_id}")
    assert rg.status_code == 200
    assert rg.get_json()["id"] == iv_id

    # Patch
    rp = client.patch(f"/interviews/{iv_id}", json={"result": "pass", "stage": "final"})
    assert rp.status_code == 200
    j = rp.get_json()
    assert j["result"] == "pass"
    assert j["stage"] == "final"

    # Filters
    flt = client.get("/interviews/?stage=final&result=pass")
    assert flt.status_code == 200
    assert len(flt.get_json()["items"]) >= 1

    # Delete
    rd = client.delete(f"/interviews/{iv_id}")
    assert rd.status_code == 204

    # 404 after delete
    rgone = client.get(f"/interviews/{iv_id}")
    assert rgone.status_code == 404
