"""
Utilidades de fecha y tiempo.
"""

from datetime import datetime


def time_ago(dt: datetime) -> str:
    """
    Retorna una representación legible del tiempo transcurrido.

    Args:
        dt: Fecha/hora de referencia.

    Returns:
        Cadena como 'hace 3 horas', 'hace 2 días', etc.
    """
    if not dt:
        return 'desconocido'

    now = datetime.utcnow()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return 'hace un momento'
    elif seconds < 3600:
        minutos = int(seconds / 60)
        return f'hace {minutos} minuto{"s" if minutos != 1 else ""}'
    elif seconds < 86400:
        horas = int(seconds / 3600)
        return f'hace {horas} hora{"s" if horas != 1 else ""}'
    elif seconds < 604800:
        dias = int(seconds / 86400)
        return f'hace {dias} día{"s" if dias != 1 else ""}'
    elif seconds < 2592000:
        semanas = int(seconds / 604800)
        return f'hace {semanas} semana{"s" if semanas != 1 else ""}'
    elif seconds < 31536000:
        meses = int(seconds / 2592000)
        return f'hace {meses} mes{"es" if meses != 1 else ""}'
    else:
        años = int(seconds / 31536000)
        return f'hace {años} año{"s" if años != 1 else ""}'
