import random
import os
import logging
import pytz

from datetime import datetime
from dotenv import dotenv_values
from tortoise.transactions import atomic, in_transaction
from decimal import Decimal
from fastapi import BackgroundTasks

from ..schemas.notadebito_schema import NotaDebito
from ..schemas.base_schema import InfoToSignXml
from ..schemas.respuestas_sri_schema import map_sri_status_to_custom
from ..exceptions.notadebito_exception import NotaDebitoDataNotExistsException, NotaDebitoErrorException
from ..services.nota_debito.xmlBuilder import createXml
from ....app.middlewares.audit_middleware import ModelAudit
from ....app.controllers.email_controller import EmailController
from ....core.emails.schemas.email_schema import EmailData
from ....app.models.model import User, NotaDebitoModel, Datos_Facturacion
from ....utils.utilsCall import PDFGenerator, DotNetCrystalClient, createAccessKey, validar_xml_con_xsd, createTempXmlFileGeneral, createTempFile, createTempXmlFile1, sign_xml_file, send_xml_to_authorization, send_xml_to_reception

UPLOAD_FOLDER = "src/assets/"

class NotaDebitoService():
    def __init__(self, db):
        self.db = db
        self.config = {
            **dotenv_values('.env')
        }

    def _safe_str(self, value, default=""):
        return default if value is None else str(value)

    def _build_notadebito_render_request(
        self,
        notadebito: NotaDebito,
        data_facturacion,
        clave_acceso: str,
        fecha_autorizacion: str = None,
        hora_autorizacion: str = None
    ) -> dict:
        fecha_autorizacion = fecha_autorizacion or datetime.now().strftime("%d/%m/%Y")
        hora_autorizacion = hora_autorizacion or datetime.now().strftime("%H:%M:%S")

        # InfoTributaria
        info_tributaria = {
            "ambiente": self._safe_str(notadebito.infoTributaria.ambiente),
            "tipoEmision": self._safe_str(notadebito.infoTributaria.tipoEmision),
            "claveAcceso": self._safe_str(clave_acceso),
            "razonSocial": self._safe_str(data_facturacion.razon_social),
            "nombreComercial": self._safe_str(data_facturacion.nombre_comercial or data_facturacion.razon_social),
            "ruc": self._safe_str(data_facturacion.ruc),
            "codDoc": self._safe_str(notadebito.infoTributaria.codDoc),
            "estab": self._safe_str(notadebito.infoTributaria.estab),
            "ptoEmi": self._safe_str(notadebito.infoTributaria.ptoEmi),
            "secuencial": self._safe_str(notadebito.infoTributaria.secuencial),
            "dirMatriz": self._safe_str(data_facturacion.direccion),
            "diaEmission": self._safe_str(notadebito.infoTributaria.diaEmission),
            "mesEmission": self._safe_str(notadebito.infoTributaria.mesEmission),
            "anioEmission": self._safe_str(notadebito.infoTributaria.anioEmission),
            "fechaAuto": fecha_autorizacion,
            "horaAuto": hora_autorizacion
        }

        # TotalConImpuestos
        impuestos = []
        for item in (notadebito.infoNotaDebito.impuestos or []):
            impuestos.append({
                "codigo": self._safe_str(item.codigo),
                "codigoPorcentaje": self._safe_str(item.codigoPorcentaje),
                "baseImponible": self._safe_str(item.baseImponible),
                "valor": self._safe_str(item.valor),
                "tarifa": self._safe_str(item.tarifa)
            })

        pagos = []
        for item in (notadebito.infoNotaDebito.pagos or []):
            pagos.append({
                "formaPago": self._safe_str(item.formaPago),
                "total": self._safe_str(item.total),
                "plazo": self._safe_str(item.plazo),
                "unidadTiempo": self._safe_str(item.unidadTiempo)
            })

        # InfoNotaCredito
        info_notadebito = {
            "fechaEmision": self._safe_str(notadebito.infoNotaDebito.fechaEmision),
            "dirEstablecimiento": self._safe_str(notadebito.infoNotaDebito.dirEstablecimiento),
            "tipoIdentificacionComprador": self._safe_str(notadebito.infoNotaDebito.tipoIdentificacionComprador),
            "razonSocialComprador": self._safe_str(notadebito.infoNotaDebito.razonSocialComprador),
            "identificacionComprador": self._safe_str(notadebito.infoNotaDebito.identificacionComprador),
            "contribuyenteEspecial": self._safe_str(notadebito.infoNotaDebito.contribuyenteEspecial),
            "obligadoContabilidad": self._safe_str(notadebito.infoNotaDebito.obligadoContabilidad or data_facturacion.obligado_contabilidad),
            "rise": self._safe_str(notadebito.infoNotaDebito.rise),   
            "codDocModificado": self._safe_str(notadebito.infoNotaDebito.codDocModificado),    
            "numDocModificado": self._safe_str(notadebito.infoNotaDebito.numDocModificado),
            "fechaEmisionDocSustento": self._safe_str(notadebito.infoNotaDebito.fechaEmisionDocSustento),
            "totalSinImpuestos": self._safe_str(notadebito.infoNotaDebito.totalSinImpuestos),     
            "impuestos": impuestos,
            "valorTotal": self._safe_str(notadebito.infoNotaDebito.valorTotal),
            "pagos": pagos
        }

       
        # InfoAdicional
        info_adicional = []
        for item in (notadebito.infoAdicional or []):
            info_adicional.append({
                "nombre": self._safe_str(item.nombre),
                "valor": self._safe_str(item.valor)
            })

        payload = {
            "infoTributaria": info_tributaria,
            "infoNotaCredito": info_notadebito,
            "infoAdicional": info_adicional,
            "campoAdicional1": self._safe_str(notadebito.campoAdicional1 or data_facturacion.ruta_logo or "logo.png"),
            "campoAdicional2": self._safe_str(notadebito.campoAdicional2 or "NotaDebito.rpt"),
            "LogoPathOverride": None
        }

        return payload
    
    async def enviar_notadebito(self, notadebito: NotaDebito, user_info: ModelAudit, background_tasks: BackgroundTasks):
        try:
            urlReception = self.config["URL_RECEPTION_PRUEBAS"] if notadebito.infoTributaria.ambiente == "1" else self.config["URL_RECEPTION"]
            urlAuthorization = self.config["URL_AUTHORIZATION_PRUEBAS"] if notadebito.infoTributaria.ambiente == "1" else self.config["URL_AUTHORIZATION"]

            data_facturacion = await Datos_Facturacion.get_or_none(user = user_info['created_by'])
            if not data_facturacion:
                raise NotaDebitoDataNotExistsException(user_info['created_by_name'])
            
            randomNumber = str(random.randint(1,99999999)).zfill(8)
            if notadebito.infoTributaria.claveAcceso:
                claveAcceso = notadebito.infoTributaria.claveAcceso
            else:
                claveAcceso = createAccessKey(notadebito.infoTributaria, randomNumber, data_facturacion)
            notadebito.infoTributaria.claveAcceso = claveAcceso

            xmlData = createXml(notadebito, claveAcceso, data_facturacion)
            xmlFileName = str(claveAcceso) + '.xml'
            xmlString = xmlData['xmlString']

            if xmlString is None:
                raise NotaDebitoErrorException("Error al crear el XML de liquidación de compra: " + xmlData['error'])
            
            xmlNoSigned = createTempXmlFile1(xmlString, xmlFileName)
            ruta = self.config['DIR_NOTA_DEBITO']
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

            xsd_path = self.config['DIR_XSD_NOTADEBITO']
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
                pathPDF = f"{self.config['DIR_NOTA_DEBITO']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                if isAuthorized:
                    #xml_autorizado = responseAuthorization['xml']
                    #overwrite_xml_file(xml_autorizado, xmlFileName, data_facturacion.ruc, ruta)
                    """
                    pdfGenerator = PDFGenerator(self.db)
                    pdfGenerator.generar_ride_notadebito(
                        notadebito,
                        claveAcceso,
                        data_facturacion,
                        datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
                        datetime.now().strftime("%d/%m/%Y")
                    )
                    """
                    fecha_auto = datetime.now().strftime("%d/%m/%Y")
                    hora_auto = datetime.now().strftime("%H:%M:%S")

                    payload = self._build_notadebito_render_request(
                        notadebito=notadebito,
                        data_facturacion=data_facturacion,
                        clave_acceso=claveAcceso,
                        fecha_autorizacion=fecha_auto,
                        hora_autorizacion=hora_auto
                    )

                    dotnet = DotNetCrystalClient(self.config['URL_API_PDF'])
                    output_pdf = f"{self.config['DIR_NOTA_DEBITO']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                    await dotnet.render_notadebito(payload, output_pdf)

                    listaDatosAdicionales = notadebito.infoAdicional if notadebito.infoAdicional else []
                    email = ""

                    for dtAdicional in listaDatosAdicionales:
                        if dtAdicional.nombre in ("Correo", "Email", "email", "correo", "EMAIL", "CORREO"):
                            email += dtAdicional.valor

                    emailData = EmailData(
                        identificacion = notadebito.infoNotaDebito.identificacionComprador,
                        usuario = notadebito.infoNotaDebito.identificacionComprador,
                        contrasenia = notadebito.infoNotaDebito.identificacionComprador,
                        nombre_usuario = notadebito.infoNotaDebito.identificacionComprador,
                        email_receptor = email,
                        subject="Nota de Debito - SOLSAP " + notadebito.infoTributaria.estab + '-' + notadebito.infoTributaria.ptoEmi + '-' + notadebito.infoTributaria.secuencial
                    )

                    emailController = EmailController()

                    autorizaciones = responseAuthorization['response_sri']
                    logging.info("Nota debito autorizada correctamente")
                    if 'autorizaciones' in autorizaciones and 'autorizacion' in autorizaciones['autorizaciones']:
                        autorizacion = autorizaciones['autorizaciones']['autorizacion'][0]
                        mensaje = ""
                        codigo_estado = map_sri_status_to_custom(sri_status=responseAuthorization['status'])
                        id_notadebito = await self.crear_registro_notadebito(notadebito, claveAcceso, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, 0, mensaje)
                        background_tasks.add_task(emailController.send_mail, emailData, notadebito, user_info, 'notadebito', id_documento=id_notadebito)
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
                        id_notadebito = await self.crear_registro_notadebito(notadebito, claveAcceso, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, identificador, mensaje)
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
                id_notadebito = await self.crear_registro_notadebito(notadebito, claveAcceso, user_info, xmlSigned.name, pathPDF, data_facturacion, isReceived[1]['estado'], codigo_estado, identificador, mensaje)
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
    async def crear_registro_notadebito(
        self,
        notadebito: NotaDebito,
        claveAcceso: str, 
        user_info: ModelAudit, 
        pathXml: str, 
        pathPDF: str, 
        data_facturacion: Datos_Facturacion, 
        estado: str, 
        estado_sap: str, 
        estado_sri: str, 
        mensaje_sri: str
    ):
        async with in_transaction():
            try:
                usuario = await User.get_or_none(id=user_info['created_by'])
                if not usuario:
                    raise NotaDebitoDataNotExistsException('Usuario no encontrado')
                
                numero_notadebito = f"{notadebito.infoTributaria.estab}-{notadebito.infoTributaria.ptoEmi}-{notadebito.infoTributaria.secuencial}"
                notadebito_db = await NotaDebitoModel.get_or_none(numero_notadebito=numero_notadebito, ruc_emisor=data_facturacion.ruc)
                ecuador = pytz.timezone("America/Guayaquil")

                iva_total = Decimal(0.00)
                if notadebito.infoNotaDebito.impuestos:
                    for impuesto in notadebito.infoNotaDebito.impuestos:
                        iva_total += Decimal(impuesto.valor)

                if notadebito_db:
                    notadebito_db.ruc_emisor = data_facturacion.ruc
                    notadebito_db.ruc_receptor = notadebito.infoNotaDebito.identificacionComprador
                    notadebito_db.clave_acceso = claveAcceso
                    notadebito_db.numero_autorizacion = notadebito.infoTributaria.claveAcceso
                    notadebito_db.numero_notadebito = numero_notadebito
                    notadebito_db.numero_factura = notadebito.infoNotaDebito.numDocModificado
                    notadebito_db.fecha_fact_rel = datetime.strptime(notadebito.infoNotaDebito.fechaEmisionDocSustento, "%d/%m/%Y")
                    notadebito_db.fecha_emision = datetime.now(ecuador)
                    notadebito_db.fecha_autorizacion = datetime.now(ecuador)
                    notadebito_db.ruta_xml = pathXml
                    notadebito_db.ruta_pdf = pathPDF
                    notadebito_db.estado = estado
                    notadebito_db.subtotal = Decimal(notadebito.infoNotaDebito.totalSinImpuestos)
                    notadebito_db.iva = iva_total
                    notadebito_db.total = Decimal(notadebito.infoNotaDebito.valorTotal)
                    notadebito_db.estado_sap = estado_sap
                    notadebito_db.estado_sri = estado_sri
                    notadebito_db.mensaje_sri = mensaje_sri
                    notadebito_db.updated = datetime.now(ecuador)
                    notadebito_db.updated_by = user_info['created_by']
                    notadebito_db.updated_by_name = user_info['created_by_name']
                    await notadebito_db.save()
                else:
                    notadebito_db = await NotaDebitoModel.create(
                        ruc_emisor=data_facturacion.ruc,
                        ruc_receptor=notadebito.infoNotaDebito.identificacionComprador,
                        user=usuario,
                        numero_notadebito=numero_notadebito,
                        numero_factura=notadebito.infoNotaDebito.numDocModificado,
                        fecha_fact_rel=datetime.strptime(notadebito.infoNotaDebito.fechaEmisionDocSustento, "%d/%m/%Y"),
                        clave_acceso=claveAcceso,
                        numero_autorizacion=notadebito.infoTributaria.claveAcceso,
                        fecha_emision=datetime.now(ecuador),
                        fecha_autorizacion=datetime.now(ecuador),
                        ruta_xml=pathXml,
                        ruta_pdf=pathPDF,
                        iva=iva_total,
                        subtotal=Decimal(notadebito.infoNotaDebito.totalSinImpuestos),
                        total=Decimal(notadebito.infoNotaDebito.valorTotal),
                        estado=estado,
                        estado_sap=estado_sap,
                        estado_sri=estado_sri,
                        mensaje_sri=mensaje_sri,
                        created = user_info['created'],
                        created_by=user_info['created_by'],
                        created_by_name=user_info['created_by_name'],
                    )

                return notadebito_db.id

            except Exception as e:
                logging.error(f"Error al crear el registro de nota de debito: {str(e)}")
                raise NotaDebitoErrorException(f"Error al crear el registro de nota de debito: {str(e)}")