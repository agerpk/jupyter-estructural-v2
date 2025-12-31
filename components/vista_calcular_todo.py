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


def generar_resultados_cmc_lista(calculo_guardado, estructura_actual, mostrar_alerta_cache=False):
    """Genera resultados CMC como lista (sin envolver en html.Div)"""
    import pandas as pd
    from utils.view_helpers import ViewHelpers
    from utils.calculo_cache import CalculoCache
    from io import StringIO
    
    try:
        vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
        resultados_html = []
        
        if mostrar_alerta_cache:
            resultados_html.append(ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=vigente))
        
        resultados_html.append(html.H4("Resultados del Cálculo Mecánico", className="mt-4 mb-3"))
        
        if calculo_guardado.get('df_conductor_html'):
            df_conductor = pd.read_json(StringIO(calculo_guardado['df_conductor_html']), orient='split').round(2)
            resultados_html.extend([
                html.H5("Conductor"),
                dbc.Table.from_dataframe(df_conductor, striped=True, bordered=True, hover=True, size="sm")
            ])
        
        if calculo_guardado.get('df_guardia1_html'):
            df_guardia1 = pd.read_json(StringIO(calculo_guardado['df_guardia1_html']), orient='split').round(2)
            resultados_html.extend([
                html.H5("Cable de Guardia 1", className="mt-4"),
                dbc.Table.from_dataframe(df_guardia1, striped=True, bordered=True, hover=True, size="sm")
            ])
        
        if calculo_guardado.get('df_guardia2_html'):
            df_guardia2 = pd.read_json(StringIO(calculo_guardado['df_guardia2_html']), orient='split').round(2)
            resultados_html.extend([
                html.H5("Cable de Guardia 2", className="mt-4"),
                dbc.Table.from_dataframe(df_guardia2, striped=True, bordered=True, hover=True, size="sm")
            ])
        
        if calculo_guardado.get('df_cargas_totales'):
            df_cargas = pd.DataFrame(calculo_guardado['df_cargas_totales'])
            for comp in ViewHelpers.crear_tabla_desde_dataframe(df_cargas, "Lista Total de Cargas", responsive=True):
                resultados_html.append(comp)
        
        if calculo_guardado.get('console_output'):
            resultados_html.append(html.Hr(className="mt-4"))
            for comp in ViewHelpers.crear_pre_output(calculo_guardado['console_output'], titulo="Output de Cálculo", font_size='0.75rem'):
                resultados_html.append(comp)
        
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
        print("❌ No hay estructura cargada")
        return [dbc.Alert("No hay estructura cargada", color="warning")]
    
    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
    print(f"📂 Cargando resultados modulares para: {nombre_estructura}")
    componentes = []
    
    # 1. CMC
    print("🔍 Verificando cache CMC...")
    calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
    if calculo_cmc:
        print("✅ Cache CMC encontrado")
        componentes.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
        try:
            lista_cmc = generar_resultados_cmc_lista(calculo_cmc, estructura_actual, mostrar_alerta_cache=True)
            print(f"🔍 DEBUG CMC: Tipo de lista_cmc: {type(lista_cmc)}, Longitud: {len(lista_cmc)}")
            for i, comp in enumerate(lista_cmc[:3]):  # Solo primeros 3 para debug
                print(f"   CMC[{i}]: {type(comp).__name__}")
            componentes.extend(lista_cmc)
            print(f"✅ CMC: {len(lista_cmc)} componentes agregados")
        except Exception as e:
            print(f"❌ Error generando CMC: {e}")
            componentes.append(dbc.Alert(f"Error cargando CMC: {str(e)}", color="danger"))
    else:
        print("❌ Cache CMC no encontrado")
        componentes.append(crear_placeholder("1. CMC"))
    
    # 2. DGE
    print("🔍 Verificando cache DGE...")
    calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
    if calculo_dge:
        print("✅ Cache DGE encontrado")
        from components.vista_diseno_geometrico import generar_resultados_dge
        componentes.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
        try:
            resultado_dge = generar_resultados_dge(calculo_dge, estructura_actual, mostrar_alerta_cache=True)
            print(f"🔍 DEBUG DGE: Tipo de resultado_dge: {type(resultado_dge)}")
            if isinstance(resultado_dge, list):
                print(f"   DGE es lista con {len(resultado_dge)} elementos")
                for i, comp in enumerate(resultado_dge[:3]):  # Solo primeros 3 para debug
                    print(f"   DGE[{i}]: {type(comp).__name__}")
                componentes.extend(resultado_dge)
                print(f"✅ DGE: {len(resultado_dge)} componentes agregados")
            else:
                print(f"   DGE es {type(resultado_dge).__name__}")
                componentes.append(resultado_dge)
                print("✅ DGE: 1 componente agregado")
        except Exception as e:
            import traceback
            print(f"❌ Error cargando DGE: {traceback.format_exc()}")
            componentes.append(dbc.Alert(f"Error cargando DGE: {str(e)}", color="danger"))
    else:
        print("❌ Cache DGE no encontrado")
        componentes.append(crear_placeholder("2. DGE"))
    
    # 3. DME
    print("🔍 Verificando cache DME...")
    calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
    if calculo_dme:
        print("✅ Cache DME encontrado")
        from components.vista_diseno_mecanico import generar_resultados_dme
        componentes.append(html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"))
        try:
            resultado_dme = generar_resultados_dme(calculo_dme, estructura_actual, mostrar_alerta_cache=True)
            print(f"🔍 DEBUG DME: Tipo de resultado_dme: {type(resultado_dme).__name__}")
            componentes.append(resultado_dme)
            print("✅ DME: 1 componente agregado")
        except Exception as e:
            import traceback
            print(f"❌ Error cargando DME: {traceback.format_exc()}")
            componentes.append(dbc.Alert(f"Error cargando DME: {str(e)}", color="danger"))
    else:
        print("❌ Cache DME no encontrado")
        componentes.append(crear_placeholder("3. DME"))
    
    # 4. Árboles de Carga
    print("🔍 Verificando cache Árboles...")
    calculo_arboles = CalculoCache.cargar_calculo_arboles(nombre_estructura)
    if calculo_arboles:
        print("✅ Cache Árboles encontrado")
        from components.vista_arboles_carga import generar_resultados_arboles
        componentes.append(html.H3("4. ÁRBOLES DE CARGA", className="mt-4"))
        try:
            resultado_arboles = generar_resultados_arboles(calculo_arboles, estructura_actual, mostrar_alerta_cache=True)
            print(f"🔍 DEBUG Árboles: Tipo de resultado_arboles: {type(resultado_arboles)}")
            if isinstance(resultado_arboles, list):
                print(f"   Árboles es lista con {len(resultado_arboles)} elementos")
                componentes.extend(resultado_arboles)
                print(f"✅ Árboles: {len(resultado_arboles)} componentes agregados")
            else:
                print(f"   Árboles es {type(resultado_arboles).__name__}")
                componentes.append(resultado_arboles)
                print("✅ Árboles: 1 componente agregado")
        except Exception as e:
            import traceback
            print(f"❌ Error cargando Árboles: {traceback.format_exc()}")
            componentes.append(dbc.Alert(f"Error cargando Árboles: {str(e)}", color="danger"))
    else:
        print("❌ Cache Árboles no encontrado")
        componentes.append(crear_placeholder("4. Árboles de Carga"))
    
    # 5. SPH
    print("🔍 Verificando cache SPH...")
    calculo_sph = CalculoCache.cargar_calculo_sph(nombre_estructura)
    if calculo_sph:
        print("✅ Cache SPH encontrado")
        from components.vista_seleccion_poste import _crear_area_resultados
        componentes.append(html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"))
        try:
            resultado_sph = _crear_area_resultados(calculo_sph, estructura_actual)
            print(f"🔍 DEBUG SPH: Tipo de resultado_sph: {type(resultado_sph).__name__}")
            # Si SPH retorna una lista, extenderla; si no, agregarla
            if isinstance(resultado_sph, list):
                print(f"   SPH es lista con {len(resultado_sph)} elementos")
                componentes.extend(resultado_sph)
                print(f"✅ SPH: {len(resultado_sph)} componentes agregados")
            else:
                componentes.append(resultado_sph)
                print("✅ SPH: 1 componente agregado")
        except Exception as e:
            import traceback
            print(f"❌ Error cargando SPH: {traceback.format_exc()}")
            componentes.append(dbc.Alert(f"Error cargando SPH: {str(e)}", color="danger"))
    else:
        print("❌ Cache SPH no encontrado")
        componentes.append(crear_placeholder("5. SPH"))
    
    # 6. Fundación
    print("🔍 Verificando cache Fundación...")
    calculo_fundacion = CalculoCache.cargar_calculo_fund(nombre_estructura)
    if calculo_fundacion:
        print("✅ Cache Fundación encontrado")
        from components.vista_fundacion import generar_resultados_fundacion
        componentes.append(html.H3("6. FUNDACIÓN", className="mt-4"))
        try:
            resultado_fundacion = generar_resultados_fundacion(calculo_fundacion, estructura_actual)
            print(f"🔍 DEBUG Fundación: Tipo de resultado_fundacion: {type(resultado_fundacion)}")
            if isinstance(resultado_fundacion, list):
                print(f"   Fundación es lista con {len(resultado_fundacion)} elementos")
                componentes.extend(resultado_fundacion)
                print(f"✅ Fundación: {len(resultado_fundacion)} componentes agregados")
            else:
                print(f"   Fundación es {type(resultado_fundacion).__name__}")
                componentes.append(resultado_fundacion)
                print("✅ Fundación: 1 componente agregado")
        except Exception as e:
            import traceback
            print(f"❌ Error cargando Fundación: {traceback.format_exc()}")
            componentes.append(dbc.Alert(f"Error cargando Fundación: {str(e)}", color="danger"))
    else:
        print("❌ Cache Fundación no encontrado")
        componentes.append(crear_placeholder("6. Fundación"))
    
    # 7. Costeo
    print("🔍 Verificando cache Costeo...")
    calculo_costeo = CalculoCache.cargar_calculo_costeo(nombre_estructura)
    if calculo_costeo:
        print("✅ Cache Costeo encontrado")
        from components.vista_costeo import generar_resultados_costeo
        componentes.append(html.H3("7. COSTEO", className="mt-4"))
        try:
            resultado_costeo = generar_resultados_costeo(calculo_costeo, estructura_actual, mostrar_alerta_cache=True)
            print(f"🔍 DEBUG Costeo: Tipo de resultado_costeo: {type(resultado_costeo)}")
            if isinstance(resultado_costeo, list):
                print(f"   Costeo es lista con {len(resultado_costeo)} elementos")
                componentes.extend(resultado_costeo)
                print(f"✅ Costeo: {len(resultado_costeo)} componentes agregados")
            else:
                print(f"   Costeo es {type(resultado_costeo).__name__}")
                componentes.append(resultado_costeo)
                print("✅ Costeo: 1 componente agregado")
        except Exception as e:
            import traceback
            print(f"❌ Error cargando Costeo: {traceback.format_exc()}")
            componentes.append(dbc.Alert(f"Error cargando Costeo: {str(e)}", color="danger"))
    else:
        print("❌ Cache Costeo no encontrado")
        componentes.append(crear_placeholder("7. Costeo"))
    
    print(f"✅ Carga modular completada: {len(componentes)} componentes totales")
    print(f"🔍 DEBUG FINAL: Tipos de componentes en lista:")
    for i, comp in enumerate(componentes[:10]):  # Solo primeros 10 para debug
        print(f"   [{i}]: {type(comp).__name__}")
    return componentes


def crear_vista_calcular_todo(estructura_actual, calculo_guardado=None):
    """Vista para ejecutar todos los cálculos en secuencia"""
    
    # Auto-cargar cache si hay estructura disponible
    contenido_inicial = [dbc.Alert("Presione un botón para comenzar", color="secondary")]
    if estructura_actual:
        try:
            print(f"🔄 VISTA: Iniciando auto-carga de cache para {estructura_actual.get('TITULO', 'N/A')}")
            contenido_inicial = cargar_resultados_modulares(estructura_actual)
            print(f"✅ VISTA: Auto-carga completada: {len(contenido_inicial)} componentes")
        except Exception as e:
            print(f"❌ VISTA: Error en auto-carga: {e}")
            contenido_inicial = [dbc.Alert(f"Error cargando cache: {str(e)}", color="warning")]
    else:
        print("⚠️ VISTA: No hay estructura_actual, mostrando placeholder")
    
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
                        html.Li("Selección de Poste de Hormigón (SPH)"),
                        html.Li("Fundación"),
                        html.Li("Costeo")
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
                html.Div(id="output-calcular-todo", children=contenido_inicial)
            ])
        ])
    ])
