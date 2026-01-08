from controllers.hipotesis_controller import listar_hipotesis, establecer_activa


def test_listar_hipotesis_returns_list():
    lst = listar_hipotesis()
    assert isinstance(lst, list)


def test_establecer_activa_creates_file():
    nombre = 'prueba_ctrl'
    path = establecer_activa(nombre)
    assert path.exists()
    # cleanup
    try:
        path.unlink()
    except Exception:
        pass