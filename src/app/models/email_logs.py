from tortoise.models import Model
from tortoise import fields

class EmailLog(Model):
    id              = fields.IntField(pk=True)
    to_email        = fields.CharField(max_length=255)
    subject         = fields.CharField(max_length=255)
    status          = fields.CharField(max_length=50, default="pending")  # pending, sent, failed
    error_message   = fields.TextField(null=True)
    retry_count     = fields.IntField(default=0)
    notified        = fields.BooleanField(default=False)  # Notifica solo una vez
    created_at      = fields.DatetimeField(auto_now_add=True)
    updated_at      = fields.DatetimeField(auto_now=True)

    numero_documento  = fields.CharField(max_length=150, null=True)

    id_factura = fields.ForeignKeyField(
        "models.Factura",
        related_name="email_logs_factura",
        source_field="id_factura",  # 👈 NOMBRE REAL EN BD
        null=True,
        on_delete=fields.SET_NULL
    )

    id_user = fields.ForeignKeyField(
        "models.User",
        related_name="email_logs_user",
        source_field="id_user",
        null=True,
        on_delete=fields.SET_NULL
    )

    id_notacredito = fields.ForeignKeyField(
        "models.NotaCreditoModel",
        related_name="email_logs_notacredito",
        source_field="id_notacredito",
        null=True,
        on_delete=fields.SET_NULL
    )

    id_retencion = fields.ForeignKeyField(
        "models.RetentionModel",
        related_name="email_logs_retencion",
        source_field="id_retencion",
        null=True,
        on_delete=fields.SET_NULL
    )

    id_liquidacioncompra = fields.ForeignKeyField(
        "models.LiquidacionCompraModel",
        related_name="email_logs_liquidacioncompra",
        source_field="id_liquidacioncompra",
        null=True,
        on_delete=fields.SET_NULL
    )

    id_guiaremision = fields.ForeignKeyField(
        "models.GuiaRemisionModel",
        related_name="email_logs_guiaremision",
        source_field="id_guiaremision",
        null=True,
        on_delete=fields.SET_NULL
    )

    id_notadebito = fields.ForeignKeyField(
        "models.NotaDebitoModel",
        related_name="email_logs_notadebito",
        source_field="id_notadebito",
        null=True,
        on_delete=fields.SET_NULL
    )

    class Meta:
        table = "email_logs"
