from tortoise import models, fields
from .auditBaseModel import AuditBasicMixin

class GuiaRemisionModel(AuditBasicMixin):
    class Meta:
        table = "guia_remision"

    id                  = fields.IntField(pk=True)
    ruc_emisor          = fields.CharField(max_length=15)
    ruc_receptor        = fields.CharField(max_length=15)
    ruc_transportista   = fields.CharField(max_length=15)
    motivo_traslado     = fields.CharField(max_length=150)
    placa               = fields.CharField(max_length=10)
    pto_partida         = fields.CharField(max_length=150)
    pto_llegada         = fields.CharField(max_length=150)
    ini_traslado        = fields.DatetimeField()
    fin_traslado        = fields.DatetimeField()
    user                = fields.ForeignKeyField('models.User', related_name='guia_remision', on_delete=fields.NO_ACTION)
    numero_guiaremision = fields.CharField(max_length=50)
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