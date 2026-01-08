import json
from utils.hipotesis_manager import HipotesisManager
from config.app_config import DATA_DIR
from pathlib import Path


def test_listar_hipotesis_includes_plantilla():
    hip_list = HipotesisManager.listar_hipotesis()
    assert isinstance(hip_list, list)
    # plantilla.hipotesis.json was created earlier in the flow
    assert any('plantilla.hipotesis.json' in name for name in hip_list)


def test_establecer_hipotesis_activa_writes_activo_file(tmp_path):
    # Use a temporary name to avoid clashing with real active file
    nombre = 'prueba_temporal'
    # Ensure directory exists
    hip_dir = Path(DATA_DIR) / 'hipotesis'
    hip_dir.mkdir(parents=True, exist_ok=True)

    activo_path = HipotesisManager.establecer_hipotesis_activa(nombre)
    assert activo_path.exists()
    datos = json.loads(activo_path.read_text(encoding='utf-8'))
    assert datos.get('hipotesis_activa') == f"{nombre}.hipotesis.json"

    # cleanup
    try:
        activo_path.unlink()
    except Exception:
        pass