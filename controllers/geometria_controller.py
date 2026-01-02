"""Controlador de diseño geométrico"""

import dash
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState


def aplicar_nodos_editados(estructura_geometria, nodos_editados_list, lib_cables=None):
    """Aplica nodos editados después del dimensionamiento automático"""
    if not nodos_editados_list:
        return
    
    print(f"\n🔧 APLICANDO {len(nodos_editados_list)} NODOS EDITADOS...")
    
    # Importar nodos editados
    estructura_geometria.importar_nodos_editados(nodos_editados_list, lib_cables)
    
    print(f"✅ Nodos editados aplicados: {len(nodos_editados_list)} nodos")


def ejecutar_calculo_dge(estructura_actual, state):
    """Ejecuta cálculo DGE y retorna resultados para mostrar"""
    try:
        from EstructuraAEA_Geometria import EstructuraAEA_Geometria
        from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
        from EstructuraAEA_Graficos import EstructuraAEA_Graficos
        from HipotesisMaestro_Especial import hipotesis_maestro
        from utils.calculo_cache import CalculoCache
        from utils.memoria_calculo_dge import gen_memoria_calculo_DGE
        import matplotlib.pyplot as plt
        
        # Obtener flechas máximas
        fmax_conductor = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_conductor.values()])
        fmax_guardia1 = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia1.values()])
        if state.calculo_mecanico.resultados_guardia2:
            fmax_guardia2 = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia2.values()])
            fmax_guardia = max(fmax_guardia1, fmax_guardia2)
        else:
            fmax_guardia = fmax_guardia1
        
        # Crear estructura de geometría
        estructura_geometria = EstructuraAEA_Geometria(
            tipo_estructura=estructura_actual.get("TIPO_ESTRUCTURA"),
            tension_nominal=estructura_actual.get("TENSION"),
            zona_estructura=estructura_actual.get("Zona_estructura"),
            disposicion=estructura_actual.get("DISPOSICION"),
            terna=estructura_actual.get("TERNA"),
            cant_hg=estructura_actual.get("CANT_HG"),
            alpha_quiebre=estructura_actual.get("alpha"),
            altura_minima_cable=estructura_actual.get("ALTURA_MINIMA_CABLE"),
            long_mensula_min_conductor=estructura_actual.get("LONGITUD_MENSULA_MINIMA_CONDUCTOR"),
            long_mensula_min_guardia=estructura_actual.get("LONGITUD_MENSULA_MINIMA_GUARDIA"),
            hadd=estructura_actual.get("HADD"),
            hadd_entre_amarres=estructura_actual.get("HADD_ENTRE_AMARRES"),
            lk=estructura_actual.get("Lk"),
            ancho_cruceta=estructura_actual.get("ANCHO_CRUCETA"),
            cable_conductor=state.calculo_objetos.cable_conductor,
            cable_guardia=state.calculo_objetos.cable_guardia,
            peso_estructura=estructura_actual.get("PESTRUCTURA"),
            peso_cadena=estructura_actual.get("PCADENA"),
            hg_centrado=estructura_actual.get("HG_CENTRADO"),
            ang_apantallamiento=estructura_actual.get("ANG_APANTALLAMIENTO"),
            hadd_hg=estructura_actual.get("HADD_HG"),
            hadd_lmen=estructura_actual.get("HADD_LMEN"),
            dist_reposicionar_hg=estructura_actual.get("DIST_REPOSICIONAR_HG"),
            ajustar_por_altura_msnm=estructura_actual.get("AJUSTAR_POR_ALTURA_MSNM"),
            metodo_altura_msnm=estructura_actual.get("METODO_ALTURA_MSNM"),
            altura_msnm=estructura_actual.get("Altura_MSNM")
        )
        
        estructura_geometria.dimensionar_unifilar(
            estructura_actual.get("L_vano"),
            fmax_conductor,
            fmax_guardia,
            dist_reposicionar_hg=estructura_actual.get("DIST_REPOSICIONAR_HG"),
            autoajustar_lmenhg=estructura_actual.get("AUTOAJUSTAR_LMENHG")
        )
        
        # Aplicar nodos editados si existen
        nodos_editados = estructura_actual.get("nodos_editados", [])
        if nodos_editados:
            # Crear lib_cables temporal para resolver referencias
            from CalculoCables import LibCables
            lib_cables = LibCables()
            lib_cables.agregar_cable(state.calculo_objetos.cable_conductor)
            lib_cables.agregar_cable(state.calculo_objetos.cable_guardia)
            if state.calculo_objetos.cable_guardia2:
                lib_cables.agregar_cable(state.calculo_objetos.cable_guardia2)
            
            aplicar_nodos_editados(estructura_geometria, nodos_editados, lib_cables)
        
        state.calculo_objetos.estructura_geometria = estructura_geometria
        
        # Crear mecánica temporal para gráficos
        estructura_mecanica_temp = EstructuraAEA_Mecanica(estructura_geometria)
        estructura_mecanica_temp.asignar_cargas_hipotesis(
            state.calculo_mecanico.df_cargas_totales,
            state.calculo_mecanico.resultados_conductor,
            state.calculo_mecanico.resultados_guardia1,
            estructura_actual.get('L_vano'),
            hipotesis_maestro,
            estructura_actual.get('t_hielo'),
            hipotesis_a_incluir="Todas",
            resultados_guardia2=state.calculo_mecanico.resultados_guardia2
        )
        
        estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica_temp)
        
        # Generar gráficos
        estructura_graficos.graficar_estructura(
            zoom_cabezal=estructura_actual.get('ZOOM_CABEZAL', 0.95),
            titulo_reemplazo=estructura_actual.get('TITULO_REEMPLAZO', estructura_actual.get('TIPO_ESTRUCTURA'))
        )
        fig_estructura = plt.gcf()
        
        estructura_graficos.graficar_cabezal(
            zoom_cabezal=estructura_actual.get('ZOOM_CABEZAL', 0.95) * 1.5,
            titulo_reemplazo=estructura_actual.get('TITULO_REEMPLAZO', estructura_actual.get('TIPO_ESTRUCTURA'))
        )
        fig_cabezal = plt.gcf()
        
        # Generar gráfico de nodos (retorna figura Plotly)
        fig_nodos = estructura_graficos.graficar_nodos_coordenadas(
            titulo_reemplazo=estructura_actual.get('TITULO_REEMPLAZO', estructura_actual.get('TIPO_ESTRUCTURA'))
        )
        
        # Generar memoria
        memoria_dge = gen_memoria_calculo_DGE(estructura_geometria)
        
        # Guardar en cache
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        CalculoCache.guardar_calculo_dge(
            nombre_estructura,
            estructura_actual,
            estructura_geometria.dimensiones,
            estructura_geometria.nodes_key,
            fig_estructura,
            fig_cabezal,
            fig_nodos,
            memoria_dge,
            estructura_geometria.conexiones
        )
        
        return {
            "exito": True,
            "mensaje": "Cálculo DGE completado",
            "dimensiones": estructura_geometria.dimensiones,
            "nodes_key": estructura_geometria.nodes_key,
            "memoria_calculo": memoria_dge,
            "fmax_conductor": fmax_conductor,
            "fmax_guardia": fmax_guardia
        }
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}


def ejecutar_calculo_cmc_automatico(estructura_actual, state):
    """Ejecuta cálculo CMC automáticamente con parámetros de estructura o familia"""
    try:
        # Si estructura_actual es de familia, usar datos directamente
        # Si es estructura individual, usar como antes
        
        # Crear objetos
        resultado_objetos = state.calculo_objetos.crear_todos_objetos(estructura_actual)
        if not resultado_objetos["exito"]:
            return {"exito": False, "mensaje": resultado_objetos["mensaje"]}
        
        # Estados climáticos desde estructura o defaults configurables por zona AEA
        estados_climaticos = estructura_actual.get("estados_climaticos", {
            "I": {"temperatura": estructura_actual["temp_max_zona"], "descripcion": "Tmáx", "viento_velocidad": 0, "espesor_hielo": 0},
            "II": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0, "espesor_hielo": 0},
            "III": {"temperatura": 10, "descripcion": "Vmáx", "viento_velocidad": estructura_actual["Vmax"], "espesor_hielo": 0},
            "IV": {"temperatura": -5, "descripcion": "Vmed", "viento_velocidad": estructura_actual["Vmed"], "espesor_hielo": estructura_actual["t_hielo"]},
            "V": {"temperatura": 8, "descripcion": "TMA", "viento_velocidad": 0, "espesor_hielo": 0}
        })
        
        # Restricciones por defecto
        restricciones_dict = {
            "conductor": {"tension_max_porcentaje": {"I": 0.25, "II": 0.40, "III": 0.40, "IV": 0.40, "V": 0.25}},
            "guardia": {
                "tension_max_porcentaje": {"I": 0.7, "II": 0.70, "III": 0.70, "IV": 0.7, "V": 0.7},
                "relflecha_max": estructura_actual.get("RELFLECHA_MAX_GUARDIA", 0.95)
            }
        }
        
        # Parámetros de cálculo - SIN valores por defecto, debe fallar si no existen
        params = {
            "L_vano": estructura_actual["L_vano"],
            "alpha": estructura_actual["alpha"],
            "theta": estructura_actual["theta"],
            "Vmax": estructura_actual["Vmax"],
            "Vmed": estructura_actual["Vmed"],
            "t_hielo": estructura_actual["t_hielo"],
            "exposicion": estructura_actual["exposicion"],
            "clase": estructura_actual["clase"],
            "Zco": estructura_actual["Zco"],
            "Zcg": estructura_actual["Zcg"],
            "Zca": estructura_actual["Zca"],
            "Zes": estructura_actual["Zes"],
            "Cf_cable": estructura_actual["Cf_cable"],
            "Cf_guardia": estructura_actual["Cf_guardia"],
            "Cf_cadena": estructura_actual["Cf_cadena"],
            "Cf_estructura": estructura_actual["Cf_estructura"],
            "PCADENA": estructura_actual["PCADENA"],
            "SALTO_PORCENTUAL": estructura_actual["SALTO_PORCENTUAL"],
            "PASO_AFINADO": estructura_actual["PASO_AFINADO"],
            "OBJ_CONDUCTOR": estructura_actual["OBJ_CONDUCTOR"],
            "OBJ_GUARDIA": estructura_actual["OBJ_GUARDIA"],
            "RELFLECHA_MAX_GUARDIA": estructura_actual["RELFLECHA_MAX_GUARDIA"],
            "RELFLECHA_SIN_VIENTO": estructura_actual["RELFLECHA_SIN_VIENTO"]
        }
        
        # Capturar output de consola
        import io, sys
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        # Ejecutar cálculo
        resultado = state.calculo_mecanico.calcular(params, estados_climaticos, restricciones_dict)
        
        console_output = buffer.getvalue()
        sys.stdout = old_stdout
        
        if resultado["exito"]:
            # Guardar en cache
            from utils.calculo_cache import CalculoCache
            from utils.plot_flechas import crear_grafico_flechas
            
            # Generar gráficos
            fig_combinado, fig_conductor, fig_guardia1, fig_guardia2 = None, None, None, None
            try:
                if state.calculo_mecanico.resultados_guardia2:
                    fig_combinado, fig_conductor, fig_guardia1, fig_guardia2 = crear_grafico_flechas(
                        state.calculo_objetos.cable_conductor,
                        state.calculo_objetos.cable_guardia,
                        params["L_vano"],
                        state.calculo_objetos.cable_guardia2
                    )
                else:
                    fig_combinado, fig_conductor, fig_guardia1 = crear_grafico_flechas(
                        state.calculo_objetos.cable_conductor,
                        state.calculo_objetos.cable_guardia,
                        params["L_vano"]
                    )
            except Exception as e:
                print(f"Error generando gráficos: {e}")
                pass
            
            # Serializar DataFrames
            df_conductor_html = state.calculo_mecanico.df_conductor.to_json(orient='split') if state.calculo_mecanico.df_conductor is not None else None
            df_guardia1_html = state.calculo_mecanico.df_guardia1.to_json(orient='split') if state.calculo_mecanico.df_guardia1 is not None else None
            df_guardia2_html = state.calculo_mecanico.df_guardia2.to_json(orient='split') if state.calculo_mecanico.df_guardia2 is not None else None
            
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            CalculoCache.guardar_calculo_cmc(
                nombre_estructura,
                estructura_actual,
                state.calculo_mecanico.resultados_conductor,
                state.calculo_mecanico.resultados_guardia1,
                state.calculo_mecanico.df_cargas_totales,
                fig_combinado,
                fig_conductor,
                fig_guardia1,
                fig_guardia2,
                resultados_guardia2=state.calculo_mecanico.resultados_guardia2,
                console_output=console_output,
                df_conductor_html=df_conductor_html,
                df_guardia1_html=df_guardia1_html,
                df_guardia2_html=df_guardia2_html
            )
            return {"exito": True, "mensaje": "Cálculo CMC completado automáticamente"}
        else:
            return {"exito": False, "mensaje": resultado["mensaje"]}
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}


def register_callbacks(app):
    """Registrar callbacks de diseño geométrico"""
    
    state = AppState()
    
    # Callback para abrir/cerrar modal de editor de nodos
    @app.callback(
        Output("modal-editor-nodos", "is_open"),
        Output("store-nodos-editor", "data"),
        Output("tabla-nodos-editor", "children"),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-editar-nodos-dge", "n_clicks"),
        Input("btn-cancelar-editor-nodos", "n_clicks"),
        Input("btn-guardar-editor-nodos", "n_clicks"),
        State("modal-editor-nodos", "is_open"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def toggle_modal_editor_nodos(n_abrir, n_cancelar, n_guardar, is_open, estructura_actual):
        from dash import callback_context
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Verificar que realmente hubo un click (no carga inicial)
        if not n_abrir and not n_cancelar and not n_guardar:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        if trigger_id in ["btn-cancelar-editor-nodos", "btn-guardar-editor-nodos"]:
            return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        if trigger_id == "btn-editar-nodos-dge":
            print("🔵 DEBUG: Botón 'Editar Nodos' presionado")
            from utils.calculo_cache import CalculoCache
            from config.app_config import DATA_DIR
            
            # RECARGAR estructura desde archivo
            # RECARGAR estructura desde archivo usando el nuevo sistema
            state.set_estructura_actual(estructura_actual)
            ruta_actual = state.get_estructura_actual_path()
            estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
            print(f"📂 DEBUG: Estructura recargada: {estructura_actual.get('TITULO', 'N/A')}")
            
            # Cargar nodos desde geometría si existe
            nodos_dict = {}
            nodos_objetos = None
            
            if state.calculo_objetos.estructura_geometria:
                nodos_dict = state.calculo_objetos.estructura_geometria.nodes_key
                nodos_objetos = state.calculo_objetos.estructura_geometria.nodos
            else:
                calculo_dge = CalculoCache.cargar_calculo_dge(estructura_actual.get("TITULO", "actual"))
                nodos_dict = calculo_dge.get("nodes_key", {}) if calculo_dge else {}
            
            if not nodos_dict:
                print("⚠️  DEBUG: No hay nodos disponibles")
                return False, dash.no_update, dash.no_update, True, "Advertencia", "Ejecute primero el cálculo DGE para crear nodos que luego puedan ser editados.", "warning", "warning"
            
            print(f"✅ DEBUG: {len(nodos_dict)} nodos encontrados, generando tabla...")
            
            # Obtener cables disponibles desde estructura_actual
            cables_disponibles = []
            if estructura_actual.get("cable_conductor_id"):
                cables_disponibles.append(estructura_actual["cable_conductor_id"])
            if estructura_actual.get("cable_guardia_id"):
                cables_disponibles.append(estructura_actual["cable_guardia_id"])
            if estructura_actual.get("cable_guardia2_id"):
                cables_disponibles.append(estructura_actual["cable_guardia2_id"])
            
            print(f"🔌 DEBUG: Cables disponibles: {cables_disponibles}")
            
            from components.vista_diseno_geometrico import generar_tabla_editor_nodos
            
            # Convertir nodos_dict a lista para store
            nodos_data = []
            for nombre, coords in nodos_dict.items():
                nodo_data = {
                    "nombre": nombre,
                    "tipo": "general",
                    "x": coords[0],
                    "y": coords[1],
                    "z": coords[2],
                    "cable_id": "",
                    "rotacion_eje_x": 0.0,
                    "rotacion_eje_y": 0.0,
                    "rotacion_eje_z": 0.0,
                    "angulo_quiebre": 0.0,
                    "tipo_fijacion": "suspensión",
                    "conectado_a": "",
                    "editar_conexiones": "✏️ Editar"
                }
                if nodos_objetos and nombre in nodos_objetos:
                    nodo_obj = nodos_objetos[nombre]
                    nodo_data["tipo"] = getattr(nodo_obj, 'tipo', 'general')
                    if hasattr(nodo_obj, 'cable_asociado') and nodo_obj.cable_asociado:
                        nodo_data["cable_id"] = nodo_obj.cable_asociado.nombre if hasattr(nodo_obj.cable_asociado, 'nombre') else ""
                    nodo_data["rotacion_eje_x"] = getattr(nodo_obj, 'rotacion_eje_x', 0.0)
                    nodo_data["rotacion_eje_y"] = getattr(nodo_obj, 'rotacion_eje_y', 0.0)
                    nodo_data["rotacion_eje_z"] = getattr(nodo_obj, 'rotacion_eje_z', 0.0)
                    nodo_data["angulo_quiebre"] = getattr(nodo_obj, 'angulo_quiebre', 0.0)
                    nodo_data["tipo_fijacion"] = getattr(nodo_obj, 'tipo_fijacion', 'suspensión') or 'suspensión'
                    conectado_a_list = getattr(nodo_obj, 'conectado_a', [])
                    if conectado_a_list:
                        nodo_data["conectado_a"] = ", ".join(conectado_a_list)
                nodos_data.append(nodo_data)
            
            # AGREGAR nodos editados guardados que NO estén en nodos_dict
            nodos_editados_guardados = estructura_actual.get("nodos_editados", [])
            nombres_existentes = set(nodos_dict.keys())
            
            # Aplicar datos de nodos editados a nodos existentes
            nodos_editados_dict = {n["nombre"]: n for n in nodos_editados_guardados}
            for i, nodo_data in enumerate(nodos_data):
                nombre = nodo_data["nombre"]
                if nombre in nodos_editados_dict:
                    nodo_editado = nodos_editados_dict[nombre]
                    # Solo actualizar si realmente fue editado
                    if nodo_editado.get("es_editado", False):
                        cable_id_editado = nodo_editado.get("cable_id", nodo_data["cable_id"])
                        print(f"   📝 Nodo {nombre}: cable_id = '{cable_id_editado}'")
                        nodos_data[i].update({
                            "tipo": nodo_editado.get("tipo", nodo_data["tipo"]),
                            "x": nodo_editado["coordenadas"][0],
                            "y": nodo_editado["coordenadas"][1],
                            "z": nodo_editado["coordenadas"][2],
                            "cable_id": cable_id_editado,
                            "rotacion_eje_x": nodo_editado.get("rotacion_eje_x", nodo_data.get("rotacion_eje_x", 0.0)),
                            "rotacion_eje_y": nodo_editado.get("rotacion_eje_y", nodo_data.get("rotacion_eje_y", 0.0)),
                            "rotacion_eje_z": nodo_editado.get("rotacion_eje_z", nodo_data["rotacion_eje_z"]),
                            "angulo_quiebre": nodo_editado.get("angulo_quiebre", nodo_data["angulo_quiebre"]),
                            "tipo_fijacion": nodo_editado.get("tipo_fijacion", nodo_data["tipo_fijacion"]),
                            "conectado_a": ", ".join(nodo_editado.get("conectado_a", [])) if isinstance(nodo_editado.get("conectado_a", []), list) else nodo_editado.get("conectado_a", "")
                        })
            
            # Agregar nodos completamente nuevos
            for nodo_editado in nodos_editados_guardados:
                nombre = nodo_editado["nombre"]
                if nombre not in nombres_existentes and nodo_editado.get("es_editado", False):
                    coords = nodo_editado["coordenadas"]
                    conectado_a_list = nodo_editado.get("conectado_a", [])
                    conectado_a_str = ", ".join(conectado_a_list) if isinstance(conectado_a_list, list) else conectado_a_list
                    
                    nodos_data.append({
                        "nombre": nombre,
                        "tipo": nodo_editado.get("tipo", "general"),
                        "x": coords[0],
                        "y": coords[1],
                        "z": coords[2],
                        "cable_id": nodo_editado.get("cable_id", ""),
                        "rotacion_eje_x": nodo_editado.get("rotacion_eje_x", 0.0),
                        "rotacion_eje_y": nodo_editado.get("rotacion_eje_y", 0.0),
                        "rotacion_eje_z": nodo_editado.get("rotacion_eje_z", 0.0),
                        "angulo_quiebre": nodo_editado.get("angulo_quiebre", 0.0),
                        "tipo_fijacion": nodo_editado.get("tipo_fijacion", "suspensión"),
                        "conectado_a": conectado_a_str,
                        "editar_conexiones": "✏️ Editar"
                    })
            
            tabla = generar_tabla_editor_nodos(nodos_data, cables_disponibles)
            print(f"✅ DEBUG: Tabla generada, abriendo modal con {len(nodos_data)} nodos")
            
            return True, nodos_data, tabla, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Callback para agregar nodo
    @app.callback(
        Output("store-nodos-editor", "data", allow_duplicate=True),
        Output("tabla-nodos-editor", "children", allow_duplicate=True),
        Input("btn-agregar-nodo-tabla", "n_clicks"),
        State("store-nodos-editor", "data"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def agregar_nodo_tabla(n_clicks, nodos_data, estructura_actual):
        if not n_clicks:
            return dash.no_update, dash.no_update
        
        nuevo_nodo = {
            "nombre": f"NUEVO_{len(nodos_data)+1}",
            "tipo": "general",
            "x": 0.0,
            "y": 0.0,
            "z": 10.0,
            "cable_id": "",
            "rotacion_eje_x": 0.0,
            "rotacion_eje_y": 0.0,
            "rotacion_eje_z": 0.0,
            "angulo_quiebre": 0.0,
            "tipo_fijacion": "suspensión",
            "conectado_a": "",
            "editar_conexiones": "✏️ Editar"
        }
        nodos_data.append(nuevo_nodo)
        
        # Regenerar tabla
        cables_disponibles = []
        if estructura_actual.get("cable_conductor_id"):
            cables_disponibles.append(estructura_actual["cable_conductor_id"])
        if estructura_actual.get("cable_guardia_id"):
            cables_disponibles.append(estructura_actual["cable_guardia_id"])
        if estructura_actual.get("cable_guardia2_id"):
            cables_disponibles.append(estructura_actual["cable_guardia2_id"])
        
        from components.vista_diseno_geometrico import generar_tabla_editor_nodos
        tabla = generar_tabla_editor_nodos(nodos_data, cables_disponibles)
        
        return nodos_data, tabla
    
    # Callbacks para asignar cables rápidamente
    @app.callback(
        Output("datatable-nodos", "data", allow_duplicate=True),
        Input("btn-asignar-conductor", "n_clicks"),
        Input("btn-asignar-guardia", "n_clicks"),
        Input("btn-quitar-cable", "n_clicks"),
        State("datatable-nodos", "data"),
        State("datatable-nodos", "active_cell"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def asignar_cable_rapido(n_conductor, n_guardia, n_quitar, tabla_data, active_cell, estructura_actual):
        from dash import callback_context
        ctx = callback_context
        if not ctx.triggered or not active_cell:
            return dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Verificar que la celda activa sea de la columna cable_id
        if active_cell["column_id"] != "cable_id":
            return dash.no_update
        
        row_index = active_cell["row"]
        
        if trigger_id == "btn-asignar-conductor":
            tabla_data[row_index]["cable_id"] = estructura_actual.get("cable_conductor_id", "")
        elif trigger_id == "btn-asignar-guardia":
            tabla_data[row_index]["cable_id"] = estructura_actual.get("cable_guardia_id", "")
        elif trigger_id == "btn-quitar-cable":
            tabla_data[row_index]["cable_id"] = ""
        
        return tabla_data
    
    # Callback para detectar cambios en la tabla de nodos
    @app.callback(
        Output("store-nodos-editor", "data", allow_duplicate=True),
        Input("datatable-nodos", "data"),
        State("store-nodos-editor", "data"),
        prevent_initial_call=True
    )
    def actualizar_nodos_desde_tabla(tabla_data, store_data):
        if not tabla_data or not store_data:
            return dash.no_update
        
        # Actualizar store con datos de la tabla
        for i, row in enumerate(tabla_data):
            if i < len(store_data):
                store_data[i].update({
                    "nombre": row.get("nombre", store_data[i]["nombre"]),
                    "tipo": row.get("tipo", store_data[i]["tipo"]),
                    "x": row.get("x", store_data[i]["x"]),
                    "y": row.get("y", store_data[i]["y"]),
                    "z": row.get("z", store_data[i]["z"]),
                    "cable_id": row.get("cable_id", store_data[i]["cable_id"]),
                    "rotacion_eje_x": row.get("rotacion_eje_x", store_data[i].get("rotacion_eje_x", 0.0)),
                    "rotacion_eje_y": row.get("rotacion_eje_y", store_data[i].get("rotacion_eje_y", 0.0)),
                    "rotacion_eje_z": row.get("rotacion_eje_z", store_data[i]["rotacion_eje_z"]),
                    "angulo_quiebre": row.get("angulo_quiebre", store_data[i]["angulo_quiebre"]),
                    "tipo_fijacion": row.get("tipo_fijacion", store_data[i]["tipo_fijacion"]),
                    "conectado_a": row.get("conectado_a", store_data[i]["conectado_a"])
                })
        
        return store_data
    
    # Callback para submodal de conexiones
    @app.callback(
        Output("submodal-conexiones", "is_open"),
        Output("checkboxes-conexiones-nodos", "children"),
        Output("store-nodos-editor", "data", allow_duplicate=True),
        Input("datatable-nodos", "active_cell"),
        Input("btn-cancelar-submodal-conexiones", "n_clicks"),
        Input("btn-aceptar-submodal-conexiones", "n_clicks"),
        State("store-nodos-editor", "data"),
        State({"type": "checkbox-conexion", "index": dash.dependencies.ALL}, "value"),
        prevent_initial_call=True
    )
    def toggle_submodal_conexiones(active_cell, n_cancelar, n_aceptar, nodos_data, checkbox_values):
        from dash import callback_context
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-cancelar-submodal-conexiones":
            return False, dash.no_update, dash.no_update
        
        if trigger_id == "btn-aceptar-submodal-conexiones":
            if checkbox_values and len(checkbox_values) > 0:
                selected = checkbox_values[0] if checkbox_values[0] else []
                # Buscar el nodo que se está editando (el último que abrió el submodal)
                for i, nodo in enumerate(nodos_data):
                    if "_editing" in nodo:
                        nodos_data[i]["conectado_a"] = ", ".join(selected)
                        del nodos_data[i]["_editing"]
                        break
                return False, dash.no_update, nodos_data
            return False, dash.no_update, dash.no_update
        
        if trigger_id == "datatable-nodos" and active_cell:
            if active_cell["column_id"] == "editar_conexiones":
                row_index = active_cell["row"]
                nodo_actual = nodos_data[row_index]["nombre"]
                conexiones_actuales = nodos_data[row_index].get("conectado_a", "")
                conexiones_list = [c.strip() for c in conexiones_actuales.split(",") if c.strip()]
                
                # Marcar nodo como editando
                nodos_data[row_index]["_editing"] = True
                
                opciones = []
                for nodo in nodos_data:
                    if nodo["nombre"] != nodo_actual:
                        opciones.append({"label": nodo["nombre"], "value": nodo["nombre"]})
                
                checkboxes = dbc.Checklist(
                    id={"type": "checkbox-conexion", "index": row_index},
                    options=opciones,
                    value=conexiones_list,
                    inline=False
                )
                return True, checkboxes, nodos_data
        
        return dash.no_update, dash.no_update, dash.no_update
    
    # Callback para guardar cambios de nodos
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-editor-nodos", "n_clicks"),
        State("store-nodos-editor", "data"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_cambios_nodos(n_clicks, nodos_data, estructura_actual):
        if not n_clicks:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        if not nodos_data:
            return dash.no_update, True, "Error", "No hay datos de nodos", "danger", "danger"
        
        try:
            from utils.estructura_manager import EstructuraManager
            
            # Validaciones
            nombres_vistos = set()
            tipos_validos = ["conductor", "guardia", "base", "cruce", "general", "viento"]
            
            for i, nodo in enumerate(nodos_data):
                # Validar nombre único
                nombre = nodo.get("nombre", "").strip()
                if not nombre:
                    return dash.no_update, True, "Error", f"Fila {i+1}: Nombre vacío", "danger", "danger"
                if nombre in nombres_vistos:
                    return dash.no_update, True, "Error", f"Nombre duplicado: {nombre}", "danger", "danger"
                nombres_vistos.add(nombre)
                
                # Validar tipo
                tipo = nodo.get("tipo", "").strip()
                if not tipo:
                    return dash.no_update, True, "Error", f"Fila {i+1}: Tipo vacío", "danger", "danger"
                if tipo not in tipos_validos:
                    return dash.no_update, True, "Error", f"Fila {i+1}: Tipo inválido '{tipo}'", "danger", "danger"
                
                # Validar coordenadas
                try:
                    x, y, z = float(nodo["x"]), float(nodo["y"]), float(nodo["z"])
                    if z < 0:
                        return dash.no_update, True, "Error", f"Fila {i+1}: Coordenada Z negativa", "danger", "danger"
                except (ValueError, TypeError, KeyError):
                    return dash.no_update, True, "Error", f"Fila {i+1}: Coordenadas inválidas", "danger", "danger"
                
                # Validar rotaciones
                try:
                    rot_x = float(nodo.get("rotacion_eje_x", 0.0))
                    rot_y = float(nodo.get("rotacion_eje_y", 0.0))
                    rot_z = float(nodo.get("rotacion_eje_z", 0.0))
                    if not (-360 <= rot_x <= 360):
                        return dash.no_update, True, "Error", f"Fila {i+1}: Rotación X debe estar entre -360° y 360°", "danger", "danger"
                    if not (-360 <= rot_y <= 360):
                        return dash.no_update, True, "Error", f"Fila {i+1}: Rotación Y debe estar entre -360° y 360°", "danger", "danger"
                    if not (-360 <= rot_z <= 360):
                        return dash.no_update, True, "Error", f"Fila {i+1}: Rotación Z debe estar entre -360° y 360°", "danger", "danger"
                except (ValueError, TypeError):
                    return dash.no_update, True, "Error", f"Fila {i+1}: Rotaciones inválidas", "danger", "danger"
            
            # Validar nodos conectados existen
            for i, nodo in enumerate(nodos_data):
                conectado_str = nodo.get("conectado_a", "").strip()
                if conectado_str:
                    conectados = [n.strip() for n in conectado_str.split(",") if n.strip()]
                    for conn in conectados:
                        if conn not in nombres_vistos:
                            return dash.no_update, True, "Error", f"Fila {i+1}: Nodo conectado '{conn}' no existe", "danger", "danger"
            
            # Crear lista de nodos editados - solo incluir nodos que realmente cambiaron
            nodos_editados = []
            nodos_originales = {}
            
            # Cargar nodos originales desde geometría o cache
            if state.calculo_objetos.estructura_geometria:
                nodos_originales = state.calculo_objetos.estructura_geometria.nodes_key
            else:
                from utils.calculo_cache import CalculoCache
                calculo_dge = CalculoCache.cargar_calculo_dge(estructura_actual.get("TITULO", "actual"))
                nodos_originales = calculo_dge.get("nodes_key", {}) if calculo_dge else {}
            
            # Comparar cada nodo con su versión original
            for nodo in nodos_data:
                nombre = nodo["nombre"].strip()
                conectado_str = nodo.get("conectado_a", "").strip()
                conectados = [n.strip() for n in conectado_str.split(",") if n.strip()] if conectado_str else []
                
                # Verificar si el nodo cambió respecto al original
                es_editado = False
                if nombre not in nodos_originales:
                    # Nodo nuevo
                    es_editado = True
                else:
                    # Comparar coordenadas
                    coords_orig = nodos_originales[nombre]
                    coords_actual = [float(nodo["x"]), float(nodo["y"]), float(nodo["z"])]
                    if abs(coords_actual[0] - coords_orig[0]) > 0.001 or abs(coords_actual[1] - coords_orig[1]) > 0.001 or abs(coords_actual[2] - coords_orig[2]) > 0.001:
                        es_editado = True
                    
                    # Verificar cable_id
                    cable_id_actual = nodo.get("cable_id", "").strip()
                    cable_id_original = ""
                    if state.calculo_objetos.estructura_geometria and nombre in state.calculo_objetos.estructura_geometria.nodos:
                        nodo_obj = state.calculo_objetos.estructura_geometria.nodos[nombre]
                        if hasattr(nodo_obj, 'cable_asociado') and nodo_obj.cable_asociado:
                            cable_id_original = nodo_obj.cable_asociado.nombre if hasattr(nodo_obj.cable_asociado, 'nombre') else ""
                    
                    if cable_id_actual != cable_id_original:
                        es_editado = True
                    
                    # Verificar otros campos si hay objetos nodo
                    if state.calculo_objetos.estructura_geometria and nombre in state.calculo_objetos.estructura_geometria.nodos:
                        nodo_obj = state.calculo_objetos.estructura_geometria.nodos[nombre]
                        if (nodo.get("tipo", "general") != getattr(nodo_obj, 'tipo', 'general') or
                            float(nodo.get("rotacion_eje_x", 0.0)) != getattr(nodo_obj, 'rotacion_eje_x', 0.0) or
                            float(nodo.get("rotacion_eje_y", 0.0)) != getattr(nodo_obj, 'rotacion_eje_y', 0.0) or
                            float(nodo.get("rotacion_eje_z", 0.0)) != getattr(nodo_obj, 'rotacion_eje_z', 0.0) or
                            float(nodo.get("angulo_quiebre", 0.0)) != getattr(nodo_obj, 'angulo_quiebre', 0.0) or
                            nodo.get("tipo_fijacion", "suspensión") != (getattr(nodo_obj, 'tipo_fijacion', 'suspensión') or 'suspensión')):
                            es_editado = True
                
                # Solo agregar si fue editado
                if es_editado:
                    nodos_editados.append({
                        "nombre": nombre,
                        "tipo": nodo["tipo"],
                        "coordenadas": [float(nodo["x"]), float(nodo["y"]), float(nodo["z"])],
                        "cable_id": nodo.get("cable_id", ""),
                        "rotacion_eje_x": float(nodo.get("rotacion_eje_x", 0.0)),
                        "rotacion_eje_y": float(nodo.get("rotacion_eje_y", 0.0)),
                        "rotacion_eje_z": float(nodo.get("rotacion_eje_z", 0.0)),
                        "angulo_quiebre": float(nodo.get("angulo_quiebre", 0.0)),
                        "tipo_fijacion": nodo.get("tipo_fijacion", "suspensión"),
                        "conectado_a": conectados,
                        "es_editado": True
                    })
            
            # Guardar en archivos JSON PRIMERO
            state.estructura_manager.guardar_nodos_editados(nodos_editados)
            
            # Recargar estructura desde archivo para asegurar persistencia
            from config.app_config import DATA_DIR
            # Recargar estructura actual usando el nuevo sistema
            state = AppState()
            state.set_estructura_actual(estructura_actual)
            ruta_actual = state.get_estructura_actual_path()
            estructura_actualizada = state.estructura_manager.cargar_estructura(ruta_actual)
            
            print(f"💾 DEBUG: Nodos guardados en archivo. Total nodos_editados: {len(estructura_actualizada.get('nodos_editados', []))}")
            
            if len(nodos_editados) == 0:
                return dash.no_update, True, "Info", "No se detectaron cambios en los nodos.", "info", "info"
            
            return estructura_actualizada, True, "Éxito", f"{len(nodos_editados)} nodos editados guardados. Recalcule DGE para aplicar cambios.", "success", "success"
            
        except Exception as e:
            return dash.no_update, True, "Error", f"Error al guardar nodos: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("estructura-actual", "data", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-params-geom", "n_clicks"),
        State("slider-tension-geom", "value"),
        State("select-zona-estructura", "value"),
        State("slider-lk-geom", "value"),
        State("slider-ang-apantallamiento", "value"),
        State("select-disposicion-geom", "value"),
        State("select-terna-geom", "value"),
        State("slider-cant-hg-geom", "value"),
        State("slider-altura-min-cable", "value"),
        State("slider-lmen-min-cond", "value"),
        State("slider-lmen-min-guard", "value"),
        State("slider-hadd-geom", "value"),
        State("slider-hadd-entre-amarres", "value"),
        State("slider-hadd-hg-geom", "value"),
        State("slider-hadd-lmen-geom", "value"),
        State("slider-ancho-cruceta-geom", "value"),
        State("slider-dist-repos-hg", "value"),
        State("switch-hg-centrado", "value"),
        State("switch-autoajustar-lmenhg", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_parametros_geometria(n_clicks, tension, zona, lk, ang_apant, disposicion, terna, cant_hg,
                                     altura_min, lmen_cond, lmen_guard, hadd, hadd_amarres, hadd_hg, hadd_lmen,
                                     ancho_cruceta, dist_repos, hg_centrado, autoajustar, estructura_actual):
        if not n_clicks:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        try:
            # Recargar estructura desde archivo
            state.set_estructura_actual(estructura_actual)
            ruta_actual = state.get_estructura_actual_path()
            estructura_actualizada = state.estructura_manager.cargar_estructura(ruta_actual)
            
            # Actualizar parámetros
            estructura_actualizada.update({
                "TENSION": tension,
                "Zona_estructura": zona,
                "Lk": lk,
                "ANG_APANTALLAMIENTO": ang_apant,
                "DISPOSICION": disposicion,
                "TERNA": terna,
                "CANT_HG": cant_hg,
                "ALTURA_MINIMA_CABLE": altura_min,
                "LONGITUD_MENSULA_MINIMA_CONDUCTOR": lmen_cond,
                "LONGITUD_MENSULA_MINIMA_GUARDIA": lmen_guard,
                "HADD": hadd,
                "HADD_ENTRE_AMARRES": hadd_amarres,
                "HADD_HG": hadd_hg,
                "HADD_LMEN": hadd_lmen,
                "ANCHO_CRUCETA": ancho_cruceta,
                "DIST_REPOSICIONAR_HG": dist_repos,
                "HG_CENTRADO": hg_centrado,
                "AUTOAJUSTAR_LMENHG": autoajustar
            })
            
            # Guardar usando el manager
            state.estructura_manager.guardar_estructura(estructura_actualizada, ruta_actual)
            
            # Actualizar estado interno
            state.set_estructura_actual(estructura_actualizada)
            
            return (
                estructura_actualizada,
                True, 
                "Éxito", 
                "Parámetros de geometría guardados", 
                "success", 
                "success"
            )
        except Exception as e:
            return (
                dash.no_update,
                True, 
                "Error", 
                f"Error al guardar: {str(e)}", 
                "danger", 
                "danger"
            )
    
    @app.callback(
        Output("output-diseno-geometrico", "children", allow_duplicate=True),
        Input("btn-cargar-cache-dge", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def cargar_cache_dge(n_clicks, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        from utils.calculo_cache import CalculoCache
        from components.vista_diseno_geometrico import generar_resultados_dge
        from config.app_config import DATA_DIR
        
        # Recargar estructura desde archivo usando el nuevo sistema
        state.set_estructura_actual(estructura_actual)
        ruta_actual = state.get_estructura_actual_path()
        estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        
        calculo_guardado = CalculoCache.cargar_calculo_dge(nombre_estructura)
        
        if calculo_guardado:
            return generar_resultados_dge(calculo_guardado, estructura_actual, mostrar_alerta_cache=True)
        else:
            return dbc.Alert("No hay datos en cache para esta estructura", color="warning")
    
    @app.callback(
        Output("output-diseno-geometrico", "children"),
        Input("btn-calcular-geom", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def calcular_diseno_geometrico(n_clicks, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        # SIEMPRE recargar estructura desde archivo usando el nuevo sistema
        state.set_estructura_actual(estructura_actual)
        ruta_actual = state.get_estructura_actual_path()
        estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
        
        # Guardar navegación
        from controllers.navigation_controller import guardar_navegacion_state
        guardar_navegacion_state("diseno-geometrico")
        
        print(f"\n🔵 DEBUG INICIO CÁLCULO DGE")
        print(f"   estructura_actual tiene nodos_editados: {'nodos_editados' in estructura_actual if estructura_actual else False}")
        if estructura_actual and 'nodos_editados' in estructura_actual:
            print(f"   Total nodos_editados: {len(estructura_actual['nodos_editados'])}")
            for nodo in estructura_actual['nodos_editados']:
                print(f"     - {nodo.get('nombre', 'SIN_NOMBRE')}")
        
        try:
            from EstructuraAEA_Geometria import EstructuraAEA_Geometria
            from utils.calculo_cache import CalculoCache
            
            # Verificar si existe cálculo CMC guardado
            if not state.calculo_mecanico.resultados_conductor or not state.calculo_mecanico.resultados_guardia1:
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
                
                if calculo_cmc:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_cmc, estructura_actual)
                    if vigente:
                        # Cargar resultados desde cache
                        resultados_cond = calculo_cmc.get('resultados_conductor', {})
                        resultados_guard = calculo_cmc.get('resultados_guardia', {})
                        
                        # Verificar que no estén vacíos
                        if not resultados_cond or not resultados_guard:
                            resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                            if not resultado_auto["exito"]:
                                return dbc.Alert(f"Error en cálculo automático CMC: {resultado_auto['mensaje']}", color="danger")
                        else:
                            state.calculo_mecanico.resultados_conductor = resultados_cond
                            state.calculo_mecanico.resultados_guardia1 = resultados_guard
                            state.calculo_mecanico.resultados_guardia2 = calculo_cmc.get('resultados_guardia2', None)
                            if calculo_cmc.get('df_cargas_totales'):
                                import pandas as pd
                                state.calculo_mecanico.df_cargas_totales = pd.DataFrame(calculo_cmc['df_cargas_totales'])
                            
                            # Crear objetos de cable si no existen
                            if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                                state.calculo_objetos.crear_todos_objetos(estructura_actual)
                    else:
                        # Ejecutar cálculo CMC automáticamente
                        resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                        if not resultado_auto["exito"]:
                            return dbc.Alert(f"Error en cálculo automático CMC: {resultado_auto['mensaje']}", color="danger")
                else:
                    # Ejecutar cálculo CMC automáticamente
                    resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                    if not resultado_auto["exito"]:
                        return dbc.Alert(f"Error en cálculo automático CMC: {resultado_auto['mensaje']}", color="danger")
            
            # Verificar que existen objetos de cálculo
            if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                state.calculo_objetos.crear_todos_objetos(estructura_actual)
            
            # Verificar que hay resultados válidos
            if not state.calculo_mecanico.resultados_conductor or not state.calculo_mecanico.resultados_guardia1:
                return dbc.Alert("No hay resultados de CMC. Ejecute primero el cálculo mecánico de cables.", color="warning")
            
            # Obtener flechas máximas
            fmax_conductor = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_conductor.values()])
            fmax_guardia1 = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia1.values()])
            if state.calculo_mecanico.resultados_guardia2:
                fmax_guardia2 = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia2.values()])
                fmax_guardia = max(fmax_guardia1, fmax_guardia2)
            else:
                fmax_guardia2 = fmax_guardia1
                fmax_guardia = fmax_guardia1
            
            # Crear estructura de geometría
            estructura_geometria = EstructuraAEA_Geometria(
                tipo_estructura=estructura_actual.get("TIPO_ESTRUCTURA"),
                tension_nominal=estructura_actual.get("TENSION"),
                zona_estructura=estructura_actual.get("Zona_estructura"),
                disposicion=estructura_actual.get("DISPOSICION"),
                terna=estructura_actual.get("TERNA"),
                cant_hg=estructura_actual.get("CANT_HG"),
                alpha_quiebre=estructura_actual.get("alpha"),
                altura_minima_cable=estructura_actual.get("ALTURA_MINIMA_CABLE"),
                long_mensula_min_conductor=estructura_actual.get("LONGITUD_MENSULA_MINIMA_CONDUCTOR"),
                long_mensula_min_guardia=estructura_actual.get("LONGITUD_MENSULA_MINIMA_GUARDIA"),
                hadd=estructura_actual.get("HADD"),
                hadd_entre_amarres=estructura_actual.get("HADD_ENTRE_AMARRES"),
                lk=estructura_actual.get("Lk"),
                ancho_cruceta=estructura_actual.get("ANCHO_CRUCETA"),
                cable_conductor=state.calculo_objetos.cable_conductor,
                cable_guardia=state.calculo_objetos.cable_guardia,
                peso_estructura=estructura_actual.get("PESTRUCTURA"),
                peso_cadena=estructura_actual.get("PCADENA"),
                hg_centrado=estructura_actual.get("HG_CENTRADO"),
                ang_apantallamiento=estructura_actual.get("ANG_APANTALLAMIENTO"),
                hadd_hg=estructura_actual.get("HADD_HG"),
                hadd_lmen=estructura_actual.get("HADD_LMEN"),
                dist_reposicionar_hg=estructura_actual.get("DIST_REPOSICIONAR_HG"),
                ajustar_por_altura_msnm=estructura_actual.get("AJUSTAR_POR_ALTURA_MSNM"),
                metodo_altura_msnm=estructura_actual.get("METODO_ALTURA_MSNM"),
                altura_msnm=estructura_actual.get("Altura_MSNM")
            )
            
            # Dimensionar
            estructura_geometria.dimensionar_unifilar(
                estructura_actual.get("L_vano"),
                fmax_conductor,
                fmax_guardia,
                dist_reposicionar_hg=estructura_actual.get("DIST_REPOSICIONAR_HG"),
                autoajustar_lmenhg=estructura_actual.get("AUTOAJUSTAR_LMENHG")
            )
            
            # Aplicar nodos editados si existen
            nodos_editados = estructura_actual.get("nodos_editados", [])
            print(f"DEBUG: Nodos editados en estructura_actual: {len(nodos_editados)}")
            if nodos_editados:
                print(f"DEBUG: Aplicando {len(nodos_editados)} nodos editados...")
                from CalculoCables import LibCables
                lib_cables = LibCables()
                lib_cables.agregar_cable(state.calculo_objetos.cable_conductor)
                lib_cables.agregar_cable(state.calculo_objetos.cable_guardia)
                if state.calculo_objetos.cable_guardia2:
                    lib_cables.agregar_cable(state.calculo_objetos.cable_guardia2)
                
                aplicar_nodos_editados(estructura_geometria, nodos_editados, lib_cables)
            else:
                print("DEBUG: No hay nodos editados para aplicar")
            
            # Guardar en estado
            state.calculo_objetos.estructura_geometria = estructura_geometria
            
            # Crear mecánica y gráficos
            from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
            from EstructuraAEA_Graficos import EstructuraAEA_Graficos
            from HipotesisMaestro_Especial import hipotesis_maestro
            
            estructura_mecanica = EstructuraAEA_Mecanica(estructura_geometria)
            # Asignar cable_guardia2 si existe
            if state.calculo_objetos.cable_guardia2:
                estructura_geometria.cable_guardia2 = state.calculo_objetos.cable_guardia2
            
            estructura_mecanica.asignar_cargas_hipotesis(
                state.calculo_mecanico.df_cargas_totales,
                state.calculo_mecanico.resultados_conductor,
                state.calculo_mecanico.resultados_guardia1,
                estructura_actual.get('L_vano'),
                hipotesis_maestro,
                estructura_actual.get('t_hielo'),
                hipotesis_a_incluir="Todas",
                resultados_guardia2=state.calculo_mecanico.resultados_guardia2
            )
            
            estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica)
            
            # Actualizar nodes_key INMEDIATAMENTE después de aplicar nodos editados
            estructura_geometria._actualizar_nodes_key()
            
            # Listar nodos DESPUÉS de actualizar nodes_key
            estructura_geometria.listar_nodos()
            
            # Generar gráficos y capturar figuras
            import matplotlib.pyplot as plt
            
            # Graficar estructura
            estructura_graficos.graficar_estructura(
                zoom_cabezal=estructura_actual.get('ZOOM_CABEZAL', 0.95),
                titulo_reemplazo=estructura_actual.get('TITULO_REEMPLAZO', estructura_actual.get('TIPO_ESTRUCTURA'))
            )
            fig_estructura = plt.gcf()
            
            # Graficar cabezal
            estructura_graficos.graficar_cabezal(
                zoom_cabezal=estructura_actual.get('ZOOM_CABEZAL', 0.95) * 1.5,
                titulo_reemplazo=estructura_actual.get('TITULO_REEMPLAZO', estructura_actual.get('TIPO_ESTRUCTURA'))
            )
            fig_cabezal = plt.gcf()
            
            # Graficar nodos (ahora retorna figura Plotly)
            fig_nodos = estructura_graficos.graficar_nodos_coordenadas(
                titulo_reemplazo=estructura_actual.get('TITULO_REEMPLAZO', estructura_actual.get('TIPO_ESTRUCTURA'))
            )
            
            # Guardar en estado
            state.calculo_objetos.estructura_mecanica = estructura_mecanica
            state.calculo_objetos.estructura_graficos = estructura_graficos
            
            # Obtener dimensiones y nodes_key ACTUALIZADOS
            dims = estructura_geometria.dimensiones
            nodes_key = estructura_geometria.obtener_nodes_key()
            print(f"\n📊 DEBUG: nodes_key tiene {len(nodes_key)} nodos para guardar en cache")
            for nombre in sorted(nodes_key.keys()):
                print(f"   - {nombre}: {nodes_key[nombre]}")
            altura_total = dims.get('altura_total', 0)
            h1a = dims.get('h1a', 0)
            h2a = dims.get('h2a', 0)
            lmen = dims.get('lmen', 0)
            lmenhg = dims.get('lmenhg', 0)
            hhg = dims.get('hhg', 0)
            
            # Obtener parámetros de cálculo del diccionario dimensiones
            theta_max = dims.get('theta_max', 0)
            coeficiente_k = dims.get('k', 0)
            Ka = dims.get('Ka', 1)
            D_fases = dims.get('D_fases', 0)
            Dhg = dims.get('Dhg', 0)
            s_estructura = dims.get('s_estructura', 0)
            # Intentar diferentes nombres de clave para a, b, altura_base_electrica
            a = dims.get('a', dims.get('altura_libre', 0))
            b = dims.get('b', 0)
            altura_base_electrica = dims.get('altura_base_electrica', dims.get('h_base_electrica', dims.get('altura_libre', 0)))
            
            # Si aún son 0, calcular desde nodos
            if altura_base_electrica == 0 and 'C1_R' in nodes_key:
                altura_base_electrica = nodes_key['C1_R'][2] - estructura_actual.get('Lk', 0)
            if a == 0:
                a = estructura_actual.get('ALTURA_MINIMA_CABLE', 6.5)
            
            # Flechas máximas
            if state.calculo_mecanico.resultados_guardia2:
                flechas_txt = f"Flechas máximas: conductor={fmax_conductor:.2f}m, guardia1={fmax_guardia1:.2f}m, guardia2={fmax_guardia2:.2f}m"
            else:
                flechas_txt = f"Flechas máximas: conductor={fmax_conductor:.2f}m, guardia={fmax_guardia:.2f}m"
            
            # Parámetros de diseño
            params_txt = (
                f"Tipo estructura: {estructura_actual.get('TIPO_ESTRUCTURA')}\n" +
                f"Tensión nominal: {estructura_actual.get('TENSION')} kV\n" +
                f"Zona: {estructura_actual.get('Zona_estructura')}\n" +
                f"Disposición: {estructura_actual.get('DISPOSICION')}\n" +
                f"Terna: {estructura_actual.get('TERNA')}\n" +
                f"Cantidad HG: {estructura_actual.get('CANT_HG')}\n" +
                f"Vano: {estructura_actual.get('L_vano')} m\n" +
                f"Autoajustar lmenhg: {'ACTIVADO' if estructura_actual.get('AUTOAJUSTAR_LMENHG') else 'DESACTIVADO'}"
            )
            
            # Dimensiones de estructura
            dims_txt = (
                f"Altura total: {altura_total:.2f} m\n" +
                f"Alturas: h1a={h1a:.2f}m, h2a={h2a:.2f}m\n" +
                f"Ménsulas: lmen={lmen:.2f}m, lmenhg={lmenhg:.2f}m\n" +
                f"Cable guardia: hhg={hhg:.2f}m"
            )
            
            # Nodos por tipo (usando objetos nodo para obtener el tipo real)
            print(f"\n📊 DEBUG: Generando texto de nodos con {len(nodes_key)} nodos")
            nodos_base = {}
            nodos_cross = {}
            nodos_cond = {}
            nodos_guard = {}
            nodos_gen = {}
            nodos_viento = {}
            
            for nombre_nodo, coords in nodes_key.items():
                # Obtener tipo del objeto nodo
                nodo_obj = estructura_geometria.nodos.get(nombre_nodo)
                if nodo_obj:
                    tipo = nodo_obj.tipo_nodo
                else:
                    # Fallback: inferir por nombre
                    if nombre_nodo == 'BASE':
                        tipo = 'base'
                    elif nombre_nodo.startswith('CROSS'):
                        tipo = 'cruce'
                    elif nombre_nodo.startswith('C') and not nombre_nodo.startswith('CROSS'):
                        tipo = 'conductor'
                    elif nombre_nodo.startswith('HG'):
                        tipo = 'guardia'
                    elif nombre_nodo == 'V':
                        tipo = 'viento'
                    else:
                        tipo = 'general'
                
                # Clasificar por tipo
                if tipo == 'base':
                    nodos_base[nombre_nodo] = coords
                elif tipo == 'cruce':
                    nodos_cross[nombre_nodo] = coords
                elif tipo == 'conductor':
                    nodos_cond[nombre_nodo] = coords
                elif tipo == 'guardia':
                    nodos_guard[nombre_nodo] = coords
                elif tipo == 'viento':
                    nodos_viento[nombre_nodo] = coords
                else:
                    nodos_gen[nombre_nodo] = coords
            
            print(f"   - Base: {len(nodos_base)}, Cruce: {len(nodos_cross)}, Conductor: {len(nodos_cond)}, Guardia: {len(nodos_guard)}, General: {len(nodos_gen)}, Viento: {len(nodos_viento)}")
            
            nodos_txt = "BASE:\n" + "\n".join([f"  {k}: ({float(v[0]):.3f}, {float(v[1]):.3f}, {float(v[2]):.3f})" for k, v in nodos_base.items()])
            if nodos_cross:
                nodos_txt += "\n\nCRUCE:\n" + "\n".join([f"  {k}: ({float(v[0]):.3f}, {float(v[1]):.3f}, {float(v[2]):.3f})" for k, v in nodos_cross.items()])
            if nodos_cond:
                nodos_txt += "\n\nCONDUCTOR:\n" + "\n".join([f"  {k}: ({float(v[0]):.3f}, {float(v[1]):.3f}, {float(v[2]):.3f})" for k, v in nodos_cond.items()])
            if nodos_guard:
                nodos_txt += "\n\nGUARDIA:\n" + "\n".join([f"  {k}: ({float(v[0]):.3f}, {float(v[1]):.3f}, {float(v[2]):.3f})" for k, v in nodos_guard.items()])
            if nodos_gen:
                nodos_txt += "\n\nGENERAL:\n" + "\n".join([f"  {k}: ({float(v[0]):.3f}, {float(v[1]):.3f}, {float(v[2]):.3f})" for k, v in nodos_gen.items()])
            if nodos_viento:
                nodos_txt += "\n\nVIENTO:\n" + "\n".join([f"  {k}: ({float(v[0]):.3f}, {float(v[1]):.3f}, {float(v[2]):.3f})" for k, v in nodos_viento.items()])
            
            # Parámetros dimensionantes
            param_dim_txt = (
                f"theta_max: {float(theta_max):.2f}°\n" +
                f"Lk: {estructura_actual.get('Lk', 0):.2f} m\n" +
                f"Coeficiente k: {float(coeficiente_k):.3f}\n" +
                f"Coeficiente Ka (altura): {float(Ka):.3f}"
            )
            
            # Distancias
            dist_txt = (
                f"D_fases: {float(D_fases):.3f} m\n" +
                f"Dhg: {float(Dhg):.3f} m\n" +
                f"s_estructura: {float(s_estructura):.3f} m\n" +
                f"a: {float(a):.3f} m\n" +
                f"b: {float(b):.3f} m\n" +
                f"Altura base eléctrica: {float(altura_base_electrica):.3f} m"
            )
            
            output = [
                dbc.Alert("GEOMETRIA COMPLETADA: {} nodos creados".format(len(nodes_key)), color="success", className="mb-3"),
                
                html.H6(flechas_txt, className="mb-3"),
                
                html.H5("PARAMETROS DE DISEÑO", className="mb-2 mt-4"),
                html.Pre(params_txt, style={"backgroundColor": "#1e1e1e", "color": "#d4d4d4", "padding": "10px", "borderRadius": "5px", "fontSize": "0.9rem"}),
                
                html.H5("DIMENSIONES DE ESTRUCTURA", className="mb-2 mt-4"),
                html.Pre(dims_txt, style={"backgroundColor": "#1e1e1e", "color": "#d4d4d4", "padding": "10px", "borderRadius": "5px", "fontSize": "0.9rem"}),
                
                html.H5("NODOS ESTRUCTURALES ({} nodos)".format(len(nodes_key)), className="mb-2 mt-4"),
                html.Pre(nodos_txt, style={"backgroundColor": "#1e1e1e", "color": "#d4d4d4", "padding": "10px", "borderRadius": "5px", "fontSize": "0.85rem"}),
            ]
            
            output.extend([
                html.H5("PARAMETROS DIMENSIONANTES", className="mb-2 mt-4"),
                html.Pre(param_dim_txt, style={"backgroundColor": "#1e1e1e", "color": "#d4d4d4", "padding": "10px", "borderRadius": "5px", "fontSize": "0.9rem"}),
                
                html.H5("DISTANCIAS", className="mb-2 mt-4"),
                html.Pre(dist_txt, style={"backgroundColor": "#1e1e1e", "color": "#d4d4d4", "padding": "10px", "borderRadius": "5px", "fontSize": "0.9rem"})
            ])
            
            # Generar memoria de cálculo
            from utils.memoria_calculo_dge import gen_memoria_calculo_DGE
            memoria_calculo = gen_memoria_calculo_DGE(estructura_geometria)
            
            # Guardar cálculo en cache CON EL NOMBRE CORRECTO
            from utils.calculo_cache import CalculoCache
            # Usar estructura_actual que ya fue recargada al inicio del callback
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            print(f"💾 DEBUG: Guardando cache con nombre: '{nombre_estructura}'")
            CalculoCache.guardar_calculo_dge(
                nombre_estructura,
                estructura_actual,
                dims,
                nodes_key,
                fig_estructura,
                fig_cabezal,
                fig_nodos,
                memoria_calculo,
                estructura_geometria.conexiones
            )
            print(f"✅ Cache DGE guardado: {nombre_estructura}")
            
            # Agregar gráficos usando base64 directo
            from io import BytesIO
            import base64
            
            output.extend([
                html.H5("GRAFICO DE ESTRUCTURA", className="mb-2 mt-4"),
            ])
            
            if fig_estructura:
                buf = BytesIO()
                fig_estructura.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                output.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%', 'maxWidth': '800px'}))
            
            output.append(html.H5("GRAFICO DE CABEZAL", className="mb-2 mt-4"))
            
            if fig_cabezal:
                buf = BytesIO()
                fig_cabezal.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                output.append(html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%', 'maxWidth': '800px'}))
            
            output.append(html.H5("GRAFICO 3D DE NODOS Y COORDENADAS", className="mb-2 mt-4"))
            
            if fig_nodos:
                # fig_nodos es ahora una figura Plotly, no matplotlib
                output.append(dcc.Graph(figure=fig_nodos, config={'displayModeBar': True}, style={'height': '800px'}))
            
            # Agregar memoria de cálculo
            output.extend([
                html.Hr(className="mt-5"),
                dbc.Card([
                    dbc.CardHeader(html.H5("Memoria de Cálculo: Diseño Geométrico de Estructura", className="mb-0")),
                    dbc.CardBody([
                        html.Pre(memoria_calculo, style={
                            "backgroundColor": "#1e1e1e",
                            "color": "#d4d4d4",
                            "padding": "15px",
                            "borderRadius": "5px",
                            "fontSize": "0.85rem",
                            "fontFamily": "'Courier New', monospace",
                            "overflowX": "auto",
                            "whiteSpace": "pre"
                        })
                    ])
                ], className="mt-3")
            ])
            
            return html.Div(output)
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR COMPLETO:\n{error_detail}")
            return dbc.Alert(f"Error en cálculo: {str(e)}", color="danger")
    
    # Importar dcc para Graph
    from dash import dcc
