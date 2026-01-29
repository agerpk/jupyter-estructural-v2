"""Controlador de diseño mecánico"""

import dash
from dash import html, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from models.app_state import AppState
import json


def register_callbacks(app):
    """Registrar callbacks de diseño mecánico"""
    
    state = AppState()
    
    @app.callback(
        Output("modal-cargas-nodos", "is_open"),
        Output("modal-cargas-nodos-contenido", "children"),
        Input("btn-cargas-nodos-dme", "n_clicks"),
        Input("btn-cerrar-modal-cargas-nodos", "n_clicks"),
        State("modal-cargas-nodos", "is_open"),
        prevent_initial_call=True
    )
    def toggle_modal_cargas_nodos(n_abrir, n_cerrar, is_open):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open, dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-cargas-nodos-dme":
            try:
                if not state.calculo_objetos.estructura_geometria:
                    return True, dbc.Alert("Ejecute primero DGE y DME para generar cargas en nodos", color="warning")
                
                from utils.consultar_cargas_nodos import consultar_cargas_todos_nodos
                import pandas as pd
                
                estructura_geometria = state.calculo_objetos.estructura_geometria
                todas_cargas = consultar_cargas_todos_nodos(estructura_geometria)
                
                # Obtener TODOS los nodos (incluyendo los que no tienen cargas)
                todos_nodos = list(estructura_geometria.nodos.keys())
                
                if not todos_nodos:
                    return True, dbc.Alert("No hay nodos en la estructura. Ejecute DGE primero.", color="warning")
                
                # Crear tabla por nodo
                contenido = []
                for nombre_nodo in todos_nodos:
                    nodo = estructura_geometria.nodos[nombre_nodo]
                    
                    # Info del nodo con indicador de editado
                    titulo_nodo = f"Nodo: {nombre_nodo}"
                    if nodo.es_editado:
                        titulo_nodo += " *"
                        titulo_style = {"color": "#FF6B00"}  # Naranja para editados
                    else:
                        titulo_style = {}
                    
                    contenido.append(html.H5(titulo_nodo, className="mt-3 mb-2", style=titulo_style))
                    
                    info_parts = [
                        f"Tipo: {nodo.tipo_nodo} | ",
                        f"Coordenadas: ({nodo.x:.3f}, {nodo.y:.3f}, {nodo.z:.3f}) | ",
                        f"Cable: {nodo.cable_asociado.nombre if nodo.cable_asociado else 'N/A'} | ",
                        f"Rotación Z: {nodo.rotacion_eje_z}°"
                    ]
                    if nodo.es_editado:
                        info_parts.append(" | 🟠 EDITADO")
                    
                    contenido.append(html.P(info_parts, style={"fontSize": "0.9rem", "color": "#666"}))
                    
                    # Tabla de cargas (si existen)
                    if nombre_nodo in todas_cargas and todas_cargas[nombre_nodo]:
                        cargas_hip = todas_cargas[nombre_nodo]
                        datos = []
                        for hip, valores in cargas_hip.items():
                            datos.append({
                                "Hipótesis": hip.split('_')[-2] if len(hip.split('_')) >= 2 else hip,
                                "Fx [daN]": round(valores["fx"], 2),
                                "Fy [daN]": round(valores["fy"], 2),
                                "Fz [daN]": round(valores["fz"], 2),
                                "Mx [daN·m]": round(valores["mx"], 2),
                                "My [daN·m]": round(valores["my"], 2),
                                "Mz [daN·m]": round(valores["mz"], 2)
                            })
                        
                        df = pd.DataFrame(datos)
                        contenido.append(dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, size="sm"))
                    else:
                        contenido.append(dbc.Alert("Sin cargas asignadas. Ejecute DME para calcular cargas.", color="info", className="mb-2"))
                    
                    contenido.append(html.Hr())
                
                return True, html.Div(contenido)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                return True, dbc.Alert(f"Error al consultar cargas: {str(e)}", color="danger")
        
        elif trigger_id == "btn-cerrar-modal-cargas-nodos":
            return False, dash.no_update
        
        return is_open, dash.no_update
    
    # Nota: El manejo del modal de edición de hipótesis se centraliza en
    # `callbacks_minimos_para_editor_hipotesis_vista.py` y en el controlador
    # `hipotesis_controller`. Para evitar callbacks duplicados que rompan la
    # navegación, este hook quedó deshabilitado aquí intencionalmente.
    # Si se necesita, reimplementar en el controlador específico del Editor.


    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Output("hipotesis-actuales", "data"),
        Input("btn-guardar-hipotesis", "n_clicks"),
        State({"type": "hip-desc", "index": ALL}, "value"),
        State({"type": "hip-desc", "index": ALL}, "id"),
        State({"type": "hip-viento-estado", "index": ALL}, "value"),
        State({"type": "hip-viento-dir", "index": ALL}, "value"),
        State({"type": "hip-viento-factor", "index": ALL}, "value"),
        State({"type": "hip-tiro-estado", "index": ALL}, "value"),
        State({"type": "hip-tiro-patron", "index": ALL}, "value"),
        State({"type": "hip-tiro-red-cond", "index": ALL}, "value"),
        State({"type": "hip-tiro-red-guard", "index": ALL}, "value"),
        State({"type": "hip-tiro-factor-cond", "index": ALL}, "value"),
        State({"type": "hip-tiro-factor-guard", "index": ALL}, "value"),
        State({"type": "hip-peso-factor", "index": ALL}, "value"),
        State({"type": "hip-peso-hielo", "index": ALL}, "value"),
        State({"type": "hip-sobrecarga", "index": ALL}, "value"),
        State("estructura-actual", "data"),
        State("hipotesis-actuales", "data"),
        prevent_initial_call=True
    )
    def guardar_hipotesis_modificadas(n_clicks, descs, desc_ids, viento_estados, viento_dirs, viento_factors,
                                      tiro_estados, tiro_patrones, tiro_red_conds, tiro_red_guards,
                                      tiro_factor_conds, tiro_factor_guards, peso_factors, peso_hielos,
                                      sobrecargas, estructura_actual, hipotesis_actuales):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        # Guardado desde DME DESHABILITADO: usar la vista central "Editor de Hipótesis"
        try:
            return True, "Deshabilitado", "La edición/guardado de hipótesis desde DME está deshabilitada. Use la vista 'Editor de Hipótesis' para modificar y guardar hipótesis.", "info", "info", hipotesis_actuales
        except Exception as e:
            import traceback
            traceback.print_exc()
            return True, "Error", f"Error: {str(e)}", "danger", "danger", hipotesis_actuales
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Output("estructura-actual", "data", allow_duplicate=True),
        Input("btn-guardar-params-dme", "n_clicks"),
        State("select-tipo-estructura-dme", "value"),
        State("switch-mostrar-c2", "value"),
        State("switch-reemplazar-titulo", "value"),
        State("switch-hipotesis-a5-dme-15pc-lk-mayor-2-5", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_parametros_mecanica(n_clicks, tipo_estructura, mostrar_c2, reemplazar_titulo, hip_a5_value, estructura_actual):

        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            estructura_actualizada = estructura_actual.copy()
            estructura_actualizada["TIPO_ESTRUCTURA"] = tipo_estructura
            estructura_actualizada["MOSTRAR_C2"] = mostrar_c2
            estructura_actualizada["REEMPLAZAR_TITULO_GRAFICO"] = reemplazar_titulo
            # Guardar nuevo parámetro hipotesis A5
            estructura_actualizada["hipotesis_a5_dme_15pc_si_lk_mayor_2_5"] = hip_a5_value
            
            state.set_estructura_actual(estructura_actualizada)
            
            # También guardar en DB
            if "TITULO" in estructura_actualizada:
                from config.app_config import DATA_DIR
                titulo = estructura_actualizada["TITULO"]
                nombre_archivo = f"{titulo}.estructura.json"
                state.estructura_manager.guardar_estructura(estructura_actualizada, DATA_DIR / nombre_archivo)
            
            return True, "Éxito", "Parámetros de mecánica guardados", "success", "success", estructura_actualizada
        except Exception as e:
            return True, "Error", f"Error al guardar: {str(e)}", "danger", "danger", dash.no_update
    
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
            from controllers.geometria_controller import ejecutar_calculo_cmc_automatico, ejecutar_calculo_dge
            from EstructuraAEA_Geometria import EstructuraAEA_Geometria
            
            # SIEMPRE ejecutar CMC automáticamente (sin gráficos)
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state, generar_plots=False)
            if not resultado_auto["exito"]:
                return dbc.Alert(f"Error en cálculo automático CMC: {resultado_auto['mensaje']}", color="danger")
            
            # SIEMPRE ejecutar DGE automáticamente (sin gráficos)
            resultado_dge = ejecutar_calculo_dge(estructura_actual, state, generar_plots=False)
            if not resultado_dge["exito"]:
                return dbc.Alert(f"Error en cálculo automático DGE: {resultado_dge['mensaje']}", color="danger")
            
            # Crear estructura_mecanica y asignar cargas
            estructura_mecanica = EstructuraAEA_Mecanica(state.calculo_objetos.estructura_geometria)
            
            from utils.hipotesis_manager import HipotesisManager
            datos_hipotesis = HipotesisManager.cargar_hipotesis_activa()
            hipotesis_maestro = {}
            if datos_hipotesis:
                hipotesis_maestro = datos_hipotesis.get('hipotesis_maestro', datos_hipotesis)
            else:
                plantilla_path = "data/hipotesis/plantilla.hipotesis.json"
                try:
                    with open(plantilla_path, 'r', encoding='utf-8') as f:
                        datos_plantilla = json.load(f)
                    hipotesis_maestro = datos_plantilla.get('hipotesis_maestro', datos_plantilla)
                except FileNotFoundError:
                    return dbc.Alert("No se encontró archivo de hipótesis", color="danger")
            
            if hipotesis_maestro:
                ok, msg = HipotesisManager.validar_hipotesis(hipotesis_maestro)
                if not ok:
                    return dbc.Alert(f"Error de validación en la hipótesis: {msg}", color="danger")
            else:
                return dbc.Alert("No se pudo cargar ninguna hipótesis", color="danger")
            
            estructura_mecanica.asignar_cargas_hipotesis(
                state.calculo_mecanico.df_cargas_totales,
                state.calculo_mecanico.resultados_conductor,
                state.calculo_mecanico.resultados_guardia1,
                estructura_actual.get('L_vano'),
                hipotesis_maestro,
                estructura_actual.get('t_hielo'),
                resultados_guardia2=state.calculo_mecanico.resultados_guardia2
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
            estructura_graficos.diagrama_barras_tiros(mostrar_c2=estructura_actual.get('MOSTRAR_C2', False))
            fig_barras = plt.gcf()
            
            # Guardar en cache ANTES de cerrar figuras
            from utils.calculo_cache import CalculoCache
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')


            CalculoCache.guardar_calculo_dme(
                nombre_estructura,
                estructura_actual,
                df_reacciones,
                fig_polar,
                fig_barras
            )
            
            # Cerrar figuras DESPUÉS de guardar
            plt.close(fig_polar)
            plt.close(fig_barras)
            
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

            # Nota: indicar en el resumen ejecutivo si A5 aplicó reducción 15% (Lk>2.5 y parámetro activo)
            try:
                hip_aplicadas = getattr(estructura_mecanica, 'hipotesis_a5_aplico_15pc', [])
                if hip_aplicadas:
                    hip_unicas = sorted(set(hip_aplicadas))
                    hip_str = ", ".join(hip_unicas)
                    resumen_txt += (
                        "\n\n💡 Nota: Hipótesis A5 - reducción conductor aplicada = 15% (Lk > 2.5 m)"
                        + (f" — {hip_str}" if hip_str else "")
                    )
            except Exception:
                pass
            
            # Generar output
            output = [
                dbc.Alert(f"REACCIONES Y TIROS EN CIMA COMPLETADO: {len(df_reacciones)} hipótesis procesadas", color="success", className="mb-3"),
                
                html.H5("RESUMEN", className="mb-2 mt-4"),
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
