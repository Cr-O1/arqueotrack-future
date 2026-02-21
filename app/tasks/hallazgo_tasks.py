"""
Tareas asíncronas de procesamiento de imágenes y hallazgos — v4.0
"""
import os
import structlog
from app.tasks.celery_app import celery

log = structlog.get_logger(__name__)


@celery.task(bind=True, max_retries=3, name='app.tasks.hallazgo_tasks.procesar_imagen_hallazgo')
def procesar_imagen_hallazgo(self, hallazgo_id: int, upload_folder: str):
    """
    Genera thumbnails y optimiza la imagen de un hallazgo.
    Se ejecuta en background tras registrar el hallazgo.

    - Thumbnail 300x300 para listas y mapas.
    - Versión optimizada (máx. 1920px, calidad 85) para vista de detalle.
    """
    try:
        from app.models.hallazgo import Hallazgo
        from app import db

        log.info("Procesando imagen hallazgo", hallazgo_id=hallazgo_id)
        hallazgo = Hallazgo.query.get(hallazgo_id)
        if not hallazgo or not hallazgo.foto:
            return {'status': 'skip', 'reason': 'sin foto'}

        foto_path = os.path.join(upload_folder, hallazgo.foto)
        if not os.path.exists(foto_path):
            return {'status': 'skip', 'reason': 'archivo no encontrado'}

        from PIL import Image
        img = Image.open(foto_path)

        # Thumbnail 300x300
        thumb = img.copy()
        thumb.thumbnail((300, 300), Image.LANCZOS)
        nombre_base, ext = os.path.splitext(hallazgo.foto)
        thumb_name = f'{nombre_base}_thumb{ext}'
        thumb.save(os.path.join(upload_folder, thumb_name), optimize=True, quality=80)

        # Versión optimizada (máx. 1920px)
        opt = img.copy()
        if max(opt.size) > 1920:
            opt.thumbnail((1920, 1920), Image.LANCZOS)
        opt_name = f'{nombre_base}_opt{ext}'
        opt.save(os.path.join(upload_folder, opt_name), optimize=True, quality=85)

        # Guardar nombres en el hallazgo
        hallazgo.foto_thumb = thumb_name
        hallazgo.foto_opt = opt_name
        db.session.commit()

        log.info("Imagen procesada", hallazgo_id=hallazgo_id,
                 thumb=thumb_name, opt=opt_name)
        return {'status': 'ok', 'thumb': thumb_name, 'opt': opt_name}

    except Exception as exc:
        log.error("Error procesando imagen", hallazgo_id=hallazgo_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery.task(name='app.tasks.hallazgo_tasks.notificar_nuevo_hallazgo')
def notificar_nuevo_hallazgo(hallazgo_id: int, yacimiento_id: int):
    """
    Notifica a los colaboradores del yacimiento sobre un nuevo hallazgo.
    (Preparado para integración con sistema de email en v6.0+)
    """
    from app.models.hallazgo import Hallazgo
    from app.models.invitacion import Invitacion

    hallazgo = Hallazgo.query.get(hallazgo_id)
    if not hallazgo:
        return

    colaboradores = Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id, estado='aceptada'
    ).all()

    log.info("Notificación nuevo hallazgo",
             hallazgo_id=hallazgo_id,
             colaboradores=len(colaboradores),
             codigo=hallazgo.codigo_acceso)

    # TODO (v6.0): enviar email real con Flask-Mail
    # for inv in colaboradores:
    #     mail.send_message(
    #         subject=f'Nuevo hallazgo en {hallazgo.yacimiento.nombre}',
    #         recipients=[inv.invitado.email],
    #         body=f'Se ha registrado un nuevo hallazgo: {hallazgo.codigo_acceso}'
    #     )

    return {'status': 'ok', 'notificados': len(colaboradores)}
