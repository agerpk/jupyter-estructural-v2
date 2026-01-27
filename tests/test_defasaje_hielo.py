import json
from types import SimpleNamespace
from EstructuraAEA_Geometria import EstructuraAEA_Geometria


def test_constructor_lee_parametros_defasaje():
    with open('data/PSJ_prueba.familia.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    estructura_actual = data['estructuras']['Estr.1']

    # Crear dummy cables (no se ejecutará lógica que los use en este test)
    cable_dummy = SimpleNamespace()

    estructura = EstructuraAEA_Geometria(
        parametros=estructura_actual,
        tipo_estructura=estructura_actual.get('TIPO_ESTRUCTURA'),
        tension_nominal=estructura_actual.get('TENSION'),
        zona_estructura=estructura_actual.get('Zona_estructura'),
        disposicion=estructura_actual.get('DISPOSICION'),
        terna=estructura_actual.get('TERNA'),
        cant_hg=estructura_actual.get('CANT_HG'),
        alpha_quiebre=estructura_actual.get('alpha'),
        altura_minima_cable=estructura_actual.get('ALTURA_MINIMA_CABLE'),
        long_mensula_min_conductor=estructura_actual.get('LONGITUD_MENSULA_MINIMA_CONDUCTOR'),
        long_mensula_min_guardia=estructura_actual.get('LONGITUD_MENSULA_MINIMA_GUARDIA'),
        hadd=estructura_actual.get('HADD'),
        hadd_entre_amarres=estructura_actual.get('HADD_ENTRE_AMARRES'),
        lk=estructura_actual.get('Lk'),
        ancho_cruceta=estructura_actual.get('ANCHO_CRUCETA'),
        cable_conductor=cable_dummy,
        cable_guardia=cable_dummy,
        peso_estructura=estructura_actual.get('PESTRUCTURA'),
        peso_cadena=estructura_actual.get('PCADENA')
    )

    assert estructura.defasaje_mensula_hielo is True
    assert estructura.lmen_extra_hielo == 1.5
    assert estructura.mensula_defasar == 'segunda'
