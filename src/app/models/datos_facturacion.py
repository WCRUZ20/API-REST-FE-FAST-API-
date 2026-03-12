from tortoise import fields
from .auditBaseModel import AuditBasicMixin

class Datos_Facturacion(AuditBasicMixin):
    class Meta:
        table = "sec_datos_facturacion"

    id                      = fields.IntField(pk=True)
    user                    = fields.ForeignKeyField('models.User', related_name='sec_datos_facturacion')
    ruc                     = fields.CharField(max_length=13, unique = True)
    razon_social            = fields.CharField(max_length=50)
    nombre_comercial        = fields.CharField(max_length=150, null = True)
    direccion               = fields.CharField(max_length=150)
    obligado_contabilidad   = fields.CharField(max_length=5)
    telefono                = fields.CharField(max_length=150, null = True)
    nombre_firma            = fields.CharField(max_length=150, null=True)
    password_sign           = fields.CharField(max_length=150, null=True)
    ruta_logo               = fields.CharField(max_length=100, null = True)