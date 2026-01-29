import math
import pandas as pd
import pytest

from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
from NodoEstructural import NodoEstructural
from HipotesisMaestro_Especial import hipotesis_maestro


class DummyCable:
    def __init__(self, nombre="DUMMY", peso=1.0):
        self.nombre = nombre
        self.peso_unitario_dan_m = peso

    def _calcular_peso_hielo(self, t_hielo):
        return 0.0


class DummyGeometry:
    def __init__(self, lk=3.0, hip_a5=True, alpha_quiebre=20.0):
        self.tipo_estructura = "Suspensión Recta"
        self.lk = lk
        self.alpha_quiebre = alpha_quiebre
        # minimal estados climáticos so SelectorEstados.buscar_hielo_max works
        self.estados_climaticos = {"6": {"espesor_hielo": 0.025}}
        self.cable_conductor = DummyCable("Cond", peso=1.0)
        self.cable_guardia1 = DummyCable("Hg1", peso=1.0)
        self.cable_guardia2 = None
        self.nodos = {}
        # Add two conductor nodes
        n1 = NodoEstructural('C1_L', (-1, 0, 10), 'conductor', cable_asociado=self.cable_conductor)
        n2 = NodoEstructural('C1_R', (1, 0, 10), 'conductor', cable_asociado=self.cable_conductor)
        self.nodos[n1.nombre] = n1
        self.nodos[n2.nombre] = n2
        self._nodes_dict = {k: (0,) for k in self.nodos.keys()}
        # hip param
        self.hipotesis_a5_dme_15pc_si_lk_mayor_2_5 = hip_a5

    def obtener_nodos_dict(self):
        return self._nodes_dict


def _expected_tiro_trans(tiro, alpha_quiebre, reduccion):
    ang_rad = math.radians(alpha_quiebre / 2)
    if reduccion > 0:
        factor_trans = 2.0 * math.sin(ang_rad) * (1 - reduccion / 2)
    else:
        factor_trans = 2.0 * math.sin(ang_rad)
    return factor_trans * tiro


def test_a5_aplica_15pc_when_lk_gt_2_5():
    geom = DummyGeometry(lk=3.0, hip_a5=True, alpha_quiebre=20.0)
    mech = EstructuraAEA_Mecanica(geom)

    df_cargas = pd.DataFrame(columns=['Código', 'Magnitud', 'Carga'])
    resultados_conductor = {'6': {'tiro_daN': 100.0}}
    resultados_guardia1 = {'6': {'tiro_daN': 10.0}}

    mech.asignar_cargas_hipotesis(df_cargas, resultados_conductor, resultados_guardia1,
                                  vano=100.0, hipotesis_maestro=hipotesis_maestro, t_hielo=0.025)

    # Find applied hypothesis name and values
    nodo = geom.nodos['C1_R']
    carga_tiro = nodo.obtener_carga('Tiro')
    assert carga_tiro is not None
    assert len(carga_tiro.hipotesis) > 0
    codigo_hip = carga_tiro.hipotesis[0]
    valores = carga_tiro.obtener_valores(codigo_hip)

    expected = _expected_tiro_trans(100.0, geom.alpha_quiebre, 0.15)
    assert pytest.approx(expected, rel=1e-3) == valores['fx']


def test_a5_no_aplica_when_lk_eq_2_5():
    geom = DummyGeometry(lk=2.5, hip_a5=True, alpha_quiebre=20.0)
    mech = EstructuraAEA_Mecanica(geom)

    df_cargas = pd.DataFrame(columns=['Código', 'Magnitud', 'Carga'])
    resultados_conductor = {'6': {'tiro_daN': 100.0}}
    resultados_guardia1 = {'6': {'tiro_daN': 10.0}}

    mech.asignar_cargas_hipotesis(df_cargas, resultados_conductor, resultados_guardia1,
                                  vano=100.0, hipotesis_maestro=hipotesis_maestro, t_hielo=0.025)

    nodo = geom.nodos['C1_R']
    carga_tiro = nodo.obtener_carga('Tiro')
    codigo_hip = carga_tiro.hipotesis[0]
    valores = carga_tiro.obtener_valores(codigo_hip)

    expected = _expected_tiro_trans(100.0, geom.alpha_quiebre, 0.20)
    assert pytest.approx(expected, rel=1e-3) == valores['fx']


def test_a5_param_false_uses_20pc():
    geom = DummyGeometry(lk=3.0, hip_a5=False, alpha_quiebre=20.0)
    mech = EstructuraAEA_Mecanica(geom)

    df_cargas = pd.DataFrame(columns=['Código', 'Magnitud', 'Carga'])
    resultados_conductor = {'6': {'tiro_daN': 100.0}}
    resultados_guardia1 = {'6': {'tiro_daN': 10.0}}

    mech.asignar_cargas_hipotesis(df_cargas, resultados_conductor, resultados_guardia1,
                                  vano=100.0, hipotesis_maestro=hipotesis_maestro, t_hielo=0.025)

    nodo = geom.nodos['C1_R']
    carga_tiro = nodo.obtener_carga('Tiro')
    codigo_hip = carga_tiro.hipotesis[0]
    valores = carga_tiro.obtener_valores(codigo_hip)

    expected = _expected_tiro_trans(100.0, geom.alpha_quiebre, 0.20)
    assert pytest.approx(expected, rel=1e-3) == valores['fx']
