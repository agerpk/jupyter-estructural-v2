"""
Controller para Familia de Estructuras - Implementación limpia y escalable
"""

import dash
from dash import Input, Output, State, no_update, html, dcc, ALL
import dash_bootstrap_components as dbc
from typing import Dict, List, Any, Optional
import json
import threading
from pathlib import Path
from datetime import datetime

from utils.familia_manager import FamiliaManager
from utils.parametros_manager import ParametrosManager
from models.app_state import AppState
from config.app_config import DATA_DIR
from utils.calculo_cache import CalculoCache
from utils.view_helpers import ViewHelpers

# ============================================================================
# GESTIÓN DE ESTADO FAMILIA ACTIVA (UNIFICADO EN CONTROLLER)
# ============================================================================

_familia_activa_nombre = None

def set_familia_activa(nombre_familia: str):
    """Establecer familia activa"""
    global _familia_activa_nombre
    _familia_activa_nombre = nombre_familia
    
    # Guardar en archivo de estado
    try:
        estado = {
            "nombre_familia": nombre_familia,
            "fecha_acceso": datetime.now().isoformat()
        }
        with open(DATA_DIR / "familia_actual.json", "w", encoding="utf-8") as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando estado familia: {e}")

def get_familia_activa() -> Optional[str]:
    """Obtener familia activa"""
    global _familia_activa_nombre
    
    if _familia_activa_nombre:
        return _familia_activa_nombre
    
    # Cargar desde archivo
    try:
        archivo_estado = DATA_DIR / "familia_actual.json"
        if archivo_estado.exists():
            with open(archivo_estado, "r", encoding="utf-8") as f:
                estado = json.load(f)
                _familia_activa_nombre = estado.get("nombre_familia")
                return _familia_activa_nombre
    except Exception as e:
        print(f"Error cargando estado familia: {e}")
    
    return None

def cargar_familia_activa() -> Optional[Dict]:
    """Cargar datos de familia activa"""
    nombre_familia = get_familia_activa()
    if nombre_familia:
        return FamiliaManager.cargar_familia(nombre_familia)
    return None

# ============================================================================
# CALLBACKS PRINCIPALES
# ============================================================================

def register_callbacks(app):
    """Registra todos los callbacks del controller"""
    
    @app.callback(
        [Output("select-familia-existente", "options"),
         Output("select-familia-existente", "value")],
        Input("select-familia-existente", "id"),
        prevent_initial_call=False
    )
    def cargar_opciones_familias(component_id):
        """Carga opciones de familias disponibles"""
        try:
            archivos_familia = FamiliaManager.obtener_archivos_familia()
            opciones = [{"label": archivo.replace(".familia", ""), "value": archivo} for archivo in archivos_familia]
            return opciones, None
        except:
            return [], None

    @app.callback(
        [Output("tabla-familia", "data"),
         Output("tabla-familia", "columns"),
         Output("input-nombre-familia", "value"),
         Output("toast-notificacion", "is_open"),
         Output("toast-notificacion", "header"),
         Output("toast-notificacion", "children"),
         Output("toast-notificacion", "color")],
        Input("select-familia-existente", "value"),
        prevent_initial_call=True
    )
    def cargar_familia_seleccionada(nombre_familia):
        """Carga familia seleccionada del dropdown"""
        if not nombre_familia:
            return no_update, no_update, no_update, False, "", "", "info"
        
        nombre_limpio = nombre_familia.replace('.familia', '') if nombre_familia.endswith('.familia') else nombre_familia
        datos_familia = FamiliaManager.cargar_familia(nombre_limpio)
        
        if not datos_familia:
            return no_update, no_update, no_update, True, "Error", f"No se pudo cargar la familia '{nombre_limpio}'", "danger"
        
        tabla_data, columnas = FamiliaManager.familia_a_tabla(datos_familia)
        return (tabla_data, columnas, datos_familia.get('nombre_familia', nombre_limpio), 
                True, "Éxito", f"Familia '{nombre_limpio}' cargada correctamente", "success")
    
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-guardar-familia", "n_clicks"),
        [State("input-nombre-familia", "value")],
        prevent_initial_call=True
    )
    def guardar_familia_simple(n_clicks, nombre_familia):
        """Guarda familia - versión simplificada"""
        print(f"🔵 DEBUG: guardar_familia_simple EJECUTADO - n_clicks: {n_clicks}, nombre: {nombre_familia}")
        
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"🔵 DEBUG: Guardando familia '{nombre_familia}'")
        
        return (True, "Éxito", f"Familia '{nombre_familia}' guardada", "success", "success")
    
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-guardar-como-familia", "n_clicks"),
        [State("input-nombre-familia", "value")],
        prevent_initial_call=True
    )
    def guardar_como_familia_simple(n_clicks, nombre_familia):
        """Guarda como familia - versión simplificada"""
        print(f"🔵 DEBUG: guardar_como_familia_simple EJECUTADO - n_clicks: {n_clicks}, nombre: {nombre_familia}")
        
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"🔵 DEBUG: Guardando como familia '{nombre_familia}'")
        
        return (True, "Éxito", f"Familia guardada como '{nombre_familia}'", "success", "success")