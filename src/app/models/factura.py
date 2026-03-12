from tortoise import fields
from .auditBaseModel import AuditBasicMixin

class Factura(AuditBasicMixin):
    class Meta:
        table = "facturas_clientes"

    id                  = fields.IntField(pk=True)
    ruc_emisor          = fields.CharField(max_length=15)
    ruc_receptor        = fields.CharField(max_length=15)
    user                = fields.ForeignKeyField('models.User', related_name='facturas_clientes', on_delete=fields.NO_ACTION)
    numero_factura      = fields.CharField(max_length=50)
    clave_acceso        = fields.CharField(max_length=100, unique=True)
    numero_autorizacion = fields.CharField(max_length=100, unique=True)
    fecha_emision       = fields.DatetimeField()
    subtotal            = fields.DecimalField(max_digits=10, decimal_places=4)
    iva                 = fields.DecimalField(max_digits=10, decimal_places=4)
    total               = fields.DecimalField(max_digits=10, decimal_places=4)
    fecha_autorizacion  = fields.DatetimeField()
    ruta_xml            = fields.CharField(max_length=150)
    ruta_pdf            = fields.CharField(max_length=150)
    estado              = fields.CharField(max_length=100, default="NO ENVIADO")
    estado_sap          = fields.IntField(default=0)  # 0: No enviado, 1: Enviado, 2: Autorizado, 3: No autorizado, 4: Firma inválida, 5: En proceso, 6: Devuelta, 11: Anulado
    estado_sri          = fields.IntField(default=0)  # Estado del SRI
    mensaje_sri         = fields.CharField(max_length=255, null=True, blank=True)
    numero_transaccion  = fields.IntField(default=0, null=True)  # Número de transacción
    """ 
    guia_remision       = fields.CharField(max_length=50, null=True, blank=True)  # Número de guía de remisión
    incoTermFactura     = fields.CharField(max_length=50, null=True, blank=True)  # Incoterm de la factura
    paisOrigen          = fields.CharField(max_length=50, null=True, blank=True)  # País de origen
    paisDestino         = fields.CharField(max_length=50, null=True, blank=True)  # País de destino """