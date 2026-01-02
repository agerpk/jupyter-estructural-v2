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

def ejecutar_calculo_familia_completa(familia_data: Dict) -> Dict:
    """
    Ejecuta cálculo completo para toda la familia
    Retorna resultados por estructura y costeo global
    """
    nombre_familia = familia_data.get("nombre_familia", "familia")
    print(f"\n🚀 INICIANDO CÁLCULO FAMILIA: {nombre_familia}")
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
        
        # Ejecutar secuencia completa para esta estructura
        resultado_estr = _ejecutar_secuencia_estructura(datos_estr, titulo)
        
        if resultado_estr["exito"]:
            resultados_familia[nombre_estr] = {
                "titulo": titulo,
                "cantidad": cantidad,
                "resultados": resultado_estr["resultados"],
                "costo_individual": resultado_estr.get("costo_total", 0)
            }
            costos_individuales[titulo] = resultado_estr.get("costo_total", 0)
            print(f"✅ {titulo}: Costo individual = {resultado_estr.get('costo_total', 0)}")
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

def _ejecutar_secuencia_estructura(datos_estructura: Dict, titulo: str) -> Dict:
    """
    Ejecuta secuencia completa CMC>DGE>DME>Árboles>SPH>Fundación>Costeo
    para una estructura individual creando archivos temporales completos
    """
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
            from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
            resultado_cmc = ejecutar_calculo_cmc_automatico(datos_estructura, state)
            if resultado_cmc.get('exito'):
                resultados["cmc"] = CalculoCache.cargar_calculo_cmc(titulo)
                print(f"✅ CMC completado para {titulo}")
            else:
                return {"exito": False, "mensaje": f"Error CMC: {resultado_cmc.get('mensaje')}"}
            
            # 2. DGE
            from controllers.geometria_controller import ejecutar_calculo_dge
            resultado_dge = ejecutar_calculo_dge(datos_estructura, state)
            if resultado_dge.get('exito'):
                resultados["dge"] = CalculoCache.cargar_calculo_dge(titulo)
                print(f"✅ DGE completado para {titulo}")
            else:
                return {"exito": False, "mensaje": f"Error DGE: {resultado_dge.get('mensaje')}"}
            
            # 3. DME
            from controllers.ejecutar_calculos import ejecutar_calculo_dme
            resultado_dme = ejecutar_calculo_dme(datos_estructura, state)
            if resultado_dme.get('exito'):
                resultados["dme"] = CalculoCache.cargar_calculo_dme(titulo)
                print(f"✅ DME completado para {titulo}")
            else:
                return {"exito": False, "mensaje": f"Error DME: {resultado_dme.get('mensaje')}"}
            
            # 4. Árboles
            from controllers.ejecutar_calculos import ejecutar_calculo_arboles
            resultado_arboles = ejecutar_calculo_arboles(datos_estructura, state)
            if resultado_arboles.get('exito'):
                resultados["arboles"] = CalculoCache.cargar_calculo_arboles(titulo)
                print(f"✅ Árboles completado para {titulo}")
            else:
                return {"exito": False, "mensaje": f"Error Árboles: {resultado_arboles.get('mensaje')}"}
            
            # 5. SPH
            from controllers.ejecutar_calculos import ejecutar_calculo_sph
            resultado_sph = ejecutar_calculo_sph(datos_estructura, state)
            if resultado_sph.get('exito'):
                resultados["sph"] = CalculoCache.cargar_calculo_sph(titulo)
                print(f"✅ SPH completado para {titulo}")
            else:
                return {"exito": False, "mensaje": f"Error SPH: {resultado_sph.get('mensaje')}"}
            
            # 6. Fundación
            from controllers.ejecutar_calculos import ejecutar_calculo_fundacion
            resultado_fundacion = ejecutar_calculo_fundacion(datos_estructura, state)
            if resultado_fundacion.get('exito'):
                resultados["fundacion"] = CalculoCache.cargar_calculo_fund(titulo)
                print(f"✅ Fundación completado para {titulo}")
            else:
                return {"exito": False, "mensaje": f"Error Fundación: {resultado_fundacion.get('mensaje')}"}
            
            # 7. Costeo
            from controllers.ejecutar_calculos import ejecutar_calculo_costeo
            resultado_costeo = ejecutar_calculo_costeo(datos_estructura, state)
            if resultado_costeo.get('exito'):
                calculo_costeo = CalculoCache.cargar_calculo_costeo(titulo)
                resultados["costeo"] = calculo_costeo
                # Extraer costo total
                if calculo_costeo and "resultados" in calculo_costeo:
                    costo_total = calculo_costeo["resultados"].get("costo_total", 0)
                print(f"✅ Costeo completado para {titulo}: {costo_total}")
            else:
                return {"exito": False, "mensaje": f"Error Costeo: {resultado_costeo.get('mensaje')}"}
            
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
    
    fig_barras = go.Figure(data=[
        go.Bar(
            x=titulos_ordenados,
            y=[costos_individuales[t] for t in titulos_ordenados],
            name="Costo Individual"
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

def generar_vista_resultados_familia(resultados_familia: Dict) -> List:
    """Generar vista con pestañas por estructura"""
    from dash import html, dcc
    import dash_bootstrap_components as dbc
    
    if not resultados_familia.get("resultados_estructuras"):
        return [dbc.Alert("No hay resultados para mostrar", color="warning")]
    
    # Crear pestañas con contenido
    pestanas = []
    
    for nombre_estr, datos in resultados_familia["resultados_estructuras"].items():
        titulo = datos["titulo"]
        
        # Contenido de pestaña
        if "error" in datos:
            contenido = dbc.Alert(f"Error: {datos['error']}", color="danger")
        else:
            contenido = _crear_contenido_estructura(datos)
        
        # Pestaña con contenido
        pestanas.append(dbc.Tab(contenido, label=titulo))
    
    # Agregar pestaña de costeo global
    contenido_costeo = _crear_contenido_costeo_familia(
        resultados_familia.get("costeo_global", {}),
        resultados_familia.get("graficos_familia", {})
    )
    pestanas.append(dbc.Tab(contenido_costeo, label="Costeo Familia"))
    
    return [dbc.Tabs(pestanas)]

def _crear_contenido_estructura(datos_estructura: Dict):
    """Crear contenido para pestaña de estructura individual"""
    from dash import html
    from components.vista_calcular_todo import generar_resultados_cmc_lista
    from components.vista_diseno_geometrico import generar_resultados_dge
    from components.vista_diseno_mecanico import generar_resultados_dme
    from components.vista_arboles_carga import generar_resultados_arboles
    from components.vista_seleccion_poste import _crear_area_resultados
    from components.vista_fundacion import generar_resultados_fundacion
    from components.vista_costeo import generar_resultados_costeo
    from dash import html
    
    resultados = datos_estructura["resultados"]
    componentes = []
    
    # CMC
    if "cmc" in resultados and resultados["cmc"]:
        componentes.append(html.H4("Cálculo Mecánico de Cables"))
        cmc_lista = generar_resultados_cmc_lista(resultados["cmc"], {}, mostrar_alerta_cache=False)
        componentes.extend(cmc_lista)
    
    # DGE
    if "dge" in resultados and resultados["dge"]:
        componentes.append(html.H4("Diseño Geométrico"))
        componentes.append(generar_resultados_dge(resultados["dge"], {}, mostrar_alerta_cache=False))
    
    # DME
    if "dme" in resultados and resultados["dme"]:
        componentes.append(html.H4("Diseño Mecánico"))
        componentes.append(generar_resultados_dme(resultados["dme"], {}, mostrar_alerta_cache=False))
    
    # Árboles
    if "arboles" in resultados and resultados["arboles"]:
        componentes.append(html.H4("Árboles de Carga"))
        componentes.append(html.Div(generar_resultados_arboles(resultados["arboles"], {}, mostrar_alerta_cache=False)))
    
    # SPH
    if "sph" in resultados and resultados["sph"]:
        componentes.append(html.H4("Selección de Poste"))
        componentes.append(html.Div(_crear_area_resultados(resultados["sph"], {})))
    
    # Fundación
    if "fundacion" in resultados and resultados["fundacion"]:
        componentes.append(html.H4("Fundación"))
        fund_result = generar_resultados_fundacion(resultados["fundacion"], {})
        if isinstance(fund_result, list):
            componentes.extend(fund_result)
        else:
            componentes.append(fund_result)
    
    # Costeo
    if "costeo" in resultados and resultados["costeo"]:
        componentes.append(html.H4("Costeo"))
        cost_result = generar_resultados_costeo(resultados["costeo"], {})
        if isinstance(cost_result, list):
            componentes.extend(cost_result)
        else:
            componentes.append(cost_result)
    
    return html.Div(componentes)

def _crear_contenido_costeo_familia(costeo_global: Dict, graficos_familia: Dict):
    """Crear contenido para pestaña de costeo global de familia"""
    from dash import html, dcc
    import dash_bootstrap_components as dbc
    
    if not costeo_global:
        return dbc.Alert("No hay datos de costeo disponibles", color="warning")
    
    componentes = [
        html.H4("Costeo Global de Familia"),
        html.Hr(),
        
        # Resumen de costos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Costo Global de Familia", className="card-title"),
                        html.H3(f"{costeo_global.get('costo_global', 0):,.2f} UM", 
                               className="text-primary")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
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