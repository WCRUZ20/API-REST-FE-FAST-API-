from tortoise import models, fields
from .auditBaseModel import AuditBasicMixin

class RetentionModel(AuditBasicMixin):
    class Meta:
        table = "retenciones_clientes"

    id                  = fields.IntField(pk=True)
    ruc_emisor          = fields.CharField(max_length=15)
    ruc_receptor        = fields.CharField(max_length=15)
    user                = fields.ForeignKeyField('models.User', related_name='retenciones_clientes', on_delete=fields.NO_ACTION)
    factura_relacionada = fields.ForeignKeyField('models.Factura', related_name='retenciones', on_delete=fields.CASCADE)
    numero_retencion    = fields.CharField(max_length=50)
    clave_acceso        = fields.CharField(max_length=100, unique=True)
    numero_autorizacion = fields.CharField(max_length=100, unique=True)
    fecha_emision       = fields.DatetimeField()
    fecha_autorizacion  = fields.DatetimeField()
    ruta_xml            = fields.CharField(max_length=150)
    ruta_pdf            = fields.CharField(max_length=150)
    estado              = fields.CharField(max_length=100, default="NO ENVIADO")
    estado_sap          = fields.IntField(default=0)
    estado_sri          = fields.IntField(default=0)
    mensaje_sri         = fields.CharField(max_length=150, null=True)
    numero_transaccion  = fields.IntField(null=True)