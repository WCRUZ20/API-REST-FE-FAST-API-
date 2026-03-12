import barcode
import base64

from barcode.writer import ImageWriter
from io import BytesIO

def generar_codigo_barras_base64(numero_codigo):
    barcode_type = barcode.get_barcode_class('code128')
    buffer = BytesIO()

    codigo_barras = barcode_type(numero_codigo, writer=ImageWriter())
    
    # Opcional: definir tamaño y DPI
    options = {
        "module_height": 20.0,  # más alto
        "module_width": 0.3,
        "font_size": 10,
        "text_distance": 5.0,   # espacio entre código y texto
        "quiet_zone": 6.5       # margen horizontal
        }

    codigo_barras.write(buffer, options)

    imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return imagen_base64
