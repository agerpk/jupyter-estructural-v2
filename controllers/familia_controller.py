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
        Output("tabla-familia", "data", allow_duplicate=True),
        [Input("btn-buscar-familia", "n_clicks"),
         Input("btn-borrar-filtros-familia", "n_clicks")],
        [State("filtro-categoria-familia", "value"),
         State("buscar-parametro-familia", "value"),
         State("tabla-familia-original", "data")],
        prevent_initial_call=True
    )
    def filtrar_tabla_familia(n_buscar, n_borrar, categoria, busqueda, tabla_original):
        """Filtrar tabla por categoría y búsqueda con botones"""
        if not tabla_original:
            raise dash.exceptions.PreventUpdate
        
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Borrar filtros
        if trigger_id == "btn-borrar-filtros-familia":
            return tabla_original
        
        # Buscar
        sin_categoria = not categoria or categoria == "todas" or categoria == ""
        sin_busqueda = not busqueda or (isinstance(busqueda, str) and busqueda.strip() == "")
        
        if sin_categoria and sin_busqueda:
            return tabla_original
        
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
        
        return tabla_filtrada
    
    @app.callback(
        [Output("filtro-categoria-familia", "value"),
         Output("buscar-parametro-familia", "value")],
        Input("btn-borrar-filtros-familia", "n_clicks"),
        prevent_initial_call=True
    )
    def limpiar_inputs_filtros(n_clicks):
        """Limpiar inputs de filtros"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        return "todas", ""
    
    @app.callback(
        Output("tabla-familia-original", "data", allow_duplicate=True),
        Input("tabla-familia", "data_timestamp"),
        [State("tabla-familia", "data"),
         State("tabla-familia-original", "data")],
        prevent_initial_call=True
    )
    def sincronizar_ediciones_directas(timestamp, tabla_filtrada, tabla_original):
        """Sincroniza TODAS las ediciones de tabla hacia tabla original"""
        if not tabla_filtrada or not tabla_original:
            raise dash.exceptions.PreventUpdate
        
        print(f"\n🔄 SINCRONIZANDO: {len(tabla_filtrada)} filas filtradas → {len(tabla_original)} filas originales")
        
        # Actualizar valores en tabla original basándose en parametro
        for fila_filtrada in tabla_filtrada:
            parametro = fila_filtrada.get("parametro")
            if not parametro:
                continue
            
            # Buscar fila correspondiente en tabla original
            for fila_original in tabla_original:
                if fila_original.get("parametro") == parametro:
                    # Copiar TODOS los valores de columnas Estr.N
                    for key in fila_filtrada.keys():
                        if key.startswith("Estr."):
                            if fila_original.get(key) != fila_filtrada.get(key):
                                print(f"  ✏️ Actualizando {parametro}.{key}: {fila_original.get(key)} → {fila_filtrada.get(key)}")
                            fila_original[key] = fila_filtrada[key]
                    break
        
        return tabla_original
    
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
         Output("modal-estados-familia-tabla-container", "children")],
        [Input("btn-abrir-estados-familia", "n_clicks"),
         Input("modal-estados-familia-btn-cancelar", "n_clicks"),
         Input("modal-estados-familia-btn-guardar", "n_clicks")],
        [State("modal-estados-familia", "is_open"),
         State("input-nombre-familia", "value")],
        prevent_initial_call=True
    )
    def toggle_modal_estados_familia(n_abrir, n_cancelar, n_guardar, is_open, nombre_familia):
        """Abrir/cerrar modal de estados climáticos de familia"""
        from components.modal_estados_climaticos import generar_tabla_estados
        
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-abrir-estados-familia":
            if n_abrir is None:
                raise dash.exceptions.PreventUpdate
            
            # Cargar familia actual
            familia_actual = {}
            if nombre_familia:
                try:
                    familia_actual = FamiliaManager.cargar_familia(nombre_familia)
                except:
                    pass
            
            estados = familia_actual.get("estados_climaticos", {
                "1": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, "espesor_hielo": 0, "restriccion_conductor": 0.25, "restriccion_guardia": 0.7, "relflecha": 0.9},
                "2": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0, "espesor_hielo": 0, "restriccion_conductor": 0.40, "restriccion_guardia": 0.70, "relflecha": 0.9},
                "3": {"temperatura": 10, "descripcion": "Vmáx", "viento_velocidad": 38.9, "espesor_hielo": 0, "restriccion_conductor": 0.40, "restriccion_guardia": 0.70, "relflecha": 0.9},
                "4": {"temperatura": -5, "descripcion": "Vmed", "viento_velocidad": 15.56, "espesor_hielo": 0.01, "restriccion_conductor": 0.40, "restriccion_guardia": 0.7, "relflecha": 0.9},
                "5": {"temperatura": 8, "descripcion": "TMA", "viento_velocidad": 0, "espesor_hielo": 0, "restriccion_conductor": 0.25, "restriccion_guardia": 0.7, "relflecha": 0.9},
                "6": {"temperatura": -5, "descripcion": "HIELO", "viento_velocidad": 0, "espesor_hielo": 0.025, "restriccion_conductor": 0.40, "restriccion_guardia": 0.7, "relflecha": 0.9},
                "7": {"temperatura": 85, "descripcion": "TMAXCOND", "viento_velocidad": 0, "espesor_hielo": 0, "restriccion_conductor": 0.25, "restriccion_guardia": 0.7, "relflecha": 0.9}
            })
            
            tabla = generar_tabla_estados(estados, "modal-estados-familia")
            return True, tabla
        
        elif trigger_id in ["modal-estados-familia-btn-cancelar", "modal-estados-familia-btn-guardar"]:
            return False, no_update
        
        raise dash.exceptions.PreventUpdate
    
    @app.callback(
        [Output("modal-estados-familia-tabla-container", "children", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("modal-estados-familia-btn-agregar", "n_clicks"),
        [State({"type": "input-temp", "modal": "modal-estados-familia", "id": ALL}, "id"),
         State({"type": "input-temp", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-desc", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-viento", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-hielo", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-rest-cond", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-rest-guard", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-relflecha", "modal": "modal-estados-familia", "id": ALL}, "value")],
        prevent_initial_call=True
    )
    def agregar_estado_familia(n_clicks, ids, temps, descs, vientos, hielos, rest_cond, rest_guard, relflechas):
        """Agregar nuevo estado"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        from components.modal_estados_climaticos import generar_tabla_estados
        
        # Reconstruir estados actuales
        estados = {}
        for i, id_dict in enumerate(ids):
            estado_id = id_dict["id"]
            estados[estado_id] = {
                "temperatura": temps[i],
                "descripcion": descs[i],
                "viento_velocidad": vientos[i],
                "espesor_hielo": hielos[i],
                "restriccion_conductor": rest_cond[i],
                "restriccion_guardia": rest_guard[i],
                "relflecha": relflechas[i]
            }
        
        # Encontrar próximo ID disponible
        ids_numericos = []
        for k in estados.keys():
            try:
                ids_numericos.append(int(k))
            except:
                pass
        
        if ids_numericos:
            nuevo_id = str(max(ids_numericos) + 1)
        else:
            nuevo_id = "1"
        
        # Agregar nuevo estado (copiar último)
        if estados:
            ultimo_estado = list(estados.values())[-1]
            estados[nuevo_id] = ultimo_estado.copy()
            estados[nuevo_id]["descripcion"] = f"Estado {nuevo_id}"
        else:
            estados[nuevo_id] = {
                "temperatura": 0,
                "descripcion": f"Estado {nuevo_id}",
                "viento_velocidad": 0,
                "espesor_hielo": 0,
                "restriccion_conductor": 0.25,
                "restriccion_guardia": 0.7,
                "relflecha": 0.9
            }
        
        tabla = generar_tabla_estados(estados, "modal-estados-familia")
        return tabla, True, "Éxito", f"Estado {nuevo_id} agregado", "success", "success"
    
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("modal-estados-familia-btn-guardar", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("tabla-familia-original", "data"),
         State("tabla-familia", "columns"),
         State({"type": "input-temp", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-desc", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-viento", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-hielo", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-rest-cond", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-rest-guard", "modal": "modal-estados-familia", "id": ALL}, "value"),
         State({"type": "input-relflecha", "modal": "modal-estados-familia", "id": ALL}, "value")],
        prevent_initial_call=True
    )
    def guardar_estados_familia(n_clicks, nombre_familia, tabla_original, columnas, temps, descs, vientos, hielos, rest_cond, rest_guard, relflechas):
        """Guardar estados climáticos en archivo .familia.json"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        if not nombre_familia:
            return True, "Error", "Debe especificar un nombre de familia", "danger", "danger"
        
        if not tabla_original or not columnas:
            return True, "Error", "No hay datos de familia para actualizar", "danger", "danger"
        
        # Intentar cargar la familia existente desde disco (más seguro que reconstruir desde tabla)
        try:
            familia_data = FamiliaManager.cargar_familia(nombre_familia)
            print(f"   💾 DEBUG guardar_estados_familia: familia cargada desde disco: {nombre_familia}")
        except Exception as e:
            # Si no se puede cargar, intentar reconstruir desde la tabla (fallback)
            try:
                familia_data = FamiliaManager.tabla_a_familia(tabla_original, columnas, nombre_familia)
                print(f"   ⚠️ WARN guardar_estados_familia: no se encontró famiglia en disco, reconstruyendo desde tabla: {e}")
            except Exception as ee:
                return True, "Error", f"Error cargando familia: {str(ee)}", "danger", "danger"

        # Construir estados climáticos unificados (con restricciones incluidas)
        estados_climaticos = {}

        for i in range(len(temps)):
            estado_id = str(i + 1)
            estados_climaticos[estado_id] = {
                "temperatura": temps[i],
                "descripcion": descs[i],
                "viento_velocidad": vientos[i],
                "espesor_hielo": hielos[i],
                "restriccion_conductor": rest_cond[i],
                "restriccion_guardia": rest_guard[i],
                "relflecha": relflechas[i]
            }

        # Actualizar estados en familia sin tocar otros campos
        familia_data["estados_climaticos"] = estados_climaticos

        # Propagar estados a cada estructura individual conservando sus demás parámetros
        for estructura_id, estructura in familia_data.get("estructuras", {}).items():
            if not isinstance(estructura, dict):
                continue
            estructura["estados_climaticos"] = estados_climaticos

        # Guardar familia actualizada
        exito = FamiliaManager.guardar_familia(familia_data)

        if not exito:
            return True, "Error", "Error guardando familia", "danger", "danger"

        return True, "Éxito", "Estados climáticos guardados en familia y estructuras", "success", "success"

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
         State("tabla-familia-original", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def guardar_familia(n_clicks, nombre_familia, tabla_original, columnas):
        """Guarda familia con datos actuales de tabla ORIGINAL (completa)"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        if not nombre_familia:
            return True, "Error", "Debe especificar un nombre de familia", "danger", "danger", no_update
        
        if not tabla_original:
            return True, "Error", "No hay datos para guardar", "danger", "danger", no_update
        
        try:
            # Convertir tabla ORIGINAL a formato familia (tiene TODOS los datos)
            familia_data = FamiliaManager.tabla_a_familia(tabla_original, columnas, nombre_familia)
            
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
         State("tabla-familia-original", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def guardar_como_familia(n_clicks, nombre_familia, tabla_original, columnas):
        """Guarda como nueva familia con datos actuales de tabla ORIGINAL (completa)"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        if not nombre_familia:
            return True, "Error", "Debe especificar un nombre de familia", "danger", "danger", no_update
        
        if not tabla_original:
            return True, "Error", "No hay datos para guardar", "danger", "danger", no_update
        
        try:
            # Convertir tabla ORIGINAL a formato familia con nombre exacto (tiene TODOS los datos)
            familia_data = FamiliaManager.tabla_a_familia(tabla_original, columnas, nombre_familia)
            
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
         State("tabla-familia-original", "data"),
         State("tabla-familia", "columns"),
         State("checklist-calculos-familia", "value")],
        prevent_initial_call=True
    )
    def calcular_familia_completa(n_clicks, nombre_familia, tabla_original, columnas, calculos_activos):
        """Ejecuta cálculo completo de familia y guarda cache"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"🚀 INICIANDO CÁLCULO FAMILIA: {nombre_familia}")
        print(f"🔍 Cálculos activos: {calculos_activos}")
        
        try:
            if not nombre_familia or not tabla_original or not columnas:
                return (no_update, True, "Error", "Faltan datos para calcular", "danger", "danger")
            
            # Convertir tabla ORIGINAL a formato familia
            familia_data = FamiliaManager.tabla_a_familia(tabla_original, columnas, nombre_familia)
            
            # Ejecutar cálculo con calculos_activos
            from utils.calcular_familia_logica_encadenada import ejecutar_calculo_familia_completa
            resultados_familia = ejecutar_calculo_familia_completa(familia_data, calculos_activos=calculos_activos)
            
            if not resultados_familia.get("exito"):
                return (no_update, True, "Error", f"Error en cálculo: {resultados_familia.get('mensaje')}", "danger", "danger")
            
            # Guardar familia en disco (sincronizado) para que el archivo en disco
            # coincida con la familia usada en el cálculo y evitar mismatches de hash
            try:
                saved = FamiliaManager.guardar_familia(familia_data)
                if saved:
                    print(f"💾 Familia '{nombre_familia}' guardada en disco (coincide con cálculo)")
                else:
                    print(f"⚠️ No se pudo guardar la familia '{nombre_familia}' en disco")
            except Exception as e:
                print(f"⚠️ Error guardando familia en disco: {e}")

            # Guardar cache en background
            def guardar_cache_async():
                try:
                    CalculoCache.guardar_calculo_familia(nombre_familia, familia_data, resultados_familia)
                except Exception as e:
                    print(f"⚠️ Error guardando cache: {e}")

            threading.Thread(target=guardar_cache_async, daemon=True).start()
            
            # Generar vista
            from utils.calcular_familia_logica_encadenada import generar_vista_resultados_familia
            vista_resultados = generar_vista_resultados_familia(resultados_familia, calculos_activos=calculos_activos)
            
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
        Output("calculos-activos-familia-store", "data"),
        Input("checklist-calculos-familia", "value"),
        prevent_initial_call=True
    )
    def guardar_calculos_activos_familia(calculos_activos):
        """Guardar checkboxes de cálculos activos en persistencia"""
        if calculos_activos is None:
            raise dash.exceptions.PreventUpdate
        
        state = AppState()
        state.set_calculos_activos_familia(calculos_activos)
        return calculos_activos
    
    @app.callback(
        [Output("resultados-familia", "children", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-cargar-cache-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("tabla-familia-original", "data"),
         State("tabla-familia", "columns"),
         State("checklist-calculos-familia", "value")],
        prevent_initial_call=True
    )
    def cargar_cache_familia(n_clicks, nombre_familia, tabla_original, columnas, calculos_activos):
        """Carga resultados desde cache si existe y es válido"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        print(f"📂 CARGANDO CACHE FAMILIA: {nombre_familia}")
        print(f"🔍 Cálculos activos: {calculos_activos}")
        
        try:
            if not nombre_familia:
                return (no_update, True, "Error", "Debe especificar nombre de familia", "danger", "danger")
            
            # Cargar cache
            calculo_guardado = CalculoCache.cargar_calculo_familia(nombre_familia)
            
            if not calculo_guardado:
                return (no_update, True, "Advertencia", "Cache no disponible", "warning", "warning")

            # Diagnostics: informar archivo origen y claves de resultados
            print(f"ℹ️ Cache encontrado: archivo_origen={calculo_guardado.get('archivo_origen')} hash={calculo_guardado.get('hash_parametros')} resultados_keys={list(calculo_guardado.get('resultados', {}).keys())}")

            # Verificar vigencia
            familia_data = FamiliaManager.tabla_a_familia(tabla_original, columnas, nombre_familia)
            vigente, mensaje = CalculoCache.verificar_vigencia_familia(calculo_guardado, familia_data)
            
            if not vigente:
                return (no_update, True, "Advertencia", mensaje, "warning", "warning")
            
            # Generar vista desde cache con calculos_activos
            from utils.calcular_familia_logica_encadenada import generar_vista_resultados_familia
            vista_resultados = generar_vista_resultados_familia(calculo_guardado["resultados"], calculos_activos=calculos_activos)
            
            return (vista_resultados, True, "Éxito", "Cache cargado correctamente", "success", "success")
            
        except Exception as e:
            import traceback
            print(f"❌ ERROR: {traceback.format_exc()}")
            return (no_update, True, "Error", f"Error: {str(e)}", "danger", "danger")

    
    @app.callback(
        Output("download-html-familia", "data"),
        Input("btn-descargar-html-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("checklist-calculos-familia", "value")],
        prevent_initial_call=True
    )
    def descargar_html_familia(n_clicks, nombre_familia, calculos_activos):
        """Descargar HTML completo de familia"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Cargar cache de familia
            calculo_guardado = CalculoCache.cargar_calculo_familia(nombre_familia)
            
            if not calculo_guardado:
                return no_update
            
            # Convertir calculos_activos a dict para checklist
            checklist_dict = {calc: True for calc in (calculos_activos or [])}
            
            # Generar HTML con checklist
            import logging
            logger = logging.getLogger(__name__)
            # Diagnostics: imprimir información básica para depuración
            print(f"ℹ️ descargar_html_familia: archivo_origen={calculo_guardado.get('archivo_origen')} resultados_keys={list(calculo_guardado.get('resultados', {}).keys())}")
            logger.debug(f"Descargando HTML familia='{nombre_familia}' checklist={checklist_dict} resultados_keys={list(calculo_guardado.get('resultados', {}).keys())}")
            from utils.descargar_html import generar_html_familia
            html_content = generar_html_familia(nombre_familia, calculo_guardado["resultados"], checklist_dict)
            
            # Retornar para descarga
            return dict(content=html_content, filename=f"{nombre_familia}_familia.html")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error generando HTML para familia '{nombre_familia}': {e}")

    
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
         Output("tabla-familia-original", "data", allow_duplicate=True),
         Output("modal-familia-parametro", "is_open", allow_duplicate=True)],
        Input("modal-familia-confirmar", "n_clicks"),
        [State("modal-familia-celda-info", "data"),
         State("tabla-familia", "data"),
         State("tabla-familia-original", "data"),
         State("modal-familia-body-parametro", "children")],
        prevent_initial_call=True
    )
    def seleccionar_opcion_familia(n_confirmar, celda_info, tabla_data, tabla_original, modal_body):
        """Actualiza tabla al confirmar modal"""
        if n_confirmar is None or not celda_info:
            return no_update, no_update, no_update
        
        # Extraer valor del componente que existe en el modal
        valor_seleccionado = None
        try:
            if modal_body and 'props' in modal_body:
                children = modal_body['props'].get('children', [])
                for child in children:
                    if isinstance(child, dict) and 'props' in child:
                        if child.get('type') == 'Dropdown':
                            valor_seleccionado = child['props'].get('value')
                            break
                        elif child.get('type') == 'Input':
                            valor_seleccionado = child['props'].get('value')
                            break
        except:
            pass
        
        if valor_seleccionado is None:
            return no_update, no_update, False
        
        fila = celda_info["fila"]
        columna = celda_info["columna"]
        parametro = celda_info["parametro"]
        
        # Actualizar tabla filtrada
        tabla_data[fila][columna] = valor_seleccionado
        
        # Actualizar tabla original (buscar por parametro)
        for fila_orig in tabla_original:
            if fila_orig.get("parametro") == parametro:
                fila_orig[columna] = valor_seleccionado
                break
        
        return tabla_data, tabla_original, False
