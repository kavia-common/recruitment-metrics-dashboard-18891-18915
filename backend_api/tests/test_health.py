def test_health_root_ok(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.get_json()
    assert data == {"message": "Healthy"}
