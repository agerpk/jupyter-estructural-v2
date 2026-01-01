"""
Controlador para gestión de Familias de Estructuras
"""

from dash import callback, Input, Output, State, ctx, no_update
import dash_bootstrap_components as dbc
from dash import html
import json
from pathlib import Path
from datetime import datetime
from utils.familia_manager import FamiliaManager
from components.vista_familia_estructuras import crear_vista_familia_estructuras

# Callbacks para vista familia

@callback(
    [Output("contenido-principal", "children", allow_duplicate=True),
     Output("toast-notificacion", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "header", allow_duplicate=True),
     Output("toast-notificacion", "children", allow_duplicate=True),
     Output("toast-notificacion", "icon", allow_duplicate=True),
     Output("toast-notificacion", "color", allow_duplicate=True)],
    [Input("menu-familia-estructuras", "n_clicks")],
    prevent_initial_call=True
)
def mostrar_vista_familia(n_clicks):
    """Mostrar vista de familia de estructuras"""
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update, no_update
    
    try:
        # Cargar familia actual si existe
        familia_actual = FamiliaManager.cargar_familia_actual()
        vista = crear_vista_familia_estructuras(familia_actual)
        
        return vista, True, "Familia de Estructuras", \
               "Vista cargada correctamente", "success", "success"
    except Exception as e:
        return no_update, True, "Error", f"Error al cargar vista: {str(e)}", "danger", "danger"

@callback(
    [Output("tabla-familia", "data", allow_duplicate=True),
     Output("tabla-familia", "columns", allow_duplicate=True),
     Output("toast-notificacion", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "header", allow_duplicate=True),
     Output("toast-notificacion", "children", allow_duplicate=True),
     Output("toast-notificacion", "icon", allow_duplicate=True),
     Output("toast-notificacion", "color", allow_duplicate=True)],
    [Input("btn-agregar-estructura", "n_clicks")],
    [State("tabla-familia", "data"),
     State("tabla-familia", "columns")],
    prevent_initial_call=True
)
def agregar_estructura(n_clicks, tabla_data, columnas_actuales):
    """Agregar nueva columna de estructura"""
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    try:
        # Determinar nombre de nueva estructura
        estructuras_existentes = [col["id"] for col in columnas_actuales if col["id"].startswith("Estr.")]
        numero_siguiente = len(estructuras_existentes) + 1
        nuevo_nombre = f"Estr.{numero_siguiente}"
        
        # Agregar nueva columna
        nueva_columna = {
            "name": nuevo_nombre,
            "id": nuevo_nombre,
            "editable": True,
            "type": "any"
        }
        columnas_actualizadas = columnas_actuales + [nueva_columna]
        
        # Copiar valores de última columna existente
        if estructuras_existentes:
            ultima_estructura = estructuras_existentes[-1]
            for fila in tabla_data:
                fila[nuevo_nombre] = fila.get(ultima_estructura, "")
        else:
            # Primera estructura, usar valores por defecto
            for fila in tabla_data:
                fila[nuevo_nombre] = ""
        
        return tabla_data, columnas_actualizadas, True, "Estructura Agregada", \
               f"Se agregó la columna {nuevo_nombre}", "success", "success"
    
    except Exception as e:
        return no_update, no_update, True, "Error", f"Error al agregar estructura: {str(e)}", "danger", "danger"

@callback(
    [Output("tabla-familia", "data", allow_duplicate=True),
     Output("tabla-familia", "columns", allow_duplicate=True),
     Output("toast-notificacion", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "header", allow_duplicate=True),
     Output("toast-notificacion", "children", allow_duplicate=True),
     Output("toast-notificacion", "icon", allow_duplicate=True),
     Output("toast-notificacion", "color", allow_duplicate=True)],
    [Input("btn-eliminar-estructura", "n_clicks")],
    [State("tabla-familia", "data"),
     State("tabla-familia", "columns")],
    prevent_initial_call=True
)
def eliminar_estructura(n_clicks, tabla_data, columnas_actuales):
    """Eliminar última columna de estructura"""
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    try:
        # Encontrar columnas de estructura
        estructuras_existentes = [col for col in columnas_actuales if col["id"].startswith("Estr.")]
        
        if len(estructuras_existentes) <= 1:
            return no_update, no_update, True, "Advertencia", \
                   "Debe mantener al menos una estructura", "warning", "warning"
        
        # Eliminar última estructura
        ultima_estructura = estructuras_existentes[-1]
        columnas_actualizadas = [col for col in columnas_actuales if col["id"] != ultima_estructura["id"]]
        
        # Eliminar columna de datos
        for fila in tabla_data:
            if ultima_estructura["id"] in fila:
                del fila[ultima_estructura["id"]]
        
        return tabla_data, columnas_actualizadas, True, "Estructura Eliminada", \
               f"Se eliminó la columna {ultima_estructura['name']}", "success", "success"
    
    except Exception as e:
        return no_update, no_update, True, "Error", f"Error al eliminar estructura: {str(e)}", "danger", "danger"

@callback(
    [Output("toast-notificacion", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "header", allow_duplicate=True),
     Output("toast-notificacion", "children", allow_duplicate=True),
     Output("toast-notificacion", "icon", allow_duplicate=True),
     Output("toast-notificacion", "color", allow_duplicate=True)],
    [Input("btn-guardar-familia", "n_clicks")],
    [State("input-nombre-familia", "value"),
     State("tabla-familia", "data")],
    prevent_initial_call=True
)
def guardar_familia(n_clicks, nombre_familia, tabla_data):
    """Guardar familia de estructuras"""
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update
    
    try:
        if not nombre_familia or nombre_familia.strip() == "":
            return True, "Error", "Debe ingresar un nombre para la familia", "danger", "danger"
        
        # Convertir tabla a formato familia
        familia_data = FamiliaManager.tabla_a_familia(tabla_data, nombre_familia.strip())
        
        # Guardar archivo
        FamiliaManager.guardar_familia(familia_data)
        
        return True, "Familia Guardada", f"Familia '{nombre_familia}' guardada correctamente", "success", "success"
    
    except Exception as e:
        return True, "Error", f"Error al guardar familia: {str(e)}", "danger", "danger"

@callback(
    [Output("modal-cargar-familia", "is_open"),
     Output("select-familia-cargar", "options")],
    [Input("btn-cargar-familia", "n_clicks"),
     Input("btn-cancelar-cargar-familia", "n_clicks"),
     Input("btn-confirmar-cargar-familia", "n_clicks")],
    [State("modal-cargar-familia", "is_open")],
    prevent_initial_call=True
)
def toggle_modal_cargar_familia(n_abrir, n_cancelar, n_confirmar, is_open):
    """Toggle modal cargar familia"""
    
    if ctx.triggered_id == "btn-cargar-familia":
        # Obtener familias disponibles
        familias_disponibles = FamiliaManager.listar_familias_disponibles()
        opciones = [{"label": f, "value": f} for f in familias_disponibles]
        return True, opciones
    
    elif ctx.triggered_id in ["btn-cancelar-cargar-familia", "btn-confirmar-cargar-familia"]:
        return False, no_update
    
    return no_update, no_update

@callback(
    [Output("input-nombre-familia", "value", allow_duplicate=True),
     Output("tabla-familia", "data", allow_duplicate=True),
     Output("tabla-familia", "columns", allow_duplicate=True),
     Output("modal-cargar-familia", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "header", allow_duplicate=True),
     Output("toast-notificacion", "children", allow_duplicate=True),
     Output("toast-notificacion", "icon", allow_duplicate=True),
     Output("toast-notificacion", "color", allow_duplicate=True)],
    [Input("btn-confirmar-cargar-familia", "n_clicks")],
    [State("select-familia-cargar", "value")],
    prevent_initial_call=True
)
def cargar_familia_seleccionada(n_clicks, familia_seleccionada):
    """Cargar familia seleccionada"""
    if not n_clicks or not familia_seleccionada:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    try:
        # Cargar familia
        familia_data = FamiliaManager.cargar_familia(familia_seleccionada)
        
        # Convertir a formato tabla
        from components.vista_familia_estructuras import generar_datos_tabla_familia
        tabla_data = generar_datos_tabla_familia(familia_data)
        
        # Generar columnas
        columnas = [
            {"name": "Parámetro", "id": "parametro", "editable": False, "type": "text"},
            {"name": "Símbolo", "id": "simbolo", "editable": False, "type": "text"},
            {"name": "Unidad", "id": "unidad", "editable": False, "type": "text"},
            {"name": "Descripción", "id": "descripcion", "editable": False, "type": "text"}
        ]
        
        estructuras = familia_data.get("estructuras", {})
        for nombre_estr in sorted(estructuras.keys()):
            columnas.append({
                "name": nombre_estr,
                "id": nombre_estr,
                "editable": True,
                "type": "any"
            })
        
        return familia_data["nombre_familia"], tabla_data, columnas, False, \
               True, "Familia Cargada", f"Familia '{familia_seleccionada}' cargada correctamente", "success", "success"
    
    except Exception as e:
        return no_update, no_update, no_update, False, \
               True, "Error", f"Error al cargar familia: {str(e)}", "danger", "danger"