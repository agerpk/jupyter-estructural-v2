"""Controlador de ajuste de parámetros"""

import dash
from dash import Input, Output, State, ALL
from models.app_state import AppState


def register_callbacks(app):
    """Registrar callbacks de ajuste de parámetros"""
    
    state = AppState()
    
    # CALLBACK ESPECÍFICO PARA CMC
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-params-cmc", "n_clicks"),
        State({"type": "estado-temp", "index": ALL}, "value"),
        State({"type": "estado-viento", "index": ALL}, "value"),
        State({"type": "estado-hielo", "index": ALL}, "value"),
        State({"type": "restriccion-conductor", "index": ALL}, "value"),
        State({"type": "restriccion-guardia", "index": ALL}, "value"),
        State({"type": "estado-temp", "index": ALL}, "id"),
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
    def guardar_params_cmc_directo(n_clicks, temps, vientos, hielos, rest_cond, rest_guard, ids,
                                   L_vano, alpha, theta, Vmax, Vmed, t_hielo,
                                   VANO_DESNIVELADO, H_PIQANTERIOR, H_PIQPOSTERIOR,
                                   SALTO_PORCENTUAL, PASO_AFINADO, OBJ_CONDUCTOR, OBJ_GUARDIA,
                                   RELFLECHA_MAX_GUARDIA, RELFLECHA_SIN_VIENTO, estructura_actual):
        print(f"\n🔵🔵🔵 CALLBACK CMC DIRECTO EJECUTADO")
        
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        try:
            from config.app_config import DATA_DIR
            
            titulo = estructura_actual['TITULO']
            ruta = DATA_DIR / f"{titulo}.estructura.json"
            estructura = state.estructura_manager.cargar_estructura(ruta)
            
            # Guardar parámetros CMC
            estructura.update({
                "L_vano": float(L_vano) if L_vano is not None else estructura.get("L_vano", 400),
                "alpha": float(alpha) if alpha is not None else estructura.get("alpha", 0),
                "theta": float(theta) if theta is not None else estructura.get("theta", 45),
                "Vmax": float(Vmax) if Vmax is not None else estructura.get("Vmax", 38.9),
                "Vmed": float(Vmed) if Vmed is not None else estructura.get("Vmed", 15.56),
                "t_hielo": float(t_hielo) if t_hielo is not None else estructura.get("t_hielo", 0.01),
                "VANO_DESNIVELADO": bool(VANO_DESNIVELADO) if VANO_DESNIVELADO is not None else estructura.get("VANO_DESNIVELADO", False),
                "H_PIQANTERIOR": float(H_PIQANTERIOR) if H_PIQANTERIOR is not None else 0.0,
                "H_PIQPOSTERIOR": float(H_PIQPOSTERIOR) if H_PIQPOSTERIOR is not None else 0.0,
                "SALTO_PORCENTUAL": float(SALTO_PORCENTUAL) if SALTO_PORCENTUAL is not None else estructura.get("SALTO_PORCENTUAL", 0.05),
                "PASO_AFINADO": float(PASO_AFINADO) if PASO_AFINADO is not None else estructura.get("PASO_AFINADO", 0.005),
                "OBJ_CONDUCTOR": OBJ_CONDUCTOR if OBJ_CONDUCTOR is not None else estructura.get("OBJ_CONDUCTOR", "FlechaMin"),
                "OBJ_GUARDIA": OBJ_GUARDIA if OBJ_GUARDIA is not None else estructura.get("OBJ_GUARDIA", "TiroMin"),
                "RELFLECHA_MAX_GUARDIA": float(RELFLECHA_MAX_GUARDIA) if RELFLECHA_MAX_GUARDIA is not None else estructura.get("RELFLECHA_MAX_GUARDIA", 0.95),
                "RELFLECHA_SIN_VIENTO": bool(RELFLECHA_SIN_VIENTO) if RELFLECHA_SIN_VIENTO is not None else estructura.get("RELFLECHA_SIN_VIENTO", True)
            })
            
            # Guardar estados climáticos
            if ids and temps:
                estados = {}
                desc = {"I": "Tmáx", "II": "Tmín", "III": "Vmáx", "IV": "Vmed", "V": "TMA"}
                
                for i, id_dict in enumerate(ids):
                    eid = id_dict["index"]
                    estados[eid] = {
                        "temperatura": float(temps[i]) if temps[i] is not None else 0,
                        "descripcion": desc.get(eid, ""),
                        "viento_velocidad": float(vientos[i]) if vientos[i] is not None else 0,
                        "espesor_hielo": float(hielos[i]) if hielos[i] is not None else 0
                    }
                
                estructura["estados_climaticos"] = estados
                
                rc = {}
                rg = {}
                for i, id_dict in enumerate(ids):
                    eid = id_dict["index"]
                    rc[eid] = float(rest_cond[i]) if rest_cond and i < len(rest_cond) and rest_cond[i] is not None else 0.25
                    rg[eid] = float(rest_guard[i]) if rest_guard and i < len(rest_guard) and rest_guard[i] is not None else 0.7
                
                estructura["restricciones_cables"] = {
                    "conductor": {"tension_max_porcentaje": rc},
                    "guardia": {"tension_max_porcentaje": rg}
                }
            
            state.estructura_manager.guardar_estructura(estructura, ruta)
            state.set_estructura_actual(estructura)
            
            return (estructura, True, "Éxito", f"Guardado: {ruta.name}", "success", "success")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return (dash.no_update, True, "Error", f"Error: {str(e)}", "danger", "danger")
    
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
        Input("btn-guardar-params-cmc", "n_clicks"),
        State({"type": "param-input", "index": ALL}, "id"),
        State({"type": "param-input", "index": ALL}, "value"),
        State({"type": "estado-temp-ajuste", "index": ALL}, "value"),
        State({"type": "estado-viento-ajuste", "index": ALL}, "value"),
        State({"type": "estado-hielo-ajuste", "index": ALL}, "value"),
        State({"type": "restriccion-conductor-ajuste", "index": ALL}, "value"),
        State({"type": "restriccion-guardia-ajuste", "index": ALL}, "value"),
        State({"type": "estado-temp-ajuste", "index": ALL}, "id"),
        State({"type": "estado-temp", "index": ALL}, "value"),
        State({"type": "estado-viento", "index": ALL}, "value"),
        State({"type": "estado-hielo", "index": ALL}, "value"),
        State({"type": "restriccion-conductor", "index": ALL}, "value"),
        State({"type": "restriccion-guardia", "index": ALL}, "value"),
        State({"type": "estado-temp", "index": ALL}, "id"),
        State("param-L_vano", "value"),
        State("param-Vmax", "value"),
        State("param-Vmed", "value"),
        State("param-VANO_DESNIVELADO", "value"),
        State("param-H_PIQANTERIOR", "value"),
        State("param-H_PIQPOSTERIOR", "value"),
        State("param-OBJ_CONDUCTOR", "value"),
        State("param-OBJ_GUARDIA", "value"),
        State("param-RELFLECHA_SIN_VIENTO", "value"),
        State("slider-alpha", "value"),
        State("slider-theta", "value"),
        State("slider-t_hielo", "value"),
        State("slider-SALTO_PORCENTUAL", "value"),
        State("slider-PASO_AFINADO", "value"),
        State("slider-RELFLECHA_MAX_GUARDIA", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_parametros_ajustados(n_clicks_ajuste, n_clicks_cmc, param_ids, param_values, 
                                     estado_temps_ajuste, estado_vientos_ajuste, estado_hielos_ajuste,
                                     restriccion_conductores_ajuste, restriccion_guardias_ajuste,
                                     estado_ids_ajuste,
                                     estado_temps_cmc, estado_vientos_cmc, estado_hielos_cmc,
                                     restriccion_conductores_cmc, restriccion_guardias_cmc,
                                     estado_ids_cmc,
                                     L_vano, Vmax, Vmed, VANO_DESNIVELADO, H_PIQANTERIOR, H_PIQPOSTERIOR,
                                     OBJ_CONDUCTOR, OBJ_GUARDIA, RELFLECHA_SIN_VIENTO,
                                     alpha, theta, t_hielo, SALTO_PORCENTUAL, PASO_AFINADO, RELFLECHA_MAX_GUARDIA,
                                     estructura_actual):
        print(f"\n🔵🔵🔵 CALLBACK EJECUTADO - n_clicks_ajuste={n_clicks_ajuste}, n_clicks_cmc={n_clicks_cmc}")
        print(f"🔵🔵🔵 estado_ids_cmc={estado_ids_cmc}")
        print(f"🔵🔵🔵 estado_temps_cmc={estado_temps_cmc}")
        
        if n_clicks_ajuste is None and n_clicks_cmc is None:
            print(f"🔵🔵🔵 AMBOS n_clicks SON NONE - ABORTANDO")
            raise dash.exceptions.PreventUpdate
        
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
        es_vista_cmc = trigger_id == "btn-guardar-params-cmc"
        
        print(f"\n🔵 Guardando parámetros desde: {'CMC' if es_vista_cmc else 'Ajuste'}")
        
        try:
            from config.app_config import DATA_DIR
            
            if not estructura_actual or 'TITULO' not in estructura_actual:
                raise ValueError("No hay estructura activa")
            
            titulo = estructura_actual['TITULO']
            ruta_archivo = DATA_DIR / f"{titulo}.estructura.json"
            print(f"📁 Archivo: {ruta_archivo.name}")
            
            estructura_actualizada = state.estructura_manager.cargar_estructura(ruta_archivo)
            
            # Guardar parámetros específicos de CMC si viene de esa vista
            if es_vista_cmc:
                if L_vano is not None:
                    estructura_actualizada["L_vano"] = float(L_vano)
                if Vmax is not None:
                    estructura_actualizada["Vmax"] = float(Vmax)
                if Vmed is not None:
                    estructura_actualizada["Vmed"] = float(Vmed)
                if VANO_DESNIVELADO is not None:
                    estructura_actualizada["VANO_DESNIVELADO"] = bool(VANO_DESNIVELADO)
                if H_PIQANTERIOR is not None:
                    estructura_actualizada["H_PIQANTERIOR"] = float(H_PIQANTERIOR)
                if H_PIQPOSTERIOR is not None:
                    estructura_actualizada["H_PIQPOSTERIOR"] = float(H_PIQPOSTERIOR)
                if OBJ_CONDUCTOR is not None:
                    estructura_actualizada["OBJ_CONDUCTOR"] = OBJ_CONDUCTOR
                if OBJ_GUARDIA is not None:
                    estructura_actualizada["OBJ_GUARDIA"] = OBJ_GUARDIA
                if RELFLECHA_SIN_VIENTO is not None:
                    estructura_actualizada["RELFLECHA_SIN_VIENTO"] = bool(RELFLECHA_SIN_VIENTO)
                if alpha is not None:
                    estructura_actualizada["alpha"] = float(alpha)
                if theta is not None:
                    estructura_actualizada["theta"] = float(theta)
                if t_hielo is not None:
                    estructura_actualizada["t_hielo"] = float(t_hielo)
                if SALTO_PORCENTUAL is not None:
                    estructura_actualizada["SALTO_PORCENTUAL"] = float(SALTO_PORCENTUAL)
                if PASO_AFINADO is not None:
                    estructura_actualizada["PASO_AFINADO"] = float(PASO_AFINADO)
                if RELFLECHA_MAX_GUARDIA is not None:
                    estructura_actualizada["RELFLECHA_MAX_GUARDIA"] = float(RELFLECHA_MAX_GUARDIA)
            
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
            
            # Seleccionar estados según vista - usar listas vacías si no existen
            if es_vista_cmc:
                estado_ids = estado_ids_cmc if estado_ids_cmc else []
                estado_temps = estado_temps_cmc if estado_temps_cmc else []
                estado_vientos = estado_vientos_cmc if estado_vientos_cmc else []
                estado_hielos = estado_hielos_cmc if estado_hielos_cmc else []
                restriccion_conductores = restriccion_conductores_cmc if restriccion_conductores_cmc else []
                restriccion_guardias = restriccion_guardias_cmc if restriccion_guardias_cmc else []
            else:
                estado_ids = estado_ids_ajuste if estado_ids_ajuste else []
                estado_temps = estado_temps_ajuste if estado_temps_ajuste else []
                estado_vientos = estado_vientos_ajuste if estado_vientos_ajuste else []
                estado_hielos = estado_hielos_ajuste if estado_hielos_ajuste else []
                restriccion_conductores = restriccion_conductores_ajuste if restriccion_conductores_ajuste else []
                restriccion_guardias = restriccion_guardias_ajuste if restriccion_guardias_ajuste else []
            
            # Guardar estados climáticos si existen
            print(f"\n📊 DEBUG ESTADOS CLIMÁTICOS:")
            print(f"  - estado_ids recibidos: {len(estado_ids) if estado_ids else 0}")
            print(f"  - estado_temps recibidos: {len(estado_temps) if estado_temps else 0}")
            
            if estado_ids and estado_temps:
                estados_climaticos = {}
                descripciones = {"I": "Tmáx", "II": "Tmín", "III": "Vmáx", "IV": "Vmed", "V": "TMA"}
                
                print(f"\n🔄 Procesando {len(estado_ids)} estados:")
                for i, estado_id_dict in enumerate(estado_ids):
                    estado_id = estado_id_dict["index"]
                    temp = float(estado_temps[i]) if estado_temps[i] is not None else 0
                    viento = float(estado_vientos[i]) if estado_vientos[i] is not None else 0
                    hielo = float(estado_hielos[i]) if estado_hielos[i] is not None else 0
                    
                    estados_climaticos[estado_id] = {
                        "temperatura": temp,
                        "descripcion": descripciones.get(estado_id, ""),
                        "viento_velocidad": viento,
                        "espesor_hielo": hielo
                    }
                    print(f"  Estado {estado_id}: T={temp}°C, V={viento}m/s, H={hielo}m")
                
                estructura_actualizada["estados_climaticos"] = estados_climaticos
                print(f"\n✅ Estados climáticos guardados: {len(estados_climaticos)}")
                
                # Guardar restricciones
                restricciones_conductor = {}
                restricciones_guardia = {}
                
                for i, estado_id_dict in enumerate(estado_ids):
                    estado_id = estado_id_dict["index"]
                    rest_cond = float(restriccion_conductores[i]) if restriccion_conductores and i < len(restriccion_conductores) and restriccion_conductores[i] is not None else 0.25
                    rest_guard = float(restriccion_guardias[i]) if restriccion_guardias and i < len(restriccion_guardias) and restriccion_guardias[i] is not None else 0.7
                    
                    restricciones_conductor[estado_id] = rest_cond
                    restricciones_guardia[estado_id] = rest_guard
                
                estructura_actualizada["restricciones_cables"] = {
                    "conductor": {"tension_max_porcentaje": restricciones_conductor},
                    "guardia": {"tension_max_porcentaje": restricciones_guardia}
                }
                print(f"✅ Restricciones guardadas")
            elif "estados_climaticos" in estructura_actualizada:
                estructura_actualizada["restricciones_cables"] = {
                    "conductor": {"tension_max_porcentaje": {estado_id: 0.25 for estado_id in estructura_actualizada["estados_climaticos"].keys()}},
                    "guardia": {"tension_max_porcentaje": {estado_id: 0.7 for estado_id in estructura_actualizada["estados_climaticos"].keys()}}
                }
            
            print(f"\n💾 Guardando archivo: {ruta_archivo}")
            print(f"   Claves en estructura_actualizada: {list(estructura_actualizada.keys())}")
            if "estados_climaticos" in estructura_actualizada:
                print(f"   ✅ 'estados_climaticos' presente con {len(estructura_actualizada['estados_climaticos'])} estados")
            if "restricciones_cables" in estructura_actualizada:
                print(f"   ✅ 'restricciones_cables' presente")
            
            state.estructura_manager.guardar_estructura(estructura_actualizada, ruta_archivo)
            state.set_estructura_actual(estructura_actualizada)
            print(f"\n✅ Guardado exitoso: {ruta_archivo.name}")
            
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
