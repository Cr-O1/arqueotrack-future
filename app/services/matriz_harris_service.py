"""
Servicio de Matriz de Harris - ArqueoTrack v3.0

Implementa el algoritmo estratigráfico para visualización y validación
de relaciones temporales entre Unidades Estratigráficas (UEs).

La Matriz de Harris es el estándar internacional para representar
las relaciones estratigráficas en excavaciones arqueológicas.
"""

import structlog
from collections import defaultdict, deque
from typing import List, Tuple, Optional

from app import db, cache
from app.models.unidad_estratigrafica import UnidadEstratigrafica, RelacionUE

log = structlog.get_logger(__name__)


class MatrizHarrisService:
    """
    Gestiona la Matriz de Harris de un yacimiento.

    La matriz se representa como un grafo dirigido donde:
    - Los nodos son UEs
    - Las aristas van de UE_POSTERIOR → UE_ANTERIOR
      (la posterior es más reciente, la anterior es más antigua)
    """

    @staticmethod
    def añadir_relacion(
        ue_posterior_id: int,
        ue_anterior_id: int,
        tipo_relacion: str = 'cubre',
        notas: str = None,
    ) -> RelacionUE:
        """
        Añade una relación estratigráfica entre dos UEs.

        Valida automáticamente que no se genere un ciclo (inconsistencia estratigráfica).

        Args:
            ue_posterior_id: UE más reciente (encima en la estratigrafía).
            ue_anterior_id: UE más antigua (debajo).
            tipo_relacion: 'cubre' | 'corta' | 'rellena' | 'igual_a' | 'se_apoya_en'

        Raises:
            ValueError: Si las UEs no pertenecen al mismo yacimiento.
            ValueError: Si se detectaría un ciclo (inconsistencia).
            ValueError: Si la relación ya existe.
        """
        ue_post = UnidadEstratigrafica.query.get_or_404(ue_posterior_id)
        ue_ant = UnidadEstratigrafica.query.get_or_404(ue_anterior_id)

        if ue_post.yacimiento_id != ue_ant.yacimiento_id:
            raise ValueError("Las UEs deben pertenecer al mismo yacimiento.")

        if ue_posterior_id == ue_anterior_id:
            raise ValueError("Una UE no puede relacionarse consigo misma.")

        existente = RelacionUE.query.filter_by(
            ue_posterior_id=ue_posterior_id, ue_anterior_id=ue_anterior_id
        ).first()
        if existente:
            raise ValueError("Esta relación estratigráfica ya existe.")

        # Validar que no genera ciclo
        if MatrizHarrisService._genera_ciclo(ue_post.yacimiento_id, ue_posterior_id, ue_anterior_id):
            raise ValueError(
                f"La relación UE {ue_post.numero_ue} → UE {ue_ant.numero_ue} "
                f"crearía una inconsistencia estratigráfica (ciclo)."
            )

        relacion = RelacionUE(
            ue_posterior_id=ue_posterior_id,
            ue_anterior_id=ue_anterior_id,
            tipo_relacion=tipo_relacion,
            notas=notas,
        )
        db.session.add(relacion)
        db.session.commit()

        cache.delete(f'matriz_harris_{ue_post.yacimiento_id}')
        log.info("Relación UE añadida",
                 ue_post=ue_post.numero_ue, ue_ant=ue_ant.numero_ue, tipo=tipo_relacion)
        return relacion

    @staticmethod
    def eliminar_relacion(relacion_id: int) -> None:
        """Elimina una relación estratigráfica."""
        relacion = RelacionUE.query.get_or_404(relacion_id)
        yacimiento_id = relacion.ue_posterior.yacimiento_id
        db.session.delete(relacion)
        db.session.commit()
        cache.delete(f'matriz_harris_{yacimiento_id}')

    @staticmethod
    @cache.memoize(timeout=300)
    def get_matriz(yacimiento_id: int, campana_id: int = None) -> dict:
        """
        Obtiene la representación completa de la Matriz de Harris.

        Retorna:
            {
              'nodos': [{'id': int, 'numero_ue': int, 'tipo': str, ...}],
              'aristas': [{'source': int, 'target': int, 'tipo': str}],
              'secuencia': [int],   # IDs de UEs en orden cronológico (más antiguo primero)
              'valida': bool,
              'errores': [str],
            }
        """
        query = UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id)
        if campana_id:
            query = query.filter_by(campana_id=campana_id)
        ues = query.order_by(UnidadEstratigrafica.numero_ue).all()

        ue_ids = {ue.id for ue in ues}

        # Obtener relaciones entre UEs del yacimiento (o campaña)
        relaciones = (
            RelacionUE.query
            .filter(
                RelacionUE.ue_posterior_id.in_(ue_ids),
                RelacionUE.ue_anterior_id.in_(ue_ids),
            )
            .all()
        )

        nodos = [ue.to_dict(include_relations=True) for ue in ues]
        aristas = [
            {
                'id': r.id,
                'source': r.ue_posterior_id,
                'target': r.ue_anterior_id,
                'tipo': r.tipo_relacion,
                'confirmada': r.confirmada,
            }
            for r in relaciones
        ]

        # Ordenación topológica (secuencia cronológica)
        secuencia, errores = MatrizHarrisService._ordenacion_topologica(ue_ids, relaciones)

        return {
            'nodos': nodos,
            'aristas': aristas,
            'secuencia': secuencia,
            'valida': len(errores) == 0,
            'errores': errores,
            'total_ues': len(ues),
            'total_relaciones': len(relaciones),
        }

    @staticmethod
    def validar(yacimiento_id: int) -> Tuple[bool, List[str]]:
        """
        Valida la coherencia estratigráfica del yacimiento.

        Returns:
            (es_valida, lista_de_errores)
        """
        matriz = MatrizHarrisService.get_matriz(yacimiento_id)
        return matriz['valida'], matriz['errores']

    @staticmethod
    def exportar_graphml(yacimiento_id: int) -> str:
        """
        Exporta la Matriz de Harris en formato GraphML
        para importar en Gephi, yEd u otros programas.
        """
        matriz = MatrizHarrisService.get_matriz(yacimiento_id)

        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<graphml xmlns="http://graphml.graphdrawing.org/graphml">')
        lines.append('  <graph id="Harris" edgedefault="directed">')

        for nodo in matriz['nodos']:
            lines.append(f'    <node id="UE{nodo["numero_ue"]}">')
            lines.append(f'      <data key="tipo">{nodo["tipo"]}</data>')
            if nodo.get("descripcion"):
                desc = nodo["descripcion"].replace('<', '&lt;').replace('>', '&gt;')
                lines.append(f'      <data key="descripcion">{desc}</data>')
            lines.append('    </node>')

        for i, arista in enumerate(matriz['aristas']):
            src_ue = next((n["numero_ue"] for n in matriz["nodos"] if n["id"] == arista["source"]), arista["source"])
            tgt_ue = next((n["numero_ue"] for n in matriz["nodos"] if n["id"] == arista["target"]), arista["target"])
            lines.append(f'    <edge id="e{i}" source="UE{src_ue}" target="UE{tgt_ue}">')
            lines.append(f'      <data key="tipo">{arista["tipo"]}</data>')
            lines.append('    </edge>')

        lines.append('  </graph>')
        lines.append('</graphml>')
        return '\n'.join(lines)

    @staticmethod
    def exportar_dot(yacimiento_id: int) -> str:
        """
        Exporta la Matriz de Harris en formato DOT (Graphviz).
        Permite generar imágenes con: dot -Tpng harris.dot -o harris.png
        """
        matriz = MatrizHarrisService.get_matriz(yacimiento_id)
        ues_por_id = {n['id']: n for n in matriz['nodos']}

        lines = ['digraph Harris {']
        lines.append('  rankdir=TB;')
        lines.append('  node [shape=box, style=filled, fillcolor=lightyellow];')

        for nodo in matriz['nodos']:
            label = f"UE {nodo['numero_ue']}"
            if nodo.get('tipo'):
                label += f"\\n({nodo['tipo']})"
            lines.append(f'  UE{nodo["numero_ue"]} [label="{label}"];')

        for arista in matriz['aristas']:
            src_num = ues_por_id.get(arista['source'], {}).get('numero_ue', arista['source'])
            tgt_num = ues_por_id.get(arista['target'], {}).get('numero_ue', arista['target'])
            lines.append(f'  UE{src_num} -> UE{tgt_num} [label="{arista["tipo"]}"];')

        lines.append('}')
        return '\n'.join(lines)

    # ── Algoritmos internos ───────────────────────────────────────────────────

    @staticmethod
    def _ordenacion_topologica(ue_ids: set, relaciones: list) -> Tuple[list, list]:
        """
        Algoritmo de Kahn para ordenación topológica del grafo estratigráfico.

        En la Matriz de Harris, la ordenación topológica = secuencia cronológica
        (el primer elemento es el más antiguo, el último el más reciente).

        Returns:
            (secuencia_ids, errores)
            Si hay ciclos, la secuencia está incompleta y errores no está vacío.
        """
        if not ue_ids:
            return [], []

        # Construir grafo de adyacencia: posterior → anterior
        # En Kahn necesitamos: in_degree de cada nodo
        in_degree = {uid: 0 for uid in ue_ids}
        adj = defaultdict(set)  # ue_posterior → {ue_anteriores}

        for rel in relaciones:
            if rel.ue_posterior_id in ue_ids and rel.ue_anterior_id in ue_ids:
                # posterior cubre/corta a anterior → anterior viene "antes"
                # Para secuencia cronológica: procesamos del más antiguo al más reciente
                # Invertimos: arista de anterior → posterior (anterior "precede a")
                adj[rel.ue_anterior_id].add(rel.ue_posterior_id)
                in_degree[rel.ue_posterior_id] += 1

        # Cola de nodos sin predecesores (los más antiguos)
        cola = deque(uid for uid in ue_ids if in_degree[uid] == 0)
        secuencia = []

        while cola:
            nodo = cola.popleft()
            secuencia.append(nodo)
            for vecino in sorted(adj[nodo]):  # sorted para determinismo
                in_degree[vecino] -= 1
                if in_degree[vecino] == 0:
                    cola.append(vecino)

        errores = []
        if len(secuencia) < len(ue_ids):
            ciclos = [uid for uid in ue_ids if uid not in secuencia]
            errores.append(
                f"Ciclo estratigráfico detectado en {len(ciclos)} UE(s): "
                f"IDs {ciclos[:5]}{'...' if len(ciclos) > 5 else ''}"
            )

        return secuencia, errores

    @staticmethod
    def _genera_ciclo(yacimiento_id: int, nuevo_posterior_id: int, nuevo_anterior_id: int) -> bool:
        """
        Verifica si añadir una relación posterior→anterior generaría un ciclo.
        Usa DFS desde nuevo_anterior_id. Si alcanza nuevo_posterior_id, hay ciclo.
        """
        # Obtener relaciones existentes
        ues = UnidadEstratigrafica.query.filter_by(yacimiento_id=yacimiento_id).all()
        ue_ids = {ue.id for ue in ues}

        relaciones = RelacionUE.query.filter(
            RelacionUE.ue_posterior_id.in_(ue_ids),
            RelacionUE.ue_anterior_id.in_(ue_ids),
        ).all()

        # Construir grafo posterior → anterior
        grafo = defaultdict(set)
        for r in relaciones:
            grafo[r.ue_posterior_id].add(r.ue_anterior_id)
        # Añadir la nueva relación hipotética
        grafo[nuevo_posterior_id].add(nuevo_anterior_id)

        # DFS desde nuevo_anterior_id buscando llegar a nuevo_posterior_id
        visitados = set()
        pila = [nuevo_anterior_id]
        while pila:
            actual = pila.pop()
            if actual == nuevo_posterior_id:
                return True
            if actual in visitados:
                continue
            visitados.add(actual)
            pila.extend(grafo[actual])

        return False
