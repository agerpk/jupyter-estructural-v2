"""Generación de HTML personalizado para Familias.

Ofrece:
- listar_secciones_disponibles(nombre_familia, resultados_familia)
- construir_html_personalizado(nombre_familia, resultados_familia, selected_keys) -> str (HTML)

Política: siempre embebemos figuras como base64. No usamos rutas relativas externas.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from utils.descargar_html_familia_completo import generar_seccion_resumen_familia
from utils.descargar_html import _safe_format, generar_seccion_cmc, generar_seccion_dge, generar_seccion_dme, generar_seccion_arboles, generar_seccion_sph, generar_seccion_fund, generar_seccion_aee
from utils.descargar_html_familia_completo import generar_indice_familia
from utils.view_helpers import ViewHelpers

logger = logging.getLogger(__name__)


@dataclass
class SectionDescriptor:
    id: str
    key: str
    label: str
    orden: int
    parent_id: Optional[str] = None
    generator_func_name: Optional[str] = None
    present_flag: bool = True


def _collect_sections_for_structure(nombre_estr: str, datos_estr: Dict[str, Any]) -> List[SectionDescriptor]:
    """Detecta secciones y subsecciones disponibles para una estructura concreta."""
    secciones: List[SectionDescriptor] = []
    resultados = datos_estr.get("resultados", {})
    orden = 1

    # Resumen/Top-level per-structure
    # CMC
    if resultados.get("cmc"):
        secciones.append(SectionDescriptor(id=f"{nombre_estr}_cmc", key=f"{nombre_estr}:cmc", label="CMC - Tablas y resultados", orden=orden, generator_func_name="cmc"))
        orden += 1

    # DGE y sus subsecciones detectables
    if resultados.get("dge"):
        secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge", key=f"{nombre_estr}:dge", label="DGE - Diseño Geométrico (completo)", orden=orden, generator_func_name="dge"))
        orden += 1
        dge = resultados.get("dge") or {}
        # Parámetros / dimensiones
        if dge.get("dimensiones"):
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_dimensiones", key=f"{nombre_estr}:dge.dimensiones", label="DGE: Dimensiones de Estructura", orden=orden, parent_id=f"{nombre_estr}_dge"))
            orden += 1
        # Nodos
        if dge.get("nodes_key"):
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_nodos", key=f"{nombre_estr}:dge.nodos", label="DGE: Nodos Estructurales", orden=orden, parent_id=f"{nombre_estr}_dge"))
            orden += 1
        # Diagramas (estructura/cabezal/nodos)
        hashp = dge.get("hash_parametros")
        if hashp:
            # if any of the expected images exists in cache -> consider diagramas present
            posibles = [f"Estructura.{hashp}.png", f"Cabezal.{hashp}.png", f"Nodos.{hashp}.png"]
            found = any(ViewHelpers.cargar_imagen_base64(n) for n in posibles)
            if found:
                secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_diagramas", key=f"{nombre_estr}:dge.diagramas", label="DGE: Diagramas (Estructura/Cabezal/Nodos)", orden=orden, parent_id=f"{nombre_estr}_dge"))
                orden += 1
        # Servidumbre
        if dge.get("servidumbre"):
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_servidumbre", key=f"{nombre_estr}:dge.servidumbre", label="DGE: Franja de Servidumbre", orden=orden, parent_id=f"{nombre_estr}_dge"))
            orden += 1
        # Memoria de calculo
        if dge.get("memoria_calculo"):
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_memoria", key=f"{nombre_estr}:dge.memoria", label="DGE: Memoria de Cálculo", orden=orden, parent_id=f"{nombre_estr}_dge"))
            orden += 1
        # Tabla PLS-CADD
        plscadd = dge.get('plscadd_csv')
        if not plscadd and hashp:
            # buscar en cache
            # ViewHelpers tiene métodos para listar archivos si se necesita, pero para mantener simple, si plscadd key existe la incluimos
            pass
        if plscadd:
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_plscadd", key=f"{nombre_estr}:dge.plscadd", label="DGE: Tabla PLS-CADD", orden=orden, parent_id=f"{nombre_estr}_dge"))
            orden += 1

    # DME
    if resultados.get("dme"):
        secciones.append(SectionDescriptor(id=f"{nombre_estr}_dme", key=f"{nombre_estr}:dme", label="DME - Diseño Mecánico (completo)", orden=orden, generator_func_name="dme"))
        orden += 1

    # Árboles
    if resultados.get("arboles"):
        secciones.append(SectionDescriptor(id=f"{nombre_estr}_arboles", key=f"{nombre_estr}:arboles", label="Árboles de Carga", orden=orden, generator_func_name="arboles"))
        orden += 1

    # SPH
    if resultados.get("sph"):
        secciones.append(SectionDescriptor(id=f"{nombre_estr}_sph", key=f"{nombre_estr}:sph", label="SPH - Selección de Poste", orden=orden, generator_func_name="sph"))
        orden += 1

    # Fundaciones
    if resultados.get("fundacion"):
        secciones.append(SectionDescriptor(id=f"{nombre_estr}_fund", key=f"{nombre_estr}:fundacion", label="Fundación", orden=orden, generator_func_name="fundacion"))
        orden += 1

    # AEE
    if resultados.get("aee"):
        secciones.append(SectionDescriptor(id=f"{nombre_estr}_aee", key=f"{nombre_estr}:aee", label="AEE - Análisis Estático", orden=orden, generator_func_name="aee"))
        orden += 1

    return secciones


def listar_secciones_disponibles(nombre_familia: str, resultados_familia: Dict[str, Any]) -> List[SectionDescriptor]:
    """Devuelve lista de SectionDescriptor representando secciones y subsecciones disponibles en la familia.

    Esta versión agrupa las subsecciones por tipo (no por estructura), de modo que
    elementos iguales (por ejemplo "DGE: Tabla PLS-CADD") aparecen una sola vez y
    su selección se aplica a todas las estructuras de la familia.

    Args:
        nombre_familia: nombre de la familia
        resultados_familia: dict con los resultados
    """
    # Normalizar entrada a 'estructuras' dict
    estructuras = {}
    if isinstance(resultados_familia, dict):
        if 'resultados_estructuras' in resultados_familia:
            estructuras = resultados_familia.get('resultados_estructuras', {})
        elif 'resultados' in resultados_familia and isinstance(resultados_familia['resultados'], dict):
            estructuras = resultados_familia['resultados'].get('resultados_estructuras', {})
        else:
            estructuras = resultados_familia.get('estructuras', {})

    # Detectar presencia por tipo (merge across structures)
    has = {
        'cmc': False,
        'dge': False,
        'dge.dimensiones': False,
        'dge.nodos': False,
        'dge.diagramas': False,
        'dge.servidumbre': False,
        'dge.memoria': False,
        'dge.plscadd': False,
        'dme': False,
        'arboles': False,
        'sph': False,
        'fundacion': False,
        'aee': False,
    }

    for nombre_estr, datos in estructuras.items():
        resultados = datos.get('resultados', {})
        if 'cmc' in resultados and resultados['cmc']:
            has['cmc'] = True
        if 'dge' in resultados and resultados['dge']:
            has['dge'] = True
            dge = resultados['dge'] or {}
            if dge.get('dimensiones'):
                has['dge.dimensiones'] = True
            if dge.get('nodes_key'):
                has['dge.nodos'] = True
            if dge.get('hash_parametros'):
                # verificar si al menos una de las imagenes existe en cache
                hashp = dge.get('hash_parametros')
                posibles = [f"Estructura.{hashp}.png", f"Cabezal.{hashp}.png", f"Nodos.{hashp}.png"]
                if any(ViewHelpers.cargar_imagen_base64(n) for n in posibles):
                    has['dge.diagramas'] = True
                # Buscar plscadd csv
                if dge.get('plscadd_csv'):
                    has['dge.plscadd'] = True
            if dge.get('servidumbre'):
                has['dge.servidumbre'] = True
            if dge.get('memoria_calculo'):
                has['dge.memoria'] = True
        if 'dme' in resultados and resultados['dme']:
            has['dme'] = True
        if 'arboles' in resultados and resultados['arboles']:
            has['arboles'] = True
        if 'sph' in resultados and resultados['sph']:
            has['sph'] = True
        if 'fundacion' in resultados and resultados['fundacion']:
            has['fundacion'] = True
        if 'aee' in resultados and resultados['aee']:
            has['aee'] = True

    secciones: List[SectionDescriptor] = []
    orden = 1
    # Resumen de familia
    secciones.append(SectionDescriptor(id="familia_resumen", key="familia:resumen", label="Resumen de Familia", orden=orden))
    orden += 1

    # Secciones generales (una sola entrada por tipo)
    if has['cmc']:
        secciones.append(SectionDescriptor(id="cmc", key="cmc", label="CMC - Tablas y resultados", orden=orden))
        orden += 1

    if has['dge']:
        secciones.append(SectionDescriptor(id="dge", key="dge", label="DGE - Diseño Geométrico (completo)", orden=orden))
        orden += 1
        if has['dge.dimensiones']:
            secciones.append(SectionDescriptor(id="dge.dimensiones", key="dge.dimensiones", label="DGE: Dimensiones de Estructura", orden=orden))
            orden += 1
        if has['dge.nodos']:
            secciones.append(SectionDescriptor(id="dge.nodos", key="dge.nodos", label="DGE: Nodos Estructurales", orden=orden))
            orden += 1
        if has['dge.diagramas']:
            secciones.append(SectionDescriptor(id="dge.diagramas", key="dge.diagramas", label="DGE: Diagramas (Estructura/Cabezal/Nodos)", orden=orden))
            orden += 1
        if has['dge.servidumbre']:
            secciones.append(SectionDescriptor(id="dge.servidumbre", key="dge.servidumbre", label="DGE: Franja de Servidumbre", orden=orden))
            orden += 1
        if has['dge.memoria']:
            secciones.append(SectionDescriptor(id="dge.memoria", key="dge.memoria", label="DGE: Memoria de Cálculo", orden=orden))
            orden += 1
        if has['dge.plscadd']:
            secciones.append(SectionDescriptor(id="dge.plscadd", key="dge.plscadd", label="DGE: Tabla PLS-CADD", orden=orden))
            orden += 1

    if has['dme']:
        secciones.append(SectionDescriptor(id="dme", key="dme", label="DME - Diseño Mecánico (completo)", orden=orden))
        orden += 1

    if has['arboles']:
        secciones.append(SectionDescriptor(id="arboles", key="arboles", label="Árboles de Carga", orden=orden))
        orden += 1

    if has['sph']:
        secciones.append(SectionDescriptor(id="sph", key="sph", label="SPH - Selección de Poste", orden=orden))
        orden += 1

    if has['fundacion']:
        secciones.append(SectionDescriptor(id="fundacion", key="fundacion", label="Fundación", orden=orden))
        orden += 1

    if has['aee']:
        secciones.append(SectionDescriptor(id="aee", key="aee", label="AEE - Análisis Estático", orden=orden))
        orden += 1

    # Costeo global
    costeo = None
    if isinstance(resultados_familia, dict):
        costeo = resultados_familia.get('costeo_global') or (resultados_familia.get('resultados') or {}).get('costeo_global')
    if costeo:
        secciones.append(SectionDescriptor(id="familia_costeo", key="familia:costeo", label="Costeo Global", orden=orden))

    return secciones


# --- Helpers para render parcial por sezioni ---

def _render_cmc_parcial(calculo_cmc: Dict[str, Any], include_keys: List[str]) -> str:
    # reutilizar generar_seccion_cmc y filtrar mínima si se requiere
    # Para simplicidad: si cualquier key cmc.* seleccionada -> devolver sección completa
    return generar_seccion_cmc(calculo_cmc)


def _render_dge_parcial(calculo_dge: Dict[str, Any], include_subkeys: List[str]) -> str:
    # Construir DGE seccion por partes según include_subkeys
    html_parts = ['<h3>2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)</h3>']

    if "dimensiones" in include_subkeys and calculo_dge.get("dimensiones"):
        dimensiones = calculo_dge.get('dimensiones', {})
        html_parts.append('<h5>Dimensiones de Estructura</h5>')
        html_parts.append('<table class="table table-bordered params-table">')
        for campo, valor in dimensiones.items():
            if isinstance(valor, (int, float)):
                formatted = _safe_format(valor, ".3f", name=f"dimensiones.{campo}")
                html_parts.append(f'<tr><td>{campo}</td><td>{formatted}</td></tr>')
            else:
                html_parts.append(f'<tr><td>{campo}</td><td>{valor}</td></tr>')
        html_parts.append('</table>')

    if "nodos" in include_subkeys and calculo_dge.get('nodes_key'):
        nodes_key = calculo_dge.get('nodes_key', {})
        html_parts.append('<h5>Nodos Estructurales</h5>')
        html_parts.append('<table class="table table-striped table-bordered table-sm">')
        html_parts.append('<thead><tr><th>Nodo</th><th>X (m)</th><th>Y (m)</th><th>Z (m)</th></tr></thead>')
        html_parts.append('<tbody>')
        for nombre_nodo, coords in nodes_key.items():
            if isinstance(coords, (list, tuple)) and len(coords) >= 3:
                x = _safe_format(coords[0], ".3f", name=f"node.{nombre_nodo}.x")
                y = _safe_format(coords[1], ".3f", name=f"node.{nombre_nodo}.y")
                z = _safe_format(coords[2], ".3f", name=f"node.{nombre_nodo}.z")
                html_parts.append(f'<tr><td><strong>{nombre_nodo}</strong></td><td>{x}</td><td>{y}</td><td>{z}</td></tr>')
        html_parts.append('</tbody></table>')

    # Diagramas (estructura/cabezal/nodos)
    if "diagramas" in include_subkeys and calculo_dge.get('hash_parametros'):
        hash_params = calculo_dge.get('hash_parametros')
        for nombre, titulo in [
            (f"Estructura.{hash_params}.png", "Estructura Completa"),
            (f"Cabezal.{hash_params}.png", "Detalle Cabezal"),
            (f"Nodos.{hash_params}.png", "Nodos y Coordenadas")
        ]:
            img_str = ViewHelpers.cargar_imagen_base64(nombre)
            if img_str:
                html_parts.append(f'<h6>{titulo}</h6>')
                html_parts.append(f'<img src="data:image/png;base64,{img_str}" alt="{titulo}">')

    # Servidumbre
    if "servidumbre" in include_subkeys and calculo_dge.get('servidumbre'):
        servidumbre_data = calculo_dge.get('servidumbre')
        html_parts.append('<h5>Franja de Servidumbre AEA-95301-2007</h5>')
        html_parts.append('<table class="table table-bordered params-table">')
        a_val = _safe_format(servidumbre_data.get("A"), ".3f", name="servidumbre.A")
        c_val = _safe_format(servidumbre_data.get("C"), ".3f", name="servidumbre.C")
        d_val = _safe_format(servidumbre_data.get("d"), ".3f", name="servidumbre.d")
        dm_val = _safe_format(servidumbre_data.get("dm"), ".3f", name="servidumbre.dm")
        vs_val = _safe_format(servidumbre_data.get("Vs"), ".2f", name="servidumbre.Vs")
        html_parts.append(f'<tr><td>Ancho total franja (A)</td><td>{a_val} m</td></tr>')
        html_parts.append(f'<tr><td>Distancia conductores externos (C)</td><td>{c_val} m</td></tr>')
        html_parts.append(f'<tr><td>Distancia seguridad (d)</td><td>{d_val} m</td></tr>')
        html_parts.append(f'<tr><td>Distancia mínima (dm)</td><td>{dm_val} m</td></tr>')
        html_parts.append(f'<tr><td>Tensión sobretensión (Vs)</td><td>{vs_val} kV</td></tr>')
        html_parts.append('</table>')
        if servidumbre_data.get('memoria_calculo'):
            html_parts.append('<h6>Memoria de Cálculo</h6>')
            html_parts.append(f'<pre>{servidumbre_data["memoria_calculo"]}</pre>')

    if "memoria" in include_subkeys and calculo_dge.get('memoria_calculo'):
        html_parts.append('<hr><h5>Memoria de Cálculo</h5>')
        html_parts.append(f'<pre>{calculo_dge["memoria_calculo"]}</pre>')

    return '\n'.join(html_parts)


def construir_html_personalizado(nombre_familia: str, resultados_familia: Dict[str, Any], selected_keys: List[str]) -> str:
    """Construye el HTML para la familia incluyendo solo las secciones seleccionadas.

    Args:
        nombre_familia: nombre de la familia
        resultados_familia: dict con resultados (como usa generar_html_familia)
        selected_keys: lista de keys seleccionadas (por ejemplo: "Estr.1:cmc", "Estr.1:dge.dimensiones")
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.debug(f"Construir HTML personalizado para familia='{nombre_familia}' seleccionadas={selected_keys}")
    total_included = []  # recoger secciones realmente incluidas durante la generación

    # Cabecera y estilos idénticos a generar_html_familia para mantener formato
    head = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Familia - {nombre}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {{
            --color-blue: #0a4a94;
            --color-green: #27a42f;
            --accent: var(--color-blue);
            --accent-alt: var(--color-green);
        }}
        body {{ padding: 20px; font-family: Arial, sans-serif; background-color: #f8f9fa; color: #212529; }}
        .container-fluid {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 4px 12px rgba(10,74,148,0.06); border-top: 6px solid var(--accent); }}
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
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1>Familia de Estructuras - {nombre}</h1>
        <p class="timestamp">Generado: {ts}</p>
        <hr>
""".format(nombre=nombre_familia, ts=timestamp)

    secciones_html = []

    # Normalizar entrada: aceptar dict directo (con 'resultados_estructuras') o formato completo de cache con 'resultados' envolviendo
    normalized_resultados = resultados_familia
    estructuras = {}
    costeo_global = {}
    if isinstance(resultados_familia, dict):
        if 'resultados_estructuras' in resultados_familia:
            estructuras = resultados_familia.get("resultados_estructuras", {})
            costeo_global = resultados_familia.get('costeo_global', {})
        elif 'resultados' in resultados_familia and isinstance(resultados_familia['resultados'], dict):
            inner = resultados_familia['resultados']
            normalized_resultados = inner
            estructuras = inner.get("resultados_estructuras", {})
            costeo_global = inner.get('costeo_global', {})
        else:
            estructuras = resultados_familia.get('estructuras', {})
            costeo_global = resultados_familia.get('costeo_global', {})

    # Construir checklist activo por estructura para pasar al generador de índice
    checklist_por_estructura = {}
    for nombre_estr, datos_estr in estructuras.items():
        resultados = datos_estr.get("resultados", {})
        dge = resultados.get('dge', {}) or {}
        local = {
            'cmc': ('cmc' in selected_keys) or (f"{nombre_estr}:cmc" in selected_keys),
            'dge': ('dge' in selected_keys) or (f"{nombre_estr}:dge" in selected_keys) or any(k.startswith('dge.') for k in selected_keys) or any(k.startswith(f"{nombre_estr}:dge.") for k in selected_keys),
            'dge.dimensiones': ('dge.dimensiones' in selected_keys) or (f"{nombre_estr}:dge.dimensiones" in selected_keys),
            'dge.nodos': ('dge.nodos' in selected_keys) or (f"{nombre_estr}:dge.nodos" in selected_keys),
            'dge.diagramas': (('dge.diagramas' in selected_keys) or (f"{nombre_estr}:dge.diagramas" in selected_keys)) and bool(dge.get('hash_parametros')),
            'dge.plscadd': (('dge.plscadd' in selected_keys) or (f"{nombre_estr}:dge.plscadd" in selected_keys)) and bool(dge.get('plscadd_csv') or dge.get('hash_parametros')),
            'dme': ('dme' in selected_keys) or (f"{nombre_estr}:dme" in selected_keys),
            'arboles': ('arboles' in selected_keys) or (f"{nombre_estr}:arboles" in selected_keys),
            'sph': ('sph' in selected_keys) or (f"{nombre_estr}:sph" in selected_keys),
            'fundacion': ('fundacion' in selected_keys) or (f"{nombre_estr}:fundacion" in selected_keys),
            'aee': ('aee' in selected_keys) or (f"{nombre_estr}:aee" in selected_keys),
            'costeo': False  # costeo por estructura no usado en checklist general aqui
        }
        checklist_por_estructura[nombre_estr] = local

    familia_safe = nombre_familia.replace(' ', '_').replace('/', '_')

    # Insertar índice siempre, basado en checklist_por_estructura
    try:
        idx_html = generar_indice_familia(nombre_familia, normalized_resultados, checklist_activo=checklist_por_estructura)
        secciones_html.append(idx_html)
        logger.debug("Índice insertado en HTML personalizado")
    except Exception as e:
        logger.exception(f"Error generando índice para familia '{nombre_familia}': {e}")

    # Resumen (incluir solo si fue explícitamente seleccionado)
    # Usamos 'normalized_resultados' para soportar tanto el formato en memoria como el formato cache (envoltorio 'resultados')
    if "familia:resumen" in selected_keys:
        secciones_html.append(generar_seccion_resumen_familia(nombre_familia, normalized_resultados))
        logger.debug("Incluir sección: familia:resumen")
        total_included.append("familia:resumen")

    if estructuras:
        logger.debug(f"Familia '{nombre_familia}' tiene {len(estructuras)} estructuras: {list(estructuras.keys())}")
        secciones_html.append(f'<div class="accordion" id="accordion_{familia_safe}">')

    for nombre_estr, datos_estr in estructuras.items():
        titulo = datos_estr.get("titulo", nombre_estr)
        titulo_id = titulo.replace(" ", "_").replace("/", "_")
        secciones_html.append(f'''<div class="accordion-item">
  <h2 class="accordion-header" id="heading_{titulo_id}">
    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_{titulo_id}" aria-expanded="false" aria-controls="collapse_{titulo_id}">
      {titulo}
    </button>
  </h2>
  <div id="collapse_{titulo_id}" class="accordion-collapse collapse" aria-labelledby="heading_{titulo_id}">
    <div class="accordion-body">''')

        resultados = datos_estr.get("resultados", {})

        # Para cada tipo de sección, comprobar si alguna key seleccionada la habilita.
        # Soporta keys globales (e.g., 'cmc', 'dge', 'dge.dimensiones') o legacy con prefijo por estructura ('Estr.1:cmc').

        # CMC
        if 'cmc' in selected_keys or any(k == f"{nombre_estr}:cmc" for k in selected_keys):
            if resultados.get('cmc'):
                secciones_html.append(_render_cmc_parcial(resultados['cmc'], selected_keys))
                logger.debug(f"Estructura {nombre_estr}: incluir cmc")
                total_included.append(f"{nombre_estr}:cmc")

        # DGE - decidir subkeys a aplicar para ESTA estructura: si 'dge' global está seleccionado -> incluir todo.
        dge = resultados.get('dge')
        if dge:
            # Recolectar subkeys para esta estructura: global 'dge.*' or structure-prefixed
            subkeys = set()
            for k in selected_keys:
                if k == 'dge' or k.startswith('dge.'):
                    # global dge.* selected
                    if '.' in k:
                        subkeys.add(k.split('.', 1)[1])
                    else:
                        # 'dge' means include all -> represent by empty set
                        subkeys = None
                        break
                if k.startswith(f"{nombre_estr}:dge."):
                    sub_part = k.split(':', 1)[1]
                    if '.' in sub_part:
                        subkeys.add(sub_part.split('.',1)[1])
                    else:
                        subkeys = None
                        break
                if k == f"{nombre_estr}:dge":
                    subkeys = None
                    break

            if subkeys is None:
                # incluir DGE completo
                secciones_html.append(generar_seccion_dge(dge))
                logger.debug(f"Estructura {nombre_estr}: incluir DGE completo")
                total_included.append(f"{nombre_estr}:dge")
            else:
                dge_subs = list(subkeys)
                if dge_subs:
                    secciones_html.append(_render_dge_parcial(dge, dge_subs))
                    for s in dge_subs:
                        logger.debug(f"Estructura {nombre_estr}: incluir dge.{s}")
                        total_included.append(f"{nombre_estr}:dge.{s}")

        # DME
        if 'dme' in selected_keys or any(k == f"{nombre_estr}:dme" for k in selected_keys):
            if resultados.get('dme'):
                secciones_html.append(generar_seccion_dme(resultados['dme']))
                logger.debug(f"Estructura {nombre_estr}: incluir dme")
                total_included.append(f"{nombre_estr}:dme")

        # Árboles
        if 'arboles' in selected_keys or any(k == f"{nombre_estr}:arboles" for k in selected_keys):
            if resultados.get('arboles'):
                secciones_html.append(generar_seccion_arboles(resultados['arboles']))
                logger.debug(f"Estructura {nombre_estr}: incluir arboles")
                total_included.append(f"{nombre_estr}:arboles")

        # SPH
        if 'sph' in selected_keys or any(k == f"{nombre_estr}:sph" for k in selected_keys):
            if resultados.get('sph'):
                secciones_html.append(generar_seccion_sph(resultados['sph']))
                logger.debug(f"Estructura {nombre_estr}: incluir sph")
                total_included.append(f"{nombre_estr}:sph")

        # Fundacion
        if 'fundacion' in selected_keys or any(k == f"{nombre_estr}:fundacion" for k in selected_keys):
            if resultados.get('fundacion'):
                secciones_html.append(generar_seccion_fund(resultados['fundacion']))
                logger.debug(f"Estructura {nombre_estr}: incluir fundacion")
                total_included.append(f"{nombre_estr}:fundacion")

        # AEE
        if 'aee' in selected_keys or any(k == f"{nombre_estr}:aee" for k in selected_keys):
            if resultados.get('aee'):
                secciones_html.append(generar_seccion_aee(resultados['aee'], datos_estr.get('estructura', {})))
                logger.debug(f"Estructura {nombre_estr}: incluir aee")
                total_included.append(f"{nombre_estr}:aee")
        secciones_html.append('</div></div></div>')

    if estructuras:
        secciones_html.append('</div>')

    # Registrar resumen de secciones incluidas
    logger.debug(f"Secciones incluidas totales: {total_included}")

    # Costeo global
    if "familia:costeo" in selected_keys or any(k.startswith("familia:costeo") for k in selected_keys):
        if costeo_global:
            from utils.descargar_html_familia_completo import generar_seccion_costeo_familia
            secciones_html.append(generar_seccion_costeo_familia(costeo_global, estructuras))
            logger.debug("Incluir sección: familia:costeo")
            total_included.append("familia:costeo")

    footer = """
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    """

    contenido = "\n".join(secciones_html)
    html_final = head + contenido + footer
    logger.debug(f"HTML personalizado generado para '{nombre_familia}' (longitud={len(html_final)})")
    return html_final
