from tortoise import models, fields

class AuditBasicMixin(models.Model):

    created         = fields.DatetimeField()
    updated         = fields.DatetimeField(null=True)
    created_by      = fields.IntField()
    updated_by      = fields.IntField(null=True)
    updated_by_name = fields.CharField(max_length=150,null=True)
    created_by_name = fields.CharField(max_length=150,null=True)