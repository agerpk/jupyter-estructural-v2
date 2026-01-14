"""Utilidad para generar HTML descargable desde cachés"""

from datetime import datetime
import pandas as pd
import base64
import json
from io import StringIO
from pathlib import Path
from config.app_config import CACHE_DIR
from utils.calculo_cache import CalculoCache
from utils.view_helpers import ViewHelpers
from utils.descargar_html_familia_fix import generar_seccion_costeo_estructura
from utils.descargar_html_familia_completo import generar_html_familia as generar_html_familia_completo


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
    
    # 6. Fundaciones
    calculo_fund = CalculoCache.cargar_calculo_fund(nombre_estructura)
    if calculo_fund:
        secciones.append(generar_seccion_fund(calculo_fund))
    
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
        df = pd.read_json(StringIO(calculo_cmc['df_conductor_html']), orient='split').round(2)
        html.append('<h5>Conductor</h5>')
        html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm', index=False))
    
    if calculo_cmc.get('df_guardia1_html'):
        df = pd.read_json(StringIO(calculo_cmc['df_guardia1_html']), orient='split').round(2)
        html.append('<h5>Cable de Guardia 1</h5>')
        html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm', index=False))
    
    if calculo_cmc.get('df_guardia2_html'):
        df = pd.read_json(StringIO(calculo_cmc['df_guardia2_html']), orient='split').round(2)
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
        df = pd.read_json(StringIO(calculo_dme['df_reacciones_html']), orient='split').round(2)
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
        df = pd.read_json(StringIO(calculo_arboles['df_resumen_html']), orient='split')
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
    
    resultados = calculo_sph.get('resultados', {})
    
    if resultados.get('configuracion_seleccionada'):
        config = resultados['configuracion_seleccionada']
        html.append('<h5>Configuración Seleccionada</h5>')
        html.append('<table class="table table-bordered params-table">')
        for campo, valor in config.items():
            html.append(f'<tr><td>{campo}</td><td>{valor}</td></tr>')
        html.append('</table>')
    
    if resultados.get('desarrollo_texto'):
        html.append('<hr><h5>Desarrollo del Cálculo</h5>')
        html.append(f'<pre>{resultados["desarrollo_texto"]}</pre>')
    
    return '\n'.join(html)


def generar_html_comparativa(titulo, comparativa_data, resultados_html=None):
    """Genera HTML completo para comparativa de cables
    
    Args:
        titulo: Título de la comparativa
        comparativa_data: Datos de configuración de la comparativa
        resultados_html: Componentes HTML de resultados (opcional)
        
    Returns:
        String con HTML completo
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Cargar cache si existe
    cache_data = CalculoCache.cargar_calculo_comparar_cmc(titulo)
    
    # Generar secciones HTML
    secciones = []
    
    # 1. Parámetros de comparativa
    secciones.append(generar_seccion_parametros_comparativa(comparativa_data))
    
    # 2. Tabla comparativa
    if cache_data:
        secciones.append(generar_seccion_tabla_comparativa(cache_data))
    
    # 3. Gráficos comparativos
    if cache_data:
        secciones.append(generar_seccion_graficos_comparativos(cache_data))
    
    # 4. Resultados por cable
    if cache_data:
        secciones.append(generar_seccion_resultados_por_cable(cache_data))
    
    contenido_html = "\n".join(secciones)
    
    html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Comparativa de Cables - {titulo}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
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
        img {{ max-width: 100%; height: auto; margin: 20px 0; border: 1px solid #dee2e6; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; margin-bottom: 30px; }}
        .params-table {{ font-size: 0.9em; }}
        .params-table td:first-child {{ font-weight: 600; background-color: #f8f9fa; }}
        .cable-section {{ margin: 40px 0; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1>Comparativa de Cables - {titulo}</h1>
        <p class="timestamp">Generado: {timestamp}</p>
        <hr>
        {contenido_html}
    </div>
</body>
</html>"""
    
    return html_completo


def generar_seccion_parametros_comparativa(comparativa_data):
    """Genera HTML para parámetros de comparativa"""
    import json
    
    html = ['<h3>PARÁMETROS DE COMPARATIVA</h3>']
    
    # Cables seleccionados
    cables = comparativa_data.get("cables_seleccionados", [])
    html.append(f'<h5>Cables Comparados ({len(cables)})</h5>')
    html.append('<ul>')
    for cable in cables:
        html.append(f'<li>{cable}</li>')
    html.append('</ul>')
    
    # Parámetros de línea
    params_linea = comparativa_data.get("parametros_linea", {})
    if params_linea:
        html.append('<h5>Parámetros de Línea</h5>')
        html.append('<table class="table table-bordered params-table">')
        for campo, valor in params_linea.items():
            html.append(f'<tr><td>{campo}</td><td>{valor}</td></tr>')
        html.append('</table>')
    
    # Estados climáticos
    estados = comparativa_data.get("estados_climaticos", {})
    if estados:
        html.append('<h5>Estados Climáticos</h5>')
        html.append('<table class="table table-bordered table-striped">')
        html.append('<thead><tr><th>Estado</th><th>Temp (°C)</th><th>Descripción</th><th>Viento (m/s)</th><th>Hielo (m)</th><th>Rest. Cond.</th></tr></thead>')
        html.append('<tbody>')
        for estado_id, estado_data in estados.items():
            html.append(f'<tr>')
            html.append(f'<td><strong>{estado_id}</strong></td>')
            html.append(f'<td>{estado_data.get("temperatura", 0)}</td>')
            html.append(f'<td>{estado_data.get("descripcion", "")}</td>')
            html.append(f'<td>{estado_data.get("viento_velocidad", 0)}</td>')
            html.append(f'<td>{estado_data.get("hielo_espesor", 0)}</td>')
            html.append(f'<td>{estado_data.get("restriccion_conductor", 0.25)}</td>')
            html.append(f'</tr>')
        html.append('</tbody></table>')
    
    return '\n'.join(html)


def generar_seccion_tabla_comparativa(cache_data):
    """Genera HTML para tabla comparativa completa"""
    html = ['<h3>TABLA COMPARATIVA DE CABLES</h3>']
    
    resultados = cache_data.get("resultados", {})
    cables_calculados = resultados.get("cables_calculados", [])
    dataframes = resultados.get("dataframes", {})
    
    if cables_calculados and dataframes:
        try:
            # Cargar propiedades de cables desde cables.json
            from config.app_config import DATA_DIR
            cables_path = DATA_DIR / "cables.json"
            
            propiedades_cables = {}
            if cables_path.exists():
                with open(cables_path, 'r', encoding='utf-8') as f:
                    cables_data = json.load(f)
                    propiedades_cables = cables_data
            
            # Crear tabla HTML
            html.append('<table class="table table-striped table-bordered">')
            html.append('<thead><tr><th>Valores/Cable</th>')
            for cable in cables_calculados:
                html.append(f'<th>{cable}</th>')
            html.append('</tr></thead><tbody>')
            
            # Filas de propiedades
            filas_datos = []
            
            # Fila 1: Sección Total
            fila = ["Sección Total (mm²)"]
            for cable_nombre in cables_calculados:
                cable_props = propiedades_cables.get(cable_nombre, {})
                tipo_cable = cable_props.get("tipo", "")
                
                if "ACSS" in tipo_cable:
                    seccion = cable_props.get("seccion_acero_mm2")
                    if seccion is not None:
                        fila.append(f"{seccion:.1f} (acero)")
                    else:
                        fila.append("N/A (acero)")
                else:
                    seccion = cable_props.get("seccion_total_mm2", "N/A")
                    if isinstance(seccion, (int, float)):
                        fila.append(f"{seccion:.1f}")
                    else:
                        fila.append("N/A")
            filas_datos.append(fila)
            
            # Fila 2: Diámetro Total
            fila = ["Diámetro Total (mm)"]
            for cable_nombre in cables_calculados:
                diametro = propiedades_cables.get(cable_nombre, {}).get("diametro_total_mm", "N/A")
                fila.append(f"{diametro}" if diametro != "N/A" else "N/A")
            filas_datos.append(fila)
            
            # Fila 3: Peso Unitario
            fila = ["Peso Unitario (daN/m)"]
            for cable_nombre in cables_calculados:
                peso = propiedades_cables.get(cable_nombre, {}).get("peso_unitario_dan_m", "N/A")
                fila.append(f"{peso}" if peso != "N/A" else "N/A")
            filas_datos.append(fila)
            
            # Fila 4: Carga de Rotura
            fila = ["Carga Rotura (daN)"]
            for cable_nombre in cables_calculados:
                rotura = propiedades_cables.get(cable_nombre, {}).get("carga_rotura_minima_dan", "N/A")
                fila.append(f"{rotura:,.0f}" if isinstance(rotura, (int, float)) else "N/A")
            filas_datos.append(fila)
            
            # Fila 5: Módulo de Elasticidad
            fila = ["Módulo Elasticidad (daN/mm²)"]
            for cable_nombre in cables_calculados:
                cable_props = propiedades_cables.get(cable_nombre, {})
                tipo_cable = cable_props.get("tipo", "")
                
                if "ACSS" in tipo_cable:
                    modulo = cable_props.get("modulo_elasticidad_acero_dan_mm2")
                    if modulo is not None:
                        fila.append(f"{modulo} (acero)")
                    else:
                        fila.append("N/A (acero)")
                else:
                    modulo = cable_props.get("modulo_elasticidad_dan_mm2", "N/A")
                    fila.append(f"{modulo}" if modulo != "N/A" else "N/A")
            filas_datos.append(fila)
            
            # Fila 6: Coeficiente Dilatación
            fila = ["Coef. Dilatación (1/°C)"]
            for cable_nombre in cables_calculados:
                cable_props = propiedades_cables.get(cable_nombre, {})
                tipo_cable = cable_props.get("tipo", "")
                
                if "ACSS" in tipo_cable:
                    dilatacion = cable_props.get("coeficiente_dilatacion_acero_1_c")
                    if dilatacion is not None:
                        fila.append(f"{dilatacion:.2e} (acero)")
                    else:
                        fila.append("N/A (acero)")
                else:
                    dilatacion = cable_props.get("coeficiente_dilatacion_1_c", "N/A")
                    if isinstance(dilatacion, (int, float)):
                        fila.append(f"{dilatacion:.2e}")
                    else:
                        fila.append("N/A")
            filas_datos.append(fila)
            
            # Fila 7: Flecha Máxima
            fila = ["Flecha Máxima (m)"]
            for cable_nombre in cables_calculados:
                flecha_max = 0
                try:
                    if cable_nombre in dataframes:
                        df = pd.read_json(StringIO(dataframes[cable_nombre]), orient='split')
                        
                        for col in df.columns:
                            if 'Flecha' in str(col) and ('m]' in str(col) or 'Vertical' in str(col)):
                                flecha_max = df[col].max()
                                break
                                
                    fila.append(f"{flecha_max:.3f}" if flecha_max > 0 else "N/A")
                except:
                    fila.append("N/A")
            filas_datos.append(fila)
            
            # Fila 8: Tiro Máximo
            fila = ["Tiro Máximo (daN)"]
            for cable_nombre in cables_calculados:
                tiro_max = 0
                try:
                    if cable_nombre in dataframes:
                        df = pd.read_json(StringIO(dataframes[cable_nombre]), orient='split')
                        
                        for col in df.columns:
                            if 'Tiro' in str(col) and 'daN' in str(col):
                                tiro_max = df[col].max()
                                break
                                
                    fila.append(f"{tiro_max:,.0f}" if tiro_max > 0 else "N/A")
                except:
                    fila.append("N/A")
            filas_datos.append(fila)
            
            # Generar filas HTML
            for fila_data in filas_datos:
                html.append('<tr>')
                for i, valor in enumerate(fila_data):
                    if i == 0:  # Primera columna (nombre de propiedad)
                        html.append(f'<td><strong>{valor}</strong></td>')
                    else:
                        html.append(f'<td>{valor}</td>')
                html.append('</tr>')
            
            html.append('</tbody></table>')
            
        except Exception as e:
            html.append(f'<p>Error generando tabla comparativa: {e}</p>')
    
    return '\n'.join(html)


def generar_seccion_graficos_comparativos(cache_data):
    """Genera HTML para gráficos comparativos"""
    html = ['<h3>GRÁFICOS COMPARATIVOS</h3>']
    
    resultados = cache_data.get("resultados", {})
    graficos = resultados.get("graficos", {})
    hash_params = cache_data.get("hash_parametros")
    
    if "comparativo" in graficos and hash_params:
        # Gráfico de flechas
        if "flechas" in graficos["comparativo"]:
            nombre_png = f"CC_Flechas.{hash_params}.png"
            img_str = ViewHelpers.cargar_imagen_base64(nombre_png)
            if img_str:
                html.append('<h5>Comparativa de Flechas</h5>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="Comparativa de Flechas">')
        
        # Gráfico de tiros
        if "tiros" in graficos["comparativo"]:
            nombre_png = f"CC_Tiros.{hash_params}.png"
            img_str = ViewHelpers.cargar_imagen_base64(nombre_png)
            if img_str:
                html.append('<h5>Comparativa de Tiros</h5>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="Comparativa de Tiros">')
    
    return '\n'.join(html)


def generar_seccion_resultados_por_cable(cache_data):
    """Genera HTML para resultados detallados por cable"""
    html = ['<h3>RESULTADOS DETALLADOS POR CABLE</h3>']
    
    resultados = cache_data.get("resultados", {})
    cables_calculados = resultados.get("cables_calculados", [])
    dataframes = resultados.get("dataframes", {})
    graficos = resultados.get("graficos", {})
    errores = resultados.get("errores", {})
    
    # Cables exitosos
    for cable_nombre in cables_calculados:
        html.append(f'<div class="cable-section">')
        html.append(f'<h4>{cable_nombre}</h4>')
        
        # Tabla de resultados
        if cable_nombre in dataframes:
            try:
                df = pd.read_json(StringIO(dataframes[cable_nombre]), orient='split')
                html.append('<h6>Resultados por Estado Climático</h6>')
                html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm', index=False))
            except Exception as e:
                html.append(f'<p>Error cargando tabla: {e}</p>')
        
        # Gráficos del cable
        if cable_nombre in graficos:
            hash_params = cache_data.get("hash_parametros")
            for nombre_grafico, archivos in graficos[cable_nombre].items():
                if "png" in archivos:
                    img_str = ViewHelpers.cargar_imagen_base64(archivos["png"])
                    if img_str:
                        html.append(f'<h6>{nombre_grafico}</h6>')
                        html.append(f'<img src="data:image/png;base64,{img_str}" alt="{nombre_grafico}">')
        
        html.append('</div>')
    
    # Cables con errores
    for cable_nombre, error_msg in errores.items():
        html.append(f'<div class="cable-section">')
        html.append(f'<h4>{cable_nombre} (Error)</h4>')
        html.append(f'<div class="alert alert-danger">Error: {error_msg}</div>')
        html.append('</div>')
    
    return '\n'.join(html)


def generar_html_familia(nombre_familia, resultados_familia):
    """Genera HTML completo para familia de estructuras - usa implementación completa"""
    return generar_html_familia_completo(nombre_familia, resultados_familia)


def generar_seccion_fund(calculo_fund):
    """Genera HTML para sección Fundaciones"""
    html = ['<h3>6. CÁLCULO DE FUNDACIONES</h3>']
    
    parametros = calculo_fund.get('parametros', {})
    resultados = calculo_fund.get('resultados', {})
    
    if parametros:
        html.append('<h5>Parámetros de Fundación</h5>')
        html.append('<table class="table table-bordered params-table">')
        for campo, valor in parametros.items():
            html.append(f'<tr><td>{campo}</td><td>{valor}</td></tr>')
        html.append('</table>')
    
    if resultados:
        html.append('<h5>Resultados</h5>')
        html.append('<table class="table table-bordered params-table">')
        for campo, valor in resultados.items():
            if isinstance(valor, (int, float)):
                html.append(f'<tr><td>{campo}</td><td>{valor:.2f}</td></tr>')
            else:
                html.append(f'<tr><td>{campo}</td><td>{valor}</td></tr>')
        html.append('</table>')
    
    imagen_3d = calculo_fund.get('imagen_3d')
    if imagen_3d:
        nombre_png = imagen_3d.replace('.json', '.png')
        img_str = ViewHelpers.cargar_imagen_base64(nombre_png)
        if img_str:
            html.append('<h5>Visualización 3D</h5>')
            html.append(f'<img src="data:image/png;base64,{img_str}" alt="Fundación 3D">')
    
    return '\n'.join(html)


