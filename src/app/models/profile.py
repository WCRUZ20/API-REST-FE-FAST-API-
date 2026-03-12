from tortoise import models, fields
from .auditBaseModel import AuditBasicMixin

class Profile(AuditBasicMixin):
    class Meta:
        table = "sec_profiles"
    

    id                  =    fields.IntField(pk=True)
    name                =    fields.CharField(max_length=50, unique=True)
    active              =    fields.BooleanField()
    