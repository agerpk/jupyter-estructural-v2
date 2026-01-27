import json
from types import SimpleNamespace
from EstructuraAEA_Geometria import EstructuraAEA_Geometria


class DummyCable:
    def __init__(self):
        # valores razonables para las fórmulas
        self.peso_unitario_dan_m = 1.65
        # clave 'V_90' cumple el criterio en calcular_theta_max
        self.viento_cache = {'V_90': {'fuerza_total_daN': 1045.27}}
        # diámetro efectivo para cálculo de viento en cargaViento
        self.diametro_m = 0.02

    def cargaViento(self, V, phi_rel_deg, exp, clase, Zc, Cf, **kwargs):
        # Aceptar kwargs (p. ej. L_vano, d_eff) que pasan los métodos de Estructura
        fuerza_total = 261.32
        L = kwargs.get('L_vano', 350)
        return {'fuerza_daN_per_m': fuerza_total / L, 'fuerza_total_daN': fuerza_total}


def _cargar_parametros_base():
    with open('data/PSJ_prueba.familia.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['estructuras']['Estr.1']


def test_defasaje_segunda_vertical():
    parametros = _cargar_parametros_base().copy()
    parametros['DISPOSICION'] = 'vertical'
    parametros['TERNA'] = 'Doble'
    parametros['defasaje_mensula_hielo'] = True
    parametros['lmen_extra_hielo'] = 1.5
    parametros['mensula_defasar'] = 'segunda'

    cable = DummyCable()
    estructura = EstructuraAEA_Geometria(
        parametros=parametros,
        tipo_estructura=parametros.get('TIPO_ESTRUCTURA'),
        tension_nominal=parametros.get('TENSION'),
        zona_estructura=parametros.get('Zona_estructura'),
        disposicion=parametros.get('DISPOSICION'),
        terna=parametros.get('TERNA'),
        cant_hg=parametros.get('CANT_HG'),
        alpha_quiebre=parametros.get('alpha'),
        altura_minima_cable=parametros.get('ALTURA_MINIMA_CABLE'),
        long_mensula_min_conductor=parametros.get('LONGITUD_MENSULA_MINIMA_CONDUCTOR'),
        long_mensula_min_guardia=parametros.get('LONGITUD_MENSULA_MINIMA_GUARDIA'),
        hadd=parametros.get('HADD'),
        hadd_entre_amarres=parametros.get('HADD_ENTRE_AMARRES'),
        lk=parametros.get('Lk'),
        ancho_cruceta=parametros.get('ANCHO_CRUCETA'),
        cable_conductor=cable,
        cable_guardia=cable,
        peso_estructura=parametros.get('PESTRUCTURA'),
        peso_cadena=parametros.get('PCADENA')
    )

    estructura.dimensionar_unifilar(parametros.get('L_vano'), 16.01, 14.49)

    lmen1_sin = estructura.dimensiones.get('Lmen1_sin_defasaje')
    lmen2 = estructura.dimensiones.get('Lmen2')

    assert lmen1_sin is not None
    assert abs(lmen2 - (lmen1_sin + 1.5)) < 1e-6


def test_defasaje_segunda_triangular_simple():
    parametros = _cargar_parametros_base().copy()
    parametros['DISPOSICION'] = 'triangular'
    parametros['TERNA'] = 'Simple'
    parametros['defasaje_mensula_hielo'] = True
    parametros['lmen_extra_hielo'] = 1.5
    parametros['mensula_defasar'] = 'segunda'

    cable = DummyCable()
    estructura = EstructuraAEA_Geometria(
        parametros=parametros,
        tipo_estructura=parametros.get('TIPO_ESTRUCTURA'),
        tension_nominal=parametros.get('TENSION'),
        zona_estructura=parametros.get('Zona_estructura'),
        disposicion=parametros.get('DISPOSICION'),
        terna=parametros.get('TERNA'),
        cant_hg=parametros.get('CANT_HG'),
        alpha_quiebre=parametros.get('alpha'),
        altura_minima_cable=parametros.get('ALTURA_MINIMA_CABLE'),
        long_mensula_min_conductor=parametros.get('LONGITUD_MENSULA_MINIMA_CONDUCTOR'),
        long_mensula_min_guardia=parametros.get('LONGITUD_MENSULA_MINIMA_GUARDIA'),
        hadd=parametros.get('HADD'),
        hadd_entre_amarres=parametros.get('HADD_ENTRE_AMARRES'),
        lk=parametros.get('Lk'),
        ancho_cruceta=parametros.get('ANCHO_CRUCETA'),
        cable_conductor=cable,
        cable_guardia=cable,
        peso_estructura=parametros.get('PESTRUCTURA'),
        peso_cadena=parametros.get('PCADENA')
    )

    estructura.dimensionar_unifilar(parametros.get('L_vano'), 16.01, 14.49)

    lmen1_sin = estructura.dimensiones.get('Lmen1_sin_defasaje')
    lmen2 = estructura.dimensiones.get('Lmen2')

    assert lmen1_sin is not None
    assert abs(lmen2 - (lmen1_sin + 1.5)) < 1e-6
