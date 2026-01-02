"""
Controller para Familia de Estructuras - Implementación limpia y escalable
"""

from dash import Input, Output, State, callback, dash, no_update, html, dcc, ALL, ctx
import dash_bootstrap_components as dbc
from typing import Dict, List, Any, Optional
import json
import threading
from pathlib import Path

from utils.parametros_manager import ParametrosManager
from models.app_state import AppState
from config.app_config import DATA_DIR
from utils.calculo_cache import CalculoCache
from utils.view_helpers import ViewHelpers

# ============================================================================
# UTILIDADES DE ARCHIVO
# ============================================================================

def sanitizar_nombre_archivo(nombre: str) -> str:
    """Limpia nombre para uso como archivo"""
    return nombre.replace(' ', '_').replace('/', '_').replace('\\', '_').replace(':', '_')

def obtener_archivos_familia() -> List[str]:
    """Obtiene lista de archivos .familia.json disponibles"""
    try:
        archivos = list(DATA_DIR.glob("*.familia.json"))
        return [archivo.stem for archivo in archivos]
    except:
        return []

def cargar_familia_desde_archivo(nombre_familia: str) -> Optional[Dict]:
    """Carga familia desde archivo .familia.json"""
    try:
        archivo = DATA_DIR / f"{sanitizar_nombre_archivo(nombre_familia)}.familia.json"
        if archivo.exists():
            with open(archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error cargando familia {nombre_familia}: {e}")
    return None

def guardar_familia_en_archivo(nombre_familia: str, datos_familia: Dict) -> bool:
    """Guarda familia en archivo .familia.json"""
    try:
        archivo = DATA_DIR / f"{sanitizar_nombre_archivo(nombre_familia)}.familia.json"
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos_familia, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando familia {nombre_familia}: {e}")
        return False

# ============================================================================
# CONVERSIÓN TABLA <-> FAMILIA
# ============================================================================

def tabla_a_familia(tabla_data: List[Dict], columnas: List[Dict], nombre_familia: str) -> Dict:
    """Convierte datos de tabla a formato .familia.json"""
    from datetime import datetime
    
    # Extraer columnas de estructura (Estr.1, Estr.2, etc.)
    columnas_estructura = [col['id'] for col in columnas if col['id'].startswith('Estr.')]
    
    estructuras = {}
    for col_id in columnas_estructura:
        estructura_data = {}
        
        # Convertir filas de tabla a estructura
        for fila in tabla_data:
            parametro = fila['parametro']
            valor = fila.get(col_id, fila.get('valor', ''))
            
            # Convertir tipos
            tipo = fila.get('tipo', 'str')
            if tipo == 'int':
                try:
                    valor = int(valor)
                except:
                    valor = 0
            elif tipo == 'float':
                try:
                    valor = float(valor)
                except:
                    valor = 0.0
            elif tipo == 'bool':
                valor = bool(valor) if isinstance(valor, bool) else str(valor).lower() == 'true'
            
            estructura_data[parametro] = valor
        
        estructuras[col_id] = estructura_data
    
    return {
        "nombre_familia": nombre_familia,
        "fecha_creacion": datetime.now().isoformat(),
        "fecha_modificacion": datetime.now().isoformat(),
        "estructuras": estructuras
    }

def familia_a_tabla(datos_familia: Dict) -> tuple[List[Dict], List[Dict]]:
    """Convierte formato .familia.json a datos de tabla"""
    if not datos_familia or 'estructuras' not in datos_familia:
        return [], []
    
    # Cargar plantilla para obtener estructura base
    try:
        with open(DATA_DIR / "plantilla.estructura.json", 'r', encoding='utf-8') as f:
            plantilla = json.load(f)
    except:
        return [], []
    
    # Generar tabla usando ParametrosManager
    tabla_base = ParametrosManager.estructura_a_tabla(plantilla)
    
    # Crear columnas base
    columnas = [
        {"name": "Parámetro", "id": "parametro", "editable": False},
        {"name": "Símbolo", "id": "simbolo", "editable": False},
        {"name": "Unidad", "id": "unidad", "editable": False},
        {"name": "Descripción", "id": "descripcion", "editable": False}
    ]
    
    # Agregar columnas de estructura
    estructuras = datos_familia['estructuras']
    for nombre_estructura in sorted(estructuras.keys()):
        columnas.append({
            "name": nombre_estructura,
            "id": nombre_estructura,
            "editable": True
        })
    
    # Llenar datos de tabla
    tabla_data = []
    for fila_base in tabla_base:
        fila = {
            "parametro": fila_base["parametro"],
            "simbolo": fila_base["simbolo"],
            "unidad": fila_base["unidad"],
            "descripcion": fila_base["descripcion"],
            "tipo": fila_base["tipo"],
            "categoria": fila_base["categoria"]
        }
        
        # Agregar valores de cada estructura
        for nombre_estructura, estructura_data in estructuras.items():
            valor = estructura_data.get(fila_base["parametro"], fila_base["valor"])
            fila[nombre_estructura] = valor
        
        tabla_data.append(fila)
    
    return tabla_data, columnas

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
        archivos_familia = list(DATA_DIR.glob("*.familia.json"))
        print(f"DEBUG: Archivos encontrados: {[str(a) for a in archivos_familia]}")
        
        opciones = []
        for archivo in archivos_familia:
            # Para el label, remover .familia del stem
            # Para el value, usar el stem completo para que coincida con la lógica de carga
            stem_completo = archivo.stem  # ej: "asdasd.familia"
            label_limpio = stem_completo.replace(".familia", "")  # ej: "asdasd"
            opciones.append({"label": label_limpio, "value": stem_completo})
        
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
    datos_familia = cargar_familia_desde_archivo(nombre_limpio)
    
    if not datos_familia:
        print(f"DEBUG: No se pudo cargar familia {nombre_limpio}")
        return no_update, no_update, no_update, True, "Error", f"No se pudo cargar la familia '{nombre_limpio}'", "danger"
    
    print(f"DEBUG: Familia cargada exitosamente: {datos_familia.get('nombre_familia')}")
    tabla_data, columnas = familia_a_tabla(datos_familia)
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
    if not n_clicks or not nombre_familia or not tabla_data:
        return False, "", "", "info", no_update, no_update
    
    try:
        datos_familia = tabla_a_familia(tabla_data, columnas, nombre_familia)
        
        if guardar_familia_en_archivo(nombre_familia, datos_familia):
            # Marcar como familia activa
            try:
                state = AppState()
                state.set_familia_activa(sanitizar_nombre_archivo(nombre_familia))
                print(f"DEBUG: Familia guardada y marcada como activa: {nombre_familia}")
            except Exception as e:
                print(f"DEBUG: Error marcando familia activa: {e}")
            
            # Actualizar opciones del dropdown
            archivos = obtener_archivos_familia()
            opciones = [{"label": archivo, "value": archivo} for archivo in archivos]
            
            return (True, "Éxito", f"Familia '{nombre_familia}' guardada correctamente", "success", 
                   datos_familia, opciones)
        else:
            return True, "Error", "No se pudo guardar la familia", "danger", no_update, no_update
    
    except Exception as e:
        return True, "Error", f"Error al guardar: {str(e)}", "danger", no_update, no_update

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
    if not familia_data:
        return "Ninguna"
    
    nombre_familia = familia_data.get('nombre_familia', 'Familia')
    return f"📁 {nombre_familia}"

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

def register_callbacks(app):
    """Registra todos los callbacks del controller"""
    # Los callbacks ya están definidos con @callback
    pass