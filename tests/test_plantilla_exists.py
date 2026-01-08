from config.app_config import DATA_DIR


def test_plantilla_hipotesis_exists():
    plantilla = DATA_DIR / "hipotesis" / "plantilla.hipotesis.json"
    assert plantilla.exists(), "plantilla.hipotesis.json no existe en data/hipotesis"
    content = plantilla.read_text(encoding='utf-8')
    assert 'Suspensión Recta' in content
