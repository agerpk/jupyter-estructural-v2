"""
Lógica encadenada para cálculo de familia de estructuras
Reutiliza secuencia CMC>DGE>DME>Árboles>SPH>Fundación>Costeo
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple
import plotly.graph_objects as go
from models.app_state import AppState
from config.app_config import DATA_DIR
from utils.calculo_cache import CalculoCache

def ejecutar_calculo_familia_completa(familia_data: Dict, generar_plots: bool = True, calculos_activos: List[str] = None) -> Dict:
    """
    Ejecuta cálculo completo para toda la familia
    Retorna resultados por estructura y costeo global
    """
    if calculos_activos is None:
        calculos_activos = ["cmc", "dge", "dme", "arboles", "sph", "fundacion", "costeo", "aee"]
    
    nombre_familia = familia_data.get("nombre_familia", "familia")
    print(f"\n🚀 INICIANDO CÁLCULO FAMILIA: {nombre_familia}")
    print(f"   Cálculos activos: {calculos_activos}")
    print(f"   Keys en familia_data: {list(familia_data.keys())}")
    print(f"   Tiene estados_climaticos: {'estados_climaticos' in familia_data}")
    print(f"   Tiene restricciones_cables: {'restricciones_cables' in familia_data}")
    
    if "estados_climaticos" in familia_data:
        print(f"   Estados climáticos: {list(familia_data['estados_climaticos'].keys())}")
    if "restricciones_cables" in familia_data:
        print(f"   Restricciones: {list(familia_data['restricciones_cables'].keys())}")
    
    if not familia_data or "estructuras" not in familia_data:
        return {"exito": False, "mensaje": "Datos de familia inválidos"}
    
    estructuras = familia_data.get("estructuras", {})
    resultados_familia = {}
    costos_individuales = {}
    
    # Procesar cada estructura
    for nombre_estr, datos_estr in estructuras.items():
        titulo = datos_estr.get("TITULO", nombre_estr)
        cantidad = datos_estr.get("cantidad", 1)
        
        print(f"\n🔧 Procesando estructura: {titulo}")
        
        # Aplicar estados climáticos y restricciones de la familia
        print(f"   📊 Aplicando estados climáticos de familia...")
        if "estados_climaticos" in familia_data:
            datos_estr["estados_climaticos"] = familia_data["estados_climaticos"]
            print(f"   ✅ Estados climáticos aplicados: {list(datos_estr['estados_climaticos'].keys())}")
        else:
            print(f"   ⚠️ NO hay estados_climaticos en familia_data")
            
        if "restricciones_cables" in familia_data:
            datos_estr["restricciones_cables"] = familia_data["restricciones_cables"]
            print(f"   ✅ Restricciones aplicadas: {list(datos_estr['restricciones_cables'].keys())}")
        else:
            print(f"   ⚠️ NO hay restricciones_cables en familia_data")
        
        # Aplicar parámetros de servidumbre de la familia O de la estructura
        # Prioridad: familia_data > datos_estr (estructura individual)
        if "mc_servidumbre" in familia_data:
            datos_estr["mc_servidumbre"] = familia_data["mc_servidumbre"]
            print(f"   ✅ mc_servidumbre aplicado desde familia: {datos_estr['mc_servidumbre']}")
        elif "mc_servidumbre" not in datos_estr:
            # Si no está en familia ni en estructura, usar False por defecto
            datos_estr["mc_servidumbre"] = False
            print(f"   ℹ️ mc_servidumbre no definido, usando False")
        else:
            print(f"   ℹ️ mc_servidumbre ya en estructura: {datos_estr.get('mc_servidumbre')}")
        
        if "plot_servidumbre" in familia_data:
            datos_estr["plot_servidumbre"] = familia_data["plot_servidumbre"]
            print(f"   ✅ plot_servidumbre aplicado desde familia: {datos_estr['plot_servidumbre']}")
        elif "plot_servidumbre" not in datos_estr:
            # Si no está en familia ni en estructura, usar False por defecto
            datos_estr["plot_servidumbre"] = False
            print(f"   ℹ️ plot_servidumbre no definido, usando False")
        else:
            print(f"   ℹ️ plot_servidumbre ya en estructura: {datos_estr.get('plot_servidumbre')}")
        
        # DEBUG: Verificar parámetros finales antes de ejecutar
        print(f"   📋 DEBUG FINAL - mc_servidumbre: {datos_estr.get('mc_servidumbre', 'NO EXISTE')}")
        print(f"   📋 DEBUG FINAL - plot_servidumbre: {datos_estr.get('plot_servidumbre', 'NO EXISTE')}")
        
        # Ejecutar secuencia completa para esta estructura
        resultado_estr = _ejecutar_secuencia_estructura(datos_estr, titulo, generar_plots, calculos_activos)
        
        if resultado_estr["exito"]:
            costo_individual = resultado_estr.get("costo_total", 0)
            print(f"✅ {titulo}: Costo individual = {costo_individual} UM")
            
            resultados_familia[nombre_estr] = {
                "titulo": titulo,
                "cantidad": cantidad,
                "resultados": resultado_estr["resultados"],
                "costo_individual": costo_individual
            }
            costos_individuales[titulo] = costo_individual
        else:
            print(f"❌ {titulo}: {resultado_estr['mensaje']}")
            resultados_familia[nombre_estr] = {
                "titulo": titulo,
                "cantidad": cantidad,
                "error": resultado_estr["mensaje"]
            }
    
    # Generar costeo global de familia
    costeo_global = _generar_costeo_familia(resultados_familia)
    
    return {
        "exito": True,
        "resultados_estructuras": resultados_familia,
        "costeo_global": costeo_global,
        "graficos_familia": _generar_graficos_familia(resultados_familia)
    }

def _cargar_familia(nombre_familia: str) -> Dict:
    """Cargar datos de familia desde archivo"""
    try:
        archivo_familia = DATA_DIR / f"{nombre_familia.replace(' ', '_')}.familia.json"
        with open(archivo_familia, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando familia: {e}")
        return {}

def _ejecutar_secuencia_estructura(datos_estructura: Dict, titulo: str, generar_plots: bool = True, calculos_activos: List[str] = None) -> Dict:
    """
    Ejecuta secuencia completa CMC>DGE>DME>Árboles>SPH>Fundación>Costeo>AEE
    para una estructura individual creando archivos temporales completos
    """
    if calculos_activos is None:
        calculos_activos = ["cmc", "dge", "dme", "arboles", "sph", "fundacion", "costeo", "aee"]
    try:
        # DEBUG: Mostrar datos recibidos
        print(f"\n📋 DEBUG: Datos recibidos para {titulo}:")
        print(f"   TITULO: {datos_estructura.get('TITULO')}")
        print(f"   cable_conductor_id: {datos_estructura.get('cable_conductor_id')}")
        print(f"   cable_guardia_id: {datos_estructura.get('cable_guardia_id')}")
        print(f"   L_vano: {datos_estructura.get('L_vano')}")
        print(f"   Vmax: {datos_estructura.get('Vmax')}")
        print(f"   Zco: {datos_estructura.get('Zco')}")
        print(f"   Cf_cable: {datos_estructura.get('Cf_cable')}")
        print(f"   Total keys: {len(datos_estructura)}")
        
        # Crear archivos temporales completos
        archivo_estructura = DATA_DIR / f"{titulo}.estructura.json"
        archivo_hipotesis = DATA_DIR / f"{titulo}.hipotesismaestro.json"
        
        # Guardar archivo .estructura.json temporal (con estados climáticos aplicados)
        with open(archivo_estructura, 'w', encoding='utf-8') as f:
            json.dump(datos_estructura, f, indent=2, ensure_ascii=False)
        
        print(f"💾 DEBUG: Archivo guardado con estados_climaticos: {'estados_climaticos' in datos_estructura}")
        print(f"💾 DEBUG: Archivo guardado con restricciones_cables: {'restricciones_cables' in datos_estructura}")
        
        # Crear archivo .hipotesismaestro.json temporal
        from HipotesisMaestro_Especial import hipotesis_maestro
        with open(archivo_hipotesis, 'w', encoding='utf-8') as f:
            json.dump(hipotesis_maestro, f, indent=2, ensure_ascii=False)
        
        # Crear AppState y configurar estructura actual
        state = AppState()
        state.set_estructura_actual(datos_estructura)
        
        resultados = {}
        costo_total = 0
        
        try:
            # 1. CMC
            if "cmc" in calculos_activos:
                from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
                resultado_cmc = ejecutar_calculo_cmc_automatico(datos_estructura, state, generar_plots)
                if resultado_cmc.get('exito'):
                    resultados["cmc"] = CalculoCache.cargar_calculo_cmc(titulo)
                    print(f"✅ CMC completado para {titulo}")
                else:
                    return {"exito": False, "mensaje": f"Error CMC: {resultado_cmc.get('mensaje')}"}
            
            # 2. DGE
            if "dge" in calculos_activos:
                from controllers.geometria_controller import ejecutar_calculo_dge
                resultado_dge = ejecutar_calculo_dge(datos_estructura, state, generar_plots)
                if resultado_dge.get('exito'):
                    resultados["dge"] = CalculoCache.cargar_calculo_dge(titulo)
                    print(f"✅ DGE completado para {titulo}")
                else:
                    return {"exito": False, "mensaje": f"Error DGE: {resultado_dge.get('mensaje')}"}
            
            # 3. DME
            if "dme" in calculos_activos:
                from controllers.ejecutar_calculos import ejecutar_calculo_dme
                resultado_dme = ejecutar_calculo_dme(datos_estructura, state, generar_plots)
                if resultado_dme.get('exito'):
                    resultados["dme"] = CalculoCache.cargar_calculo_dme(titulo)
                    print(f"✅ DME completado para {titulo}")
                else:
                    return {"exito": False, "mensaje": f"Error DME: {resultado_dme.get('mensaje')}"}
            
            # 4. Árboles
            if "arboles" in calculos_activos:
                from controllers.ejecutar_calculos import ejecutar_calculo_arboles
                resultado_arboles = ejecutar_calculo_arboles(datos_estructura, state, generar_plots)
                if resultado_arboles.get('exito'):
                    resultados["arboles"] = CalculoCache.cargar_calculo_arboles(titulo)
                    print(f"✅ Árboles completado para {titulo}")
                else:
                    return {"exito": False, "mensaje": f"Error Árboles: {resultado_arboles.get('mensaje')}"}
            
            # 5. SPH
            if "sph" in calculos_activos:
                from controllers.ejecutar_calculos import ejecutar_calculo_sph
                resultado_sph = ejecutar_calculo_sph(datos_estructura, state)
                if resultado_sph.get('exito'):
                    resultados["sph"] = CalculoCache.cargar_calculo_sph(titulo)
                    print(f"✅ SPH completado para {titulo}")
                else:
                    return {"exito": False, "mensaje": f"Error SPH: {resultado_sph.get('mensaje')}"}
            
            # 6. Fundación
            if "fundacion" in calculos_activos:
                from controllers.ejecutar_calculos import ejecutar_calculo_fundacion
                resultado_fundacion = ejecutar_calculo_fundacion(datos_estructura, state, generar_plots)
                if resultado_fundacion.get('exito'):
                    resultados["fundacion"] = CalculoCache.cargar_calculo_fund(titulo)
                    print(f"✅ Fundación completado para {titulo}")
                else:
                    return {"exito": False, "mensaje": f"Error Fundación: {resultado_fundacion.get('mensaje')}"}
            
            # 7. Costeo
            if "costeo" in calculos_activos:
                from controllers.ejecutar_calculos import ejecutar_calculo_costeo
                resultado_costeo = ejecutar_calculo_costeo(datos_estructura, state)
                
                if resultado_costeo.get('exito'):
                    calculo_costeo = CalculoCache.cargar_calculo_costeo(titulo)
                    resultados["costeo"] = calculo_costeo
                    
                    # Extraer costo total desde resultado_costeo (tiene el valor correcto)
                    if resultado_costeo.get('resultados') and 'resumen_costos' in resultado_costeo['resultados']:
                        costo_total = float(resultado_costeo['resultados']['resumen_costos'].get('costo_total', 0))
                        print(f"   ✅ Costeo completado para {titulo}: {costo_total:.2f} UM")
                    else:
                        costo_total = 0
                        print(f"   ⚠️ Costeo sin resumen_costos para {titulo}")
                else:
                    print(f"   ❌ Error Costeo para {titulo}: {resultado_costeo.get('mensaje')}")
                    return {"exito": False, "mensaje": f"Error Costeo: {resultado_costeo.get('mensaje')}"}
            
            # 8. AEE
            if "aee" in calculos_activos:
                from controllers.ejecutar_calculos import ejecutar_calculo_aee
                resultado_aee = ejecutar_calculo_aee(datos_estructura, state)
                if resultado_aee.get('exito'):
                    resultados["aee"] = CalculoCache.cargar_calculo_aee(titulo)
                    print(f"✅ AEE completado para {titulo}")
                else:
                    return {"exito": False, "mensaje": f"Error AEE: {resultado_aee.get('mensaje')}"}
            
            return {
                "exito": True,
                "resultados": resultados,
                "costo_total": costo_total
            }
            
        finally:
            # Limpiar archivos temporales
            try:
                if archivo_estructura.exists():
                    archivo_estructura.unlink()
                if archivo_hipotesis.exists():
                    archivo_hipotesis.unlink()
                print(f"🧹 Archivos temporales eliminados para {titulo}")
            except Exception as e:
                print(f"⚠️ Error eliminando archivos temporales: {e}")
        
    except Exception as e:
        import traceback
        print(f"❌ Error en secuencia para {titulo}: {traceback.format_exc()}")
        return {"exito": False, "mensaje": f"Error en secuencia: {str(e)}"}

def _generar_costeo_familia(resultados_familia: Dict) -> Dict:
    """Generar costeo global de familia"""
    costo_global = 0
    costos_parciales = {}
    costos_individuales = {}
    
    for nombre_estr, datos in resultados_familia.items():
        if "error" not in datos:
            titulo = datos["titulo"]
            cantidad = datos["cantidad"]
            costo_individual = datos["costo_individual"]
            costo_parcial = costo_individual * cantidad
            
            costos_individuales[titulo] = costo_individual
            costos_parciales[titulo] = costo_parcial
            costo_global += costo_parcial
    
    return {
        "costo_global": costo_global,
        "costos_individuales": costos_individuales,
        "costos_parciales": costos_parciales
    }

def _generar_colores_circulo_cromatico(n: int) -> List[str]:
    """Generar n colores equidistantes en el círculo cromático HSL"""
    import colorsys
    
    colores = []
    for i in range(n):
        # Calcular hue (matiz) equidistante en el círculo (0-360 grados)
        hue = i / n
        # Saturación y luminosidad fijas para colores vibrantes
        saturation = 0.7
        lightness = 0.5
        
        # Convertir HSL a RGB
        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        
        # Convertir a formato rgb(r, g, b)
        color_rgb = f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})"
        colores.append(color_rgb)
    
    return colores

def _generar_graficos_familia(resultados_familia: Dict) -> Dict:
    """Generar gráficos de barras y torta para familia"""
    costos_individuales = {}
    costos_parciales = {}
    
    # Extraer datos
    for nombre_estr, datos in resultados_familia.items():
        if "error" not in datos:
            titulo = datos["titulo"]
            cantidad = datos["cantidad"]
            costo_individual = datos["costo_individual"]
            costo_parcial = costo_individual * cantidad
            
            costos_individuales[titulo] = costo_individual
            costos_parciales[titulo] = costo_parcial
    
    # Gráfico de barras - costos individuales (mayor a menor)
    titulos_ordenados = sorted(costos_individuales.keys(), 
                              key=lambda x: costos_individuales[x], reverse=True)
    
    # Generar colores distintos para cada estructura
    colores = _generar_colores_circulo_cromatico(len(titulos_ordenados))
    
    fig_barras = go.Figure(data=[
        go.Bar(
            x=titulos_ordenados,
            y=[costos_individuales[t] for t in titulos_ordenados],
            name="Costo Individual",
            marker=dict(color=colores)
        )
    ])
    fig_barras.update_layout(
        title="Costos Individuales por Estructura",
        xaxis_title="Estructura",
        yaxis_title="Costo [UM]"
    )
    
    # Gráfico de torta - costos parciales (individual × cantidad)
    fig_torta = go.Figure(data=[
        go.Pie(
            labels=list(costos_parciales.keys()),
            values=list(costos_parciales.values()),
            name="Costo Parcial"
        )
    ])
    fig_torta.update_layout(
        title="Distribución de Costos Parciales (Individual × Cantidad)"
    )
    
    return {
        "grafico_barras": fig_barras,
        "grafico_torta": fig_torta
    }

def generar_vista_resultados_familia(resultados_familia: Dict, calculos_activos: List[str] = None) -> List:
    """Generar vista con pestañas por estructura"""
    from dash import html, dcc
    import dash_bootstrap_components as dbc
    
    if calculos_activos is None:
        calculos_activos = ["cmc", "dge", "dme", "arboles", "sph", "fundacion", "costeo", "aee"]
    
    if not resultados_familia.get("resultados_estructuras"):
        return [dbc.Alert("No hay resultados para mostrar", color="warning")]
    
    # Crear pestañas con contenido
    pestanas = []
    
    for nombre_estr, datos in resultados_familia["resultados_estructuras"].items():
        titulo = datos["titulo"]
        
        # Contenido de pestaña
        if "error" in datos:
            contenido = html.Div([
                dbc.Alert(f"Error: {datos['error']}", color="danger")
            ], style={"padding": "20px"})
        else:
            contenido = _crear_contenido_estructura(datos, calculos_activos)
        
        # Pestaña con contenido envuelto en Container
        pestanas.append(dbc.Tab(
            dbc.Container(contenido, fluid=True, style={"padding": "20px"}),
            label=titulo
        ))
    
    # Agregar pestaña de costeo global
    contenido_costeo = _crear_contenido_costeo_familia(
        resultados_familia.get("costeo_global", {}),
        resultados_familia.get("graficos_familia", {}),
        resultados_familia.get("resultados_estructuras", {})
    )
    pestanas.append(dbc.Tab(
        dbc.Container(contenido_costeo, fluid=True, style={"padding": "20px"}),
        label="Costeo Familia"
    ))
    
    return [dbc.Tabs(pestanas, style={"marginTop": "20px"})]

def _crear_contenido_estructura(datos_estructura: Dict, calculos_activos: List[str] = None):
    """Crear contenido para pestaña de estructura individual"""
    from dash import html
    import dash_bootstrap_components as dbc
    
    if calculos_activos is None:
        calculos_activos = ["cmc", "dge", "dme", "arboles", "sph", "fundacion", "costeo", "aee"]
    
    print(f"\n🔍 DEBUG _crear_contenido_estructura:")
    print(f"   Keys en datos_estructura: {list(datos_estructura.keys())}")
    
    if "error" in datos_estructura:
        print(f"   ❌ Error encontrado: {datos_estructura['error']}")
        return [dbc.Alert(f"Error: {datos_estructura['error']}", color="danger")]
    
    resultados = datos_estructura.get("resultados", {})
    print(f"   Keys en resultados: {list(resultados.keys())}")
    
    if not resultados:
        print(f"   ⚠️ No hay resultados")
        return [dbc.Alert("No hay resultados disponibles", color="warning")]
    
    componentes = []
    
    try:
        # CMC
        if "cmc" in calculos_activos and "cmc" in resultados and resultados["cmc"]:
            print(f"   ✅ Generando CMC...")
            from components.vista_calculo_mecanico import generar_resultados_cmc
            componentes.append(html.H4("1. Cálculo Mecánico de Cables"))
            componentes.append(html.Hr())
            try:
                # Omitir verificación de vigencia en contexto de familia
                cmc_content = generar_resultados_cmc(resultados["cmc"], {}, omitir_vigencia=True)
                if cmc_content:
                    # generar_resultados_cmc retorna html.Div con children como lista
                    if hasattr(cmc_content, 'children'):
                        componentes.append(cmc_content)
                    elif isinstance(cmc_content, list):
                        componentes.extend(cmc_content)
                    else:
                        componentes.append(cmc_content)
                    print(f"   ✅ CMC agregado")
                else:
                    print(f"   ⚠️ CMC retornó None")
            except Exception as e:
                import traceback
                print(f"   ❌ Error en CMC: {traceback.format_exc()}")
                componentes.append(dbc.Alert(f"Error en CMC: {e}", color="warning"))
        
        # DGE
        if "dge" in calculos_activos and "dge" in resultados and resultados["dge"]:
            print(f"   ✅ Generando DGE...")
            from components.vista_diseno_geometrico import generar_resultados_dge
            componentes.append(html.H4("2. Diseño Geométrico"))
            componentes.append(html.Hr())
            try:
                # Reconstruir estructura_actual desde resultados para verificar mc_servidumbre y plot_servidumbre
                estructura_params = resultados["dge"].get("parametros", {})
                print(f"   🔍 DEBUG DGE - Keys en parametros: {list(estructura_params.keys())}")
                print(f"   🔍 DEBUG DGE - mc_servidumbre: {estructura_params.get('mc_servidumbre')}")
                print(f"   🔍 DEBUG DGE - plot_servidumbre: {estructura_params.get('plot_servidumbre')}")
                print(f"   🔍 DEBUG DGE - servidumbre en cache: {'servidumbre' in resultados['dge']}")
                if 'servidumbre' in resultados['dge'] and resultados['dge']['servidumbre'] is not None:
                    print(f"   🔍 DEBUG DGE - Keys en servidumbre: {list(resultados['dge']['servidumbre'].keys())}")
                elif 'servidumbre' in resultados['dge']:
                    print(f"   ⚠️ DEBUG DGE - servidumbre es None")
                dge_content = generar_resultados_dge(resultados["dge"], estructura_params)
                if dge_content:
                    if isinstance(dge_content, list):
                        componentes.extend(dge_content)
                    else:
                        componentes.append(dge_content)
                    print(f"   ✅ DGE agregado")
                else:
                    print(f"   ⚠️ DGE retornó None")
            except Exception as e:
                import traceback
                print(f"   ❌ Error en DGE: {traceback.format_exc()}")
                componentes.append(dbc.Alert(f"Error en DGE: {e}", color="warning"))
        
        # DME
        if "dme" in calculos_activos and "dme" in resultados and resultados["dme"]:
            print(f"   ✅ Generando DME...")
            from components.vista_diseno_mecanico import generar_resultados_dme
            componentes.append(html.H4("3. Diseño Mecánico"))
            componentes.append(html.Hr())
            try:
                dme_content = generar_resultados_dme(resultados["dme"], {})
                if dme_content:
                    if isinstance(dme_content, list):
                        componentes.extend(dme_content)
                    else:
                        componentes.append(dme_content)
                    print(f"   ✅ DME agregado")
                else:
                    print(f"   ⚠️ DME retornó None")
            except Exception as e:
                print(f"   ❌ Error en DME: {e}")
                componentes.append(dbc.Alert(f"Error en DME: {e}", color="warning"))
        
        # Árboles
        if "arboles" in calculos_activos and "arboles" in resultados and resultados["arboles"]:
            print(f"   ✅ Generando Árboles...")
            from components.vista_arboles_carga import generar_resultados_arboles
            componentes.append(html.H4("4. Árboles de Carga"))
            componentes.append(html.Hr())
            try:
                arboles_content = generar_resultados_arboles(resultados["arboles"], {})
                if arboles_content:
                    if isinstance(arboles_content, list):
                        componentes.extend(arboles_content)
                    else:
                        componentes.append(arboles_content)
                    print(f"   ✅ Árboles agregado")
                else:
                    print(f"   ⚠️ Árboles retornó None")
            except Exception as e:
                print(f"   ❌ Error en Árboles: {e}")
                componentes.append(dbc.Alert(f"Error en Árboles: {e}", color="warning"))
        
        # SPH
        if "sph" in calculos_activos and "sph" in resultados and resultados["sph"]:
            print(f"   ✅ Generando SPH...")
            from components.vista_seleccion_poste import _crear_area_resultados
            componentes.append(html.H4("5. Selección de Poste"))
            componentes.append(html.Hr())
            try:
                sph_content = _crear_area_resultados(resultados["sph"], {})
                if sph_content:
                    if isinstance(sph_content, list):
                        componentes.extend(sph_content)
                    else:
                        componentes.append(sph_content)
                    print(f"   ✅ SPH agregado")
                else:
                    print(f"   ⚠️ SPH retornó None")
            except Exception as e:
                print(f"   ❌ Error en SPH: {e}")
                componentes.append(dbc.Alert(f"Error en SPH: {e}", color="warning"))
        
        # Fundación
        if "fundacion" in calculos_activos and "fundacion" in resultados and resultados["fundacion"]:
            print(f"   ✅ Generando Fundación...")
            from components.vista_fundacion import generar_resultados_fundacion
            componentes.append(html.H4("6. Fundación"))
            componentes.append(html.Hr())
            try:
                # Omitir verificación de vigencia en contexto de familia
                fund_content = generar_resultados_fundacion(resultados["fundacion"], {}, omitir_vigencia=True)
                if fund_content:
                    if isinstance(fund_content, list):
                        componentes.extend(fund_content)
                    else:
                        componentes.append(fund_content)
                    print(f"   ✅ Fundación agregado")
                else:
                    print(f"   ⚠️ Fundación retornó None")
            except Exception as e:
                print(f"   ❌ Error en Fundación: {e}")
                componentes.append(dbc.Alert(f"Error en Fundación: {e}", color="warning"))
        
        # Costeo
        if "costeo" in calculos_activos and "costeo" in resultados and resultados["costeo"]:
            print(f"   ✅ Generando Costeo...")
            from components.vista_costeo import generar_resultados_costeo
            componentes.append(html.H4("7. Costeo"))
            componentes.append(html.Hr())
            try:
                cost_content = generar_resultados_costeo(resultados["costeo"], {})
                if cost_content:
                    if isinstance(cost_content, list):
                        componentes.extend(cost_content)
                    else:
                        componentes.append(cost_content)
                    print(f"   ✅ Costeo agregado")
                else:
                    print(f"   ⚠️ Costeo retornó None")
            except Exception as e:
                print(f"   ❌ Error en Costeo: {e}")
                componentes.append(dbc.Alert(f"Error en Costeo: {e}", color="warning"))
        
        # AEE
        if "aee" in calculos_activos and "aee" in resultados and resultados["aee"]:
            print(f"   ✅ Generando AEE...")
            from components.vista_analisis_estatico import generar_resultados_aee
            componentes.append(html.H4("8. Análisis Estático de Esfuerzos"))
            componentes.append(html.Hr())
            try:
                aee_content = generar_resultados_aee(resultados["aee"], {})
                if aee_content:
                    if isinstance(aee_content, list):
                        componentes.extend(aee_content)
                    else:
                        componentes.append(aee_content)
                    print(f"   ✅ AEE agregado")
                else:
                    print(f"   ⚠️ AEE retornó None")
            except Exception as e:
                print(f"   ❌ Error en AEE: {e}")
                componentes.append(dbc.Alert(f"Error en AEE: {e}", color="warning"))
        
        print(f"   📊 Total componentes generados: {len(componentes)}")
        
        if not componentes:
            return [dbc.Alert("No se generaron componentes de resultados", color="warning")]
        
        return componentes
        
    except Exception as e:
        import traceback
        error_msg = f"Error generando contenido: {str(e)}\n{traceback.format_exc()}"
        print(f"   ❌ {error_msg}")
        return dbc.Alert(error_msg, color="danger")

def _crear_contenido_costeo_familia(costeo_global: Dict, graficos_familia: Dict, resultados_estructuras: Dict = None):
    """Crear contenido para pestaña de costeo global de familia"""
    from dash import html, dcc
    import dash_bootstrap_components as dbc
    
    print(f"📊 DEBUG costeo_global: {costeo_global}")
    print(f"📊 DEBUG graficos_familia keys: {list(graficos_familia.keys()) if graficos_familia else 'None'}")
    
    if not costeo_global:
        return dbc.Alert("No hay datos de costeo disponibles", color="warning")
    
    costo_global_valor = costeo_global.get('costo_global', 0)
    costos_individuales = costeo_global.get('costos_individuales', {})
    costos_parciales = costeo_global.get('costos_parciales', {})
    
    print(f"💰 DEBUG: Costo global = {costo_global_valor}")
    print(f"💰 DEBUG: Costos individuales = {costos_individuales}")
    print(f"💰 DEBUG: Costos parciales = {costos_parciales}")
    
    # Extraer cantidades desde resultados_estructuras
    cantidades_por_titulo = {}
    if resultados_estructuras:
        for nombre_estr, datos in resultados_estructuras.items():
            titulo = datos.get("titulo", nombre_estr)
            cantidad = datos.get("cantidad", 1)
            cantidades_por_titulo[titulo] = cantidad
    
    componentes = [
        html.H4("Costeo Global de Familia"),
        html.Hr(),
        
        # Resumen de costos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Costo Global de Familia", className="card-title"),
                        html.H3(f"{costo_global_valor:,.2f} UM", className="text-primary")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Tabla de costos
        html.H5("Detalle de Costos por Estructura"),
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Estructura"),
                html.Th("Costo Individual [UM]"),
                html.Th("Cantidad"),
                html.Th("Costo Parcial [UM]")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(titulo),
                    html.Td(f"{costos_individuales.get(titulo, 0):,.2f}"),
                    html.Td(str(cantidades_por_titulo.get(titulo, 1))),
                    html.Td(f"{costos_parciales.get(titulo, 0):,.2f}")
                ]) for titulo in costos_individuales.keys()
            ])
        ], bordered=True, hover=True, className="mb-4"),
        
        # Gráficos
        html.H5("Análisis Comparativo"),
    ]
    
    # Gráfico de barras
    if "grafico_barras" in graficos_familia:
        componentes.append(
            dcc.Graph(
                figure=graficos_familia["grafico_barras"],
                config={'displayModeBar': True}
            )
        )
    
    # Gráfico de torta
    if "grafico_torta" in graficos_familia:
        componentes.append(
            dcc.Graph(
                figure=graficos_familia["grafico_torta"],
                config={'displayModeBar': True}
            )
        )
    
    return html.Div(componentes)