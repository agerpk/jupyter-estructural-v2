from datetime import datetime
import logging
from pathlib import Path
from config.app_config import CACHE_DIR
from utils.descargar_html_familia_fix import generar_seccion_costeo_estructura
from utils.view_helpers import ViewHelpers

logger = logging.getLogger(__name__)

def _safe_format(value, fmt=None, default="N/A", name=None):
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

def generar_indice_familia(nombre_familia, resultados_familia, checklist_activo=None):
    """Genera índice con hyperlinks y subentradas por sección
    
    Args:
        nombre_familia: Nombre de la familia
        resultados_familia: Resultados de cálculos
        checklist_activo: Dict con secciones activas por estructura.
            Puede ser un dict global ("cmc": True, ...) o un mapping por estructura:
            {"Estr.1": {"cmc": True, "dge.dimensiones": True, ...}, ...}
    """
    html = ['<div class="indice"><h3>Índice</h3><ul>']
    html.append('<li><a href="#resumen">Resumen de Familia</a></li>')
    
    estructuras = resultados_familia.get("resultados_estructuras", {})
    for nombre_estr, datos_estr in estructuras.items():
        titulo = datos_estr.get("titulo", nombre_estr)
        titulo_id = titulo.replace(" ", "_").replace("/", "_")
        titulo_label = f"Estructura: {titulo}"
        # Link opens the accordion collapse for the structure (show label as 'Estructura: TITULO')
        html.append(f'<li><a href="#collapse_{titulo_id}" data-bs-toggle="collapse" data-bs-target="#collapse_{titulo_id}">Estructura: {titulo}</a>')
        
        # Subentradas por sección (solo si están en checklist)
        if "error" not in datos_estr:
            resultados = datos_estr.get("resultados", {})
            html.append('<ul>')
            
            # Determinar checklist local: si checklist_activo es mapping por estructura, usarlo, si no, usar checklist_activo directamente
            local_check = None
            if isinstance(checklist_activo, dict) and checklist_activo:
                # mapping por estructura?
                if any(isinstance(v, dict) for v in checklist_activo.values()):
                    local_check = checklist_activo.get(nombre_estr, {})
                else:
                    local_check = checklist_activo
            else:
                local_check = None

            # Si hay checklist, verificar cada sección; si no hay checklist, incluir todo
            if local_check:
                # CMC
                if local_check.get("cmc") and "cmc" in resultados and resultados["cmc"]:
                    html.append(f'<li><a href="#' + f"{titulo_id}_cmc_collapse" + '" data-bs-toggle="collapse" data-bs-target="#' + f"{titulo_id}_cmc_collapse" + '">1. Cálculo Mecánico de Cables</a></li>')
                # DGE (y subentradas)
                if (local_check.get("dge") or local_check.get("dge.dimensiones") or local_check.get("dge.nodos") or local_check.get("dge.diagramas") or local_check.get("dge.plscadd")) and "dge" in resultados and resultados["dge"]:
                    dge = resultados["dge"]
                    plscadd = dge.get('plscadd_csv')
                    if not plscadd:
                        hashp = dge.get('hash_parametros')
                        if hashp:
                            matches = list(Path(CACHE_DIR).glob(f"*{hashp}*.csv"))
                            if matches:
                                plscadd = matches[0].name

                    html.append(f'<li><a href="#{titulo_id}_dge_collapse" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_dge_collapse">2. Diseño Geométrico</a>')
                    # Sublista con las subsecciones seleccionadas
                    html.append('<ul>')
                    if local_check.get('dge.dimensiones') and dge.get('dimensiones'):
                        html.append(f'<li><a href="#{titulo_id}_dge_dimensiones">Dimensiones de Estructura</a></li>')
                    if local_check.get('dge.nodos') and dge.get('nodes_key'):
                        html.append(f'<li><a href="#{titulo_id}_dge_nodos">Nodos Estructurales</a></li>')
                    # Diagramas: separar en 3 entradas
                    if local_check.get('dge.diagramas') and dge.get('hash_parametros'):
                        html.append(f'<li><a href="#{titulo_id}_dge_graf_estructura">Gráfico de Estructura</a></li>')
                        html.append(f'<li><a href="#{titulo_id}_dge_graf_cabezal">Gráfico de Cabezal</a></li>')
                        html.append(f'<li><a href="#{titulo_id}_dge_graf_nodos">Gráfico 3D de Nodos y Coordenadas</a></li>')
                    if plscadd and local_check.get('dge.plscadd'):
                        html.append(f'<li><a href="#{titulo_id}_dge_plscadd">Tabla PLS-CADD</a></li>')
                    html.append('</ul>')
                    html.append('</li>')
                # DME
                if local_check.get("dme") and "dme" in resultados and resultados["dme"]:
                    html.append(f'<li><a href="#' + f"{titulo_id}_dme_collapse" + '" data-bs-toggle="collapse" data-bs-target="#' + f"{titulo_id}_dme_collapse" + '">3. Diseño Mecánico</a></li>')
                # Árboles
                if local_check.get("arboles") and "arboles" in resultados and resultados["arboles"]:
                    html.append(f'<li><a href="#' + f"{titulo_id}_arboles_collapse" + '" data-bs-toggle="collapse" data-bs-target="#' + f"{titulo_id}_arboles_collapse" + '">4. Árboles de Carga</a></li>')
                # SPH
                if local_check.get("sph") and "sph" in resultados and resultados["sph"]:
                    html.append(f'<li><a href="#' + f"{titulo_id}_sph_collapse" + '" data-bs-toggle="collapse" data-bs-target="#' + f"{titulo_id}_sph_collapse" + '">5. Selección de Poste</a></li>')
                # Fundación
                if local_check.get("fundacion") and "fundacion" in resultados and resultados["fundacion"]:
                    html.append(f'<li><a href="#' + f"{titulo_id}_fundacion_collapse" + '" data-bs-toggle="collapse" data-bs-target="#' + f"{titulo_id}_fundacion_collapse" + '">6. Fundación</a></li>')
                # AEE
                if local_check.get("aee") and "aee" in resultados and resultados["aee"]:
                    html.append(f'<li><a href="#' + f"{titulo_id}_aee_collapse" + '" data-bs-toggle="collapse" data-bs-target="#' + f"{titulo_id}_aee_collapse" + '">7. Análisis Estático</a></li>')
                # Costeo por estructura
                if local_check.get("costeo") and "costeo" in resultados and resultados["costeo"]:
                    html.append(f'<li><a href="#' + f"{titulo_id}_costeo_collapse" + '" data-bs-toggle="collapse" data-bs-target="#' + f"{titulo_id}_costeo_collapse" + '">8. Costeo</a></li>')
            else:
                # Sin checklist, incluir todo lo que tenga datos
                if "cmc" in resultados and resultados["cmc"]:
                    html.append(f'<li><a href="#${titulo_id}_cmc_collapse" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_cmc_collapse">1. Cálculo Mecánico de Cables</a></li>'.replace('$',''))
                if "dge" in resultados and resultados["dge"]:
                    dge = resultados["dge"]
                    plscadd = dge.get('plscadd_csv')
                    if not plscadd:
                        hashp = dge.get('hash_parametros')
                        if hashp:
                            matches = list(Path(CACHE_DIR).glob(f"*{hashp}*.csv"))
                            if matches:
                                plscadd = matches[0].name
                    html.append(f'<li><a href="#' + f"{titulo_id}_dge_collapse" + '" data-bs-toggle="collapse" data-bs-target="#' + f"{titulo_id}_dge_collapse" + '">2. Diseño Geométrico</a>')
                    html.append('<ul>')
                    if dge.get('dimensiones'):
                        html.append(f'<li><a href="#' + f"{titulo_id}_dge_dimensiones" + '">Dimensiones de Estructura</a></li>')
                    if dge.get('nodes_key'):
                        html.append(f'<li><a href="#' + f"{titulo_id}_dge_nodos" + '">Nodos Estructurales</a></li>')
                    if dge.get('hash_parametros'):
                        html.append(f'<li><a href="#' + f"{titulo_id}_dge_graf_estructura" + '">GRAFICO DE ESTRUCTURA</a></li>')
                        html.append(f'<li><a href="#' + f"{titulo_id}_dge_graf_cabezal" + '">GRAFICO DE CABEZAL</a></li>')
                        html.append(f'<li><a href="#' + f"{titulo_id}_dge_graf_nodos" + '">GRAFICO 3D DE NODOS Y COORDENADAS</a></li>')
                    if plscadd:
                        html.append(f'<li><a href="#' + f"{titulo_id}_dge_plscadd" + '">Tabla PLS-CADD</a></li>')
                    html.append('</ul>')
                    html.append('</li>')
                if "dme" in resultados and resultados["dme"]:
                    dme = resultados.get('dme')
                    html.append(f'<li><a href="#{titulo_id}_dme_collapse">3. Diseño Mecánico</a>')
                    html.append('<ul>')
                    if dme and (dme.get('resumen_ejecutivo') or dme.get('resumen') or dme.get('texto_resumen') or dme.get('resumen_html')):
                        html.append(f'<li><a href="#{titulo_id}_dme_resumen">Resumen Ejecutivo</a></li>')
                    if dme and dme.get('df_reacciones_html'):
                        html.append(f'<li><a href="#{titulo_id}_dme_tabla_reacciones">Tabla Resumen de Reacciones y Tiros</a></li>')
                    if dme and dme.get('hash_parametros'):
                        html.append(f'<li><a href="#{titulo_id}_dme_polar">Diagrama Polar de Tiros</a></li>')
                        html.append(f'<li><a href="#{titulo_id}_dme_barras">Diagrama de Barras</a></li>')
                    html.append('</ul>')
                    html.append('</li>')
                if "arboles" in resultados and resultados["arboles"]:
                    html.append(f'<li><a href="#${titulo_id}_arboles_collapse" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_arboles_collapse">4. Árboles de Carga</a></li>'.replace('$',''))
                if "sph" in resultados and resultados["sph"]:
                    html.append(f'<li><a href="#${titulo_id}_sph_collapse" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_sph_collapse">5. Selección de Poste</a></li>'.replace('$',''))
                if "fundacion" in resultados and resultados["fundacion"]:
                    html.append(f'<li><a href="#${titulo_id}_fundacion_collapse" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_fundacion_collapse">6. Fundación</a></li>'.replace('$',''))
                if "aee" in resultados and resultados["aee"]:
                    html.append(f'<li><a href="#${titulo_id}_aee_collapse" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_aee_collapse">7. Análisis Estático</a></li>'.replace('$',''))
                if "costeo" in resultados and resultados["costeo"]:
                    html.append(f'<li><a href="#${titulo_id}_costeo_collapse" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_costeo_collapse">8. Costeo</a></li>'.replace('$',''))
            
            html.append('</ul>')
        html.append('</li>')
    
    # Costeo Global solo si está en checklist o no hay checklist
    if not checklist_activo or checklist_activo.get("costeo"):
        html.append('<li><a href="#collapse_costeo_global">Costeo Global</a></li>')
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
    
    logger.debug(f"Generando HTML familia='{nombre_familia}' con {len(resultados_familia.get('resultados_estructuras', {}))} estructuras, checklist={checklist_activo}")

    # Intentar cargar logo embebido (logo_distrocuyo.png) si existe en cache/assets
    try:
        logo_b64 = ViewHelpers.cargar_imagen_base64('logo_distrocuyo.png')
        if logo_b64:
            # Inline logo placed before the main header; not fixed
            logo_html = f'<img id="logo_distrocuyo" src="data:image/png;base64,{logo_b64}" alt="logo" draggable="false" style="height:50px; width:auto; margin-right:12px; vertical-align: middle; -webkit-user-drag:none;">'
        else:
            logo_html = ''
    except Exception as e:
        logger.debug(f"Logo no encontrado o error cargando logo: {e}")
        logo_html = ''

    indice = generar_indice_familia(nombre_familia, resultados_familia, checklist_activo)
    secciones = [indice]
    secciones.append(generar_seccion_resumen_familia(nombre_familia, resultados_familia))
    
    estructuras = resultados_familia.get("resultados_estructuras", {})
    familia_safe = nombre_familia.replace(' ', '_').replace('/', '_')
    if estructuras:
        secciones.append(f'<div class="accordion" id="accordion_{familia_safe}">')

    # Construir el contenido final e insertar logo si existe (logo_html)
    contenido_html = "\n".join(secciones)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
... (template continues below, no change here)
"""

    for nombre_estr, datos_estr in estructuras.items():
        titulo = datos_estr.get("titulo", nombre_estr)
        titulo_id = titulo.replace(" ", "_").replace("/", "_")
        # Accordion item por estructura
        secciones.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}">
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_{titulo_id}" aria-expanded="true" aria-controls="collapse_{titulo_id}">
      Estructura: {titulo}
    </button>
  </h2>
  <div id="collapse_{titulo_id}" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}">
    <div class="accordion-body">''')

        if "error" in datos_estr:
            secciones.append(f'<div class="alert alert-danger">Error: {datos_estr["error"]}</div>')
        else:
            try:
                logger.debug(f"Generando secciones para estructura: {titulo} (id: {titulo_id})")
                secciones.append(generar_seccion_estructura_familia(datos_estr, titulo_id, checklist_activo))
            except Exception as e:
                import traceback
                logger.exception(f"Error generando secciones para estructura {titulo}: {e}\n{traceback.format_exc()}")
                secciones.append(f'<div class="alert alert-danger">Error generando secciones de {titulo}: {e}</div>')

        secciones.append('</div></div></div>')

    if estructuras:
        secciones.append('</div>')
    
    costeo_global = resultados_familia.get("costeo_global", {})
    if costeo_global and (checklist_activo is None or checklist_activo.get("costeo", True)):
        secciones.append(generar_seccion_costeo_familia(costeo_global, estructuras))
        logger.debug(f"Se agregó sección Costeo Global para familia '{nombre_familia}' con {len(estructuras)} estructuras")
    
    contenido_html = "\n".join(secciones)
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Familia - {nombre_familia}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {{
            --color-blue: #0a4a94;
            --color-green: #27a42f;
            --accent: var(--color-blue);
            --accent-alt: var(--color-green);
        }}
        body {{ padding: 20px; font-family: Arial, sans-serif; background-color: #f8f9fa; color: #212529; }}
        .container-fluid {{ position: relative; max-width: 1400px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 4px 12px rgba(10,74,148,0.06); border-top: 6px solid var(--accent); }}
        /* logo image is absolutely positioned within the container and is non-interactive */
        h1 {{ color: var(--accent); border-bottom: 3px solid var(--accent); padding-bottom: 10px; }}
        h2 {{ color: var(--accent-alt); margin-top: 40px; }}
        h3 {{ color: var(--accent); margin-top: 30px; border-bottom: 2px solid var(--accent); padding-bottom: 8px; }}
        h4 {{ color: #6c757d; margin-top: 20px; }}
        h5 {{ color: #adb5bd; margin-top: 15px; }}
        table {{ margin: 20px 0; font-size: 0.9em; border-collapse: separate; border-spacing: 0; }}
        table th {{ background-color: rgba(10,74,148,0.06); color: var(--accent); font-weight: 700; border-bottom: 2px solid rgba(10,74,148,0.08); }}
        pre {{ background-color: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; border: 1px solid rgba(0,0,0,0.08); }}
        .alert {{ margin: 20px 0; padding: 15px; border-radius: 5px; }}
        .alert-success {{ background-color: rgba(39,164,47,0.08); border: 1px solid rgba(39,164,47,0.14); color: var(--accent-alt); }}
        .indice {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .indice ul {{ list-style: none; padding-left: 0; }}
        .indice ul ul {{ padding-left: 25px; margin-top: 5px; }}
        .indice li {{ margin: 8px 0; }}
        .indice a {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
        .indice a:hover {{ text-decoration: underline; color: var(--accent-alt); }}
        .timestamp {{ color: rgba(0,0,0,0.5); font-size: 0.9em; margin-bottom: 30px; }}
        .grid-2col {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 20px; margin: 20px 0; }}
        .grid-2col img {{ width: 100%; height: auto; }}
        /* Smaller table style for wide tables like Árboles de Carga */
        .small-table table {{ font-size: 0.86rem; }}
        .table-responsive {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }} 
        /* Accent helper classes */
        .accent {{ color: var(--accent); font-weight: 700; }}
        .accent-alt {{ color: var(--accent-alt); font-weight: 700; }}
        .accent-bar {{ background: linear-gradient(90deg, var(--accent), var(--accent-alt)); height: 6px; border-radius: 4px; display:block; margin: 8px 0; }}

        /* Accordion buttons: bold, white text, blue (collapsed) -> green (expanded) */
        .accordion-button {{ font-weight: 700; color: #fff !important; background-color: var(--accent) !important; border: none; transition: background-color 0.22s ease, color 0.22s ease; }}
        .accordion-button:focus {{ box-shadow: none; }}
        .accordion-button::after {{ filter: invert(1); }}
        /* When expanded (not .collapsed), use green */
        .accordion-button:not(.collapsed) {{ background-color: var(--accent-alt) !important; color: #fff !important; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1>{logo_html} Familia de Estructuras - {nombre_familia}</h1>
        <p class="timestamp">Generado: {timestamp}</p>
        <hr>
        {contenido_html}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
    // Index click: open necessary collapses (if any) and scroll to the target header/element with offset
    document.addEventListener('DOMContentLoaded', function(){{
      var index = document.querySelector('.indice');
      if(!index) return;
      index.addEventListener('click', function(ev){{
        var link = ev.target.closest && ev.target.closest('a');
        if(!link) return;
        if(!link.closest('.indice')) return;
        var href = link.getAttribute('href') || link.getAttribute('data-bs-target');
        if(!href || !href.startsWith('#')) return;
        ev.preventDefault();
        ev.stopPropagation(); // prevent Bootstrap default toggle handlers so we control showing

        var id = href.substring(1);
        var headerBtn = document.querySelector('[aria-controls="' + id + '"]');
        var targetEl = document.getElementById(id) || document.querySelector(href) || headerBtn;
        if(!targetEl) return;

        // Collect ancester collapses that need to be opened (outermost first)
        var ancestors = [];
        try {{
          var node = targetEl;
          while(node){{
            var parentCollapse = node.closest && node.closest('.accordion-collapse');
            if(parentCollapse && ancestors.indexOf(parentCollapse) === -1){{
              ancestors.push(parentCollapse);
              node = parentCollapse.parentElement;
            }} else {{
              break;
            }}
          }}
        }} catch(e){{ console && console.debug && console.debug('Error collecting ancestor collapses', e); }}

        ancestors.reverse();

        var offset = 80; // space for header/logo
        var scrollToTarget = function(){{
          try{{
            var btn = document.querySelector('[aria-controls="' + id + '"]');
            var scrollEl = btn || targetEl;
            var top = scrollEl.getBoundingClientRect().top + window.scrollY - offset;
            window.scrollTo({{ top: top, behavior: 'smooth' }});
          }}catch(e){{}}
        }};

        var openSequential = function(idx){{
          if(idx >= ancestors.length){{
            // Ensure target collapse is shown if it's a collapse element
            var targetCollapse = document.getElementById(id);
            if(targetCollapse && targetCollapse.classList && !targetCollapse.classList.contains('show')){{
              var inst = bootstrap.Collapse.getOrCreateInstance(targetCollapse);
              var onShown = function(){{
                targetCollapse.removeEventListener('shown.bs.collapse', onShown);
                scrollToTarget();
              }};
              targetCollapse.addEventListener('shown.bs.collapse', onShown);
              inst.show();
            }} else {{
              // Nothing to open, just scroll
              scrollToTarget();
            }}
            return;
          }}

          var parentEl = ancestors[idx];
          try{{
            if(parentEl.classList && parentEl.classList.contains('show')){{
              openSequential(idx+1);
              return;
            }}
          }}catch(e){{}}

          var inst = bootstrap.Collapse.getOrCreateInstance(parentEl);
          var onShownParent = function(){{
            parentEl.removeEventListener('shown.bs.collapse', onShownParent);
            openSequential(idx+1);
          }};
          parentEl.addEventListener('shown.bs.collapse', onShownParent);
          inst.show();
        }};

        if(ancestors.length){{
          openSequential(0);
        }} else {{
          // No ancestors, just ensure target collapse is open or scroll immediately
          var targetCollapse = document.getElementById(id);
          if(targetCollapse && targetCollapse.classList && !targetCollapse.classList.contains('show')){{
            var inst2 = bootstrap.Collapse.getOrCreateInstance(targetCollapse);
            var onShown2 = function(){{
              targetCollapse.removeEventListener('shown.bs.collapse', onShown2);
              scrollToTarget();
            }};
            targetCollapse.addEventListener('shown.bs.collapse', onShown2);
            inst2.show();
          }} else {{
            scrollToTarget();
          }}
        }}
      }}, false);
    }});
    </script>
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
        costo_global = costeo_global.get("costo_global", None)
        cg = _safe_format(costo_global, ",.2f", name="costeo_global.costo_global")
        html.append(f'<tr><td><strong>Costo Global</strong></td><td>{cg} UM</td></tr>')
    
    html.append('</table>')
    
    html.append('<h4>Estructuras en la Familia</h4>')
    html.append('<table class="table table-striped table-bordered">')
    html.append('<thead><tr><th>Estructura</th><th>Título</th><th>Cantidad</th><th>Costo Individual</th><th>Costo Parcial</th></tr></thead>')
    html.append('<tbody>')
    
    for nombre_estr, datos_estr in estructuras.items():
        titulo = datos_estr.get("titulo", nombre_estr)
        cantidad = datos_estr.get("cantidad", 1)
        costo_ind = datos_estr.get("costo_individual", None)
        costo_parc = (costo_ind or 0) * cantidad
        
        costo_ind_str = _safe_format(costo_ind, ",.2f", name=f"estructura.{nombre_estr}.costo_individual")
        costo_parc_str = _safe_format(costo_parc, ",.2f", name=f"estructura.{nombre_estr}.costo_parcial")
        
        html.append(f'<tr><td>{nombre_estr}</td><td>{titulo}</td><td>{cantidad}</td>')
        html.append(f'<td>{costo_ind_str} UM</td><td>{costo_parc_str} UM</td></tr>')
    
    html.append('</tbody></table>')
    return '\n'.join(html)


def generar_seccion_estructura_familia(datos_estructura, titulo_id, checklist_activo=None):
    """Genera HTML para estructura dentro de familia con IDs para navegación
    
    Args:
        datos_estructura: Datos de la estructura
        titulo_id: ID para navegación
        checklist_activo: Dict con secciones activas {"cmc": True, "dge": True, ...}
    """
    from utils.descargar_html import generar_seccion_cmc, generar_seccion_dge, generar_seccion_dme, generar_seccion_arboles, generar_seccion_sph, generar_seccion_fund, generar_seccion_aee
    
    html = []
    resultados = datos_estructura.get("resultados", {})
    estructura_actual = datos_estructura.get("estructura", {})
    
    # Si no hay checklist, incluir todo lo que tenga datos
    if checklist_activo is None:
        checklist_activo = {k: True for k in resultados.keys()}

    inner_acc = f"accordion_{titulo_id}_sub"
    html.append(f'<div class="accordion" id="{inner_acc}">')

    # 1. CMC
    if checklist_activo.get("cmc") and "cmc" in resultados and resultados["cmc"]:
        html.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}_cmc">
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_cmc_collapse" aria-expanded="true" aria-controls="{titulo_id}_cmc_collapse">
      1. Cálculo Mecánico de Cables
    </button>
  </h2>
  <div id="{titulo_id}_cmc_collapse" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}_cmc">
    <div class="accordion-body">''')
        html.append(generar_seccion_cmc(resultados["cmc"]))
        html.append('</div></div></div>')

    # 2. DGE
    if checklist_activo.get("dge") and "dge" in resultados and resultados["dge"]:
        html.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}_dge">
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_dge_collapse" aria-expanded="true" aria-controls="{titulo_id}_dge_collapse">
      2. Diseño Geométrico
    </button>
  </h2>
  <div id="{titulo_id}_dge_collapse" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}_dge">
    <div class="accordion-body">''')
        html.append(generar_seccion_dge(resultados["dge"], id_prefix=titulo_id))

        # Agregar subsección Tabla PLS-CADD al final de DGE si existe
        try:
            dge_calc = resultados["dge"]
            plscadd = dge_calc.get('plscadd_csv')
            if not plscadd:
                hashp = dge_calc.get('hash_parametros')
                if hashp:
                    matches = list(Path(CACHE_DIR).glob(f"*{hashp}*.csv"))
                    if matches:
                        plscadd = matches[0].name
        except Exception:
            plscadd = None

        if plscadd:
            # Inserta un sub-acordeón para la tabla PLS-CADD
            html.append(f'''<div class="accordion" id="{titulo_id}_dge_plscadd_acc">
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading_{titulo_id}_dge_plscadd">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#%s" aria-expanded="true" aria-controls="%s">
        Tabla PLS-CADD
      </button>
    </h2>
    <div id="{titulo_id}_dge_plscadd" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}_dge_plscadd">
      <div class="accordion-body">''')

            # Intentar cargar y renderizar el CSV (skip rows si hay metadatos)
            try:
                from pathlib import Path as _P
                import pandas as _pd
                csv_path = _P(CACHE_DIR) / plscadd
                if csv_path.exists():
                    lines = csv_path.read_text(encoding='utf-8').splitlines()
                    header_idx = 0
                    for i, line in enumerate(lines[:30]):
                        if line.strip().startswith('Set #') or 'Set #' in line:
                            header_idx = i
                            break

                    # Parse and render metadata lines (lines before header)
                    try:
                        import csv as _csv
                        from io import StringIO as _StringIO
                        meta_lines = lines[:header_idx] if header_idx > 0 else []
                        meta_rows = []
                        if meta_lines:
                            reader = _csv.reader(_StringIO('\n'.join(meta_lines)))
                            for r in reader:
                                # Ignore fully empty rows
                                if any((cell or '').strip() for cell in r):
                                    meta_rows.append(r)
                        if meta_rows:
                            html.append('<h6>Información de Estructura</h6>')
                            html.append('<table class="table table-sm table-borderless">')
                            for row in meta_rows:
                                if len(row) == 1:
                                    html.append(f'<tr><td colspan="2"><strong>{row[0]}</strong></td></tr>')
                                else:
                                    key = row[0]
                                    val = row[1] if len(row) > 1 else ''
                                    html.append(f'<tr><td><strong>{key}</strong></td><td>{val}</td></tr>')
                            html.append('</table>')
                    except Exception as e:
                        logger.exception(f"Error parseando metadata PLS-CADD: {e}")

                    # Leer la tabla principal saltando las filas de metadatos
                    if header_idx > 0:
                        df_pls = _pd.read_csv(csv_path, skiprows=header_idx)
                    else:
                        df_pls = _pd.read_csv(csv_path)

                    html.append('<div class="table-responsive">')
                    html.append(df_pls.to_html(classes='table table-striped table-bordered table-sm', index=False))
                    html.append('</div>')
                else:
                    html.append(f'<div class="alert alert-warning">CSV PLS-CADD no encontrado en cache: {plscadd}</div>')
            except Exception as e:
                logger.exception(f"Error mostrando CSV PLS-CADD en familia DGE: {e}")
                html.append(f'<div class="alert alert-warning">No se pudo mostrar preview CSV PLS-CADD: {e}</div>')

            html.append('</div></div></div>')

        html.append('</div></div></div>')

    # 3. DME
    if checklist_activo.get("dme") and "dme" in resultados and resultados["dme"]:
        html.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}_dme">
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_dme_collapse" aria-expanded="true" aria-controls="{titulo_id}_dme_collapse">
      3. Diseño Mecánico
    </button>
  </h2>
  <div id="{titulo_id}_dme_collapse" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}_dme">
    <div class="accordion-body">''')
        html.append(generar_seccion_dme(resultados["dme"], id_prefix=titulo_id))
        html.append('</div></div></div>')

    # 4. Árboles
    if checklist_activo.get("arboles") and "arboles" in resultados and resultados["arboles"]:
        html.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}_arboles">
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_arboles_collapse" aria-expanded="true" aria-controls="{titulo_id}_arboles_collapse">
      4. Árboles de Carga
    </button>
  </h2>
  <div id="{titulo_id}_arboles_collapse" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}_arboles">
    <div class="accordion-body">''')
        html.append(generar_seccion_arboles(resultados["arboles"]))
        html.append('</div></div></div>')

    # 5. SPH
    if checklist_activo.get("sph") and "sph" in resultados and resultados["sph"]:
        html.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}_sph">
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_sph_collapse" aria-expanded="true" aria-controls="# {titulo_id}_sph_collapse">
      5. Selección de Poste
    </button>
  </h2>
  <div id="{titulo_id}_sph_collapse" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}_sph">
    <div class="accordion-body">''')
        html.append(generar_seccion_sph(resultados["sph"]))
        html.append('</div></div></div>')

    # 6. Fundación
    if checklist_activo.get("fundacion") and "fundacion" in resultados and resultados["fundacion"]:
        html.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}_fundacion">
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="# {titulo_id}_fundacion_collapse" aria-expanded="true" aria-controls="{titulo_id}_fundacion_collapse">
      6. Fundación
    </button>
  </h2>
  <div id="{titulo_id}_fundacion_collapse" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}_fundacion">
    <div class="accordion-body">''')
        html.append(generar_seccion_fund(resultados["fundacion"]))
        html.append('</div></div></div>')

    # 7. AEE
    if checklist_activo.get("aee") and "aee" in resultados and resultados["aee"]:
        html.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}_aee">
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#{titulo_id}_aee_collapse" aria-expanded="true" aria-controls="# {titulo_id}_aee_collapse">
      7. Análisis Estático de Esfuerzos
    </button>
  </h2>
  <div id="{titulo_id}_aee_collapse" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}_aee">
    <div class="accordion-body">''')
        html.append(generar_seccion_aee(resultados["aee"], estructura_actual))
        html.append('</div></div></div>')

    # 8. Costeo
    if checklist_activo.get("costeo") and "costeo" in resultados and resultados["costeo"]:
        html.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}_costeo">
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="# {titulo_id}_costeo_collapse" aria-expanded="true" aria-controls="{titulo_id}_costeo_collapse">
      8. Costeo
    </button>
  </h2>
  <div id="{titulo_id}_costeo_collapse" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}_costeo">
    <div class="accordion-body">''')
        html.append(generar_seccion_costeo_estructura(resultados["costeo"]))
        html.append('</div></div></div>')

    html.append('</div>')
    return '\n'.join(html)


def generar_seccion_costeo_familia(costeo_global, estructuras):
    """Genera HTML para costeo global (colapsable)"""
    html = [
        '<div class="accordion" id="accordion_costeo_global">',
        '  <div class="accordion-item">',
        '    <h2 class="accordion-header" id="heading_costeo_global">',
        '      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_costeo_global" aria-expanded="true" aria-controls="collapse_costeo_global">',
        '        COSTEO GLOBAL',
        '      </button>',
        '    </h2>',
        '    <div id="collapse_costeo_global" class="accordion-collapse collapse show" aria-labelledby="heading_costeo_global">',
        '      <div class="accordion-body">'
    ]
    
    costo_global = costeo_global.get("costo_global", None)
    costos_individuales = costeo_global.get("costos_individuales", {})
    costos_parciales = costeo_global.get("costos_parciales", {})
    
    cg = _safe_format(costo_global, ",.2f", name="costeo_global.costo_global")
    html.append(f'<div class="alert alert-success"><h3>Costo Global: {cg} UM</h3></div>')
    
    html.append('<table class="table table-striped table-bordered">')
    html.append('<thead><tr><th>Estructura</th><th>Costo Individual</th><th>Cantidad</th><th>Costo Parcial</th></tr></thead>')
    html.append('<tbody>')
    
    for titulo in sorted(costos_individuales.keys(), key=lambda x: costos_individuales[x], reverse=True):
        costo_ind = costos_individuales[titulo]
        costo_parc = costos_parciales.get(titulo, None)
        
        cantidad = 1
        for nombre_estr, datos_estr in estructuras.items():
            if datos_estr.get("titulo") == titulo:
                cantidad = datos_estr.get("cantidad", 1)
                break
        
        costo_ind_str = _safe_format(costo_ind, ",.2f", name=f"costeo.{titulo}.costo_individual")
        costo_parc_str = _safe_format(costo_parc, ",.2f", name=f"costeo.{titulo}.costo_parcial")
        
        html.append(f'<tr><td>{titulo}</td><td>{costo_ind_str} UM</td>')
        html.append(f'<td>{cantidad}</td><td><strong>{costo_parc_str} UM</strong></td></tr>')
    
    html.append('</tbody></table>')
    html.append('      </div>')
    html.append('    </div>')
    html.append('  </div>')
    html.append('</div>')
    return '\n'.join(html)
