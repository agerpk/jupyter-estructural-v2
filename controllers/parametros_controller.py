"""Controlador de ajuste de parámetros"""

import dash
from dash import Input, Output, State, ALL
from models.app_state import AppState


def register_callbacks(app):
    """Registrar callbacks de ajuste de parámetros"""
    
    state = AppState()
    
    # Sincronizar sliders con inputs en vista ajuste parámetros
    @app.callback(
        Output({"type": "param-input", "index": ALL}, "value"),
        Output({"type": "param-slider", "index": ALL}, "value"),
        Input({"type": "param-slider", "index": ALL}, "value"),
        Input({"type": "param-input", "index": ALL}, "value"),
        State({"type": "param-slider", "index": ALL}, "id"),
        State({"type": "param-input", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    def sync_slider_input(slider_values, input_values, slider_ids, input_ids):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"]
        
        # Si fue disparado por un slider
        if "param-slider" in trigger_id:
            slider_map = {sid["index"]: val for sid, val in zip(slider_ids, slider_values)}
            result_inputs = [slider_map.get(iid["index"], dash.no_update) for iid in input_ids]
            return result_inputs, [dash.no_update] * len(slider_ids)
        
        # Si fue disparado por un input
        elif "param-input" in trigger_id:
            input_map = {iid["index"]: val for iid, val in zip(input_ids, input_values) if val is not None}
            result_sliders = [input_map.get(sid["index"], dash.no_update) for sid in slider_ids]
            return [dash.no_update] * len(input_ids), result_sliders
        
        raise dash.exceptions.PreventUpdate
    
    # Sincronizar sliders con inputs en vista CMC
    @app.callback(
        Output("param-H_PIQANTERIOR", "value"),
        Output("param-H_PIQPOSTERIOR", "value"),
        Output("slider-H_PIQANTERIOR", "value"),
        Output("slider-H_PIQPOSTERIOR", "value"),
        Input("slider-H_PIQANTERIOR", "value"),
        Input("slider-H_PIQPOSTERIOR", "value"),
        Input("param-H_PIQANTERIOR", "value"),
        Input("param-H_PIQPOSTERIOR", "value"),
        prevent_initial_call=True
    )
    def sync_cmc_slider_input(slider_ant, slider_post, input_ant, input_post):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "slider-H_PIQANTERIOR":
            return slider_ant, dash.no_update, dash.no_update, dash.no_update
        elif trigger_id == "slider-H_PIQPOSTERIOR":
            return dash.no_update, slider_post, dash.no_update, dash.no_update
        elif trigger_id == "param-H_PIQANTERIOR":
            return dash.no_update, dash.no_update, input_ant if input_ant is not None else dash.no_update, dash.no_update
        elif trigger_id == "param-H_PIQPOSTERIOR":
            return dash.no_update, dash.no_update, dash.no_update, input_post if input_post is not None else dash.no_update
        
        raise dash.exceptions.PreventUpdate
    
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("guardar-parametros", "n_clicks"),
        State({"type": "param-input", "index": ALL}, "id"),
        State({"type": "param-input", "index": ALL}, "value"),
        State({"type": "estado-temp-ajuste", "index": ALL}, "value"),
        State({"type": "estado-viento-ajuste", "index": ALL}, "value"),
        State({"type": "estado-hielo-ajuste", "index": ALL}, "value"),
        State({"type": "restriccion-conductor-ajuste", "index": ALL}, "value"),
        State({"type": "restriccion-guardia-ajuste", "index": ALL}, "value"),
        State({"type": "estado-temp-ajuste", "index": ALL}, "id"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_parametros_ajustados(n_clicks, param_ids, param_values, 
                                     estado_temps, estado_vientos, estado_hielos,
                                     restriccion_conductores, restriccion_guardias,
                                     estado_ids, estructura_actual):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"\n🔵 Guardando parámetros...")
        
        try:
            from config.app_config import DATA_DIR
            
            if not estructura_actual or 'TITULO' not in estructura_actual:
                raise ValueError("No hay estructura activa")
            
            titulo = estructura_actual['TITULO']
            ruta_archivo = DATA_DIR / f"{titulo}.estructura.json"
            print(f"📁 Archivo: {ruta_archivo.name}")
            
            estructura_actualizada = state.estructura_manager.cargar_estructura(ruta_archivo)
            
            for param_id, param_value in zip(param_ids, param_values):
                if param_id and "index" in param_id:
                    param_key = param_id["index"]
                    
                    # Manejar parámetros de costeo anidados
                    if param_key.startswith("costeo_"):
                        # Inicializar estructura de costeo si no existe
                        if "costeo" not in estructura_actualizada:
                            estructura_actualizada["costeo"] = {
                                "postes": {},
                                "accesorios": {},
                                "fundaciones": {},
                                "montaje": {},
                                "adicional_estructura": 2000.0
                            }
                        
                        # Mapear parámetros de costeo
                        costeo_map = {
                            "costeo_coef_a": ("postes", "coef_a"),
                            "costeo_coef_b": ("postes", "coef_b"),
                            "costeo_coef_c": ("postes", "coef_c"),
                            "costeo_precio_vinculos": ("accesorios", "vinculos"),
                            "costeo_precio_crucetas": ("accesorios", "crucetas"),
                            "costeo_precio_mensulas": ("accesorios", "mensulas"),
                            "costeo_precio_hormigon": ("fundaciones", "precio_m3_hormigon"),
                            "costeo_factor_hierro": ("fundaciones", "factor_hierro"),
                            "costeo_precio_estructura": ("montaje", "precio_por_estructura"),
                            "costeo_factor_terreno": ("montaje", "factor_terreno"),
                            "costeo_adicional_estructura": (None, "adicional_estructura")
                        }
                        
                        if param_key in costeo_map:
                            categoria, sub_param = costeo_map[param_key]
                            try:
                                valor_float = float(param_value)
                                if categoria:
                                    estructura_actualizada["costeo"][categoria][sub_param] = valor_float
                                else:
                                    estructura_actualizada["costeo"][sub_param] = valor_float
                            except:
                                pass  # Ignorar valores inválidos
                    
                    elif param_key in estructura_actual:
                        original_value = estructura_actual[param_key]
                        
                        if isinstance(original_value, bool):
                            estructura_actualizada[param_key] = bool(param_value)
                        elif isinstance(original_value, int):
                            try:
                                estructura_actualizada[param_key] = int(float(param_value))
                            except:
                                estructura_actualizada[param_key] = param_value
                        elif isinstance(original_value, float):
                            try:
                                estructura_actualizada[param_key] = float(param_value)
                            except:
                                estructura_actualizada[param_key] = param_value
                        else:
                            estructura_actualizada[param_key] = param_value
                    else:
                        estructura_actualizada[param_key] = param_value
            
            # Guardar estados climáticos si existen
            if estado_ids and estado_temps:
                estados_climaticos = {}
                descripciones = {"I": "Tmáx", "II": "Tmín", "III": "Vmáx", "IV": "Vmed", "V": "TMA"}
                
                for i, estado_id_dict in enumerate(estado_ids):
                    estado_id = estado_id_dict["index"]
                    estados_climaticos[estado_id] = {
                        "temperatura": float(estado_temps[i]) if estado_temps[i] is not None else 0,
                        "descripcion": descripciones.get(estado_id, ""),
                        "viento_velocidad": float(estado_vientos[i]) if estado_vientos[i] is not None else 0,
                        "espesor_hielo": float(estado_hielos[i]) if estado_hielos[i] is not None else 0
                    }
                
                estructura_actualizada["estados_climaticos"] = estados_climaticos
                
                # Guardar restricciones
                if restriccion_conductores and restriccion_guardias:
                    estructura_actualizada["restricciones_cables"] = {
                        "conductor": {
                            "tension_max_porcentaje": {
                                estado_id_dict["index"]: float(restriccion_conductores[i]) if restriccion_conductores[i] is not None else 0.25
                                for i, estado_id_dict in enumerate(estado_ids)
                            }
                        },
                        "guardia": {
                            "tension_max_porcentaje": {
                                estado_id_dict["index"]: float(restriccion_guardias[i]) if restriccion_guardias[i] is not None else 0.7
                                for i, estado_id_dict in enumerate(estado_ids)
                            }
                        }
                    }
            
            state.estructura_manager.guardar_estructura(estructura_actualizada, ruta_archivo)
            state.set_estructura_actual(estructura_actualizada)
            print(f"✅ Guardado: {ruta_archivo.name}")
            
            return (
                estructura_actualizada,
                True, 
                "Éxito", 
                f"Guardado en: {ruta_archivo.name}", 
                "success", 
                "success"
            )
            
        except Exception as e:
            print(f"Error guardando parámetros: {e}")
            return (
                dash.no_update,
                True,
                "Error",
                f"Error al guardar parámetros: {str(e)}",
                "danger",
                "danger"
            )
