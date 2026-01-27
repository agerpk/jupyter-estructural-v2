import json
from models.app_state import AppState
from config.app_config import DATA_DIR, ESTRUCTURA_STATE_FILE


def test_set_estructura_actual_without_title(tmp_path, monkeypatch):
    # Use a temporary folder for data dir to avoid modifying real files
    monkeypatch.setattr('config.app_config.DATA_DIR', tmp_path)
    monkeypatch.setattr('config.app_config.ESTRUCTURA_STATE_FILE', tmp_path / 'estructura_state.json')

    state = AppState()
    # Ensure no estructura activa initially
    state._estructura_actual_titulo = None

    # Call with estructura sin TITULO
    estructura = {'L_vano': 100}
    state.set_estructura_actual(estructura)

    # Should assign default title and set key in estructura
    assert state._estructura_actual_titulo == 'estructura'
    assert estructura['TITULO'] == 'estructura'

    # Persisted file should exist and contain the title
    with open(ESTRUCTURA_STATE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data.get('estructura_activa') == 'estructura'
