import io


def test_vista_dme_no_tiene_modificar_hipotesis():
    from components import vista_diseno_mecanico
    source = open(vista_diseno_mecanico.__file__, 'r', encoding='utf-8').read()
    assert 'Modificar Hipótesis' not in source
    assert 'btn-abrir-editor-hipotesis' not in source
