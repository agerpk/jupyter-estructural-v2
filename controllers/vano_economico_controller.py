"""
Controller para Vano Económico
"""

import dash
from dash import Input, Output, State, no_update, html
from models.app_state import AppState
from utils.calculo_cache import CalculoCache
import dash_bootstrap_components as dbc

def register_callbacks(app):
    """Registrar callbacks de vano económico"""
    
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("vano-economico-btn-confirmar", "n_clicks"),
        [State("vano-economico-input-min", "value"),
         State("vano-economico-input-max", "value"),
         State("vano-economico-salto", "value"),
         State("vano-economico-input-longtraza", "value"),
         State("vano-economico-select-criterio-rr", "value"),
         State("vano-economico-input-rr-cada-x-m", "value"),
         State("vano-economico-input-rr-cada-x-s", "value"),
         State("vano-economico-input-cant-rr-manual", "value")],
        prevent_initial_call=True
    )
    def confirmar_ajustes(n_clicks, vano_min, vano_max, salto, longtraza,
                         criterio_rr, rr_cada_x_m, rr_cada_x_s, cant_rr_manual):
        """Guardar ajustes en AppState"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"🟢 DEBUG CONFIRMAR: longtraza={longtraza}, criterio_rr={criterio_rr}")
        print(f"🟢 DEBUG CONFIRMAR: vano_min={vano_min}, vano_max={vano_max}, salto={salto}")
        # Validar campos obligatorios
        if not all([vano_min, vano_max, salto, longtraza, criterio_rr]):
            return (True, "Error", "Complete todos los campos obligatorios", "danger", "danger")
        
        if vano_max <= vano_min:
            return (True, "Error", "Vano máximo debe ser mayor que vano mínimo", "danger", "danger")
        
        state = AppState()
        ajustes = {
            "vano_min": vano_min,
            "vano_max": vano_max,
            "salto": salto,
            "longtraza": longtraza,
            "criterio_rr": criterio_rr,
            "rr_cada_x_m": rr_cada_x_m,
            "rr_cada_x_s": rr_cada_x_s,
            "cant_rr_manual": cant_rr_manual
        }
        state.set_vano_economico_ajustes(ajustes)
        
        return (True, "Éxito", "Ajustes guardados correctamente", "success", "success")
    
    @app.callback(
        [Output("vano-economico-select-familia", "options"),
         Output("vano-economico-select-familia", "value")],
        Input("vano-economico-select-familia", "id"),
        prevent_initial_call=False
    )
    def cargar_opciones_familias(component_id):
        """Cargar familias disponibles"""
        from utils.familia_manager import FamiliaManager
        archivos = FamiliaManager.obtener_archivos_familia()
        opciones = [{"label": f, "value": f} for f in archivos]
        return opciones, None
    
    @app.callback(
        [Output("vano-economico-familia-actual", "children"),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("vano-economico-select-familia", "value"),
        prevent_initial_call=True
    )
    def cargar_familia_seleccionada(nombre_familia):
        """Cargar familia seleccionada"""
        if nombre_familia is None:
            raise dash.exceptions.PreventUpdate
        
        state = AppState()
        state.set_familia_activa(nombre_familia)
        
        return (nombre_familia, True, "Éxito", 
                f"Familia '{nombre_familia}' cargada", 
                "success", "success")
    
    @app.callback(
        [Output("vano-economico-input-cant-rr-manual", "disabled"),
         Output("vano-economico-row-manual", "style")],
        Input("vano-economico-select-criterio-rr", "value")
    )
    def toggle_manual_rr(criterio):
        """Habilitar/deshabilitar input manual según criterio"""
        if criterio == "Manual":
            return False, {"display": "block"}
        return True, {"display": "none"}
    
    @app.callback(
        Output("vano-economico-display-cantidades", "children"),
        [Input("vano-economico-input-longtraza", "value"),
         Input("vano-economico-select-criterio-rr", "value"),
         Input("vano-economico-input-rr-cada-x-m", "value"),
         Input("vano-economico-input-rr-cada-x-s", "value"),
         Input("vano-economico-input-cant-rr-manual", "value")],
        [State("vano-economico-input-min", "value"),
         State("vano-economico-input-max", "value")]
    )
    def actualizar_display_cantidades(longtraza, criterio_rr, 
                                     rr_cada_x_m, rr_cada_x_s, cant_rr_manual,
                                     vano_min, vano_max):
        """Actualizar display de cantidades calculadas con vano medio"""
        if not all([vano_min, vano_max, longtraza]):
            return html.P("Complete los campos para ver cantidades", className="text-muted")
        
        try:
            from utils.vano_economico_utils import calcular_cantidades
            
            # Usar vano medio para ejemplo
            vano_medio = (vano_min + vano_max) / 2
            
            # Obtener cant_RA de familia activa
            state = AppState()
            nombre_familia = state.get_familia_activa()
            if nombre_familia:
                from utils.familia_manager import FamiliaManager
                from utils.vano_economico_utils import obtener_cant_ra_familia
                familia_data = FamiliaManager.cargar_familia(nombre_familia)
                cant_ra = obtener_cant_ra_familia(familia_data)
            else:
                cant_ra = 0
            
            cantidades = calcular_cantidades(
                longtraza, vano_medio, criterio_rr,
                rr_cada_x_m or 2000, rr_cada_x_s or 5, cant_rr_manual or 0, cant_ra
            )
            
            return dbc.Row([
                dbc.Col([html.Strong("Terminales:"), html.Span(f" {cantidades['cant_T']}")], width=3),
                dbc.Col([html.Strong("Suspensiones:"), html.Span(f" {cantidades['cant_S']}")], width=3),
                dbc.Col([html.Strong("Retenciones:"), html.Span(f" {cantidades['cant_RR']}")], width=3),
                dbc.Col([html.Strong("Ret. Angulares:"), html.Span(f" {cantidades['cant_RA']}")], width=3)
            ])
        except Exception as e:
            return html.P(f"Error: {str(e)}", className="text-danger")
    
    @app.callback(
        [Output("vano-economico-resultados", "children"),
         Output("vano-economico-progress", "value"),
         Output("vano-economico-progress-container", "style"),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("vano-economico-btn-calcular", "n_clicks"),
        [State("vano-economico-input-min", "value"),
         State("vano-economico-input-max", "value"),
         State("vano-economico-salto", "value"),
         State("vano-economico-input-longtraza", "value"),
         State("vano-economico-select-criterio-rr", "value"),
         State("vano-economico-input-rr-cada-x-m", "value"),
         State("vano-economico-input-rr-cada-x-s", "value"),
         State("vano-economico-input-cant-rr-manual", "value"),
         State("vano-economico-switch-generar-plots", "value")],
        prevent_initial_call=True
    )
    def calcular_vano_economico(n_clicks, vano_min, vano_max, salto, longtraza,
                               criterio_rr, rr_cada_x_m, rr_cada_x_s, cant_rr_manual, generar_plots):
        """Ejecutar cálculo de vano económico"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        # Cargar ajustes desde AppState
        state = AppState()
        ajustes = state.get_vano_economico_ajustes()
        
        if ajustes:
            vano_min = ajustes.get("vano_min", vano_min)
            vano_max = ajustes.get("vano_max", vano_max)
            salto = ajustes.get("salto", salto)
            longtraza = ajustes.get("longtraza", longtraza)
            criterio_rr = ajustes.get("criterio_rr", criterio_rr)
            rr_cada_x_m = ajustes.get("rr_cada_x_m", rr_cada_x_m)
            rr_cada_x_s = ajustes.get("rr_cada_x_s", rr_cada_x_s)
            cant_rr_manual = ajustes.get("cant_rr_manual", cant_rr_manual)
        
        print(f"🔵 DEBUG: Usando ajustes - vano_min={vano_min}, vano_max={vano_max}, salto={salto}")
        
        # Validar inputs obligatorios
        campos_faltantes = []
        if not vano_min: campos_faltantes.append("vano_min")
        if not vano_max: campos_faltantes.append("vano_max")
        if not salto: campos_faltantes.append("salto")
        if not longtraza: campos_faltantes.append("longtraza")
        if not criterio_rr: campos_faltantes.append("criterio_rr")
        
        if campos_faltantes:
            print(f"❌ DEBUG: Campos faltantes: {campos_faltantes}")
            return (no_update, 0, {"display": "none"}, True, "Error", 
                   f"Complete: {', '.join(campos_faltantes)}", "danger", "danger")
        
        if vano_max <= vano_min:
            return (no_update, 0, {"display": "none"}, True, "Error", 
                   "Vano máximo debe ser mayor que vano mínimo", "danger", "danger")
        
        # Cargar familia activa
        state = AppState()
        nombre_familia = state.get_familia_activa()
        
        if not nombre_familia:
            return (no_update, 0, {"display": "none"}, True, "Error", 
                   "No hay familia activa. Seleccione una familia primero.", "danger", "danger")
        
        try:
            print(f"🚀 Iniciando cálculo de vano económico para familia: {nombre_familia}")
            
            # Ejecutar cálculo iterativo con generar_plots
            from utils.vano_economico_utils import calcular_vano_economico_iterativo, generar_vista_resultados_vano_economico
            resultados = calcular_vano_economico_iterativo(
                nombre_familia, vano_min, vano_max, salto,
                longtraza, criterio_rr, 
                rr_cada_x_m, rr_cada_x_s, cant_rr_manual, generar_plots
            )
            
            # Guardar en cache
            parametros = {
                "nombre_familia": nombre_familia,
                "vano_min": vano_min,
                "vano_max": vano_max,
                "salto": salto,
                "longtraza": longtraza,
                "criterio_rr": criterio_rr,
                "rr_cada_x_m": rr_cada_x_m,
                "rr_cada_x_s": rr_cada_x_s,
                "cant_rr_manual": cant_rr_manual
            }
            CalculoCache.guardar_calculo_vano_economico(nombre_familia, parametros, resultados)
            
            # Generar vista de resultados
            vista_resultados = generar_vista_resultados_vano_economico(resultados)
            
            return (vista_resultados, 100, {"display": "block"}, True, "Éxito", 
                   "Cálculo de vano económico completado", "success", "success")
            
        except Exception as e:
            import traceback
            print(f"❌ ERROR: {traceback.format_exc()}")
            return (no_update, 0, {"display": "none"}, True, "Error", 
                   f"Error: {str(e)}", "danger", "danger")
    
    @app.callback(
        [Output("vano-economico-resultados", "children", allow_duplicate=True),
         Output("vano-economico-progress", "value", allow_duplicate=True),
         Output("vano-economico-progress-container", "style", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("vano-economico-btn-cargar-cache", "n_clicks"),
        prevent_initial_call=True
    )
    def cargar_cache_vano_economico(n_clicks):
        """Cargar resultados desde cache"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        try:
            state = AppState()
            nombre_familia = state.get_familia_activa()
            
            if not nombre_familia:
                return (no_update, 0, {"display": "none"}, True, "Error", 
                       "No hay familia activa", "danger", "danger")
            
            calculo_guardado = CalculoCache.cargar_calculo_vano_economico(nombre_familia)
            
            if not calculo_guardado:
                return (no_update, 0, {"display": "none"}, True, "Advertencia", 
                       "No hay cache disponible para esta familia", "warning", "warning")
            
            from utils.vano_economico_utils import generar_vista_resultados_vano_economico
            vista_resultados = generar_vista_resultados_vano_economico(calculo_guardado["resultados"])
            
            return (vista_resultados, 100, {"display": "block"}, True, "Éxito", 
                   "Cache cargado correctamente", "success", "success")
            
        except Exception as e:
            import traceback
            print(f"❌ ERROR: {traceback.format_exc()}")
            return (no_update, 0, {"display": "none"}, True, "Error", 
                   f"Error: {str(e)}", "danger", "danger")
