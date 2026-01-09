from utils.hipotesis_manager import HipotesisManager
from config.app_config import DATA_DIR
from pathlib import Path


def test_eliminar_hipotesis_crea_y_elimina(tmp_path):
    hip_dir = Path(DATA_DIR) / 'hipotesis'
    hip_dir.mkdir(parents=True, exist_ok=True)
    nombre = 'temp_para_borrar'
    destino = hip_dir / f"{nombre}.hipotesis.json"
    destino.write_text('{"hash_estructura":"x","hipotesis_maestro":{}}', encoding='utf-8')
    assert destino.exists()
    res = HipotesisManager.eliminar_hipotesis(nombre)
    assert res is True
    assert not destino.exists()