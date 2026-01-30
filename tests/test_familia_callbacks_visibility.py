from controllers import familia_controller


def test_mostrar_boton_descargar_muestra_ambos():
    # Simular que hay contenido en resultados-familia
    resultados = ['dummy html content']
    style_completo, style_personalizado = familia_controller.mostrar_boton_descargar(resultados)

    assert isinstance(style_completo, dict)
    assert isinstance(style_personalizado, dict)
    assert style_completo.get('display') == 'block'
    assert style_personalizado.get('display') == 'block'


def test_mostrar_boton_descargar_oculta_ambos():
    resultados = []
    style_completo, style_personalizado = familia_controller.mostrar_boton_descargar(resultados)
    assert style_completo.get('display') == 'none'
    assert style_personalizado.get('display') == 'none'
