from tortoise import models
from datetime import datetime

from ..models.auditBaseModel import AuditBasicMixin

class ModelAudit():
    created_by:int 
    updated_by:int
    created_by_name:str 
    updated_by_name:str
    created: datetime
    updated: datetime 

class AuditRecord():

    def set_creation_data(self, model: AuditBasicMixin, user):
        model.created = datetime.now()
        model.created_by = user["id"]
        model.created_by_name = user["full_name"]
  
    async def audit_for_create_dict(self,user)->ModelAudit:
        return {
            "created": datetime.now(),
            "created_by": user["id"],
            "created_by_name": user["full_name"]            
        }
    
    async def audit_for_update_dict(self,user)->ModelAudit:
        return {
            "updated": datetime.now(),
            "updated_by": user["id"],
            "updated_by_user": user["full_name"]            
        }

    async def audit_values_for_create(self,user)->ModelAudit:
        model = ModelAudit()
        model.created = datetime.now()
        model.created_by = user["id"]
        model.created_by_name = user["full_name"]
        return model
    
    
    async def audit_values_for_update(self,user)->ModelAudit:
        model = ModelAudit()
        model.updated = datetime.now()
        model.updated_by = user["id"]
        model.updated_by_name = user["full_name"]
        return model