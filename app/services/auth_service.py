"""
Servicio de Autenticación.
"""

import structlog
from app import db
from app.models.user import Usuario

log = structlog.get_logger(__name__)


class AuthService:

    @staticmethod
    def registrar(datos: dict) -> Usuario:
        """
        Registra un nuevo usuario.

        Args:
            datos: Diccionario con los campos del usuario.

        Returns:
            Usuario creado.

        Raises:
            ValueError: Si el username o email ya están en uso.
        """
        if Usuario.query.filter_by(nombre_usuario=datos.get('nombre_usuario')).first():
            raise ValueError('El nombre de usuario ya está en uso.')
        if Usuario.query.filter_by(email=datos.get('email')).first():
            raise ValueError('El correo electrónico ya está registrado.')

        log.info("Registrando usuario", email=datos.get('email'))
        usuario = Usuario(
            nombre_usuario=datos['nombre_usuario'],
            nombre=datos['nombre'],
            apellidos=datos['apellidos'],
            email=datos['email'],
            fecha_nacimiento=datos['fecha_nacimiento'],
            ocupacion=datos.get('ocupacion'),
        )
        usuario.set_password(datos['contraseña'])
        db.session.add(usuario)
        db.session.commit()
        log.info("Usuario registrado", user_id=usuario.id)
        return usuario

    @staticmethod
    def autenticar(email: str, contraseña: str):
        """
        Verifica credenciales.

        Returns:
            Usuario si las credenciales son válidas, None si no.
        """
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.check_password(contraseña):
            return usuario
        return None

    @staticmethod
    def eliminar_cuenta(usuario: Usuario) -> None:
        """Elimina la cuenta y todos sus datos."""
        log.warning("Eliminando cuenta", user_id=usuario.id)
        db.session.delete(usuario)
        db.session.commit()
