"""Controlador de diseño mecánico"""

import dash
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState


def register_callbacks(app):
    """Registrar callbacks de diseño mecánico"""
    
    state = AppState()
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-params-dme", "n_clicks"),
        State("select-tipo-estructura-dme", "value"),
        State("switch-mostrar-c2", "value"),
        State("slider-zoom-cabezal", "value"),
        State("switch-reemplazar-titulo", "value"),
        prevent_initial_call=True
    )
    def guardar_parametros_mecanica(n_clicks, tipo_estructura, mostrar_c2, zoom_cabezal, reemplazar_titulo):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            parametros = {
                "TIPO_ESTRUCTURA": tipo_estructura,
                "MOSTRAR_C2": mostrar_c2,
                "ZOOM_CABEZAL": zoom_cabezal,
                "REEMPLAZAR_TITULO_GRAFICO": reemplazar_titulo
            }
            
            state.estructura_manager.actualizar_parametros(parametros)
            return True, "Éxito", "Parámetros de mecánica guardados", "success", "success"
        except Exception as e:
            return True, "Error", f"Error al guardar: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("output-diseno-mecanico", "children"),
        Input("btn-calcular-dme", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def calcular_diseno_mecanico(n_clicks, estructura_actual):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
            from utils.calculo_cache import CalculoCache
            from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
            from EstructuraAEA_Geometria import EstructuraAEA_Geometria
            
            # Auto-ejecutar CMC si no existe
            if not state.calculo_mecanico.resultados_conductor or not state.calculo_mecanico.resultados_guardia:
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
                
                if calculo_cmc:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_cmc, estructura_actual)
                    if vigente:
                        import pandas as pd
                        state.calculo_mecanico.resultados_conductor = calculo_cmc.get('resultados_conductor', {})
                        state.calculo_mecanico.resultados_guardia = calculo_cmc.get('resultados_guardia', {})
                        if calculo_cmc.get('df_cargas_totales'):
                            state.calculo_mecanico.df_cargas_totales = pd.DataFrame(calculo_cmc['df_cargas_totales'])
                        if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                            state.calculo_objetos.crear_todos_objetos(estructura_actual)
                    else:
                        resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                        if not resultado_auto["exito"]:
                            return dbc.Alert(f"Error en cálculo automático CMC: {resultado_auto['mensaje']}", color="danger")
                else:
                    resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                    if not resultado_auto["exito"]:
                        return dbc.Alert(f"Error en cálculo automático CMC: {resultado_auto['mensaje']}", color="danger")
            
            # Auto-ejecutar DGE si no existe
            if not state.calculo_objetos.estructura_geometria:
                nombre_estructura = estructura_actual.get('TITULO', 'estructura')
                calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
                
                if calculo_dge:
                    vigente, _ = CalculoCache.verificar_vigencia(calculo_dge, estructura_actual)
                    if not vigente:
                        calculo_dge = None
                
                if not calculo_dge:
                    # Asegurar que existen objetos de cable
                    if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                        state.calculo_objetos.crear_todos_objetos(estructura_actual)
                    
                    # Ejecutar DGE automáticamente
                    fmax_conductor = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_conductor.values()])
                    fmax_guardia = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia.values()])
                    
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
                    
                    state.calculo_objetos.estructura_geometria = estructura_geometria
                    state.calculo_objetos.estructura_mecanica = None
                    state.calculo_objetos.estructura_graficos = None
                    
                    # Guardar DGE
                    import matplotlib.pyplot as plt
                    from EstructuraAEA_Graficos import EstructuraAEA_Graficos
                    from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
                    from HipotesisMaestro import hipotesis_maestro
                    
                    estructura_mecanica = EstructuraAEA_Mecanica(estructura_geometria)
                    estructura_mecanica.asignar_cargas_hipotesis(
                        state.calculo_mecanico.df_cargas_totales,
                        state.calculo_mecanico.resultados_conductor,
                        state.calculo_mecanico.resultados_guardia,
                        estructura_actual.get('L_vano'),
                        hipotesis_maestro,
                        estructura_actual.get('t_hielo')
                    )
                    
                    estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica)
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
                    
                    CalculoCache.guardar_calculo_dge(
                        nombre_estructura,
                        estructura_actual,
                        estructura_geometria.dimensiones,
                        estructura_geometria.obtener_nodes_key(),
                        fig_estructura,
                        fig_cabezal
                    )
                    
                    state.calculo_objetos.estructura_mecanica = estructura_mecanica
                    state.calculo_objetos.estructura_graficos = estructura_graficos
            
            # Usar estructura_mecanica del state si existe y es válida, sino crear nueva
            if state.calculo_objetos.estructura_mecanica and state.calculo_objetos.estructura_mecanica.geometria:
                estructura_mecanica = state.calculo_objetos.estructura_mecanica
            else:
                estructura_mecanica = EstructuraAEA_Mecanica(state.calculo_objetos.estructura_geometria)
                
                from HipotesisMaestro import hipotesis_maestro
                estructura_mecanica.asignar_cargas_hipotesis(
                    state.calculo_mecanico.df_cargas_totales,
                    state.calculo_mecanico.resultados_conductor,
                    state.calculo_mecanico.resultados_guardia,
                    estructura_actual.get('L_vano'),
                    hipotesis_maestro,
                    estructura_actual.get('t_hielo')
                )
                
                state.calculo_objetos.estructura_mecanica = estructura_mecanica
            
            # Determinar nodo cima
            nodes_key = state.calculo_objetos.estructura_geometria.nodes_key
            if "TOP" in nodes_key:
                nodo_cima = "TOP"
            elif "HG1" in nodes_key:
                nodo_cima = "HG1"
            else:
                nodo_cima = max(nodes_key.items(), key=lambda x: x[1][2])[0]
            
            # Calcular reacciones
            df_reacciones = state.calculo_objetos.estructura_mecanica.calcular_reacciones_tiros_cima(
                nodo_apoyo="BASE",
                nodo_cima=nodo_cima
            )
            
            # Generar gráficos
            import matplotlib.pyplot as plt
            from EstructuraAEA_Graficos import EstructuraAEA_Graficos
            
            estructura_graficos = EstructuraAEA_Graficos(
                state.calculo_objetos.estructura_geometria,
                state.calculo_objetos.estructura_mecanica
            )
            
            # Diagrama polar
            estructura_graficos.diagrama_polar_tiros()
            fig_polar = plt.gcf()
            
            # Diagrama de barras
            estructura_graficos.diagrama_barras_tiros()
            fig_barras = plt.gcf()
            
            # Guardar en cache con thread separado
            from utils.calculo_cache import CalculoCache
            import threading
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            def guardar_async():
                CalculoCache.guardar_calculo_dme(
                    nombre_estructura,
                    estructura_actual,
                    df_reacciones,
                    fig_polar,
                    fig_barras
                )
            
            threading.Thread(target=guardar_async, daemon=True).start()
            
            # Preparar DataFrame con nombres de hipótesis legibles
            df_display = df_reacciones.copy()
            df_display.index = [idx.split('_')[-2] if len(idx.split('_')) >= 2 else idx for idx in df_display.index]
            df_display.index.name = 'Hipótesis'
            df_display = df_display.reset_index()
            
            # Renombrar columnas para tabla
            df_display = df_display[['Hipótesis', 'Reaccion_Fx_daN', 'Reaccion_Fy_daN', 'Reaccion_Fz_daN', 
                                     'Reaccion_Mx_daN_m', 'Reaccion_My_daN_m', 'Reaccion_Mz_daN_m',
                                     'Tiro_X_daN', 'Tiro_Y_daN', 'Tiro_resultante_daN', 'Angulo_grados']]
            df_display.columns = ['Hipótesis', 'Fx [daN]', 'Fy [daN]', 'Fz [daN]', 'Mx [daN·m]', 'My [daN·m]', 
                                  'Mz [daN·m]', 'Tiro_X [daN]', 'Tiro_Y [daN]', 'Tiro_Res [daN]', 'Ángulo [°]']
            
            # Resumen ejecutivo
            max_tiro = df_reacciones['Tiro_resultante_daN'].max()
            min_fz = df_reacciones['Reaccion_Fz_daN'].min()
            hip_max_tiro = df_reacciones['Tiro_resultante_daN'].idxmax()
            hip_min_fz = df_reacciones['Reaccion_Fz_daN'].idxmin()
            altura_efectiva = df_reacciones['Altura_efectiva_m'].iloc[0]
            nodo_apoyo = df_reacciones['Nodo_apoyo'].iloc[0]
            nodo_cima = df_reacciones['Nodo_cima'].iloc[0]
            
            resumen_txt = (
                f"Estructura: {estructura_actual.get('TENSION')}kV - {estructura_actual.get('TIPO_ESTRUCTURA')}\n" +
                f"Altura efectiva: {altura_efectiva:.2f} m\n" +
                f"Nodo apoyo: {nodo_apoyo}, Nodo cima: {nodo_cima}\n\n" +
                f"🔴 Hipótesis más desfavorable por tiro en cima:\n" +
                f"   {hip_max_tiro}: {max_tiro:.1f} daN\n\n" +
                f"🔴 Hipótesis más desfavorable por carga vertical:\n" +
                f"   {hip_min_fz}: {min_fz:.1f} daN"
            )
            
            # Generar output
            output = [
                dbc.Alert(f"REACCIONES Y TIROS EN CIMA COMPLETADO: {len(df_reacciones)} hipótesis procesadas", color="success", className="mb-3"),
                
                html.H5("RESUMEN EJECUTIVO", className="mb-2 mt-4"),
                html.Pre(resumen_txt, style={"backgroundColor": "#1e1e1e", "color": "#d4d4d4", "padding": "10px", "borderRadius": "5px", "fontSize": "0.9rem"}),
                
                html.H5("TABLA RESUMEN DE REACCIONES Y TIROS", className="mb-2 mt-4"),
                dbc.Table.from_dataframe(df_display, striped=True, bordered=True, hover=True, size="sm"),
            ]
            
            # Agregar gráficos
            from io import BytesIO
            import base64
            import matplotlib.pyplot as plt
            
            if fig_polar:
                buf = BytesIO()
                fig_polar.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                plt.close(fig_polar)
                output.extend([
                    html.H5("DIAGRAMA POLAR DE TIROS", className="mb-2 mt-4"),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%'})
                ])
            
            if fig_barras:
                buf = BytesIO()
                fig_barras.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                plt.close(fig_barras)
                output.extend([
                    html.H5("DIAGRAMA DE BARRAS", className="mb-2 mt-4"),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%'})
                ])
            
            return html.Div(output)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return dbc.Alert(f"Error en cálculo: {str(e)}", color="danger")
