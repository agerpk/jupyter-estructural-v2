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
        [Output("tabla-familia", "data", allow_duplicate=True),
         Output("tabla-familia", "page_current", allow_duplicate=True)],
        [Input("filtro-categoria-familia", "value"),
         Input("buscar-parametro-familia", "value")],
        [State("tabla-familia-original", "data")],
        prevent_initial_call=True
    )
    def filtrar_tabla_familia(categoria, busqueda, tabla_original):
        """Filtrar tabla por categoría y búsqueda"""
        if not tabla_original:
            raise dash.exceptions.PreventUpdate
        
        sin_categoria = not categoria or categoria == "todas" or categoria == ""
        sin_busqueda = not busqueda or (isinstance(busqueda, str) and busqueda.strip() == "")
        
        if sin_categoria and sin_busqueda:
            return tabla_original, 0
        
        tabla_filtrada = list(tabla_original)
        
        if not sin_categoria:
            tabla_filtrada = [fila for fila in tabla_filtrada if fila.get("categoria") == categoria]
        
        if not sin_busqueda:
            busqueda_lower = busqueda.lower().strip()
            tabla_filtrada = [
                fila for fila in tabla_filtrada
                if busqueda_lower in str(fila.get("parametro", "")).lower() or
                   busqueda_lower in str(fila.get("descripcion", "")).lower() or
                   busqueda_lower in str(fila.get("simbolo", "")).lower()
            ]
        
        return tabla_filtrada, 0
    
    @app.callback(
        Output("tabla-familia-original", "data", allow_duplicate=True),
        [Input("btn-agregar-estructura", "n_clicks"),
         Input("btn-eliminar-estructura", "n_clicks"),
         Input("select-familia-existente", "value")],
        State("tabla-familia", "data"),
        prevent_initial_call=True
    )
    def actualizar_tabla_original_estructura(n_agregar, n_eliminar, familia_cargada, tabla_actual):
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
         Output("tabla-familia", "data", allow_duplicate=True),
         Output("tabla-familia-original", "data", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-agregar-estructura", "n_clicks"),
        [State("tabla-familia", "columns"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def agregar_estructura_tabla(n_agregar, columnas, tabla_data):
        """Agregar columna de estructura"""
        if n_agregar is None:
            raise dash.exceptions.PreventUpdate
        
        cols_estr = [col['id'] for col in columnas if col['id'].startswith('Estr.')]
        
        if not cols_estr:
            nuevo_num = 1
        else:
            numeros = [int(col.replace('Estr.', '')) for col in cols_estr]
            nuevo_num = max(numeros) + 1
        
        nuevo_col_id = f"Estr.{nuevo_num}"
        ultima_col = cols_estr[-1] if cols_estr else None
        
        columnas.append({
            "name": nuevo_col_id,
            "id": nuevo_col_id,
            "editable": True,
            "type": "any"
        })
        
        for fila in tabla_data:
            if ultima_col:
                fila[nuevo_col_id] = fila.get(ultima_col, "")
            else:
                fila[nuevo_col_id] = fila.get("valor", "")
        
        return columnas, tabla_data, list(tabla_data), True, "Éxito", f"Estructura {nuevo_col_id} agregada", "success", "success"
    
    @app.callback(
        [Output("modal-eliminar-estructura", "is_open"),
         Output("select-columna-eliminar", "options")],
        [Input("btn-eliminar-estructura", "n_clicks"),
         Input("modal-eliminar-estructura-cancelar", "n_clicks"),
         Input("modal-eliminar-estructura-confirmar", "n_clicks")],
        [State("modal-eliminar-estructura", "is_open"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def toggle_modal_eliminar_estructura(n_abrir, n_cancelar, n_confirmar, is_open, columnas):
        """Abrir/cerrar modal de eliminar estructura"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-eliminar-estructura":
            if n_abrir is None:
                raise dash.exceptions.PreventUpdate
            
            cols_estr = [col['id'] for col in columnas if col['id'].startswith('Estr.')]
            opciones_columnas = [{"label": col, "value": col} for col in cols_estr]
            
            return True, opciones_columnas
        
        elif trigger_id in ["modal-eliminar-estructura-cancelar", "modal-eliminar-estructura-confirmar"]:
            return False, no_update
        
        raise dash.exceptions.PreventUpdate
    
    @app.callback(
        [Output("tabla-familia", "columns", allow_duplicate=True),
         Output("tabla-familia", "data", allow_duplicate=True),
         Output("tabla-familia-original", "data", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("modal-eliminar-estructura-confirmar", "n_clicks"),
        [State("select-columna-eliminar", "value"),
         State("tabla-familia", "columns"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def eliminar_estructura_confirmado(n_clicks, col_eliminar, columnas, tabla_data):
        """Eliminar estructura tras confirmación"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        if not col_eliminar:
            return no_update, no_update, no_update, True, "Error", "Debe seleccionar una columna", "danger", "danger"
        
        cols_estr = [col['id'] for col in columnas if col['id'].startswith('Estr.')]
        if len(cols_estr) <= 1:
            return no_update, no_update, no_update, True, "Advertencia", "Debe mantener al menos una estructura", "warning", "warning"
        
        columnas = [col for col in columnas if col['id'] != col_eliminar]
        
        for fila in tabla_data:
            if col_eliminar in fila:
                del fila[col_eliminar]
        
        return columnas, tabla_data, list(tabla_data), True, "Éxito", f"Estructura {col_eliminar} eliminada", "success", "success"
    
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
        
        # Establecer familia activa en AppState
        state = AppState()
        state.set_familia_activa(nombre_limpio)
        
        tabla_data, columnas = FamiliaManager.familia_a_tabla(datos_familia)
        return (tabla_data, columnas, datos_familia.get('nombre_familia', nombre_limpio), 
                True, "Éxito", f"Familia '{nombre_limpio}' cargada correctamente", "success")
    
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True),
         Output("select-familia-existente", "options", allow_duplicate=True)],
        Input("btn-guardar-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("tabla-familia", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def guardar_familia(n_clicks, nombre_familia, tabla_data, columnas):
        """Guarda familia con datos actuales de tabla"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        if not nombre_familia:
            return True, "Error", "Debe especificar un nombre de familia", "danger", "danger", no_update
        
        try:
            # Convertir tabla a formato familia
            familia_data = FamiliaManager.tabla_a_familia(tabla_data, columnas, nombre_familia)
            
            # Guardar
            FamiliaManager.guardar_familia(familia_data)
            
            # Establecer como familia activa
            state = AppState()
            state.set_familia_activa(nombre_familia)
            
            # Actualizar opciones dropdown
            archivos_familia = FamiliaManager.obtener_archivos_familia()
            opciones = [{"label": archivo.replace(".familia", ""), "value": archivo} for archivo in archivos_familia]
            
            return True, "Éxito", f"Familia '{nombre_familia}' guardada", "success", "success", opciones
            
        except Exception as e:
            return True, "Error", f"Error guardando: {str(e)}", "danger", "danger", no_update
    
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True),
         Output("select-familia-existente", "options", allow_duplicate=True)],
        Input("btn-guardar-como-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("tabla-familia", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def guardar_como_familia(n_clicks, nombre_familia, tabla_data, columnas):
        """Guarda como nueva familia con datos actuales de tabla"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        if not nombre_familia:
            return True, "Error", "Debe especificar un nombre de familia", "danger", "danger", no_update
        
        try:
            # Convertir tabla a formato familia con nombre exacto
            familia_data = FamiliaManager.tabla_a_familia(tabla_data, columnas, nombre_familia)
            
            # Guardar con nombre exacto
            FamiliaManager.guardar_familia(familia_data)
            
            # Establecer como familia activa
            state = AppState()
            state.set_familia_activa(nombre_familia)
            
            # Actualizar opciones dropdown
            archivos_familia = FamiliaManager.obtener_archivos_familia()
            opciones = [{"label": archivo.replace(".familia", ""), "value": archivo} for archivo in archivos_familia]
            
            return True, "Éxito", f"Familia guardada como '{nombre_familia}'", "success", "success", opciones
            
        except Exception as e:
            return True, "Error", f"Error guardando: {str(e)}", "danger", "danger", no_update
    
    @app.callback(
        [Output("modal-eliminar-familia", "is_open"),
         Output("modal-eliminar-familia-nombre", "children")],
        [Input("btn-eliminar-familia", "n_clicks"),
         Input("modal-eliminar-cancelar", "n_clicks"),
         Input("modal-eliminar-confirmar", "n_clicks")],
        [State("modal-eliminar-familia", "is_open"),
         State("input-nombre-familia", "value")],
        prevent_initial_call=True
    )
    def toggle_modal_eliminar_familia(n_abrir, n_cancelar, n_confirmar, is_open, nombre_familia):
        """Abrir/cerrar modal de eliminar familia"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-eliminar-familia":
            if n_abrir is None or not nombre_familia:
                raise dash.exceptions.PreventUpdate
            return True, nombre_familia
        
        elif trigger_id in ["modal-eliminar-cancelar", "modal-eliminar-confirmar"]:
            return False, no_update
        
        raise dash.exceptions.PreventUpdate
    
    @app.callback(
        [Output("input-nombre-familia", "value", allow_duplicate=True),
         Output("tabla-familia", "data", allow_duplicate=True),
         Output("tabla-familia", "columns", allow_duplicate=True),
         Output("select-familia-existente", "options", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("modal-eliminar-confirmar", "n_clicks"),
        State("input-nombre-familia", "value"),
        prevent_initial_call=True
    )
    def eliminar_familia_confirmado(n_clicks, nombre_familia):
        """Eliminar familia tras confirmación"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        if not nombre_familia:
            return no_update, no_update, no_update, no_update, True, "Error", "No hay familia seleccionada", "danger", "danger"
        
        try:
            # Eliminar familia
            exito = FamiliaManager.eliminar_familia(nombre_familia)
            
            if not exito:
                return no_update, no_update, no_update, no_update, True, "Error", f"No se pudo eliminar familia '{nombre_familia}'", "danger", "danger"
            
            # Crear familia nueva vacía
            familia_nueva = FamiliaManager.crear_familia_nueva()
            from components.vista_familia_estructuras import generar_datos_tabla_familia
            tabla_data = generar_datos_tabla_familia(familia_nueva)
            
            # Columnas base
            columnas = [
                {"name": "Categoría", "id": "categoria", "editable": False},
                {"name": "Parámetro", "id": "parametro", "editable": False},
                {"name": "Símbolo", "id": "simbolo", "editable": False},
                {"name": "Unidad", "id": "unidad", "editable": False},
                {"name": "Descripción", "id": "descripcion", "editable": False},
                {"name": "Estr.1", "id": "Estr.1", "editable": True} # SIEMPRE EDITABLES
            ]
            
            # Actualizar opciones de familias
            archivos_familia = FamiliaManager.obtener_archivos_familia()
            opciones = [{"label": archivo.replace(".familia", ""), "value": archivo} for archivo in archivos_familia]
            
            return "", tabla_data, columnas, opciones, True, "Éxito", f"Familia '{nombre_familia}' eliminada", "success", "success"
            
        except Exception as e:
            return no_update, no_update, no_update, no_update, True, "Error", f"Error: {str(e)}", "danger", "danger"
    
    @app.callback(
        [Output("modal-cargar-columna", "is_open"),
         Output("select-estructura-cargar-columna", "options"),
         Output("select-columna-destino", "options")],
        [Input("btn-cargar-columna", "n_clicks"),
         Input("modal-cargar-columna-cancelar", "n_clicks"),
         Input("modal-cargar-columna-confirmar", "n_clicks")],
        [State("modal-cargar-columna", "is_open"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def toggle_modal_cargar_columna(n_abrir, n_cancelar, n_confirmar, is_open, columnas):
        """Abrir/cerrar modal de cargar columna"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-cargar-columna":
            if n_abrir is None:
                raise dash.exceptions.PreventUpdate
            
            # Obtener lista de estructuras
            state = AppState()
            estructuras_disponibles = state.estructura_manager.listar_estructuras()
            opciones_estructuras = [{"label": e.replace(".estructura.json", ""), "value": e} for e in estructuras_disponibles]
            
            # Obtener columnas Estr.N
            cols_estr = [col['id'] for col in columnas if col['id'].startswith('Estr.')]
            opciones_columnas = [{"label": col, "value": col} for col in cols_estr]
            
            return True, opciones_estructuras, opciones_columnas
        
        elif trigger_id in ["modal-cargar-columna-cancelar", "modal-cargar-columna-confirmar"]:
            return False, no_update, no_update
        
        raise dash.exceptions.PreventUpdate
    
    @app.callback(
        [Output("tabla-familia", "data", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("modal-cargar-columna-confirmar", "n_clicks"),
        [State("select-estructura-cargar-columna", "value"),
         State("select-columna-destino", "value"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def cargar_estructura_en_columna(n_clicks, estructura_archivo, columna_destino, tabla_data):
        """Cargar estructura existente en columna seleccionada"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        if not estructura_archivo or not columna_destino:
            return no_update, True, "Error", "Debe seleccionar estructura y columna", "danger", "danger"
        
        try:
            # Cargar estructura
            state = AppState()
            estructura_path = DATA_DIR / estructura_archivo
            estructura_data = state.estructura_manager.cargar_estructura(estructura_path)
            
            # Actualizar valores en tabla
            for fila in tabla_data:
                parametro = fila.get("parametro")
                
                # Manejar campos anidados de costeo
                if parametro and "." in parametro:
                    partes = parametro.split(".")
                    if partes[0] == "costeo":
                        costeo_data = estructura_data.get("costeo", {})
                        if len(partes) == 3:
                            # costeo.subcampo.subsubcampo
                            subcampo_data = costeo_data.get(partes[1], {})
                            valor = subcampo_data.get(partes[2], fila.get(columna_destino, ""))
                        else:
                            # costeo.subcampo
                            valor = costeo_data.get(partes[1], fila.get(columna_destino, ""))
                        fila[columna_destino] = valor
                else:
                    # Campo simple
                    valor = estructura_data.get(parametro, fila.get(columna_destino, ""))
                    fila[columna_destino] = valor
            
            nombre_estructura = estructura_data.get("TITULO", estructura_archivo)
            return tabla_data, True, "Éxito", f"Estructura '{nombre_estructura}' cargada en {columna_destino}", "success", "success"
            
        except Exception as e:
            return no_update, True, "Error", f"Error cargando estructura: {str(e)}", "danger", "danger"
    
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
        """Ejecuta cálculo completo de familia y guarda cache"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"🚀 INICIANDO CÁLCULO FAMILIA: {nombre_familia}")
        
        try:
            if not nombre_familia or not tabla_data or not columnas:
                return (no_update, True, "Error", "Faltan datos para calcular", "danger", "danger")
            
            # Convertir tabla a formato familia
            familia_data = FamiliaManager.tabla_a_familia(tabla_data, columnas, nombre_familia)
            
            # Ejecutar cálculo
            from utils.calcular_familia_logica_encadenada import ejecutar_calculo_familia_completa
            resultados_familia = ejecutar_calculo_familia_completa(familia_data)
            
            if not resultados_familia.get("exito"):
                return (no_update, True, "Error", f"Error en cálculo: {resultados_familia.get('mensaje')}", "danger", "danger")
            
            # Guardar cache en background
            def guardar_cache_async():
                try:
                    CalculoCache.guardar_calculo_familia(nombre_familia, familia_data, resultados_familia)
                except Exception as e:
                    print(f"⚠️ Error guardando cache: {e}")
            
            threading.Thread(target=guardar_cache_async, daemon=True).start()
            
            # Generar vista
            from utils.calcular_familia_logica_encadenada import generar_vista_resultados_familia
            vista_resultados = generar_vista_resultados_familia(resultados_familia)
            
            return (vista_resultados, True, "Éxito", "Cálculo de familia completado", "success", "success")
            
        except Exception as e:
            import traceback
            print(f"❌ ERROR: {traceback.format_exc()}")
            return (no_update, True, "Error", f"Error: {str(e)}", "danger", "danger")
    
    @app.callback(
        Output("btn-descargar-html-familia", "style"),
        Input("resultados-familia", "children"),
        prevent_initial_call=False
    )
    def mostrar_boton_descargar(resultados):
        """Mostrar botón descargar cuando hay resultados"""
        if resultados and len(resultados) > 0:
            return {"display": "block", "margin-top": "20px"}
        return {"display": "none"}
    
    @app.callback(
        [Output("resultados-familia", "children", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-cargar-cache-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("tabla-familia", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def cargar_cache_familia(n_clicks, nombre_familia, tabla_data, columnas):
        """Carga resultados desde cache si existe y es válido"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"📂 CARGANDO CACHE FAMILIA: {nombre_familia}")
        
        try:
            if not nombre_familia:
                return (no_update, True, "Error", "Debe especificar nombre de familia", "danger", "danger")
            
            # Cargar cache
            calculo_guardado = CalculoCache.cargar_calculo_familia(nombre_familia)
            
            if not calculo_guardado:
                return (no_update, True, "Advertencia", "Cache no disponible", "warning", "warning")
            
            # Verificar vigencia
            familia_data = FamiliaManager.tabla_a_familia(tabla_data, columnas, nombre_familia)
            vigente, mensaje = CalculoCache.verificar_vigencia_familia(calculo_guardado, familia_data)
            
            if not vigente:
                return (no_update, True, "Advertencia", mensaje, "warning", "warning")
            
            # Generar vista desde cache
            from utils.calcular_familia_logica_encadenada import generar_vista_resultados_familia
            vista_resultados = generar_vista_resultados_familia(calculo_guardado["resultados"])
            
            return (vista_resultados, True, "Éxito", "Cache cargado correctamente", "success", "success")
            
        except Exception as e:
            import traceback
            print(f"❌ ERROR: {traceback.format_exc()}")
            return (no_update, True, "Error", f"Error: {str(e)}", "danger", "danger")

    
    @app.callback(
        Output("download-html-familia", "data"),
        Input("btn-descargar-html-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("resultados-familia", "children")],
        prevent_initial_call=True
    )
    def descargar_html_familia(n_clicks, nombre_familia, resultados):
        """Descargar HTML completo de familia"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Cargar cache de familia
            calculo_guardado = CalculoCache.cargar_calculo_familia(nombre_familia)
            
            if not calculo_guardado:
                return no_update
            
            # Generar HTML
            from utils.descargar_html import generar_html_familia
            html_content = generar_html_familia(nombre_familia, calculo_guardado["resultados"])
            
            # Retornar para descarga
            return dict(content=html_content, filename=f"{nombre_familia}_familia.html")
            
        except Exception as e:
            print(f"Error generando HTML: {e}")
            return no_update

    
    @app.callback(
        [Output("modal-familia-parametro", "is_open"),
         Output("modal-familia-body-parametro", "children"),
         Output("modal-familia-celda-info", "data")],
        [Input("tabla-familia", "active_cell"),
         Input("modal-familia-confirmar", "n_clicks"),
         Input("modal-familia-cancelar", "n_clicks")],
        [State("modal-familia-parametro", "is_open"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def manejar_modal_familia(active_cell, n_confirm, n_cancel, is_open, tabla_data):
        """Maneja edición de celdas mediante modal"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id in ["modal-familia-confirmar", "modal-familia-cancelar"]:
            return False, no_update, no_update
        
        if trigger_id == "tabla-familia" and active_cell:
            col_id = active_cell["column_id"]
            if not col_id.startswith("Estr."):
                raise dash.exceptions.PreventUpdate
            
            fila = active_cell["row"]
            tipo = tabla_data[fila].get("tipo", "str")
            valor_actual = tabla_data[fila].get(col_id, "")
            parametro = tabla_data[fila].get("parametro", "")
            
            # Tipos numéricos se editan directamente en celda, NO abrir modal
            if tipo in ["int", "float"]:
                raise dash.exceptions.PreventUpdate
            
            from utils.parametros_manager import ParametrosManager
            
            # Buscar opciones para el parámetro
            opciones = None
            if parametro in ["cable_conductor_id", "cable_guardia_id", "cable_guardia2_id"]:
                try:
                    with open("data/cables.json", "r", encoding="utf-8") as f:
                        cables_data = json.load(f)
                        opciones = list(cables_data.keys())
                except:
                    opciones = None
            else:
                opciones = ParametrosManager.obtener_opciones_parametro(parametro)
            
            # Si tiene opciones, mostrar botones
            if opciones:
                contenido = html.Div([
                    html.P(f"Seleccione valor para {parametro}:"),
                    dcc.Dropdown(
                        id="dropdown-familia-opciones",
                        options=[{"label": op, "value": op} for op in opciones],
                        value=valor_actual,
                        clearable=False
                    )
                ])
            elif tipo == "bool":
                contenido = html.Div([
                    html.P(f"Seleccione valor para {parametro}:"),
                    dcc.Dropdown(
                        id="dropdown-familia-opciones",
                        options=[{"label": "Verdadero", "value": True}, {"label": "Falso", "value": False}],
                        value=valor_actual,
                        clearable=False
                    )
                ])
            else:
                # Input de texto para campos sin opciones
                contenido = html.Div([
                    html.P(f"Ingrese valor para {parametro}:"),
                    dbc.Input(
                        id="input-valor",
                        type="text",
                        value=valor_actual
                    )
                ])
            
            celda_info = {"fila": fila, "columna": col_id, "parametro": parametro, "tipo": tipo}
            return True, contenido, celda_info
        
        raise dash.exceptions.PreventUpdate
    
    @app.callback(
        [Output("tabla-familia", "data", allow_duplicate=True),
         Output("modal-familia-parametro", "is_open", allow_duplicate=True)],
        Input("modal-familia-confirmar", "n_clicks"),
        [State("modal-familia-celda-info", "data"),
         State("tabla-familia", "data"),
         State("modal-familia-body-parametro", "children")],
        prevent_initial_call=True
    )
    def seleccionar_opcion_familia(n_confirmar, celda_info, tabla_data, modal_body):
        """Actualiza tabla al confirmar modal"""
        if n_confirmar is None or not celda_info:
            return no_update, no_update
        
        print(f"🔵 DEBUG: Confirmar presionado - celda_info: {celda_info}")
        
        # Extraer valor del componente que existe en el modal
        valor_seleccionado = None
        try:
            # Buscar dropdown o input en el modal_body
            if modal_body and 'props' in modal_body:
                children = modal_body['props'].get('children', [])
                for child in children:
                    if isinstance(child, dict) and 'props' in child:
                        # Buscar dropdown
                        if child.get('type') == 'Dropdown':
                            valor_seleccionado = child['props'].get('value')
                            print(f"✅ DEBUG: Valor de dropdown: {valor_seleccionado}")
                            break
                        # Buscar input
                        elif child.get('type') == 'Input':
                            valor_seleccionado = child['props'].get('value')
                            print(f"✅ DEBUG: Valor de input: {valor_seleccionado}")
                            break
        except Exception as e:
            print(f"⚠️ DEBUG: Error extrayendo valor: {e}")
        
        if valor_seleccionado is None:
            print("❌ DEBUG: No se pudo extraer valor del modal")
            return no_update, False
        
        fila = celda_info["fila"]
        columna = celda_info["columna"]
        tabla_data[fila][columna] = valor_seleccionado
        
        print(f"✅ DEBUG: Tabla actualizada - fila {fila}, col {columna}, valor: {valor_seleccionado}")
        return tabla_data, False
