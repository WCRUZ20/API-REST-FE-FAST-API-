import random
import os
import logging
import base64
import pytz

from datetime import datetime
from dotenv import dotenv_values
from tortoise.transactions import atomic, in_transaction
from jinja2 import Template
from weasyprint import HTML
from decimal import Decimal
from fastapi import BackgroundTasks

from ..schemas.guia_remision_schema import GuiaRemision
from ..schemas.base_schema import InfoToSignXml
from ..schemas.respuestas_sri_schema import map_sri_status_to_custom
from ..exceptions.guia_remision_exception import GuiaRemisionDataNotExistsException, GuiaRemisionErrorException
from ..services.guia_remision.xmlBuilder import createXml
from ....app.middlewares.audit_middleware import ModelAudit
from ....app.controllers.email_controller import EmailController
from ....core.emails.schemas.email_schema import EmailData
from ....app.middlewares.audit_middleware import ModelAudit
from ....app.models.model import GuiaRemisionModel, User, Datos_Facturacion
from ....utils.utilsCall import PDFGenerator, DotNetCrystalClient, createAccessKey, validar_xml_con_xsd, createTempXmlFileGeneral, createTempXmlFile, createTempFile, createTempXmlFile1, sign_xml_file, send_xml_to_authorization, send_xml_to_reception

UPLOAD_FOLDER = "src/assets/"

class GuiaService():
    def __init__(self, db):
        self.db = db
        self.config = {
            **dotenv_values('.env')
        }

    def _safe_str(self, value, default=""):
        return default if value is None else str(value)

    def _build_guiaremision_render_request(
        self,
        guiaremision: GuiaRemision,
        data_facturacion,
        clave_acceso: str,
        fecha_autorizacion: str = None,
        hora_autorizacion: str = None
    ) -> dict:
        fecha_autorizacion = fecha_autorizacion or datetime.now().strftime("%d/%m/%Y")
        hora_autorizacion = hora_autorizacion or datetime.now().strftime("%H:%M:%S")

        # InfoTributaria
        info_tributaria = {
            "ambiente": self._safe_str(guiaremision.infoTributaria.ambiente),
            "tipoEmision": self._safe_str(guiaremision.infoTributaria.tipoEmision),
            "claveAcceso": self._safe_str(clave_acceso),
            "razonSocial": self._safe_str(data_facturacion.razon_social),
            "nombreComercial": self._safe_str(data_facturacion.nombre_comercial or data_facturacion.razon_social),
            "ruc": self._safe_str(data_facturacion.ruc),
            "codDoc": self._safe_str(guiaremision.infoTributaria.codDoc),
            "estab": self._safe_str(guiaremision.infoTributaria.estab),
            "ptoEmi": self._safe_str(guiaremision.infoTributaria.ptoEmi),
            "secuencial": self._safe_str(guiaremision.infoTributaria.secuencial),
            "dirMatriz": self._safe_str(data_facturacion.direccion),
            "diaEmission": self._safe_str(guiaremision.infoTributaria.diaEmission),
            "mesEmission": self._safe_str(guiaremision.infoTributaria.mesEmission),
            "anioEmission": self._safe_str(guiaremision.infoTributaria.anioEmission),
            "fechaAuto": fecha_autorizacion,
            "horaAuto": hora_autorizacion
        }

        # InfoGuiaRemision
        info_guiaremision = {
            "dirEstablecimiento": self._safe_str(guiaremision.infoGuiaRemision.dirEstablecimiento),
            "dirPartida": self._safe_str(guiaremision.infoGuiaRemision.dirPartida),
            "tipoIdentificacionTransportista": self._safe_str(guiaremision.infoGuiaRemision.tipoIdentificacionTransportista),
            "razonSocialTransportista": self._safe_str(guiaremision.infoGuiaRemision.razonSocialTransportista),
            "rucTransportista": self._safe_str(guiaremision.infoGuiaRemision.rucTransportista),
            "contribuyenteEspecial": self._safe_str(guiaremision.infoGuiaRemision.contribuyenteEspecial),
            "obligadoContabilidad": self._safe_str(guiaremision.infoGuiaRemision.obligadoContabilidad or data_facturacion.obligado_contabilidad),
            "rise": self._safe_str(guiaremision.infoGuiaRemision.rise),   
            "fechaIniTransporte": self._safe_str(guiaremision.infoGuiaRemision.fechaIniTransporte),    
            "fechaFinTransporte": self._safe_str(guiaremision.infoGuiaRemision.fechaFinTransporte),
            "placa": self._safe_str(guiaremision.infoGuiaRemision.placa),
        }

        # Detalles
        detalles = []
        for det in (guiaremision.destinatarios.detalles or []):
            detalles_adicionales = []
            for add in (det.detallesAdicionales or []):
                detalles_adicionales.append({
                    "nombre": self._safe_str(add.nombre),
                    "valor": self._safe_str(add.valor)
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
            })

        destinatarios = {
            "identificacionDestinatario": self._safe_str(guiaremision.destinatarios.fechaIniTransporte),
            "razonSocialDestinatario": self._safe_str(guiaremision.destinatarios.razonSocialDestinatario),
            "dirDestinatario": self._safe_str(guiaremision.destinatarios.dirDestinatario),
            "motivoTraslado": self._safe_str(guiaremision.destinatarios.motivoTraslado),
            "codEstabDestino": self._safe_str(guiaremision.destinatarios.codEstabDestino),
            "codDocSustento": self._safe_str(guiaremision.destinatarios.codDocSustento),
            "numDocSustento": self._safe_str(guiaremision.destinatarios.numDocSustento),
            "numAutDocSustento": self._safe_str(guiaremision.destinatarios.numAutDocSustento),
            "fechaEmisionDocSustento": self._safe_str(guiaremision.destinatarios.fechaEmisionDocSustento),
            "docAduaneroUnico": self._safe_str(guiaremision.destinatarios.docAduaneroUnico),
            "ruta": self._safe_str(guiaremision.destinatarios.ruta),
            "detalles": detalles
        }


        # InfoAdicional
        info_adicional = []
        for item in (guiaremision.infoAdicional or []):
            info_adicional.append({
                "nombre": self._safe_str(item.nombre),
                "valor": self._safe_str(item.valor)
            })

        payload = {
            "infoTributaria": info_tributaria,
            "infoNotaCredito": info_guiaremision,
            "destinatarios": destinatarios,
            "infoAdicional": info_adicional,
            "campoAdicional1": self._safe_str(guiaremision.campoAdicional1 or data_facturacion.ruta_logo or "logo.png"),
            "campoAdicional2": self._safe_str(guiaremision.campoAdicional2 or "GuiaRemision.rpt"),
            "LogoPathOverride": None
        }

        return payload

    async def enviar_guia_remision(self, guia_remision: GuiaRemision, user_info: ModelAudit, background_tasks: BackgroundTasks):
        try:
            
            urlReception = self.config["URL_RECEPTION_PRUEBAS"] if guia_remision.infoTributaria.tipoEmision == "1" else self.config["URL_RECEPTION"]
            urlAuthorization = self.config["URL_AUTHORIZATION_PRUEBAS"] if guia_remision.infoTributaria.tipoEmision == "1" else self.config["URL_AUTHORIZATION"]

            data_facturacion = await Datos_Facturacion.get_or_none(user = user_info['created_by'])
            if not data_facturacion:
                raise GuiaRemisionDataNotExistsException(user_info['created_by_name'])
            
            randomNumber = str(random.randint(1,99999999)).zfill(8)
            if guia_remision.infoTributaria.claveAcceso:
                claveAcceso = guia_remision.infoTributaria.claveAcceso
            else:
                claveAcceso = createAccessKey(guia_remision.infoTributaria, randomNumber, data_facturacion)
            guia_remision.infoTributaria.claveAcceso = claveAcceso

            xmlData = createXml(guia_remision, claveAcceso, data_facturacion)
            xmlFileName = str(claveAcceso) + '.xml'
            xmlString = xmlData['xmlString']

            if xmlString is None:
                raise GuiaRemisionErrorException("Error al crear el XML de liquidación de compra: " + xmlData['error'])

            xmlNoSigned = createTempXmlFile1(xmlString, xmlFileName)
            ruta = self.config['DIR_GUIA_REMISION']
            xmlSigned = createTempXmlFileGeneral(xmlString, xmlFileName, data_facturacion.ruc, ruta)

            certificateName = data_facturacion.nombre_firma + '.p12'
            pathSignature = os.path.abspath('src/assets/firmasElectronicas/' + certificateName)

            with open(pathSignature, 'rb') as file:
                digitalSignature = file.read()
                certificateToSign = createTempFile(digitalSignature, certificateName)
            
            passwordP12 = data_facturacion.password_sign
            infoToSignXml = InfoToSignXml(
                pathXmlToSign=xmlNoSigned.name,
                pathXmlSigned=xmlSigned.name,
                pathSignatureP12=certificateToSign.name,
                passwordSignature=passwordP12
            )

            isXmlCreated = sign_xml_file(infoToSignXml)

            xsd_path = self.config['DIR_XSD_GUIAREMISION']
            xmlSigned.seek(0)
            xml_string_data = xmlSigned.read()
            is_xml_valid = validar_xml_con_xsd(xml_string_data, xsd_path)

            isReceived = await send_xml_to_reception(
                pathXmlSigned=xmlSigned.name,
                urlToReception=urlReception,
            )

            isAuthorized = False
            pathPDF = ""
            if isReceived[0]:
                responseAuthorization = await send_xml_to_authorization(
                    claveAcceso,
                    urlAuthorization
                )

                isAuthorized = responseAuthorization['isValid']

                #PDF documento
                pathPDF = f"{self.config['DIR_GUIA_REMISION']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                if isAuthorized:
                    #pdfGenerator = PDFGenerator(self.db)
                    #pdfGenerator.generar_ride_guiaremision(guia_remision, claveAcceso, data_facturacion, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), datetime.now().strftime("%d/%m/%Y"))
                    fecha_auto = datetime.now().strftime("%d/%m/%Y")
                    hora_auto = datetime.now().strftime("%H:%M:%S")

                    payload = self._build_guiaremision_render_request(
                        guiaremision=guia_remision,
                        data_facturacion=data_facturacion,
                        clave_acceso=claveAcceso,
                        fecha_autorizacion=fecha_auto,
                        hora_autorizacion=hora_auto
                    )

                    dotnet = DotNetCrystalClient(self.config['URL_API_PDF'])
                    output_pdf = f"{self.config['DIR_GUIA_REMISION']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                    await dotnet.render_guiaremision(payload, output_pdf)

                    listaDatosAdicionales = guia_remision.infoAdicional
                    email = ""
                    for dtAdicional in listaDatosAdicionales:
                        if dtAdicional.nombre in ("Correo", "Email", "email", "correo", "EMAIL", "CORREO"):
                            email += dtAdicional.valor
                    emailData = EmailData(
                        identificacion = guia_remision.destinatarios[0].identificacionDestinatario,
                        usuario = guia_remision.destinatarios[0].identificacionDestinatario,
                        contrasenia = guia_remision.destinatarios[0].identificacionDestinatario,
                        nombre_usuario = guia_remision.destinatarios[0].identificacionDestinatario,
                        email_receptor = email,
                        subject="Guia de Remisión Electrónica - SOLSAP " + guia_remision.infoTributaria.estab + "-" + guia_remision.infoTributaria.ptoEmi + "-" + guia_remision.infoTributaria.secuencial
                    )
                    emailController = EmailController()
                    
                    autorizaciones = responseAuthorization['response_sri']
                    if 'autorizaciones' in autorizaciones and 'autorizacion' in autorizaciones['autorizaciones']:
                        autorizacion = autorizaciones['autorizaciones']['autorizacion'][0]
                        mensaje = ""
                        codigo_estado = map_sri_status_to_custom(sri_status=responseAuthorization['status'])
                        id_guia = await self.crear_registro_guiaremision(guia_remision, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, 0, mensaje)
                        background_tasks.add_task(
                            emailController.send_mail,
                            emailData,
                            guia_remision,
                            user_info,
                            'guiaremision',
                            id_documento=id_guia
                        )
                        logging.info("Guia de remision autorizada correctamente")
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
                        id_guia = await self.crear_registro_guiaremision(guia_remision, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, identificador, mensaje)
                        
                        return {
                            'result': {
                                'codigo': codigo_estado,
                                'claveAcceso': claveAcceso,
                                'mensaje': identificador + ' - ' + mensaje + ' - ' + identificador_adicional
                            }
                        }
            else:
                identificador = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['identificador'] if 'comprobantes' in isReceived[1] else ''
                codigo_estado = map_sri_status_to_custom(sri_status=isReceived[1]['estado'], identificador=identificador)
                mensaje = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['mensaje'] if 'comprobantes' in isReceived[1] else ''
                identificador_adicional = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['informacionAdicional'] if 'comprobantes' in isReceived[1] else ''
                if not identificador_adicional:
                    identificador_adicional = ''
                id_guia = await self.crear_registro_guiaremision(guia_remision, user_info, xmlSigned.name, pathPDF, data_facturacion, isReceived[1]['estado'], codigo_estado, identificador, mensaje)
                
                return {
                    'result': {
                        'codigo': codigo_estado,
                        'claveAcceso': claveAcceso,
                        'mensaje': identificador + ' - ' + mensaje + ' - ' + identificador_adicional
                    }
                }
        except Exception as e:
            raise e
        
    @atomic()
    async def crear_registro_guiaremision(
        self,
        guiaremision: GuiaRemision,
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
                    raise GuiaRemisionErrorException('Usuario no encontrado.')


                numero_guia_remision = f"{guiaremision.infoTributaria.estab}-{guiaremision.infoTributaria.ptoEmi}-{guiaremision.infoTributaria.secuencial}"

                # Buscar si ya existe una factura con ese número de factura
                guiaRemisionData = await GuiaRemisionModel.get_or_none(numero_guiaremision=numero_guia_remision)
                ecuador = pytz.timezone("America/Guayaquil")
                if guiaRemisionData:
                    # Actualizar todos los campos, incluida clave_acceso
                    guiaRemisionData.ruc_emisor = data_facturacion.ruc
                    guiaRemisionData.ruc_receptor = guiaremision.destinatarios[0].identificacionDestinatario
                    guiaRemisionData.ruc_transportista = guiaremision.infoGuiaRemision.rucTransportista
                    guiaRemisionData.motivo_traslado = guiaremision.destinatarios[0].motivoTraslado
                    guiaRemisionData.placa = guiaremision.infoGuiaRemision.placa
                    guiaRemisionData.pto_partida = guiaremision.infoGuiaRemision.dirPartida
                    guiaRemisionData.pto_llegada = guiaremision.destinatarios[0].dirDestinatario
                    guiaRemisionData.ini_traslado = datetime.strptime(guiaremision.infoGuiaRemision.fechaIniTransporte, "%d/%m/%Y")
                    guiaRemisionData.fin_traslado = datetime.strptime(guiaremision.infoGuiaRemision.fechaFinTransporte, "%d/%m/%Y")
                    guiaRemisionData.clave_acceso = guiaremision.infoTributaria.claveAcceso
                    guiaRemisionData.numero_autorizacion = guiaremision.infoTributaria.claveAcceso
                    guiaRemisionData.fecha_emision = datetime.now(ecuador)
                    guiaRemisionData.fecha_autorizacion = datetime.now(ecuador)
                    guiaRemisionData.ruta_xml = pathXml
                    guiaRemisionData.ruta_pdf = pathPdf
                    guiaRemisionData.estado = estado
                    guiaRemisionData.updated = datetime.now(ecuador)
                    guiaRemisionData.updated_by = user_info['created_by']
                    guiaRemisionData.updated_by_name = user_info['created_by_name']
                    guiaRemisionData.estado_sap = estado_sap
                    guiaRemisionData.estado_sri = estado_sri
                    guiaRemisionData.mensaje_sri = mensaje_sri
                    await guiaRemisionData.save()
                    #mensaje = f"Factura {factura.numero_factura} actualizada correctamente."
                else:
                    guiaRemisionData = await GuiaRemisionModel.create(
                        ruc_emisor = data_facturacion.ruc,
                        ruc_receptor = guiaremision.destinatarios[0].identificacionDestinatario,
                        ruc_transportista = guiaremision.infoGuiaRemision.rucTransportista,
                        motivo_traslado = guiaremision.destinatarios[0].motivoTraslado,
                        placa = guiaremision.infoGuiaRemision.placa,
                        pto_partida = guiaremision.infoGuiaRemision.dirPartida,
                        pto_llegada = guiaremision.destinatarios[0].dirDestinatario,
                        ini_traslado = datetime.strptime(guiaremision.infoGuiaRemision.fechaIniTransporte, "%d/%m/%Y"),
                        fin_traslado = datetime.strptime(guiaremision.infoGuiaRemision.fechaFinTransporte, "%d/%m/%Y"),
                        user = usuario,
                        numero_guiaremision = numero_guia_remision,
                        clave_acceso = guiaremision.infoTributaria.claveAcceso,
                        numero_autorizacion = guiaremision.infoTributaria.claveAcceso,
                        fecha_emision = datetime.now(ecuador),
                        fecha_autorizacion = datetime.now(ecuador),
                        ruta_xml = pathXml,
                        ruta_pdf = pathPdf,
                        created = user_info['created'],
                        created_by = user_info['created_by'],
                        created_by_name = user_info['created_by_name'],
                        estado = estado,
                        estado_sap = estado_sap,
                        estado_sri = estado_sri,
                        mensaje_sri = mensaje_sri
                    )
                    #mensaje = f"Factura {factura.numero_factura} registrada correctamente."

                return guiaRemisionData.id

            except Exception as e:
                raise GuiaRemisionErrorException(f"Error al crear el registro de la guia de remision: {str(e)}")