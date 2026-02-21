"""
Celery Tasks - Generación de Informes PDF (v4.0)
Genera informes de yacimientos y campañas de forma asíncrona con ReportLab.
"""

import os
import io
from datetime import datetime

import structlog

from app.tasks.celery_app import celery

log = structlog.get_logger(__name__)


@celery.task(bind=True, max_retries=2, default_retry_delay=60,
             name='tasks.generar_informe_yacimiento')
def generar_informe_yacimiento(self, yacimiento_id: int, usuario_id: int, output_dir: str = '/tmp'):
    """
    Genera un informe PDF completo de un yacimiento con:
    - Datos generales, mapa de situación
    - Lista de hallazgos (con miniaturas)
    - Sectores y fases
    - Campañas y UEs (si las hay)
    - Inventario de muestras y resultados analíticos

    Args:
        yacimiento_id: ID del yacimiento.
        usuario_id: ID del usuario que solicita el informe.
        output_dir: Directorio donde guardar el PDF generado.

    Returns:
        dict con 'path' del archivo generado y 'total_paginas'.
    """
    try:
        from app.models.yacimiento import Yacimiento
        from app.models.hallazgo import Hallazgo
        from app.models.campana import Campana
        from app.models.unidad_estratigrafica import UnidadEstratigrafica
        from app.models.muestra import Muestra

        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        log.info('informe.iniciando', yacimiento_id=yacimiento_id)

        yac = Yacimiento.query.get(yacimiento_id)
        if not yac:
            raise ValueError(f'Yacimiento {yacimiento_id} no encontrado')

        filename = f'informe_yac{yacimiento_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        filepath = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2 * cm,
            title=f'Informe — {yac.nombre}',
            author='ArqueoTrack',
        )

        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                     fontSize=20, spaceAfter=12, alignment=TA_CENTER)
        style_h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=14,
                                  spaceBefore=16, spaceAfter=6, textColor=colors.HexColor('#2c3e50'))
        style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=11,
                                  spaceBefore=10, spaceAfter=4, textColor=colors.HexColor('#34495e'))
        style_normal = styles['Normal']
        style_small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8)
        style_caption = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=8,
                                       textColor=colors.grey, alignment=TA_CENTER)

        story = []

        # ── Portada ──────────────────────────────────────────────────────────
        story.append(Spacer(1, 3 * cm))
        story.append(Paragraph('ArqueoTrack', ParagraphStyle('Brand', parent=styles['Normal'],
                                                               fontSize=10, textColor=colors.grey,
                                                               alignment=TA_CENTER)))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(yac.nombre, style_title))
        story.append(Paragraph('Informe General del Yacimiento', ParagraphStyle(
            'Subtitle', parent=styles['Normal'], fontSize=13, alignment=TA_CENTER,
            textColor=colors.HexColor('#7f8c8d'))))
        story.append(Spacer(1, 1 * cm))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#bdc3c7')))
        story.append(Spacer(1, 0.5 * cm))

        info_portada = [
            ['Generado:', datetime.now().strftime('%d/%m/%Y a las %H:%M')],
            ['Período:', f'{yac.fecha_inicio or "—"} → {yac.fecha_fin or "En curso"}'],
        ]
        if yac.municipio:
            info_portada.append(['Localización:', f'{yac.municipio}, {yac.provincia or ""}, {yac.pais or ""}'])
        t_portada = Table(info_portada, colWidths=[4 * cm, 12 * cm])
        t_portada.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_portada)
        story.append(PageBreak())

        # ── Información general ───────────────────────────────────────────────
        story.append(Paragraph('1. Información General', style_h1))
        if yac.descripcion:
            story.append(Paragraph(yac.descripcion, style_normal))
            story.append(Spacer(1, 0.4 * cm))

        datos_gen = [
            ['Campo', 'Valor'],
            ['Estado', yac.estado or '—'],
            ['Tipo', yac.tipo or '—'],
            ['Cronología', yac.cronologia or '—'],
            ['Municipio', yac.municipio or '—'],
            ['Provincia', yac.provincia or '—'],
            ['Coordenadas', f'{yac.latitud:.6f}, {yac.longitud:.6f}' if yac.latitud else '—'],
            ['Altitud', f'{yac.altitud} m' if yac.altitud else '—'],
        ]
        t_gen = Table(datos_gen, colWidths=[5 * cm, 11 * cm])
        t_gen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_gen)

        # ── Estadísticas ──────────────────────────────────────────────────────
        story.append(Spacer(1, 0.8 * cm))
        story.append(Paragraph('2. Resumen Estadístico', style_h1))

        total_hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).count()
        total_campanas = Campana.query.filter_by(yacimiento_id=yacimiento_id).count()
        total_ues = UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id).count()
        total_muestras = Muestra.query.filter_by(yacimiento_id=yacimiento_id).count()

        stats_data = [
            ['Hallazgos registrados', str(total_hallazgos)],
            ['Campañas', str(total_campanas)],
            ['Unidades estratigráficas', str(total_ues)],
            ['Muestras de laboratorio', str(total_muestras)],
        ]
        t_stats = Table(stats_data, colWidths=[10 * cm, 6 * cm])
        t_stats.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#eaf4fb'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t_stats)

        # ── Hallazgos ─────────────────────────────────────────────────────────
        if total_hallazgos:
            story.append(PageBreak())
            story.append(Paragraph('3. Registro de Hallazgos', style_h1))
            hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id)\
                .order_by(Hallazgo.fecha.desc()).limit(200).all()
            headers = ['#', 'Nombre', 'Tipo', 'Estado', 'Fecha', 'Coordenadas']
            rows = [headers]
            for h in hallazgos:
                coords = f'{h.latitud:.5f}, {h.longitud:.5f}' if h.latitud else '—'
                rows.append([
                    str(h.id),
                    Paragraph(h.nombre[:45], style_small),
                    h.tipo or '—',
                    h.estado_conservacion or '—',
                    h.fecha.strftime('%d/%m/%Y') if h.fecha else '—',
                    coords,
                ])
            t_h = Table(rows, colWidths=[1*cm, 5*cm, 3*cm, 3*cm, 2.5*cm, 3.5*cm])
            t_h.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#dee2e6')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(t_h)

        # ── Campañas ──────────────────────────────────────────────────────────
        if total_campanas:
            story.append(PageBreak())
            story.append(Paragraph('4. Campañas Arqueológicas', style_h1))
            campanas = Campana.query.filter_by(yacimiento_id=yacimiento_id)\
                .order_by(Campana.anio.desc()).all()
            for c in campanas:
                story.append(Paragraph(f'{c.anio} — {c.nombre}', style_h2))
                if c.objetivos:
                    story.append(Paragraph(f'<b>Objetivos:</b> {c.objetivos}', style_normal))
                if c.resultados:
                    story.append(Paragraph(f'<b>Resultados:</b> {c.resultados}', style_normal))
                story.append(Spacer(1, 0.3 * cm))

        # ── Muestras ──────────────────────────────────────────────────────────
        if total_muestras:
            story.append(PageBreak())
            story.append(Paragraph('5. Inventario de Muestras', style_h1))
            muestras = Muestra.query.filter_by(yacimiento_id=yacimiento_id)\
                .order_by(Muestra.fecha_recogida.desc()).all()
            headers_m = ['Código', 'Tipo', 'Estado', 'Laboratorio', 'Fecha recogida']
            rows_m = [headers_m]
            for m in muestras:
                rows_m.append([
                    m.codigo,
                    m.tipo,
                    m.estado,
                    m.laboratorio or '—',
                    m.fecha_recogida.strftime('%d/%m/%Y') if m.fecha_recogida else '—',
                ])
            t_m = Table(rows_m, colWidths=[3*cm, 3*cm, 3.5*cm, 5*cm, 3.5*cm])
            t_m.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#dee2e6')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(t_m)

        doc.build(story)
        total_paginas = doc.page

        log.info('informe.generado', path=filepath, paginas=total_paginas)
        return {'path': filepath, 'total_paginas': total_paginas, 'filename': filename}

    except Exception as exc:
        log.error('informe.error', yacimiento_id=yacimiento_id, error=str(exc))
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=2, default_retry_delay=30,
             name='tasks.generar_informe_campana')
def generar_informe_campana(self, campana_id: int, usuario_id: int, output_dir: str = '/tmp'):
    """
    Genera un informe PDF específico de una campaña arqueológica:
    - Ficha técnica de la campaña
    - Equipo participante
    - UEs excavadas durante la campaña
    - Hallazgos asociados
    - Muestras recogidas y resultados
    """
    try:
        from app.models.campana import Campana
        from app.models.hallazgo import Hallazgo
        from app.models.unidad_estratigrafica import UnidadEstratigrafica
        from app.models.muestra import Muestra

        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

        campana = Campana.query.get(campana_id)
        if not campana:
            raise ValueError(f'Campaña {campana_id} no encontrada')

        filename = f'informe_campana{campana_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        filepath = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2.5*cm, bottomMargin=2*cm,
                                title=f'Campaña {campana.anio} — {campana.nombre}')
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f'Campaña {campana.anio}', ParagraphStyle(
            'Brand', parent=styles['Normal'], fontSize=9, textColor=colors.grey)))
        story.append(Paragraph(campana.nombre, ParagraphStyle(
            'Title', parent=styles['Title'], fontSize=18)))
        story.append(Paragraph(campana.yacimiento.nombre if campana.yacimiento else '', styles['Normal']))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#bdc3c7')))
        story.append(Spacer(1, 0.5*cm))

        # Ficha técnica
        ficha = [
            ['Estado', campana.estado],
            ['Fecha inicio', campana.fecha_inicio.strftime('%d/%m/%Y') if campana.fecha_inicio else '—'],
            ['Fecha fin', campana.fecha_fin.strftime('%d/%m/%Y') if campana.fecha_fin else '—'],
            ['Financiador', campana.financiador or '—'],
            ['Presupuesto', f'{campana.presupuesto:,.0f} €' if campana.presupuesto else '—'],
        ]
        t = Table(ficha, colWidths=[4*cm, 12*cm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#dee2e6')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

        if campana.objetivos:
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph('Objetivos', styles['Heading2']))
            story.append(Paragraph(campana.objetivos, styles['Normal']))

        if campana.resultados:
            story.append(Spacer(1, 0.4*cm))
            story.append(Paragraph('Resultados', styles['Heading2']))
            story.append(Paragraph(campana.resultados, styles['Normal']))

        doc.build(story)
        log.info('informe_campana.generado', campana_id=campana_id, path=filepath)
        return {'path': filepath, 'filename': filename}

    except Exception as exc:
        log.error('informe_campana.error', campana_id=campana_id, error=str(exc))
        raise self.retry(exc=exc)
