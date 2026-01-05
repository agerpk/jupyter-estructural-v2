"""Fix para generar HTML de familia con índice y secciones completas"""

def generar_indice_familia(nombre_familia, resultados_familia):
    """Genera índice con hyperlinks"""
    html = ['<div class="indice"><h3>Índice</h3><ul>']
    html.append('<li><a href="#resumen">Resumen de Familia</a></li>')
    
    estructuras = resultados_familia.get("resultados_estructuras", {})
    for nombre_estr, datos_estr in estructuras.items():
        titulo = datos_estr.get("titulo", nombre_estr)
        titulo_id = titulo.replace(" ", "_").replace("/", "_")
        html.append(f'<li><a href="#{titulo_id}">{titulo}</a></li>')
    
    html.append('<li><a href="#costeo-global">Costeo Global</a></li>')
    html.append('</ul></div>')
    return '\n'.join(html)

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
