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
            "Default max upload size is 10 MB. Returns the number of inserted and updated rows, and a list of errors (if any)."
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
                "description": "Bad Request. Missing file, invalid file type, or failed Excel parsing.",
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
        # Some browsers may send application/octet-stream; allow if extension is valid
        valid_mime = (
            content_type.startswith("application/vnd.openxmlformats")
            or "ms-excel" in content_type
            or (content_type == "application/octet-stream" and allowed_ext)
        )
        if not (allowed_ext or valid_mime):
            blp.abort(
                400,
                message="Invalid file type. Please upload an Excel file with extension .xlsx or .xls under form field 'file'."
            )

        # Optional: enforce a sane max size (10 MB default)
        max_size_bytes = 10 * 1024 * 1024
        content_length = request.content_length or getattr(f, "content_length", None)
        if content_length and content_length > max_size_bytes:
            blp.abort(400, message="Uploaded file is too large. Maximum allowed size is 10 MB.")

        # Ensure stream is at the beginning before reading
        try:
            f.stream.seek(0)
        except Exception:
            # If seek fails, continue; read will still attempt from current position
            pass

        # Delegate to service. It returns graceful error list if parsing fails.
        try:
            inserted, updated, errors = process_excel_upload(f)
        except Exception as e:
            # Defensive: convert unexpected errors to a readable message
            blp.abort(400, message=f"Failed to process Excel upload: {e}")

        # Return 200 with details and errors array for client-side rendering
        return {"inserted": inserted, "updated": updated, "errors": errors}
