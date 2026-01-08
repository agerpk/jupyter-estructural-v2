import os
from config.app_config import DATA_DIR
from utils.borrar_cache import borrar_cache


def test_borrar_cache_preserva_hipotesis_folder(tmp_path, monkeypatch):
    # Arrange: crear carpeta data/hipotesis si no existe y un archivo de prueba
    hip_dir = DATA_DIR / "hipotesis"
    hip_dir.mkdir(parents=True, exist_ok=True)
    test_file = hip_dir / "test_project.hipotesis.json"
    test_content = {"dummy": True}
    test_file.write_text('{"dummy": true}', encoding='utf-8')

    # Act
    archivos_borrados, errores = borrar_cache()

    # Assert: la carpeta y el archivo siguen existiendo
    assert hip_dir.exists() and hip_dir.is_dir()
    assert test_file.exists(), "El archivo de hipótesis fue borrado pero no debería"
    # errores list should be empty or not contain hipotesis deletion
    assert all("hipotesis" not in e for e in errores)
