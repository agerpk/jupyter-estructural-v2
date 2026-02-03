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
import pandas as pd
from io import StringIO
from utils.descargar_html_familia_completo import generar_seccion_resumen_familia
from utils.descargar_html import _safe_format, _load_image_base64, generar_seccion_cmc, generar_seccion_dge, generar_seccion_dme, generar_seccion_arboles, generar_seccion_sph, generar_seccion_fund, generar_seccion_aee
from utils.descargar_html_familia_completo import generar_indice_familia
from utils.view_helpers import ViewHelpers
from config.app_config import CACHE_DIR
from pathlib import Path

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
            # Resumen de distancias: D_fases, Dhg, Lk y alturas derivadas
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_distancias", key=f"{nombre_estr}:dge.distancias", label="DGE: Distancias de Estructura", orden=orden, parent_id=f"{nombre_estr}_dge"))
            orden += 1
        # Nodos
        if dge.get("nodes_key"):
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_nodos", key=f"{nombre_estr}:dge.nodos", label="DGE: Nodos Estructurales", orden=orden, parent_id=f"{nombre_estr}_dge"))
            orden += 1
        # Diagramas (estructura/cabezal/nodos) -> separar en 3 entradas
        hashp = dge.get("hash_parametros")
        if hashp:
            posibles = [f"Estructura.{hashp}.png", f"Cabezal.{hashp}.png", f"Nodos.{hashp}.png"]
            founds = { 'graf_estructura': ViewHelpers.cargar_imagen_base64(posibles[0]),
                       'graf_cabezal': ViewHelpers.cargar_imagen_base64(posibles[1]),
                       'graf_nodos': ViewHelpers.cargar_imagen_base64(posibles[2]) }
            if founds['graf_estructura']:
                secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_graf_estructura", key=f"{nombre_estr}:dge.diagramas.graf_estructura", label="DGE: Gráfico de Estructura", orden=orden, parent_id=f"{nombre_estr}_dge"))
                orden += 1
            if founds['graf_cabezal']:
                secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_graf_cabezal", key=f"{nombre_estr}:dge.diagramas.graf_cabezal", label="DGE: Gráfico de Cabezal", orden=orden, parent_id=f"{nombre_estr}_dge"))
                orden += 1
            if founds['graf_nodos']:
                secciones.append(SectionDescriptor(id=f"{nombre_estr}_dge_graf_nodos", key=f"{nombre_estr}:dge.diagramas.graf_nodos", label="DGE: Gráfico 3D de Nodos y Coordenadas", orden=orden, parent_id=f"{nombre_estr}_dge"))
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

    # DME (y subsecciones)
    if resultados.get("dme"):
        dme = resultados.get('dme') or {}
        secciones.append(SectionDescriptor(id=f"{nombre_estr}_dme", key=f"{nombre_estr}:dme", label="DME - Diseño Mecánico (completo)", orden=orden, generator_func_name="dme"))
        orden += 1
        # Resumen ejecutivo
        if any(dme.get(k) for k in ['resumen_ejecutivo','resumen','texto_resumen','resumen_html']):
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dme_resumen", key=f"{nombre_estr}:dme.resumen", label="DME: Resumen Ejecutivo", orden=orden, parent_id=f"{nombre_estr}_dme"))
            orden += 1
        # Tabla de reacciones
        if dme.get('df_reacciones_html'):
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dme_tabla", key=f"{nombre_estr}:dme.tabla", label="DME: Tabla Resumen de Reacciones y Tiros", orden=orden, parent_id=f"{nombre_estr}_dme"))
            orden += 1
        # Diagramas
        if dme.get('hash_parametros'):
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dme_polar", key=f"{nombre_estr}:dme.polar", label="DME: Diagrama Polar de Tiros", orden=orden, parent_id=f"{nombre_estr}_dme"))
            orden += 1
            secciones.append(SectionDescriptor(id=f"{nombre_estr}_dme_barras", key=f"{nombre_estr}:dme.barras", label="DME: Diagrama de Barras", orden=orden, parent_id=f"{nombre_estr}_dme"))
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
        'dge.graf_estructura': False,
        'dge.graf_cabezal': False,
        'dge.graf_nodos': False,
        'dge.servidumbre': False,
        'dge.memoria': False,
        'dge.plscadd': False,
        'dge.distancias': False,
        'dme': False,
        'dme.resumen': False,
        'dme.tabla': False,
        'dme.polar': False,
        'dme.barras': False,
        'arboles': False,
        'arboles.tabla': False,
        'arboles.imagenes': False,
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
                # Habilitar resumen de distancias si existen dimensiones
                has['dge.distancias'] = True
            if dge.get('nodes_key'):
                has['dge.nodos'] = True
            if dge.get('hash_parametros'):
                # verificar si al menos una de las imagenes existe en cache
                hashp = dge.get('hash_parametros')
                posibles = [f"Estructura.{hashp}.png", f"Cabezal.{hashp}.png", f"Nodos.{hashp}.png"]
                found_graf_estructura = ViewHelpers.cargar_imagen_base64(posibles[0])
                found_graf_cabezal = ViewHelpers.cargar_imagen_base64(posibles[1])
                found_graf_nodos = ViewHelpers.cargar_imagen_base64(posibles[2])
                if found_graf_estructura:
                    has['dge.graf_estructura'] = True
                if found_graf_cabezal:
                    has['dge.graf_cabezal'] = True
                if found_graf_nodos:
                    has['dge.graf_nodos'] = True
                # Buscar plscadd csv
                if dge.get('plscadd_csv'):
                    has['dge.plscadd'] = True
            if dge.get('servidumbre'):
                has['dge.servidumbre'] = True
            if dge.get('memoria_calculo'):
                has['dge.memoria'] = True
            if dge.get('hash_parametros'):
                # mark dme-like flags only for DME presence below (if present)
                pass
            # DME flags
            if 'dme' in resultados and resultados['dme']:
                has['dme'] = True
                dme = resultados['dme'] or {}
                if any(dme.get(k) for k in ['resumen_ejecutivo','resumen','texto_resumen','resumen_html']):
                    has['dme.resumen'] = True
                if dme.get('df_reacciones_html'):
                    has['dme.tabla'] = True
                if dme.get('hash_parametros'):
                    has['dme.polar'] = True
                    has['dme.barras'] = True
        if 'dme' in resultados and resultados['dme']:
            has['dme'] = True
        if 'arboles' in resultados and resultados['arboles']:
            has['arboles'] = True
            arb = resultados['arboles'] or {}
            if arb.get('df_resumen_html'):
                has['arboles.tabla'] = True
            imagenes = arb.get('imagenes') or []
            if imagenes and len(imagenes) > 0:
                has['arboles.imagenes'] = True
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
        if has['dge.graf_estructura']:
            secciones.append(SectionDescriptor(id="dge.graf_estructura", key="dge.diagramas.graf_estructura", label="DGE: Gráfico de Estructura", orden=orden))
            orden += 1
        if has['dge.graf_cabezal']:
            secciones.append(SectionDescriptor(id="dge.graf_cabezal", key="dge.diagramas.graf_cabezal", label="DGE: Gráfico de Cabezal", orden=orden))
            orden += 1
        if has['dge.graf_nodos']:
            secciones.append(SectionDescriptor(id="dge.graf_nodos", key="dge.diagramas.graf_nodos", label="DGE: Gráfico 3D de Nodos y Coordenadas", orden=orden))
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
        if has.get('dge.distancias'):
            secciones.append(SectionDescriptor(id="dge.distancias", key="dge.distancias", label="DGE: Distancias de Estructura", orden=orden))
            orden += 1
    if has['dme']:
        secciones.append(SectionDescriptor(id="dme", key="dme", label="DME - Diseño Mecánico (completo)", orden=orden))
        orden += 1
        if has['dme.resumen']:
            secciones.append(SectionDescriptor(id="dme.resumen", key="dme.resumen", label="DME: Resumen Ejecutivo", orden=orden))
            orden += 1
        if has['dme.tabla']:
            secciones.append(SectionDescriptor(id="dme.tabla", key="dme.tabla", label="DME: Tabla Resumen de Reacciones y Tiros", orden=orden))
            orden += 1
        if has['dme.polar']:
            secciones.append(SectionDescriptor(id="dme.polar", key="dme.polar", label="DME: Diagrama Polar de Tiros", orden=orden))
            orden += 1
        if has['dme.barras']:
            secciones.append(SectionDescriptor(id="dme.barras", key="dme.barras", label="DME: Diagrama de Barras", orden=orden))
            orden += 1

    if has['arboles']:
        secciones.append(SectionDescriptor(id="arboles", key="arboles", label="Árboles de Carga", orden=orden))
        orden += 1
        if has.get('arboles.tabla'):
            secciones.append(SectionDescriptor(id="arboles.tabla", key="arboles.tabla", label="Cargas Aplicadas por Nodo", orden=orden, parent_id="arboles"))
            orden += 1
        if has.get('arboles.imagenes'):
            secciones.append(SectionDescriptor(id="arboles.imagenes", key="arboles.imagenes", label="Árboles", orden=orden, parent_id="arboles"))
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


def _render_dge_parcial(calculo_dge: Dict[str, Any], include_subkeys: List[str], id_prefix: str = None) -> str:
    # Construir DGE seccion por partes según include_subkeys
    html_parts = ['<h3>2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)</h3>']

    if "dimensiones" in include_subkeys and calculo_dge.get("dimensiones"):
        dimensiones = calculo_dge.get('dimensiones', {})
        if id_prefix:
            html_parts.append(f'<h5 id="{id_prefix}_dge_dimensiones">Dimensiones de Estructura</h5>')
        else:
            html_parts.append('<h5>Dimensiones de Estructura</h5>')
        html_parts.append('<table class="table table-bordered params-table">')
        for campo, valor in dimensiones.items():
            if isinstance(valor, (int, float)):
                formatted = _safe_format(valor, ".3f", name=f"dimensiones.{campo}")
                html_parts.append(f'<tr><td>{campo}</td><td>{formatted}</td></tr>')
            else:
                html_parts.append(f'<tr><td>{campo}</td><td>{valor}</td></tr>')
        html_parts.append('</table>')

    # Resumen de distancias (usar formateador centralizado si está disponible)
    if "distancias" in include_subkeys and calculo_dge.get('dimensiones'):
        dimensiones = calculo_dge.get('dimensiones', {})
        try:
            from EstructuraAEA_Geometria import EstructuraAEA_Geometria
            dist_txt = EstructuraAEA_Geometria.formato_resumen_distancias(dimensiones)
        except Exception:
            # Fallback simple
            D_fases = dimensiones.get('D_fases', 0.0)
            Dhg = dimensiones.get('Dhg', 0.0)
            Lk = dimensiones.get('Lk', 0.0)
            dist_txt = (f"Distancia entre Fases (D_Fases): {D_fases:.2f} m\n"
                        f"Distancia Guardia-Fase (Dhg): {Dhg:.2f} m\n\n"
                        f"Longitud de Cadena Oscilante (Lk): {Lk:.2f} m\n")
        if id_prefix:
            html_parts.append(f'<h5 id="{id_prefix}_dge_distancias">Distancias de Estructura</h5>')
        else:
            html_parts.append('<h5>Distancias de Estructura</h5>')
        html_parts.append(f'<pre style="white-space: pre-wrap;">{dist_txt}</pre>')

    if "nodos" in include_subkeys and calculo_dge.get('nodes_key'):
        nodes_key = calculo_dge.get('nodes_key', {})
        if id_prefix:
            html_parts.append(f'<h5 id="{id_prefix}_dge_nodos">Nodos Estructurales</h5>')
        else:
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
    if ("diagramas" in include_subkeys or any(sk.startswith('diagramas.') for sk in include_subkeys)) and calculo_dge.get('hash_parametros'):
        hash_params = calculo_dge.get('hash_parametros')
        entries = [
            (f"Estructura.{hash_params}.png", "Estructura Completa", 'graf_estructura'),
            (f"Cabezal.{hash_params}.png", "Detalle Cabezal", 'graf_cabezal'),
            (f"Nodos.{hash_params}.png", "Nodos y Coordenadas", 'graf_nodos')
        ]
        for nombre, titulo, shortid in entries:
            key_name = f"diagramas.{shortid}"
            if ('diagramas' in include_subkeys) or (key_name in include_subkeys) or (f'dge.diagramas.{shortid}' in include_subkeys):
                img_str = ViewHelpers.cargar_imagen_base64(nombre)
                if img_str:
                    if id_prefix:
                        html_parts.append(f'<h6 id="{id_prefix}_dge_{shortid}">{titulo}</h6>')
                    else:
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

    # Tabla PLS-CADD (si fue seleccionada)
    if "plscadd" in include_subkeys:
        plscadd = calculo_dge.get('plscadd_csv')
        if not plscadd:
            hashp = calculo_dge.get('hash_parametros')
            if hashp:
                matches = list(Path(CACHE_DIR).glob(f"*{hashp}*.csv"))
                if matches:
                    plscadd = matches[0].name
        if plscadd:
            html_parts.append('<hr><h5>Tabla PLS-CADD</h5>')
            try:
                from pathlib import Path as _P
                import pandas as _pd
                import csv as _csv
                from io import StringIO as _StringIO
                csv_path = _P(CACHE_DIR) / plscadd
                if csv_path.exists():
                    lines = csv_path.read_text(encoding='utf-8').splitlines()
                    header_idx = 0
                    for i, line in enumerate(lines[:30]):
                        if line.strip().startswith('Set #') or 'Set #' in line:
                            header_idx = i
                            break

                    # Parse metadata lines
                    meta_lines = lines[:header_idx] if header_idx > 0 else []
                    if meta_lines:
                        html_parts.append('<h6>Información de Estructura</h6>')
                        html_parts.append('<table class="table table-sm table-borderless">')
                        reader = _csv.reader(_StringIO('\n'.join(meta_lines)))
                        for r in reader:
                            if any((cell or '').strip() for cell in r):
                                if len(r) == 1:
                                    html_parts.append(f'<tr><td colspan="2"><strong>{r[0]}</strong></td></tr>')
                                else:
                                    key = r[0]
                                    val = r[1] if len(r) > 1 else ''
                                    html_parts.append(f'<tr><td><strong>{key}</strong></td><td>{val}</td></tr>')
                        html_parts.append('</table>')

                    # Read table skipping metadata rows
                    if header_idx > 0:
                        df_pls = _pd.read_csv(csv_path, skiprows=header_idx)
                    else:
                        df_pls = _pd.read_csv(csv_path)

                    html_parts.append('<div class="table-responsive">')
                    html_parts.append(df_pls.to_html(classes='"table table-striped table-bordered table-sm"', index=False))
                    html_parts.append('</div>')
                else:
                    html_parts.append(f'<div class="alert alert-warning">CSV PLS-CADD no encontrado en cache: {plscadd}</div>')
            except Exception as e:
                logger.exception(f"Error mostrando CSV PLS-CADD en familia personalizado DGE: {e}")
                html_parts.append(f'<div class="alert alert-warning">No se pudo mostrar CSV PLS-CADD: {e}</div>')

    return '\n'.join(html_parts)


def _render_dme_parcial(calculo_dme: Dict[str, Any], include_subkeys: List[str], id_prefix: str = None) -> str:
    """Render parcial de DME según include_subkeys: ['resumen','tabla','polar','barras']"""
    html_parts = ['<h3>3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)</h3>']

    # Resumen
    if 'resumen' in include_subkeys:
        resumen = None
        for k in ['resumen_ejecutivo','resumen','texto_resumen','resumen_html']:
            if calculo_dme.get(k):
                resumen = calculo_dme.get(k)
                break
        if resumen:
            if id_prefix:
                html_parts.append(f'<h5 id="{id_prefix}_dme_resumen">Resumen Ejecutivo</h5>')
            else:
                html_parts.append('<h5>Resumen Ejecutivo</h5>')
            html_parts.append(f'<pre>{resumen}</pre>')

    # Tabla de reacciones
    if 'tabla' in include_subkeys and calculo_dme.get('df_reacciones_html'):
        df = pd.read_json(StringIO(calculo_dme['df_reacciones_html']), orient='split').round(2)
        if id_prefix:
            html_parts.append(f'<h5 id="{id_prefix}_dme_tabla_reacciones">Tabla Resumen de Reacciones y Tiros</h5>')
        else:
            html_parts.append('<h5>Tabla Resumen de Reacciones y Tiros</h5>')
        html_parts.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm'))

    # Polar / Barras
    if 'polar' in include_subkeys or 'barras' in include_subkeys:
        hash_params = calculo_dme.get('hash_parametros')
        if hash_params:
            if 'polar' in include_subkeys:
                nombre = f"DME_Polar.{hash_params}.png"
                titulo = "Diagrama Polar de Reacciones"
                img_str = _load_image_base64(nombre, context="DME")
                if img_str:
                    if id_prefix:
                        html_parts.append(f'<h5 id="{id_prefix}_dme_polar">{titulo}</h5>')
                    else:
                        html_parts.append(f'<h5>{titulo}</h5>')
                    html_parts.append(f'<img src="data:image/png;base64,{img_str}" alt="{titulo}">')
                else:
                    html_parts.append(f'<div class="alert alert-warning">No se encontró imagen: {titulo} ({nombre})</div>')
            if 'barras' in include_subkeys:
                nombre = f"DME_Barras.{hash_params}.png"
                titulo = "Diagrama de Barras"
                img_str = _load_image_base64(nombre, context="DME")
                if img_str:
                    if id_prefix:
                        html_parts.append(f'<h5 id="{id_prefix}_dme_barras">{titulo}</h5>')
                    else:
                        html_parts.append(f'<h5>{titulo}</h5>')
                    html_parts.append(f'<img src="data:image/png;base64,{img_str}" alt="{titulo}">')
                else:
                    html_parts.append(f'<div class="alert alert-warning">No se encontró imagen: {titulo} ({nombre})</div>')

    return '\n'.join(html_parts)


def _render_arboles_parcial(calculo_arboles: Dict[str, Any], include_subkeys: List[str], id_prefix: str = None) -> str:
    """Render parcial de Árboles de Carga según include_subkeys: ['tabla','imagenes']"""
    html_parts = ['<h3>4. ÁRBOLES DE CARGA</h3>']

    # Tabla de cargas aplicadas por nodo
    if 'tabla' in include_subkeys:
        if calculo_arboles.get('df_resumen_html'):
            try:
                df = pd.read_json(StringIO(calculo_arboles['df_resumen_html']), orient='split')
                if id_prefix:
                    html_parts.append(f'<h5 id="{id_prefix}_arboles_tabla">Cargas Aplicadas por Nodo</h5>')
                else:
                    html_parts.append('<h5>Cargas Aplicadas por Nodo</h5>')
                html_parts.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm'))
            except Exception as e:
                html_parts.append('<div class="alert alert-warning">Error cargando tabla de Árboles de Carga.</div>')
        elif calculo_arboles.get('df_cargas_completo'):
            try:
                df_dict = calculo_arboles['df_cargas_completo']
                if isinstance(df_dict, dict) and 'columns' in df_dict and 'column_codes' in df_dict:
                    arrays = []
                    for level_idx in range(len(df_dict['columns'])):
                        level_values = df_dict['columns'][level_idx]
                        codes = df_dict['column_codes'][level_idx]
                        arrays.append([level_values[code] for code in codes])
                    multi_idx = pd.MultiIndex.from_arrays(arrays)
                    try:
                        # No label for second level to avoid 'Componente' header
                        multi_idx.names = ['Hipótesis', None]
                    except Exception:
                        pass
                    df = pd.DataFrame(df_dict.get('data', []), columns=multi_idx)
                else:
                    df = pd.read_json(pd.io.json.dumps(df_dict), orient='split')
                df = df.round(2)
                if id_prefix:
                    html_parts.append(f'<h5 id="{id_prefix}_arboles_tabla">Cargas Aplicadas por Nodo</h5>')
                else:
                    html_parts.append('<h5>Cargas Aplicadas por Nodo</h5>')
                html_parts.append('<div class="table-responsive small-table">')
                html_parts.append(df.to_html(classes='table table-striped table-bordered table-hover table-sm'))
                html_parts.append('</div>')
            except Exception as e:
                html_parts.append('<div class="alert alert-warning">Error cargando tabla de Árboles de Carga.</div>')
        else:
            # No table available
            pass

    # Imágenes
    if 'imagenes' in include_subkeys and calculo_arboles.get('imagenes'):
        imagenes = calculo_arboles.get('imagenes', [])
        if imagenes:
            if id_prefix:
                html_parts.append(f'<h5 id="{id_prefix}_arboles_imagenes">Árboles</h5>')
            else:
                html_parts.append('<h5>Árboles</h5>')
            html_parts.append('<div class="grid-2col">')
            for img_item in imagenes:
                img_nombre = img_item if isinstance(img_item, str) else img_item.get('nombre', '')
                if img_nombre:
                    img_str = ViewHelpers.cargar_imagen_base64(img_nombre)
                    if img_str:
                        titulo = img_nombre.split("HIP_")[-1].replace(".png", "") if "HIP_" in img_nombre else img_nombre
                        html_parts.append(f'<div><h6>{titulo}</h6><img src="data:image/png;base64,{img_str}" alt="{img_nombre}"></div>')
            html_parts.append('</div>')

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
    # Intentar cargar logo embebido (logo_distrocuyo.png)
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
        .grid-2col {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0; align-items: start; }}
        .grid-2col img {{ width: 100%; height: auto; display: block; margin: 0 auto; }}
        @media (max-width: 720px) {{
            .grid-2col {{ grid-template-columns: 1fr; }}
        }}
        .alert {{ margin: 20px 0; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1>{logo_html} Familia de Estructuras - {nombre}</h1>
        <p class="timestamp">Generado: {ts}</p>
        <hr>
""".format(nombre=nombre_familia, ts=timestamp, logo_html=logo_html)

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
    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_{titulo_id}" aria-expanded="true" aria-controls="collapse_{titulo_id}">
      Estructura: {titulo}
    </button>
  </h2>
  <div id="collapse_{titulo_id}" class="accordion-collapse collapse show" aria-labelledby="heading_{titulo_id}">
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
                secciones_html.append(generar_seccion_dge(dge, id_prefix=titulo_id))
                logger.debug(f"Estructura {nombre_estr}: incluir DGE completo")
                total_included.append(f"{nombre_estr}:dge")
            else:
                dge_subs = list(subkeys)
                if dge_subs:
                    secciones_html.append(_render_dge_parcial(dge, dge_subs, id_prefix=titulo_id))
                    for s in dge_subs:
                        logger.debug(f"Estructura {nombre_estr}: incluir dge.{s}")
                        total_included.append(f"{nombre_estr}:dge.{s}")

        # DME (soporta subkeys dme.resumen, dme.tabla, dme.polar, dme.barras)
        dme_selected = False
        dme_subs = set()
        for k in selected_keys:
            if k == 'dme' or k == f"{nombre_estr}:dme":
                dme_selected = True
                break
            if k.startswith('dme.'):
                dme_subs.add(k.split('.',1)[1])
            if k.startswith(f"{nombre_estr}:dme."):
                sub = k.split(':',1)[1]
                if '.' in sub:
                    dme_subs.add(sub.split('.',1)[1])
        if dme_selected:
            if resultados.get('dme'):
                secciones_html.append(generar_seccion_dme(resultados['dme'], id_prefix=titulo_id))
                logger.debug(f"Estructura {nombre_estr}: incluir dme")
                total_included.append(f"{nombre_estr}:dme")
        else:
            if dme_subs and resultados.get('dme'):
                secciones_html.append(_render_dme_parcial(resultados['dme'], list(dme_subs), id_prefix=titulo_id))
                for s in dme_subs:
                    logger.debug(f"Estructura {nombre_estr}: incluir dme.{s}")
                    total_included.append(f"{nombre_estr}:dme.{s}")

        # Árboles (soporta subsecciones 'arboles.tabla' y 'arboles.imagenes')
        arboles_selected = False
        arboles_subs = set()
        for k in selected_keys:
            if k == 'arboles' or k == f"{nombre_estr}:arboles":
                arboles_selected = True
                break
            if k.startswith('arboles.'):
                arboles_subs.add(k.split('.',1)[1])
            if k.startswith(f"{nombre_estr}:arboles."):
                sub = k.split(':',1)[1]
                if '.' in sub:
                    arboles_subs.add(sub.split('.',1)[1])

        if arboles_selected:
            if resultados.get('arboles'):
                secciones_html.append(generar_seccion_arboles(resultados['arboles']))
                logger.debug(f"Estructura {nombre_estr}: incluir arboles completo")
                total_included.append(f"{nombre_estr}:arboles")
        else:
            if arboles_subs and resultados.get('arboles'):
                secciones_html.append(_render_arboles_parcial(resultados['arboles'], list(arboles_subs), id_prefix=titulo_id))
                for s in arboles_subs:
                    logger.debug(f"Estructura {nombre_estr}: incluir arboles.{s}")
                    total_included.append(f"{nombre_estr}:arboles.{s}")

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

        // Collect ancestor collapses that need to be opened (outermost first)
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
</html>
    """

    contenido = "\n".join(secciones_html)
    html_final = head + contenido + footer
    logger.debug(f"HTML personalizado generado para '{nombre_familia}' (longitud={len(html_final)})")
    return html_final
