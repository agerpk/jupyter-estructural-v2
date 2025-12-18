"""Utilidad para generar HTML descargable desde cachés"""

from datetime import datetime
import pandas as pd
import base64
from pathlib import Path
from config.app_config import CACHE_DIR
from utils.calculo_cache import CalculoCache
from utils.view_helpers import ViewHelpers


def generar_html_completo(estructura_actual):
    """Genera HTML completo desde cachés individuales
    
    Args:
        estructura_actual: Dict con datos de estructura
        
    Returns:
        String con HTML completo
    """
    if not estructura_actual:
        return "<html><body><h1>No hay estructura cargada</h1></body></html>"
    
    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generar secciones HTML
    secciones = []
    
    # 0. Parámetros de estructura
    secciones.append(generar_seccion_parametros(estructura_actual))
    
    # 1. CMC
    calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
    if calculo_cmc:
        secciones.append(generar_seccion_cmc(calculo_cmc))
    
    # 2. DGE
    calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
    if calculo_dge:
        secciones.append(generar_seccion_dge(calculo_dge))
    
    # 3. DME
    calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
    if calculo_dme:
        secciones.append(generar_seccion_dme(calculo_dme))
    
    # 4. Árboles
    calculo_arboles = CalculoCache.cargar_calculo_arboles(nombre_estructura)
    if calculo_arboles:
        secciones.append(generar_seccion_arboles(calculo_arboles))
    
    # 5. SPH
    calculo_sph = CalculoCache.cargar_calculo_sph(nombre_estructura)
    if calculo_sph:
        secciones.append(generar_seccion_sph(calculo_sph))
    
    contenido_html = "\n".join(secciones)
    
    html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cálculo Completo - {nombre_estructura}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.18.0.min.js"></script>
    <style>
        body {{ padding: 20px; font-family: Arial, sans-serif; background-color: #f8f9fa; }}
        .container-fluid {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #0d6efd; border-bottom: 3px solid #0d6efd; padding-bottom: 10px; }}
        h3 {{ color: #198754; margin-top: 40px; border-bottom: 2px solid #198754; padding-bottom: 8px; }}
        h4 {{ color: #0dcaf0; margin-top: 30px; }}
        h5 {{ color: #6c757d; margin-top: 20px; }}
        h6 {{ color: #adb5bd; margin-top: 15px; font-style: italic; }}
        table {{ margin: 20px 0; font-size: 0.9em; }}
        table th {{ background-color: #e9ecef; font-weight: 600; }}
        pre {{ background-color: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; font-size: 0.85em; overflow-x: auto; }}
        .alert {{ margin: 20px 0; padding: 15px; border-radius: 5px; }}
        .alert-success {{ background-color: #d1e7dd; border: 1px solid #badbcc; color: #0f5132; }}
        .alert-warning {{ background-color: #fff3cd; border: 1px solid #ffecb5; color: #664d03; }}
        .alert-info {{ background-color: #cff4fc; border: 1px solid #b6effb; color: #055160; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; border: 1px solid #dee2e6; }}
        .plotly-graph-div {{ margin: 20px 0; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; margin-bottom: 30px; }}
        .grid-2col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .grid-2col img {{ width: 100%; }}
        .params-table {{ font-size: 0.9em; }}
        .params-table td:first-child {{ font-weight: 600; background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1>Cálculo Completo - {nombre_estructura}</h1>
        <p class="timestamp">Generado: {timestamp}</p>
        <hr>
        {contenido_html}
    </div>
</body>
</html>"""
    
    return html_completo


def generar_seccion_parametros(estructura_actual):
    """Genera HTML para parámetros de estructura"""
    import json
    
    html = ['<h3>PARÁMETROS DE ESTRUCTURA</h3>']
    
    html.append('<table class="table table-bordered params-table">')
    
    # Mostrar todos los parámetros ordenados alfabéticamente
    for campo in sorted(estructura_actual.keys()):
        valor = estructura_actual[campo]
        
        # Formatear valores complejos (dict, list) como JSON
        if isinstance(valor, (dict, list)):
            valor_str = json.dumps(valor, indent=2, ensure_ascii=False)
            html.append(f'<tr><td>{campo}</td><td><pre style="margin:0; background:#1e1e1e; color:#d4d4d4; padding:8px; border-radius:4px; font-size:0.85em;">{valor_str}</pre></td></tr>')
        else:
            html.append(f'<tr><td>{campo}</td><td style="color:#212529;">{valor}</td></tr>')
    
    html.append('</table>')
    
    return '\n'.join(html)


def generar_seccion_cmc(calculo_cmc):
    """Genera HTML para sección CMC"""
    html = ['<h3>1. CÁLCULO MECÁNICO DE CABLES (CMC)</h3>']
    
    # Tablas de DataFrames
    if calculo_cmc.get('df_conductor_html'):
        df = pd.read_json(calculo_cmc['df_conductor_html'], orient='split').round(2)
        html.append('<h5>Conductor</h5>')
        html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm', index=False))
    
    if calculo_cmc.get('df_guardia1_html'):
        df = pd.read_json(calculo_cmc['df_guardia1_html'], orient='split').round(2)
        html.append('<h5>Cable de Guardia 1</h5>')
        html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm', index=False))
    
    if calculo_cmc.get('df_guardia2_html'):
        df = pd.read_json(calculo_cmc['df_guardia2_html'], orient='split').round(2)
        html.append('<h5>Cable de Guardia 2</h5>')
        html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm', index=False))
    
    # Gráficos como PNG (convertir desde JSON)
    hash_params = calculo_cmc.get('hash_parametros')
    if hash_params:
        html.append('<h5>Gráficos de Flechas</h5>')
        
        for nombre_json, titulo in [
            (f"CMC_Combinado.{hash_params}.json", "Conductor y Guardia"),
            (f"CMC_Conductor.{hash_params}.json", "Solo Conductor"),
            (f"CMC_Guardia.{hash_params}.json", "Solo Cable de Guardia 1"),
            (f"CMC_Guardia2.{hash_params}.json", "Solo Cable de Guardia 2")
        ]:
            # Intentar cargar PNG primero
            nombre_png = nombre_json.replace('.json', '.png')
            img_str = ViewHelpers.cargar_imagen_base64(nombre_png)
            if img_str:
                html.append(f'<h6>{titulo}</h6>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="{titulo}">')
    
    # Console output
    if calculo_cmc.get('console_output'):
        html.append('<hr><h5>Output de Cálculo</h5>')
        html.append(f'<pre>{calculo_cmc["console_output"]}</pre>')
    
    return '\n'.join(html)


def generar_seccion_dge(calculo_dge):
    """Genera HTML para sección DGE"""
    html = ['<h3>2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)</h3>']
    
    hash_params = calculo_dge.get('hash_parametros')
    if hash_params:
        for nombre, titulo in [
            (f"Estructura.{hash_params}.png", "Estructura Completa"),
            (f"Cabezal.{hash_params}.png", "Detalle Cabezal"),
            (f"Nodos.{hash_params}.png", "Nodos y Coordenadas")
        ]:
            img_str = ViewHelpers.cargar_imagen_base64(nombre)
            if img_str:
                html.append(f'<h5>{titulo}</h5>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="{titulo}">')
    
    if calculo_dge.get('memoria_calculo'):
        html.append('<hr><h5>Memoria de Cálculo</h5>')
        html.append(f'<pre>{calculo_dge["memoria_calculo"]}</pre>')
    
    return '\n'.join(html)


def generar_seccion_dme(calculo_dme):
    """Genera HTML para sección DME"""
    html = ['<h3>3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)</h3>']
    
    if calculo_dme.get('df_reacciones_html'):
        df = pd.read_json(calculo_dme['df_reacciones_html'], orient='split').round(2)
        html.append('<h5>Reacciones por Hipótesis</h5>')
        html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm'))
    
    hash_params = calculo_dme.get('hash_parametros')
    if hash_params:
        for nombre, titulo in [
            (f"DME_Polar.{hash_params}.png", "Diagrama Polar de Reacciones"),
            (f"DME_Barras.{hash_params}.png", "Diagrama de Barras")
        ]:
            img_str = ViewHelpers.cargar_imagen_base64(nombre)
            if img_str:
                html.append(f'<h5>{titulo}</h5>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="{titulo}">')
    
    return '\n'.join(html)


def generar_seccion_arboles(calculo_arboles):
    """Genera HTML para sección Árboles de Carga"""
    html = ['<h3>4. ÁRBOLES DE CARGA</h3>']
    
    if calculo_arboles.get('df_resumen_html'):
        df = pd.read_json(calculo_arboles['df_resumen_html'], orient='split')
        html.append('<h5>Resumen de Cargas por Hipótesis</h5>')
        html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm'))
    
    imagenes = calculo_arboles.get('imagenes', [])
    if imagenes:
        html.append('<h5>Diagramas de Árboles de Carga</h5>')
        html.append('<div class="grid-2col">')
        
        for img_item in imagenes:
            # imagenes puede ser lista de strings o lista de dicts
            img_nombre = img_item if isinstance(img_item, str) else img_item.get('nombre', '')
            if img_nombre:
                img_str = ViewHelpers.cargar_imagen_base64(img_nombre)
                if img_str:
                    titulo = img_nombre.split("HIP_")[-1].replace(".png", "") if "HIP_" in img_nombre else img_nombre
                    html.append(f'<div><h6>{titulo}</h6><img src="data:image/png;base64,{img_str}" alt="{img_nombre}"></div>')
        
        html.append('</div>')
    
    return '\n'.join(html)


def generar_seccion_sph(calculo_sph):
    """Genera HTML para sección SPH"""
    html = ['<h3>5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)</h3>']
    
    if calculo_sph.get('desarrollo_texto'):
        html.append('<h5>Desarrollo del Cálculo</h5>')
        html.append(f'<pre>{calculo_sph["desarrollo_texto"]}</pre>')
    
    return '\n'.join(html)
