"""
Servicio de Matriz de Harris — ArqueoTrack 2.0 (v3.0)
Implementa la ordenación topológica, detección de ciclos y exportación
del diagrama estratigráfico (Matriz de Harris).
"""
import json
import structlog
from collections import defaultdict, deque
from typing import List, Dict, Tuple, Optional

from app import db
from app.models.unidad_estratigrafica import UnidadEstratigrafica, RelacionUE

log = structlog.get_logger(__name__)


class HarrisService:
    """
    Servicio completo para gestión de la Matriz de Harris.

    La Matriz de Harris es un diagrama estratigráfico que muestra las relaciones
    cronológicas relativas entre Unidades Estratigráficas (UE):
    - Abajo = más antiguo
    - Arriba = más reciente
    - Flecha = "es anterior a"
    """

    @staticmethod
    def añadir_relacion(ue_posterior_id: int, ue_anterior_id: int,
                        tipo: str = 'cubre', notas: str = None, **kwargs) -> RelacionUE:
        """
        Añade una relación estratigráfica.

        Args:
            ue_posterior_id: UE más reciente (la que cubre / corta).
            ue_anterior_id: UE más antigua (la que es cubierta / cortada).
            tipo: tipo de relación (cubre, corta, rellena, etc.)

        Raises:
            ValueError: Si la relación crearía un ciclo estratigráfico.
        """
        tipo = kwargs.pop('tipo_relacion', tipo)
        if ue_posterior_id == ue_anterior_id:
            raise ValueError('Una UE no puede relacionarse con la misma UE.')

        # Comprobar que no existe ya
        existente = RelacionUE.query.filter_by(
            ue_posterior_id=ue_posterior_id, ue_anterior_id=ue_anterior_id
        ).first()
        if existente:
            raise ValueError('Esta relación estratigráfica ya existe.')

        # Verificar que no crea un ciclo
        ue_posterior = UnidadEstratigrafica.query.get(ue_posterior_id)
        ue_anterior = UnidadEstratigrafica.query.get(ue_anterior_id)
        if not ue_posterior or not ue_anterior:
            raise ValueError('Una de las UEs no existe.')
        if ue_posterior.yacimiento_id != ue_anterior.yacimiento_id:
            raise ValueError('Las UEs deben pertenecer al mismo yacimiento.')

        yacimiento_id = ue_posterior.yacimiento_id
        if HarrisService._crearía_ciclo(yacimiento_id, ue_posterior_id, ue_anterior_id):
            raise ValueError(
                f'Añadir esta relación crearía un ciclo estratigráfico '
                f'(UE#{ue_posterior_id} → UE#{ue_anterior_id}).'
            )

        relacion = RelacionUE(
            ue_posterior_id=ue_posterior_id, ue_anterior_id=ue_anterior_id,
            tipo_relacion=tipo, notas=notas,
        )
        db.session.add(relacion)
        db.session.commit()
        log.info("Relación Harris añadida", posterior=ue_posterior_id, anterior=ue_anterior_id)
        return relacion

    @staticmethod
    def eliminar_relacion(relacion_id: int) -> None:
        relacion = RelacionUE.query.get_or_404(relacion_id)
        db.session.delete(relacion)
        db.session.commit()

    @staticmethod
    def ordenacion_topologica(yacimiento_id: int) -> List[UnidadEstratigrafica]:
        """
        Devuelve las UEs ordenadas cronológicamente (Kahn's algorithm).
        Primero las más antiguas (sin predecesores), al final las más recientes.

        Returns:
            Lista ordenada de UEs (más antigua → más reciente).

        Raises:
            ValueError: Si el grafo tiene ciclos.
        """
        ues = UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id).all()
        ue_map = {ue.id: ue for ue in ues}

        # Grafo: anterior_id → {posterior_ids}
        grafo = defaultdict(set)
        in_degree = defaultdict(int)
        for ue in ues:
            in_degree[ue.id] = in_degree.get(ue.id, 0)

        relaciones = RelacionUE.query.filter(
            RelacionUE.ue_posterior_id.in_(list(ue_map.keys()))
        ).all()

        for rel in relaciones:
            grafo[rel.ue_anterior_id].add(rel.ue_posterior_id)
            in_degree[rel.ue_posterior_id] = in_degree.get(rel.ue_posterior_id, 0) + 1
            if rel.ue_anterior_id not in in_degree:
                in_degree[rel.ue_anterior_id] = 0

        # Kahn's algorithm
        cola = deque([uid for uid, deg in in_degree.items() if deg == 0])
        ordenadas = []

        while cola:
            uid = cola.popleft()
            if uid in ue_map:
                ordenadas.append(ue_map[uid])
            for sucesor_id in grafo[uid]:
                in_degree[sucesor_id] -= 1
                if in_degree[sucesor_id] == 0:
                    cola.append(sucesor_id)

        if len(ordenadas) < len(ues):
            raise ValueError('El grafo estratigráfico contiene ciclos. Revisa las relaciones.')

        return ordenadas

    @staticmethod
    def exportar_json(yacimiento_id: int) -> dict:
        """
        Exporta la matriz como grafo JSON (compatible con D3.js y Vis.js).
        """
        ues = UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id).all()
        relaciones = RelacionUE.query.filter(
            RelacionUE.ue_posterior_id.in_([ue.id for ue in ues])
        ).all()

        nodos = [{
            'id': ue.id,
            'label': f'UE-{ue.numero_ue}',
            'tipo': ue.tipo,
            'descripcion': ue.descripcion or '',
            'color_munsell': ue.color_munsell or '',
            'excavada': ue.excavada,
            'total_hallazgos': ue.total_hallazgos,
        } for ue in ues]

        aristas = [{
            'id': rel.id,
            'from': rel.ue_anterior_id,
            'to': rel.ue_posterior_id,
            'tipo': rel.tipo_relacion,
            'confirmada': rel.confirmada,
        } for rel in relaciones]

        return {'nodes': nodos, 'edges': aristas}

    @staticmethod
    def exportar_graphml(yacimiento_id: int) -> str:
        """
        Exporta la Matriz de Harris en formato GraphML para software especializado
        (Harris Matrix Composer, Stratify, etc.).
        """
        data = HarrisService.exportar_json(yacimiento_id)
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/graphml">',
            '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
            '  <key id="tipo" for="node" attr.name="tipo" attr.type="string"/>',
            '  <key id="relacion" for="edge" attr.name="relacion" attr.type="string"/>',
            '  <graph id="harris" edgedefault="directed">',
        ]
        for node in data['nodes']:
            lines.append(f'    <node id="UE{node["id"]}">')
            lines.append(f'      <data key="label">{node["label"]}</data>')
            lines.append(f'      <data key="tipo">{node["tipo"]}</data>')
            lines.append('    </node>')
        for edge in data['edges']:
            lines.append(f'    <edge source="UE{edge["from"]}" target="UE{edge["to"]}">')
            lines.append(f'      <data key="relacion">{edge["tipo"]}</data>')
            lines.append('    </edge>')
        lines += ['  </graph>', '</graphml>']
        return '\n'.join(lines)

    @staticmethod
    def validar_coherencia(yacimiento_id: int):
        """
        Valida la coherencia de la Matriz de Harris.

        Returns:
            Lista de mensajes de error/advertencia. Vacía si todo está bien.
        """
        errores = []
        ues = UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id).all()

        # 1. Detectar ciclos
        try:
            HarrisService.ordenacion_topologica(yacimiento_id)
        except ValueError:
            errores.append('⛔ Se detectaron relaciones circulares en la Matriz de Harris.')

        # 2. Validar cotas
        for ue in ues:
            if ue.cota_superior is not None and ue.cota_inferior is not None:
                if ue.cota_superior < ue.cota_inferior:
                    errores.append(
                        f'⚠️ UE #{ue.numero_ue}: cota superior ({ue.cota_superior}) '
                        f'es menor que cota inferior ({ue.cota_inferior}).'
                    )

        # 3. UEs sin relaciones (advertencia, no error)
        ids_con_relacion = set()
        for rel in RelacionUE.query.filter(
            RelacionUE.ue_posterior_id.in_([ue.id for ue in ues])
        ).all():
            ids_con_relacion.add(rel.ue_posterior_id)
            ids_con_relacion.add(rel.ue_anterior_id)

        ues_aisladas = [ue for ue in ues if ue.id not in ids_con_relacion]
        if ues_aisladas:
            nums = ', '.join(f'#{ue.numero_ue}' for ue in ues_aisladas)
            errores.append(f'ℹ️ UEs sin relaciones estratigráficas: {nums}')

        return {'tiene_ciclos': any('circulares' in e for e in errores), 'errores': errores}

    @staticmethod
    def _crearía_ciclo(yacimiento_id: int, nuevo_posterior_id: int,
                        nuevo_anterior_id: int) -> bool:
        """
        Verifica si añadir nuevo_anterior → nuevo_posterior crearía un ciclo.
        Usa DFS: comprueba si nuevo_posterior ya es alcanzable desde nuevo_anterior.
        """
        ues = [ue.id for ue in
               UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id).all()]
        relaciones = RelacionUE.query.filter(
            RelacionUE.ue_posterior_id.in_(ues)
        ).all()

        # Grafo existente: anterior → posteriores
        grafo = defaultdict(set)
        for rel in relaciones:
            grafo[rel.ue_anterior_id].add(rel.ue_posterior_id)

        # DFS desde nuevo_posterior: ¿llegamos a nuevo_anterior?
        visitados = set()
        pila = [nuevo_posterior_id]
        while pila:
            nodo = pila.pop()
            if nodo == nuevo_anterior_id:
                return True
            if nodo not in visitados:
                visitados.add(nodo)
                pila.extend(grafo[nodo])
        return False
