import pytest
from utils.descargar_html_familia_personalizado import listar_secciones_disponibles, construir_html_personalizado


def _fake_resultados_familia():
    return {
        "resultados_estructuras": {
            "Estr.1": {
                "titulo": "Puma 12m",
                "cantidad": 2,
                "resultados": {
                    "cmc": {"df_conductor_html": None, "hash_parametros": "abc123", "console_output": "OK"},
                    "dge": {"dimensiones": {"L": 10, "H": 12}, "nodes_key": {"N1": [0,0,0]}, "hash_parametros": "h123", "servidumbre": {"A": 5}, "memoria_calculo": "memoria"},
                    "dme": None,
                    "arboles": None,
                    "sph": None
                }
            }
        },
        "costeo_global": {"costo_global": 1000}
    }


def test_listar_secciones_disponibles_basico():
    datos = _fake_resultados_familia()
    secciones = listar_secciones_disponibles("FamiliaPrueba", datos)
    keys = [s.key for s in secciones]

    assert 'cmc' in keys
    assert 'dge' in keys
    assert 'dge.dimensiones' in keys
    assert 'familia:costeo' in keys


def test_construir_html_personalizado_incluye_seleccionadas():
    datos = _fake_resultados_familia()
    # seleccionar solo resumen y dge.dimensiones (clave global)
    selected = ["familia:resumen", "dge.dimensiones"]
    html = construir_html_personalizado("FamiliaPrueba", datos, selected)
    assert "Dimensiones de Estructura" in html
    assert "CMC" not in html or "CÁLCULO MECÁNICO" not in html  # CMC no seleccionado
    # selecting costeo should include costeo_global
    html2 = construir_html_personalizado("FamiliaPrueba", datos, ["familia:costeo"])
    assert "Costeo Global" in html2
