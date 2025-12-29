"""
Controller para vista de comparar cables
"""

from dash import Input, Output, State, callback_context, html, dcc
import dash
import dash_bootstrap_components as dbc
from utils.comparar_cables_manager import ComparativaCablesManager
from utils.cable_manager import CableManager
from utils.calculo_cache import CalculoCache
from components.vista_comparar_cables import crear_vista_comparar_cables, _crear_lista_cables
import json
import pandas as pd

def registrar_callbacks_comparar_cables(app):
    """Registrar todos los callbacks de comparar cables"""
    
    # Callback para actualizar lista de cables disponibles
    @app.callback(
        Output("select-cable-agregar", "options"),
        Input("select-cable-agregar", "id")
    )
    def cargar_cables_disponibles(_):
        """Cargar lista de cables disponibles"""
        try:
            # Cargar desde cables_2.json (incluye cables convertidos)
            from config.app_config import DATA_DIR
            cables_path = DATA_DIR / "cables_2.json"
            if cables_path.exists():
                with open(cables_path, 'r', encoding='utf-8') as f:
                    cables_data = json.load(f)
                cables = list(cables_data.keys())
            else:
                # Fallback a cables.json original
                cable_manager = CableManager()
                cables = cable_manager.obtener_lista_cables()
            
            return [{"label": cable, "value": cable} for cable in sorted(cables)]
        except Exception as e:
            print(f"Error cargando cables: {e}")
            return []
    
    # Callback para agregar cable
    @app.callback(
        [Output("lista-cables-seleccionados", "children"),
         Output("select-cable-agregar", "value"),
         Output("store-comparativa-actual", "data", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-agregar-cable", "n_clicks"),
        [State("select-cable-agregar", "value"),
         State("store-comparativa-actual", "data")],
        prevent_initial_call=True
    )
    def agregar_cable(n_clicks, cable_seleccionado, comparativa_actual):
        """Agregar cable a la lista de seleccionados"""
        if not n_clicks or not cable_seleccionado:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # Obtener o crear comparativa
        if not comparativa_actual:
            comparativa_actual = ComparativaCablesManager.crear_comparativa_nueva("Nueva_Comparativa")
        
        cables_actuales = comparativa_actual.get("cables_seleccionados", [])
        
        # Validar que no esté duplicado
        if cable_seleccionado in cables_actuales:
            return (dash.no_update, dash.no_update, dash.no_update,
                   True, "Advertencia", f"El cable '{cable_seleccionado}' ya está seleccionado", "warning")
        
        # Validar límite máximo
        if len(cables_actuales) >= 10:
            return (dash.no_update, dash.no_update, dash.no_update,
                   True, "Advertencia", "Máximo 10 cables permitidos", "warning")
        
        # Agregar cable
        cables_actuales.append(cable_seleccionado)
        comparativa_actual["cables_seleccionados"] = cables_actuales
        
        return (_crear_lista_cables(cables_actuales), None, comparativa_actual,
               True, "Éxito", f"Cable '{cable_seleccionado}' agregado", "success")
    
    # Callback para eliminar cable
    @app.callback(
        [Output("lista-cables-seleccionados", "children", allow_duplicate=True),
         Output("store-comparativa-actual", "data", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input({"type": "btn-eliminar-cable", "index": dash.ALL}, "n_clicks"),
        State("store-comparativa-actual", "data"),
        prevent_initial_call=True
    )
    def eliminar_cable(n_clicks_list, comparativa_actual):
        """Eliminar cable de la lista"""
        if not any(n_clicks_list) or not comparativa_actual:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # Determinar qué botón fue presionado
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # Extraer índice del botón presionado
        trigger_info = ctx.triggered[0]["prop_id"]
        try:
            # Parsear el JSON del trigger para obtener el índice
            import re
            match = re.search(r'"index":(\d+)', trigger_info)
            if match:
                indice = int(match.group(1))
                
                cables_actuales = comparativa_actual.get("cables_seleccionados", [])
                if 0 <= indice < len(cables_actuales):
                    cable_eliminado = cables_actuales.pop(indice)
                    comparativa_actual["cables_seleccionados"] = cables_actuales
                    
                    return (_crear_lista_cables(cables_actuales), comparativa_actual,
                           True, "Éxito", f"Cable '{cable_eliminado}' eliminado", "success")
        except Exception as e:
            print(f"Error eliminando cable: {e}")
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Callback para abrir modal de cargar comparativa
    @app.callback(
        [Output("modal-cargar-comparativa", "is_open"),
         Output("select-comparativa-cargar", "options")],
        Input("btn-cargar-comparativa", "n_clicks"),
        State("modal-cargar-comparativa", "is_open"),
        prevent_initial_call=True
    )
    def abrir_modal_cargar(n_clicks, is_open):
        """Abrir modal para cargar comparativa"""
        if not n_clicks:
            return dash.no_update, dash.no_update
        
        # Obtener lista de comparativas disponibles
        comparativas = ComparativaCablesManager.listar_comparativas()
        opciones = [{"label": comp, "value": comp} for comp in comparativas]
        
        return not is_open, opciones
    
    # Callback para cargar comparativa seleccionada
    @app.callback(
        [Output("store-comparativa-actual", "data", allow_duplicate=True),
         Output("input-titulo-comparativa", "value", allow_duplicate=True),
         Output("modal-cargar-comparativa", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-confirmar-cargar-comp", "n_clicks"),
        State("select-comparativa-cargar", "value"),
        prevent_initial_call=True
    )
    def cargar_comparativa_seleccionada(n_clicks, titulo_seleccionado):
        """Cargar comparativa seleccionada"""
        if not n_clicks or not titulo_seleccionado:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        try:
            comparativa_data = ComparativaCablesManager.cargar_comparativa(titulo_seleccionado)
            if comparativa_data:
                # Guardar en navegación state
                try:
                    from config.app_config import DATA_DIR
                    import json
                    nav_file = DATA_DIR / "navegacion_state.json"
                    nav_data = {"ultima_vista": "comparativa-cmc", "comparativa_actual": titulo_seleccionado}
                    if nav_file.exists():
                        with open(nav_file, 'r', encoding='utf-8') as f:
                            nav_data.update(json.load(f))
                    nav_data["comparativa_actual"] = titulo_seleccionado
                    with open(nav_file, 'w', encoding='utf-8') as f:
                        json.dump(nav_data, f)
                except Exception as e:
                    print(f"Error guardando navegación state: {e}")
                
                return (comparativa_data, titulo_seleccionado, False, 
                       True, "Éxito", f"Comparativa '{titulo_seleccionado}' cargada correctamente", "success")
            else:
                return (dash.no_update, dash.no_update, dash.no_update,
                       True, "Error", f"No se pudo cargar la comparativa '{titulo_seleccionado}'", "danger")
        except Exception as e:
            return (dash.no_update, dash.no_update, dash.no_update,
                   True, "Error", f"Error cargando comparativa: {str(e)}", "danger")
    
    # Callback para nueva comparativa
    @app.callback(
        [Output("store-comparativa-actual", "data", allow_duplicate=True),
         Output("input-titulo-comparativa", "value", allow_duplicate=True)],
        Input("btn-nueva-comparativa", "n_clicks"),
        prevent_initial_call=True
    )
    def nueva_comparativa(n_clicks):
        """Crear nueva comparativa"""
        if not n_clicks:
            return dash.no_update, dash.no_update
        
        nueva_comp = ComparativaCablesManager.crear_comparativa_nueva("Nueva_Comparativa")
        return nueva_comp, "Nueva_Comparativa"
    
    # Callback para actualizar lista de cables cuando cambia el estado
    @app.callback(
        Output("lista-cables-seleccionados", "children", allow_duplicate=True),
        Input("store-comparativa-actual", "data"),
        prevent_initial_call=True
    )
    def actualizar_lista_cables_desde_estado(comparativa_actual):
        """Actualizar lista visual de cables desde el estado"""
        if not comparativa_actual:
            return _crear_lista_cables([])
        
        cables_seleccionados = comparativa_actual.get("cables_seleccionados", [])
        return _crear_lista_cables(cables_seleccionados)
    
    # Callback para actualizar tabla de estados climáticos
    @app.callback(
        Output("tabla-estados-climaticos", "children"),
        Input("store-comparativa-actual", "data"),
        prevent_initial_call=False
    )
    def actualizar_tabla_estados(comparativa_actual):
        """Actualizar tabla de estados climáticos desde el estado"""
        from components.vista_comparar_cables import _crear_tabla_estados_climaticos
        
        if not comparativa_actual:
            # Crear estados por defecto si no hay comparativa
            estados_default = {
                "I": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, "hielo_espesor": 0, "restriccion_conductor": 0.25, "restriccion_guardia": 0.7},
                "II": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0, "hielo_espesor": 0, "restriccion_conductor": 0.4, "restriccion_guardia": 0.7},
                "III": {"temperatura": 10, "descripcion": "Vmáx", "viento_velocidad": 38.9, "hielo_espesor": 0, "restriccion_conductor": 0.4, "restriccion_guardia": 0.7},
                "IV": {"temperatura": -5, "descripcion": "Vmed", "viento_velocidad": 15.56, "hielo_espesor": 0.01, "restriccion_conductor": 0.4, "restriccion_guardia": 0.7},
                "V": {"temperatura": 8, "descripcion": "TMA", "viento_velocidad": 0, "hielo_espesor": 0, "restriccion_conductor": 0.25, "restriccion_guardia": 0.7}
            }
            return _crear_tabla_estados_climaticos(estados_default)
        
        estados = comparativa_actual.get("estados_climaticos", {})
        return _crear_tabla_estados_climaticos(estados)
    
    # Callback para actualizar estados climáticos editados
    @app.callback(
        Output("store-comparativa-actual", "data", allow_duplicate=True),
        [Input({"type": "temp-estado", "index": dash.ALL}, "value"),
         Input({"type": "desc-estado", "index": dash.ALL}, "value"),
         Input({"type": "viento-estado", "index": dash.ALL}, "value"),
         Input({"type": "hielo-estado", "index": dash.ALL}, "value"),
         Input({"type": "rest-cond-estado", "index": dash.ALL}, "value"),
         Input({"type": "rest-guard-estado", "index": dash.ALL}, "value")],
        State("store-comparativa-actual", "data"),
        prevent_initial_call=True
    )
    def actualizar_estados_climaticos(temps, descs, vientos, hielos, rest_conds, rest_guards, comparativa_actual):
        """Actualizar estados climáticos editados"""
        if not comparativa_actual or not any([temps, descs, vientos, hielos, rest_conds, rest_guards]):
            return dash.no_update
        
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update
        
        # Obtener estados actuales
        estados = comparativa_actual.get("estados_climaticos", {})
        estados_ids = list(estados.keys())
        
        # Actualizar valores según el trigger
        trigger_info = ctx.triggered[0]["prop_id"]
        if "temp-estado" in trigger_info and temps:
            for i, temp in enumerate(temps):
                if i < len(estados_ids) and temp is not None:
                    estados[estados_ids[i]]["temperatura"] = temp
        elif "desc-estado" in trigger_info and descs:
            for i, desc in enumerate(descs):
                if i < len(estados_ids) and desc is not None:
                    estados[estados_ids[i]]["descripcion"] = desc
        elif "viento-estado" in trigger_info and vientos:
            for i, viento in enumerate(vientos):
                if i < len(estados_ids) and viento is not None:
                    estados[estados_ids[i]]["viento_velocidad"] = viento
        elif "hielo-estado" in trigger_info and hielos:
            for i, hielo in enumerate(hielos):
                if i < len(estados_ids) and hielo is not None:
                    estados[estados_ids[i]]["hielo_espesor"] = hielo
        elif "rest-cond-estado" in trigger_info and rest_conds:
            for i, rest in enumerate(rest_conds):
                if i < len(estados_ids) and rest is not None:
                    estados[estados_ids[i]]["restriccion_conductor"] = rest
        elif "rest-guard-estado" in trigger_info and rest_guards:
            for i, rest in enumerate(rest_guards):
                if i < len(estados_ids) and rest is not None:
                    estados[estados_ids[i]]["restriccion_guardia"] = rest
        
        comparativa_actual["estados_climaticos"] = estados
        return comparativa_actual
    
    # Callback para actualizar parámetros en el estado
    @app.callback(
        Output("store-comparativa-actual", "data", allow_duplicate=True),
        [Input("slider-vano-comparativa", "value"),
         Input("select-theta-comparativa", "value"),
         Input("input-vmax-comparativa", "value"),
         Input("input-vmed-comparativa", "value"),
         Input("select-hielo-comparativa", "value"),
         Input("switch-vano-desnivelado", "value"),
         Input("select-objetivo-conductor", "value"),
         Input("select-salto-porcentual", "value"),
         Input("select-paso-afinado", "value"),
         Input("input-h-piq-anterior", "value"),
         Input("input-h-piq-posterior", "value"),
         Input("select-exposicion-comparativa", "value"),
         Input("select-clase-comparativa", "value"),
         Input("input-zco-comparativa", "value"),
         Input("input-cf-cable-comparativa", "value")],
        State("store-comparativa-actual", "data"),
        prevent_initial_call=True
    )
    def actualizar_parametros(vano, theta, vmax, vmed, hielo, vano_desnivelado, 
                             objetivo, salto, paso, h_anterior, h_posterior, 
                             exposicion, clase, zco, cf_cable, comparativa_actual):
        """Actualizar parámetros en el estado de la comparativa"""
        if not comparativa_actual:
            comparativa_actual = ComparativaCablesManager.crear_comparativa_nueva("Nueva_Comparativa")
        
        # Actualizar parámetros de línea
        comparativa_actual["parametros_linea"].update({
            "L_vano": vano or 150,
            "theta": theta if theta is not None else 0,
            "Vmax": vmax or 38.9,
            "Vmed": vmed or 15.56,
            "t_hielo": hielo if hielo is not None else 0,
            "exposicion": exposicion or "C",
            "clase": clase or "C",
            "Zco": zco if zco is not None else 13.0,
            "Cf_cable": cf_cable if cf_cable is not None else 1.0
        })
        
        # Actualizar configuración de cálculo
        comparativa_actual["configuracion_calculo"].update({
            "VANO_DESNIVELADO": vano_desnivelado if vano_desnivelado is not None else True,
            "OBJ_CONDUCTOR": objetivo or "FlechaMin",
            "SALTO_PORCENTUAL": salto if salto is not None else 0.05,
            "PASO_AFINADO": paso if paso is not None else 0.01,
            "H_PIQANTERIOR": h_anterior if h_anterior is not None else 0,
            "H_PIQPOSTERIOR": h_posterior if h_posterior is not None else 0
        })
        
        return comparativa_actual
    
    # Callback para mostrar/ocultar controles de desnivel
    @app.callback(
        Output("controles-desnivel", "style"),
        Input("switch-vano-desnivelado", "value"),
        prevent_initial_call=True
    )
    def toggle_controles_desnivel(vano_desnivelado):
        """Mostrar/ocultar controles de desnivel según switch"""
        if vano_desnivelado:
            return {"display": "block"}
        else:
            return {"display": "none"}
    
    # Callback para cargar cache
    @app.callback(
        [Output("store-comparativa-actual", "data", allow_duplicate=True),
         Output("resultados-comparativa", "children", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-cargar-cache-comparativa", "n_clicks"),
        State("store-comparativa-actual", "data"),
        prevent_initial_call=True
    )
    def cargar_cache_comparativa(n_clicks, comparativa_actual):
        """Cargar resultados desde cache"""
        if not n_clicks or not comparativa_actual:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        titulo = comparativa_actual.get("titulo", "Sin_Titulo")
        
        try:
            # Intentar cargar cache
            cache_data = CalculoCache.cargar_calculo_comparar_cmc(titulo)
            
            if cache_data:
                # Verificar vigencia
                hash_actual = ComparativaCablesManager.calcular_hash_parametros(comparativa_actual)
                hash_cache = cache_data.get("hash_parametros")
                
                # Mostrar resultados independientemente de vigencia (como CMC)
                from components.vista_comparar_cables import generar_resultados_desde_cache
                resultado_html = generar_resultados_desde_cache(cache_data)
                
                if hash_actual == hash_cache:
                    return (comparativa_actual, resultado_html,
                           True, "Éxito", f"Cache cargado para '{titulo}' (vigente)", "success")
                else:
                    return (comparativa_actual, resultado_html,
                           True, "Advertencia", f"Cache cargado para '{titulo}' (parámetros modificados)", "warning")
            else:
                # No existe cache
                return (dash.no_update, dash.no_update,
                       True, "Info", f"No hay cache disponible para '{titulo}'. Ejecute cálculo primero.", "info")
                
        except Exception as e:
            return (dash.no_update, dash.no_update,
                   True, "Error", f"Error cargando cache: {str(e)}", "danger")
    
    # Callback para guardar comparativa
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-guardar-comparativa", "n_clicks"),
        [State("input-titulo-comparativa", "value"),
         State("store-comparativa-actual", "data")],
        prevent_initial_call=True
    )
    def guardar_comparativa(n_clicks, titulo, comparativa_actual):
        """Guardar comparativa actual"""
        if not n_clicks:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # Validar título
        valido, mensaje = ComparativaCablesManager.validar_titulo(titulo)
        if not valido:
            return True, "Error", mensaje, "danger"
        
        try:
            # Usar datos actuales o crear nueva si no existe
            if comparativa_actual:
                comparativa_actual["titulo"] = titulo
                # Actualizar fecha de modificación
                from datetime import datetime
                comparativa_actual["fecha_modificacion"] = datetime.now().isoformat()
                comparativa_data = comparativa_actual
            else:
                comparativa_data = ComparativaCablesManager.crear_comparativa_nueva(titulo)
            
            ruta_guardada = ComparativaCablesManager.guardar_comparativa(comparativa_data)
            
            # Guardar título en navegación state para persistencia
            try:
                from config.app_config import DATA_DIR
                import json
                nav_file = DATA_DIR / "navegacion_state.json"
                nav_data = {"ultima_vista": "comparativa-cmc", "comparativa_actual": titulo}
                if nav_file.exists():
                    with open(nav_file, 'r', encoding='utf-8') as f:
                        nav_data.update(json.load(f))
                nav_data["comparativa_actual"] = titulo
                with open(nav_file, 'w', encoding='utf-8') as f:
                    json.dump(nav_data, f)
            except Exception as e:
                print(f"Error guardando navegación state: {e}")
            
            return True, "Éxito", f"Comparativa guardada: {titulo}", "success"
        except Exception as e:
            return True, "Error", f"Error guardando comparativa: {str(e)}", "danger"
    
    # Callback para calcular comparativa
    @app.callback(
        [Output("resultados-comparativa", "children"),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-calcular-comparativa", "n_clicks"),
        State("store-comparativa-actual", "data"),
        prevent_initial_call=True
    )
    def calcular_comparativa(n_clicks, comparativa_actual):
        """Ejecutar cálculo de comparativa"""
        if not n_clicks or not comparativa_actual:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        try:
            # Extraer datos de la comparativa
            titulo = comparativa_actual.get("titulo", "Sin_Titulo")
            cables_seleccionados = comparativa_actual.get("cables_seleccionados", [])
            
            # Validar que hay cables seleccionados
            if not cables_seleccionados:
                return (dbc.Alert("Debe seleccionar al menos un cable para calcular", color="warning"),
                       dash.no_update, dash.no_update, dash.no_update, dash.no_update)
            
            # Ejecutar cálculo real
            from utils.comparativa_cmc_calculo import ejecutar_comparativa_cmc, crear_grafico_comparativo
            
            print(f"🔄 Iniciando cálculo comparativo para {len(cables_seleccionados)} cables...")
            resultados = ejecutar_comparativa_cmc(comparativa_actual)
            print(f"📊 Resultados obtenidos: {list(resultados.keys())}")
            
            # Crear tabs con resultados por cable
            tabs = []
            print(f"📋 Creando tabs para {len(resultados)} cables...")
            
            # Tab comparativo primero
            try:
                from utils.comparativa_cmc_calculo import crear_grafico_comparativo
                fig_flechas, fig_tiros = crear_grafico_comparativo(resultados)
                tab_comparativo = dbc.Tab(
                    label="Comparativo", 
                    tab_id="tab-comparativo",
                    children=[
                        html.H6("Comparativa de Flechas", className="mt-3"),
                        dcc.Graph(figure=fig_flechas, config={'displayModeBar': True}),
                        html.H6("Comparativa de Tiros", className="mt-4"),
                        dcc.Graph(figure=fig_tiros, config={'displayModeBar': True})
                    ]
                )
                tabs.append(tab_comparativo)
            except Exception as e:
                print(f"Error creando gráficos comparativos: {e}")
                tab_comparativo = dbc.Tab(
                    label="Comparativo",
                    tab_id="tab-comparativo", 
                    children=[dbc.Alert("Error generando gráficos comparativos", color="warning")]
                )
                tabs.append(tab_comparativo)
            
            # Tabs por cable
            cables_exitosos = 0
            for cable_nombre, resultado in resultados.items():
                if "error" in resultado:
                    tab_content = dbc.Alert(f"Error: {resultado['error']}", color="danger")
                else:
                    cables_exitosos += 1
                    # Crear tabla de resultados completa
                    try:
                        if resultado.get('dataframe_html'):
                            df_data = json.loads(resultado['dataframe_html'])
                            df = pd.DataFrame(df_data['data'], columns=df_data['columns'])
                            tabla = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, size="sm")
                        else:
                            tabla = html.P("No hay datos de tabla")
                    except Exception as e:
                        print(f"Error generando tabla para {cable_nombre}: {e}")
                        tabla = html.P(f"Error generando tabla: {e}")
                    
                    # Crear gráficos de flechas
                    graficos = []
                    if 'graficos' in resultado and resultado['graficos']:
                        for nombre_grafico, fig_data in resultado['graficos'].items():
                            try:
                                if fig_data is not None:
                                    grafico = dcc.Graph(figure=fig_data, config={'displayModeBar': True})
                                    graficos.append(html.H6(nombre_grafico, className="mt-3"))
                                    graficos.append(grafico)
                            except Exception as e:
                                print(f"Error creando gráfico {nombre_grafico}: {e}")
                    
                    convergencia_msg = "Convergencia: Sí" if resultado.get('convergencia') else "Convergencia: No"
                    tiempo_calculo = resultado.get('tiempo_calculo', 0)
                    tiempo_msg = f"Tiempo: {tiempo_calculo:.1f}s" if tiempo_calculo is not None else "Tiempo: N/A"
                    
                    tab_content = html.Div([
                        dbc.Alert(f"{convergencia_msg} - {tiempo_msg}", 
                                 color="success" if resultado.get('convergencia') else "warning"),
                        html.H6("Resultados por Estado Climático:"),
                        tabla
                    ] + graficos)
                
                tab = dbc.Tab(label=cable_nombre[:20], tab_id=f"tab-{cable_nombre}", children=tab_content)
                tabs.append(tab)
            
            # Guardar cache automáticamente
            print(f"💾 Guardando cache para '{titulo}'...")
            try:
                CalculoCache.guardar_calculo_comparar_cmc(
                    titulo, comparativa_actual, resultados
                )
                print(f"✅ Cache guardado automáticamente para '{titulo}'")
            except Exception as e:
                print(f"⚠️ Error guardando cache: {e}")
            
            resultado_html = html.Div([
                dbc.Alert(f"Cálculo completado: {cables_exitosos} de {len(cables_seleccionados)} cables exitosos", 
                         color="success" if cables_exitosos > 0 else "warning"),
                dbc.Tabs(tabs, active_tab="tab-comparativo")
            ])
            
            print(f"🏁 Retornando resultados: {cables_exitosos}/{len(cables_seleccionados)} cables exitosos")
            return (resultado_html, True, "Éxito", 
                   f"Cálculo completado: {cables_exitosos or 0}/{len(cables_seleccionados) or 0} cables", "success")
            
        except Exception as e:
            print(f"Error en cálculo: {e}")
            import traceback
            print(traceback.format_exc())
            return (dbc.Alert(f"Error en cálculo: {str(e)}", color="danger"),
                   True, "Error", f"Error en cálculo: {str(e)}", "danger")
    # Callback para descargar HTML
    @app.callback(
        Output("download-html-comparativa", "data"),
        Input("btn-descargar-html-comparativa", "n_clicks"),
        State("store-comparativa-actual", "data"),
        State("resultados-comparativa", "children"),
        prevent_initial_call=True
    )
    def descargar_html_comparativa(n_clicks, comparativa_actual, resultados_html):
        """Descargar resultados como HTML"""
        if not n_clicks or not comparativa_actual:
            return dash.no_update
        
        try:
            from utils.descargar_html import generar_html_comparativa
            titulo = comparativa_actual.get("titulo", "Comparativa")
            html_content = generar_html_comparativa(titulo, comparativa_actual, resultados_html)
            
            return dict(content=html_content, filename=f"{titulo}_comparativa.html")
        except Exception as e:
            print(f"Error generando HTML: {e}")
            return dash.no_update