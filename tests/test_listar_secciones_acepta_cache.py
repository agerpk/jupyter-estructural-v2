from utils.descargar_html_familia_personalizado import listar_secciones_disponibles


def test_listar_secciones_acepta_formato_cache():
    # Formato simulado como el que devuelve CalculoCache.cargar_calculo_familia
    fake_cache = {
        "hash_parametros": "h123",
        "fecha_calculo": "2026-01-30T00:00:00",
        "archivo_origen": "FamiliaPrueba.calculoFAMILIA.json",
        "resultados": {
            "exito": True,
            "resultados_estructuras": {
                "Estr.1": {
                    "titulo": "Puma 12m",
                    "cantidad": 1,
                    "resultados": {
                        "cmc": {"hash_parametros": "abc"},
                        "dge": {"dimensiones": {"L": 10}}
                    }
                }
            },
            "costeo_global": {"costo_global": 1000}
        }
    }

    secciones = listar_secciones_disponibles("FamiliaPrueba", fake_cache)
    keys = [s.key for s in secciones]

    assert "familia:resumen" in keys
    assert "cmc" in keys
    assert "dge" in keys
    assert "familia:costeo" in keys
