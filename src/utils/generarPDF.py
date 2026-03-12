import base64
import os
import httpx

from dotenv import dotenv_values
from jinja2 import Template
from weasyprint import HTML

from .codigoBarras import generar_codigo_barras_base64
from ..core.documentos_electronicos_core.schemas.schemas import FacturaSchema, GuiaSchema, LiquidacionCompraSchema, NotaCreditoSchema, RetencionSchema, NotaDebitoSchema
from ..app.models.model import Datos_Facturacion
from ..app.constans.enums import DocumentType, ImpositivoRetenido

UPLOAD_FOLDER = "src/assets/"

class PDFGenerator():
    def __init__(self, db):
        self.db = db
        self.config = {
            **dotenv_values('.env')
        }

    def generar_ride(self, invoice: FacturaSchema, claveAcceso: str, data_facturacion: Datos_Facturacion, fechaAutorizacion, issueDate):
        pathPDF = f"{self.config['DIR_FACTURAS']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
        ruta_logo_path = os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, invoice.campoAdicional1) if invoice.campoAdicional1 else (os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, data_facturacion.ruta_logo) if data_facturacion.ruta_logo else None)
        logo_base64 = None
        if ruta_logo_path:
            with open(ruta_logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        imagen_codigo_barras_base64 = generar_codigo_barras_base64(claveAcceso)
        datos_articulos = []
        detalles_keys_set = set()
        
        iva_0 = 0
        iva_15 = 0
        subtotal_iva_15 = 0
        subtotal_iva_0 = 0
        for ttImpuesto in invoice.infoFactura.totalConImpuestos:
            if ttImpuesto.codigo == "2":
                iva_15 += float(ttImpuesto.valor)
                subtotal_iva_15 = float(ttImpuesto.baseImponible)
            if ttImpuesto.codigo == "3":
                iva_0 += float(ttImpuesto.valor)
                subtotal_iva_0 = float(ttImpuesto.baseImponible)

        descuento_total = 0
        total_sin_impuestos = 0

        for detalle in invoice.detalles:
            descuento_total += float(detalle.descuento)
            total_sin_impuestos += float(detalle.precioTotalSinImpuesto)

            # Procesar detalles adicionales
            detalles_adicionales = {
                d.nombre: d.valor
                for d in getattr(detalle, "detallesAdicionales", [])
                if d.nombre and d.nombre.strip() != "-"
            }

            detalles_keys_set.update(detalles_adicionales.keys())

            dt = {
                "code": detalle.codigoPrincipal,
                "aux_code": detalle.codigoAuxiliar if detalle.codigoAuxiliar else "N/A",
                "quantity": detalle.cantidad,
                "description": detalle.descripcion,
                "unit_price": "$" + detalle.precioUnitario,
                "discount": "$" + detalle.descuento,
                "total_price": "$" + detalle.precioTotalSinImpuesto,
                "additional_details": detalles_adicionales
            }
            datos_articulos.append(dt)

        # Convertir infoAdicional a dict general
        additional_info_dict = {
            item.nombre: item.valor
            for item in invoice.infoAdicional
            if item.nombre and item.nombre.strip() != "-"
        } if invoice.infoAdicional else {}

        # Armar el JSON para renderizar
        data = {
            "documento": "Factura",
            "logo_url": logo_base64,
            "company_name": data_facturacion.razon_social,
            "company_address": data_facturacion.direccion,
            "accounting_required": data_facturacion.obligado_contabilidad,
            "company_ruc": data_facturacion.ruc,
            "invoice_number": f"{invoice.infoTributaria.estab}-{invoice.infoTributaria.ptoEmi}-{invoice.infoTributaria.secuencial}",
            "authorization_date": fechaAutorizacion,
            "environment": "PRUEBA" if invoice.infoTributaria.ambiente == "1" else "PRODUCCION",
            "issue": "Normal" if invoice.infoTributaria.tipoEmision == "1" else "Contingencia",
            "authorization_number": invoice.infoTributaria.claveAcceso,
            "barcode_url": imagen_codigo_barras_base64,
            "client_name": invoice.infoFactura.razonSocialComprador,
            "client_ruc": invoice.infoFactura.identificacionComprador,
            "issue_date": issueDate,
            "remission_guide": "N/A",
            "invoice_items": datos_articulos,
            "detalle_column_keys": sorted(list(detalles_keys_set)),  # <- aquí las columnas adicionales dinámicas
            "additional_info": additional_info_dict,
            "totals": [
                {"label": "SUBTOTAL IVA 15%", "amount": "$" + "{:.2f}".format(float(subtotal_iva_15))},
                {"label": "SUBTOTAL 0%", "amount": "$" + "{:.2f}".format(float(subtotal_iva_0))},
                {"label": "SUBTOTAL No objeto IVA", "amount": "$0.00"},
                {"label": "SUBTOTAL SIN IMPUESTOS", "amount": "$" + invoice.infoFactura.totalSinImpuestos},
                {"label": "SUBTOTAL Exento de IVA", "amount": "$0.00"},
                {"label": "TOTAL Descuento", "amount": "$" + "{:.2f}".format(descuento_total)},
                {"label": "ICE", "amount": "$0.00"},
                {"label": "IVA 15%", "amount": "$" + "{:.2f}".format(float(iva_15))},
                {"label": "IRBPN", "amount": "$0.00"},
                {"label": "PROPINA", "amount": "$" + "{:.2f}".format(float(invoice.infoFactura.propina)) if invoice.infoFactura.propina else "0.00"},
                {"label": "VALOR TOTAL", "amount": "$" + "{:.2f}".format(float(invoice.infoFactura.importeTotal))}
            ]
        }

        # Lee la plantilla HTML y crea un Template de Jinja2
        template_path = self.config['DIR_PDF_FACTURAS']
        with open(template_path, encoding='utf-8') as file:
            template = Template(file.read())

        # Renderiza la plantilla con los datos proporcionados
        html_content = template.render(data)
        pdf = HTML(string=html_content).write_pdf()
        with open(pathPDF, "wb") as f:
            f.write(pdf)

    def generar_ride_notacredito(self, notacredito: NotaCreditoSchema, claveAcceso: str, data_facturacion: Datos_Facturacion, fechaAutorizacion, issueDate):
        pathPDF = f"{self.config['DIR_NOTAS_CREDITO']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
        ruta_logo_path = os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, notacredito.campoAdicional1) if notacredito.campoAdicional1 and notacredito.campoAdicional1 != "" else (os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, data_facturacion.ruta_logo) if data_facturacion.ruta_logo else None)
        logo_base64 = None
        if ruta_logo_path:
            with open(ruta_logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        imagen_codigo_barras_base64 = generar_codigo_barras_base64(claveAcceso)
        datos_articulos = []
        detalles_keys_set = set()

        iva_0 = 0
        iva_15 = 0
        subtotal_iva_15 = 0
        subtotal_iva_0 = 0
        for ttImpuesto in notacredito.infoNotaCredito.totalConImpuestos:
            if ttImpuesto.codigoPorcentaje == "4":
                iva_15 += float(ttImpuesto.valor)
                subtotal_iva_15 = float(ttImpuesto.baseImponible)
            if ttImpuesto.codigoPorcentaje == "0":
                iva_0 += float(ttImpuesto.valor)
                subtotal_iva_0 = float(ttImpuesto.baseImponible)

        descuento_total = 0
        total_sin_impuestos = 0

        for detalle in notacredito.detalles:
            descuento_total += float(detalle.descuento)
            total_sin_impuestos += float(detalle.precioTotalSinImpuesto)

            # Procesar detalles adicionales
            detalles_adicionales = {
                d.nombre: d.valor
                for d in getattr(detalle, "detallesAdicionales", [])
                if d.nombre and d.nombre.strip() != "-"
            }

            detalles_keys_set.update(detalles_adicionales.keys())

            dt = {
                "code": detalle.codigoInterno,
                "aux_code": detalle.codigoAdicional if detalle.codigoAdicional else "N/A",
                "quantity": detalle.cantidad,
                "description": detalle.descripcion,
                "unit_price": "$" + detalle.precioUnitario,
                "discount": "$" + detalle.descuento,
                "total_price": "$" + detalle.precioTotalSinImpuesto,
                "additional_details": detalles_adicionales
            }
            datos_articulos.append(dt)

        # Convertir infoAdicional a dict general
        additional_info_dict = {
            item.nombre: item.valor
            for item in notacredito.infoAdicional
            if item.nombre and item.nombre.strip() != "-"
        } if notacredito.infoAdicional else {}

        # Armar el JSON para renderizar
        data = {
            "documento": "Nota de Crédito",
            "logo_url": logo_base64,
            "company_name": data_facturacion.razon_social,
            "company_address": data_facturacion.direccion,
            "accounting_required": data_facturacion.obligado_contabilidad,
            "company_ruc": data_facturacion.ruc,
            "invoice_number": f"{notacredito.infoTributaria.estab}-{notacredito.infoTributaria.ptoEmi}-{notacredito.infoTributaria.secuencial}",
            "authorization_date": fechaAutorizacion,
            "environment": "PRUEBA" if notacredito.infoTributaria.ambiente == "1" else "PRODUCCION",
            "issue": "Normal" if notacredito.infoTributaria.tipoEmision == "1" else "Contingencia",
            "authorization_number": notacredito.infoTributaria.claveAcceso,
            "barcode_url": imagen_codigo_barras_base64,
            "client_name": notacredito.infoNotaCredito.razonSocialComprador,
            "client_ruc": notacredito.infoNotaCredito.identificacionComprador,
            "factura_relacionada": notacredito.infoNotaCredito.numDocModificado,
            "razon_modificacion": notacredito.infoNotaCredito.motivo,
            "issue_date": issueDate,
            "remission_guide": "N/A",
            "invoice_items": datos_articulos,
            "detalle_column_keys": sorted(list(detalles_keys_set)),  # <- aquí las columnas adicionales dinámicas
            "additional_info": additional_info_dict,
            "totals": [
                {"label": "SUBTOTAL IVA 15%", "amount": "$" + "{:.2f}".format(float(subtotal_iva_15))},
                {"label": "SUBTOTAL 0%", "amount": "$" + "{:.2f}".format(float(subtotal_iva_0))},
                {"label": "SUBTOTAL No objeto IVA", "amount": "$0.00"},
                {"label": "SUBTOTAL SIN IMPUESTOS", "amount": "$" + notacredito.infoNotaCredito.totalSinImpuestos},
                {"label": "SUBTOTAL Exento de IVA", "amount": "$0.00"},
                {"label": "TOTAL Descuento", "amount": "$" + "{:.2f}".format(descuento_total)},
                {"label": "ICE", "amount": "$0.00"},
                {"label": "IVA 15%", "amount": "$" + "{:.2f}".format(float(iva_15))},
                {"label": "IRBPN", "amount": "$0.00"},
                {"label": "VALOR TOTAL", "amount": "$" + "{:.2f}".format(float(notacredito.infoNotaCredito.valorModificacion))}
            ]
        }

        # Lee la plantilla HTML y crea un Template de Jinja2
        template_path = self.config['DIR_PDF_NOTAS_CREDITO']
        with open(template_path, encoding='utf-8') as file:
            template = Template(file.read())

        # Renderiza la plantilla con los datos proporcionados
        html_content = template.render(data)
        pdf = HTML(string=html_content).write_pdf()
        with open(pathPDF, "wb") as f:
            f.write(pdf)

    def generar_ride_retencion(self, retencion: RetencionSchema, claveAcceso: str, data_facturacion: Datos_Facturacion, fechaAutorizacion, issueDate):
        pathPDF = f"{self.config['DIR_RETENCIONES']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
        ruta_logo_path = os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, retencion.campoAdicional1) if retencion.campoAdicional1 and retencion.campoAdicional1 != "" else (os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, data_facturacion.ruta_logo) if data_facturacion.ruta_logo else None)
        logo_base64 = None
        if ruta_logo_path:
            with open(ruta_logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        imagen_codigo_barras_base64 = generar_codigo_barras_base64(claveAcceso)
        datos_articulos = []

        ruta_logo_path_footer = os.path.join(UPLOAD_FOLDER + "imgs/solsap", "PNG-footer-qr-facturas-1.png") 
        logo_base64_footer = None
        if ruta_logo_path_footer:
            with open(ruta_logo_path_footer, "rb") as image_file:
                logo_base64_footer = base64.b64encode(image_file.read()).decode('utf-8')

        for detalle in retencion.docsSustento:

            for _retencion in detalle.retenciones:
                dt = {
                    "comprobante": DocumentType(detalle.codDocSustento).name,
                    "numero": detalle.numDocSustento,
                    "fechaEmision": detalle.fechaEmisionDocSustento,
                    "ejerFiscal": retencion.infoCompRetencion.periodoFiscal,
                    "baseImponible": _retencion.baseImponible,
                    "impuesto": ImpositivoRetenido(_retencion.codigo).name,
                    "porcentajeRetener": _retencion.porcentajeRetener,
                    "valorRetenido": _retencion.valorRetenido,
                }
                datos_articulos.append(dt)
                
        # Convertir infoAdicional a dict general
        additional_info_dict = {
            item.nombre: item.valor
            for item in retencion.infoAdicional
            if item.nombre and item.nombre.strip() != "-"
        } if retencion.infoAdicional else {}

        # Armar el JSON para renderizar
        data = {
            "documento": "COMPROBANTE DE RETENCIÓN",
            "logo_url": logo_base64,
            "company_name": data_facturacion.razon_social,
            "company_address": data_facturacion.direccion,
            "accounting_required": data_facturacion.obligado_contabilidad,
            "company_ruc": data_facturacion.ruc,
            "invoice_number": f"{retencion.infoTributaria.estab}-{retencion.infoTributaria.ptoEmi}-{retencion.infoTributaria.secuencial}",
            "authorization_date": fechaAutorizacion,
            "environment": "PRUEBA" if retencion.infoTributaria.ambiente == "1" else "PRODUCCION",
            "issue": "Normal" if retencion.infoTributaria.tipoEmision == "1" else "Contingencia",
            "authorization_number": retencion.infoTributaria.claveAcceso,
            "barcode_url": imagen_codigo_barras_base64,
            "client_name": retencion.infoCompRetencion.razonSocialSujetoRetenido,
            "client_ruc": retencion.infoCompRetencion.identificacionSujetoRetenido,
            "issue_date": issueDate,
            "invoice_items": datos_articulos,
            "additional_info": additional_info_dict,
            "footer_image_base64": logo_base64_footer
        }

        # Lee la plantilla HTML y crea un Template de Jinja2
        template_path = self.config['DIR_PDF_RETENCIONES']
        with open(template_path, encoding='utf-8') as file:
            template = Template(file.read())

        # Renderiza la plantilla con los datos proporcionados
        html_content = template.render(data)
        pdf = HTML(string=html_content).write_pdf()
        with open(pathPDF, "wb") as f:
            f.write(pdf)

    def generar_ride_liquidacioncompra(self, liquidacioncompra: LiquidacionCompraSchema, claveAcceso: str, data_facturacion: Datos_Facturacion, fechaAutorizacion, issueDate):
        pathPDF = f"{self.config['DIR_LIQUIDACION_COMPRA']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
        ruta_logo_path = os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, liquidacioncompra.campoAdicional1) if liquidacioncompra.campoAdicional1 and liquidacioncompra.campoAdicional1 != "" else (os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, data_facturacion.ruta_logo) if data_facturacion.ruta_logo else None)
        logo_base64 = None
        if ruta_logo_path:
            with open(ruta_logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        imagen_codigo_barras_base64 = generar_codigo_barras_base64(claveAcceso)
        
        ruta_logo_path_footer = os.path.join(UPLOAD_FOLDER + "imgs/solsap", "PNG-footer-qr-facturas-1.png") 
        logo_base64_footer = None
        if ruta_logo_path_footer:
            with open(ruta_logo_path_footer, "rb") as image_file:
                logo_base64_footer = base64.b64encode(image_file.read()).decode('utf-8')
        
        datos_articulos = []
        detalles_keys_set = set()

        iva_0 = 0
        iva_15 = 0
        subtotal_iva_15 = 0
        subtotal_iva_0 = 0
        for ttImpuesto in liquidacioncompra.infoLiquidacionCompra.totalConImpuestos:
            if ttImpuesto.codigoPorcentaje == "4":
                iva_15 += float(ttImpuesto.valor)
                subtotal_iva_15 = float(ttImpuesto.baseImponible)
            if ttImpuesto.codigoPorcentaje == "0":
                iva_0 += float(ttImpuesto.valor)
                subtotal_iva_0 = float(ttImpuesto.baseImponible)

        descuento_total = 0
        total_sin_impuestos = 0

        for detalle in liquidacioncompra.detalles:
            descuento_total += float(detalle.descuento)
            total_sin_impuestos += float(detalle.precioTotalSinImpuesto)

            # Procesar detalles adicionales
            detalles_adicionales = {
                d.nombre: d.valor
                for d in getattr(detalle, "detallesAdicionales", [])
                if d.nombre and d.nombre.strip() != "-"
            }

            detalles_keys_set.update(detalles_adicionales.keys())

            dt = {
                "code": detalle.codigoPrincipal,
                "aux_code": detalle.codigoAuxiliar if detalle.codigoAuxiliar else "N/A",
                "quantity": detalle.cantidad,
                "description": detalle.descripcion,
                "unit_price": "$" + detalle.precioUnitario,
                "discount": "$" + detalle.descuento,
                "total_price": "$" + detalle.precioTotalSinImpuesto,
                "additional_details": detalles_adicionales
            }
            datos_articulos.append(dt)
        
        additional_info_dict = {
            item.nombre: item.valor
            for item in liquidacioncompra.infoAdicional
            if item.nombre and item.nombre.strip() != "-"
        } if liquidacioncompra.infoAdicional else {}

        data = {
            "documento": "Liquidación de Compra",
            "logo_url": logo_base64,
            "company_name": data_facturacion.razon_social,
            "company_address": data_facturacion.direccion,
            "accounting_required": data_facturacion.obligado_contabilidad,
            "company_ruc": data_facturacion.ruc,
            "invoice_number": f"{liquidacioncompra.infoTributaria.estab}-{liquidacioncompra.infoTributaria.ptoEmi}-{liquidacioncompra.infoTributaria.secuencial}",
            "authorization_date": fechaAutorizacion,
            "environment": "PRUEBA" if liquidacioncompra.infoTributaria.ambiente == "1" else "PRODUCCION",
            "issue": "Normal" if liquidacioncompra.infoTributaria.tipoEmision == "1" else "Contingencia",
            "authorization_number": liquidacioncompra.infoTributaria.claveAcceso,
            "barcode_url": imagen_codigo_barras_base64,
            "client_name": liquidacioncompra.infoLiquidacionCompra.razonSocialProveedor,
            "client_ruc": liquidacioncompra.infoLiquidacionCompra.identificacionProveedor,
            "issue_date": issueDate,
            "invoice_items": datos_articulos,
            "detalle_column_keys": sorted(list(detalles_keys_set)),  # <- aquí las columnas adicionales dinámicas
            "additional_info": additional_info_dict,
            "footer_image_base64": logo_base64_footer,
            "totals": [
                {"label": "SUBTOTAL IVA 15%", "amount": "$" + "{:.2f}".format(float(subtotal_iva_15))},
                {"label": "SUBTOTAL 0%", "amount": "$" + "{:.2f}".format(float(subtotal_iva_0))},
                {"label": "SUBTOTAL No objeto IVA", "amount": "$0.00"},
                {"label": "SUBTOTAL SIN IMPUESTOS", "amount": "$" + liquidacioncompra.infoLiquidacionCompra.totalSinImpuestos},
                {"label": "SUBTOTAL Exento de IVA", "amount": "$0.00"},
                {"label": "TOTAL Descuento", "amount": "$" + "{:.2f}".format(descuento_total)},
                {"label": "ICE", "amount": "$0.00"},
                {"label": "IVA 15%", "amount": "$" + "{:.2f}".format(float(iva_15))},
                {"label": "IRBPN", "amount": "$0.00"},
                {"label": "VALOR TOTAL", "amount": "$" + "{:.2f}".format(float(liquidacioncompra.infoLiquidacionCompra.importeTotal))}
            ]
        }

        # Lee la plantilla HTML y crea un Template de Jinja2
        template_path = self.config['DIR_PDF_LIQUIDACION_COMPRA']
        with open(template_path, encoding='utf-8') as file:
            template = Template(file.read())
        
        html_content = template.render(data)
        pdf = HTML(string=html_content).write_pdf()
        with open(pathPDF, "wb") as f:
            f.write(pdf)

    def generar_ride_guiaremision(self, guiaRemision: GuiaSchema, claveAcceso: str, data_facturacion: Datos_Facturacion, fechaAutorizacion, issueDate):
        pathPDF = f"{self.config['DIR_GUIA_REMISION']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
        ruta_logo_path = os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, guiaRemision.campoAdicional1) if guiaRemision.campoAdicional1 and guiaRemision.campoAdicional1 != "" else (os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, data_facturacion.ruta_logo) if data_facturacion.ruta_logo else None)
        logo_base64 = None
        if ruta_logo_path:
            with open(ruta_logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        imagen_codigo_barras_base64 = generar_codigo_barras_base64(claveAcceso)

        ruta_logo_path_footer = os.path.join(UPLOAD_FOLDER + "imgs/solsap", "PNG-footer-qr-facturas-1.png") 
        logo_base64_footer = None
        if ruta_logo_path_footer:
            with open(ruta_logo_path_footer, "rb") as image_file:
                logo_base64_footer = base64.b64encode(image_file.read()).decode('utf-8')
        datos_articulos = []

        cliente_destinado = ""
        ruc_cliente_destinado = ""
        motivo_traslado = ""
        comp_venta = ""
        detalles_keys_set = set()
        for destinatario in guiaRemision.destinatarios:
            if cliente_destinado == "":
                cliente_destinado += destinatario.razonSocialDestinatario
                ruc_cliente_destinado += destinatario.identificacionDestinatario
                motivo_traslado += destinatario.motivoTraslado
            if destinatario.codDocSustento:
                comp_venta += "FACTURA " + destinatario.numDocSustento 
            for detalle in destinatario.detalles:
                detalles_adicionales = {
                    d.nombre: d.valor
                    for d in detalle.detallesAdicionales
                    if d.nombre and d.nombre.strip() != "-"
                }

                detalles_keys_set.update(detalles_adicionales.keys())

                dt = {
                    "codigo": detalle.codigoInterno,
                    "descripcion": detalle.descripcion,
                    "detallesAdicionales": detalles_adicionales,
                    "cantidad": detalle.cantidad
                }

                datos_articulos.append(dt)

        additional_info_dict = {
            item.nombre: item.valor
            for item in guiaRemision.infoAdicional
            if item.nombre and item.nombre.strip() != "-"
        } if guiaRemision.infoAdicional else {}

        data = {
            "documento": "GUIA DE REMISIÓN",
            "logo_url": logo_base64,
            "company_name": data_facturacion.razon_social,
            "company_address": data_facturacion.direccion,
            "accounting_required": data_facturacion.obligado_contabilidad,
            "company_ruc": data_facturacion.ruc,
            "invoice_number": f"{guiaRemision.infoTributaria.estab}-{guiaRemision.infoTributaria.ptoEmi}-{guiaRemision.infoTributaria.secuencial}",
            "authorization_date": fechaAutorizacion,
            "environment": "PRUEBA" if guiaRemision.infoTributaria.ambiente == "1" else "PRODUCCION",
            "issue": "Normal" if guiaRemision.infoTributaria.tipoEmision == "1" else "Contingencia",
            "authorization_number": guiaRemision.infoTributaria.claveAcceso,
            "barcode_url": imagen_codigo_barras_base64,
            "client_name": cliente_destinado,
            "client_ruc": ruc_cliente_destinado,
            "issue_date": issueDate,
            "invoice_items": datos_articulos,
            "additional_info": additional_info_dict,
            "footer_image_base64": logo_base64_footer,
            "motivo_traslado": motivo_traslado,
            "ini_traslado": guiaRemision.infoGuiaRemision.fechaIniTransporte,
            "fin_traslado": guiaRemision.infoGuiaRemision.fechaFinTransporte,
            "comprobante_venta": comp_venta,
            "detalle_column_keys": sorted(list(detalles_keys_set)),
            "transportista": guiaRemision.infoGuiaRemision.razonSocialTransportista,
            "ruc_transportista": guiaRemision.infoGuiaRemision.rucTransportista,
            "placa": guiaRemision.infoGuiaRemision.placa,
            "pto_partida": guiaRemision.infoGuiaRemision.dirPartida,
            "pto_llegada": guiaRemision.destinatarios[0].dirDestinatario,
            "fin_traslado": guiaRemision.infoGuiaRemision.fechaFinTransporte,
            "ini_traslado": guiaRemision.infoGuiaRemision.fechaIniTransporte
        }

        # Lee la plantilla HTML y crea un Template de Jinja2
        template_path = self.config['DIR_PDF_GUIA_REMISION']
        with open(template_path, encoding='utf-8') as file:
            template = Template(file.read())

        # Renderiza la plantilla con los datos proporcionados
        html_content = template.render(data)
        pdf = HTML(string=html_content).write_pdf()
        with open(pathPDF, "wb") as f:
            f.write(pdf)

    def generar_ride_notadebito(self, notadebito: NotaDebitoSchema, claveAcceso: str, data_facturacion: Datos_Facturacion, fechaAutorizacion, issueDate):
    
        pathPDF = f"{self.config['DIR_NOTA_DEBITO']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
        ruta_logo_path = os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, notadebito.campoAdicional1) if notadebito.campoAdicional1 and notadebito.campoAdicional1 != "" else (os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruc, data_facturacion.ruta_logo) if data_facturacion.ruta_logo else None)
        logo_base64 = None
        if ruta_logo_path:
            with open(ruta_logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        imagen_codigo_barras_base64 = generar_codigo_barras_base64(claveAcceso)
        
        ruta_logo_path_footer = os.path.join(UPLOAD_FOLDER + "imgs/solsap", "PNG-footer-qr-facturas-1.png") 
        logo_base64_footer = None
        if ruta_logo_path_footer:
            with open(ruta_logo_path_footer, "rb") as image_file:
                logo_base64_footer = base64.b64encode(image_file.read()).decode('utf-8')
            
        datos_articulos = []
        #detalles_keys_set = set()

        iva_0 = 0
        iva_15 = 0
        subtotal_iva_15 = 0
        subtotal_iva_0 = 0
        for ttImpuesto in notadebito.infoNotaDebito.impuestos:
            if ttImpuesto.codigoPorcentaje == "4":
                iva_15 += float(ttImpuesto.valor)
                subtotal_iva_15 = float(ttImpuesto.baseImponible)
            if ttImpuesto.codigoPorcentaje == "0":
                iva_0 += float(ttImpuesto.valor)
                subtotal_iva_0 = float(ttImpuesto.baseImponible)
        
        descuento_total = 0
        total_sin_impuestos = 0

        for detalle in notadebito.motivos:
            """ descuento_total += float(detalle.descuento) """
            total_sin_impuestos += float(detalle.valor)

            # Procesar detalles adicionales
            """ detalles_adicionales = {
                d.nombre: d.valor
                for d in getattr(detalle, "detallesAdicionales", [])
                if d.nombre and d.nombre.strip() != "-"
            }

            detalles_keys_set.update(detalles_adicionales.keys()) """

            dt = {
                "razon": detalle.razon,
                "valor": "$" + "{:.2f}".format(float(detalle.valor))
            }
            datos_articulos.append(dt)

        additional_info_dict = {
            item.nombre: item.valor
            for item in notadebito.infoAdicional
            if item.nombre and item.nombre.strip() != "-"
        } if notadebito.infoAdicional else {}

        data = {
            "documento": "Nota de Debito",
            "logo_url": logo_base64,
            "company_name": data_facturacion.razon_social,
            "company_address": data_facturacion.direccion,
            "accounting_required": data_facturacion.obligado_contabilidad,
            "company_ruc": data_facturacion.ruc,
            "invoice_number": f"{notadebito.infoTributaria.estab}-{notadebito.infoTributaria.ptoEmi}-{notadebito.infoTributaria.secuencial}",
            "authorization_date": fechaAutorizacion,
            "environment": "PRUEBA" if notadebito.infoTributaria.ambiente == "1" else "PRODUCCION",
            "issue": "Normal" if notadebito.infoTributaria.tipoEmision == "1" else "Contingencia",
            "authorization_number": notadebito.infoTributaria.claveAcceso,
            "barcode_url": imagen_codigo_barras_base64,
            "client_name": notadebito.infoNotaDebito.razonSocialComprador,
            "client_ruc": notadebito.infoNotaDebito.identificacionComprador,
            "issue_date": issueDate,
            "invoice_items": datos_articulos,
            "comprobante_venta": "FACTURA" if notadebito.infoNotaDebito.codDocModificado else "",
            "f_emision_fact_rel": notadebito.infoNotaDebito.fechaEmisionDocSustento if notadebito.infoNotaDebito.fechaEmisionDocSustento else "",
            "num_fact_rel": notadebito.infoNotaDebito.numDocModificado if notadebito.infoNotaDebito.numDocModificado else "",
            #"detalle_column_keys": sorted(list(detalles_keys_set)),  # <- aquí las columnas adicionales dinámicas
            "additional_info": additional_info_dict,
            "footer_image_base64": logo_base64_footer,
            "totals": [
                {"label": "SUBTOTAL IVA 15%", "amount": "$" + "{:.2f}".format(float(subtotal_iva_15))},
                {"label": "SUBTOTAL 0%", "amount": "$" + "{:.2f}".format(float(subtotal_iva_0))},
                {"label": "SUBTOTAL No objeto IVA", "amount": "$0.00"},
                {"label": "SUBTOTAL SIN IMPUESTOS", "amount": "$" + notadebito.infoNotaDebito.totalSinImpuestos},
                {"label": "SUBTOTAL Exento de IVA", "amount": "$0.00"},
                {"label": "TOTAL Descuento", "amount": "$" + "{:.2f}".format(descuento_total)},
                {"label": "ICE", "amount": "$0.00"},
                {"label": "IVA 15%", "amount": "$" + "{:.2f}".format(float(iva_15))},
                {"label": "IRBPN", "amount": "$0.00"},
                {"label": "VALOR TOTAL", "amount": "$" + "{:.2f}".format(float(notadebito.infoNotaDebito.valorTotal))}
            ]
        }

        # Lee la plantilla HTML y crea un Template de Jinja2
        template_path = self.config['DIR_PDF_NOTADEBITO']
        with open(template_path, encoding='utf-8') as file:
            template = Template(file.read())
        
        html_content = template.render(data)
        pdf = HTML(string=html_content).write_pdf()
        with open(pathPDF, "wb") as f:
            f.write(pdf)