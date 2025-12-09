"""
Componentes para entrada de parámetros de estructura
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def crear_input_parametro(param_key, param_value, param_type, opciones=None):
    """
    Crear componente de entrada para un parámetro
    
    Args:
        param_key: Nombre del parámetro
        param_value: Valor actual
        param_type: Tipo de dato (str, int, float, bool, list)
        opciones: Lista de opciones para tipos de lista
    """
    
    # Determinar tipo de input basado en el tipo de dato
    if param_type == bool:
        return dbc.Row([
            dbc.Col(dbc.Label(param_key), width=6),
            dbc.Col(
                dbc.Switch(
                    id={"type": "param-input", "index": param_key},
                    value=bool(param_value),
                    className="mt-1"
                ),
                width=6
            )
        ], className="mb-3")
    
    elif param_type == str and opciones:
        # Select para listas de strings
        return dbc.Row([
            dbc.Col(dbc.Label(param_key), width=6),
            dbc.Col(
                dbc.Select(
                    id={"type": "param-input", "index": param_key},
                    value=str(param_value),
                    options=[{"label": opt, "value": opt} for opt in opciones],
                    className="mt-1"
                ),
                width=6
            )
        ], className="mb-3")
    
    elif param_type == int:
        # Input numérico con step 1
        return dbc.Row([
            dbc.Col(dbc.Label(param_key), width=6),
            dbc.Col(
                dbc.Input(
                    id={"type": "param-input", "index": param_key},
                    value=int(param_value),
                    type="number",
                    step=1,
                    className="mt-1"
                ),
                width=6
            )
        ], className="mb-3")
    
    elif param_type == float:
        # Input numérico con step pequeño
        return dbc.Row([
            dbc.Col(dbc.Label(param_key), width=6),
            dbc.Col(
                dbc.Input(
                    id={"type": "param-input", "index": param_key},
                    value=float(param_value),
                    type="number",
                    step="any",
                    className="mt-1"
                ),
                width=6
            )
        ], className="mb-3")
    
    else:
        # Input de texto por defecto
        return dbc.Row([
            dbc.Col(dbc.Label(param_key), width=6),
            dbc.Col(
                dbc.Input(
                    id={"type": "param-input", "index": param_key},
                    value=str(param_value),
                    type="text",
                    className="mt-1"
                ),
                width=6
            )
        ], className="mb-3")

def crear_grupo_parametros(grupo_nombre, parametros, estructura_data, opciones_especiales=None):
    """
    Crear un grupo de parámetros (acordeón)
    
    Args:
        grupo_nombre: Nombre del grupo
        parametros: Lista de tuplas (clave, tipo, descripción)
        estructura_data: Diccionario con datos actuales
        opciones_especiales: Diccionario con opciones para parámetros específicos
    """
    
    items = []
    for param_key, param_type, descripcion in parametros:
        if param_key in estructura_data:
            value = estructura_data[param_key]
            
            # Obtener opciones si existen
            opciones = None
            if opciones_especiales and param_key in opciones_especiales:
                opciones = opciones_especiales[param_key]
            
            items.append(
                dbc.Card([
                    dbc.CardBody([
                        crear_input_parametro(param_key, value, param_type, opciones),
                        html.Small(descripcion, className="text-muted")
                    ])
                ], className="mb-2")
            )
    
    return dbc.AccordionItem(
        title=grupo_nombre,
        children=items
    )