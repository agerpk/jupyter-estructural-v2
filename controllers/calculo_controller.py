"""Controlador de cálculos AEA"""

import dash
from dash import html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from models.app_state import AppState
from utils.plot_flechas import crear_grafico_flechas


def register_callbacks(app):
    """Registrar callbacks de cálculos"""
    
    state = AppState()
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("menu-crear-cables", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def crear_cables_callback(n_clicks, estructura_actual):
        if not estructura_actual:
            return True, "Error", "No hay estructura cargada", "danger", "danger"
        
        resultado = state.calculo_objetos.crear_objetos_cable(estructura_actual)
        
        if resultado["exito"]:
            mensaje = f"{resultado['mensaje']}\n✓ Conductor: {resultado['conductor']}\n✓ Guardia: {resultado['guardia']}"
            return True, "Éxito", mensaje, "success", "success"
        else:
            return True, "Error", resultado["mensaje"], "danger", "danger"
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("menu-crear-cadena", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def crear_cadena_callback(n_clicks, estructura_actual):
        if not estructura_actual:
            return True, "Error", "No hay estructura cargada", "danger", "danger"
        
        resultado = state.calculo_objetos.crear_objetos_cadena(estructura_actual)
        
        if resultado["exito"]:
            return True, "Éxito", resultado["mensaje"], "success", "success"
        else:
            return True, "Error", resultado["mensaje"], "danger", "danger"
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("menu-crear-estructura-obj", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def crear_estructura_obj_callback(n_clicks, estructura_actual):
        if not estructura_actual:
            return True, "Error", "No hay estructura cargada", "danger", "danger"
        
        resultado = state.calculo_objetos.crear_objetos_estructura(estructura_actual)
        
        if resultado["exito"]:
            return True, "Éxito", resultado["mensaje"], "success", "success"
        else:
            return True, "Error", resultado["mensaje"], "danger", "danger"
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("menu-crear-todos-objetos", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def crear_todos_objetos_callback(n_clicks, estructura_actual):
        if not estructura_actual:
            return True, "Error", "No hay estructura cargada", "danger", "danger"
        
        resultado = state.calculo_objetos.crear_todos_objetos(estructura_actual)
        
        if resultado["exito"]:
            return True, "Éxito", resultado["mensaje"], "success", "success"
        else:
            return True, "Error", resultado["mensaje"], "danger", "danger"
    

    
    # Callback eliminado - ahora manejado por parametros_controller.py
    
    @app.callback(
        Output("resultados-cmc", "children", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-calcular-cmc", "n_clicks"),
        State("param-L_vano", "value"),
        State("slider-alpha", "value"),
        State("slider-theta", "value"),
        State("param-Vmax", "value"),
        State("param-Vmed", "value"),
        State("slider-t_hielo", "value"),
        State("param-VANO_DESNIVELADO", "value"),
        State("param-H_PIQANTERIOR", "value"),
        State("param-H_PIQPOSTERIOR", "value"),
        State("slider-SALTO_PORCENTUAL", "value"),
        State("slider-PASO_AFINADO", "value"),
        State("param-OBJ_CONDUCTOR", "value"),
        State("param-OBJ_GUARDIA", "value"),
        State("slider-RELFLECHA_MAX_GUARDIA", "value"),
        State("param-RELFLECHA_SIN_VIENTO", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def calcular_cmc(n_clicks, L_vano, alpha, theta, Vmax, Vmed, t_hielo,
                    VANO_DESNIVELADO, H_PIQANTERIOR, H_PIQPOSTERIOR,
                    SALTO_PORCENTUAL, PASO_AFINADO, OBJ_CONDUCTOR, OBJ_GUARDIA,
                    RELFLECHA_MAX_GUARDIA, RELFLECHA_SIN_VIENTO, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Guardar parámetros antes de calcular
            estructura_actualizada = estructura_actual.copy()
            estructura_actualizada.update({
                "L_vano": float(L_vano),
                "alpha": float(alpha),
                "theta": float(theta),
                "Vmax": float(Vmax),
                "Vmed": float(Vmed),
                "t_hielo": float(t_hielo),
                "VANO_DESNIVELADO": bool(VANO_DESNIVELADO),
                "H_PIQANTERIOR": float(H_PIQANTERIOR) if H_PIQANTERIOR else 0.0,
                "H_PIQPOSTERIOR": float(H_PIQPOSTERIOR) if H_PIQPOSTERIOR else 0.0,
                "SALTO_PORCENTUAL": float(SALTO_PORCENTUAL),
                "PASO_AFINADO": float(PASO_AFINADO),
                "OBJ_CONDUCTOR": OBJ_CONDUCTOR,
                "OBJ_GUARDIA": OBJ_GUARDIA,
                "RELFLECHA_MAX_GUARDIA": float(RELFLECHA_MAX_GUARDIA),
                "RELFLECHA_SIN_VIENTO": bool(RELFLECHA_SIN_VIENTO)
            })
            
            estructura_actual = estructura_actualizada
            resultado_objetos = state.calculo_objetos.crear_todos_objetos(estructura_actual)
            if not resultado_objetos["exito"]:
                return dash.no_update, True, "Error", resultado_objetos["mensaje"], "danger", "danger"
            
            # Usar estados climáticos desde estructura_actual (guardados por modal)
            estados_climaticos = estructura_actual.get("estados_climaticos")
            if not estados_climaticos:
                return dash.no_update, True, "Error", "Debe definir estados climáticos usando el botón 'Editar Estados Climaticos y Restricciones'", "danger", "danger"
            
            # Construir restricciones desde estados_climaticos
            restricciones_dict = {
                "conductor": {"tension_max_porcentaje": {}},
                "guardia": {"tension_max_porcentaje": {}, "relflecha_max": float(RELFLECHA_MAX_GUARDIA)}
            }
            for estado_id, datos in estados_climaticos.items():
                restricciones_dict["conductor"]["tension_max_porcentaje"][estado_id] = datos.get("restriccion_conductor", 0.25)
                restricciones_dict["guardia"]["tension_max_porcentaje"][estado_id] = datos.get("restriccion_guardia", 0.7)
            
            params = {
                "L_vano": float(L_vano),
                "alpha": float(alpha),
                "theta": float(theta),
                "Vmax": float(Vmax),
                "Vmed": float(Vmed),
                "t_hielo": float(t_hielo),
                "exposicion": estructura_actual.get("exposicion", "C"),
                "clase": estructura_actual.get("clase", "C"),
                "Zco": estructura_actual.get("Zco", 13.0),
                "Zcg": estructura_actual.get("Zcg", 13.0),
                "Zca": estructura_actual.get("Zca", 13.0),
                "Zes": estructura_actual.get("Zes", 10.0),
                "Cf_cable": estructura_actual.get("Cf_cable", 1.0),
                "Cf_guardia": estructura_actual.get("Cf_guardia", 1.0),
                "Cf_cadena": estructura_actual.get("Cf_cadena", 0.9),
                "Cf_estructura": estructura_actual.get("Cf_estructura", 0.9),
                "PCADENA": estructura_actual.get("PCADENA", 10.5),
                "SALTO_PORCENTUAL": float(SALTO_PORCENTUAL),
                "PASO_AFINADO": float(PASO_AFINADO),
                "OBJ_CONDUCTOR": OBJ_CONDUCTOR,
                "OBJ_GUARDIA": OBJ_GUARDIA,
                "RELFLECHA_MAX_GUARDIA": float(RELFLECHA_MAX_GUARDIA),
                "RELFLECHA_SIN_VIENTO": bool(RELFLECHA_SIN_VIENTO),
                "VANO_DESNIVELADO": bool(VANO_DESNIVELADO),
                "H_PIQANTERIOR": float(H_PIQANTERIOR) if H_PIQANTERIOR else 0.0,
                "H_PIQPOSTERIOR": float(H_PIQPOSTERIOR) if H_PIQPOSTERIOR else 0.0
            }
            
            # Capturar console output
            import io, sys
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            
            resultado = state.calculo_mecanico.calcular(params, estados_climaticos, restricciones_dict)
            
            console_output = buffer.getvalue()
            sys.stdout = old_stdout
            
            if resultado["exito"]:
                # Guardar DataFrames para caché
                df_conductor_cache = resultado["df_conductor"]
                df_guardia1_cache = resultado["df_guardia1"]
                df_guardia2_cache = resultado.get("df_guardia2")
                
                resultados_html = [
                    html.H4("Resultados del Cálculo Mecánico", className="mt-4 mb-3"),
                    
                    html.H5("Conductor"),
                    dbc.Table.from_dataframe(df_conductor_cache, striped=True, bordered=True, hover=True, size="sm"),
                    
                    html.H5("Cable de Guardia 1", className="mt-4"),
                    dbc.Table.from_dataframe(df_guardia1_cache, striped=True, bordered=True, hover=True, size="sm"),
                ]
                
                if df_guardia2_cache is not None:
                    resultados_html.extend([
                        html.H5("Cable de Guardia 2", className="mt-4"),
                        dbc.Table.from_dataframe(df_guardia2_cache, striped=True, bordered=True, hover=True, size="sm"),
                    ])
                
                if resultado["df_cargas_totales"] is not None:
                    resultados_html.extend([
                        html.H5("Lista Total de Cargas", className="mt-4"),
                        html.Div(dbc.Table.from_dataframe(resultado["df_cargas_totales"], striped=True, bordered=True, hover=True, size="sm"), className="table-responsive"),
                        dbc.Button("Descargar CSV", id="btn-descargar-cargas-csv", color="primary", className="mt-2")
                    ])
                
                # Output de consola
                if console_output:
                    resultados_html.extend([
                        html.Hr(className="mt-4"),
                        html.H5("Output de Cálculo", className="mb-2"),
                        html.Pre(console_output, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.75rem', 'maxHeight': '300px', 'overflowY': 'auto'})
                    ])
                
                if state.calculo_objetos.cable_conductor and state.calculo_objetos.cable_guardia:
                    try:
                        figs = crear_grafico_flechas(
                            state.calculo_objetos.cable_conductor,
                            state.calculo_objetos.cable_guardia,
                            float(L_vano),
                            state.calculo_objetos.cable_guardia2,
                            estados_climaticos
                        )
                        fig_combinado = figs[0]
                        fig_conductor = figs[1]
                        fig_guardia1 = figs[2]
                        fig_guardia2 = figs[3] if len(figs) > 3 else None
                        resultados_html.extend([
                            html.H5("Gráficos de Flechas", className="mt-4"),
                            html.H6("Conductor y Guardia", className="mt-3"),
                            dcc.Graph(figure=fig_combinado, config={'displayModeBar': True}),
                            html.H6("Solo Conductor", className="mt-3"),
                            dcc.Graph(figure=fig_conductor, config={'displayModeBar': True}),
                            html.H6("Solo Cable de Guardia 1", className="mt-3"),
                            dcc.Graph(figure=fig_guardia1, config={'displayModeBar': True})
                        ])
                        
                        if fig_guardia2:
                            resultados_html.extend([
                                html.H6("Solo Cable de Guardia 2", className="mt-3"),
                                dcc.Graph(figure=fig_guardia2, config={'displayModeBar': True})
                            ])
                        
                        # Guardar imágenes y JSON en background sin bloquear
                        from utils.calculo_cache import CalculoCache
                        from utils.view_helpers import ViewHelpers
                        import threading
                        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                        
                        def guardar_async():
                            # Guardar datos en cache con DataFrames completos
                            hash_params = CalculoCache.guardar_calculo_cmc(
                                nombre_estructura, 
                                estructura_actual, 
                                state.calculo_mecanico.resultados_conductor,
                                state.calculo_mecanico.resultados_guardia1,
                                state.calculo_mecanico.df_cargas_totales,
                                fig_combinado,
                                fig_conductor,
                                fig_guardia1,
                                resultados_guardia2=state.calculo_mecanico.resultados_guardia2,
                                console_output=console_output,
                                df_conductor_html=df_conductor_cache.to_json(orient='split'),
                                df_guardia1_html=df_guardia1_cache.to_json(orient='split'),
                                df_guardia2_html=df_guardia2_cache.to_json(orient='split') if df_guardia2_cache is not None else None
                            )
                            
                            # Guardar JSON interactivos
                            ViewHelpers.guardar_figura_plotly_json(fig_combinado, f"CMC_Combinado.{hash_params}.json")
                            ViewHelpers.guardar_figura_plotly_json(fig_conductor, f"CMC_Conductor.{hash_params}.json")
                            ViewHelpers.guardar_figura_plotly_json(fig_guardia1, f"CMC_Guardia.{hash_params}.json")
                            if fig_guardia2:
                                ViewHelpers.guardar_figura_plotly_json(fig_guardia2, f"CMC_Guardia2.{hash_params}.json")
                        
                        threading.Thread(target=guardar_async, daemon=True).start()
                    except Exception as e:
                        print(f"Error generando gráficos de flechas: {e}")
                        import traceback
                        traceback.print_exc()
                
                return resultados_html, True, "Éxito", "Cálculo completado y guardado", "success", "success"
            else:
                return dash.no_update, True, "Error", resultado["mensaje"], "danger", "danger"
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return dash.no_update, True, "Error", f"Error en cálculo: {str(e)}", "danger", "danger"
