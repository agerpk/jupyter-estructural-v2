"""Controlador de diseño geométrico"""

import dash
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState


def ejecutar_calculo_cmc_automatico(estructura_actual, state):
    """Ejecuta cálculo CMC automáticamente con parámetros de estructura"""
    try:
        # Crear objetos
        resultado_objetos = state.calculo_objetos.crear_todos_objetos(estructura_actual)
        if not resultado_objetos["exito"]:
            return {"exito": False, "mensaje": resultado_objetos["mensaje"]}
        
        # Estados climáticos por defecto
        estados_ids = ["I", "II", "III", "IV", "V"]
        descripciones = ["Tmáx", "Tmín", "Vmáx", "Vmed", "TMA"]
        estados_climaticos = {
            "I": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, "espesor_hielo": 0},
            "II": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0, "espesor_hielo": 0},
            "III": {"temperatura": 10, "descripcion": "Vmáx", "viento_velocidad": estructura_actual.get("Vmax", 38.9), "espesor_hielo": 0},
            "IV": {"temperatura": -5, "descripcion": "Vmed", "viento_velocidad": estructura_actual.get("Vmed", 15.56), "espesor_hielo": estructura_actual.get("t_hielo", 0.01)},
            "V": {"temperatura": 8, "descripcion": "TMA", "viento_velocidad": 0, "espesor_hielo": 0}
        }
        
        # Restricciones por defecto
        restricciones_dict = {
            "conductor": {"tension_max_porcentaje": {"I": 0.25, "II": 0.40, "III": 0.40, "IV": 0.40, "V": 0.25}},
            "guardia": {
                "tension_max_porcentaje": {"I": 0.7, "II": 0.70, "III": 0.70, "IV": 0.7, "V": 0.7},
                "relflecha_max": estructura_actual.get("RELFLECHA_MAX_GUARDIA", 0.95)
            }
        }
        
        # Parámetros de cálculo
        params = {
            "L_vano": estructura_actual.get("L_vano", 400),
            "alpha": estructura_actual.get("alpha", 0),
            "theta": estructura_actual.get("theta", 45),
            "Vmax": estructura_actual.get("Vmax", 38.9),
            "Vmed": estructura_actual.get("Vmed", 15.56),
            "t_hielo": estructura_actual.get("t_hielo", 0.01),
            "exposicion": estructura_actual.get("exposicion", "C"),
            "clase": estructura_actual.get("clase", "C"),
            "Zco": estructura_actual.get("Zco", 13.0),
            "Zcg": estructura_actual.get("Zcg", 13.0),
            "Zca": estructura_actual.get("Zca", 13.0),
            "Zes": estructura_actual.get("Zes", 10.0),
            "Cf_cable": estructura_actual.get("Cf_cable", 1.0),
            "Cf_guardia": estructura_actual.get("Cf_guardia", 1.0),
            "Cf_cadena": estructura_actual.get("Cf_cadena", 0.9),
            "Cf_estructura": estructura_actual.get("Cf_estructura", 0.9),
            "PCADENA": estructura_actual.get("PCADENA", 10.5),
            "SALTO_PORCENTUAL": estructura_actual.get("SALTO_PORCENTUAL", 0.05),
            "PASO_AFINADO": estructura_actual.get("PASO_AFINADO", 0.005),
            "OBJ_CONDUCTOR": estructura_actual.get("OBJ_CONDUCTOR", "FlechaMin"),
            "OBJ_GUARDIA": estructura_actual.get("OBJ_GUARDIA", "TiroMin"),
            "RELFLECHA_MAX_GUARDIA": estructura_actual.get("RELFLECHA_MAX_GUARDIA", 0.95),
            "RELFLECHA_SIN_VIENTO": estructura_actual.get("RELFLECHA_SIN_VIENTO", True)
        }
        
        # Ejecutar cálculo
        resultado = state.calculo_mecanico.calcular(params, estados_climaticos, restricciones_dict)
        
        if resultado["exito"]:
            # Guardar en cache
            from utils.calculo_cache import CalculoCache
            from utils.plot_flechas import crear_grafico_flechas
            
            # Generar gráficos
            fig_combinado, fig_conductor, fig_guardia1, fig_guardia2 = None, None, None, None
            try:
                fig_combinado, fig_conductor, fig_guardia1 = crear_grafico_flechas(
                    state.calculo_mecanico.resultados_conductor,
                    state.calculo_mecanico.resultados_guardia1,
                    params["L_vano"]
                )
            except:
                pass
            
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            CalculoCache.guardar_calculo_cmc(
                nombre_estructura,
                estructura_actual,
                state.calculo_mecanico.resultados_conductor,
                state.calculo_mecanico.resultados_guardia1,
                state.calculo_mecanico.df_cargas_totales,
                fig_combinado,
                fig_conductor,
                fig_guardia1
            )
            return {"exito": True, "mensaje": "Cálculo CMC completado automáticamente"}
        else:
            return {"exito": False, "mensaje": resultado["mensaje"]}
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}


def register_callbacks(app):
    """Registrar callbacks de diseño geométrico"""
    
    state = AppState()
    
    @app.callback(
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
        State("input-altura-min-cable", "value"),
        State("slider-lmen-min-cond", "value"),
        State("slider-lmen-min-guard", "value"),
        State("slider-hadd-geom", "value"),
        State("input-hadd-entre-amarres", "value"),
        State("slider-hadd-hg-geom", "value"),
        State("slider-hadd-lmen-geom", "value"),
        State("slider-ancho-cruceta-geom", "value"),
        State("input-dist-repos-hg", "value"),
        State("switch-hg-centrado", "value"),
        State("switch-autoajustar-lmenhg", "value"),
        prevent_initial_call=True
    )
    def guardar_parametros_geometria(n_clicks, tension, zona, lk, ang_apant, disposicion, terna, cant_hg,
                                     altura_min, lmen_cond, lmen_guard, hadd, hadd_amarres, hadd_hg, hadd_lmen,
                                     ancho_cruceta, dist_repos, hg_centrado, autoajustar):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            parametros = {
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
            }
            
            state.estructura_manager.actualizar_parametros(parametros)
            return True, "Éxito", "Parámetros de geometría guardados", "success", "success"
        except Exception as e:
            return True, "Error", f"Error al guardar: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("output-diseno-geometrico", "children"),
        Input("btn-calcular-geom", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def calcular_diseno_geometrico(n_clicks, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
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
            
            # Guardar en estado
            state.calculo_objetos.estructura_geometria = estructura_geometria
            
            # Listar nodos (imprime info detallada)
            estructura_geometria.listar_nodos()
            
            # Crear mecánica y gráficos
            from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
            from EstructuraAEA_Graficos import EstructuraAEA_Graficos
            from HipotesisMaestro import hipotesis_maestro
            
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
            
            # Guardar en estado
            state.calculo_objetos.estructura_mecanica = estructura_mecanica
            state.calculo_objetos.estructura_graficos = estructura_graficos
            
            # Generar output completo como en notebook
            nodes_key = estructura_geometria.obtener_nodes_key()
            
            # Obtener dimensiones del diccionario dimensiones
            dims = estructura_geometria.dimensiones
            altura_total = dims.get('altura_total', 0)
            h1a = dims.get('h1a', 0)
            h2a = dims.get('h2a', 0)
            lmen = dims.get('lmen', 0)
            lmenhg = dims.get('lmenhg', 0)
            hhg = dims.get('hhg', 0)
            
            # Obtener parámetros de cálculo del diccionario dimensiones
            theta_max = dims.get('theta_max', 0)
            k = dims.get('k', 0)
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
            
            # Nodos por categoría
            nodos_base = {k: v for k, v in nodes_key.items() if k == 'BASE'}
            nodos_cross = {k: v for k, v in nodes_key.items() if k.startswith('CROSS')}
            nodos_cond = {k: v for k, v in nodes_key.items() if k.startswith('C')}
            nodos_guard = {k: v for k, v in nodes_key.items() if k.startswith('HG')}
            nodos_gen = {k: v for k, v in nodes_key.items() if k in ['MEDIO', 'TOP', 'V']}
            
            nodos_txt = "BASE:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_base.items()])
            if nodos_cross:
                nodos_txt += "\n\nCRUCE:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_cross.items()])
            if nodos_cond:
                nodos_txt += "\n\nCONDUCTOR:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_cond.items()])
            if nodos_guard:
                nodos_txt += "\n\nGUARDIA:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_guard.items()])
            if nodos_gen:
                nodos_txt += "\n\nGENERAL:\n" + "\n".join([f"  {k}: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for k, v in nodos_gen.items()])
            
            # Parámetros dimensionantes
            param_dim_txt = (
                f"theta_max: {theta_max:.2f}°\n" +
                f"Lk: {estructura_actual.get('Lk', 0):.2f} m\n" +
                f"Coeficiente k: {k:.3f}\n" +
                f"Coeficiente Ka (altura): {Ka:.3f}"
            )
            
            # Distancias
            dist_txt = (
                f"D_fases: {D_fases:.3f} m\n" +
                f"Dhg: {Dhg:.3f} m\n" +
                f"s_estructura: {s_estructura:.3f} m\n" +
                f"a: {a:.3f} m\n" +
                f"b: {b:.3f} m\n" +
                f"Altura base eléctrica: {altura_base_electrica:.3f} m"
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
            
            # Guardar cálculo en cache
            from utils.calculo_cache import CalculoCache
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            CalculoCache.guardar_calculo_dge(
                nombre_estructura,
                estructura_actual,
                dims,
                nodes_key,
                fig_estructura,
                fig_cabezal,
                memoria_calculo
            )
            
            # Agregar gráficos - convertir matplotlib a plotly
            from dash import dcc
            import plotly.graph_objects as go
            from io import BytesIO
            import base64
            
            if fig_estructura:
                # Convertir figura matplotlib a imagen
                buf = BytesIO()
                fig_estructura.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                output.extend([
                    html.H5("GRAFICO DE ESTRUCTURA", className="mb-2 mt-4"),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%', 'maxWidth': '800px'})
                ])
            
            if fig_cabezal:
                # Convertir figura matplotlib a imagen
                buf = BytesIO()
                fig_cabezal.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                output.extend([
                    html.H5("GRAFICO DE CABEZAL", className="mb-2 mt-4"),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%', 'maxWidth': '800px'})
                ])
            
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
