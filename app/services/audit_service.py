"""
Servicio de Auditoría — ArqueoTrack 2.0 (v2.0)
Centraliza el registro del audit trail para todas las operaciones críticas.
"""
import structlog
from functools import wraps
from flask_login import current_user
from app import db
from app.models.audit_log import AuditLog

log = structlog.get_logger(__name__)


class AuditService:

    @staticmethod
    def registrar(operacion: str, entidad_tipo: str, entidad_id: int = None,
                  datos_antes: dict = None, datos_despues: dict = None,
                  yacimiento_id: int = None, institucion_id: int = None,
                  exitoso: bool = True, mensaje_error: str = None):
        """Registra una operación en el audit trail."""
        try:
            user_id = current_user.id if current_user and current_user.is_authenticated else None
        except Exception:
            user_id = None

        AuditLog.registrar(
            operacion=operacion, entidad_tipo=entidad_tipo, entidad_id=entidad_id,
            usuario_id=user_id, datos_antes=datos_antes, datos_despues=datos_despues,
            yacimiento_id=yacimiento_id, institucion_id=institucion_id,
            exitoso=exitoso, mensaje_error=mensaje_error,
        )
        # No hacemos commit aquí; se incluye en la transacción del llamador.

    @staticmethod
    def auditado(operacion: str, entidad_tipo: str, yacimiento_id_campo: str = None):
        """
        Decorador que registra automáticamente el audit trail de una función de servicio.

        Uso:
            @AuditService.auditado('create', 'hallazgo', yacimiento_id_campo='yacimiento_id')
            def crear_hallazgo(user_id, yacimiento_id, datos):
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    resultado = func(*args, **kwargs)
                    yac_id = kwargs.get(yacimiento_id_campo) if yacimiento_id_campo else None
                    ent_id = getattr(resultado, 'id', None)
                    AuditService.registrar(
                        operacion=operacion, entidad_tipo=entidad_tipo,
                        entidad_id=ent_id, yacimiento_id=yac_id,
                        exitoso=True,
                    )
                    return resultado
                except Exception as e:
                    AuditService.registrar(
                        operacion=operacion, entidad_tipo=entidad_tipo,
                        exitoso=False, mensaje_error=str(e),
                    )
                    raise
            return wrapper
        return decorator

    @staticmethod
    def obtener_historial_yacimiento(yacimiento_id: int, limite: int = 50) -> list:
        return (AuditLog.query
                .filter_by(yacimiento_id=yacimiento_id)
                .order_by(AuditLog.fecha.desc())
                .limit(limite)
                .all())

    @staticmethod
    def obtener_historial_usuario(user_id: int, limite: int = 100) -> list:
        return (AuditLog.query
                .filter_by(usuario_id=user_id)
                .order_by(AuditLog.fecha.desc())
                .limit(limite)
                .all())
