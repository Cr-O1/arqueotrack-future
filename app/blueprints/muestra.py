"""
Blueprint de Muestras - ArqueoTrack v3.0
Gestión del inventario de muestras y cadena de custodia de laboratorio.
"""

import io
import structlog
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, send_file, Response
from flask_login import login_required, current_user

from app import db
from app.models.muestra import Muestra, ResultadoAnalisis
from app.models.yacimiento import Yacimiento
from app.forms import MuestraForm, EnviarLaboratorioForm, ResultadoAnalisisForm
from app.services.muestra_service import MuestraService
from app.services.audit_service import AuditService

log = structlog.get_logger(__name__)
muestra_bp = Blueprint('muestra', __name__)


def _get_yacimiento_or_403(yacimiento_id: int) -> Yacimiento:
    yac = Yacimiento.query.get_or_404(yacimiento_id)
    if yac.propietario_id != current_user.id and not yac.tiene_colaborador(current_user):
        abort(403)
    return yac


def _choices_ues_hallazgos(yacimiento_id: int):
    from app.models.unidad_estratigrafica import UnidadEstratigrafica
    from app.models.hallazgo import Hallazgo
    from app.models.campana import Campana
    ues = UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id)\
        .order_by(UnidadEstratigrafica.numero_ue).all()
    hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id)\
        .order_by(Hallazgo.id.desc()).limit(100).all()
    campanas = Campana.query.filter_by(yacimiento_id=yacimiento_id)\
        .order_by(Campana.anio.desc()).all()
    return ues, hallazgos, campanas


@muestra_bp.route('/yacimientos/<int:yacimiento_id>/muestras')
@login_required
def listar(yacimiento_id: int):
    """Lista de muestras con filtros opcionales."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    tipo = request.args.get('tipo')
    estado = request.args.get('estado')
    q = Muestra.query.filter_by(yacimiento_id=yacimiento_id)
    if tipo:
        q = q.filter_by(tipo=tipo)
    if estado:
        q = q.filter_by(estado=estado)
    muestras = q.order_by(Muestra.fecha_recogida.desc()).all()
    return render_template('muestras/listar.html', yacimiento=yac, muestras=muestras,
                           tipo_filtro=tipo, estado_filtro=estado)


@muestra_bp.route('/yacimientos/<int:yacimiento_id>/muestras/nueva', methods=['GET', 'POST'])
@login_required
def nueva(yacimiento_id: int):
    """Registra una nueva muestra."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    ues, hallazgos, campanas = _choices_ues_hallazgos(yacimiento_id)
    form = MuestraForm()
    form.ue_id.choices = [(0, '— Sin UE —')] + [(u.id, f'UE {u.numero_ue}') for u in ues]
    form.hallazgo_id.choices = [(0, '— Sin hallazgo —')] + [(h.id, f'#{h.id} {h.nombre[:40]}') for h in hallazgos]
    form.campana_id.choices = [(0, '— Sin campaña —')] + [(c.id, f'{c.anio} · {c.nombre}') for c in campanas]
    if form.validate_on_submit():
        try:
            muestra = MuestraService.crear(
                yacimiento_id=yacimiento_id,
                tipo=form.tipo.data,
                descripcion=form.descripcion.data,
                cantidad=form.cantidad.data,
                peso_gramos=form.peso_gramos.data,
                contenedor=form.contenedor.data,
                lat=form.latitud.data,
                lng=form.longitud.data,
                cota=form.cota.data,
                contexto_extraccion=form.contexto_extraccion.data,
                fecha_recogida=form.fecha_recogida.data,
                condiciones_almacenamiento=form.condiciones_almacenamiento.data,
                ue_id=form.ue_id.data or None,
                hallazgo_id=form.hallazgo_id.data or None,
                campana_id=form.campana_id.data or None,
                recogida_por_id=current_user.id,
            )
            AuditService.registrar('create', 'muestra', muestra.id, yacimiento_id=yacimiento_id)
            flash(f'Muestra {muestra.codigo} registrada.', 'success')
            return redirect(url_for('muestra.detalle', yacimiento_id=yacimiento_id, muestra_id=muestra.id))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('muestras/form.html', form=form, yacimiento=yac, title='Nueva muestra')


@muestra_bp.route('/yacimientos/<int:yacimiento_id>/muestras/<int:muestra_id>')
@login_required
def detalle(yacimiento_id: int, muestra_id: int):
    """Detalle de muestra con historial de resultados."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    muestra = Muestra.query.filter_by(id=muestra_id, yacimiento_id=yacimiento_id).first_or_404()
    form_lab = EnviarLaboratorioForm()
    form_resultado = ResultadoAnalisisForm()
    return render_template('muestras/detalle.html', yacimiento=yac, muestra=muestra,
                           form_lab=form_lab, form_resultado=form_resultado)


@muestra_bp.route('/yacimientos/<int:yacimiento_id>/muestras/<int:muestra_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(yacimiento_id: int, muestra_id: int):
    """Edita una muestra."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    muestra = Muestra.query.filter_by(id=muestra_id, yacimiento_id=yacimiento_id).first_or_404()
    ues, hallazgos, campanas = _choices_ues_hallazgos(yacimiento_id)
    form = MuestraForm(obj=muestra)
    form.ue_id.choices = [(0, '— Sin UE —')] + [(u.id, f'UE {u.numero_ue}') for u in ues]
    form.hallazgo_id.choices = [(0, '— Sin hallazgo —')] + [(h.id, f'#{h.id} {h.nombre[:40]}') for h in hallazgos]
    form.campana_id.choices = [(0, '— Sin campaña —')] + [(c.id, f'{c.anio} · {c.nombre}') for c in campanas]
    if form.validate_on_submit():
        MuestraService.actualizar(muestra_id, **{
            k: v for k, v in form.data.items() if k not in ('submit', 'csrf_token')
        })
        AuditService.registrar('update', 'muestra', muestra_id, yacimiento_id=yacimiento_id)
        flash('Muestra actualizada.', 'success')
        return redirect(url_for('muestra.detalle', yacimiento_id=yacimiento_id, muestra_id=muestra_id))
    return render_template('muestras/form.html', form=form, yacimiento=yac, muestra=muestra, title='Editar muestra')


@muestra_bp.route('/yacimientos/<int:yacimiento_id>/muestras/<int:muestra_id>/laboratorio', methods=['POST'])
@login_required
def enviar_laboratorio(yacimiento_id: int, muestra_id: int):
    """Registra envío de muestra a laboratorio."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    muestra = Muestra.query.filter_by(id=muestra_id, yacimiento_id=yacimiento_id).first_or_404()
    form = EnviarLaboratorioForm()
    if form.validate_on_submit():
        MuestraService.enviar_a_laboratorio(
            muestra_id,
            laboratorio=form.laboratorio.data,
            numero_laboratorio=form.numero_laboratorio.data,
        )
        AuditService.registrar('update', 'muestra', muestra_id,
                               datos_despues={'estado': 'en_laboratorio', 'laboratorio': form.laboratorio.data},
                               yacimiento_id=yacimiento_id)
        flash('Envío a laboratorio registrado.', 'success')
    else:
        flash('Error al procesar el formulario.', 'danger')
    return redirect(url_for('muestra.detalle', yacimiento_id=yacimiento_id, muestra_id=muestra_id))


@muestra_bp.route('/yacimientos/<int:yacimiento_id>/muestras/<int:muestra_id>/resultado', methods=['POST'])
@login_required
def registrar_resultado(yacimiento_id: int, muestra_id: int):
    """Registra el resultado de un análisis de laboratorio."""
    yac = _get_yacimiento_or_403(yacimiento_id)
    muestra = Muestra.query.filter_by(id=muestra_id, yacimiento_id=yacimiento_id).first_or_404()
    form = ResultadoAnalisisForm()
    if form.validate_on_submit():
        MuestraService.registrar_resultado(
            muestra_id,
            tipo_analisis=form.tipo_analisis.data,
            valor_principal=form.valor_principal.data,
            margen_error=form.margen_error.data,
            descripcion=form.descripcion.data,
            interpretacion=form.interpretacion.data,
            metodo=form.metodo.data,
            tecnico=form.tecnico.data,
            referencias=form.referencias.data,
            revisado_por_id=current_user.id,
        )
        AuditService.registrar('create', 'resultado_analisis', muestra_id, yacimiento_id=yacimiento_id)
        flash('Resultado de análisis registrado.', 'success')
    else:
        flash('Error al procesar el formulario.', 'danger')
    return redirect(url_for('muestra.detalle', yacimiento_id=yacimiento_id, muestra_id=muestra_id))


@muestra_bp.route('/yacimientos/<int:yacimiento_id>/muestras/exportar.csv')
@login_required
def exportar_csv(yacimiento_id: int):
    """Exporta el inventario de muestras como CSV."""
    _get_yacimiento_or_403(yacimiento_id)
    csv_content = MuestraService.exportar_inventario_csv(yacimiento_id)
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=muestras_{yacimiento_id}.csv'},
    )


@muestra_bp.route('/yacimientos/<int:yacimiento_id>/muestras/<int:muestra_id>/eliminar', methods=['POST'])
@login_required
def eliminar(yacimiento_id: int, muestra_id: int):
    """Elimina una muestra."""
    yac = Yacimiento.query.get_or_404(yacimiento_id)
    if yac.propietario_id != current_user.id:
        abort(403)
    muestra = Muestra.query.filter_by(id=muestra_id, yacimiento_id=yacimiento_id).first_or_404()
    codigo = muestra.codigo
    db.session.delete(muestra)
    db.session.commit()
    AuditService.registrar('delete', 'muestra', muestra_id, yacimiento_id=yacimiento_id)
    flash(f'Muestra {codigo} eliminada.', 'success')
    return redirect(url_for('muestra.listar', yacimiento_id=yacimiento_id))
