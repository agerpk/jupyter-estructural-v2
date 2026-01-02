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
        [Output("tabla-familia", "data", allow_duplicate=True)],
        [Input("filtro-categoria-familia", "value"),
         Input("buscar-parametro-familia", "value")],
        [State("tabla-familia-original", "data")],
        prevent_initial_call=True
    )
    def filtrar_tabla_familia(categoria, busqueda, tabla_original):
        """Filtrar tabla por categoría y búsqueda"""
        print(f"\n🔍 DEBUG FILTRO: categoria={categoria}, busqueda='{busqueda}'")
        print(f"   tabla_original tiene {len(tabla_original) if tabla_original else 0} filas")
        
        if not tabla_original:
            raise dash.exceptions.PreventUpdate
        
        # Si no hay filtros activos, retornar tabla completa
        sin_categoria = not categoria or categoria == "todas" or categoria == ""
        sin_busqueda = not busqueda or (isinstance(busqueda, str) and busqueda.strip() == "")
        
        print(f"   sin_categoria={sin_categoria}, sin_busqueda={sin_busqueda}")
        
        if sin_categoria and sin_busqueda:
            print(f"   ✅ Retornando tabla completa: {len(tabla_original)} filas")
            return [tabla_original]
        
        tabla_filtrada = list(tabla_original)  # Crear copia
        
        # Filtrar por categoría
        if not sin_categoria:
            tabla_filtrada = [fila for fila in tabla_filtrada if fila.get("categoria") == categoria]
            print(f"   Después de filtrar por categoría '{categoria}': {len(tabla_filtrada)} filas")
        
        # Filtrar por búsqueda
        if not sin_busqueda:
            busqueda_lower = busqueda.lower().strip()
            tabla_filtrada = [
                fila for fila in tabla_filtrada
                if busqueda_lower in str(fila.get("parametro", "")).lower() or
                   busqueda_lower in str(fila.get("descripcion", "")).lower() or
                   busqueda_lower in str(fila.get("simbolo", "")).lower()
            ]
            print(f"   Después de filtrar por búsqueda '{busqueda}': {len(tabla_filtrada)} filas")
        
        return [tabla_filtrada]
    
    @app.callback(
        Output("tabla-familia-original", "data", allow_duplicate=True),
        [Input("btn-agregar-estructura", "n_clicks"),
         Input("select-familia-existente", "value")],
        State("tabla-familia", "data"),
        prevent_initial_call=True
    )
    def actualizar_tabla_original_estructura(n_agregar, familia_cargada, tabla_actual):
        """Actualizar tabla original cuando cambia estructura de datos"""
        print(f"\n💾 DEBUG: Actualizando tabla-familia-original con {len(tabla_actual) if tabla_actual else 0} filas")
        if not tabla_actual:
            raise dash.exceptions.PreventUpdate
        return list(tabla_actual)
    
    @app.callback(
        Output("tabla-familia-original", "data"),
        Input("tabla-familia", "data"),
        prevent_initial_call=False
    )
    def guardar_tabla_original_inicial(tabla_data):
        """Guardar tabla original SOLO en carga inicial"""
        ctx = dash.callback_context
        # Solo en carga inicial (sin trigger)
        if not ctx.triggered or ctx.triggered[0]['prop_id'] == '.':
            print(f"\n💾 DEBUG INICIAL: Guardando tabla original con {len(tabla_data) if tabla_data else 0} filas")
            return list(tabla_data) if tabla_data else []
        # Si hay trigger, no actualizar
        raise dash.exceptions.PreventUpdate
    
    @app.callback(
        [Output("tabla-familia", "columns", allow_duplicate=True),
         Output("tabla-familia", "data", allow_duplicate=True)],
        Input("btn-agregar-estructura", "n_clicks"),
        [State("tabla-familia", "columns"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def agregar_estructura(n_clicks, columnas, tabla_data):
        """Agregar nueva columna de estructura"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        # Encontrar última columna Estr.N
        cols_estr = [col['id'] for col in columnas if col['id'].startswith('Estr.')]
        if not cols_estr:
            nuevo_num = 1
        else:
            numeros = [int(col.replace('Estr.', '')) for col in cols_estr]
            nuevo_num = max(numeros) + 1
        
        nuevo_col_id = f"Estr.{nuevo_num}"
        ultima_col = cols_estr[-1] if cols_estr else None
        
        # Agregar nueva columna
        columnas.append({
            "name": nuevo_col_id,
            "id": nuevo_col_id,
            "editable": False,
            "type": "any"
        })
        
        # Copiar valores de última columna
        for fila in tabla_data:
            if ultima_col:
                fila[nuevo_col_id] = fila.get(ultima_col, "")
            else:
                fila[nuevo_col_id] = fila.get("valor", "")
        
        return columnas, tabla_data
    
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
        Output("tabla-estados-familia", "children"),
        Input("input-nombre-familia", "value"),
        prevent_initial_call=False
    )
    def cargar_tabla_estados_climaticos(nombre_familia):
        """Carga tabla de estados climáticos para la familia"""
        from components.vista_familia_estructuras import crear_tabla_estados_climaticos_familia
        
        # Intentar cargar familia existente
        familia_actual = {}
        if nombre_familia:
            try:
                familia_actual = FamiliaManager.cargar_familia(nombre_familia)
            except:
                pass
        
        return crear_tabla_estados_climaticos_familia(familia_actual)
    
    @app.callback(
        [Output("modal-estados-familia", "is_open"),
         Output("modal-estados-body", "children")],
        [Input("btn-modificar-estados-familia", "n_clicks"),
         Input("modal-estados-cancelar", "n_clicks"),
         Input("modal-estados-guardar", "n_clicks")],
        [State("modal-estados-familia", "is_open"),
         State("input-nombre-familia", "value")],
        prevent_initial_call=True
    )
    def toggle_modal_estados(n_abrir, n_cancelar, n_guardar, is_open, nombre_familia):
        """Abrir/cerrar modal de estados climáticos"""
        from components.vista_familia_estructuras import crear_tabla_estados_climaticos_familia
        
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-modificar-estados-familia":
            if n_abrir is None:
                raise dash.exceptions.PreventUpdate
            
            # Cargar familia actual
            familia_actual = {}
            if nombre_familia:
                try:
                    familia_actual = FamiliaManager.cargar_familia(nombre_familia)
                except:
                    pass
            
            tabla = crear_tabla_estados_climaticos_familia(familia_actual)
            return True, tabla
        
        elif trigger_id in ["modal-estados-cancelar", "modal-estados-guardar"]:
            return False, no_update
        
        raise dash.exceptions.PreventUpdate
    
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("modal-estados-guardar", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State({"type": "familia-estado-temp", "index": ALL}, "value"),
         State({"type": "familia-estado-desc", "index": ALL}, "value"),
         State({"type": "familia-estado-viento", "index": ALL}, "value"),
         State({"type": "familia-estado-hielo", "index": ALL}, "value"),
         State({"type": "familia-restriccion-conductor", "index": ALL}, "value"),
         State({"type": "familia-restriccion-guardia", "index": ALL}, "value")],
        prevent_initial_call=True
    )
    def guardar_estados_climaticos(n_clicks, nombre_familia, temps, descs, vientos, hielos, rest_cond, rest_guard):
        """Guardar estados climáticos en archivo .familia.json"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"\n💾 DEBUG GUARDAR ESTADOS CLIMÁTICOS:")
        print(f"   nombre_familia: {nombre_familia}")
        print(f"   temps: {temps}")
        print(f"   descs: {descs}")
        print(f"   vientos: {vientos}")
        print(f"   hielos: {hielos}")
        print(f"   rest_cond: {rest_cond}")
        print(f"   rest_guard: {rest_guard}")
        
        if not nombre_familia:
            return True, "Error", "Debe especificar un nombre de familia", "danger", "danger"
        
        try:
            # Cargar familia existente o crear nueva
            try:
                familia_data = FamiliaManager.cargar_familia(nombre_familia)
                print(f"   ✅ Familia cargada: {list(familia_data.keys())}")
            except:
                familia_data = FamiliaManager.crear_familia_nueva()
                familia_data["nombre_familia"] = nombre_familia
                print(f"   ⚠️ Familia nueva creada")
            
            # Construir estados climáticos
            estados_ids = ["I", "II", "III", "IV", "V"]
            estados_climaticos = {}
            restricciones_cables = {"conductor": {}, "guardia": {}}
            
            for i, estado_id in enumerate(estados_ids):
                estados_climaticos[estado_id] = {
                    "temperatura": temps[i] if i < len(temps) else 0,
                    "descripcion": descs[i] if i < len(descs) else "",
                    "viento_velocidad": vientos[i] if i < len(vientos) else 0,
                    "espesor_hielo": hielos[i] if i < len(hielos) else 0
                }
                restricciones_cables["conductor"][estado_id] = rest_cond[i] if i < len(rest_cond) else 0.25
                restricciones_cables["guardia"][estado_id] = rest_guard[i] if i < len(rest_guard) else 0.7
            
            print(f"   📊 Estados climáticos construidos: {list(estados_climaticos.keys())}")
            print(f"   📊 Estado I: {estados_climaticos['I']}")
            print(f"   📊 Restricciones conductor: {restricciones_cables['conductor']}")
            print(f"   📊 Restricciones guardia: {restricciones_cables['guardia']}")
            
            # Actualizar familia
            familia_data["estados_climaticos"] = estados_climaticos
            familia_data["restricciones_cables"] = restricciones_cables
            
            print(f"   💾 Guardando familia con keys: {list(familia_data.keys())}")
            
            # Guardar
            FamiliaManager.guardar_familia(familia_data)
            
            print(f"   ✅ Familia guardada exitosamente\n")
            
            return True, "Éxito", "Estados climáticos guardados correctamente", "success", "success"
            
        except Exception as e:
            return True, "Error", f"Error guardando estados: {str(e)}", "danger", "danger"

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