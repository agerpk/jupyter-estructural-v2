from datetime import datetime
from utils.descargar_html_familia_fix import generar_seccion_costeo_estructura

def generar_indice_familia(nombre_familia, resultados_familia):
    """Genera índice con hyperlinks y subentradas por sección"""
    html = ['<div class="indice"><h3>Índice</h3><ul>']
    html.append('<li><a href="#resumen">Resumen de Familia</a></li>')
    
    estructuras = resultados_familia.get("resultados_estructuras", {})
    for nombre_estr, datos_estr in estructuras.items():
        titulo = datos_estr.get("titulo", nombre_estr)
        titulo_id = titulo.replace(" ", "_").replace("/", "_")
        html.append(f'<li><a href="#{titulo_id}">{titulo}</a>')
        
        # Subentradas por sección
        if "error" not in datos_estr:
            resultados = datos_estr.get("resultados", {})
            html.append('<ul>')
            if "cmc" in resultados and resultados["cmc"]:
                html.append(f'<li><a href="#{titulo_id}_cmc">1. Cálculo Mecánico de Cables</a></li>')
            if "dge" in resultados and resultados["dge"]:
                html.append(f'<li><a href="#{titulo_id}_dge">2. Diseño Geométrico</a></li>')
            if "dme" in resultados and resultados["dme"]:
                html.append(f'<li><a href="#{titulo_id}_dme">3. Diseño Mecánico</a></li>')
            if "arboles" in resultados and resultados["arboles"]:
                html.append(f'<li><a href="#{titulo_id}_arboles">4. Árboles de Carga</a></li>')
            if "sph" in resultados and resultados["sph"]:
                html.append(f'<li><a href="#{titulo_id}_sph">5. Selección de Poste</a></li>')
            if "fundacion" in resultados and resultados["fundacion"]:
                html.append(f'<li><a href="#{titulo_id}_fundacion">6. Fundación</a></li>')
            if "costeo" in resultados and resultados["costeo"]:
                html.append(f'<li><a href="#{titulo_id}_costeo">7. Costeo</a></li>')
            html.append('</ul>')
        html.append('</li>')
    
    html.append('<li><a href="#costeo-global">Costeo Global</a></li>')
    html.append('</ul></div>')
    return '\n'.join(html)

def generar_html_familia(nombre_familia, resultados_familia, checklist_activo=None):
    """Genera HTML completo para familia de estructuras
    
    Args:
        nombre_familia: Nombre de la familia
        resultados_familia: Resultados de cálculos
        checklist_activo: Dict con secciones activas {"cmc": True, "dge": True, ...}
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    indice = generar_indice_familia(nombre_familia, resultados_familia)
    secciones = [indice]
    secciones.append(generar_seccion_resumen_familia(nombre_familia, resultados_familia))
    
    estructuras = resultados_familia.get("resultados_estructuras", {})
    for nombre_estr, datos_estr in estructuras.items():
        titulo = datos_estr.get("titulo", nombre_estr)
        titulo_id = titulo.replace(" ", "_").replace("/", "_")
        secciones.append(f'<h2 id="{titulo_id}" style="margin-top:60px; border-top:3px solid #0d6efd; padding-top:20px;">{titulo}</h2>')
        
        if "error" in datos_estr:
            secciones.append(f'<div class="alert alert-danger">Error: {datos_estr["error"]}</div>')
        else:
            secciones.append(generar_seccion_estructura_familia(datos_estr, titulo_id, checklist_activo))
    
    costeo_global = resultados_familia.get("costeo_global", {})
    if costeo_global and (checklist_activo is None or checklist_activo.get("costeo")):
        secciones.append(generar_seccion_costeo_familia(costeo_global, estructuras))
    
    contenido_html = "\n".join(secciones)
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Familia - {nombre_familia}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ padding: 20px; font-family: Arial, sans-serif; background-color: #f8f9fa; }}
        .container-fluid {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #0d6efd; border-bottom: 3px solid #0d6efd; padding-bottom: 10px; }}
        h2 {{ color: #198754; margin-top: 40px; }}
        h3 {{ color: #0dcaf0; margin-top: 30px; border-bottom: 2px solid #0dcaf0; padding-bottom: 8px; }}
        h4 {{ color: #6c757d; margin-top: 20px; }}
        h5 {{ color: #adb5bd; margin-top: 15px; }}
        table {{ margin: 20px 0; font-size: 0.9em; }}
        table th {{ background-color: #e9ecef; font-weight: 600; }}
        pre {{ background-color: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; border: 1px solid #dee2e6; }}
        .alert {{ margin: 20px 0; padding: 15px; border-radius: 5px; }}
        .alert-success {{ background-color: #d1e7dd; border: 1px solid #badbcc; color: #0f5132; }}
        .indice {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .indice ul {{ list-style: none; padding-left: 0; }}
        .indice ul ul {{ padding-left: 25px; margin-top: 5px; }}
        .indice li {{ margin: 8px 0; }}
        .indice a {{ color: #0d6efd; text-decoration: none; }}
        .indice a:hover {{ text-decoration: underline; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; margin-bottom: 30px; }}
        .grid-2col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .grid-2col img {{ width: 100%; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1>Familia de Estructuras - {nombre_familia}</h1>
        <p class="timestamp">Generado: {timestamp}</p>
        <hr>
        {contenido_html}
    </div>
</body>
</html>"""


def generar_seccion_resumen_familia(nombre_familia, resultados_familia):
    """Genera HTML para resumen de familia"""
    html = ['<h3 id="resumen">RESUMEN DE FAMILIA</h3>']
    
    estructuras = resultados_familia.get("resultados_estructuras", {})
    costeo_global = resultados_familia.get("costeo_global", {})
    
    html.append('<table class="table table-bordered">')
    html.append(f'<tr><td><strong>Nombre Familia</strong></td><td>{nombre_familia}</td></tr>')
    html.append(f'<tr><td><strong>Cantidad de Estructuras</strong></td><td>{len(estructuras)}</td></tr>')
    
    if costeo_global:
        costo_global = costeo_global.get("costo_global", 0)
        html.append(f'<tr><td><strong>Costo Global</strong></td><td>{costo_global:,.2f} UM</td></tr>')
    
    html.append('</table>')
    
    html.append('<h4>Estructuras en la Familia</h4>')
    html.append('<table class="table table-striped table-bordered">')
    html.append('<thead><tr><th>Estructura</th><th>Título</th><th>Cantidad</th><th>Costo Individual</th><th>Costo Parcial</th></tr></thead>')
    html.append('<tbody>')
    
    for nombre_estr, datos_estr in estructuras.items():
        titulo = datos_estr.get("titulo", nombre_estr)
        cantidad = datos_estr.get("cantidad", 1)
        costo_ind = datos_estr.get("costo_individual", 0)
        costo_parc = costo_ind * cantidad
        
        html.append(f'<tr><td>{nombre_estr}</td><td>{titulo}</td><td>{cantidad}</td>')
        html.append(f'<td>{costo_ind:,.2f} UM</td><td>{costo_parc:,.2f} UM</td></tr>')
    
    html.append('</tbody></table>')
    return '\n'.join(html)


def generar_seccion_estructura_familia(datos_estructura, titulo_id, checklist_activo=None):
    """Genera HTML para estructura dentro de familia con IDs para navegación
    
    Args:
        datos_estructura: Datos de la estructura
        titulo_id: ID para navegación
        checklist_activo: Dict con secciones activas {"cmc": True, "dge": True, ...}
    """
    from utils.descargar_html import generar_seccion_cmc, generar_seccion_dge, generar_seccion_dme, generar_seccion_arboles, generar_seccion_sph, generar_seccion_fund
    
    html = []
    resultados = datos_estructura.get("resultados", {})
    
    # Si no hay checklist, incluir todo lo que tenga datos
    if checklist_activo is None:
        checklist_activo = {k: True for k in resultados.keys()}
    
    if checklist_activo.get("cmc") and "cmc" in resultados and resultados["cmc"]:
        html.append(f'<h4 id="{titulo_id}_cmc">1. Cálculo Mecánico de Cables</h4>')
        html.append(generar_seccion_cmc(resultados["cmc"]))
    if checklist_activo.get("dge") and "dge" in resultados and resultados["dge"]:
        html.append(f'<h4 id="{titulo_id}_dge">2. Diseño Geométrico</h4>')
        html.append(generar_seccion_dge(resultados["dge"]))
    if checklist_activo.get("dme") and "dme" in resultados and resultados["dme"]:
        html.append(f'<h4 id="{titulo_id}_dme">3. Diseño Mecánico</h4>')
        html.append(generar_seccion_dme(resultados["dme"]))
    if checklist_activo.get("arboles") and "arboles" in resultados and resultados["arboles"]:
        html.append(f'<h4 id="{titulo_id}_arboles">4. Árboles de Carga</h4>')
        html.append(generar_seccion_arboles(resultados["arboles"]))
    if checklist_activo.get("sph") and "sph" in resultados and resultados["sph"]:
        html.append(f'<h4 id="{titulo_id}_sph">5. Selección de Poste</h4>')
        html.append(generar_seccion_sph(resultados["sph"]))
    if checklist_activo.get("fundacion") and "fundacion" in resultados and resultados["fundacion"]:
        html.append(f'<h4 id="{titulo_id}_fundacion">6. Fundación</h4>')
        html.append(generar_seccion_fund(resultados["fundacion"]))
    if checklist_activo.get("costeo") and "costeo" in resultados and resultados["costeo"]:
        html.append(f'<h4 id="{titulo_id}_costeo">7. Costeo</h4>')
        html.append(generar_seccion_costeo_estructura(resultados["costeo"]))
    
    return '\n'.join(html)


def generar_seccion_costeo_familia(costeo_global, estructuras):
    """Genera HTML para costeo global"""
    html = ['<h2 id="costeo-global" style="margin-top:60px; border-top:3px solid #198754; padding-top:20px;">COSTEO GLOBAL</h2>']
    
    costo_global = costeo_global.get("costo_global", 0)
    costos_individuales = costeo_global.get("costos_individuales", {})
    costos_parciales = costeo_global.get("costos_parciales", {})
    
    html.append(f'<div class="alert alert-success"><h3>Costo Global: {costo_global:,.2f} UM</h3></div>')
    
    html.append('<table class="table table-striped table-bordered">')
    html.append('<thead><tr><th>Estructura</th><th>Costo Individual</th><th>Cantidad</th><th>Costo Parcial</th></tr></thead>')
    html.append('<tbody>')
    
    for titulo in sorted(costos_individuales.keys(), key=lambda x: costos_individuales[x], reverse=True):
        costo_ind = costos_individuales[titulo]
        costo_parc = costos_parciales.get(titulo, 0)
        
        cantidad = 1
        for nombre_estr, datos_estr in estructuras.items():
            if datos_estr.get("titulo") == titulo:
                cantidad = datos_estr.get("cantidad", 1)
                break
        
        html.append(f'<tr><td>{titulo}</td><td>{costo_ind:,.2f} UM</td>')
        html.append(f'<td>{cantidad}</td><td><strong>{costo_parc:,.2f} UM</strong></td></tr>')
    
    html.append('</tbody></table>')
    return '\n'.join(html)
