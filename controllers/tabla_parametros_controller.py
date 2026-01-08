"""
Controller para tabla de parámetros - callbacks y lógica de sincronización.
"""

from dash import Input, Output, State, callback, dash, no_update, html, dcc, ALL, ctx
import dash_bootstrap_components as dbc
from typing import Dict, List, Any
import json

from utils.parametros_manager import ParametrosManager
from utils.validadores_parametros import ValidadoresParametros
from components.tabla_parametros import validar_tabla_parametros
from models.app_state import AppState
from components.pestanas_parametros import crear_tabla_estados_climaticos_ajuste

# Modal para estados climáticos (compartido entre tabla y panel)
modal_estados_panel = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Estados Climáticos y Restricciones")),
    dbc.ModalBody(id="modal-estados-panel-body"),
    dbc.ModalFooter([
        dbc.Button("Cancelar", id="modal-estados-panel-cancelar", color="secondary", className="me-2"),
        dbc.Button("Guardar", id="modal-estados-panel-guardar", color="primary")
    ])
], id="modal-estados-panel", is_open=False, size="xl")

@callback(
    [Output("contenido-pestana-parametros", "children"),
     Output("toast-validacion-tabla", "is_open", allow_duplicate=True),
     Output("toast-validacion-tabla", "children", allow_duplicate=True),
     Output("toast-validacion-tabla", "icon", allow_duplicate=True)],
    Input("pestanas-parametros", "active_tab"),
    State("estructura-actual", "data"),
    prevent_initial_call='initial_duplicate'
)
def cambiar_pestana_parametros(tab_activo, estructura_actual):
    """Cambia contenido según pestaña activa"""
    
    if not tab_activo:
        tab_activo = "tabla"
    
    # Recargar estructura desde archivo para asegurar datos actualizados
    from config.app_config import DATA_DIR
    state = AppState()
    try:
        titulo = estructura_actual.get('TITULO', 'estructura') if estructura_actual else 'estructura'
        ruta_estructura = DATA_DIR / f"{titulo}.estructura.json"
        estructura_actual = state.estructura_manager.cargar_estructura(ruta_estructura)
    except:
        if not estructura_actual:
            return "No hay estructura cargada", False, "", "warning"
    
    try:
        # Obtener cables disponibles una sola vez
        try:
            with open("data/cables.json", "r", encoding="utf-8") as f:
                cables_data = json.load(f)
                cables_disponibles = list(cables_data.keys())
        except:
            cables_disponibles = []
        
        if tab_activo == "tabla":
            from components.tabla_parametros import crear_tabla_parametros, crear_filtros_categoria
            from components.pestanas_parametros import crear_alerta_sincronizacion
            
            contenido = [
                crear_filtros_categoria(),
                crear_tabla_parametros(estructura_actual, cables_disponibles)
            ]
            
        elif tab_activo == "panel":
            from components.vista_ajuste_parametros import crear_vista_ajuste_parametros
            
            contenido = html.Div([
                crear_vista_ajuste_parametros(estructura_actual, cables_disponibles),
                modal_estados_panel
            ])
        
        else:
            return "Pestaña no válida", False, "", "warning"
        
        return contenido, False, "", "success"
        
    except Exception as e:
        return f"Error al cargar contenido: {str(e)}", True, f"Error: {str(e)}", "danger"

@callback(
    [Output("tabla-parametros", "data", allow_duplicate=True),
     Output("toast-validacion-tabla", "is_open", allow_duplicate=True),
     Output("toast-validacion-tabla", "children", allow_duplicate=True),
     Output("toast-validacion-tabla", "icon", allow_duplicate=True)],
    Input("filtro-categoria", "value"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def filtrar_por_categoria(categoria_seleccionada, estructura_actual):
    """Filtra tabla por categoría"""
    
    # Recargar desde archivo para tener datos actualizados
    from config.app_config import DATA_DIR
    state = AppState()
    try:
        titulo = estructura_actual.get('TITULO', 'estructura') if estructura_actual else 'estructura'
        ruta_estructura = DATA_DIR / f"{titulo}.estructura.json"
        estructura_actual = state.estructura_manager.cargar_estructura(ruta_estructura)
    except:
        pass
    
    if not estructura_actual:
        return no_update, False, "", "info"
    
    try:
        tabla_data = ParametrosManager.estructura_a_tabla(estructura_actual)
        
        if categoria_seleccionada != "todas":
            tabla_data = [fila for fila in tabla_data if fila["categoria"] == categoria_seleccionada]
        
        return tabla_data, False, "", "success"
        
    except Exception as e:
        return no_update, True, f"Error al filtrar: {str(e)}", "danger"

@callback(
    [Output("estructura-actual", "data", allow_duplicate=True),
     Output("toast-validacion-tabla", "is_open", allow_duplicate=True),
     Output("toast-validacion-tabla", "children", allow_duplicate=True),
     Output("toast-validacion-tabla", "icon", allow_duplicate=True)],
    Input("guardar-parametros-tabla", "n_clicks"),
    State("tabla-parametros", "data"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def guardar_parametros_desde_tabla(n_clicks, tabla_data, estructura_actual):
    """Guarda parámetros editados en tabla"""
    
    if not n_clicks or not tabla_data:
        return no_update, False, "", "info"
    
    try:
        # Validar datos de tabla
        errores = validar_tabla_parametros(tabla_data)
        
        if errores:
            mensaje_error = "Errores de validación encontrados:\n"
            for error in errores[:3]:  # Mostrar máximo 3 errores
                mensaje_error += f"• {error['parametro']}: {error['error']}\n"
            
            if len(errores) > 3:
                mensaje_error += f"... y {len(errores) - 3} errores más"
            
            return no_update, True, mensaje_error, "danger"
        
        # Convertir tabla a estructura
        estructura_actualizada = ParametrosManager.tabla_a_estructura(tabla_data)
        
        # Mantener campos que no están en la tabla
        for key, value in estructura_actual.items():
            if key not in estructura_actualizada:
                estructura_actualizada[key] = value
        
        # Guardar directamente en {TITULO}.estructura.json
        from config.app_config import DATA_DIR
        state = AppState()
        titulo = estructura_actualizada.get('TITULO', 'estructura')
        ruta_estructura = DATA_DIR / f"{titulo}.estructura.json"
        
        # Guardar en el archivo usando el manager
        state.estructura_manager.guardar_estructura(estructura_actualizada, ruta_estructura)
        
        # Actualizar el estado interno
        state.set_estructura_actual(estructura_actualizada)
        
        return estructura_actualizada, True, "Parámetros guardados exitosamente", "success"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return no_update, True, f"Error al guardar: {str(e)}", "danger"

@callback(
    Output("tabla-parametros", "data", allow_duplicate=True),
    Input("buscar-parametro", "value"),
    State("tabla-parametros", "data"),
    prevent_initial_call=True
)
def buscar_parametro(texto_busqueda, tabla_data):
    """Filtra tabla por texto de búsqueda"""
    
    if not texto_busqueda:
        # Si no hay búsqueda, recargar desde archivo
        from config.app_config import DATA_DIR
        state = AppState()
        try:
            # Obtener TITULO desde tabla_data si está disponible
            titulo = 'estructura'
            if tabla_data and len(tabla_data) > 0:
                for fila in tabla_data:
                    if fila.get('parametro') == 'TITULO':
                        titulo = fila.get('valor', 'estructura')
                        break
            ruta_estructura = DATA_DIR / f"{titulo}.estructura.json"
            estructura_actual = state.estructura_manager.cargar_estructura(ruta_estructura)
            return ParametrosManager.estructura_a_tabla(estructura_actual)
        except:
            return no_update
    
    if not tabla_data:
        return no_update
    
    texto_lower = texto_busqueda.lower()
    
    tabla_filtrada = [
        fila for fila in tabla_data
        if (texto_lower in fila["parametro"].lower() or 
            texto_lower in fila["descripcion"].lower() or
            texto_lower in fila["simbolo"].lower())
    ]
    
    return tabla_filtrada

@callback(
    [Output("tabla-parametros", "style_data_conditional", allow_duplicate=True),
     Output("toast-validacion-tabla", "is_open", allow_duplicate=True),
     Output("toast-validacion-tabla", "children", allow_duplicate=True),
     Output("toast-validacion-tabla", "icon", allow_duplicate=True)],
    Input("tabla-parametros", "data_timestamp"),
    State("tabla-parametros", "data"),
    prevent_initial_call=True
)
def validar_en_tiempo_real(timestamp, tabla_data):
    """Valida datos en tiempo real y aplica estilos"""
    
    if not tabla_data:
        return no_update, False, "", "info"
    
    try:
        errores = validar_tabla_parametros(tabla_data)
        
        # Estilos base
        estilos = [
            {
                'if': {'column_id': 'valor'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'column_id': 'parametro'},
                'fontWeight': 'bold'
            }
        ]
        
        # Agregar estilos para errores
        for error in errores:
            estilos.append({
                'if': {
                    'filter_query': f'{{parametro}} = {error["parametro"]}',
                    'column_id': 'valor'
                },
                'backgroundColor': '#f8d7da',
                'color': '#721c24'
            })
        
        # Mostrar notificación si hay errores
        if errores:
            mensaje = f"Se encontraron {len(errores)} errores de validación"
            return estilos, True, mensaje, "warning"
        
        return estilos, False, "", "success"
        
    except Exception as e:
        return no_update, True, f"Error en validación: {str(e)}", "danger"

@callback(
    [Output("modal-parametro", "is_open"),
     Output("modal-body-parametro", "children"),
     Output("modal-celda-info", "data")],
    [Input("tabla-parametros", "active_cell"),
     Input("modal-confirmar", "n_clicks"),
     Input("modal-cancelar", "n_clicks")],
    [State("modal-parametro", "is_open"),
     State("tabla-parametros", "data")],
    prevent_initial_call=True
)
def manejar_modal_parametro(active_cell, n_confirm, n_cancel, is_open, tabla_data):
    """Maneja apertura/cierre del modal"""
    if not ctx.triggered:
        return no_update, no_update, no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Abrir modal al hacer clic en celda
    if trigger_id == "tabla-parametros" and active_cell:
        if active_cell["column_id"] != "valor":
            return no_update, no_update, no_update
        
        fila = active_cell["row"]
        parametro = tabla_data[fila]["parametro"]
        valor_actual = tabla_data[fila]["valor"]
        tipo = tabla_data[fila]["tipo"]
        
        # Obtener opciones si es select
        opciones = ParametrosManager.obtener_opciones_parametro(parametro)
        
        # Para cables, cargar opciones dinámicamente desde cables.json
        if parametro in ["cable_conductor_id", "cable_guardia_id", "cable_guardia2_id"] and not opciones:
            try:
                with open("data/cables.json", "r", encoding="utf-8") as f:
                    cables_data = json.load(f)
                    opciones = list(cables_data.keys())
            except:
                opciones = []
        
        if opciones and len(opciones) > 0:
            # Modal con botones para opciones
            botones = []
            for opcion in opciones:
                color = "primary" if opcion == valor_actual else "outline-secondary"
                botones.append(
                    dbc.Button(
                        str(opcion),
                        id={"type": "opcion-btn", "value": opcion},
                        color=color,
                        className="me-2 mb-2",
                        size="sm"
                    )
                )
            contenido = html.Div([
                html.P(f"Seleccione valor para {parametro}:"),
                html.Div(botones)
            ])
            celda_info = {"fila": fila, "parametro": parametro, "tipo": tipo}
            return True, contenido, celda_info
        
        elif tipo == "bool":
            # Modal para booleanos
            contenido = html.Div([
                html.P(f"Seleccione valor para {parametro}:"),
                dbc.ButtonGroup([
                    dbc.Button(
                        "Verdadero",
                        id={"type": "bool-btn", "value": True},
                        color="success" if valor_actual else "outline-success"
                    ),
                    dbc.Button(
                        "Falso",
                        id={"type": "bool-btn", "value": False},
                        color="danger" if not valor_actual else "outline-danger"
                    )
                ])
            ])
            celda_info = {"fila": fila, "parametro": parametro, "tipo": tipo}
            return True, contenido, celda_info
        
        elif tipo in ["int", "float"]:
            # No abrir modal para numéricos, editar directo en celda
            return no_update, no_update, no_update
        
        else:
            # Para str sin opciones, verificar si es parámetro de color
            if parametro.startswith("parametros_graficos.colores."):
                # Modal con color picker nativo HTML5
                contenido = html.Div([
                    html.P(f"Seleccione color para {parametro}:"),
                    html.Div([
                        html.Label("Selector de color:", style={"marginBottom": "5px"}),
                        dcc.Input(
                            id="native-color-picker",
                            type="color",
                            value=valor_actual if valor_actual else "#000000",
                            style={
                                "width": "100%",
                                "height": "150px",
                                "border": "1px solid #ccc",
                                "borderRadius": "4px",
                                "cursor": "pointer"
                            }
                        )
                    ], className="mb-3"),
                    html.Div([
                        html.Label("Código hexadecimal:", style={"marginBottom": "5px"}),
                        dbc.Input(
                            id="input-hex-color",
                            type="text",
                            value=valor_actual if valor_actual else "#000000",
                            placeholder="#RRGGBB",
                            style={"fontFamily": "monospace"}
                        )
                    ])
                ])
                celda_info = {"fila": fila, "parametro": parametro, "tipo": "hex_color"}
                return True, contenido, celda_info
            else:
                # Para str sin opciones, editar directo en celda
                return no_update, no_update, no_update
    
    # Cerrar modal
    elif trigger_id in ["modal-confirmar", "modal-cancelar"]:
        return False, no_update, no_update
    
    return no_update, no_update, no_update

@callback(
    [Output("input-hex-color", "value"),
     Output("native-color-picker", "value")],
    [Input("native-color-picker", "value"),
     Input("input-hex-color", "value")],
    prevent_initial_call=True
)
def sincronizar_color_pickers(color_picker_value, hex_input_value):
    """Sincroniza el color picker nativo con el input hex"""
    if not ctx.triggered:
        return no_update, no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Si cambió el color picker nativo, actualizar el input hex
    if trigger_id == "native-color-picker":
        return color_picker_value.upper(), no_update
    
    # Si cambió el input hex, actualizar el color picker
    elif trigger_id == "input-hex-color":
        # Validar que sea un color hex válido
        if hex_input_value and hex_input_value.startswith("#") and len(hex_input_value) == 7:
            return no_update, hex_input_value
    
    return no_update, no_update

@callback(
    [Output("tabla-parametros", "data", allow_duplicate=True),
     Output("modal-parametro", "is_open", allow_duplicate=True)],
    [Input({"type": "opcion-btn", "value": ALL}, "n_clicks"),
     Input({"type": "bool-btn", "value": ALL}, "n_clicks"),
     Input("modal-confirmar", "n_clicks")],
    [State("modal-celda-info", "data"),
     State("tabla-parametros", "data"),
     State("input-hex-color", "value")],
    prevent_initial_call=True
)
def seleccionar_opcion_directa(n_clicks_opciones, n_clicks_bool, n_confirmar, celda_info, tabla_data, hex_value):
    """Actualiza tabla directamente al seleccionar opción y cierra modal"""
    if not ctx.triggered or not celda_info:
        return no_update, no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Si es confirmar en modal hex_color
    if trigger_id == "modal-confirmar" and celda_info.get("tipo") == "hex_color":
        if hex_value:
            fila = celda_info["fila"]
            tabla_data[fila]["valor"] = hex_value.upper()
            return tabla_data, False
        return no_update, no_update
    
    # Obtener el valor seleccionado de botones
    trigger = ctx.triggered[0]
    if trigger["value"] is None:
        return no_update, no_update
    
    # Extraer valor del componente que disparó el callback
    component_id = trigger["prop_id"].split(".")[0]
    import json
    component_data = json.loads(component_id)
    valor_seleccionado = component_data["value"]
    
    # Actualizar tabla
    fila = celda_info["fila"]
    tabla_data[fila]["valor"] = valor_seleccionado
    
    # Cerrar modal y actualizar tabla
    return tabla_data, False

@callback(
    [Output("modal-estados-tabla", "is_open"),
     Output("modal-estados-tabla-body", "children")],
    [Input("btn-modificar-estados-tabla", "n_clicks"),
     Input("modal-estados-tabla-cancelar", "n_clicks"),
     Input("modal-estados-tabla-guardar", "n_clicks")],
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def manejar_modal_estados_tabla(n_abrir, n_cancelar, n_guardar, estructura_actual):
    """Maneja apertura/cierre del modal de estados climáticos"""
    if not ctx.triggered:
        return no_update, no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "btn-modificar-estados-tabla":
        tabla = crear_tabla_estados_climaticos_ajuste(estructura_actual)
        return True, tabla
    
    return False, no_update

@callback(
    [Output("modal-estados-panel", "is_open"),
     Output("modal-estados-panel-body", "children")],
    [Input("btn-modificar-estados-panel", "n_clicks"),
     Input("modal-estados-panel-cancelar", "n_clicks"),
     Input("modal-estados-panel-guardar", "n_clicks")],
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def manejar_modal_estados_panel(n_abrir, n_cancelar, n_guardar, estructura_actual):
    """Maneja apertura/cierre del modal de estados climáticos en panel"""
    if not ctx.triggered:
        return no_update, no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "btn-modificar-estados-panel":
        tabla = crear_tabla_estados_climaticos_ajuste(estructura_actual)
        return True, tabla
    
    return False, no_update