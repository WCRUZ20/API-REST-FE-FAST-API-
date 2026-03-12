from lxml import etree

from .....app.models.model import Datos_Facturacion
from ...schemas.liquidacion_compra_schema import LiquidacionCompra

def createXml(info: LiquidacionCompra, accessKey: str, data_facturacion: Datos_Facturacion):
    fecha_emision_liquidacioncompra = f"{info.infoTributaria.diaEmission}/{info.infoTributaria.mesEmission}/{info.infoTributaria.anioEmission}"
    try:
        root = etree.Element('liquidacionCompra', attrib={
            'id': 'comprobante',
            'version': '1.1.0'
        })

        # infoTributaria
        infoTributaria = etree.SubElement(root, 'infoTributaria')
        etree.SubElement(infoTributaria, 'ambiente').text = info.infoTributaria.ambiente
        etree.SubElement(infoTributaria, 'tipoEmision').text = info.infoTributaria.tipoEmision
        etree.SubElement(infoTributaria, 'razonSocial').text = data_facturacion.razon_social
        etree.SubElement(infoTributaria, 'nombreComercial').text = data_facturacion.nombre_comercial
        etree.SubElement(infoTributaria, 'ruc').text = data_facturacion.ruc
        etree.SubElement(infoTributaria, 'claveAcceso').text = accessKey
        etree.SubElement(infoTributaria, 'codDoc').text = info.infoTributaria.codDoc
        etree.SubElement(infoTributaria, 'estab').text = info.infoTributaria.estab
        etree.SubElement(infoTributaria, 'ptoEmi').text = info.infoTributaria.ptoEmi
        etree.SubElement(infoTributaria, 'secuencial').text = info.infoTributaria.secuencial
        etree.SubElement(infoTributaria, 'dirMatriz').text = data_facturacion.direccion

        # infoCompRetencion
        infoLiquidacionCompra = etree.SubElement(root, 'infoLiquidacionCompra')
        etree.SubElement(infoLiquidacionCompra, 'fechaEmision').text = fecha_emision_liquidacioncompra
        etree.SubElement(infoLiquidacionCompra, 'dirEstablecimiento').text = info.infoLiquidacionCompra.dirEstablecimiento
        if info.infoLiquidacionCompra.contribuyenteEspecial:
            etree.SubElement(infoLiquidacionCompra, 'contribuyenteEspecial').text = info.infoLiquidacionCompra.contribuyenteEspecial
        etree.SubElement(infoLiquidacionCompra, 'obligadoContabilidad').text = data_facturacion.obligado_contabilidad
        etree.SubElement(infoLiquidacionCompra, 'tipoIdentificacionProveedor').text = info.infoLiquidacionCompra.tipoIdentificacionProveedor
        etree.SubElement(infoLiquidacionCompra, 'razonSocialProveedor').text = info.infoLiquidacionCompra.razonSocialProveedor
        etree.SubElement(infoLiquidacionCompra, 'identificacionProveedor').text = info.infoLiquidacionCompra.identificacionProveedor
        etree.SubElement(infoLiquidacionCompra, 'direccionProveedor').text = info.infoLiquidacionCompra.direccionProveedor
        etree.SubElement(infoLiquidacionCompra, 'totalSinImpuestos').text = info.infoLiquidacionCompra.totalSinImpuestos
        etree.SubElement(infoLiquidacionCompra, 'totalDescuento').text = info.infoLiquidacionCompra.totalDescuento

        if info.infoLiquidacionCompra.codDocReembolso:
            etree.SubElement(infoLiquidacionCompra, 'codDocReembolso').text = info.infoLiquidacionCompra.codDocReembolso
            etree.SubElement(infoLiquidacionCompra, 'totalComprobantesReembolso').text = info.infoLiquidacionCompra.totalComprobantesReembolso
            etree.SubElement(infoLiquidacionCompra, 'totalBaseImponibleReembolso').text = info.infoLiquidacionCompra.totalBaseImponibleReembolso
            etree.SubElement(infoLiquidacionCompra, 'totalImpuestoReembolso').text = info.infoLiquidacionCompra.totalImpuestoReembolso
        
        totalConImpuestos = etree.SubElement(infoLiquidacionCompra, 'totalConImpuestos')
        for totalImpuesto in info.infoLiquidacionCompra.totalConImpuestos: 
            totalConImpuesto = etree.SubElement(totalConImpuestos, 'totalImpuesto')
            etree.SubElement(totalConImpuesto, 'codigo').text = totalImpuesto.codigo
            etree.SubElement(totalConImpuesto, 'codigoPorcentaje').text = totalImpuesto.codigoPorcentaje
            etree.SubElement(totalConImpuesto, 'baseImponible').text = totalImpuesto.baseImponible
            etree.SubElement(totalConImpuesto, 'valor').text = totalImpuesto.valor
            if totalImpuesto.descuentoAdicional:
                etree.SubElement(totalConImpuesto, 'descuentoAdicional').text = totalImpuesto.descuentoAdicional
        
        etree.SubElement(infoLiquidacionCompra, 'importeTotal').text = info.infoLiquidacionCompra.importeTotal
        etree.SubElement(infoLiquidacionCompra, 'moneda').text = info.infoLiquidacionCompra.moneda

        #Pagos
        pagos = etree.SubElement(infoLiquidacionCompra, 'pagos')
        for _pago in info.infoLiquidacionCompra.pagos:
            pago = etree.SubElement(pagos, 'pago')
            etree.SubElement(pago, 'formaPago').text = _pago.formaPago
            etree.SubElement(pago, 'total').text = _pago.total
            etree.SubElement(pago, 'plazo').text = _pago.plazo
            if _pago.unidadTiempo:
                etree.SubElement(pago, 'unidadTiempo').text = _pago.unidadTiempo

        #Detalle
        detalles = etree.SubElement(root, 'detalles')
        for _detalle in info.detalles:
            detalle = etree.SubElement(detalles, 'detalle')
            etree.SubElement(detalle, 'codigoPrincipal').text = _detalle.codigoPrincipal
            etree.SubElement(detalle, 'codigoAuxiliar').text = _detalle.codigoAuxiliar
            etree.SubElement(detalle, 'descripcion').text = _detalle.descripcion
            if _detalle.unidadMedida:
                etree.SubElement(detalle, 'unidadMedida').text = _detalle.unidadMedida
            etree.SubElement(detalle, 'cantidad').text = str(_detalle.cantidad)
            etree.SubElement(detalle, 'precioUnitario').text = _detalle.precioUnitario
            etree.SubElement(detalle, 'descuento').text = _detalle.descuento
            etree.SubElement(detalle, 'precioTotalSinImpuesto').text = _detalle.precioTotalSinImpuesto
            if _detalle.detallesAdicionales:    
                detallesAdicionales = etree.SubElement(
                    detalle, 'detallesAdicionales')
                for additional in _detalle.detallesAdicionales:
                    campoAdicional = etree.SubElement(
                        detallesAdicionales, 'detAdicional', attrib={'nombre': additional.nombre, 'valor': additional.valor})
            
            impuestos = etree.SubElement(detalle, 'impuestos')
            for impuesto_ in _detalle.impuestos:
                impuesto = etree.SubElement(impuestos, 'impuesto')
                codigo = etree.SubElement(impuesto, 'codigo')
                codigo.text = str(impuesto_.codigo)
                codigoPorcentaje = etree.SubElement(impuesto, 'codigoPorcentaje')
                codigoPorcentaje.text = impuesto_.codigoPorcentaje
                tarifa = etree.SubElement(impuesto, 'tarifa')
                tarifa.text = str(impuesto_.tarifa)
                baseImponible = etree.SubElement(impuesto, 'baseImponible')
                baseImponible.text = str(impuesto_.baseImponible)
                valor = etree.SubElement(impuesto, 'valor')
                valor.text = str(impuesto_.valor)

        # infoAdicional
        if info.infoAdicional:
            infoAdicional = etree.SubElement(root, 'infoAdicional')
            for campo in info.infoAdicional:
                campoAdicional = etree.SubElement(infoAdicional, 'campoAdicional', attrib={'nombre': campo.nombre})
                campoAdicional.text = campo.valor

        xml_string = etree.tostring(root, pretty_print=True).decode('utf-8')

        return {
            'xmlFile': root,
            'xmlString': xml_string
        }

    except Exception as e:
        print('Error al generar el XML de retención:', str(e))
        return {
            'xmlFile': None,
            'xmlString': None,
            'error': str(e)
        }