"""
Servicio de Muestras y Análisis — ArqueoTrack 2.0 (v3.0)
"""
import structlog
from app import db, cache
from app.models.muestra import Muestra, ResultadoAnalisis

log = structlog.get_logger(__name__)


class MuestraService:

    @staticmethod
    def crear(yacimiento_id: int, recogida_por_id: int, datos: dict) -> Muestra:
        log.info("Creando muestra", yacimiento_id=yacimiento_id, tipo=datos.get('tipo'))
        muestra = Muestra(
            yacimiento_id=yacimiento_id,
            recogida_por_id=recogida_por_id,
            **datos,
        )
        db.session.add(muestra)
        db.session.commit()
        log.info("Muestra creada", muestra_id=muestra.id, codigo=muestra.codigo)
        return muestra

    @staticmethod
    def actualizar(muestra: Muestra, datos: dict) -> Muestra:
        for campo, valor in datos.items():
            if hasattr(muestra, campo):
                setattr(muestra, campo, valor)
        db.session.commit()
        return muestra

    @staticmethod
    def enviar_a_laboratorio(muestra: Muestra, laboratorio: str,
                              numero_laboratorio: str = None) -> Muestra:
        from datetime import datetime
        muestra.estado = 'en_laboratorio'
        muestra.laboratorio = laboratorio
        muestra.numero_laboratorio = numero_laboratorio
        muestra.fecha_envio_laboratorio = datetime.utcnow()
        db.session.commit()
        log.info("Muestra enviada a laboratorio", muestra_id=muestra.id, lab=laboratorio)
        return muestra

    @staticmethod
    def registrar_resultado(muestra_id: int, tipo_analisis: str, datos: dict,
                             revisor_id: int = None) -> ResultadoAnalisis:
        """Registra el resultado de un análisis y actualiza el estado de la muestra."""
        muestra = Muestra.query.get_or_404(muestra_id)
        resultado = ResultadoAnalisis(
            muestra_id=muestra_id,
            tipo_analisis=tipo_analisis,
            revisor_id=revisor_id,
            **datos,
        )
        db.session.add(resultado)
        muestra.estado = 'resultado_disponible'
        from datetime import datetime
        muestra.fecha_recepcion_resultados = datetime.utcnow()
        db.session.commit()
        log.info("Resultado registrado", muestra_id=muestra_id, tipo=tipo_analisis)
        return resultado

    @staticmethod
    def exportar_inventario_csv(yacimiento_id: int) -> str:
        """Genera un CSV con el inventario de muestras de un yacimiento."""
        import io, csv
        muestras = Muestra.query.filter_by(yacimiento_id=yacimiento_id).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Código', 'Tipo', 'Estado', 'UE', 'Hallazgo',
                         'Laboratorio', 'Fecha recogida', 'Tiene resultado'])
        for m in muestras:
            writer.writerow([
                m.codigo, m.tipo, m.estado,
                m.ue.numero_ue if m.ue else '',
                m.hallazgo.codigo_acceso if m.hallazgo else '',
                m.laboratorio or '', m.fecha_recogida or '',
                'Sí' if m.tiene_resultado else 'No',
            ])
        return output.getvalue()
