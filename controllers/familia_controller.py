"""
Controller para Familia de Estructuras - Implementación limpia y escalable
"""

from dash import Input, Output, State, callback, dash, no_update, html, dcc, ALL, ctx
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

@callback(
    [Output("select-familia-existente", "options"),
     Output("select-familia-existente", "value")],
    Input("select-familia-existente", "id"),
    prevent_initial_call=False
)
def cargar_opciones_familias(component_id):
    """Carga opciones de familias disponibles"""
    print(f"DEBUG: cargar_opciones_familias ejecutado con component_id: {component_id}")
    try:
        archivos_familia = FamiliaManager.obtener_archivos_familia()
        print(f"DEBUG: Archivos encontrados: {archivos_familia}")
        
        opciones = []
        for archivo in archivos_familia:
            # Para el label, remover .familia del stem
            # Para el value, usar el stem completo para que coincida con la lógica de carga
            label_limpio = archivo.replace(".familia", "")
            opciones.append({"label": label_limpio, "value": archivo})
        
        print(f"DEBUG: Opciones generadas: {opciones}")
        return opciones, None
    except Exception as e:
        print(f"ERROR: {e}")
        return [], None

@callback(
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
    print(f"DEBUG: Callback ejecutado con valor: {nombre_familia}")
    
    if not nombre_familia:
        print("DEBUG: Valor vacío, retornando no_update")
        return no_update, no_update, no_update, False, "", "", "info"
    
    # Limpiar nombre si viene con .familia
    if nombre_familia.endswith('.familia'):
        nombre_limpio = nombre_familia[:-8]
        print(f"DEBUG: Nombre limpiado de '{nombre_familia}' a '{nombre_limpio}'")
    else:
        nombre_limpio = nombre_familia
        print(f"DEBUG: Nombre ya limpio: '{nombre_limpio}'")
    
    print(f"DEBUG: Intentando cargar familia: {nombre_limpio}")
    datos_familia = FamiliaManager.cargar_familia(nombre_limpio)
    
    if not datos_familia:
        print(f"DEBUG: No se pudo cargar familia {nombre_limpio}")
        return no_update, no_update, no_update, True, "Error", f"No se pudo cargar la familia '{nombre_limpio}'", "danger"
    
    print(f"DEBUG: Familia cargada exitosamente: {datos_familia.get('nombre_familia')}")
    tabla_data, columnas = FamiliaManager.familia_a_tabla(datos_familia)
    print(f"DEBUG: Tabla generada con {len(tabla_data)} filas y {len(columnas)} columnas")
    
    return (tabla_data, columnas, datos_familia.get('nombre_familia', nombre_limpio), 
            True, "Éxito", f"Familia '{nombre_limpio}' cargada correctamente", "success")

@callback(
    [Output("tabla-familia", "columns", allow_duplicate=True),
     Output("tabla-familia", "data", allow_duplicate=True)],
    Input("btn-agregar-estructura", "n_clicks"),
    [State("tabla-familia", "columns"),
     State("tabla-familia", "data")],
    prevent_initial_call=True
)
def agregar_estructura(n_clicks, columnas, tabla_data):
    """Agrega nueva columna de estructura"""
    if not n_clicks or not columnas or not tabla_data:
        return no_update, no_update
    
    # Encontrar próximo número de estructura
    nums_existentes = []
    for col in columnas:
        if col['id'].startswith('Estr.'):
            try:
                num = int(col['id'].split('.')[1])
                nums_existentes.append(num)
            except:
                continue
    
    proximo_num = max(nums_existentes, default=0) + 1
    nueva_columna_id = f"Estr.{proximo_num}"
    
    # Agregar nueva columna
    nueva_columna = {
        "name": nueva_columna_id,
        "id": nueva_columna_id,
        "editable": True
    }
    columnas_actualizadas = columnas + [nueva_columna]
    
    # Copiar valores de última columna existente
    ultima_columna = None
    for col in reversed(columnas):
        if col['id'].startswith('Estr.'):
            ultima_columna = col['id']
            break
    
    # Actualizar datos de tabla
    tabla_actualizada = []
    for fila in tabla_data:
        nueva_fila = fila.copy()
        if ultima_columna and ultima_columna in fila:
            nueva_fila[nueva_columna_id] = fila[ultima_columna]
        else:
            nueva_fila[nueva_columna_id] = fila.get('valor', '')
        tabla_actualizada.append(nueva_fila)
    
    return columnas_actualizadas, tabla_actualizada

@callback(
    [Output("tabla-familia", "columns", allow_duplicate=True),
     Output("tabla-familia", "data", allow_duplicate=True)],
    Input("btn-eliminar-estructura", "n_clicks"),
    [State("tabla-familia", "columns"),
     State("tabla-familia", "data")],
    prevent_initial_call=True
)
def eliminar_estructura(n_clicks, columnas, tabla_data):
    """Elimina última columna de estructura"""
    if not n_clicks or not columnas or not tabla_data:
        return no_update, no_update
    
    # Encontrar columnas de estructura
    columnas_estructura = [col for col in columnas if col['id'].startswith('Estr.')]
    
    # No eliminar si solo hay una estructura
    if len(columnas_estructura) <= 1:
        return no_update, no_update
    
    # Encontrar última columna por número
    ultima_columna = None
    max_num = 0
    for col in columnas_estructura:
        try:
            num = int(col['id'].split('.')[1])
            if num > max_num:
                max_num = num
                ultima_columna = col['id']
        except:
            continue
    
    if not ultima_columna:
        return no_update, no_update
    
    # Eliminar columna
    columnas_actualizadas = [col for col in columnas if col['id'] != ultima_columna]
    
    # Eliminar datos de esa columna
    tabla_actualizada = []
    for fila in tabla_data:
        nueva_fila = {k: v for k, v in fila.items() if k != ultima_columna}
        tabla_actualizada.append(nueva_fila)
    
    return columnas_actualizadas, tabla_actualizada

@callback(
    [Output("toast-notificacion", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "header", allow_duplicate=True),
     Output("toast-notificacion", "children", allow_duplicate=True),
     Output("toast-notificacion", "color", allow_duplicate=True),
     Output("familia-activa-state", "data", allow_duplicate=True),
     Output("select-familia-existente", "options", allow_duplicate=True)],
    Input("btn-guardar-familia", "n_clicks"),
    [State("input-nombre-familia", "value"),
     State("tabla-familia", "data"),
     State("tabla-familia", "columns")],
    prevent_initial_call=True
)
def guardar_familia(n_clicks, nombre_familia, tabla_data, columnas):
    """Guarda familia en archivo"""
    print(f"DEBUG: guardar_familia - n_clicks: {n_clicks}, nombre: {nombre_familia}")
    
    if not n_clicks:
        return False, "", "", "info", no_update, no_update
    
    if not nombre_familia or not nombre_familia.strip():
        return True, "Error", "Debe ingresar un nombre para la familia", "danger", no_update, no_update
    
    if not tabla_data or not columnas:
        return True, "Error", "No hay datos para guardar", "danger", no_update, no_update
    
    try:
        datos_familia = FamiliaManager.tabla_a_familia(tabla_data, columnas, nombre_familia.strip())
        print(f"DEBUG: Datos familia generados: {datos_familia.get('nombre_familia')}")
        
        if FamiliaManager.guardar_familia(datos_familia):
            # Marcar como familia activa
            set_familia_activa(nombre_familia.strip())
            print(f"DEBUG: Familia guardada y marcada como activa: {nombre_familia}")
            
            # Actualizar opciones del dropdown
            archivos = FamiliaManager.obtener_archivos_familia()
            opciones = [{"label": archivo.replace('.familia', ''), "value": archivo} for archivo in archivos]
            
            return (True, "Éxito", f"Familia '{nombre_familia}' guardada correctamente", "success", 
                   datos_familia, opciones)
        else:
            return True, "Error", "No se pudo guardar la familia", "danger", no_update, no_update
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return True, "Error", f"Error al guardar: {str(e)}", "danger", no_update, no_update

@callback(
    [Output("toast-notificacion", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "header", allow_duplicate=True),
     Output("toast-notificacion", "children", allow_duplicate=True),
     Output("toast-notificacion", "color", allow_duplicate=True),
     Output("familia-activa-state", "data", allow_duplicate=True),
     Output("select-familia-existente", "options", allow_duplicate=True),
     Output("input-nombre-familia", "value", allow_duplicate=True)],
    Input("btn-guardar-como-familia", "n_clicks"),
    [State("input-nombre-familia", "value"),
     State("tabla-familia", "data"),
     State("tabla-familia", "columns")],
    prevent_initial_call=True
)
def guardar_como_familia(n_clicks, nombre_familia, tabla_data, columnas):
    """Guarda familia con nuevo nombre"""
    print(f"DEBUG: guardar_como_familia - n_clicks: {n_clicks}, nombre: {nombre_familia}")
    
    if not n_clicks:
        return False, "", "", "info", no_update, no_update, no_update
    
    if not nombre_familia or not nombre_familia.strip():
        return True, "Error", "Debe ingresar un nombre para la familia", "danger", no_update, no_update, no_update
    
    if not tabla_data or not columnas:
        return True, "Error", "No hay datos para guardar", "danger", no_update, no_update, no_update
    
    # Agregar sufijo "_copia" si ya existe
    nombre_base = nombre_familia.strip()
    nombre_nuevo = nombre_base
    contador = 1
    
    while True:
        try:
            FamiliaManager.cargar_familia(nombre_nuevo)
            # Si llega aquí, el archivo existe
            if contador == 1:
                nombre_nuevo = f"{nombre_base}_copia"
            else:
                nombre_nuevo = f"{nombre_base}_copia{contador}"
            contador += 1
        except FileNotFoundError:
            # El archivo no existe, podemos usar este nombre
            break
    
    try:
        datos_familia = FamiliaManager.tabla_a_familia(tabla_data, columnas, nombre_nuevo)
        print(f"DEBUG: Guardando como '{nombre_nuevo}'")
        
        if FamiliaManager.guardar_familia(datos_familia):
            # Marcar como familia activa
            set_familia_activa(nombre_nuevo)
            print(f"DEBUG: Familia guardada como '{nombre_nuevo}' y marcada como activa")
            
            # Actualizar opciones del dropdown
            archivos = FamiliaManager.obtener_archivos_familia()
            opciones = [{"label": archivo.replace('.familia', ''), "value": archivo} for archivo in archivos]
            
            return (True, "Éxito", f"Familia guardada como '{nombre_nuevo}'", "success", 
                   datos_familia, opciones, nombre_nuevo)
        else:
            return True, "Error", "No se pudo guardar la familia", "danger", no_update, no_update, no_update
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return True, "Error", f"Error al guardar: {str(e)}", "danger", no_update, no_update, no_update

@callback(
    [Output("modal-eliminar-familia", "is_open"),
     Output("modal-eliminar-familia-nombre", "children")],
    [Input("btn-eliminar-familia", "n_clicks"),
     Input("modal-eliminar-confirmar", "n_clicks"),
     Input("modal-eliminar-cancelar", "n_clicks")],
    [State("input-nombre-familia", "value"),
     State("modal-eliminar-familia", "is_open")],
    prevent_initial_call=True
)
def manejar_modal_eliminar_familia(n_eliminar, n_confirmar, n_cancelar, nombre_familia, is_open):
    """Maneja modal de confirmación para eliminar familia"""
    if not ctx.triggered:
        return no_update, no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "btn-eliminar-familia" and nombre_familia:
        return True, nombre_familia
    elif trigger_id in ["modal-eliminar-confirmar", "modal-eliminar-cancelar"]:
        return False, no_update
    
    return no_update, no_update

@callback(
    [Output("toast-notificacion", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "header", allow_duplicate=True),
     Output("toast-notificacion", "children", allow_duplicate=True),
     Output("toast-notificacion", "color", allow_duplicate=True),
     Output("select-familia-existente", "options", allow_duplicate=True),
     Output("input-nombre-familia", "value", allow_duplicate=True),
     Output("tabla-familia", "data", allow_duplicate=True),
     Output("tabla-familia", "columns", allow_duplicate=True)],
    Input("modal-eliminar-confirmar", "n_clicks"),
    [State("input-nombre-familia", "value")],
    prevent_initial_call=True
)
def eliminar_familia_confirmado(n_clicks, nombre_familia):
    """Elimina familia después de confirmación"""
    if not n_clicks or not nombre_familia:
        return False, "", "", "info", no_update, no_update, no_update, no_update
    
    try:
        # Eliminar archivo
        nombre_archivo = nombre_familia.replace(" ", "_").replace("/", "_")
        archivo_familia = DATA_DIR / f"{nombre_archivo}.familia.json"
        
        if archivo_familia.exists():
            archivo_familia.unlink()
            
            # Limpiar familia activa si era la eliminada
            if get_familia_activa() == nombre_familia:
                set_familia_activa("")
            
            # Actualizar opciones del dropdown
            archivos = FamiliaManager.obtener_archivos_familia()
            opciones = [{"label": archivo, "value": archivo} for archivo in archivos]
            
            # Crear familia nueva vacía
            familia_nueva = FamiliaManager.crear_familia_nueva()
            tabla_data, columnas = FamiliaManager.familia_a_tabla(familia_nueva)
            
            return (True, "Éxito", f"Familia '{nombre_familia}' eliminada correctamente", "success", 
                   opciones, "", tabla_data, columnas)
        else:
            return True, "Error", f"Familia '{nombre_familia}' no encontrada", "danger", no_update, no_update, no_update, no_update
    
    except Exception as e:
        return True, "Error", f"Error al eliminar: {str(e)}", "danger", no_update, no_update, no_update, no_update

# ============================================================================
# MODAL DE EDICIÓN DE PARÁMETROS
# ============================================================================

@callback(
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
def manejar_modal_parametro(active_cell, n_confirm, n_cancel, is_open, tabla_data):
    """Maneja modal de edición de parámetros"""
    if not ctx.triggered:
        return no_update, no_update, no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Abrir modal al hacer clic en celda
    if trigger_id == "tabla-familia" and active_cell:
        col_id = active_cell["column_id"]
        
        # Solo abrir para columnas de estructura
        if not col_id.startswith("Estr."):
            return no_update, no_update, no_update
        
        fila = active_cell["row"]
        parametro = tabla_data[fila]["parametro"]
        valor_actual = tabla_data[fila].get(col_id, "")
        tipo = tabla_data[fila]["tipo"]
        
        # Solo abrir modal para tipos no numéricos
        if tipo in ["int", "float"]:
            return no_update, no_update, no_update
        
        # Obtener opciones si es select
        opciones = ParametrosManager.obtener_opciones_parametro(parametro)
        
        if opciones:
            # Modal con botones para opciones
            botones = []
            for opcion in opciones:
                color = "primary" if opcion == valor_actual else "outline-secondary"
                botones.append(
                    dbc.Button(
                        opcion,
                        id={"type": "familia-opcion-btn", "value": opcion},
                        color=color,
                        className="me-2 mb-2",
                        size="sm"
                    )
                )
            contenido = html.Div([
                html.P(f"Seleccione valor para {parametro}:"),
                html.Div(botones)
            ])
        elif tipo == "bool":
            # Modal para booleanos
            contenido = html.Div([
                html.P(f"Seleccione valor para {parametro}:"),
                dbc.ButtonGroup([
                    dbc.Button(
                        "Verdadero",
                        id={"type": "familia-bool-btn", "value": True},
                        color="success" if valor_actual else "outline-success"
                    ),
                    dbc.Button(
                        "Falso",
                        id={"type": "familia-bool-btn", "value": False},
                        color="danger" if not valor_actual else "outline-danger"
                    )
                ])
            ])
        else:
            # Modal para texto
            contenido = html.Div([
                html.P(f"Ingrese valor para {parametro}:"),
                dbc.Input(
                    id="input-familia-valor",
                    type="text",
                    value=str(valor_actual)
                )
            ])
        
        celda_info = {"fila": fila, "columna": col_id, "parametro": parametro, "tipo": tipo}
        return True, contenido, celda_info
    
    # Cerrar modal
    elif trigger_id in ["modal-familia-confirmar", "modal-familia-cancelar"]:
        return False, no_update, no_update
    
    return no_update, no_update, no_update

@callback(
    [Output("tabla-familia", "data", allow_duplicate=True),
     Output("modal-familia-parametro", "is_open", allow_duplicate=True)],
    [Input({"type": "familia-opcion-btn", "value": ALL}, "n_clicks"),
     Input({"type": "familia-bool-btn", "value": ALL}, "n_clicks")],
    [State("modal-familia-celda-info", "data"),
     State("tabla-familia", "data")],
    prevent_initial_call=True
)
def seleccionar_opcion_directa(n_clicks_opciones, n_clicks_bool, celda_info, tabla_data):
    """Actualiza tabla al seleccionar opción en modal"""
    if not ctx.triggered or not celda_info:
        return no_update, no_update
    
    # Obtener valor seleccionado
    trigger = ctx.triggered[0]
    if trigger["value"] is None:
        return no_update, no_update
    
    component_id = trigger["prop_id"].split(".")[0]
    component_data = json.loads(component_id)
    valor_seleccionado = component_data["value"]
    
    # Actualizar tabla
    fila = celda_info["fila"]
    columna = celda_info["columna"]
    tabla_data[fila][columna] = valor_seleccionado
    
    return tabla_data, False

# Agregar callback para badge familia activa
@callback(
    Output("badge-familia-activa", "children"),
    Input("familia-activa-state", "data"),
    prevent_initial_call=True
)
def actualizar_badge_familia_activa(familia_data):
    """Actualiza badge con familia activa"""
    nombre_familia = get_familia_activa()
    if nombre_familia:
        return f"📁 {nombre_familia.replace('_', ' ')}"
    return "Ninguna"

# Agregar callback para confirmar modal de texto
@callback(
    [Output("tabla-familia", "data", allow_duplicate=True),
     Output("modal-familia-parametro", "is_open", allow_duplicate=True)],
    Input("modal-familia-confirmar", "n_clicks"),
    [State("input-familia-valor", "value"),
     State("modal-familia-celda-info", "data"),
     State("tabla-familia", "data")],
    prevent_initial_call=True
)
def confirmar_modal_texto(n_clicks, valor_texto, celda_info, tabla_data):
    """Confirma edición de texto en modal"""
    if not n_clicks or not celda_info or valor_texto is None:
        return no_update, no_update
    
    # Actualizar tabla
    fila = celda_info["fila"]
    columna = celda_info["columna"]
    tabla_data[fila][columna] = valor_texto
    
    return tabla_data, False

# ============================================================================
# MODAL CARGAR COLUMNA
# ============================================================================

@callback(
    [Output("modal-cargar-columna", "is_open"),
     Output("select-estructura-cargar-columna", "options"),
     Output("select-columna-destino", "options")],
    [Input("btn-cargar-columna", "n_clicks"),
     Input("modal-cargar-columna-confirmar", "n_clicks"),
     Input("modal-cargar-columna-cancelar", "n_clicks")],
    [State("tabla-familia", "columns"),
     State("modal-cargar-columna", "is_open")],
    prevent_initial_call=True
)
def manejar_modal_cargar_columna(n_abrir, n_confirmar, n_cancelar, columnas, is_open):
    """Maneja modal de cargar columna"""
    if not ctx.triggered:
        return no_update, no_update, no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "btn-cargar-columna":
        # Cargar estructuras disponibles
        estructuras = FamiliaManager.listar_estructuras_disponibles()
        opciones_estructuras = [{"label": est, "value": est} for est in estructuras]
        
        # Cargar columnas disponibles
        columnas_estructura = [col['id'] for col in columnas if col['id'].startswith('Estr.')]
        opciones_columnas = [{"label": col, "value": col} for col in columnas_estructura]
        
        return True, opciones_estructuras, opciones_columnas
    
    elif trigger_id in ["modal-cargar-columna-confirmar", "modal-cargar-columna-cancelar"]:
        return False, no_update, no_update
    
    return no_update, no_update, no_update

@callback(
    [Output("tabla-familia", "data", allow_duplicate=True),
     Output("modal-cargar-columna", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "is_open", allow_duplicate=True),
     Output("toast-notificacion", "header", allow_duplicate=True),
     Output("toast-notificacion", "children", allow_duplicate=True),
     Output("toast-notificacion", "color", allow_duplicate=True)],
    Input("modal-cargar-columna-confirmar", "n_clicks"),
    [State("select-estructura-cargar-columna", "value"),
     State("select-columna-destino", "value"),
     State("tabla-familia", "data")],
    prevent_initial_call=True
)
def cargar_columna_confirmado(n_clicks, estructura_seleccionada, columna_destino, tabla_data):
    """Carga datos de estructura en columna seleccionada"""
    if not n_clicks or not estructura_seleccionada or not columna_destino:
        return no_update, no_update, False, "", "", "info"
    
    try:
        # Cargar estructura seleccionada
        estructura_data = FamiliaManager.cargar_estructura_individual(estructura_seleccionada)
        
        # Actualizar tabla con datos de la estructura
        tabla_actualizada = []
        for fila in tabla_data:
            nueva_fila = fila.copy()
            parametro = fila["parametro"]
            
            # Obtener valor de la estructura
            if parametro in estructura_data:
                nueva_fila[columna_destino] = estructura_data[parametro]
            elif parametro == "cantidad":
                nueva_fila[columna_destino] = 1  # Valor por defecto
            
            tabla_actualizada.append(nueva_fila)
        
        return (tabla_actualizada, False, True, "Éxito", 
               f"Datos de '{estructura_seleccionada}' cargados en '{columna_destino}'", "success")
    
    except Exception as e:
        return (no_update, False, True, "Error", 
               f"Error al cargar estructura: {str(e)}", "danger")

def register_callbacks(app):
    """Registra todos los callbacks del controller"""
    # Los callbacks ya están definidos con @callback
    pass