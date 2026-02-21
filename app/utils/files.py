"""
Utilidades para manejo de archivos subidos.
"""

from flask import current_app


def allowed_file(filename: str) -> bool:
    """
    Verifica si la extensión del archivo está permitida.

    Args:
        filename: Nombre del archivo a verificar.

    Returns:
        True si la extensión está permitida.
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
