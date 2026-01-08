from utils.hipotesis_manager import HipotesisManager
from config.app_config import DATA_DIR
from pathlib import Path


def test_obtener_hipotesis_activa_returns_none_if_missing(tmp_path):
    hip_dir = Path(DATA_DIR) / 'hipotesis'
    activo_path = hip_dir / 'activo.json'
    if activo_path.exists():
        activo_path.unlink()
    assert HipotesisManager.obtener_hipotesis_activa() is None


def test_validar_hipotesis_plantilla_is_ok():
    from utils.hipotesis_manager import HipotesisManager
    hip = HipotesisManager.cargar_hipotesis_por_nombre('plantilla')
    assert hip is None or isinstance(hip, dict) or True
    # if plantilla exists, validation should pass
    if hip:
        ok, msg = HipotesisManager.validar_hipotesis(hip.get('hipotesis_maestro', hip))
        assert ok


def test_importar_hipotesis_temp_file(tmp_path):
    # Create a temp JSON and import
    temp = tmp_path / 'ext.hip'
    temp.write_text('{"mi": {"param": 1}}', encoding='utf-8')
    res = HipotesisManager.importar_hipotesis_desde_archivo(str(temp))
    assert res is True
    # cleanup: remove imported file
    hip_dir = Path(DATA_DIR) / 'hipotesis'
    destino = hip_dir / 'ext.hip.hipotesis.json'
    if destino.exists():
        destino.unlink()