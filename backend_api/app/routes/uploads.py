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
    # PUBLIC_INTERFACE
    @blp.response(200, UploadResultSchema, description="Successful Excel upload processing result")
    @blp.doc(
        summary="Upload Excel file with candidate, client, and position data.",
        description=(
            "Accepts a multipart/form-data POST with a single file field named 'file'.\n"
            "The Excel workbook may contain sheets: 'clients', 'positions', and 'candidates'.\n"
            "Expected columns:\n"
            "- clients: [name, industry, account_manager, status]\n"
            "- positions: [title, status, client_name, location, salary_min, salary_max]\n"
            "- candidates: [full_name, email, phone, status, source, position_title, client_name, applied_on]\n\n"
            "Returns the number of inserted and updated rows, and a list of errors (if any)."
        ),
        requestBody={
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "file": {
                                "type": "string",
                                "format": "binary",
                                "description": "Excel file (.xlsx recommended) containing recruitment data"
                            }
                        },
                        "required": ["file"]
                    }
                }
            }
        },
        responses={
            400: {
                "description": "Bad Request. Missing file or invalid file type.",
            }
        },
        operationId="uploadExcelFile",
        tags=["Uploads"],
    )
    def post(self):
        """
        Upload Excel file with candidate, client, and position data.

        Parameters:
            - multipart/form-data field 'file': The Excel file (.xlsx recommended).

        Returns:
            JSON object with keys:
            - inserted: number of created records across entities
            - updated: number of updated records
            - errors: list of parsing or database errors captured during processing
        """
        # Validate presence of the file field
        if "file" not in request.files:
            blp.abort(400, message="Missing file in form-data under key 'file'")

        f = request.files["file"]

        # Basic filename/content-type validation for clearer client guidance
        filename = (f.filename or "").lower()
        allowed_ext = (filename.endswith(".xlsx") or filename.endswith(".xls"))
        content_type = (f.mimetype or "").lower()

        # Common Excel MIME types include:
        # - application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (.xlsx)
        # - application/vnd.ms-excel (.xls)
        if not allowed_ext and not content_type.startswith("application/vnd.openxmlformats") and "ms-excel" not in content_type:
            blp.abort(
                400,
                message="Invalid file type. Please upload an Excel file with extension .xlsx or .xls under form field 'file'."
            )

        # Delegate to service. It returns graceful error list if parsing fails.
        inserted, updated, errors = process_excel_upload(f)

        # If parsing failed entirely, surface as 400 with details for clients
        if inserted == 0 and updated == 0 and errors:
            # Still return 200 by default behavior? Prefer 200 with errors array so client can show feedback.
            # However, many clients expect 200 to indicate success path. We'll keep 200 and include errors.
            pass

        return {"inserted": inserted, "updated": updated, "errors": errors}
