"""
Utilidades para cálculo de Vano Económico
REUTILIZA: ejecutar_calculo_familia_completa() de calcular_familia_logica_encadenada.py
"""

import copy
import math
from typing import Dict, List, Tuple
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc

def generar_lista_vanos(vano_min: float, vano_max: float, salto: float) -> List[float]:
    """Generar lista de vanos según especificación"""
    vanos = [vano_min]
    vano_actual = vano_min + salto
    
    while vano_actual < vano_max:
        vanos.append(vano_actual)
        vano_actual += salto
    
    vanos.append(vano_max)
    return vanos

def validar_familia_vano_economico(familia_data: Dict) -> Tuple[bool, str]:
    """Validar que familia tenga estructura correcta para vano económico"""
    estructuras = familia_data.get("estructuras", {})
    
    # Contar tipos
    count_suspension = 0
    count_rr = 0  # alpha=0
    count_terminal = 0
    
    for nombre, datos in estructuras.items():
        tipo = datos.get("TIPO_ESTRUCTURA", "")
        alpha = datos.get("alpha", 0)
        
        if "Suspensi" in tipo and "Recta" in tipo:
            count_suspension += 1
        elif "Terminal" in tipo:
            count_terminal += 1
        elif "Retenci" in tipo or "Angular" in tipo:
            if alpha == 0:
                count_rr += 1
    
    # Validar
    if count_suspension != 1:
        return False, f"Error: Existen {count_suspension} estructuras de tipo Suspensión (debe ser 1)"
    if count_rr != 1:
        return False, f"Error: Existen {count_rr} estructuras de tipo Retención con alpha=0 (debe ser 1)"
    if count_terminal != 1:
        return False, f"Error: Existen {count_terminal} estructuras de tipo Terminal (debe ser 1)"
    
    return True, "OK"

def calcular_cantidades(longtraza: float, l_vano: float, criterio_rr: str,
                       rr_cada_x_m: float, rr_cada_x_s: int, cant_rr_manual: int,
                       cant_ra: int) -> Dict[str, int]:
    """Calcular cantidades dinámicas según criterio"""
    cant_t = 2
    cant_s = math.ceil(longtraza / l_vano)
    
    if criterio_rr == "Distancia":
        cant_rr = math.ceil(longtraza / rr_cada_x_m) - 1 - cant_ra
    elif criterio_rr == "Suspensiones":
        cant_rr = math.ceil(cant_s / rr_cada_x_s) - cant_ra
    else:  # Manual
        cant_rr = cant_rr_manual
    
    cant_rr = max(0, cant_rr)  # No negativo
    
    return {
        "cant_T": cant_t,
        "cant_S": cant_s,
        "cant_RR": cant_rr,
        "cant_RA": cant_ra
    }

def obtener_cant_ra_familia(familia_data: Dict) -> int:
    """Obtener cantidad total de RA (alpha>0) en familia"""
    cant_ra = 0
    for nombre, datos in familia_data.get("estructuras", {}).items():
        tipo = datos.get("TIPO_ESTRUCTURA", "")
        alpha = datos.get("alpha", 0)
        if ("Retenci" in tipo or "Angular" in tipo) and alpha > 0:
            cant_ra += datos.get("Cantidad", 1)
    return cant_ra

def modificar_vano_y_cantidades_familia(familia_data: Dict, nuevo_vano: float,
                                        cantidades: Dict[str, int]) -> Dict:
    """Modificar L_vano y Cantidad en todas las estructuras de la familia"""
    familia_modificada = copy.deepcopy(familia_data)
    
    for nombre_estr, datos_estr in familia_modificada["estructuras"].items():
        # Modificar vano
        datos_estr["L_vano"] = nuevo_vano
        
        # Modificar cantidad según tipo
        tipo = datos_estr.get("TIPO_ESTRUCTURA", "")
        alpha = datos_estr.get("alpha", 0)
        
        if "Terminal" in tipo:
            datos_estr["Cantidad"] = cantidades["cant_T"]
        elif "Suspensi" in tipo and "Recta" in tipo:
            datos_estr["Cantidad"] = cantidades["cant_S"]
        elif ("Retenci" in tipo or "Angular" in tipo) and alpha == 0:
            datos_estr["Cantidad"] = cantidades["cant_RR"]
        # RA mantiene cantidad original
    
    return familia_modificada

def calcular_vano_economico_iterativo(nombre_familia: str, 
                                      vano_min: float, 
                                      vano_max: float, 
                                      salto: float,
                                      longtraza: float,
                                      criterio_rr: str,
                                      rr_cada_x_m: float,
                                      rr_cada_x_s: int,
                                      cant_rr_manual: int,
                                      generar_plots: bool = False) -> Dict:
    """
    Calcular costo de familia para cada vano con cantidades dinámicas
    REUTILIZA: ejecutar_calculo_familia_completa()
    """
    from utils.familia_manager import FamiliaManager
    from utils.calcular_familia_logica_encadenada import ejecutar_calculo_familia_completa
    
    # Cargar familia base
    familia_base = FamiliaManager.cargar_familia(nombre_familia)
    
    # Validar familia
    valido, mensaje = validar_familia_vano_economico(familia_base)
    if not valido:
        raise ValueError(mensaje)
    
    # Obtener cant_RA de familia
    cant_ra = obtener_cant_ra_familia(familia_base)
    
    # Generar lista de vanos
    vanos = generar_lista_vanos(vano_min, vano_max, salto)
    
    resultados_por_vano = {}
    
    for i, vano in enumerate(vanos):
        print(f"🔄 Calculando vano {vano}m ({i+1}/{len(vanos)})...")
        
        # Calcular cantidades para este vano
        cantidades = calcular_cantidades(
            longtraza, vano, criterio_rr, 
            rr_cada_x_m, rr_cada_x_s, cant_rr_manual, cant_ra
        )
        
        print(f"   Cantidades: T={cantidades['cant_T']}, S={cantidades['cant_S']}, "
              f"RR={cantidades['cant_RR']}, RA={cantidades['cant_RA']}")
        
        # Crear copia de familia con L_vano y Cantidad modificados
        familia_modificada = modificar_vano_y_cantidades_familia(
            familia_base, vano, cantidades
        )
        
        # REUTILIZAR función existente (con control de plots)
        resultado = ejecutar_calculo_familia_completa(familia_modificada, generar_plots=generar_plots)
        
        if resultado.get("exito"):
            costo_global = resultado["costeo_global"]["costo_global"]
            resultados_por_vano[vano] = {
                "costo_global": costo_global,
                "costeo_detalle": resultado["costeo_global"],
                "cantidades": cantidades,
                "familia_modificada": familia_modificada  # Guardar familia para obtener alpha
            }
            print(f"✅ Vano {vano}m: {costo_global:.2f} UM")
        else:
            print(f"❌ Error en vano {vano}m")
    
    return {
        "vanos": vanos,
        "resultados": resultados_por_vano,
        "familia_nombre": nombre_familia,
        "longtraza": longtraza,
        "criterio_rr": criterio_rr
    }

def generar_grafico_curva_vano_economico(resultados: Dict) -> go.Figure:
    """Generar gráfico de curva vano vs costo"""
    import numpy as np
    
    vanos = resultados["vanos"]
    costos = [resultados["resultados"][v]["costo_global"] for v in vanos]
    
    fig = go.Figure()
    
    # Curva con línea
    fig.add_trace(go.Scatter(
        x=vanos, y=costos,
        mode='lines+markers',
        name='Costo Total',
        line=dict(color='blue', width=3),
        marker=dict(size=10, color='red')
    ))
    
    # Encontrar vano óptimo (mínimo costo)
    idx_min = costos.index(min(costos))
    vano_optimo = vanos[idx_min]
    costo_optimo = costos[idx_min]
    
    # Marcar vano óptimo
    fig.add_trace(go.Scatter(
        x=[vano_optimo], y=[costo_optimo],
        mode='markers+text',
        name='Vano Óptimo',
        marker=dict(size=15, color='green', symbol='star'),
        text=[f'Óptimo: {vano_optimo}m'],
        textposition='top center'
    ))
    
    fig.update_layout(
        title="Curva de Vano Económico",
        xaxis_title="Vano [m]",
        yaxis_title="Costo Total Familia [UM]",
        hovermode='x unified'
    )
    
    return fig

def generar_grafico_barras_apiladas(resultados: Dict) -> go.Figure:
    """Generar gráfico de barras apiladas por estructura"""
    vanos = resultados["vanos"]
    
    # Extraer costos por estructura para cada vano
    estructuras_nombres = set()
    for vano in vanos:
        detalle = resultados["resultados"][vano]["costeo_detalle"]
        estructuras_nombres.update(detalle["costos_parciales"].keys())
    
    fig = go.Figure()
    
    for estructura in estructuras_nombres:
        costos_estructura = []
        for vano in vanos:
            detalle = resultados["resultados"][vano]["costeo_detalle"]
            costo = detalle["costos_parciales"].get(estructura, 0)
            costos_estructura.append(costo)
        
        fig.add_trace(go.Bar(
            name=estructura,
            x=vanos,
            y=costos_estructura
        ))
    
    fig.update_layout(
        barmode='stack',
        title="Distribución de Costos por Estructura y Vano",
        xaxis_title="Vano [m]",
        yaxis_title="Costo [UM]"
    )
    
    return fig

def _calcular_costo_tipo(resultado_vano: Dict, tipo: str) -> float:
    """Calcular costo parcial por tipo de estructura (costo individual * cantidad)"""
    costos_parciales = resultado_vano["costeo_detalle"]["costos_parciales"]
    familia = resultado_vano["familia_modificada"]["estructuras"]
    
    # Crear mapeo de TITULO a clave de estructura
    titulo_a_clave = {}
    for clave, datos in familia.items():
        titulo = datos.get("TITULO", "")
        if titulo:
            titulo_a_clave[titulo] = clave
    
    costo_total = 0.0
    for nombre_estr, costo in costos_parciales.items():
        # Buscar clave real usando TITULO
        clave_real = titulo_a_clave.get(nombre_estr, nombre_estr)
        
        if clave_real not in familia:
            continue
            
        tipo_estr = familia[clave_real].get("TIPO_ESTRUCTURA", "")
        alpha = familia[clave_real].get("alpha", 0)
        
        if tipo == "S" and "Suspensi" in tipo_estr:
            costo_total += costo
        elif tipo == "RR" and "Retenci" in tipo_estr and alpha == 0:
            costo_total += costo
        elif tipo == "RA" and ("Retenci" in tipo_estr or "Angular" in tipo_estr) and alpha > 0:
            costo_total += costo
        elif tipo == "T" and "Terminal" in tipo_estr:
            costo_total += costo
    
    return costo_total

def _calcular_costo_individual(resultado_vano: Dict, tipo: str) -> float:
    """Calcular costo individual (unitario) por tipo de estructura"""
    costos_parciales = resultado_vano["costeo_detalle"]["costos_parciales"]
    familia = resultado_vano["familia_modificada"]["estructuras"]
    
    # Crear mapeo de TITULO a clave de estructura
    titulo_a_clave = {}
    for clave, datos in familia.items():
        titulo = datos.get("TITULO", "")
        if titulo:
            titulo_a_clave[titulo] = clave
    
    costo_individual = 0.0
    for nombre_estr, costo in costos_parciales.items():
        # Buscar clave real usando TITULO
        clave_real = titulo_a_clave.get(nombre_estr, nombre_estr)
        
        if clave_real not in familia:
            continue
            
        tipo_estr = familia[clave_real].get("TIPO_ESTRUCTURA", "")
        alpha = familia[clave_real].get("alpha", 0)
        cantidad = familia[clave_real].get("Cantidad", 1)
        
        if cantidad > 0:
            costo_unit = costo / cantidad
        else:
            costo_unit = 0.0
        
        if tipo == "S" and "Suspensi" in tipo_estr:
            costo_individual = costo_unit
            break
        elif tipo == "RR" and "Retenci" in tipo_estr and alpha == 0:
            costo_individual = costo_unit
            break
        elif tipo == "RA" and ("Retenci" in tipo_estr or "Angular" in tipo_estr) and alpha > 0:
            costo_individual = costo_unit
            break
        elif tipo == "T" and "Terminal" in tipo_estr:
            costo_individual = costo_unit
            break
    
    return costo_individual

def generar_vista_resultados_vano_economico(resultados: Dict) -> html.Div:
    """Generar vista de resultados de vano económico"""
    
    if not resultados or not resultados.get("resultados"):
        return dbc.Alert("No hay resultados para mostrar", color="warning")
    
    vanos = resultados["vanos"]
    costos = [resultados["resultados"][v]["costo_global"] for v in vanos]
    
    # Encontrar vano óptimo
    idx_min = costos.index(min(costos))
    vano_optimo = vanos[idx_min]
    costo_optimo = costos[idx_min]
    
    # Generar gráficos
    fig_curva = generar_grafico_curva_vano_economico(resultados)
    fig_barras = generar_grafico_barras_apiladas(resultados)
    
    return html.Div([
        # Resumen
        dbc.Card([
            dbc.CardHeader(html.H5("Resumen de Vano Económico")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("Vano Óptimo:", className="text-muted"),
                        html.H3(f"{vano_optimo} m", className="text-success")
                    ], width=4),
                    dbc.Col([
                        html.H6("Costo Óptimo:", className="text-muted"),
                        html.H3(f"{costo_optimo:,.2f} UM", className="text-primary")
                    ], width=4),
                    dbc.Col([
                        html.H6("Vanos Analizados:", className="text-muted"),
                        html.H3(f"{len(vanos)}", className="text-info")
                    ], width=4)
                ])
            ])
        ], className="mb-4"),
        
        # Gráfico de curva
        html.H5("Curva de Vano Económico"),
        dcc.Graph(figure=fig_curva, config={'displayModeBar': True}),
        
        html.Hr(),
        
        # Gráfico de barras apiladas
        html.H5("Distribución de Costos por Estructura"),
        dcc.Graph(figure=fig_barras, config={'displayModeBar': True}),
        
        html.Hr(),
        
        # Tabla de resultados
        html.H5("Tabla de Resultados"),
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Vano [m]"),
                html.Th("Cant. S"),
                html.Th("Cant. RR"),
                html.Th("Costo Ind. S [UM]"),
                html.Th("Costo Ind. RR [UM]"),
                html.Th("Costo Ind. RA [UM]"),
                html.Th("Costo Ind. T [UM]"),
                html.Th("Costo S [UM]"),
                html.Th("Costo RR [UM]"),
                html.Th("Costo RA [UM]"),
                html.Th("Costo T [UM]"),
                html.Th("Costo Total [UM]"),
                html.Th("Diferencia vs Óptimo [%]")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(f"{vano:.0f}", style={"fontWeight": "bold"} if vano == vano_optimo else {}),
                    html.Td(f"{resultados['resultados'][vano]['cantidades']['cant_S']}"),
                    html.Td(f"{resultados['resultados'][vano]['cantidades']['cant_RR']}"),
                    html.Td(f"{_calcular_costo_individual(resultados['resultados'][vano], 'S'):,.2f}"),
                    html.Td(f"{_calcular_costo_individual(resultados['resultados'][vano], 'RR'):,.2f}"),
                    html.Td(f"{_calcular_costo_individual(resultados['resultados'][vano], 'RA'):,.2f}"),
                    html.Td(f"{_calcular_costo_individual(resultados['resultados'][vano], 'T'):,.2f}"),
                    html.Td(f"{_calcular_costo_tipo(resultados['resultados'][vano], 'S'):,.2f}"),
                    html.Td(f"{_calcular_costo_tipo(resultados['resultados'][vano], 'RR'):,.2f}"),
                    html.Td(f"{_calcular_costo_tipo(resultados['resultados'][vano], 'RA'):,.2f}"),
                    html.Td(f"{_calcular_costo_tipo(resultados['resultados'][vano], 'T'):,.2f}"),
                    html.Td(f"{resultados['resultados'][vano]['costo_global']:,.2f}",
                           style={"color": "green", "fontWeight": "bold"} if vano == vano_optimo else {}),
                    html.Td(f"{((resultados['resultados'][vano]['costo_global'] - costo_optimo) / costo_optimo * 100):+.2f}%")
                ]) for vano in vanos
            ])
        ], bordered=True, hover=True, striped=True),
        
        html.Hr(),
        
        # Botón descargar HTML
        dbc.Button("Descargar HTML", id="vano-economico-btn-descargar-html", color="success", className="mt-3")
    ])
