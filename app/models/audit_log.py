"""
Modelo de Auditoría (Audit Trail) para ArqueoTrack 2.0 (v2.0).
Registra todas las operaciones de creación, edición y eliminación.
"""

from datetime import datetime
from app import db


class AuditLog(db.Model):
    """
    Registro inmutable de auditoría.
    Se crea automáticamente en cada operación importante del sistema.
    """

    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    # Quién
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'),
                            nullable=True, index=True)
    ip_address = db.Column(db.String(45))  # IPv4 o IPv6
    user_agent = db.Column(db.String(300))

    # Qué entidad
    entidad_tipo = db.Column(db.String(50), nullable=False, index=True)
    # hallazgo | yacimiento | sector | fase | ue | muestra | institucion | campana | usuario

    entidad_id = db.Column(db.Integer, index=True)
    entidad_codigo = db.Column(db.String(50))   # código legible (ej: código_acceso del hallazgo)

    # Qué operación
    operacion = db.Column(db.String(20), nullable=False)
    # create | update | delete | login | logout | export | invite

    # Datos del cambio
    datos_antes = db.Column(db.Text)   # JSON snapshot antes
    datos_despues = db.Column(db.Text)  # JSON snapshot después
    campos_modificados = db.Column(db.Text)  # JSON lista de campos

    # Contexto
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id', ondelete='SET NULL'),
                               nullable=True, index=True)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id', ondelete='SET NULL'),
                                nullable=True)

    # Resultado
    exitoso = db.Column(db.Boolean, default=True)
    mensaje_error = db.Column(db.Text)

    # Timestamp (inmutable)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relaciones (read-only, sin cascade)
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])

    __table_args__ = (
        db.Index('idx_audit_entidad', 'entidad_tipo', 'entidad_id'),
        db.Index('idx_audit_fecha_usuario', 'fecha', 'usuario_id'),
        db.Index('idx_audit_operacion', 'operacion'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'entidad_tipo': self.entidad_tipo,
            'entidad_id': self.entidad_id,
            'operacion': self.operacion,
            'exitoso': self.exitoso,
            'fecha': self.fecha.isoformat(),
        }

    def __repr__(self):
        return f'<AuditLog {self.operacion} {self.entidad_tipo}#{self.entidad_id} by user#{self.usuario_id}>'

    # Timestamp
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relaciones
    usuario = db.relationship('Usuario', back_populates='audit_logs')

    __table_args__ = (
        db.Index('idx_audit_entidad', 'entidad_tipo', 'entidad_id'),
        db.Index('idx_audit_yacimiento', 'yacimiento_id'),
        db.Index('idx_audit_fecha', 'fecha'),
    )

    @classmethod
    def registrar(cls, operacion: str, entidad_tipo: str, entidad_id: int = None,
                  usuario_id: int = None, datos_antes: dict = None, datos_despues: dict = None,
                  yacimiento_id: int = None, institucion_id: int = None,
                  exitoso: bool = True, mensaje_error: str = None):
        """Crea un registro de auditoría."""
        import json
        from flask import request as flask_request
        try:
            ip = flask_request.remote_addr
            ua = flask_request.user_agent.string[:300] if flask_request.user_agent else ''
        except RuntimeError:
            ip, ua = None, None

        log = cls(
            operacion=operacion, entidad_tipo=entidad_tipo, entidad_id=entidad_id,
            usuario_id=usuario_id,
            ip_address=ip, user_agent=ua,
            datos_antes=json.dumps(datos_antes) if datos_antes else None,
            datos_despues=json.dumps(datos_despues) if datos_despues else None,
            yacimiento_id=yacimiento_id, institucion_id=institucion_id,
            exitoso=exitoso, mensaje_error=mensaje_error,
        )
        from app import db as _db
        _db.session.add(log)
        return log

    def __repr__(self):
        return f'<AuditLog {self.operacion} {self.entidad_tipo}#{self.entidad_id}>'
