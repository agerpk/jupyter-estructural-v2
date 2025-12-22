"""Controlador de gestión de estructuras"""

import dash
from dash import Input, Output, State
from models.app_state import AppState
from config.app_config import DATA_DIR


def register_callbacks(app):
    """Registrar callbacks de gestión de estructuras"""
    
    state = AppState()
    
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-cargar-db", "n_clicks"),
        State("select-estructura-db", "value"),
        prevent_initial_call=True
    )
    def cargar_estructura_desde_db(n_clicks, nombre_estructura):
        if not nombre_estructura:
            return dash.no_update, True, "Error", "Seleccione una estructura", "danger", "danger"
        
        try:
            ruta_estructura = DATA_DIR / nombre_estructura
            estructura = state.estructura_manager.cargar_estructura(ruta_estructura)
            
            if estructura:
                # Limpiar nodos_editados si no tiene el campo o está vacío
                if "nodos_editados" not in estructura or not estructura["nodos_editados"]:
                    estructura["nodos_editados"] = []
                
                # GUARDAR EN ACTUAL.ESTRUCTURA.JSON
                state.estructura_manager.guardar_estructura(estructura, state.archivo_actual)
                
                # TAMBIÉN GUARDAR EN TITULO.ESTRUCTURA.JSON
                if "TITULO" in estructura:
                    titulo = estructura["TITULO"]
                    nombre_archivo = f"{titulo}.estructura.json"
                    state.estructura_manager.guardar_estructura(estructura, DATA_DIR / nombre_archivo)
                
                return estructura, True, "Éxito", f"Estructura '{nombre_estructura}' cargada correctamente", "success", "success"
        except Exception as e:
            print(f"❌ Error cargando estructura: {e}")
        
        return dash.no_update, True, "Error", "No se pudo cargar la estructura", "danger", "danger"
    
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-como-confirmar", "n_clicks"),
        State("input-titulo-nuevo", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_estructura_como(n_clicks, nuevo_titulo, estructura_actual):
        if not nuevo_titulo or not nuevo_titulo.strip():
            return dash.no_update, True, "Error", "Ingrese un título válido", "danger", "danger"
        
        try:
            titulo_origen = estructura_actual.get("TITULO", "")
            estructura_actualizada = estructura_actual.copy()
            estructura_actualizada["TITULO"] = nuevo_titulo.strip()
            
            nombre_archivo = f"{nuevo_titulo.strip()}.estructura.json"
            ruta_destino = DATA_DIR / nombre_archivo
            
            state.estructura_manager.guardar_estructura(estructura_actualizada, ruta_destino)
            state.estructura_manager.guardar_estructura(estructura_actualizada, state.archivo_actual)
            
            # Copiar hipótesis de estructura origen si existen
            from utils.hipotesis_manager import HipotesisManager
            HipotesisManager.copiar_hipotesis_guardar_como(
                titulo_origen,
                nuevo_titulo.strip(),
                str(ruta_destino)
            )
            
            return estructura_actualizada, True, "Éxito", f"Estructura guardada como '{nuevo_titulo}'", "success", "success"
        except Exception as e:
            print(f"Error guardando estructura: {e}")
        
        return dash.no_update, True, "Error", "No se pudo guardar la estructura", "danger", "danger"
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-plantilla-confirmar", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_como_plantilla(n_clicks, estructura_actual):
        try:
            state.estructura_manager.guardar_estructura(estructura_actual, state.estructura_manager.plantilla_path)
            return True, "Éxito", "Plantilla actualizada correctamente", "success", "success"
        except Exception as e:
            print(f"Error guardando plantilla: {e}")
            return True, "Error", "No se pudo guardar la plantilla", "danger", "danger"
    
    @app.callback(
        Output("modal-nueva-estructura", "is_open"),
        Output("input-nombre-nueva-estructura", "value"),
        Input("menu-nueva-estructura", "n_clicks"),
        Input("btn-cancelar-nueva", "n_clicks"),
        Input("btn-crear-nueva-confirmar", "n_clicks"),
        State("modal-nueva-estructura", "is_open"),
        prevent_initial_call=True
    )
    def toggle_modal_nueva_estructura(abrir, cancelar, crear, is_open):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open, ""
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "menu-nueva-estructura":
            return True, ""
        elif trigger_id in ["btn-cancelar-nueva", "btn-crear-nueva-confirmar"]:
            return False, ""
        
        return is_open, ""
    
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-crear-nueva-confirmar", "n_clicks"),
        State("input-nombre-nueva-estructura", "value"),
        prevent_initial_call=True
    )
    def crear_nueva_estructura_callback(n_clicks, nombre):
        if not nombre or not nombre.strip():
            return dash.no_update, True, "Error", "Ingrese un nombre válido", "danger", "danger"
        
        try:
            nueva_estructura = state.estructura_manager.crear_nueva_estructura(titulo=nombre.strip())
            
            # GUARDAR EN ACTUAL.ESTRUCTURA.JSON
            state.estructura_manager.guardar_estructura(nueva_estructura, state.archivo_actual)
            
            # TAMBIÉN GUARDAR EN TITULO.ESTRUCTURA.JSON
            titulo = nueva_estructura["TITULO"]
            nombre_archivo = f"{titulo}.estructura.json"
            state.estructura_manager.guardar_estructura(nueva_estructura, DATA_DIR / nombre_archivo)
            
            return nueva_estructura, True, "Éxito", f"Nueva estructura '{nombre.strip()}' creada", "success", "success"
        except Exception as e:
            return dash.no_update, True, "Error", f"Error al crear estructura: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Output("estructuras-disponibles", "data", allow_duplicate=True),
        Input("menu-guardar-estructura", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_estructura_db(n_clicks, estructura_actual):
        if estructura_actual and "TITULO" in estructura_actual:
            try:
                titulo = estructura_actual["TITULO"]
                nombre_archivo = f"{titulo}.estructura.json"
                state.estructura_manager.guardar_estructura(estructura_actual, DATA_DIR / nombre_archivo)
                state.estructura_manager.guardar_estructura(estructura_actual, state.archivo_actual)
                estructuras = state.estructura_manager.listar_estructuras()
                return True, "Éxito", f"Estructura guardada: {nombre_archivo}", "success", "success", estructuras
            except Exception as e:
                return True, "Error", f"Error al guardar: {str(e)}", "danger", "danger", dash.no_update
        return True, "Error", "No hay estructura para guardar", "danger", "danger", dash.no_update
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Output("contenido-principal", "children", allow_duplicate=True),
        Input("btn-eliminar-estructura", "n_clicks"),
        State("select-estructura-eliminar", "value"),
        prevent_initial_call=True
    )
    def eliminar_estructura_callback(n_clicks, nombre_estructura):
        if n_clicks is None or not nombre_estructura:
            raise dash.exceptions.PreventUpdate
        
        try:
            from components.vista_home import crear_vista_home
            exito = state.estructura_manager.eliminar_estructura(nombre_estructura)
            
            if exito:
                return True, "Éxito", f"Estructura '{nombre_estructura}' eliminada correctamente", "success", "success", crear_vista_home()
            else:
                return True, "Error", f"No se pudo eliminar la estructura '{nombre_estructura}'", "danger", "danger", dash.no_update
        except Exception as e:
            print(f"Error eliminando estructura: {e}")
            return True, "Error", f"Error al eliminar la estructura: {str(e)}", "danger", "danger", dash.no_update
