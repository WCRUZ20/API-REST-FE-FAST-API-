import random
import os
import base64
import logging
import pytz

from jinja2 import Template
from weasyprint import HTML
from decimal import Decimal
from fastapi import BackgroundTasks
from datetime import datetime
from dotenv import dotenv_values
from tortoise.transactions import atomic, in_transaction

#from utils.generarPDFDotNet import DotNetCrystalClient


from ..schemas.invoice_schema import Invoice, InfoToSignXml
from ..schemas.respuestas_sri_schema import map_sri_status_to_custom
from ..services.factura.xmlBuilder import createXml
from ..exceptions.factura_exception import InvoiceErrorException, InvoiceDataNotExistsException
from ....app.controllers.email_controller import EmailController
from ....core.emails.schemas.email_schema import EmailData
from ....app.middlewares.audit_middleware import ModelAudit
from ....app.models.model import Factura, User, Datos_Facturacion
from ....utils.utilsCall import PDFGenerator, DotNetCrystalClient, createAccessKey, validar_xml_con_xsd, generar_codigo_barras_base64, createTempXmlFile, createTempFile, createTempXmlFile1, sign_xml_file, send_xml_to_authorization, send_xml_to_reception


UPLOAD_FOLDER = "src/assets/"

class InvoiceService():

    def __init__(self, db):
        self.db = db
        self.config = {
            **dotenv_values('.env')
        }

    def _safe_str(self, value, default=""):
        return default if value is None else str(value)

    def _build_factura_render_request(
        self,
        invoice: Invoice,
        data_facturacion,
        clave_acceso: str,
        fecha_autorizacion: str = None,
        hora_autorizacion: str = None
    ) -> dict:
        fecha_autorizacion = fecha_autorizacion or datetime.now().strftime("%d/%m/%Y")
        hora_autorizacion = hora_autorizacion or datetime.now().strftime("%H:%M:%S")

        # InfoTributaria
        info_tributaria = {
            "ambiente": self._safe_str(invoice.infoTributaria.ambiente),
            "tipoEmision": self._safe_str(invoice.infoTributaria.tipoEmision),
            "claveAcceso": self._safe_str(clave_acceso),
            "razonSocial": self._safe_str(data_facturacion.razon_social),
            "nombreComercial": self._safe_str(data_facturacion.nombre_comercial or data_facturacion.razon_social),
            "ruc": self._safe_str(data_facturacion.ruc),
            "codDoc": self._safe_str(invoice.infoTributaria.codDoc),
            "estab": self._safe_str(invoice.infoTributaria.estab),
            "ptoEmi": self._safe_str(invoice.infoTributaria.ptoEmi),
            "secuencial": self._safe_str(invoice.infoTributaria.secuencial),
            "dirMatriz": self._safe_str(data_facturacion.direccion),
            "diaEmission": self._safe_str(invoice.infoTributaria.diaEmission),
            "mesEmission": self._safe_str(invoice.infoTributaria.mesEmission),
            "anioEmission": self._safe_str(invoice.infoTributaria.anioEmission),
            "fechaAuto": fecha_autorizacion,
            "horaAuto": hora_autorizacion
        }

        # TotalConImpuestos
        total_con_impuestos = []
        for item in (invoice.infoFactura.totalConImpuestos or []):
            total_con_impuestos.append({
                "codigo": self._safe_str(item.codigo),
                "codigoPorcentaje": self._safe_str(item.codigoPorcentaje),
                "baseImponible": self._safe_str(item.baseImponible),
                "valor": self._safe_str(item.valor)
            })

        # Pagos
        pagos = []
        for item in (invoice.infoFactura.pagos or []):
            pagos.append({
                "formaPago": self._safe_str(item.formaPago),
                "total": self._safe_str(item.total),
                "plazo": self._safe_str(item.plazo),
                "unidadTiempo": self._safe_str(item.unidadTiempo)
            })

        # Reembolsos
        reembolsos = []
        for reembolso in (invoice.infoFactura.reembolsos or []):
            detalle_impuestos = []
            for imp in (reembolso.detalleImpuestos or []):
                detalle_impuestos.append({
                    "codigo": self._safe_str(imp.codigo),
                    "codigoPorcentaje": self._safe_str(imp.codigoPorcentaje),
                    "baseImponibleReembolso": self._safe_str(imp.baseImponibleReembolso),
                    "tarifa": self._safe_str(imp.tarifa),
                    "impuestoReembolso": self._safe_str(imp.impuestoReembolso)
                })

            reembolsos.append({
                "tipoIdentificacionProveedorReembolso": self._safe_str(reembolso.tipoIdentificacionProveedorReembolso),
                "identificacionProveedorReembolso": self._safe_str(reembolso.identificacionProveedorReembolso),
                "codPaisPagoProveedorReembolso": self._safe_str(reembolso.codPaisPagoProveedorReembolso),
                "tipoProveedorReembolso": self._safe_str(reembolso.tipoProveedorReembolso),
                "codDocReembolso": self._safe_str(reembolso.codDocReembolso),
                "estabDocReembolso": self._safe_str(reembolso.estabDocReembolso),
                "ptoEmiDocReembolso": self._safe_str(reembolso.ptoEmiDocReembolso),
                "secuencialDocReembolso": self._safe_str(reembolso.secuencialDocReembolso),
                "fechaEmisionDocReembolso": self._safe_str(reembolso.fechaEmisionDocReembolso),
                "numeroautorizacionDocReemb": self._safe_str(reembolso.numeroautorizacionDocReemb),
                "detalleImpuestos": detalle_impuestos
            })

        # InfoFactura
        info_factura = {
            "fechaEmision": self._safe_str(invoice.infoFactura.fechaEmision),
            "dirEstablecimiento": self._safe_str(invoice.infoFactura.dirEstablecimiento),
            "contribuyenteEspecial": self._safe_str(invoice.infoFactura.contribuyenteEspecial),
            "obligadoContabilidad": self._safe_str(invoice.infoFactura.obligadoContabilidad or data_facturacion.obligado_contabilidad),
            "tipoIdentificacionComprador": self._safe_str(invoice.infoFactura.tipoIdentificacionComprador),
            "guiaRemision": self._safe_str(invoice.infoFactura.guiaRemision),
            "razonSocialComprador": self._safe_str(invoice.infoFactura.razonSocialComprador),
            "identificacionComprador": self._safe_str(invoice.infoFactura.identificacionComprador),
            "direccionComprador": self._safe_str(invoice.infoFactura.direccionComprador),
            "totalSinImpuestos": self._safe_str(invoice.infoFactura.totalSinImpuestos),
            "totalDescuento": self._safe_str(invoice.infoFactura.totalDescuento),
            "totalConImpuestos": total_con_impuestos,
            "propina": self._safe_str(invoice.infoFactura.propina),
            "importeTotal": self._safe_str(invoice.infoFactura.importeTotal),
            "moneda": self._safe_str(invoice.infoFactura.moneda),
            "pagos": pagos,
            "valorRetIva": self._safe_str(invoice.infoFactura.valorRetIva),
            "valorRetRenta": self._safe_str(invoice.infoFactura.valorRetRenta),
            "comercioExterior": self._safe_str(invoice.infoFactura.comercioExterior),
            "IncoTermFactura": self._safe_str(invoice.infoFactura.IncoTermFactura),
            "lugarIncoTerm": self._safe_str(invoice.infoFactura.lugarIncoTerm),
            "paisOrigen": self._safe_str(invoice.infoFactura.paisOrigen),
            "puertoEmbarque": self._safe_str(invoice.infoFactura.puertoEmbarque),
            "paisDestino": self._safe_str(invoice.infoFactura.paisDestino),
            "paisAdquisicion": self._safe_str(invoice.infoFactura.paisAdquisicion),
            "incoTermTotalSinImpuestos": self._safe_str(invoice.infoFactura.incoTermTotalSinImpuestos),
            "fleteInternacional": self._safe_str(invoice.infoFactura.fleteInternacional),
            "seguroInternacional": self._safe_str(invoice.infoFactura.seguroInternacional),
            "gastosAduaneros": self._safe_str(invoice.infoFactura.gastosAduaneros),
            "gastosTransporteOtros": self._safe_str(invoice.infoFactura.gastosTransporteOtros),
            "codDocReembolso": self._safe_str(invoice.infoFactura.codDocReembolso),
            "totalComprobantesReembolso": self._safe_str(invoice.infoFactura.totalComprobantesReembolso),
            "totalBaseImponibleReembolso": self._safe_str(invoice.infoFactura.totalBaseImponibleReembolso),
            "totalImpuestoReembolso": self._safe_str(invoice.infoFactura.totalImpuestoReembolso),
            "reembolsos": reembolsos
        }

        # Detalles
        detalles = []
        for det in (invoice.detalles or []):
            detalles_adicionales = []
            for add in (det.detallesAdicionales or []):
                detalles_adicionales.append({
                    "nombre": self._safe_str(add.nombre),
                    "valor": self._safe_str(add.valor)
                })

            impuestos = []
            for imp in (det.impuestos or []):
                impuestos.append({
                    "codigo": self._safe_str(imp.codigo),
                    "codigoPorcentaje": self._safe_str(imp.codigoPorcentaje),
                    "baseImponible": self._safe_str(imp.baseImponible),
                    "valor": self._safe_str(imp.valor),
                    "tarifa": self._safe_str(imp.tarifa)
                })

            detalles.append({
                "codigoPrincipal": self._safe_str(det.codigoPrincipal),
                "codigoAuxiliar": self._safe_str(det.codigoAuxiliar),
                "descripcion": self._safe_str(det.descripcion),
                "cantidad": det.cantidad,
                "precioUnitario": self._safe_str(det.precioUnitario),
                "descuento": self._safe_str(det.descuento),
                "precioTotalSinImpuesto": self._safe_str(det.precioTotalSinImpuesto),
                "detallesAdicionales": detalles_adicionales,
                "impuestos": impuestos
            })

        # Retenciones
        retenciones = []
        for ret in (invoice.retenciones or []):
            retenciones.append({
                "codigo": self._safe_str(ret.codigo),
                "codigoPorcentaje": self._safe_str(ret.codigoPorcentaje),
                "tarifa": self._safe_str(ret.tarifa),
                "valor": self._safe_str(ret.valor)
            })

        # InfoAdicional
        info_adicional = []
        for item in (invoice.infoAdicional or []):
            info_adicional.append({
                "nombre": self._safe_str(item.nombre),
                "valor": self._safe_str(item.valor)
            })

        payload = {
            "infoTributaria": info_tributaria,
            "infoFactura": info_factura,
            "detalles": detalles,
            "retenciones": retenciones,
            "infoAdicional": info_adicional,
            "campoAdicional1": self._safe_str(invoice.campoAdicional1 or data_facturacion.ruta_logo or "logo.png"),
            "campoAdicional2": self._safe_str(invoice.campoAdicional2 or "Factura01.rpt"),
            "LogoPathOverride": None
        }

        return payload

    async def process_invoice_in_background(self, invoice: Invoice, urlReception, urlAuthorization, user_info, background_tasks: BackgroundTasks):
        data_facturacion = await Datos_Facturacion.get_or_none(user = user_info['created_by'])
        if not data_facturacion:
            raise InvoiceDataNotExistsException(user_info['created_by_name'])

        claveAcceso = invoice.infoTributaria.claveAcceso #createAccessKey(invoice.documentInfo, randomNumber, data_facturacion)

        xmlData = createXml(invoice, claveAcceso, data_facturacion)

        xmlFileName = str(claveAcceso) + '.xml'

        xmlString = xmlData['xmlString']

        # create temp files to create xml
        xmlNoSigned = createTempXmlFile1(xmlString, xmlFileName)
        xmlSigned = createTempXmlFile(xmlString, xmlFileName, data_facturacion.ruc)

        # get digital signature
        certificateName = data_facturacion.nombre_firma + '.p12'
        pathSignature = os.path.abspath('src/assets/firmasElectronicas/' + certificateName)
        with open(pathSignature, 'rb') as file:
            digitalSignature = file.read()
            certificateToSign = createTempFile(digitalSignature, certificateName)
        
        # password of signature
        passwordP12 = data_facturacion.password_sign
        infoToSignXml = InfoToSignXml(
            pathXmlToSign=xmlNoSigned.name,
            pathXmlSigned=xmlSigned.name,
            pathSignatureP12=certificateToSign.name,
            passwordSignature=passwordP12)
        
        # sign xml and creating temp file
        isXmlCreated = sign_xml_file(infoToSignXml)

        #antes
        # Enviar XML para la recepción
        isReceived = await send_xml_to_reception(
            pathXmlSigned=xmlSigned.name,
            urlToReception=urlReception,
        )

        # Autorizar XML
        isAuthorized = False
        pathPDF = ""
        if isReceived[0]:
            responseAuthorization = await send_xml_to_authorization(
                claveAcceso,
                urlAuthorization,
            )
            isAuthorized = responseAuthorization['isValid']

            pathPDF = self.config['DIR_FACTURAS'] + f"/{data_facturacion.ruc}/{claveAcceso}.pdf"

            if isAuthorized:
                # Datos dinámicos para la factura
                imagen_codigo_barras_base64 = generar_codigo_barras_base64(claveAcceso)
                datos_articulos = []
                descuento_total = 0
                total_sin_impuestos = 0
                for detalle in invoice.detalles:
                    descuento_total += float(detalle.descuento)
                    total_sin_impuestos += float(detalle.precioTotalSinImpuesto)
                    dt = {
                            "code": detalle.codigoPrincipal,
                            "aux_code": detalle.codigoAuxiliar if detalle.codigoAuxiliar else "N/A",
                            "quantity": detalle.cantidad,
                            "description": detalle.descripcion,
                            "detail_1": "N/A",
                            "detail_2": "N/A",
                            "unit_price": "$" + detalle.precioUnitario,
                            "discount": "$" + detalle.descuento,
                            "total_price": "$" + detalle.precioTotalSinImpuesto
                        }
                    datos_articulos.append(dt)

                ruta_logo_path = os.path.join(UPLOAD_FOLDER + "imgs", data_facturacion.ruta_logo) if data_facturacion.ruta_logo else None
                logo_base64 = None
                if ruta_logo_path:
                    with open(ruta_logo_path, "rb") as image_file:
                        logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')

                subTotal15 = 0
                iva15 = 0
                subTotal0 = 0
                subTotalNoObjetoIVA = 0
                subTotalSinImpuesto = 0
                subTotalExentoIVA = 0

                for tax in invoice.totalsWithTax:
                    if tax.percentageCode == "4":
                        subTotal15 += float(tax.taxableBase)
                        iva15 += float(tax.taxValue)
                    elif tax.percentageCode == "0":
                        subTotal0 += float(tax.taxableBase)


                data = {
                    "documento": "Factura",
                    "logo_url": logo_base64,
                    "company_name": data_facturacion.razon_social,
                    "company_address": data_facturacion.direccion,
                    "accounting_required": data_facturacion.obligado_contabilidad,
                    "company_ruc": data_facturacion.ruc,
                    "invoice_number": invoice.infoTributaria.estab + '-' + invoice.infoTributaria.ptoEmi + '-' + invoice.infoTributaria.secuencial,
                    "authorization_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "environment": "PRUEBA",
                    "issue": "Normal",
                    "authorization_number": invoice.infoTributaria.claveAcceso,
                    "barcode_url": imagen_codigo_barras_base64,
                    "client_name": invoice.infoFactura.razonSocialComprador,
                    "client_ruc": invoice.infoFactura.identificacionComprador,
                    "issue_date": datetime.now().strftime("%d/%m/%Y"),
                    "remission_guide": "N/A",
                    "invoice_items": datos_articulos,
                    "additional_email": invoice.infoAdicional[0].valor if invoice.infoAdicional else "N/A",
                    "totals": [
                        {"label": "SUBTOTAL IVA 15%", "amount": "$" + invoice.infoFactura.totalSinImpuestos},
                        {"label": "SUBTOTAL 0%", "amount": "$0.00"},
                        {"label": "SUBTOTAL No objeto IVA", "amount": "$0.00"},
                        {"label": "SUBTOTAL SIN IMPUESTOS", "amount": "$" + invoice.infoFactura.totalSinImpuestos},
                        {"label": "SUBTOTAL Exento de IVA", "amount": "$0.00"},
                        {"label": "TOTAL Descuento", "amount": "$" + "{:.2f}".format(descuento_total)},
                        {"label": "ICE", "amount": "$0.00"},
                        {"label": "IVA 15%", "amount": "$" + "{:.2f}".format(float(invoice.infoFactura.totalConImpuestos[0].valor)) if invoice.infoFactura.totalConImpuestos else "$0.00"}, 
                        {"label": "IRBPN", "amount": "$0.00"},
                        {"label": "PROPINA", "amount": "$" + "{:.2f}".format(float(invoice.infoFactura.propina)) if invoice.infoFactura.propina else "$0.00"},
                        {"label": "VALOR TOTAL", "amount": "$" + "{:.2f}".format(float(invoice.infoFactura.importeTotal))}
                    ]
                }

                # Lee la plantilla HTML y crea un Template de Jinja2
                template_path = self.config['DIR_BASE'] + "/src/assets/templates/facturaPdf.html"
                with open(template_path, encoding='utf-8') as file:
                    template = Template(file.read())

                # Renderiza la plantilla con los datos proporcionados
                html_content = template.render(data)
                pdf = HTML(string=html_content).write_pdf()
                with open(pathPDF, "wb") as f:
                    f.write(pdf)

                await self.crear_registro_factura(invoice, user_info, xmlSigned.name, pathPDF, data_facturacion)
                listaDatosAdicionales = invoice.infoAdicional
                email = ""
                for dtAdicional in listaDatosAdicionales:
                    if dtAdicional.nombre == "Correo":
                        email += dtAdicional.valor
                emailData = EmailData(
                    identificacion = invoice.infoFactura.identificacionComprador,
                    usuario = invoice.infoFactura.identificacionComprador,
                    contrasenia = invoice.infoFactura.identificacionComprador,
                    nombre_usuario = invoice.infoFactura.razonSocialComprador,
                    email_receptor = email,
                    subject=""
                )
                emailController = EmailController()
                background_tasks.add_task(emailController.send_mail, emailData, invoice, user_info, 'facturas')
        else:
            await self.crear_registro_factura(invoice, user_info, xmlSigned.name, pathPDF, data_facturacion)
            #os.remove(xmlSigned.name)

    async def send_invoice_sap(self, invoice: Invoice, user_info: ModelAudit, background_tasks: BackgroundTasks):
        try:
            # url for reception and authorization
            urlReception = self.config["URL_RECEPTION_PRUEBAS"] if invoice.infoTributaria.ambiente == "1" else self.config["URL_RECEPTION"]
            urlAuthorization = self.config["URL_AUTHORIZATION_PRUEBAS"] if invoice.infoTributaria.ambiente == "1" else self.config["URL_AUTHORIZATION"]

            data_facturacion = await Datos_Facturacion.get_or_none(user = user_info['created_by'])
            if not data_facturacion:
                raise InvoiceDataNotExistsException(user_info['created_by_name'])

            randomNumber = str(random.randint(1,99999999)).zfill(8)

            claveAcceso = ""
            if invoice.infoTributaria.claveAcceso:
                registroFactura = await Factura.get_or_none(clave_acceso=invoice.infoTributaria.claveAcceso)
                
                if not registroFactura:
                    # Si la factura fue devuelta, se debe generar una nueva clave
                    claveAcceso = createAccessKey(invoice.infoTributaria, randomNumber, data_facturacion)
                else:
                    claveAcceso = invoice.infoTributaria.claveAcceso
            else:
                claveAcceso = createAccessKey(invoice.infoTributaria, randomNumber, data_facturacion)

            invoice.infoTributaria.claveAcceso = claveAcceso

            xmlData = createXml(invoice, claveAcceso, data_facturacion)

            xmlFileName = str(claveAcceso) + '.xml'

            xmlString = xmlData['xmlString']
            if xmlString is None:
                raise InvoiceErrorException("Error al crear el XML de la factura: " + xmlData['error'])

            # create temp files to create xml
            xmlNoSigned = createTempXmlFile1(xmlString, xmlFileName)
            xmlSigned = createTempXmlFile(xmlString, xmlFileName, data_facturacion.ruc)
            
            # get digital signature
            certificateName = data_facturacion.nombre_firma + '.p12'
            pathSignature = os.path.abspath('src/assets/firmasElectronicas/' + certificateName)
            with open(pathSignature, 'rb') as file:
                digitalSignature = file.read()
                certificateToSign = createTempFile(digitalSignature, certificateName)
            
            # password of signature
            passwordP12 = data_facturacion.password_sign
            infoToSignXml = InfoToSignXml(
                pathXmlToSign=xmlNoSigned.name,
                pathXmlSigned=xmlSigned.name,
                pathSignatureP12=certificateToSign.name,
                passwordSignature=passwordP12)
            
            # sign xml and creating temp file
            isXmlCreated = sign_xml_file(infoToSignXml)

            xsd_path = self.config['DIR_XSD_FACTURA']
            xmlSigned.seek(0)
            xml_string_data = xmlSigned.read()
            is_xml_valid = validar_xml_con_xsd(xml_string_data, xsd_path)

            #antes
            # Enviar XML para la recepción
            isReceived = await send_xml_to_reception(
                pathXmlSigned=xmlSigned.name,
                urlToReception=urlReception,
            )

            # Autorizar XML
            isAuthorized = False
            pathPDF = ""
                    
            if isReceived[0]:
                responseAuthorization = await send_xml_to_authorization(
                    claveAcceso,
                    urlAuthorization,
                )
                isAuthorized = responseAuthorization['isValid']

                pathPDF = f"{self.config['DIR_FACTURAS']}/{data_facturacion.ruc}/{claveAcceso}.pdf"

                if isAuthorized:
                    ##GENERA LOS PDF CON LOS HMTL 
                    """
                    pdfGenerator = PDFGenerator(self.db)
                    pdfGenerator.generar_ride(invoice, claveAcceso, data_facturacion, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), datetime.now().strftime("%d/%m/%Y"))
                    """

                                       
                    fecha_auto = datetime.now().strftime("%d/%m/%Y")
                    hora_auto = datetime.now().strftime("%H:%M:%S")

                    payload = self._build_factura_render_request(
                        invoice=invoice,
                        data_facturacion=data_facturacion,
                        clave_acceso=claveAcceso,
                        fecha_autorizacion=fecha_auto,
                        hora_autorizacion=hora_auto
                    )

                    dotnet = DotNetCrystalClient(self.config['URL_API_PDF'])
                    output_pdf = f"{self.config['DIR_FACTURAS']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                    await dotnet.render_factura01(payload, output_pdf)
                   
                    listaDatosAdicionales = invoice.infoAdicional
                    email = ""
                    for dtAdicional in listaDatosAdicionales:
                        if dtAdicional.nombre.upper() in ("Correo", "Email", "email", "correo", "EMAIL", "CORREO"):
                            email += dtAdicional.valor
                    emailData = EmailData(
                        identificacion = invoice.infoFactura.identificacionComprador,
                        usuario = invoice.infoFactura.identificacionComprador,
                        contrasenia = invoice.infoFactura.identificacionComprador,
                        nombre_usuario = invoice.infoFactura.razonSocialComprador,
                        email_receptor = email,
                        subject="Factura Electrónica - SOLSAP " + invoice.infoTributaria.estab + "-" + invoice.infoTributaria.ptoEmi + "-" + invoice.infoTributaria.secuencial
                    )
                    emailController = EmailController()
                    #background_tasks.add_task(emailController.send_mail, emailData, invoice, user_info, 'facturas')

                    # Después de obtener la respuesta del SRI...
                    print("Autorizacion SRI")
                    print(responseAuthorization)
                    autorizaciones = responseAuthorization['response_sri']
                    if 'autorizaciones' in autorizaciones and 'autorizacion' in autorizaciones['autorizaciones']:
                        autorizacion = autorizaciones['autorizaciones']['autorizacion'][0]
                        mensaje = ""
                        codigo_estado = map_sri_status_to_custom(sri_status=responseAuthorization['status'])
                        id_factura = await self.crear_registro_factura(invoice, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, 0, mensaje)
                        background_tasks.add_task(
                            emailController.send_mail,
                            emailData,
                            invoice,
                            user_info,
                            'facturas',
                            id_documento=id_factura
                        )
                        return {
                            'result': {
                                'codigo': codigo_estado,
                                'mensaje': responseAuthorization['status'],
                                'claveAcceso': claveAcceso
                            }
                        }
                else:
                    
                    print("Autorizacion SRI")
                    print(responseAuthorization)
                    autorizaciones = responseAuthorization['response_sri']
                    if 'autorizaciones' in autorizaciones and 'autorizacion' in autorizaciones['autorizaciones']:
                        autorizacion = autorizaciones['autorizaciones']['autorizacion'][0]
                        mensaje = autorizacion['mensajes']['mensaje'][0]['mensaje'] if 'mensajes' in autorizacion else ''
                        identificador = autorizacion['mensajes']['mensaje'][0]['identificador'] if 'mensajes' in autorizacion else ''
                        identificador_adicional = autorizacion['mensajes']['mensaje'][0]['informacionAdicional'] if 'mensajes' in autorizacion else ''
                        codigo_estado = map_sri_status_to_custom(sri_status=responseAuthorization['status'], identificador=identificador)
                        id_factura = await self.crear_registro_factura(invoice, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, identificador, mensaje)
                        
                        return {
                            'result': {
                                'codigo': codigo_estado,
                                'claveAcceso': claveAcceso,
                                'mensaje': identificador + ' - ' + mensaje + ' - ' + identificador_adicional
                            }
                        }
            else:
                print("Recepcion SRI")
                print(isReceived)
                identificador = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['identificador'] if 'comprobantes' in isReceived[1] else ''
                codigo_estado = map_sri_status_to_custom(sri_status=isReceived[1]['estado'], identificador=identificador)
                mensaje = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['mensaje'] if 'comprobantes' in isReceived[1] else ''
                identificador_adicional = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['informacionAdicional'] if 'comprobantes' in isReceived[1] else ''
                if not identificador_adicional:
                    identificador_adicional = ''
                id_factura = await self.crear_registro_factura(invoice, user_info, xmlSigned.name, pathPDF, data_facturacion, isReceived[1]['estado'], codigo_estado, identificador, mensaje)
                
                return {
                    'result': {
                        'codigo': codigo_estado,
                        'claveAcceso': claveAcceso,
                        'mensaje': identificador + ' - ' + mensaje + ' - ' + identificador_adicional
                    }
                }
                #os.remove(xmlSigned.name)
        except Exception as e:
            raise e      

    async def sign_invoice(self, invoice: Invoice, user_info: ModelAudit, background_tasks: BackgroundTasks):
        # url for reception and authorization
        urlReception = self.config["URL_RECEPTION_PRUEBAS"] if invoice.infoTributaria.tipoEmision == "1" else self.config["URL_RECEPTION"]
        urlAuthorization = self.config["URL_AUTHORIZATION_PRUEBAS"] if invoice.infoTributaria.tipoEmision == "1" else self.config["URL_AUTHORIZATION"]

        data_facturacion = await Datos_Facturacion.get_or_none(user = user_info['created_by'])
        if not data_facturacion:
            raise InvoiceDataNotExistsException(user_info['created_by_name'])

        randomNumber = str(random.randint(1,99999999)).zfill(8)

        claveAcceso = createAccessKey(invoice.infoTributaria, randomNumber, data_facturacion)
        invoice.infoTributaria.claveAcceso = claveAcceso

        background_tasks.add_task(
            self.process_invoice_in_background,
            invoice,
            urlReception,
            urlAuthorization,
            user_info,
            background_tasks
        )

        return {
            'result': {
                'accessKey': claveAcceso,
                'message': 'Factura siendo procesada en segundo plano'
            }
        }
        
    @atomic()
    async def crear_registro_factura(
        self,
        invoice: Invoice,
        user_info: ModelAudit,
        pathXml,
        pathPdf,
        data_facturacion,
        estado,
        estado_sap,
        estado_sri,
        mensaje_sri
    ):
        async with in_transaction():
            try:
                usuario = await User.get_or_none(id=user_info['created_by'])
                if not usuario:
                    raise InvoiceErrorException('Usuario no encontrado.')

                # Calcular IVA total
                iva_total = Decimal(0.00)
                if invoice.infoFactura.totalConImpuestos:
                    for impuesto in invoice.infoFactura.totalConImpuestos:
                        iva_total += Decimal(impuesto.valor)

                numero_factura = f"{invoice.infoTributaria.estab}-{invoice.infoTributaria.ptoEmi}-{invoice.infoTributaria.secuencial}"

                # Buscar si ya existe una factura con ese número de factura
                factura = await Factura.get_or_none(numero_factura=numero_factura)
                ecuador = pytz.timezone("America/Guayaquil")
                if factura:
                    # Actualizar todos los campos, incluida clave_acceso
                    factura.ruc_emisor = data_facturacion.ruc
                    factura.ruc_receptor = invoice.infoFactura.identificacionComprador
                    factura.clave_acceso = invoice.infoTributaria.claveAcceso
                    factura.numero_autorizacion = invoice.infoTributaria.claveAcceso
                    factura.fecha_emision = datetime.now(ecuador)
                    factura.subtotal = Decimal(invoice.infoFactura.totalSinImpuestos)
                    factura.iva = iva_total
                    factura.total = Decimal(invoice.infoFactura.importeTotal)
                    factura.fecha_autorizacion = datetime.now(ecuador)
                    factura.ruta_xml = pathXml
                    factura.ruta_pdf = pathPdf
                    factura.estado = estado if estado else 0
                    factura.updated = datetime.now(ecuador)
                    factura.updated_by = user_info['created_by']
                    factura.updated_by_name = user_info['created_by_name']
                    factura.estado_sap = estado_sap
                    factura.estado_sri = estado_sri
                    factura.mensaje_sri = mensaje_sri
                    await factura.save()
                    #mensaje = f"Factura {factura.numero_factura} actualizada correctamente."
                else:
                    factura = await Factura.create(
                        ruc_emisor = data_facturacion.ruc,
                        ruc_receptor = invoice.infoFactura.identificacionComprador,
                        clave_acceso = invoice.infoTributaria.claveAcceso,
                        numero_autorizacion = invoice.infoTributaria.claveAcceso,
                        numero_factura = numero_factura,
                        fecha_emision = datetime.now(ecuador),
                        subtotal = Decimal(invoice.infoFactura.totalSinImpuestos),
                        iva = iva_total,
                        total = Decimal(invoice.infoFactura.importeTotal),
                        fecha_autorizacion = datetime.now(ecuador),
                        ruta_xml = pathXml,
                        ruta_pdf = pathPdf,
                        user = usuario,
                        created = user_info['created'],
                        created_by = user_info['created_by'],
                        created_by_name = user_info['created_by_name'],
                        estado = estado if estado else 0,
                        estado_sap = estado_sap,
                        estado_sri = estado_sri,
                        mensaje_sri = mensaje_sri
                    )
                    #mensaje = f"Factura {factura.numero_factura} registrada correctamente."

                return factura.id

            except Exception as e:
                raise InvoiceErrorException(f"Error al crear el registro de la factura: {str(e)}")
            
