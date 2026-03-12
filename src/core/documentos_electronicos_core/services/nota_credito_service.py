import os
import random
import random as rd
import base64
import pytz

from datetime import datetime
from dotenv import dotenv_values
from tortoise.transactions import atomic, in_transaction
from tortoise.queryset import Q
from ..schemas.nota_credito_schema import NotaCredito, InfoToSignXml
from ..schemas.respuestas_sri_schema import map_sri_status_to_custom
from ..exceptions.nota_credito_exception import NotaCreditoDataNotExistsException, NotaCreditoErrorException
from ...shared.schemas.shared_schema import CertificadoFirma
from ....app.models.model import Datos_Facturacion, User, Factura, NotaCreditoModel
from ....app.middlewares.audit_middleware import ModelAudit
from ....app.controllers.email_controller import EmailController
from ....core.emails.schemas.email_schema import EmailData
from ....utils.utilsCall import PDFGenerator, DotNetCrystalClient, createAccessKey, validar_xml_con_xsd, generar_codigo_barras_base64, createTempXmlFile_notacredito, createXmlNotaCredito, createTempXmlFile, createTempFile, createTempXmlFile1, sign_xml_file, send_xml_to_authorization, send_xml_to_reception

from fastapi import BackgroundTasks
from jinja2 import Template
from weasyprint import HTML
from decimal import Decimal

UPLOAD_FOLDER = "src/assets/"

class NotaCreditoService():
    def __init__(self, db):
        self.db = db
        self.config = {
            **dotenv_values('.env')
        }

    def _safe_str(self, value, default=""):
        return default if value is None else str(value)

    def _build_notacredito_render_request(
        self,
        notacredito: NotaCredito,
        data_facturacion,
        clave_acceso: str,
        fecha_autorizacion: str = None,
        hora_autorizacion: str = None
    ) -> dict:
        fecha_autorizacion = fecha_autorizacion or datetime.now().strftime("%d/%m/%Y")
        hora_autorizacion = hora_autorizacion or datetime.now().strftime("%H:%M:%S")

        # InfoTributaria
        info_tributaria = {
            "ambiente": self._safe_str(notacredito.infoTributaria.ambiente),
            "tipoEmision": self._safe_str(notacredito.infoTributaria.tipoEmision),
            "claveAcceso": self._safe_str(clave_acceso),
            "razonSocial": self._safe_str(data_facturacion.razon_social),
            "nombreComercial": self._safe_str(data_facturacion.nombre_comercial or data_facturacion.razon_social),
            "ruc": self._safe_str(data_facturacion.ruc),
            "codDoc": self._safe_str(notacredito.infoTributaria.codDoc),
            "estab": self._safe_str(notacredito.infoTributaria.estab),
            "ptoEmi": self._safe_str(notacredito.infoTributaria.ptoEmi),
            "secuencial": self._safe_str(notacredito.infoTributaria.secuencial),
            "dirMatriz": self._safe_str(data_facturacion.direccion),
            "diaEmission": self._safe_str(notacredito.infoTributaria.diaEmission),
            "mesEmission": self._safe_str(notacredito.infoTributaria.mesEmission),
            "anioEmission": self._safe_str(notacredito.infoTributaria.anioEmission),
            "fechaAuto": fecha_autorizacion,
            "horaAuto": hora_autorizacion
        }

        # TotalConImpuestos
        total_con_impuestos = []
        for item in (notacredito.infoNotaCredito.totalConImpuestos or []):
            total_con_impuestos.append({
                "codigo": self._safe_str(item.codigo),
                "codigoPorcentaje": self._safe_str(item.codigoPorcentaje),
                "baseImponible": self._safe_str(item.baseImponible),
                "valor": self._safe_str(item.valor)
            })


        # InfoNotaCredito
        info_notacreito = {
            "fechaEmision": self._safe_str(notacredito.infoNotaCredito.fechaEmision),
            "dirEstablecimiento": self._safe_str(notacredito.infoNotaCredito.dirEstablecimiento),
            "tipoIdentificacionComprador": self._safe_str(notacredito.infoNotaCredito.tipoIdentificacionComprador),
            "razonSocialComprador": self._safe_str(notacredito.infoNotaCredito.razonSocialComprador),
            "identificacionComprador": self._safe_str(notacredito.infoNotaCredito.identificacionComprador),
            "contribuyenteEspecial": self._safe_str(notacredito.infoNotaCredito.contribuyenteEspecial),
            "obligadoContabilidad": self._safe_str(notacredito.infoNotaCredito.obligadoContabilidad or data_facturacion.obligado_contabilidad),
            "rise": self._safe_str(notacredito.infoNotaCredito.rise),   
            "codDocModificado": self._safe_str(notacredito.infoNotaCredito.codDocModificado),    
            "numDocModificado": self._safe_str(notacredito.infoNotaCredito.numDocModificado),
            "fechaEmisionDocSustento": self._safe_str(notacredito.infoNotaCredito.fechaEmisionDocSustento),
            "totalSinImpuestos": self._safe_str(notacredito.infoNotaCredito.totalSinImpuestos),     
            "valorModificacion": self._safe_str(notacredito.infoNotaCredito.valorModificacion),
            "moneda": self._safe_str(notacredito.infoNotaCredito.moneda),
            "totalConImpuestos": total_con_impuestos,
            "motivo": self._safe_str(notacredito.infoNotaCredito.motivo)
        }

        # Detalles
        detalles = []
        for det in (notacredito.detalles or []):
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

        # InfoAdicional
        info_adicional = []
        for item in (notacredito.infoAdicional or []):
            info_adicional.append({
                "nombre": self._safe_str(item.nombre),
                "valor": self._safe_str(item.valor)
            })

        payload = {
            "infoTributaria": info_tributaria,
            "infoNotaCredito": info_notacreito,
            "detalles": detalles,
            "infoAdicional": info_adicional,
            "campoAdicional1": self._safe_str(notacredito.campoAdicional1 or data_facturacion.ruta_logo or "logo.png"),
            "campoAdicional2": self._safe_str(notacredito.campoAdicional2 or "NotaCredito.rpt"),
            "LogoPathOverride": None
        }

        return payload

    async def process_nota_credito_in_background(self, nota_credito: NotaCredito, data_facturacion, clave_acceso, xmlSigned, urlReception, urlAuth, user_info, background_tasks: BackgroundTasks):
        isReceived = await send_xml_to_reception(
            pathXmlSigned= xmlSigned.name,
            urlToReception= urlReception
        )

        isAuthorized = False
        pathPDF = ""
        if isReceived[0]:
            responseAuth = await send_xml_to_authorization(
                clave_acceso,
                urlAuth
            )

            isAuthorized = responseAuth['isValid']
            nota_credito.documentInfo.accessKey = clave_acceso

            pathPDF = self.config['DIR_NOTAS_CREDITO'] + f"/{data_facturacion.ruc}/{clave_acceso}.pdf"

            if isAuthorized:
                # Datos dinámicos para la factura
                imagen_codigo_barras_base64 = generar_codigo_barras_base64(clave_acceso)
                datos_articulos = []
                descuento_total = 0
                total_sin_impuestos = 0
                for detalle in nota_credito.details:
                    descuento_total += float(detalle.discount)
                    total_sin_impuestos += float(detalle.taxableBaseTax)
                    dt = {
                            "code": detalle.productCode,
                            "aux_code": "N/A",
                            "quantity": detalle.quantity,
                            "description": detalle.description,
                            "detail_1": "N/A",
                            "detail_2": "N/A",
                            "unit_price": "$" + detalle.price,
                            "discount": "$" + detalle.discount,
                            "total_price": "$" + detalle.taxableBaseTax
                        }
                    datos_articulos.append(dt)

                data = {
                    "documento": "Nota de Credito",
                    "logo_url": "https://onedrive.live.com/embed?resid=5CDC7572FB09E9B2%2193197&authkey=%21AIWHuvwFoypNH0Y&width=300",
                    "company_name": data_facturacion.razon_social,
                    "company_address": data_facturacion.direccion,
                    "accounting_required": data_facturacion.obligado_contabilidad,
                    "company_ruc": data_facturacion.ruc,
                    "invoice_number": nota_credito.documentInfo.establishment + '-' + nota_credito.documentInfo.emissionPoint + '-' + nota_credito.documentInfo.sequential,
                    "authorization_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "environment": "PRUEBA",
                    "issue": "Normal",
                    "authorization_number": nota_credito.documentInfo.accessKey,
                    "barcode_url": imagen_codigo_barras_base64,
                    "client_name": nota_credito.customer.customerName,
                    "client_ruc": nota_credito.customer.customerDni,
                    "issue_date": datetime.now().strftime("%d/%m/%Y"),
                    "remission_guide": "",
                    "invoice_items": datos_articulos,
                    "additional_email": nota_credito.additionalInfo[0].value,
                    "totals": [
                        {"label": "SUBTOTAL IVA 15%", "amount": "$" + nota_credito.payment.totalWithoutTaxes},
                        {"label": "SUBTOTAL 0%", "amount": "$0.00"},
                        {"label": "SUBTOTAL No objeto IVA", "amount": "$0.00"},
                        {"label": "SUBTOTAL SIN IMPUESTOS", "amount": "$" + nota_credito.payment.totalWithoutTaxes},
                        {"label": "SUBTOTAL Exento de IVA", "amount": "$0.00"},
                        {"label": "TOTAL Descuento", "amount": "$" + "{:.2f}".format(descuento_total)},
                        {"label": "ICE", "amount": "$0.00"},
                        {"label": "IVA 15%", "amount": "$" + nota_credito.totalsWithTax[0].taxValue},
                        {"label": "IRBPN", "amount": "$0.00"},
                        {"label": "PROPINA", "amount": "$0.00"},
                        {"label": "VALOR TOTAL", "amount": "$" + nota_credito.totalsWithTax[0].taxableBase }
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
        
            xmlSignedValue = responseAuth['xml']

            await self.crear_registro_notacredito(nota_credito, user_info, xmlSigned.name, pathPDF, data_facturacion)
            listaDatosAdicionales = nota_credito.additionalInfo
            email = ""
            for dtAdicional in listaDatosAdicionales:
                if dtAdicional.name == "Correo":
                    email += dtAdicional.value
            emailData = EmailData(
                identificacion = nota_credito.customer.customerDni,
                usuario = nota_credito.customer.customerDni,
                contrasenia = nota_credito.customer.customerDni,
                nombre_usuario = nota_credito.customer.customerName,
                email_receptor = email,
                subject=""
            )
            emailController = EmailController()
            background_tasks.add_task(emailController.send_mail, emailData, nota_credito, user_info, 'notacredito')
        else:
            await self.crear_registro_notacredito(nota_credito, user_info, xmlSigned.name, pathPDF, data_facturacion)
            os.remove(xmlSigned.name)

    async def sign_nota_credito(self, nota_credito: NotaCredito, user_info: ModelAudit, background_tasks: BackgroundTasks):
        #datos_certificado_firma = await self.get_certificado_firma(user_info)

        datos_certificado_firma = await Datos_Facturacion.get_or_none(user = user_info['created_by']).prefetch_related('user')
        if not datos_certificado_firma:
            raise NotaCreditoDataNotExistsException(user_info['created_by_name'])
        
        randomNumber = str(rd.randint(1,99999999)).zfill(8)

        clave_acceso = createAccessKey(nota_credito.documentInfo, randomNumber, datos_certificado_firma)

        xmlData = createXmlNotaCredito(nota_credito, clave_acceso, datos_certificado_firma)
        
        xmlFileName = str(clave_acceso) + '.xml'

        xmlString = xmlData['xmlString']

        xmlNoSigned = createTempXmlFile1(xmlString, xmlFileName)
        xmlSigned = createTempXmlFile_notacredito(xmlString, xmlFileName, datos_certificado_firma.ruc)

        certificateName = datos_certificado_firma.nombre_firma + '.p12'
        pathSignature = os.path.abspath(self.config['RUTA_FIRMAS_ELECTRONICAS'] + certificateName)
        with open(pathSignature, 'rb') as file:
            digitalSignature = file.read()
            certificateToSign = createTempFile(digitalSignature, certificateName)
        
        passwordP12 = datos_certificado_firma.password_sign
        infoToSignXml = InfoToSignXml(
            pathXmlToSign=xmlNoSigned.name,
            pathXmlSigned=xmlSigned.name,
            pathSignatureP12=certificateToSign.name,
            passwordSignature=passwordP12
        )

        isXmlCreated = sign_xml_file(infoToSignXml)

        # url for reception and authorization
        urlReception = self.config["URL_RECEPTION"]
        urlAuthorization = self.config["URL_AUTHORIZATION"]

        background_tasks.add_task(
            self.process_nota_credito_in_background,
            nota_credito,
            datos_certificado_firma,
            clave_acceso,
            xmlSigned,
            urlReception,
            urlAuthorization,
            user_info,
            background_tasks
        )

        return {
            'result': {
                'accessKey': clave_acceso,
                'message': 'Nota de credito siendo procesada en segundo plano'
            }
        }

    async def sign_nota_credito_sap(self, nota_credito: NotaCredito, user_info: ModelAudit, background_tasks: BackgroundTasks):
        try:
            # url for reception and authorization
            urlReception = self.config["URL_RECEPTION_PRUEBAS"] if nota_credito.infoTributaria.tipoEmision == "1" else self.config["URL_RECEPTION"]
            urlAuthorization = self.config["URL_AUTHORIZATION_PRUEBAS"] if nota_credito.infoTributaria.tipoEmision == "1" else self.config["URL_AUTHORIZATION"]
            data_facturacion = await Datos_Facturacion.get_or_none(user = user_info['created_by'])
            if not data_facturacion:
                raise NotaCreditoDataNotExistsException(user_info['created_by_name'])

            randomNumber = str(random.randint(1,99999999)).zfill(8)
            
            claveAcceso = ""
            if nota_credito.infoTributaria.claveAcceso:
                registroFactura = await Factura.get_or_none(clave_acceso=nota_credito.infoTributaria.claveAcceso)

                if registroFactura and registroFactura.estado_sap == 6:
                    # Si la factura fue devuelta, se debe generar una nueva clave
                    claveAcceso = createAccessKey(nota_credito.infoTributaria, randomNumber, data_facturacion)
                else:
                    claveAcceso = nota_credito.infoTributaria.claveAcceso
            else:
                claveAcceso = createAccessKey(nota_credito.infoTributaria, randomNumber, data_facturacion)
            
            nota_credito.infoTributaria.claveAcceso = claveAcceso

            xmlData = createXmlNotaCredito(nota_credito, claveAcceso, data_facturacion)
            xmlFileName = str(claveAcceso) + '.xml'
            xmlString = xmlData['xmlString']

            if xmlString is None:
                raise NotaCreditoErrorException("Error al crear el XML de la nota de crédito: " + xmlData['error'])

            # create temp files to create xml
            xmlNoSigned = createTempXmlFile1(xmlString, xmlFileName)
            xmlSigned = createTempXmlFile_notacredito(xmlString, xmlFileName, data_facturacion.ruc)

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
            
            isXmlCreated = sign_xml_file(infoToSignXml)

            
            xsd_path = self.config['DIR_XSD_NOTACREDITO']
            xmlSigned.seek(0)
            xml_string_data = xmlSigned.read()
            is_xml_valid = validar_xml_con_xsd(xml_string_data, xsd_path)

            # Enviar XML para la recepción
            isReceived = await send_xml_to_reception(
                pathXmlSigned=xmlSigned.name,
                urlToReception=urlReception,
            )

            isAuthorized = False
            pathPDF = ""
            if isReceived[0]:
                responseAuthorization = await send_xml_to_authorization(
                    claveAcceso,
                    urlAuthorization,
                )
                isAuthorized = responseAuthorization['isValid']

                pathPDF = f"{self.config['DIR_NOTAS_CREDITO']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                
                if isAuthorized:
                    #pdfGenerator = PDFGenerator(self.db)
                    #pdfGenerator.generar_ride_notacredito(nota_credito, claveAcceso, data_facturacion, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), datetime.now().strftime("%d/%m/%Y"))
                    
                    fecha_auto = datetime.now().strftime("%d/%m/%Y")
                    hora_auto = datetime.now().strftime("%H:%M:%S")

                    payload = self._build_notacredito_render_request(
                        notacredito=nota_credito,
                        data_facturacion=data_facturacion,
                        clave_acceso=claveAcceso,
                        fecha_autorizacion=fecha_auto,
                        hora_autorizacion=hora_auto
                    )

                    dotnet = DotNetCrystalClient(self.config['URL_API_PDF'])
                    output_pdf = f"{self.config['DIR_NOTAS_CREDITO']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                    await dotnet.render_notacredito(payload, output_pdf)

                    #await self.crear_registro_factura(invoice, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"])
                    listaDatosAdicionales = nota_credito.infoAdicional
                    email = ""
                    for dtAdicional in listaDatosAdicionales:
                        if dtAdicional.nombre in ("Correo", "Email", "email", "correo", "EMAIL", "CORREO"):
                            email += dtAdicional.valor
                    emailData = EmailData(
                        identificacion = nota_credito.infoNotaCredito.identificacionComprador,
                        usuario = nota_credito.infoNotaCredito.identificacionComprador,
                        contrasenia = nota_credito.infoNotaCredito.identificacionComprador,
                        nombre_usuario = nota_credito.infoNotaCredito.razonSocialComprador,
                        email_receptor = email,
                        subject="Nota de Credito - SOLSAP " + nota_credito.infoTributaria.estab + '-' + nota_credito.infoTributaria.ptoEmi + '-' + nota_credito.infoTributaria.secuencial
                    )
                    emailController = EmailController()

                    # Después de obtener la respuesta del SRI...
                    autorizaciones = responseAuthorization['response_sri']
                    if 'autorizaciones' in autorizaciones and 'autorizacion' in autorizaciones['autorizaciones']:
                        autorizacion = autorizaciones['autorizaciones']['autorizacion'][0]
                        mensaje = ""
                        print(responseAuthorization)
                        codigo_estado = map_sri_status_to_custom(sri_status=responseAuthorization['status'])
                        id_notacredito = await self.crear_registro_notacredito(nota_credito, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, 0, mensaje)

                        background_tasks.add_task(emailController.send_mail, emailData, nota_credito, user_info, 'notacredito', id_documento=id_notacredito)

                        return {
                            'result': {
                                'codigo': codigo_estado,
                                'mensaje': responseAuthorization['status'],
                                'claveAcceso': claveAcceso
                            }
                        }
                else:
                    
                    autorizaciones = responseAuthorization['response_sri']
                    if 'autorizaciones' in autorizaciones and 'autorizacion' in autorizaciones['autorizaciones']:
                        autorizacion = autorizaciones['autorizaciones']['autorizacion'][0]
                        mensaje = autorizacion['mensajes']['mensaje'][0]['mensaje'] if 'mensajes' in autorizacion else ''
                        identificador = autorizacion['mensajes']['mensaje'][0]['identificador'] if 'mensajes' in autorizacion else ''
                        identificador_adicional = autorizacion['mensajes']['mensaje'][0]['informacionAdicional'] if 'mensajes' in autorizacion else ''
                        codigo_estado = map_sri_status_to_custom(sri_status=responseAuthorization['status'], identificador=identificador)
                        id_notacredito = await self.crear_registro_notacredito(nota_credito, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, identificador, mensaje)
                        return {
                            'result': {
                                'codigo': codigo_estado,
                                'claveAcceso': claveAcceso,
                                'mensaje': identificador + ' - ' + mensaje + ' - ' + identificador_adicional
                            }
                        }
            else:
                identificador = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['identificador'] if 'comprobantes' in isReceived[1] else ''
                print(isReceived)
                codigo_estado = map_sri_status_to_custom(sri_status=isReceived[1]['estado'], identificador=identificador)
                mensaje = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['mensaje'] if 'comprobantes' in isReceived[1] else ''
                identificador_adicional = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['informacionAdicional'] if 'comprobantes' in isReceived[1] else ''
                if not identificador_adicional:
                    identificador_adicional = ''
                await self.crear_registro_notacredito(nota_credito, user_info, xmlSigned.name, pathPDF, data_facturacion, isReceived[1]['estado'], codigo_estado, identificador, mensaje)
                return {
                    'result': {
                        'codigo': codigo_estado,
                        'claveAcceso': claveAcceso,
                        'mensaje': identificador + ' - ' + mensaje + ' - ' + identificador_adicional
                    }
                }
        except Exception as e:
            raise NotaCreditoErrorException(f"Error con el envio de nota de credito: {str(e)}")

    @atomic()
    async def crear_registro_notacredito(self, nota_credito: NotaCredito, user_info: ModelAudit, pathXml, pathPdf, data_facturacion, estado, estado_sap, estado_sri, mensaje_sri):
        async with in_transaction():
            try:
                usuario = await User.get_or_none(id= user_info['created_by'])
                if not usuario:
                    raise NotaCreditoErrorException('Usuario no encontrado')

                numero_factura_related = nota_credito.infoNotaCredito.numDocModificado
                factura_related = await Factura.get_or_none(numero_factura = numero_factura_related)
                if not factura_related:
                    raise NotaCreditoErrorException('Factura relacionada no encontrada')
                
                iva_total = Decimal(0.00)
                if nota_credito.infoNotaCredito.totalConImpuestos:
                    for impuesto in nota_credito.infoNotaCredito.totalConImpuestos:
                        iva_total += Decimal(impuesto.valor)

                numero_notacredito = f"{nota_credito.infoTributaria.estab}-{nota_credito.infoTributaria.ptoEmi}-{nota_credito.infoTributaria.secuencial}"

                notaCredito = await NotaCreditoModel.get_or_none(numero_notacredito=numero_notacredito)
                ecuador = pytz.timezone("America/Guayaquil")

                if notaCredito:
                    notaCredito.ruc_emisor = data_facturacion.ruc
                    notaCredito.ruc_receptor = nota_credito.infoNotaCredito.identificacionComprador
                    notaCredito.clave_acceso = nota_credito.infoTributaria.claveAcceso
                    notaCredito.numero_autorizacion = nota_credito.infoTributaria.claveAcceso
                    notaCredito.fecha_emision = datetime.now(ecuador)
                    notaCredito.subtotal = Decimal(nota_credito.infoNotaCredito.totalSinImpuestos)
                    notaCredito.iva = iva_total
                    notaCredito.total = Decimal(nota_credito.infoNotaCredito.valorModificacion)
                    notaCredito.fecha_autorizacion = datetime.now(ecuador)
                    notaCredito.ruta_xml = pathXml
                    notaCredito.ruta_pdf = pathPdf
                    notaCredito.estado = estado
                    notaCredito.updated = datetime.now(ecuador)
                    notaCredito.updated_by = user_info['created_by']
                    notaCredito.updated_by_name = user_info['created_by_name']
                    notaCredito.estado_sap = estado_sap
                    notaCredito.mensaje_sri = mensaje_sri
                    notaCredito.estado_sri = estado_sri
                    notaCredito.motivo_nc = nota_credito.infoNotaCredito.motivo
                    await notaCredito.save()
                else:
                    # Crear un nuevo registro de Nota de Crédito
                    notaCredito = await NotaCreditoModel.create(
                        ruc_emisor = data_facturacion.ruc,
                        ruc_receptor = nota_credito.infoNotaCredito.identificacionComprador,
                        clave_acceso = nota_credito.infoTributaria.claveAcceso,
                        numero_autorizacion = nota_credito.infoTributaria.claveAcceso,
                        numero_notacredito = nota_credito.infoTributaria.estab + '-' + nota_credito.infoTributaria.ptoEmi + '-' + nota_credito.infoTributaria.secuencial,
                        fecha_emision = datetime.now(ecuador), 
                        subtotal = Decimal(nota_credito.infoNotaCredito.totalSinImpuestos),
                        iva = iva_total,
                        total = Decimal(nota_credito.infoNotaCredito.valorModificacion),
                        fecha_autorizacion = datetime.now(ecuador),
                        ruta_xml = pathXml,
                        ruta_pdf = pathPdf,
                        user = usuario,
                        factura_relacionada = factura_related,
                        created = user_info['created'],
                        created_by = user_info['created_by'],
                        created_by_name = user_info['created_by_name'],
                        motivo_nc = nota_credito.infoNotaCredito.motivo,
                        estado = estado,
                        estado_sap = estado_sap,
                        estado_sri = estado_sri,
                        mensaje_sri = mensaje_sri,
                    )

                return notaCredito.id
            except Exception as e:
                raise NotaCreditoErrorException(f"Error al crear el registro de Nota de Crédito: {str(e)}")