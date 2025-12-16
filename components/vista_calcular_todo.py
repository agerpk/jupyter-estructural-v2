"""Vista para Calcular Todo - Carga modular de cachés"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.calculo_cache import CalculoCache


def crear_placeholder(titulo):
    """Crea un placeholder para sección sin cálculo"""
    return dbc.Alert(
        f"⚠️ {titulo}: No se realizó cálculo de esta sección.",
        color="secondary",
        className="mb-3"
    )


def generar_resultados_cmc_lista(calculo_guardado, estructura_actual):
    """Genera resultados CMC como lista (sin envolver en html.Div)"""
    import pandas as pd
    from utils.view_helpers import ViewHelpers
    from utils.calculo_cache import CalculoCache
    
    try:
        vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
        resultados_html = [
            ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=vigente),
            html.H4("Resultados del Cálculo Mecánico", className="mt-4 mb-3"),
        ]
        
        if calculo_guardado.get('df_conductor_html'):
            df_conductor = pd.read_json(calculo_guardado['df_conductor_html'], orient='split').round(2)
            resultados_html.extend([
                html.H5("Conductor"),
                dbc.Table.from_dataframe(df_conductor, striped=True, bordered=True, hover=True, size="sm")
            ])
        
        if calculo_guardado.get('df_guardia1_html'):
            df_guardia1 = pd.read_json(calculo_guardado['df_guardia1_html'], orient='split').round(2)
            resultados_html.extend([
                html.H5("Cable de Guardia 1", className="mt-4"),
                dbc.Table.from_dataframe(df_guardia1, striped=True, bordered=True, hover=True, size="sm")
            ])
        
        if calculo_guardado.get('df_guardia2_html'):
            df_guardia2 = pd.read_json(calculo_guardado['df_guardia2_html'], orient='split').round(2)
            resultados_html.extend([
                html.H5("Cable de Guardia 2", className="mt-4"),
                dbc.Table.from_dataframe(df_guardia2, striped=True, bordered=True, hover=True, size="sm")
            ])
        
        if calculo_guardado.get('df_cargas_totales'):
            df_cargas = pd.DataFrame(calculo_guardado['df_cargas_totales'])
            resultados_html.extend(ViewHelpers.crear_tabla_desde_dataframe(df_cargas, "Lista Total de Cargas", responsive=True))
        
        if calculo_guardado.get('console_output'):
            resultados_html.append(html.Hr(className="mt-4"))
            resultados_html.extend(ViewHelpers.crear_pre_output(calculo_guardado['console_output'], titulo="Output de Cálculo", font_size='0.75rem'))
        
        hash_params = calculo_guardado.get('hash_parametros')
        if hash_params:
            resultados_html.append(html.H5("Gráficos de Flechas", className="mt-4"))
            
            fig_combinado_dict = ViewHelpers.cargar_figura_plotly_json(f"CMC_Combinado.{hash_params}.json")
            if fig_combinado_dict:
                resultados_html.append(html.H6("Conductor y Guardia", className="mt-3"))
                resultados_html.append(dcc.Graph(figure=fig_combinado_dict, config={'displayModeBar': True}))
            
            fig_conductor_dict = ViewHelpers.cargar_figura_plotly_json(f"CMC_Conductor.{hash_params}.json")
            if fig_conductor_dict:
                resultados_html.append(html.H6("Solo Conductor", className="mt-3"))
                resultados_html.append(dcc.Graph(figure=fig_conductor_dict, config={'displayModeBar': True}))
            
            fig_guardia_dict = ViewHelpers.cargar_figura_plotly_json(f"CMC_Guardia.{hash_params}.json")
            if fig_guardia_dict:
                resultados_html.append(html.H6("Solo Cable de Guardia 1", className="mt-3"))
                resultados_html.append(dcc.Graph(figure=fig_guardia_dict, config={'displayModeBar': True}))
            
            fig_guardia2_dict = ViewHelpers.cargar_figura_plotly_json(f"CMC_Guardia2.{hash_params}.json")
            if fig_guardia2_dict:
                resultados_html.append(html.H6("Solo Cable de Guardia 2", className="mt-3"))
                resultados_html.append(dcc.Graph(figure=fig_guardia2_dict, config={'displayModeBar': True}))
        
        return resultados_html
    except Exception as e:
        import traceback
        print(f"Error en generar_resultados_cmc_lista: {traceback.format_exc()}")
        return [dbc.Alert(f"Error cargando resultados: {str(e)}", color="warning")]


def cargar_resultados_modulares(estructura_actual):
    """Carga resultados desde cachés individuales con placeholders donde no existan"""
    if not estructura_actual:
        return [dbc.Alert("No hay estructura cargada", color="warning")]
    
    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
    componentes = []
    
    # 1. CMC
    calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
    if calculo_cmc:
        componentes.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
        componentes.extend(generar_resultados_cmc_lista(calculo_cmc, estructura_actual))
    else:
        componentes.append(crear_placeholder("1. CMC"))
    
    # 2. DGE
    calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
    if calculo_dge:
        from components.vista_diseno_geometrico import generar_resultados_dge
        componentes.extend([
            html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"),
            generar_resultados_dge(calculo_dge, estructura_actual)
        ])
    else:
        componentes.append(crear_placeholder("2. DGE"))
    
    # 3. DME
    calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
    if calculo_dme:
        from components.vista_diseno_mecanico import generar_resultados_dme
        componentes.extend([
            html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"),
            generar_resultados_dme(calculo_dme, estructura_actual)
        ])
    else:
        componentes.append(crear_placeholder("3. DME"))
    
    # 4. Árboles de Carga
    calculo_arboles = CalculoCache.cargar_calculo_arboles(nombre_estructura)
    if calculo_arboles:
        from components.vista_arboles_carga import generar_resultados_arboles
        componentes.extend([
            html.H3("4. ÁRBOLES DE CARGA", className="mt-4"),
            html.Div(generar_resultados_arboles(calculo_arboles, estructura_actual))
        ])
    else:
        componentes.append(crear_placeholder("4. Árboles de Carga"))
    
    # 5. SPH
    calculo_sph = CalculoCache.cargar_calculo_sph(nombre_estructura)
    if calculo_sph:
        from components.vista_seleccion_poste import _crear_area_resultados
        componentes.extend([
            html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"),
            html.Div(_crear_area_resultados(calculo_sph, estructura_actual))
        ])
    else:
        componentes.append(crear_placeholder("5. SPH"))
    
    return componentes


def crear_vista_calcular_todo(estructura_actual, calculo_guardado=None):
    """Vista para ejecutar todos los cálculos en secuencia"""
    
    return html.Div([
        dcc.Download(id="download-html-todo"),
        dbc.Card([
            dbc.CardHeader(html.H4("Calcular Todo - Ejecución Completa", className="mb-0")),
            dbc.CardBody([
                dbc.Alert([
                    html.H5("Secuencia de Cálculo:", className="alert-heading"),
                    html.P("Esta vista ejecutará automáticamente todos los cálculos en el siguiente orden:"),
                    html.Ol([
                        html.Li("Cálculo Mecánico de Cables (CMC)"),
                        html.Li("Diseño Geométrico de Estructura (DGE)"),
                        html.Li("Diseño Mecánico de Estructura (DME)"),
                        html.Li("Árboles de Carga"),
                        html.Li("Selección de Poste de Hormigón (SPH)")
                    ]),
                    html.P("Los resultados se mostrarán en orden a continuación.", className="mb-0")
                ], color="info", className="mb-4"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Ejecutar Cálculo Completo",
                            id="btn-calcular-todo",
                            color="success",
                            size="lg",
                            className="w-100"
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Button(
                            "Cargar desde Cache",
                            id="btn-cargar-cache-todo",
                            color="info",
                            size="lg",
                            className="w-100"
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Button(
                            "Descargar como HTML",
                            id="btn-descargar-html-todo",
                            color="primary",
                            size="lg",
                            className="w-100"
                        )
                    ], md=4)
                ], className="mb-4"),
                
                html.Hr(),
                
                # Área de resultados
                html.Div(id="output-calcular-todo", children=[
                    dbc.Alert("Presione un botón para comenzar", color="secondary")
                ])
            ])
        ])
    ])
