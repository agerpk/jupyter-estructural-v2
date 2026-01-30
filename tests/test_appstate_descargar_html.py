from models.app_state import AppState


def test_set_get_descargar_html_secciones(tmp_path, monkeypatch):
    # Isolate state file to tmp dir
    import os
    from config import app_config
    # Monkeypatch FAMILIA_STATE_FILE to point inside tmp_path
    monkeypatch.setattr(app_config, 'FAMILIA_STATE_FILE', tmp_path / 'familia_state.json')

    state = AppState()

    # Initially empty
    s = state.get_descargar_html_secciones()
    assert isinstance(s, dict)
    assert len(s) == 0

    # Set mapping (global keys)
    mapping = {'cmc': True, 'dge.dimensiones': False}
    state.set_descargar_html_secciones(mapping)

    s2 = state.get_descargar_html_secciones()
    assert s2.get('cmc') is True
    assert s2.get('dge.dimensiones') is False

    # Update partial: add new key and ensure merge persists both
    mapping2 = {'dge.plscadd': True}
    state.set_descargar_html_secciones({**s2, **mapping2})
    s3 = state.get_descargar_html_secciones()
    assert s3.get('dge.plscadd') is True
    assert s3.get('cmc') is True
