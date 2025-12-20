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
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_parametros_ajustados(n_clicks, param_ids, param_values, estructura_actual):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        try:
            # SIEMPRE recargar desde archivo para obtener datos actualizados
            from config.app_config import DATA_DIR
            estructura_actual = state.estructura_manager.cargar_estructura(DATA_DIR / "actual.estructura.json")
            estructura_actualizada = estructura_actual.copy()
            
            for param_id, param_value in zip(param_ids, param_values):
                if param_id and "index" in param_id:
                    param_key = param_id["index"]
                    
                    if param_key in estructura_actual:
                        original_value = estructura_actual[param_key]
                        
                        # Manejar morfología especialmente
                        if param_key == "MORFOLOGIA":
                            # Extraer parámetros de morfología y actualizar legacy
                            from EstructuraAEA_Geometria_Morfologias import extraer_parametros_morfologia
                            try:
                                params = extraer_parametros_morfologia(param_value)
                                estructura_actualizada["MORFOLOGIA"] = param_value
                                estructura_actualizada["TERNA"] = params["TERNA"]
                                estructura_actualizada["DISPOSICION"] = params["DISPOSICION"]
                                estructura_actualizada["CANT_HG"] = params["CANT_HG"]
                                estructura_actualizada["HG_CENTRADO"] = params["HG_CENTRADO"]
                            except Exception as e:
                                print(f"Error procesando morfología {param_value}: {e}")
                                estructura_actualizada[param_key] = param_value
                        elif isinstance(original_value, bool):
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
            
            state.estructura_manager.guardar_estructura(estructura_actualizada, state.archivo_actual)
            
            # También guardar en DB si tiene título
            if "TITULO" in estructura_actualizada:
                from config.app_config import DATA_DIR
                titulo = estructura_actualizada["TITULO"]
                nombre_archivo = f"{titulo}.estructura.json"
                state.estructura_manager.guardar_estructura(estructura_actualizada, DATA_DIR / nombre_archivo)
            
            return (
                estructura_actualizada,
                True, 
                "Éxito", 
                "Parámetros guardados correctamente", 
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
