from tortoise import fields
from tortoise.models import Model


class ApiRequestLog(Model):
    id = fields.IntField(pk=True)
    endpoint = fields.CharField(max_length=255)
    method = fields.CharField(max_length=10)
    request_at = fields.DatetimeField(auto_now_add=True)
    response_code = fields.IntField()
    response_detail = fields.TextField(null=True)
    user_identifier = fields.CharField(max_length=150, null=True)

    class Meta:
        table = "api_request_logs"