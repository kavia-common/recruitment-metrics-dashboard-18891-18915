from marshmallow import fields, validate
from .extensions import ma
from .models import CandidateStatus, InterviewStage, PositionStatus

class PaginationSchema(ma.Schema):
    total = fields.Int(description="Total number of items")
    total_pages = fields.Int(description="Total pages")
    page = fields.Int(description="Current page index (1-based)")
    page_size = fields.Int(description="Page size")

class ClientSchema(ma.Schema):
    id = fields.Int(dump_only=True, description="Client ID")
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200), description="Client name")
    industry = fields.Str(allow_none=True, description="Industry")
    account_manager = fields.Str(allow_none=True, description="Account manager")
    status = fields.Str(required=True, validate=validate.OneOf([e.value for e in PositionStatus]), description="Position status for client accounts")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class PositionSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, description="Position title")
    status = fields.Str(required=True, validate=validate.OneOf([e.value for e in PositionStatus]), description="Position status")
    client_id = fields.Int(required=True, description="Owning client ID")
    location = fields.Str(allow_none=True)
    salary_min = fields.Float(allow_none=True)
    salary_max = fields.Float(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class CandidateSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    full_name = fields.Str(required=True, description="Candidate full name")
    email = fields.Email(allow_none=True, description="Email")
    phone = fields.Str(allow_none=True, description="Phone")
    status = fields.Str(required=True, validate=validate.OneOf([e.value for e in CandidateStatus]), description="Candidate pipeline status")
    source = fields.Str(allow_none=True, description="Source of candidate")
    position_id = fields.Int(allow_none=True, description="Applied position ID")
    applied_on = fields.Date(allow_none=True, description="Application date")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class InterviewSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    candidate_id = fields.Int(required=True, description="Candidate ID")
    stage = fields.Str(required=True, validate=validate.OneOf([e.value for e in InterviewStage]), description="Interview stage")
    scheduled_at = fields.DateTime(required=True, description="Scheduled date/time")
    result = fields.Str(allow_none=True, description="Result status (pass/fail/no_show/pending)")
    interviewer = fields.Str(allow_none=True, description="Interviewer name")
    notes = fields.Str(allow_none=True, description="Notes")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class UploadResultSchema(ma.Schema):
    inserted = fields.Int(required=True, description="Rows inserted")
    updated = fields.Int(required=True, description="Rows updated")
    errors = fields.List(fields.Str(), description="Error messages")

class NotificationSchema(ma.Schema):
    type = fields.Str(required=True, description="Notification type")
    message = fields.Str(required=True, description="Notification text")
    meta = fields.Dict(keys=fields.Str(), values=fields.Raw(), description="Extra metadata")

class MetricsSchema(ma.Schema):
    total_candidates = fields.Int()
    hired_candidates = fields.Int()
    open_positions = fields.Int()
    closed_positions = fields.Int()
    upcoming_interviews = fields.Int()
