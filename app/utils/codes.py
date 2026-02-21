"""
Generador de códigos únicos para hallazgos.
"""

import random
import string


def generar_codigo_unico(longitud: int = 10) -> str:
    """
    Genera un código alfanumérico único en mayúsculas.

    Args:
        longitud: Número de caracteres del código (default: 10).

    Returns:
        Código alfanumérico aleatorio.
    """
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choices(caracteres, k=longitud))
