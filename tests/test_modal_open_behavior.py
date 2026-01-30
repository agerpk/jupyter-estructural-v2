from models.app_state import AppState
from utils.descargar_html_familia_personalizado import listar_secciones_disponibles


def test_modal_open_default_true(monkeypatch, tmp_path):
    # Monkeypatch familia state file location
    from config import app_config
    monkeypatch.setattr(app_config, 'FAMILIA_STATE_FILE', tmp_path / 'familia_state.json')

    state = AppState()
    # ensure empty
    state.set_descargar_html_secciones({})

    # Fake resultados_familia
    fake = {
        'resultados_estructuras': {
            'Estr.1': {'titulo': 'P1', 'resultados': {'cmc': {}, 'dge': {'dimensiones': {}}}}
        },
        'costeo_global': {}
    }

    secciones = listar_secciones_disponibles('F', fake)
    option_keys = [s.key for s in secciones]

    # Emulate opening modal logic: new keys -> True and persist
    persisted = state.get_descargar_html_secciones() or {}
    updated = False
    for k in option_keys:
        if k not in persisted:
            persisted[k] = True
            updated = True
    if updated:
        state.set_descargar_html_secciones(persisted)

    s2 = state.get_descargar_html_secciones()
    for k in option_keys:
        assert s2.get(k) is True
