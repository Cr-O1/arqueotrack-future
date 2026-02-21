"""
Utilidades de seguridad.
"""

from urllib.parse import urlparse, urljoin
from flask import request


def is_safe_url(target: str) -> bool:
    """
    Verifica que una URL de redirección sea segura (mismo host).
    Previene ataques de redirección abierta.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ('http', 'https')
        and ref_url.netloc == test_url.netloc
    )
