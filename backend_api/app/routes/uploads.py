from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from ..schemas import UploadResultSchema
from ..services import process_excel_upload

blp = Blueprint(
    "Uploads",
    "uploads",
    url_prefix="/uploads",
    description="Excel upload endpoints"
)

@blp.route("/excel")
class ExcelUpload(MethodView):
    @blp.response(200, UploadResultSchema)
    def post(self):
        """Upload Excel file with candidate, client, and position data."""
        if "file" not in request.files:
            blp.abort(400, message="Missing file in form-data under key 'file'")
        f = request.files["file"]
        inserted, updated, errors = process_excel_upload(f)
        return {"inserted": inserted, "updated": updated, "errors": errors}
