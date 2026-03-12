import json
import xmltodict
from lxml import etree
from .....core.documentos_electronicos_core.schemas.invoice_schema import Invoice
from .....app.models.datos_facturacion import Datos_Facturacion

def jsonToXml(json_str):
    data = json.loads(json_str)

    xml_str = xmltodict.unparse(data)

    return xml_str

def createXml(info: Invoice, accessKeyInvoice: str, data_facturacion: Datos_Facturacion):
    fecha_emision_factura = str(
            info.infoTributaria.diaEmission
        ) + '/' + str(
            info.infoTributaria.mesEmission
        ) + '/' + str(
            info.infoTributaria.anioEmission)
    try:
        print('dataaaa:', data_facturacion.nombre_comercial)
        root = etree.Element('factura', attrib={
                'id': 'comprobante', 'version':'2.0.0'
            })
        infoTributaria = etree.SubElement(root, 'infoTributaria')
        ambiente = etree.SubElement(infoTributaria, 'ambiente')
        ambiente.text = ''.join(info.infoTributaria.ambiente)
        tipoEmision = etree.SubElement(infoTributaria, 'tipoEmision')
        tipoEmision.text = ''.join(info.infoTributaria.tipoEmision)
        nombreNegocio = etree.SubElement(infoTributaria, 'razonSocial')
        nombreNegocio.text = ''.join(data_facturacion.razon_social)
        nombreComercial = etree.SubElement(infoTributaria, 'nombreComercial')
        nombreComercial.text = ''.join(data_facturacion.nombre_comercial)
        ruc = etree.SubElement(infoTributaria, 'ruc')
        ruc.text = ''.join(data_facturacion.ruc)
        claveAcceso = etree.SubElement(infoTributaria, 'claveAcceso')
        claveAcceso.text = ''.join(accessKeyInvoice)
        codDoc = etree.SubElement(infoTributaria, 'codDoc')
        codDoc.text = ''.join(info.infoTributaria.codDoc)
        establecimiento = etree.SubElement(infoTributaria, 'estab')
        establecimiento.text = ''.join(info.infoTributaria.estab)
        puntoEmision = etree.SubElement(infoTributaria, 'ptoEmi')
        puntoEmision.text = ''.join(info.infoTributaria.ptoEmi)
        secuencial = etree.SubElement(infoTributaria, 'secuencial')
        secuencial.text = ''.join(info.infoTributaria.secuencial)
        direccionMatriz = etree.SubElement(infoTributaria, 'dirMatriz')
        direccionMatriz.text = ''.join(data_facturacion.direccion)
        # end info tributaria

        infoFactura = etree.SubElement(root, 'infoFactura')
        fechaEmision = etree.SubElement(infoFactura, 'fechaEmision')
        fechaEmision.text = ''.join(fecha_emision_factura)
        dirEstablecimiento = etree.SubElement(
            infoFactura, 'dirEstablecimiento')
        dirEstablecimiento.text = info.infoFactura.dirEstablecimiento    
        obligatedAccounting = etree.SubElement(
            infoFactura, 'obligadoContabilidad')
        obligatedAccounting.text = data_facturacion.obligado_contabilidad

        #Exportaciones
        if info.infoFactura.comercioExterior:
            etree.SubElement(infoFactura, 'comercioExterior').text = info.infoFactura.comercioExterior
            etree.SubElement(infoFactura, 'incoTermFactura').text = info.infoFactura.IncoTermFactura
            etree.SubElement(infoFactura, 'lugarIncoTerm').text = info.infoFactura.lugarIncoTerm
            paisOrigen = etree.SubElement(infoFactura, 'paisOrigen')
            paisOrigen.text = info.infoFactura.paisOrigen
            etree.SubElement(infoFactura, 'puertoEmbarque').text = info.infoFactura.puertoEmbarque
            paisDestino = etree.SubElement(infoFactura, 'paisDestino')
            paisDestino.text = info.infoFactura.paisDestino
            etree.SubElement(infoFactura, 'paisAdquisicion').text = info.infoFactura.paisAdquisicion

        identificationType = etree.SubElement(
            infoFactura, 'tipoIdentificacionComprador')
        identificationType.text = info.infoFactura.tipoIdentificacionComprador

        #Guia de remision
        if info.infoFactura.guiaRemision:
            guiaRemision = etree.SubElement(infoFactura, 'guiaRemision')
            guiaRemision.text = info.infoFactura.guiaRemision

        razonSocialComprador = etree.SubElement(
            infoFactura, 'razonSocialComprador')
        razonSocialComprador.text = info.infoFactura.razonSocialComprador
        customerDni = etree.SubElement(
            infoFactura, 'identificacionComprador')
        customerDni.text = info.infoFactura.identificacionComprador
        if info.infoFactura.direccionComprador:
            customerAddress = etree.SubElement(
                infoFactura, 'direccionComprador')
            customerAddress.text = info.infoFactura.direccionComprador
        totalSinImpuestos = etree.SubElement(infoFactura, 'totalSinImpuestos')
        totalSinImpuestos.text = info.infoFactura.totalSinImpuestos

        if info.infoFactura.incoTermTotalSinImpuestos:
            etree.SubElement(infoFactura, 'incoTermTotalSinImpuestos').text = info.infoFactura.incoTermTotalSinImpuestos

        totalDescuento = etree.SubElement(infoFactura, 'totalDescuento')
        totalDescuento.text = info.infoFactura.totalDescuento

        totalConImpuestos = etree.SubElement(infoFactura, 'totalConImpuestos')
        for tax in info.infoFactura.totalConImpuestos:
            totalTax = etree.SubElement(totalConImpuestos, 'totalImpuesto')
            totalTaxCode = etree.SubElement(totalTax, 'codigo')
            totalTaxCode.text = tax.codigo
            percentageCode = etree.SubElement(totalTax, 'codigoPorcentaje')
            percentageCode.text = tax.codigoPorcentaje
            taxableBase = etree.SubElement(totalTax, 'baseImponible')
            taxableBase.text = str(tax.baseImponible)
            value = etree.SubElement(totalTax, 'valor')
            value.text = str(tax.valor)

        propina = etree.SubElement(infoFactura, 'propina')
        propina.text = str(info.infoFactura.propina)

        if info.infoFactura.fleteInternacional:
            etree.SubElement(infoFactura, 'fleteInternacional').text = info.infoFactura.fleteInternacional

        if info.infoFactura.seguroInternacional:
            etree.SubElement(infoFactura, 'seguroInternacional').text = info.infoFactura.seguroInternacional

        if info.infoFactura.gastosAduaneros:
            etree.SubElement(infoFactura, 'gastosAduaneros').text = info.infoFactura.gastosAduaneros
        
        if info.infoFactura.gastosTransporteOtros:
            etree.SubElement(infoFactura, 'gastosTransporteOtros').text = info.infoFactura.gastosTransporteOtros

        importeTotal = etree.SubElement(infoFactura, 'importeTotal')
        importeTotal.text = str(info.infoFactura.importeTotal)
        moneda = etree.SubElement(infoFactura, 'moneda')
        moneda.text = str(info.infoFactura.moneda)

        #Pagos
        pagos = etree.SubElement(infoFactura, 'pagos')
        for pago_info in info.infoFactura.pagos:
            pago = etree.SubElement(pagos, 'pago')

            formaPago = etree.SubElement(pago, 'formaPago')
            formaPago.text = str(pago_info.formaPago)

            total = etree.SubElement(pago, 'total')
            total.text = str(pago_info.total)
            if pago_info.plazo:
                plazo = etree.SubElement(pago, 'plazo')
                plazo.text = str(pago_info.plazo)
            if pago_info.unidadTiempo:
                unidadTiempo = etree.SubElement(pago, 'unidadTiempo')
                unidadTiempo.text = str(pago_info.unidadTiempo)

        
        if info.infoFactura.valorRetIva:
            etree.SubElement(infoFactura, 'valorRetIva').text = info.infoFactura.valorRetIva
        if info.infoFactura.valorRetRenta:
            etree.SubElement(infoFactura, 'valorRetRenta').text = info.infoFactura.valorRetRenta

        #Detalles
        detalles_ = etree.SubElement(root, 'detalles')
        for item in info.detalles:
            detalle = etree.SubElement(detalles_, 'detalle')
            codigoPrincipal = etree.SubElement(detalle, 'codigoPrincipal')
            codigoPrincipal.text = item.codigoPrincipal
            if item.codigoAuxiliar:
                codigoAuxiliar = etree.SubElement(detalle, 'codigoAuxiliar')
                codigoAuxiliar.text = item.codigoAuxiliar
            description = etree.SubElement(detalle, 'descripcion')
            description.text = item.descripcion
            cantidad = etree.SubElement(detalle, 'cantidad')
            cantidad.text = str(item.cantidad)
            precioUnitario = etree.SubElement(detalle, 'precioUnitario')
            precioUnitario.text = str(item.precioUnitario)
            descuento = etree.SubElement(detalle, 'descuento')
            descuento.text = str(item.descuento)
            precioTotalSinImpuesto = etree.SubElement(
                detalle, 'precioTotalSinImpuesto')
            precioTotalSinImpuesto.text = str(item.precioTotalSinImpuesto)
            if item.detallesAdicionales:    
                detallesAdicionales = etree.SubElement(
                    detalle, 'detallesAdicionales')
                for additional in item.detallesAdicionales:
                    campoAdicional = etree.SubElement(
                        detallesAdicionales, 'detAdicional', attrib={'nombre': additional.nombre, 'valor': additional.valor})
                    #campoAdicional.text = additional.valor
            if item.impuestos:
                impuestos = etree.SubElement(detalle, 'impuestos')
                for tax in item.impuestos:
                    impuesto = etree.SubElement(impuestos, 'impuesto')
                    codigo = etree.SubElement(impuesto, 'codigo')
                    codigo.text = str(tax.codigo)
                    codigoPorcentaje = etree.SubElement(
                        impuesto, 'codigoPorcentaje')
                    codigoPorcentaje.text = tax.codigoPorcentaje
                    tarifa = etree.SubElement(impuesto, 'tarifa')
                    tarifa.text = str(tax.tarifa)
                    baseImponible = etree.SubElement(impuesto, 'baseImponible')
                    baseImponible.text = str(tax.baseImponible)
                    valor = etree.SubElement(impuesto, 'valor')
                    valor.text = str(tax.valor)
        
        #Reembolsos
        if info.infoFactura.codDocReembolso and info.infoFactura.codDocReembolso == '41':
            etree.SubElement(infoFactura, 'codDocReembolso').text = info.infoFactura.codDocReembolso
            etree.SubElement(infoFactura, 'totalComprobantesReembolso').text = info.infoFactura.totalComprobantesReembolso
            etree.SubElement(infoFactura, 'totalBaseImponibleReembolso').text = info.infoFactura.totalBaseImponibleReembolso
            etree.SubElement(infoFactura, 'totalImpuestoReembolso').text = info.infoFactura.totalImpuestoReembolso
            if info.infoFactura.reembolsos:
                reembolsos = etree.SubElement(infoFactura, 'reembolsos')
                reembolsoDetalle = etree.SubElement(reembolsos, 'reembolsoDetalle')
                for reembolso in info.infoFactura.reembolsos:
                    etree.SubElement(reembolsoDetalle, 'tipoIdentificacionProveedorReembolso').text = reembolso.tipoIdentificacionProveedorReembolso
                    etree.SubElement(reembolsoDetalle, 'identificacionProveedorReembolso').text = reembolso.identificacionProveedorReembolso
                    etree.SubElement(reembolsoDetalle, 'codPaisPagoProveedorReembolso').text = reembolso.codPaisPagoProveedorReembolso
                    etree.SubElement(reembolsoDetalle, 'tipoProveedorReembolso').text = reembolso.tipoProveedorReembolso
                    etree.SubElement(reembolsoDetalle, 'codDocReembolso').text = reembolso.codDocReembolso
                    etree.SubElement(reembolsoDetalle, 'estabDocReembolso').text = reembolso.estabDocReembolso
                    etree.SubElement(reembolsoDetalle, 'ptoEmiDocReembolso').text = reembolso.ptoEmiDocReembolso
                    etree.SubElement(reembolsoDetalle, 'secuencialDocReembolso').text = reembolso.secuencialDocReembolso
                    etree.SubElement(reembolsoDetalle, 'fechaEmisionDocReembolso').text = reembolso.fechaEmisionDocReembolso
                    etree.SubElement(reembolsoDetalle, 'numeroautorizacionDocReemb').text = reembolso.numeroautorizacionDocReemb
                    detalleImpuestos = etree.SubElement(reembolsoDetalle, 'detalleImpuestos')
                    for impuesto in reembolso.detalleImpuestos:
                        detalleImpuesto = etree.SubElement(detalleImpuestos, 'detalleImpuesto')
                        etree.SubElement(detalleImpuesto, 'codigo').text = impuesto.codigo
                        etree.SubElement(detalleImpuesto, 'codigoPorcentaje').text = impuesto.codigoPorcentaje
                        etree.SubElement(detalleImpuesto, 'baseImponibleReembolso').text = impuesto.baseImponibleReembolso
                        etree.SubElement(detalleImpuesto, 'tarifa').text = impuesto.tarifa
                        etree.SubElement(detalleImpuesto, 'impuestoReembolso').text = impuesto.impuestoReembolso

        #Retenciones
        if info.retenciones:
            retenciones = etree.SubElement(root, 'retenciones')
            for retencion in info.retenciones:
                retencion_element = etree.SubElement(retenciones, 'retencion')
                codigo = etree.SubElement(retencion_element, 'codigo')
                codigo.text = retencion.codigo
                codigoPorcentaje = etree.SubElement(
                    retencion_element, 'codigoPorcentaje')
                codigoPorcentaje.text = str(retencion.codigoPorcentaje)
                tarifa = etree.SubElement(retencion_element, 'tarifa')
                tarifa.text = retencion.tarifa
                valorRetenido = etree.SubElement(
                    retencion_element, 'valor')
                valorRetenido.text = retencion.valor

        #Informacion adicional
        if info.infoAdicional:
            infoAdicional = etree.SubElement(root, 'infoAdicional')
            for item in info.infoAdicional:
                campoAdicional = etree.SubElement(
                    infoAdicional, 'campoAdicional', attrib={'nombre': item.nombre})
                campoAdicional.text = item.valor

        #xml_string = etree.tostring(root, pretty_print=True).decode('utf-8')
        
        xml_bytes = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        )
        
        xml_string = xml_bytes.decode("utf-8")
        return {
            'xmlFile': root,
            'xmlString': xml_string
        }
    except Exception as e:
        print('Error: ' + str(e))
        return {
            'xmlFile': None,
            'xmlString': None,
            'error': str(e)
        }