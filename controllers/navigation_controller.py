"""Controlador de navegación"""

import dash
from dash import Input, Output, State, ALL, callback_context
import json
from pathlib import Path
from components.vista_home import crear_vista_home
from components.vista_ajuste_parametros import crear_vista_ajuste_parametros_con_pestanas
from components.vista_eliminar_estructura import crear_vista_eliminar_estructura
from components.vista_calculo_mecanico import crear_vista_calculo_mecanico
from views.vista_editor_hipotesis import crear_vista_editor_hipotesis
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
    
    # Callback para sincronizar AppState con Dash Store
    @app.callback(
        Output("badge-estructura-actual", "children"),
        Input("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def sincronizar_estructura_actual(estructura_data):
        """Sincronizar AppState cuando cambia el Store de Dash"""
        if estructura_data:
            state.set_estructura_actual(estructura_data)
            titulo = estructura_data.get('TITULO', 'Sin título')
            return f"Estructura: {titulo}"
        return "Sin estructura"
    
    # Badge para familia actual
    @app.callback(
        Output("badge-familia-actual", "children"),
        [Input("contenido-principal", "children"),
         Input("familia-actual-state", "data")],
        prevent_initial_call=False
    )
    def actualizar_badge_familia(contenido, familia_state_data):
        """Actualizar badge de familia desde AppState"""
        try:
            # Obtener familia activa desde AppState
            familia_activa = state.get_familia_activa()
            if familia_activa:
                return f"Familia: {familia_activa.replace('_', ' ')}"
            return "Sin familia"
        except:
            return "Sin familia"
    
    @app.callback(
        Output("contenido-principal", "children"),
        Input("btn-inicio", "n_clicks"),
        Input({"type": "btn-volver", "index": ALL}, "n_clicks"),
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
        Input("menu-fundacion", "n_clicks"),
        Input("menu-costeo", "n_clicks"),
        Input("menu-calcular-todo", "n_clicks"),
        Input("menu-consola", "n_clicks"),
        Input("menu-comparativa-cmc", "n_clicks"),
        Input("menu-familia-estructuras", "n_clicks"),
        Input("menu-vano-economico", "n_clicks"),
        Input("menu-analisis-estatico", "n_clicks"),
        Input("menu-editor-hipotesis", "n_clicks"),
        State("estructura-actual", "data"),
    )
    def navegar_vistas(n_clicks_inicio, btn_volver_clicks, n_clicks_ajustar, 
                       n_clicks_eliminar, n_clicks_cmc,
                       n_clicks_agregar_cable, n_clicks_modificar_cable, n_clicks_eliminar_cable,
                       n_clicks_diseno_geom, n_clicks_diseno_mec, n_clicks_arboles, n_clicks_sph, 
                       n_clicks_fundacion, n_clicks_costeo, n_clicks_calcular_todo, n_clicks_consola, 
                       n_clicks_comparativa_cmc, n_clicks_familia, n_clicks_vano_economico, 
                       n_clicks_aee, n_clicks_editor_hip, estructura_actual):
        ctx = callback_context
        
        # Detectar carga inicial (app restart o hot reload)
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
        es_carga_inicial = not ctx.triggered
        
        if es_carga_inicial:
            ultima_vista = cargar_navegacion_state()
            print(f"DEBUG: Carga inicial detectada, restaurando vista: {ultima_vista}")
            if ultima_vista == "calculo-mecanico":
                from utils.calculo_cache import CalculoCache
                from config.app_config import DATA_DIR
                
                # Recargar estructura desde archivo para tener datos actualizados
                if estructura_actual:
                    titulo = estructura_actual.get('TITULO', 'estructura')
                    ruta_estructura = DATA_DIR / f"{titulo}.estructura.json"
                    try:
                        estructura_actual = state.estructura_manager.cargar_estructura(ruta_estructura)
                        print(f"✅ (F5) Estructura recargada desde archivo: {titulo}")
                    except Exception as e:
                        print(f"⚠️ (F5) Error recargando estructura: {e}")
                
                calculo_guardado = None
                if estructura_actual:
                    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                    calculo_guardado = CalculoCache.cargar_calculo_cmc(nombre_estructura)
                return crear_vista_calculo_mecanico(estructura_actual, calculo_guardado)
            elif ultima_vista == "ajustar-parametros":
                from config.app_config import DATA_DIR
                # Recargar estructura desde archivo
                if estructura_actual:
                    titulo = estructura_actual.get('TITULO', 'estructura')
                    ruta_estructura = DATA_DIR / f"{titulo}.estructura.json"
                    try:
                        estructura_actual = state.estructura_manager.cargar_estructura(ruta_estructura)
                    except:
                        pass
                cables_disponibles = state.cable_manager.obtener_cables()
                return crear_vista_ajuste_parametros_con_pestanas(estructura_actual, cables_disponibles)
            elif ultima_vista == "diseno-geometrico":
                from components.vista_diseno_geometrico import crear_vista_diseno_geometrico
                return crear_vista_diseno_geometrico(estructura_actual, None)
            elif ultima_vista == "diseno-mecanico":
                from components.vista_diseno_mecanico import crear_vista_diseno_mecanico
                from utils.calculo_cache import CalculoCache
                from utils.hipotesis_manager import HipotesisManager

                # Cargar la hipótesis activa. Si no existe, usar la plantilla.
                datos_hipotesis = HipotesisManager.cargar_hipotesis_activa()
                hipotesis_maestro = {}
                if datos_hipotesis:
                    print(f"✅ (NAV) Usando hipótesis activa: {HipotesisManager.obtener_hipotesis_activa()}")
                    hipotesis_maestro = datos_hipotesis.get('hipotesis_maestro', datos_hipotesis)
                else:
                    print("⚠️ (NAV) Hipótesis activa no encontrada. Usando plantilla.")
                    plantilla_path = "data/hipotesis/plantilla.hipotesis.json"
                    try:
                        import json
                        with open(plantilla_path, 'r', encoding='utf-8') as f:
                            datos_plantilla = json.load(f)
                        hipotesis_maestro = datos_plantilla.get('hipotesis_maestro', datos_plantilla)
                    except FileNotFoundError:
                        print(f"❌ (NAV) ERROR: No se encontró el archivo de plantilla en {plantilla_path}.")
                        hipotesis_maestro = {}

                if not hipotesis_maestro:
                    print("❌ (NAV) ERROR FATAL: No se pudo cargar ninguna hipótesis.")
                    # Aquí se podría retornar una vista de error
                
                calculo_guardado = None
                if estructura_actual:
                    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
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
                return crear_vista_arboles_carga(estructura_actual, None)
            elif ultima_vista == "fundacion":
                from components.vista_fundacion import crear_vista_fundacion
                return crear_vista_fundacion(estructura_actual, None)
            elif ultima_vista == "costeo":
                from components.vista_costeo import crear_vista_costeo
                return crear_vista_costeo(estructura_actual, None)
            elif ultima_vista == "calcular-todo":
                from components.vista_calcular_todo import crear_vista_calcular_todo
                return crear_vista_calcular_todo(estructura_actual, None)
            elif ultima_vista == "consola":
                from components.vista_consola import crear_vista_consola
                return crear_vista_consola()
            elif ultima_vista == "comparativa-cmc":
                from components.vista_comparar_cables import crear_vista_comparar_cables
                # Intentar cargar comparativa actual desde navegación state
                try:
                    from config.app_config import DATA_DIR
                    import json
                    nav_file = DATA_DIR / "navegacion_state.json"
                    comparativa_actual = None
                    if nav_file.exists():
                        with open(nav_file, 'r', encoding='utf-8') as f:
                            nav_data = json.load(f)
                            comparativa_titulo = nav_data.get("comparativa_actual")
                            if comparativa_titulo:
                                from utils.comparar_cables_manager import ComparativaCablesManager
                                comparativa_actual = ComparativaCablesManager.cargar_comparativa(comparativa_titulo)
                    return crear_vista_comparar_cables(comparativa_actual)
                except Exception as e:
                    print(f"Error cargando comparativa: {e}")
                    return crear_vista_comparar_cables(None)
            elif ultima_vista == "familia-estructuras":
                from components.vista_familia_estructuras import crear_vista_familia_estructuras
                familia_actual = state.cargar_familia_activa()
                return crear_vista_familia_estructuras(familia_actual)
            elif ultima_vista == "vano-economico":
                from components.vista_vano_economico import crear_vista_vano_economico
                return crear_vista_vano_economico()
            elif ultima_vista == "analisis-estatico":
                from components.vista_analisis_estatico import crear_vista_analisis_estatico
                from utils.calculo_cache import CalculoCache
                calculo_guardado = None
                if estructura_actual:
                    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                    calculo_guardado = CalculoCache.cargar_calculo_aee(nombre_estructura)
                return crear_vista_analisis_estatico(estructura_actual, calculo_guardado)
            return crear_vista_home()
        
        print(f"DEBUG: Trigger detectado: {trigger_id}")
        
        if trigger_id == "btn-inicio":
            guardar_navegacion_state("home")
            return crear_vista_home()
        
        elif trigger_id == "menu-ajustar-parametros":
            guardar_navegacion_state("ajustar-parametros")
            from config.app_config import DATA_DIR
            # Recargar estructura desde archivo
            if estructura_actual:
                titulo = estructura_actual.get('TITULO', 'estructura')
                ruta_estructura = DATA_DIR / f"{titulo}.estructura.json"
                try:
                    estructura_actual = state.estructura_manager.cargar_estructura(ruta_estructura)
                except:
                    pass
            cables_disponibles = state.cable_manager.obtener_cables()
            return crear_vista_ajuste_parametros_con_pestanas(estructura_actual, cables_disponibles)
        
        elif trigger_id == "menu-eliminar-estructura":
            return crear_vista_eliminar_estructura()
        
        elif trigger_id == "menu-calculo-mecanico":
            guardar_navegacion_state("calculo-mecanico")
            from utils.calculo_cache import CalculoCache
            from config.app_config import DATA_DIR
            
            # Recargar estructura desde archivo para tener datos actualizados
            if estructura_actual:
                titulo = estructura_actual.get('TITULO', 'estructura')
                ruta_estructura = DATA_DIR / f"{titulo}.estructura.json"
                try:
                    estructura_actual = state.estructura_manager.cargar_estructura(ruta_estructura)
                    print(f"✅ Estructura recargada desde archivo: {titulo}")
                except Exception as e:
                    print(f"⚠️ Error recargando estructura: {e}")
            
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
            return crear_vista_diseno_geometrico(estructura_actual, None)
        
        elif trigger_id == "menu-diseno-mecanico":
            guardar_navegacion_state("diseno-mecanico")
            from components.vista_diseno_mecanico import crear_vista_diseno_mecanico
            from utils.calculo_cache import CalculoCache
            from utils.hipotesis_manager import HipotesisManager

            if not estructura_actual:
                estructura_actual = state.estructura_manager.cargar_estructura(state.get_estructura_actual_path())

            nombre_estructura = estructura_actual.get('TITULO', 'estructura')

            # Cargar la hipótesis activa. Si no existe, usar la plantilla.
            datos_hipotesis = HipotesisManager.cargar_hipotesis_activa()
            hipotesis_maestro = {}
            if datos_hipotesis:
                print(f"✅ (NAV) Usando hipótesis activa: {HipotesisManager.obtener_hipotesis_activa()}")
                hipotesis_maestro = datos_hipotesis.get('hipotesis_maestro', datos_hipotesis)
            else:
                print("⚠️ (NAV) Hipótesis activa no encontrada. Usando plantilla.")
                plantilla_path = "data/hipotesis/plantilla.hipotesis.json"
                try:
                    import json
                    with open(plantilla_path, 'r', encoding='utf-8') as f:
                        datos_plantilla = json.load(f)
                    hipotesis_maestro = datos_plantilla.get('hipotesis_maestro', datos_plantilla)
                except FileNotFoundError:
                    print(f"❌ (NAV) ERROR: No se encontró el archivo de plantilla en {plantilla_path}.")
                    hipotesis_maestro = {}
            
            if not hipotesis_maestro:
                print("❌ (NAV) ERROR FATAL: No se pudo cargar ninguna hipótesis.")
                # Aquí se podría retornar una vista de error
            
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
            return crear_vista_arboles_carga(estructura_actual, None)
        
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
        
        elif trigger_id == "menu-fundacion":
            guardar_navegacion_state("fundacion")
            from components.vista_fundacion import crear_vista_fundacion
            return crear_vista_fundacion(estructura_actual, None)
        
        elif trigger_id == "menu-costeo":
            guardar_navegacion_state("costeo")
            from components.vista_costeo import crear_vista_costeo
            return crear_vista_costeo(estructura_actual, None)
        
        elif trigger_id == "menu-calcular-todo":
            guardar_navegacion_state("calcular-todo")
            from components.vista_calcular_todo import crear_vista_calcular_todo
            return crear_vista_calcular_todo(estructura_actual, None)
        
        elif trigger_id == "menu-consola":
            guardar_navegacion_state("consola")
            from components.vista_consola import crear_vista_consola
            return crear_vista_consola()
        
        elif trigger_id == "menu-comparativa-cmc":
            guardar_navegacion_state("comparativa-cmc")
            from components.vista_comparar_cables import crear_vista_comparar_cables
            # Intentar cargar comparativa actual desde navegación state
            try:
                from config.app_config import DATA_DIR
                import json
                nav_file = DATA_DIR / "navegacion_state.json"
                comparativa_actual = None
                if nav_file.exists():
                    with open(nav_file, 'r', encoding='utf-8') as f:
                        nav_data = json.load(f)
                        comparativa_titulo = nav_data.get("comparativa_actual")
                        if comparativa_titulo:
                            from utils.comparar_cables_manager import ComparativaCablesManager
                            comparativa_actual = ComparativaCablesManager.cargar_comparativa(comparativa_titulo)
                return crear_vista_comparar_cables(comparativa_actual)
            except Exception as e:
                print(f"Error cargando comparativa: {e}")
                return crear_vista_comparar_cables(None)
        
        elif trigger_id == "menu-familia-estructuras":
            guardar_navegacion_state("familia-estructuras")
            from components.vista_familia_estructuras import crear_vista_familia_estructuras
            familia_actual = state.cargar_familia_activa()
            return crear_vista_familia_estructuras(familia_actual)
        
        elif trigger_id == "menu-vano-economico":
            guardar_navegacion_state("vano-economico")
            from components.vista_vano_economico import crear_vista_vano_economico
            return crear_vista_vano_economico()
        
        elif trigger_id == "menu-analisis-estatico":
            guardar_navegacion_state("analisis-estatico")
            from components.vista_analisis_estatico import crear_vista_analisis_estatico
            from utils.calculo_cache import CalculoCache
            calculo_guardado = None
            if estructura_actual:
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                calculo_guardado = CalculoCache.cargar_calculo_aee(nombre_estructura)
            return crear_vista_analisis_estatico(estructura_actual, calculo_guardado)
        
        elif trigger_id == "menu-editor-hipotesis":
            guardar_navegacion_state("editor-hipotesis")
            return crear_vista_editor_hipotesis()
        
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
