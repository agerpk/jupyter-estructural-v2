from utils.calculo_cache import CalculoCache
from pathlib import Path
from config.app_config import CACHE_DIR


def test_guardar_calculo_dme_incluye_hipotesis_activa(tmp_path):
    nombre = "test_struct"
    estructura_data = {"HIPOTESIS_ACTIVA": "proyectoX.hipotesis.json"}
    df_reacciones = None

    # Ejecutar
    hash_params = CalculoCache.guardar_calculo_dme(nombre, estructura_data, df_reacciones, None, None)

    archivo = CACHE_DIR / f"{nombre}.calculoDME.json"
    assert archivo.exists(), "Archivo de cache DME no generado"
    data = archivo.read_text(encoding='utf-8')
    assert 'proyectoX.hipotesis.json' in data
