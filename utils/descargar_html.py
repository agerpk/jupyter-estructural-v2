"""Utilidad para generar HTML descargable desde cachés"""

from datetime import datetime
import pandas as pd
import base64
import json
from io import StringIO
from pathlib import Path
import logging
from config.app_config import CACHE_DIR
from utils.calculo_cache import CalculoCache
from utils.view_helpers import ViewHelpers
from utils.descargar_html_familia_fix import generar_seccion_costeo_estructura
from utils.descargar_html_familia_completo import generar_html_familia as generar_html_familia_completo

# Logger y helpers para formateo seguro
logger = logging.getLogger(__name__)

def _safe_format(value, fmt=None, default="N/A", name=None):
    """Formatea valores numéricos de forma segura. Devuelve 'N/A' si value es None o falla."""
    try:
        if value is None:
            logger.debug(f"Valor None al formatear: {name}")
            return default
        if fmt and isinstance(value, (int, float)):
            try:
                return format(value, fmt)
            except Exception as e:
                logger.debug(f"Error formateando {name} con fmt '{fmt}': {e} - valor={value}")
                return default
        return str(value)
    except Exception as e:
        logger.exception(f"Error en _safe_format {name}: {e}")
        return default


def _load_image_base64(nombre, context=None):
    """Cargar imagen en base64 con logging en DEBUG si falta o falla."""
    try:
        img_str = ViewHelpers.cargar_imagen_base64(nombre)
        if not img_str:
            logger.debug(f"Imagen no encontrada: {nombre} (context={context})")
        return img_str
    except Exception as e:
        logger.exception(f"Error cargando imagen {nombre}: {e}")
        return None



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

    # Intentar cargar logo embebido (logo_distrocuyo.png)
    try:
        logo_b64 = _load_image_base64('logo_distrocuyo.png', context='global')
        if logo_b64:
            logo_html = f'<img id="logo_distrocuyo" src="data:image/png;base64,{logo_b64}" alt="logo" draggable="false" style="position:fixed; top:20px; right:30px; height:50px; width:auto; pointer-events:none; user-select:none; -webkit-user-drag:none; z-index:9999;">'
        else:
            logo_html = ''
    except Exception as e:
        logger.debug(f"Logo no encontrado o error cargando logo: {e}")
        logo_html = ''

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
        secciones.append(generar_seccion_dge(calculo_dge, id_prefix=nombre_estructura.replace(' ','_').replace('/','_')))
    
    # 3. DME
    calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
    if calculo_dme:
        secciones.append(generar_seccion_dme(calculo_dme, id_prefix=nombre_estructura.replace(' ','_').replace('/','_')))
    
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
    
    # 7. AEE
    calculo_aee = CalculoCache.cargar_calculo_aee(nombre_estructura)
    if calculo_aee:
        secciones.append(generar_seccion_aee(calculo_aee, estructura_actual))
    
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
        .container-fluid {{ position: relative; max-width: 1400px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        /* logo image is absolutely positioned within the container and is non-interactive */
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
    <div class="container-fluid">{logo_html}
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


def generar_seccion_dge(calculo_dge, id_prefix=None):
    """Genera HTML para sección DGE (acepta id_prefix para anclar subsecciones)"""
    html = ['<h3>2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)</h3>']
    
    logger.debug(f"Generando DGE (keys: {list(calculo_dge.keys())})")
    # Dimensiones y parámetros
    dimensiones = calculo_dge.get('dimensiones', {})
    if dimensiones:
        if id_prefix:
            html.append(f'<h5 id="{id_prefix}_dge_dimensiones">Dimensiones de Estructura</h5>')
        else:
            html.append('<h5>Dimensiones de Estructura</h5>')
        html.append('<table class="table table-bordered params-table">')
        for campo, valor in dimensiones.items():
            if isinstance(valor, (int, float)):
                formatted = _safe_format(valor, ".3f", name=f"dimensiones.{campo}")
                html.append(f'<tr><td>{campo}</td><td>{formatted}</td></tr>')
            else:
                html.append(f'<tr><td>{campo}</td><td>{valor}</td></tr>')
        html.append('</table>')
    
    # Nodos estructurales
    nodes_key = calculo_dge.get('nodes_key', {})
    if nodes_key:
        if id_prefix:
            html.append(f'<h5 id="{id_prefix}_dge_nodos">Nodos Estructurales</h5>')
        else:
            html.append('<h5>Nodos Estructurales</h5>')
        html.append('<table class="table table-striped table-bordered table-sm">')
        html.append('<thead><tr><th>Nodo</th><th>X (m)</th><th>Y (m)</th><th>Z (m)</th></tr></thead>')
        html.append('<tbody>')
        for nombre_nodo, coords in nodes_key.items():
            if isinstance(coords, (list, tuple)) and len(coords) >= 3:
                x = _safe_format(coords[0], ".3f", name=f"node.{nombre_nodo}.x")
                y = _safe_format(coords[1], ".3f", name=f"node.{nombre_nodo}.y")
                z = _safe_format(coords[2], ".3f", name=f"node.{nombre_nodo}.z")
                html.append(f'<tr><td><strong>{nombre_nodo}</strong></td><td>{x}</td><td>{y}</td><td>{z}</td></tr>')
        html.append('</tbody></table>')
    
    # Imágenes
    hash_params = calculo_dge.get('hash_parametros')
    if hash_params:
        html.append('<h5>Diagramas</h5>')
        for nombre, titulo, shortid in [
            (f"Estructura.{hash_params}.png", "Estructura Completa", 'graf_estructura'),
            (f"Cabezal.{hash_params}.png", "Detalle Cabezal", 'graf_cabezal'),
            (f"Nodos.{hash_params}.png", "Nodos y Coordenadas", 'graf_nodos')
        ]:
            img_str = ViewHelpers.cargar_imagen_base64(nombre)
            if img_str:
                if id_prefix:
                    html.append(f'<h6 id="{id_prefix}_dge_{shortid}">{titulo}</h6>')
                else:
                    html.append(f'<h6>{titulo}</h6>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="{titulo}">')

    # Nota: la tabla PLS-CADD se mostrará como una subsección independiente dentro de DGE en la versión "familia".
    # Para la vista individual (calculo completo) no incluimos descarga ni preview de CSV aquí.
    pass
    
    # Servidumbre
    servidumbre_data = calculo_dge.get('servidumbre')
    if servidumbre_data:
        html.append('<h5>Franja de Servidumbre AEA-95301-2007</h5>')
        html.append('<table class="table table-bordered params-table">')
        a_val = _safe_format(servidumbre_data.get("A"), ".3f", name="servidumbre.A")
        c_val = _safe_format(servidumbre_data.get("C"), ".3f", name="servidumbre.C")
        d_val = _safe_format(servidumbre_data.get("d"), ".3f", name="servidumbre.d")
        dm_val = _safe_format(servidumbre_data.get("dm"), ".3f", name="servidumbre.dm")
        vs_val = _safe_format(servidumbre_data.get("Vs"), ".2f", name="servidumbre.Vs")
        html.append(f'<tr><td>Ancho total franja (A)</td><td>{a_val} m</td></tr>')
        html.append(f'<tr><td>Distancia conductores externos (C)</td><td>{c_val} m</td></tr>')
        html.append(f'<tr><td>Distancia seguridad (d)</td><td>{d_val} m</td></tr>')
        html.append(f'<tr><td>Distancia mínima (dm)</td><td>{dm_val} m</td></tr>')
        html.append(f'<tr><td>Tensión sobretensión (Vs)</td><td>{vs_val} kV</td></tr>')
        html.append('</table>')
        
        if servidumbre_data.get('memoria_calculo'):
            html.append('<h6>Memoria de Cálculo</h6>')
            html.append(f'<pre>{servidumbre_data["memoria_calculo"]}</pre>')
        
        # Gráfico de servidumbre
        if hash_params:
            nombre_serv = f"Servidumbre.{hash_params}.png"
            img_str = _load_image_base64(nombre_serv, context="servidumbre")
            if img_str:
                html.append('<h6>Gráfico de Franja de Servidumbre</h6>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="Servidumbre">')
    
    # Memoria de cálculo
    if calculo_dge.get('memoria_calculo'):
        html.append('<hr><h5>Memoria de Cálculo</h5>')
        html.append(f'<pre>{calculo_dge["memoria_calculo"]}</pre>')
    
    return '\n'.join(html)


def generar_seccion_dme(calculo_dme, id_prefix=None):
    """Genera HTML para sección DME (acepta id_prefix para anclar subsecciones)"""
    html = ['<h3>3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)</h3>']
    
    # Resumen ejecutivo (opcional)
    resumen_keys = ['resumen_ejecutivo','resumen','texto_resumen','resumen_html']
    resumen = None
    for k in resumen_keys:
        if calculo_dme.get(k):
            resumen = calculo_dme.get(k)
            break
    if resumen:
        if id_prefix:
            html.append(f'<h5 id="{id_prefix}_dme_resumen">Resumen Ejecutivo</h5>')
        else:
            html.append('<h5>Resumen Ejecutivo</h5>')
        html.append(f'<pre>{resumen}</pre>')

    # Tabla resumen de reacciones
    if calculo_dme.get('df_reacciones_html'):
        df = pd.read_json(StringIO(calculo_dme['df_reacciones_html']), orient='split').round(2)
        if id_prefix:
            html.append(f'<h5 id="{id_prefix}_dme_tabla_reacciones">Tabla Resumen de Reacciones y Tiros</h5>')
        else:
            html.append('<h5>Tabla Resumen de Reacciones y Tiros</h5>')
        html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm'))
    
    hash_params = calculo_dme.get('hash_parametros')
    if hash_params:
        for nombre, titulo, shortid in [
            (f"DME_Polar.{hash_params}.png", "Diagrama Polar de Reacciones", 'polar'),
            (f"DME_Barras.{hash_params}.png", "Diagrama de Barras", 'barras')
        ]:
            img_str = _load_image_base64(nombre, context="DME")
            if img_str:
                if id_prefix:
                    html.append(f'<h5 id="{id_prefix}_dme_{shortid}">{titulo}</h5>')
                else:
                    html.append(f'<h5>{titulo}</h5>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="{titulo}">')
            else:
                logger.debug(f"Imagen DME faltante: {nombre}")
                html.append(f'<div class="alert alert-warning">No se encontró imagen: {titulo} ({nombre})</div>')
    
    return '\n'.join(html)


def generar_seccion_arboles(calculo_arboles):
    """Genera HTML para sección Árboles de Carga"""
    html = ['<h3>4. ÁRBOLES DE CARGA</h3>']

    # Debug: keys present en calculo_arboles
    logger.debug(f"Generando Árboles - keys disponibles: {list(calculo_arboles.keys())}")

    # Preferencia: df_resumen_html (stringified JSON). Fallback: df_cargas_completo (dict saved form)
    if calculo_arboles.get('df_resumen_html'):
        try:
            df = pd.read_json(StringIO(calculo_arboles['df_resumen_html']), orient='split')
            logger.debug(f"Arboles - df_resumen_html rows={len(df)} cols={len(df.columns)} columns={list(df.columns)} head={df.head(2).to_dict(orient='records')}")
            html.append('<h5>Resumen de Cargas por Hipótesis</h5>')
            html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm'))
        except Exception as e:
            logger.exception(f"Error parseando df_resumen_html en Árboles: {e}")
            html.append('<div class="alert alert-warning">Error al cargar resumen de cargas.</div>')
    elif calculo_arboles.get('df_cargas_completo'):
        # df_cargas_completo is stored as a dict (from DataFrame.to_dict or custom structure)
        try:
            df_dict = calculo_arboles['df_cargas_completo']
            # Reconstruct DataFrame similar to UI: support 'columns' + 'column_codes' format
            if isinstance(df_dict, dict) and 'columns' in df_dict and 'column_codes' in df_dict:
                arrays = []
                for level_idx in range(len(df_dict['columns'])):
                    level_values = df_dict['columns'][level_idx]
                    codes = df_dict['column_codes'][level_idx]
                    arrays.append([level_values[code] for code in codes])
                multi_idx = pd.MultiIndex.from_arrays(arrays)
                try:
                    # No label on second level (remove 'Componente' header to match UI)
                    multi_idx.names = ['Hipótesis', None]
                except Exception:
                    pass
                df = pd.DataFrame(df_dict.get('data', []), columns=multi_idx)
            else:
                # Try to load as orient='split' JSON if dict-like
                df = pd.read_json(pd.io.json.dumps(df_dict), orient='split')
            df = df.round(2)
            html.append('<h5> Cargas Aplicadas por Nodo</h5>')
            html.append('<div class="table-responsive small-table">')
            html.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm'))
            html.append('</div>')
        except Exception as e:
            logger.exception(f"Error reconstruyendo df_cargas_completo en Árboles: {e}")
            html.append('<div class="alert alert-warning">Error al cargar tabla de cargas por nodo.</div>')
    else:
        logger.debug("Arboles - No se encontró 'df_resumen_html' ni 'df_cargas_completo' en calculo_arboles")

    imagenes = calculo_arboles.get('imagenes', [])
    logger.debug(f"Arboles - imágenes detectadas: count={len(imagenes)} preview={[ (i if isinstance(i,str) else i.get('nombre')) for i in imagenes][:10]}")

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
                    logger.debug(f"Arboles - imagen cargada: {img_nombre} (titulo={titulo})")
                else:
                    logger.debug(f"Arboles - imagen faltante en cache: {img_nombre}")

        html.append('</div>')

    return '\n'.join(html)


def generar_seccion_sph(calculo_sph):
    """Genera HTML para sección SPH"""
    html = ['<h3>5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)</h3>']
    
    resultados = calculo_sph.get('resultados', {})
    desarrollo_texto = calculo_sph.get('desarrollo_texto', '')
    
    if resultados:
        logger.debug(f"Generando SPH (config: {resultados.get('config_seleccionada')})")
        config_seleccionada = resultados.get('config_seleccionada', 'N/A')
        dimensiones = resultados.get('dimensiones', {})
        Rc_adopt = resultados.get('Rc_adopt', None)
        
        # Determinar número de postes
        n_postes = 1 if "Monoposte" in config_seleccionada else 2 if "Biposte" in config_seleccionada else 3
        
        html.append('<div class="alert alert-success">')
        html.append('<h5>Cálculo Completado</h5>')
        html.append('<hr>')
        html.append(f'<p><strong>Configuración:</strong> {config_seleccionada}<br>')
        ht = _safe_format(dimensiones.get("Ht_comercial"), ".1f", name="sph.Ht_comercial")
        rc = _safe_format(Rc_adopt, ".0f", name="sph.Rc_adopt")
        hl = _safe_format(dimensiones.get("Hl"), ".2f", name="sph.Hl")
        he = _safe_format(dimensiones.get("He_final"), ".2f", name="sph.He_final")
        html.append(f'<strong>Código:</strong> {n_postes} x {ht}m / Ro {rc}daN<br>')
        html.append(f'<strong>Altura libre:</strong> {hl} m<br>')
        html.append(f'<strong>Empotramiento:</strong> {he} m<br>')
        html.append(f'<strong>Resistencia en cima:</strong> {rc} daN</p>')
        html.append('</div>')
    
    if desarrollo_texto:
        html.append('<hr><h5>Desarrollo Completo</h5>')
        html.append(f'<pre>{desarrollo_texto}</pre>')
    
    if not resultados and not desarrollo_texto:
        html.append('<p>No hay resultados de SPH disponibles.</p>')
    
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
    # Intentar cargar logo embebido (logo_distrocuyo.png)
    try:
        logo_b64 = ViewHelpers.cargar_imagen_base64('logo_distrocuyo.png')
        if logo_b64:
            logo_html = f'<img id="logo_distrocuyo" src="data:image/png;base64,{logo_b64}" alt="logo" draggable="false" style="position:absolute; top:20px; right:30px; height:50px; width:auto; pointer-events:none; user-select:none; -webkit-user-drag:none;">'
        else:
            logo_html = ''
    except Exception:
        logo_html = ''

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
        .container-fluid {{ position: relative; max-width: 1400px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        /* logo image is absolutely positioned within the container and is non-interactive */
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


def generar_html_familia(nombre_familia, resultados_familia, checklist_activo=None):
    """Genera HTML completo para familia de estructuras - usa implementación completa"""
    return generar_html_familia_completo(nombre_familia, resultados_familia, checklist_activo)


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
                formatted = _safe_format(valor, ".2f", name=f"fund.{campo}")
                html.append(f'<tr><td>{campo}</td><td>{formatted}</td></tr>')
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




def generar_seccion_aee(calculo_aee, estructura_actual):
    """Genera HTML para seccion AEE"""
    html = ['<h3>8. ANALISIS ESTATICO DE ESFUERZOS (AEE)</h3>']
    
    resultados = calculo_aee.get('resultados', {})
    hash_params = calculo_aee.get('hash_parametros')
    
    # Resumen Comparativo
    if resultados.get('resumen_comparativo'):
        df_dict = resultados['resumen_comparativo']
        df_resumen = pd.DataFrame(df_dict['data'], columns=df_dict['columns'])
        html.append('<h5>Resumen Comparativo - Maximos por Conexion</h5>')
        html.append(df_resumen.to_html(classes='table table-striped table-bordered table-hover table-sm', index=False))
    
    # Tablas de nodos
    if resultados.get('nodos_info'):
        nodos_data = []
        for nombre, info in resultados['nodos_info'].items():
            x = _safe_format(info.get('x'), ".2f", name=f"aee.nodo.{nombre}.x")
            y = _safe_format(info.get('y'), ".2f", name=f"aee.nodo.{nombre}.y")
            z = _safe_format(info.get('z'), ".2f", name=f"aee.nodo.{nombre}.z")
            nodos_data.append({
                'Nodo': nombre,
                'X [m]': x,
                'Y [m]': y,
                'Z [m]': z,
                'Tipo': info.get('tipo')
            })
        df_nodos = pd.DataFrame(nodos_data)
        html.append('<h5>Nodos de la Estructura</h5>')
        html.append(df_nodos.to_html(classes='table table-striped table-bordered table-sm', index=False))
    
    # Tabla de reacciones
    if resultados.get('df_reacciones'):
        df_dict = resultados['df_reacciones']
        df_reacciones = pd.DataFrame(df_dict['data'], columns=df_dict['columns'], index=df_dict['index'])
        html.append('<h5>Reacciones en Base por Hipotesis</h5>')
        html.append(df_reacciones.to_html(classes='table table-striped table-bordered table-sm'))
    
    # Diagramas (PNG)
    diagramas = resultados.get('diagramas', {})
    if diagramas and hash_params:
        html.append('<h5>Diagramas de Esfuerzos</h5>')
        for nombre_diagrama in diagramas.keys():
            img_filename = f"AEE_{nombre_diagrama}.{hash_params}.png"
            img_str = ViewHelpers.cargar_imagen_base64(img_filename)
            if img_str:
                html.append(f'<h6>{nombre_diagrama.replace("_", " ")}</h6>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="{nombre_diagrama}">')
    
    return '\n'.join(html)
