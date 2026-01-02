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
    
    @app.callback(
        [Output("resultados-familia", "children"),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-calcular-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("tabla-familia", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def calcular_familia_completa(n_clicks, nombre_familia, tabla_data, columnas):
        """Ejecuta cálculo completo de familia"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"🚀 INICIANDO CÁLCULO FAMILIA: {nombre_familia}")
        
        try:
            # Validar datos
            if not nombre_familia or not tabla_data or not columnas:
                return (no_update, True, "Error", "Faltan datos para calcular", "danger", "danger")
            
            # Convertir tabla a formato familia
            familia_data = FamiliaManager.tabla_a_familia(tabla_data, columnas, nombre_familia)
            
            # Ejecutar cálculo usando utilidad
            from utils.calcular_familia_logica_encadenada import ejecutar_calculo_familia_completa
            resultados_familia = ejecutar_calculo_familia_completa(familia_data)
            
            if not resultados_familia.get("exito"):
                return (no_update, True, "Error", f"Error en cálculo: {resultados_familia.get('mensaje')}", "danger", "danger")
            
            # Generar vista con pestañas
            from utils.calcular_familia_logica_encadenada import generar_vista_resultados_familia
            vista_resultados = generar_vista_resultados_familia(resultados_familia)
            
            return (vista_resultados, True, "Éxito", "Cálculo de familia completado", "success", "success")
            
        except Exception as e:
            import traceback
            print(f"❌ ERROR: {traceback.format_exc()}")
            return (no_update, True, "Error", f"Error: {str(e)}", "danger", "danger")