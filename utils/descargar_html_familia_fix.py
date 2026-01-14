"""Fix para generar HTML de familia - funciones auxiliares"""

def generar_seccion_costeo_estructura(calculo_costeo):
    """Genera HTML para costeo de estructura individual"""
    if not calculo_costeo:
        return '<p>No hay datos de costeo</p>'
    
    resultados = calculo_costeo.get('resultados', {})
    resumen = resultados.get('resumen_costos', {})
    
    if not resumen:
        return '<p>No hay resumen de costos</p>'
    
    html = ['<h5>Resumen de Costos</h5>', '<table class="table table-bordered">']
    for campo, valor in resumen.items():
        if isinstance(valor, (int, float)):
            html.append(f'<tr><td><strong>{campo}</strong></td><td>{valor:,.2f} UM</td></tr>')
        else:
            html.append(f'<tr><td><strong>{campo}</strong></td><td>{valor}</td></tr>')
    html.append('</table>')
    return '\n'.join(html)
