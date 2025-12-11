"""Controlador de cálculos AEA"""

import dash
from dash import html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from models.app_state import AppState
from components.vista_calculo_mecanico import crear_tabla_estados_climaticos
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
    
    @app.callback(
        Output("tabla-estados-climaticos", "children"),
        Input("contenido-principal", "children"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def actualizar_tabla_estados(contenido, estructura_actual):
        return crear_tabla_estados_climaticos(estructura_actual)
    
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-params-cmc", "n_clicks"),
        State("param-L_vano", "value"),
        State("param-alpha", "value"),
        State("param-theta", "value"),
        State("param-Vmax", "value"),
        State("param-Vmed", "value"),
        State("param-t_hielo", "value"),
        State("param-SALTO_PORCENTUAL", "value"),
        State("param-PASO_AFINADO", "value"),
        State("param-OBJ_CONDUCTOR", "value"),
        State("param-OBJ_GUARDIA", "value"),
        State("param-RELFLECHA_MAX_GUARDIA", "value"),
        State("param-RELFLECHA_SIN_VIENTO", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_params_cmc(n_clicks, L_vano, alpha, theta, Vmax, Vmed, t_hielo,
                           SALTO_PORCENTUAL, PASO_AFINADO, OBJ_CONDUCTOR, OBJ_GUARDIA,
                           RELFLECHA_MAX_GUARDIA, RELFLECHA_SIN_VIENTO, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            estructura_actualizada = estructura_actual.copy()
            estructura_actualizada.update({
                "L_vano": float(L_vano),
                "alpha": float(alpha),
                "theta": float(theta),
                "Vmax": float(Vmax),
                "Vmed": float(Vmed),
                "t_hielo": float(t_hielo),
                "SALTO_PORCENTUAL": float(SALTO_PORCENTUAL),
                "PASO_AFINADO": float(PASO_AFINADO),
                "OBJ_CONDUCTOR": OBJ_CONDUCTOR,
                "OBJ_GUARDIA": OBJ_GUARDIA,
                "RELFLECHA_MAX_GUARDIA": float(RELFLECHA_MAX_GUARDIA),
                "RELFLECHA_SIN_VIENTO": bool(RELFLECHA_SIN_VIENTO)
            })
            
            state.estructura_manager.guardar_estructura(estructura_actualizada, state.archivo_actual)
            
            return estructura_actualizada, True, "Éxito", "Parámetros guardados", "success", "success"
        except Exception as e:
            return dash.no_update, True, "Error", f"Error: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("resultados-cmc", "children"),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-calcular-cmc", "n_clicks"),
        State("param-L_vano", "value"),
        State("param-alpha", "value"),
        State("param-theta", "value"),
        State("param-Vmax", "value"),
        State("param-Vmed", "value"),
        State("param-t_hielo", "value"),
        State("param-SALTO_PORCENTUAL", "value"),
        State("param-PASO_AFINADO", "value"),
        State("param-OBJ_CONDUCTOR", "value"),
        State("param-OBJ_GUARDIA", "value"),
        State("param-RELFLECHA_MAX_GUARDIA", "value"),
        State("param-RELFLECHA_SIN_VIENTO", "value"),
        State({"type": "estado-temp", "index": ALL}, "value"),
        State({"type": "estado-viento", "index": ALL}, "value"),
        State({"type": "estado-hielo", "index": ALL}, "value"),
        State({"type": "restriccion-conductor", "index": ALL}, "value"),
        State({"type": "restriccion-guardia", "index": ALL}, "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def calcular_cmc(n_clicks, L_vano, alpha, theta, Vmax, Vmed, t_hielo,
                    SALTO_PORCENTUAL, PASO_AFINADO, OBJ_CONDUCTOR, OBJ_GUARDIA,
                    RELFLECHA_MAX_GUARDIA, RELFLECHA_SIN_VIENTO,
                    temps, vientos, hielos, restricciones_cond, restricciones_guard, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            resultado_objetos = state.calculo_objetos.crear_todos_objetos(estructura_actual)
            if not resultado_objetos["exito"]:
                return html.Div(), True, "Error", resultado_objetos["mensaje"], "danger", "danger"
            
            estados_ids = ["I", "II", "III", "IV", "V"]
            descripciones = ["Tmáx", "Tmín", "Vmáx", "Vmed", "TMA"]
            estados_climaticos = {}
            for i, estado_id in enumerate(estados_ids):
                estados_climaticos[estado_id] = {
                    "temperatura": float(temps[i]),
                    "descripcion": descripciones[i],
                    "viento_velocidad": float(vientos[i]),
                    "espesor_hielo": float(hielos[i])
                }
            
            restricciones_dict = {
                "conductor": {"tension_max_porcentaje": {}},
                "guardia": {"tension_max_porcentaje": {}, "relflecha_max": float(RELFLECHA_MAX_GUARDIA)}
            }
            for i, estado_id in enumerate(estados_ids):
                restricciones_dict["conductor"]["tension_max_porcentaje"][estado_id] = float(restricciones_cond[i])
                restricciones_dict["guardia"]["tension_max_porcentaje"][estado_id] = float(restricciones_guard[i])
            
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
                "RELFLECHA_SIN_VIENTO": bool(RELFLECHA_SIN_VIENTO)
            }
            
            resultado = state.calculo_mecanico.calcular(params, estados_climaticos, restricciones_dict)
            
            if resultado["exito"]:
                resultados_html = [
                    html.H4("Resultados del Cálculo Mecánico", className="mt-4 mb-3"),
                    
                    html.H5("Conductor"),
                    dbc.Table.from_dataframe(resultado["df_conductor"], striped=True, bordered=True, hover=True, size="sm"),
                    
                    html.H5("Cable de Guardia 1", className="mt-4"),
                    dbc.Table.from_dataframe(resultado["df_guardia1"], striped=True, bordered=True, hover=True, size="sm"),
                ]
                
                if resultado.get("df_guardia2") is not None:
                    resultados_html.extend([
                        html.H5("Cable de Guardia 2", className="mt-4"),
                        dbc.Table.from_dataframe(resultado["df_guardia2"], striped=True, bordered=True, hover=True, size="sm"),
                    ])
                
                if resultado["df_cargas_totales"] is not None:
                    resultados_html.extend([
                        html.H5("Lista Total de Cargas", className="mt-4"),
                        dbc.Table.from_dataframe(resultado["df_cargas_totales"], striped=True, bordered=True, hover=True, size="sm"),
                        dbc.Button("Descargar CSV", id="btn-descargar-cargas-csv", color="primary", className="mt-2")
                    ])
                
                if state.calculo_mecanico.resultados_conductor and state.calculo_mecanico.resultados_guardia1:
                    try:
                        figs = crear_grafico_flechas(
                            state.calculo_mecanico.resultados_conductor,
                            state.calculo_mecanico.resultados_guardia1,
                            float(L_vano),
                            state.calculo_mecanico.resultados_guardia2
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
                        
                        # Guardar imágenes en background sin bloquear
                        from utils.calculo_cache import CalculoCache
                        import threading
                        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                        
                        def guardar_async():
                            CalculoCache.guardar_calculo_cmc(
                                nombre_estructura, 
                                estructura_actual, 
                                state.calculo_mecanico.resultados_conductor,
                                state.calculo_mecanico.resultados_guardia1,
                                state.calculo_mecanico.df_cargas_totales,
                                fig_combinado,
                                fig_conductor,
                                fig_guardia1
                            )
                        
                        threading.Thread(target=guardar_async, daemon=True).start()
                    except Exception as e:
                        print(f"Error generando gráficos de flechas: {e}")
                        import traceback
                        traceback.print_exc()
                
                return resultados_html, True, "Éxito", "Cálculo completado y guardado", "success", "success"
            else:
                return html.Div(), True, "Error", resultado["mensaje"], "danger", "danger"
                
        except Exception as e:
            return html.Div(), True, "Error", f"Error en cálculo: {str(e)}", "danger", "danger"
