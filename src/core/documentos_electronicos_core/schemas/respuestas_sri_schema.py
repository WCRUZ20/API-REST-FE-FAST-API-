# respuestas_sri_schema.py

SRI_ERROR_CODE_MAPPING = {
    "2": "3",   # RUC NO ACTIVO → No autorizado
    "10": "3",  # Establecimiento clausurado → No autorizado
    "26": "6",  # Tamaño máximo superado → Devuelta
    "27": "3",  # Clase no permitido → No autorizado
    "28": "6",  # Acuerdo de medios electronicos no aceptado → Devuelta
    "35": "6",  # Documento invalido → Devuelta
    "36": "6",  # Version del esquema descontinuado → Devuelta
    "37": "4",  # RUC sin autorizacion de emisión → Validar datos
    "39": "4",  # Firma electronica del emisor no es valida → Validar datos
    "40": "4",  # Error en el certificado → Validar datos
    "43": "5",  # En proceso SRI → En proceso
    "56": "3",  #Establecimiento cerrado → No autorizado
    "65": "6",  #Fecha de emisión extemporánea → Devuelta
    "99": "7",  # Error en consulta → Error de consulta
}

SRI_STATE_MAPPING = {
    "NO ENVIADO": "0",  # No enviado
    "EN PROCESO": "1",  # Enviado al SRI
    "AUTORIZADO": "2",
    "NO AUTORIZADO": "3",
    "VALIDAR DATOS": "4",  # personalizado por mensaje
    "EN PROCESO SRI": "5",
    "DEVUELTA": "6",
    "ANULADO": "11"
}

DEFAULT_ERROR_CODE = "0"  # No enviado

def map_sri_status_to_custom(sri_status: str, identificador: str = "") -> str:
    estado = ""
    if sri_status:
        estado += sri_status.strip().upper()
    else:
        estado += "NO ENVIADO"
    identificador = identificador.strip()

    # Si el SRI devuelve un código de error conocido
    if identificador in SRI_ERROR_CODE_MAPPING:
        return SRI_ERROR_CODE_MAPPING[identificador]

    # Mapeo por estado directo
    if estado in SRI_STATE_MAPPING:
        return SRI_STATE_MAPPING[estado]

    return DEFAULT_ERROR_CODE
