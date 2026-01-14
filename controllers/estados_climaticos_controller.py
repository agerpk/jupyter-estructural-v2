"""
Controller para modal de estados climáticos de estructuras individuales.
"""

import dash
from dash import Input, Output, State, ALL, callback_context
import json
from pathlib import Path
from config.app_config import DATA_DIR
from components.modal_estados_climaticos import generar_tabla_estados


def extraer_estados_de_inputs(inputs_temp, inputs_desc, inputs_viento, inputs_hielo, 
                               inputs_rest_cond, inputs_rest_guard, inputs_relflecha):
    """
    Extrae estados climáticos desde los inputs del modal
    
    Returns:
        dict: {id: {temperatura, descripcion, viento_velocidad, ...}}
    """
    estados = {}
    
    for i in range(len(inputs_temp)):
        estado_id = str(i + 1)  # IDs numéricos 1, 2, 3...
        
        estados[estado_id] = {
            "temperatura": inputs_temp[i] if inputs_temp[i] is not None else 0,
            "descripcion": inputs_desc[i] if inputs_desc[i] else "",
            "viento_velocidad": inputs_viento[i] if inputs_viento[i] is not None else 0,
            "espesor_hielo": inputs_hielo[i] if inputs_hielo[i] is not None else 0,
            "restriccion_conductor": inputs_rest_cond[i] if inputs_rest_cond[i] is not None else 0.25,
            "restriccion_guardia": inputs_rest_guard[i] if inputs_rest_guard[i] is not None else 0.7,
            "relflecha": inputs_relflecha[i] if inputs_relflecha[i] is not None else 0.9
        }
    
    return estados


def register_callbacks(app):
    """Registra callbacks del modal de estados climáticos para estructuras"""
    
    # Abrir modal
    @app.callback(
        [Output("modal-estados-estructura", "is_open"),
         Output("modal-estados-estructura-tabla-container", "children"),
         Output("modal-estados-estructura-estados-data", "data")],
        Input("btn-abrir-estados-estructura", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def abrir_modal(n_clicks, estructura_actual):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        # Cargar estados actuales
        estados = estructura_actual.get("estados_climaticos", {
            "1": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, 
                  "espesor_hielo": 0, "restriccion_conductor": 0.25, 
                  "restriccion_guardia": 0.7, "relflecha": 0.9}
        })
        
        tabla = generar_tabla_estados(estados, "modal-estados-estructura")
        
        return True, tabla, estados
    
    # Agregar estado
    @app.callback(
        [Output("modal-estados-estructura-tabla-container", "children", allow_duplicate=True),
         Output("modal-estados-estructura-estados-data", "data", allow_duplicate=True)],
        Input("modal-estados-estructura-btn-agregar", "n_clicks"),
        State("modal-estados-estructura-estados-data", "data"),
        prevent_initial_call=True
    )
    def agregar_estado(n_clicks, estados_actuales):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        # Encontrar primer ID disponible
        ids_usados = [int(id) for id in estados_actuales.keys()]
        nuevo_id = 1
        while nuevo_id in ids_usados:
            nuevo_id += 1
        
        # Copiar datos del último estado
        ultimo_estado = list(estados_actuales.values())[-1]
        estados_actuales[str(nuevo_id)] = ultimo_estado.copy()
        
        tabla = generar_tabla_estados(estados_actuales, "modal-estados-estructura")
        
        return tabla, estados_actuales
    
    # Eliminar estado
    @app.callback(
        [Output("modal-estados-estructura-tabla-container", "children", allow_duplicate=True),
         Output("modal-estados-estructura-estados-data", "data", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input({"type": "btn-eliminar", "modal": "modal-estados-estructura", "id": ALL}, "n_clicks"),
        State("modal-estados-estructura-estados-data", "data"),
        prevent_initial_call=True
    )
    def eliminar_estado(n_clicks_list, estados_actuales):
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate
        
        # Validar mínimo 1 estado
        if len(estados_actuales) <= 1:
            return (dash.no_update, dash.no_update, True, "Advertencia", 
                    "Debe haber al menos 1 estado climático", "warning", "warning")
        
        # Obtener ID del estado a eliminar
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        estado_id = eval(trigger_id)["id"]
        
        # Eliminar estado
        if estado_id in estados_actuales:
            del estados_actuales[estado_id]
        
        tabla = generar_tabla_estados(estados_actuales, "modal-estados-estructura")
        
        return tabla, estados_actuales, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Guardar estados
    @app.callback(
        [Output("estructura-actual", "data", allow_duplicate=True),
         Output("modal-estados-estructura", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("modal-estados-estructura-btn-guardar", "n_clicks"),
        [State({"type": "input-temp", "modal": "modal-estados-estructura", "id": ALL}, "value"),
         State({"type": "input-desc", "modal": "modal-estados-estructura", "id": ALL}, "value"),
         State({"type": "input-viento", "modal": "modal-estados-estructura", "id": ALL}, "value"),
         State({"type": "input-hielo", "modal": "modal-estados-estructura", "id": ALL}, "value"),
         State({"type": "input-rest-cond", "modal": "modal-estados-estructura", "id": ALL}, "value"),
         State({"type": "input-rest-guard", "modal": "modal-estados-estructura", "id": ALL}, "value"),
         State({"type": "input-relflecha", "modal": "modal-estados-estructura", "id": ALL}, "value"),
         State("estructura-actual", "data")],
        prevent_initial_call=True
    )
    def guardar_estados(n_clicks, temps, descs, vientos, hielos, rest_conds, rest_guards, relflechas, estructura_actual):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        # Extraer estados de inputs
        estados = extraer_estados_de_inputs(temps, descs, vientos, hielos, rest_conds, rest_guards, relflechas)
        
        # Actualizar estructura
        estructura_actual["estados_climaticos"] = estados
        
        # Guardar archivo
        nombre = estructura_actual.get("TITULO", "estructura")
        archivo = DATA_DIR / f"{nombre}.estructura.json"
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(estructura_actual, f, indent=2, ensure_ascii=False)
        
        return (estructura_actual, False, True, "Éxito", 
                f"Estados climáticos guardados ({len(estados)} estados)", "success", "success")
    
    # Cancelar
    @app.callback(
        Output("modal-estados-estructura", "is_open", allow_duplicate=True),
        Input("modal-estados-estructura-btn-cancelar", "n_clicks"),
        prevent_initial_call=True
    )
    def cancelar_modal(n_clicks):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        return False
    
    # Abrir sub-modal copiar estados
    @app.callback(
        [Output("modal-copiar-estados", "is_open"),
         Output("modal-copiar-estados-dropdown-estructuras", "options")],
        Input("modal-estados-estructura-btn-copiar", "n_clicks"),
        prevent_initial_call=True
    )
    def abrir_modal_copiar(n_clicks):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        # Listar archivos .estructura.json en DATA_DIR
        estructuras = []
        for archivo in DATA_DIR.glob("*.estructura.json"):
            nombre = archivo.stem.replace(".estructura", "")
            estructuras.append({"label": nombre, "value": str(archivo)})
        
        return True, estructuras
    
    # Confirmar copiar estados
    @app.callback(
        [Output("modal-estados-estructura-tabla-container", "children", allow_duplicate=True),
         Output("modal-estados-estructura-estados-data", "data", allow_duplicate=True),
         Output("modal-copiar-estados", "is_open", allow_duplicate=True)],
        Input("modal-copiar-estados-btn-confirmar", "n_clicks"),
        State("modal-copiar-estados-dropdown-estructuras", "value"),
        prevent_initial_call=True
    )
    def confirmar_copiar_estados(n_clicks, archivo_origen):
        if n_clicks is None or not archivo_origen:
            raise dash.exceptions.PreventUpdate
        
        # Cargar estructura origen
        with open(archivo_origen, 'r', encoding='utf-8') as f:
            estructura_origen = json.load(f)
        
        estados_origen = estructura_origen.get("estados_climaticos", {})
        
        # Detectar y convertir legacy (I, II, III, IV, V)
        if any(id in ["I", "II", "III", "IV", "V"] for id in estados_origen.keys()):
            estados_nuevos = {}
            nuevo_id = 1
            for id_origen, datos in estados_origen.items():
                if id_origen not in ["I", "II", "III", "IV", "V"]:
                    estados_nuevos[str(nuevo_id)] = datos
                    nuevo_id += 1
        else:
            # Copiar con IDs numéricos secuenciales
            estados_nuevos = {}
            nuevo_id = 1
            for datos in estados_origen.values():
                estados_nuevos[str(nuevo_id)] = datos
                nuevo_id += 1
        
        # Generar nueva tabla
        tabla = generar_tabla_estados(estados_nuevos, "modal-estados-estructura")
        
        return tabla, estados_nuevos, False
    
    # Cancelar sub-modal copiar
    @app.callback(
        Output("modal-copiar-estados", "is_open", allow_duplicate=True),
        Input("modal-copiar-estados-btn-cancelar", "n_clicks"),
        prevent_initial_call=True
    )
    def cancelar_modal_copiar(n_clicks):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        return False
