from tortoise import models, fields
from .auditBaseModel import AuditBasicMixin

class User(AuditBasicMixin):
    class Meta:
        table = "sec_users"

    id              = fields.IntField(pk=True)
    identificacion  = fields.CharField(max_length=15)
    usuario         = fields.CharField(max_length=150, unique=True)
    email           = fields.CharField(max_length=50)
    password        = fields.BinaryField()
    full_name       = fields.CharField(max_length=150)
    active          = fields.BooleanField()
    profile         = fields.ForeignKeyField('models.Profile', related_name='sec_users')