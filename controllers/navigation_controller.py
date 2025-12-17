"""Controlador de navegación"""

import dash
from dash import Input, Output, State, ALL, callback_context
import json
from pathlib import Path
from components.vista_home import crear_vista_home
from components.vista_ajuste_parametros import crear_vista_ajuste_parametros
from components.vista_eliminar_estructura import crear_vista_eliminar_estructura
from components.vista_calculo_mecanico import crear_vista_calculo_mecanico
from components.vista_gestion_cables import crear_vista_agregar_cable, crear_vista_modificar_cable, crear_vista_eliminar_cable
from models.app_state import AppState
from config.app_config import NAVEGACION_STATE_FILE


def guardar_navegacion_state(vista_id):
    """Guarda el estado de navegación"""
    try:
        NAVEGACION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(NAVEGACION_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"ultima_vista": vista_id}, f)
        print(f"DEBUG: Navegación guardada: {vista_id}")
    except Exception as e:
        print(f"ERROR guardando navegación: {e}")

def cargar_navegacion_state():
    """Carga el estado de navegación"""
    try:
        if NAVEGACION_STATE_FILE.exists():
            with open(NAVEGACION_STATE_FILE, 'r', encoding='utf-8') as f:
                vista = json.load(f).get("ultima_vista", "home")
                print(f"DEBUG: Navegación cargada: {vista}")
                return vista
    except Exception as e:
        print(f"ERROR cargando navegación: {e}")
    return "home"

def register_callbacks(app):
    """Registrar callbacks de navegación"""
    
    state = AppState()
    
    @app.callback(
        Output("contenido-principal", "children"),
        Input("btn-inicio", "n_clicks"),
        Input({"type": "btn-volver", "index": ALL}, "n_clicks"),
        Input("store-catenaria-actual", "data"),
        Input("menu-ajustar-parametros", "n_clicks"),
        Input("menu-eliminar-estructura", "n_clicks"),
        Input("menu-calculo-mecanico", "n_clicks"),
        Input("menu-agregar-cable", "n_clicks"),
        Input("menu-modificar-cable", "n_clicks"),
        Input("menu-eliminar-cable", "n_clicks"),
        Input("menu-diseno-geometrico", "n_clicks"),
        Input("menu-diseno-mecanico", "n_clicks"),
        Input("menu-arboles-carga", "n_clicks"),
        Input("menu-seleccion-poste", "n_clicks"),
        Input("menu-calcular-todo", "n_clicks"),
        State("estructura-actual", "data"),
    )
    def navegar_vistas(n_clicks_inicio, btn_volver_clicks, catenaria_data, n_clicks_ajustar, 
                       n_clicks_eliminar, n_clicks_cmc,
                       n_clicks_agregar_cable, n_clicks_modificar_cable, n_clicks_eliminar_cable,
                       n_clicks_diseno_geom, n_clicks_diseno_mec, n_clicks_arboles, n_clicks_sph, 
                       n_clicks_calcular_todo, estructura_actual):
        ctx = callback_context
        
        # Detectar carga inicial (app restart o hot reload)
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
        es_carga_inicial = not ctx.triggered or (trigger_id == "store-catenaria-actual" and not catenaria_data)
        
        if es_carga_inicial:
            ultima_vista = cargar_navegacion_state()
            print(f"DEBUG: Carga inicial detectada, restaurando vista: {ultima_vista}")
            if ultima_vista == "calculo-mecanico":
                from utils.calculo_cache import CalculoCache
                calculo_guardado = None
                if estructura_actual:
                    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                    calculo_guardado = CalculoCache.cargar_calculo_cmc(nombre_estructura)
                return crear_vista_calculo_mecanico(estructura_actual, calculo_guardado)
            elif ultima_vista == "ajustar-parametros":
                cables_disponibles = state.cable_manager.obtener_cables()
                return crear_vista_ajuste_parametros(estructura_actual, cables_disponibles)
            elif ultima_vista == "diseno-geometrico":
                from components.vista_diseno_geometrico import crear_vista_diseno_geometrico
                from utils.calculo_cache import CalculoCache
                calculo_guardado = None
                if estructura_actual:
                    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                    calculo_guardado = CalculoCache.cargar_calculo_dge(nombre_estructura)
                else:
                    estructura_actual = state.estructura_manager.cargar_estructura(state.archivo_actual)
                    if estructura_actual:
                        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                        calculo_guardado = CalculoCache.cargar_calculo_dge(nombre_estructura)
                print(f"DEBUG: Restaurando vista DGE con estructura: {estructura_actual.get('TITULO') if estructura_actual else 'None'}")
                return crear_vista_diseno_geometrico(estructura_actual, calculo_guardado)
            elif ultima_vista == "diseno-mecanico":
                from components.vista_diseno_mecanico import crear_vista_diseno_mecanico
                from utils.calculo_cache import CalculoCache
                from utils.hipotesis_manager import HipotesisManager
                from HipotesisMaestro_Especial import hipotesis_maestro as hipotesis_base
                from config.app_config import DATA_DIR
                
                if not estructura_actual:
                    estructura_actual = state.estructura_manager.cargar_estructura(state.archivo_actual)
                
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                estructura_json_path = str(DATA_DIR / f"{nombre_estructura}.estructura.json")
                hipotesis_maestro = HipotesisManager.cargar_o_crear_hipotesis(
                    nombre_estructura,
                    estructura_json_path,
                    hipotesis_base
                )
                
                calculo_guardado = CalculoCache.cargar_calculo_dme(nombre_estructura)
                return crear_vista_diseno_mecanico(estructura_actual, calculo_guardado, hipotesis_maestro)
            elif ultima_vista == "seleccion-poste":
                from components.vista_seleccion_poste import crear_vista_seleccion_poste
                from utils.calculo_cache import CalculoCache
                calculo_guardado = None
                if estructura_actual:
                    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                    calculo_guardado = CalculoCache.cargar_calculo_sph(nombre_estructura)
                return crear_vista_seleccion_poste(estructura_actual, calculo_guardado)
            elif ultima_vista == "arboles-carga":
                from components.vista_arboles_carga import crear_vista_arboles_carga
                from utils.calculo_cache import CalculoCache
                calculo_guardado = None
                if estructura_actual:
                    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                    calculo_guardado = CalculoCache.cargar_calculo_arboles(nombre_estructura)
                return crear_vista_arboles_carga(estructura_actual, calculo_guardado)
            elif ultima_vista == "calcular-todo":
                from components.vista_calcular_todo import crear_vista_calcular_todo
                from utils.calculo_cache import CalculoCache
                calculo_guardado = None
                if estructura_actual:
                    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                    calculo_guardado = CalculoCache.cargar_calculo_todo(nombre_estructura)
                return crear_vista_calcular_todo(estructura_actual, calculo_guardado)
            elif ultima_vista == "ajustar-catenaria":
                from components.vista_ajustar_catenaria import crear_vista_ajustar_catenaria
                return crear_vista_ajustar_catenaria({})
            return crear_vista_home()
        
        print(f"DEBUG: Trigger detectado: {trigger_id}")
        
        if trigger_id == "store-catenaria-actual":
            if catenaria_data:
                guardar_navegacion_state("ajustar-catenaria")
                from components.vista_ajustar_catenaria import crear_vista_ajustar_catenaria
                return crear_vista_ajustar_catenaria(catenaria_data)
            return dash.no_update
        
        elif trigger_id == "btn-inicio":
            guardar_navegacion_state("home")
            return crear_vista_home()
        
        elif trigger_id == "menu-ajustar-parametros":
            guardar_navegacion_state("ajustar-parametros")
            cables_disponibles = state.cable_manager.obtener_cables()
            return crear_vista_ajuste_parametros(estructura_actual, cables_disponibles)
        
        elif trigger_id == "menu-eliminar-estructura":
            return crear_vista_eliminar_estructura()
        
        elif trigger_id == "menu-calculo-mecanico":
            guardar_navegacion_state("calculo-mecanico")
            from utils.calculo_cache import CalculoCache
            calculo_guardado = None
            if estructura_actual:
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                calculo_guardado = CalculoCache.cargar_calculo_cmc(nombre_estructura)
            return crear_vista_calculo_mecanico(estructura_actual, calculo_guardado)
        
        elif trigger_id == "menu-agregar-cable":
            cables_disponibles = state.cable_manager.obtener_cables()
            from components.vista_gestion_cables import crear_vista_agregar_cable_con_opciones
            return crear_vista_agregar_cable_con_opciones(cables_disponibles)
        
        elif trigger_id == "menu-modificar-cable":
            cables_disponibles = state.cable_manager.obtener_cables()
            return crear_vista_modificar_cable(cables_disponibles)
        
        elif trigger_id == "menu-eliminar-cable":
            cables_disponibles = state.cable_manager.obtener_cables()
            return crear_vista_eliminar_cable(cables_disponibles)
        
        elif trigger_id == "menu-diseno-geometrico":
            guardar_navegacion_state("diseno-geometrico")
            from components.vista_diseno_geometrico import crear_vista_diseno_geometrico
            from utils.calculo_cache import CalculoCache
            calculo_guardado = None
            if estructura_actual:
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                calculo_guardado = CalculoCache.cargar_calculo_dge(nombre_estructura)
            return crear_vista_diseno_geometrico(estructura_actual, calculo_guardado)
        
        elif trigger_id == "menu-diseno-mecanico":
            guardar_navegacion_state("diseno-mecanico")
            from components.vista_diseno_mecanico import crear_vista_diseno_mecanico
            from utils.calculo_cache import CalculoCache
            from utils.hipotesis_manager import HipotesisManager
            from HipotesisMaestro_Especial import hipotesis_maestro as hipotesis_base
            
            if not estructura_actual:
                estructura_actual = state.estructura_manager.cargar_estructura(state.archivo_actual)
            
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            # Cargar hipótesis
            from config.app_config import DATA_DIR
            estructura_json_path = str(DATA_DIR / f"{nombre_estructura}.estructura.json")
            hipotesis_maestro = HipotesisManager.cargar_o_crear_hipotesis(
                nombre_estructura,
                estructura_json_path,
                hipotesis_base
            )
            
            # Cargar cálculo guardado
            calculo_guardado = None
            calculo_guardado = CalculoCache.cargar_calculo_dme(nombre_estructura)
            if calculo_guardado:
                vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
                if not vigente:
                    calculo_guardado = None
            
            return crear_vista_diseno_mecanico(estructura_actual, calculo_guardado, hipotesis_maestro)
        
        elif trigger_id == "menu-arboles-carga":
            guardar_navegacion_state("arboles-carga")
            from components.vista_arboles_carga import crear_vista_arboles_carga
            from utils.calculo_cache import CalculoCache
            calculo_guardado = None
            if estructura_actual:
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                calculo_guardado = CalculoCache.cargar_calculo_arboles(nombre_estructura)
                if calculo_guardado:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
                    if not vigente:
                        calculo_guardado = None
            return crear_vista_arboles_carga(estructura_actual, calculo_guardado)
        
        elif trigger_id == "menu-seleccion-poste":
            guardar_navegacion_state("seleccion-poste")
            from components.vista_seleccion_poste import crear_vista_seleccion_poste
            from utils.calculo_cache import CalculoCache
            calculo_guardado = None
            if estructura_actual:
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                calculo_guardado = CalculoCache.cargar_calculo_sph(nombre_estructura)
                if calculo_guardado:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
                    if not vigente:
                        calculo_guardado = None
            return crear_vista_seleccion_poste(estructura_actual, calculo_guardado)
        
        elif trigger_id == "menu-calcular-todo":
            guardar_navegacion_state("calcular-todo")
            from components.vista_calcular_todo import crear_vista_calcular_todo
            from utils.calculo_cache import CalculoCache
            calculo_guardado = None
            if estructura_actual:
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                calculo_guardado = CalculoCache.cargar_calculo_todo(nombre_estructura)
                if calculo_guardado:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)
                    if not vigente:
                        calculo_guardado = None
            return crear_vista_calcular_todo(estructura_actual, calculo_guardado)
        
        elif "btn-volver" in trigger_id:
            try:
                trigger_json = json.loads(trigger_id.replace("'", '"'))
                if trigger_json.get("type") == "btn-volver":
                    if trigger_json.get("index") == "catenaria":
                        guardar_navegacion_state("home")
                        return crear_vista_home()
                    guardar_navegacion_state("home")
                    return crear_vista_home()
            except:
                pass
    
        return dash.no_update
