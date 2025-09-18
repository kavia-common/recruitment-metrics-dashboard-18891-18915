from .conftest import make_excel_bytes

def test_upload_without_file_fails(client):
    res = client.post("/uploads/excel")
    assert res.status_code == 400
    data = res.get_json()
    assert "Missing file" in data.get("message", "")


def test_upload_excel_success_flow(client):
    bio = make_excel_bytes()
    data = {
        "file": (bio, "import.xlsx"),
    }
    res = client.post("/uploads/excel", data=data, content_type="multipart/form-data")
    assert res.status_code == 200, res.get_data(as_text=True)
    body = res.get_json()
    assert "inserted" in body and "updated" in body and "errors" in body
    # After upload, clients endpoint should list the uploaded client
    cl = client.get("/clients/")
    assert cl.status_code == 200
    items = cl.get_json()["items"]
    assert any(c["name"] == "Widget Co" for c in items)
