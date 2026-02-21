"""
Tests unitarios v3.0 — Unidades Estratigráficas, Matriz de Harris y Muestras.
"""

import pytest
from datetime import date

from app.models.unidad_estratigrafica import UnidadEstratigrafica, RelacionUE
from app.models.muestra import Muestra, ResultadoAnalisis
from app.services.ue_service import UEService
from app.services.harris_service import HarrisService
from app.services.muestra_service import MuestraService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def usuario(db):
    from app.models.user import Usuario
    u = Usuario(nombre='Carlos Ruiz', email='carlos@test.com')
    u.set_password('pass')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def yacimiento(db, usuario):
    from app.models.yacimiento import Yacimiento
    y = Yacimiento(
        nombre='Yacimiento Harris',
        propietario_id=usuario.id,
        municipio='Toledo',
        pais='ES',
        latitud=39.8628,
        longitud=-4.0273,
        estado='activo',
    )
    db.session.add(y)
    db.session.commit()
    return y


@pytest.fixture
def tres_ues(db, yacimiento, usuario):
    """Crea 3 UEs: UE1 (más antigua), UE2, UE3 (más reciente)."""
    ue1 = UEService.crear(yacimiento_id=yacimiento.id, tipo='deposito',
                          descripcion='Nivel inferior', registrada_por_id=usuario.id)
    ue2 = UEService.crear(yacimiento_id=yacimiento.id, tipo='deposito',
                          descripcion='Nivel medio', registrada_por_id=usuario.id)
    ue3 = UEService.crear(yacimiento_id=yacimiento.id, tipo='interfaz',
                          descripcion='Interfaz superior', registrada_por_id=usuario.id)
    return ue1, ue2, ue3


# ── Tests UEService ───────────────────────────────────────────────────────────

class TestUEService:

    def test_crear_ue_asigna_numero(self, db, yacimiento, usuario):
        """Crear UE asigna automáticamente el siguiente número."""
        ue1 = UEService.crear(yacimiento_id=yacimiento.id, tipo='deposito',
                              registrada_por_id=usuario.id)
        ue2 = UEService.crear(yacimiento_id=yacimiento.id, tipo='corte',
                              registrada_por_id=usuario.id)
        assert ue1.numero_ue == 1
        assert ue2.numero_ue == 2

    def test_crear_ue_numero_manual(self, db, yacimiento, usuario):
        """Se puede especificar un número UE manualmente."""
        ue = UEService.crear(yacimiento_id=yacimiento.id, tipo='estructura',
                             numero_ue=100, registrada_por_id=usuario.id)
        assert ue.numero_ue == 100

    def test_crear_ue_numero_duplicado(self, db, yacimiento, usuario):
        """UE con número duplicado en mismo yacimiento lanza ValueError."""
        UEService.crear(yacimiento_id=yacimiento.id, tipo='deposito',
                        numero_ue=5, registrada_por_id=usuario.id)
        with pytest.raises(ValueError, match='número UE'):
            UEService.crear(yacimiento_id=yacimiento.id, tipo='corte',
                            numero_ue=5, registrada_por_id=usuario.id)

    def test_siguiente_numero(self, db, yacimiento, usuario):
        """siguiente_numero() retorna el próximo número disponible."""
        assert UEService.siguiente_numero(yacimiento.id) == 1
        UEService.crear(yacimiento_id=yacimiento.id, tipo='deposito', registrada_por_id=usuario.id)
        assert UEService.siguiente_numero(yacimiento.id) == 2

    def test_marcar_excavada(self, db, yacimiento, usuario):
        """marcar_excavada() actualiza el campo excavada y fechas."""
        ue = UEService.crear(yacimiento_id=yacimiento.id, tipo='deposito',
                             registrada_por_id=usuario.id)
        assert ue.excavada is False
        UEService.marcar_excavada(ue.id, fecha_inicio=date(2025, 4, 1))
        db.session.refresh(ue)
        assert ue.excavada is True

    def test_actualizar_ue(self, db, yacimiento, usuario):
        """Actualizar campos de una UE."""
        ue = UEService.crear(yacimiento_id=yacimiento.id, tipo='deposito',
                             registrada_por_id=usuario.id)
        UEService.actualizar(ue.id, color_munsell='10YR 5/4', compactacion='compacta')
        db.session.refresh(ue)
        assert ue.color_munsell == '10YR 5/4'
        assert ue.compactacion == 'compacta'

    def test_eliminar_ue(self, db, yacimiento, usuario):
        """Eliminar una UE."""
        ue = UEService.crear(yacimiento_id=yacimiento.id, tipo='deposito',
                             registrada_por_id=usuario.id)
        ue_id = ue.id
        UEService.eliminar(ue_id)
        assert UnidadEstratigrafica.query.get(ue_id) is None


# ── Tests HarrisService ───────────────────────────────────────────────────────

class TestHarrisService:

    def test_añadir_relacion_basica(self, db, tres_ues):
        """Añadir relación Harris entre dos UEs."""
        ue1, ue2, ue3 = tres_ues
        # UE2 (posterior) cubre UE1 (anterior)
        rel = HarrisService.añadir_relacion(
            ue_posterior_id=ue2.id,
            ue_anterior_id=ue1.id,
            tipo_relacion='cubre',
        )
        assert rel.id is not None
        assert rel.ue_posterior_id == ue2.id
        assert rel.ue_anterior_id == ue1.id
        assert rel.tipo_relacion == 'cubre'

    def test_no_autorelacion(self, db, tres_ues):
        """Una UE no puede relacionarse consigo misma."""
        ue1, _, _ = tres_ues
        with pytest.raises(ValueError, match='misma UE'):
            HarrisService.añadir_relacion(ue1.id, ue1.id, 'cubre')

    def test_no_duplicado(self, db, tres_ues):
        """No se puede añadir la misma relación dos veces."""
        ue1, ue2, _ = tres_ues
        HarrisService.añadir_relacion(ue2.id, ue1.id, 'cubre')
        with pytest.raises(ValueError, match='ya existe'):
            HarrisService.añadir_relacion(ue2.id, ue1.id, 'cubre')

    def test_deteccion_ciclo(self, db, tres_ues):
        """Detecta y rechaza relaciones que crearían ciclos."""
        ue1, ue2, ue3 = tres_ues
        # Cadena: UE3 > UE2 > UE1
        HarrisService.añadir_relacion(ue3.id, ue2.id, 'cubre')
        HarrisService.añadir_relacion(ue2.id, ue1.id, 'cubre')
        # UE1 > UE3 crearía ciclo UE3 > UE2 > UE1 > UE3
        with pytest.raises(ValueError, match='ciclo'):
            HarrisService.añadir_relacion(ue1.id, ue3.id, 'cubre')

    def test_ordenacion_topologica(self, db, tres_ues):
        """Ordenación topológica retorna UEs de más antigua a más reciente."""
        ue1, ue2, ue3 = tres_ues
        yacimiento_id = ue1.yacimiento_id
        # UE3 > UE2 > UE1 (UE1 es la más antigua)
        HarrisService.añadir_relacion(ue3.id, ue2.id, 'cubre')
        HarrisService.añadir_relacion(ue2.id, ue1.id, 'cubre')

        orden = HarrisService.ordenacion_topologica(yacimiento_id)
        ids = [u.id for u in orden]
        # UE1 debe aparecer antes que UE2, que antes que UE3
        assert ids.index(ue1.id) < ids.index(ue2.id)
        assert ids.index(ue2.id) < ids.index(ue3.id)

    def test_exportar_json_formato(self, db, tres_ues):
        """exportar_json() retorna estructura con nodes y edges."""
        ue1, ue2, _ = tres_ues
        HarrisService.añadir_relacion(ue2.id, ue1.id, 'cubre')
        data = HarrisService.exportar_json(ue1.yacimiento_id)
        assert 'nodes' in data
        assert 'edges' in data
        assert len(data['nodes']) >= 2
        assert len(data['edges']) >= 1
        # Verificar estructura de nodo
        nodo = data['nodes'][0]
        assert 'id' in nodo
        assert 'label' in nodo
        assert 'tipo' in nodo

    def test_exportar_graphml(self, db, tres_ues):
        """exportar_graphml() retorna XML válido con graphml raíz."""
        ue1, ue2, _ = tres_ues
        HarrisService.añadir_relacion(ue2.id, ue1.id, 'cubre')
        xml_str = HarrisService.exportar_graphml(ue1.yacimiento_id)
        assert '<?xml' in xml_str or '<graphml' in xml_str
        assert f'UE-{ue1.numero_ue}' in xml_str

    def test_validar_coherencia_sin_errores(self, db, tres_ues):
        """validar_coherencia() no reporta errores en grafo sin ciclos."""
        ue1, ue2, ue3 = tres_ues
        HarrisService.añadir_relacion(ue3.id, ue2.id, 'cubre')
        HarrisService.añadir_relacion(ue2.id, ue1.id, 'cubre')
        resultado = HarrisService.validar_coherencia(ue1.yacimiento_id)
        assert resultado['tiene_ciclos'] is False
        assert len(resultado['errores']) == 0

    def test_eliminar_relacion(self, db, tres_ues):
        """Eliminar una relación Harris."""
        ue1, ue2, _ = tres_ues
        rel = HarrisService.añadir_relacion(ue2.id, ue1.id, 'cubre')
        rel_id = rel.id
        HarrisService.eliminar_relacion(rel_id)
        assert RelacionUE.query.get(rel_id) is None

    def test_ordenacion_grafo_vacio(self, db, yacimiento, usuario):
        """Topological sort con cero UEs devuelve lista vacía."""
        orden = HarrisService.ordenacion_topologica(yacimiento.id)
        assert orden == []

    def test_mismo_yacimiento_requerido(self, db, usuario):
        """UEs de diferente yacimiento no pueden relacionarse."""
        from app.models.yacimiento import Yacimiento
        y2 = Yacimiento(nombre='Otro Yac', propietario_id=usuario.id,
                        municipio='Madrid', pais='ES', latitud=40.0, longitud=-3.7, estado='activo')
        db.session.add(y2)
        db.session.commit()

        ue_a = UEService.crear(yacimiento_id=1, tipo='deposito', registrada_por_id=usuario.id)
        ue_b = UEService.crear(yacimiento_id=y2.id, tipo='deposito', registrada_por_id=usuario.id)
        with pytest.raises(ValueError, match='mismo yacimiento'):
            HarrisService.añadir_relacion(ue_a.id, ue_b.id, 'cubre')


# ── Tests MuestraService ──────────────────────────────────────────────────────

class TestMuestraService:

    def test_crear_muestra_genera_codigo(self, db, yacimiento, usuario):
        """Crear muestra genera código único M-XXXXXXXX."""
        m = MuestraService.crear(
            yacimiento_id=yacimiento.id,
            tipo='c14',
            descripcion='Carbón de hogar',
            recogida_por_id=usuario.id,
        )
        assert m.id is not None
        assert m.codigo.startswith('M-')
        assert len(m.codigo) == 10  # 'M-' + 8 chars
        assert m.estado == 'recogida'

    def test_codigo_unico(self, db, yacimiento, usuario):
        """Dos muestras tienen códigos distintos."""
        m1 = MuestraService.crear(yacimiento_id=yacimiento.id, tipo='c14',
                                  recogida_por_id=usuario.id)
        m2 = MuestraService.crear(yacimiento_id=yacimiento.id, tipo='palinologia',
                                  recogida_por_id=usuario.id)
        assert m1.codigo != m2.codigo

    def test_enviar_a_laboratorio(self, db, yacimiento, usuario):
        """Enviar a laboratorio cambia estado y registra datos."""
        m = MuestraService.crear(yacimiento_id=yacimiento.id, tipo='c14',
                                 recogida_por_id=usuario.id)
        MuestraService.enviar_a_laboratorio(m.id, laboratorio='Beta Analytic',
                                            numero_laboratorio='BETA-12345')
        db.session.refresh(m)
        assert m.estado == 'en_laboratorio'
        assert m.laboratorio == 'Beta Analytic'
        assert m.numero_laboratorio == 'BETA-12345'
        assert m.fecha_envio is not None

    def test_registrar_resultado(self, db, yacimiento, usuario):
        """Registrar resultado actualiza estado y crea ResultadoAnalisis."""
        m = MuestraService.crear(yacimiento_id=yacimiento.id, tipo='c14',
                                 recogida_por_id=usuario.id)
        MuestraService.enviar_a_laboratorio(m.id, laboratorio='Beta Analytic')

        resultado = MuestraService.registrar_resultado(
            m.id,
            tipo_analisis='c14',
            valor_principal='1250 BP',
            margen_error='±30',
            descripcion='Muestra de carbón con datación medieval',
            interpretacion='Correspond al siglo XIII',
            revisado_por_id=usuario.id,
        )
        db.session.refresh(m)
        assert m.estado == 'resultado_disponible'
        assert resultado.valor_principal == '1250 BP'
        assert resultado.margen_error == '±30'
        assert resultado.muestra_id == m.id

    def test_exportar_csv(self, db, yacimiento, usuario):
        """exportar_inventario_csv() retorna CSV con cabecera y datos."""
        MuestraService.crear(yacimiento_id=yacimiento.id, tipo='c14', recogida_por_id=usuario.id)
        MuestraService.crear(yacimiento_id=yacimiento.id, tipo='palinologia', recogida_por_id=usuario.id)
        csv_content = MuestraService.exportar_inventario_csv(yacimiento.id)
        assert 'codigo' in csv_content.lower() or 'Código' in csv_content
        assert 'c14' in csv_content
        assert 'palinologia' in csv_content

    def test_actualizar_muestra(self, db, yacimiento, usuario):
        """Actualizar descripción y peso de una muestra."""
        m = MuestraService.crear(yacimiento_id=yacimiento.id, tipo='sedimento',
                                 recogida_por_id=usuario.id)
        MuestraService.actualizar(m.id, descripcion='Sedimento arenoso', peso_gramos=150.5)
        db.session.refresh(m)
        assert m.descripcion == 'Sedimento arenoso'
        assert m.peso_gramos == 150.5
