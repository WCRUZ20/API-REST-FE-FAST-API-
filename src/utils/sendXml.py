import base64
import logging
from zeep import Client

async def send_xml_to_reception(pathXmlSigned: str, urlToReception: str):
    # get xml from directory
    with open(pathXmlSigned, 'rb') as f:
        xml_signed = f.read()

    # encode xml to base64 and decode in utf-8
    base64_binary_xml = base64.b64encode(xml_signed).decode('utf-8')

    try:
        cliente = Client(wsdl=urlToReception)
        result = cliente.service.validarComprobante(base64_binary_xml)
        if result['estado'] == 'RECIBIDA':
            return True, result
        else:
            return False, result

    except Exception as e:
        logging.error('Error to send xml for reception: %s' % str(e))
        return False, None

async def send_xml_to_authorization(accessKey: str, urlToAuthorization: str):
    try:
        cliente = Client(wsdl=urlToAuthorization)
        result = cliente.service.autorizacionComprobante(accessKey)
        if not result.autorizaciones:
            return {
                'isValid': False,
                'xml': None,
                'response_sri': result
            }
        status = result.autorizaciones.autorizacion[0].estado
        if status == 'AUTORIZADO' or status == 'EN PROCESO':

            xml = result.autorizaciones.autorizacion[0].comprobante
            return {
                'isValid': True,
                'status': status,
                'xml': xml,
                'response_sri': result
            }
        else:
            return {
                'isValid': False,
                'status': status,
                'xml': None,
                'response_sri': result
            }
    except Exception as e:
        logging.error('Error to send xml for reception: %s' % str(e))
        return {
            'isValid': False,
            'status': status,
            'xml': None,
            'error': str(e),
            'response_sri': None
        }
    
async def send_consult_accesskey(accessKey: str, urlToConsult: str):
    try:
        cliente = Client(wsdl=urlToConsult)
        result = cliente.service.consultarEstadoAutorizacionComprobante(accessKey)
        #print('result: ', result)
        if result['estadoConsulta'] and not result['estadoAutorizacion']:
            respuestaWS = result['mensajes']['mensaje'][0]
            mensaje = respuestaWS['mensaje']
            informacionAdiccional = respuestaWS['informacionAdicional']
            return {
                'codigo': None,
                'mensaje': mensaje + ' - ' + informacionAdiccional,
                'claveAcceso': accessKey,
                'tipoComprobante': result['tipoComprobante'],
                'fechaAutorizacion': result['fechaAutorizacion']
            }
        elif not result['estadoConsulta'] and result['estadoAutorizacion']:
            fechaAutorizacion = result['fechaAutorizacion'] if 'fechaAutorizacion' in result else None
            print('fechaAutorizacion: ', fechaAutorizacion)
            return {
                'codigo': 2,
                'mensaje': result['estadoAutorizacion'],
                'claveAcceso': accessKey,
                'tipoComprobante': result['tipoComprobante'],
                'fechaAutorizacion': fechaAutorizacion
            }
    except Exception as e:
        logging.error('Error to send xml for reception: %s' % str(e))
        return {
            'isValid': False,
            'xml': None,
            'error': str(e)
        }