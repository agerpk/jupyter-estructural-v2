import dash
from dash import Input, Output, State, callback_context, html
import dash_bootstrap_components as dbc
import pandas as pd
import threading
from utils.Sulzberger import Sulzberger
from utils.calculo_cache import CalculoCache
from utils.view_helpers import ViewHelpers
from models.app_state import AppState
from config.app_config import DATA_DIR

def registrar_callbacks_fundacion(app):
    """Registrar callbacks para la vista de fundación"""
    
    @app.callback(
        [Output("resultados-fundacion", "children"),
         Output("toast-fundacion", "is_open", allow_duplicate=True),
         Output("toast-fundacion", "header", allow_duplicate=True),
         Output("toast-fundacion", "children", allow_duplicate=True),
         Output("toast-fundacion", "icon", allow_duplicate=True),
         Output("toast-fundacion", "color", allow_duplicate=True)],
        [Input("btn-calcular-fundacion", "n_clicks")],
        [State("dropdown-metodo-fundacion", "value"),
         State("dropdown-forma-fundacion", "value"),
         State("dropdown-tipo-base", "value"),
         State("input-n-postes", "value"),
         State("input-orientacion", "value"),
         State("input-t", "value"),
         State("input-a", "value"),
         State("input-b", "value"),
         State("input-fs", "value"),
         State("input-tg-alfa-adm", "value"),
         State("input-t-he-max", "value"),
         State("input-sigma-max-adm", "value"),
         State("input-c", "value"),
         State("input-sigma-adm", "value"),
         State("input-beta", "value"),
         State("input-mu", "value"),
         State("input-dml", "value"),
         State("input-dmf", "value"),
         State("input-dmol", "value"),
         State("input-spc", "value"),
         State("input-pp", "value"),
         State("input-con", "value"),
         State("input-gamma-hor", "value"),
         State("input-gamma-tierra", "value"),
         State("input-cacb", "value"),
         State("input-incremento-calc", "value"),
         State("estructura-actual", "data")],
        prevent_initial_call=True
    )
    def calcular_fundacion(n_clicks, metodo, forma, tipo_base, n_postes, orientacion,
                          t, a, b, fs, tg_alfa_adm, t_he_max, sigma_max_adm,
                          c, sigma_adm, beta, mu, dml, dmf, dmol, spc, pp, con,
                          gamma_hor, gamma_tierra, cacb, incremento, estructura_actual):
        """Ejecutar cálculo de fundación"""
        print(f"🔵 DEBUG: Callback calcular_fundacion ejecutado, n_clicks={n_clicks}")
        
        if not n_clicks:
            print(f"⚠️ DEBUG: n_clicks es {n_clicks}, retornando no_update")
            return dash.no_update, False, "", "", "", ""
        
        try:
            # Recargar estructura actual
            state = AppState()
            estructura_actual = state.estructura_manager.cargar_estructura(DATA_DIR / "actual.estructura.json")
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            print(f"🔵 DEBUG: Iniciando cálculo fundación para {nombre_estructura}")
            
            # Validar método
            if metodo != "sulzberger":
                return dash.no_update, True, "Error", "Método no implementado", "danger", "danger"
            
            # Validar parámetros obligatorios
            if any(param is None for param in [t, a, b, fs, tg_alfa_adm, t_he_max, sigma_max_adm,
                                              c, sigma_adm, beta, mu, gamma_hor, gamma_tierra, cacb, incremento]):
                return dash.no_update, True, "Error", "Faltan parámetros obligatorios", "danger", "danger"
            
            # Obtener parámetros de estructura desde SPH
            print(f"🔍 DEBUG: Obteniendo parámetros desde SPH...")
            parametros_estructura = obtener_parametros_desde_sph(nombre_estructura, estructura_actual)
            
            if not parametros_estructura:
                return dash.no_update, True, "Error", "No se pudieron obtener parámetros de SPH. Verifique que la estructura esté configurada correctamente.", "danger", "danger"
            
            print(f"✅ DEBUG: Parámetros SPH obtenidos: Gp={parametros_estructura['Gp']}, he={parametros_estructura['he']}, hipótesis={len(parametros_estructura.get('hipotesis_fuerzas', []))}")
            
            # Configurar parámetros
            parametros_suelo = {
                'sigma_adm': sigma_adm,
                'gamma_hor': gamma_hor,
                'gamma_tierra': gamma_tierra,
                'mu': mu,
                'C': c,
                'beta': beta
            }
            
            parametros_calculo = {
                'FS': fs,
                'tg_alfa_adm': tg_alfa_adm,
                't_he_max': t_he_max,
                'sigma_max_adm': sigma_max_adm,
                'incremento': incremento,
                'cacb': cacb,
                'max_iteraciones': 10000,  # 10 mil iteraciones
                't_max': 3.0,
                'factor_rombica': 0.5
            }
            
            # Agregar parámetros configurables del poste
            parametros_poste = {
                'dml': dml,
                'dmf': dmf,
                'dmol': dmol,
                'spc': spc,
                'pp': pp,
                'con': con,
                'n_postes': n_postes,
                'orientacion': orientacion,
                'forma': forma
            }
            
            # Crear instancia Sulzberger con parámetros completos
            parametros_estructura_completos = {
                'Gp': parametros_estructura['Gp'],
                'h': parametros_estructura.get('h', 15.0),
                'hl': parametros_estructura.get('hl', 13.5),
                'he': parametros_estructura['he'],
                'dc': parametros_estructura.get('dc', 0.31),
                'n_postes': n_postes,
                'hipotesis_fuerzas': parametros_estructura['hipotesis_fuerzas']
            }
            
            sulzberger = Sulzberger(
                parametros_estructura=parametros_estructura_completos,
                parametros_suelo=parametros_suelo,
                parametros_calculo=parametros_calculo
            )
            
            # Ejecutar cálculo para todas las hipótesis
            resultados = sulzberger.calcular_fundacion_multiples_hipotesis(
                tin=t, ain=a, bin=b, tipo_base=tipo_base
            )
            
            # Generar DataFrame y memoria
            df_resultados = sulzberger.obtener_dataframe_todas_hipotesis()
            memoria_calculo = sulzberger.obtener_memoria_calculo()
            
            print(f"✅ DEBUG: Cálculo completado. Hipótesis dimensionante: {resultados['hipotesis_dimensionante']}")
            print(f"📊 DEBUG: DataFrame generado con {len(df_resultados)} filas")
            print(f"📝 DEBUG: Memoria de cálculo: {len(memoria_calculo)} caracteres")
            
            # Guardar en cache en background
            def guardar_async():
                try:
                    parametros_cache = {
                        'estructura': parametros_estructura,
                        'suelo': parametros_suelo,
                        'calculo': parametros_calculo,
                        'poste': parametros_poste,
                        'dimensiones': {'t': t, 'a': a, 'b': b, 'tipo_base': tipo_base}
                    }
                    
                    resultados_cache = {
                        'resultados': resultados,
                        'dataframe_html': df_resultados.to_json(orient='split'),
                        'memoria_calculo': memoria_calculo
                    }
                    
                    CalculoCache.guardar_calculo_fund(
                        nombre_estructura,
                        parametros_cache,
                        resultados_cache
                    )
                    print(f"💾 DEBUG: Cache guardado para {nombre_estructura}")
                except Exception as e:
                    print(f"❌ ERROR guardando cache: {e}")
            
            threading.Thread(target=guardar_async, daemon=True).start()
            
            # Crear componentes de resultado - SIMPLIFICADO PARA DEBUG
            print(f"🔍 DEBUG: Creando componentes HTML simplificados")
            
            resultados_html = [
                dbc.Alert("Cálculo completado exitosamente", color="success", className="mb-3"),
                html.H4("Resultados del Cálculo de Fundación", className="mt-4 mb-3")
            ]
            
            # Agregar tabla de resultados
            if len(df_resultados) > 0:
                print(f"📊 DEBUG: Agregando tabla directamente con dbc.Table.from_dataframe")
                resultados_html.append(html.H5("Resultados por Hipótesis"))
                resultados_html.append(
                    dbc.Table.from_dataframe(
                        df_resultados,
                        striped=True, bordered=True, hover=True, size="sm"
                    )
                )
            
            # Agregar memoria de cálculo - SIMPLIFICADO
            if memoria_calculo:
                print(f"📋 DEBUG: Agregando memoria de cálculo directamente")
                resultados_html.append(html.Hr(className="mt-4"))
                resultados_html.append(html.H5("Memoria de Cálculo"))
                resultados_html.append(
                    html.Pre(
                        memoria_calculo,
                        style={
                            'backgroundColor': '#1e1e1e',
                            'color': '#d4d4d4',
                            'padding': '10px',
                            'borderRadius': '5px',
                            'fontSize': '0.75rem',
                            'maxHeight': '300px',
                            'overflowY': 'auto',
                            'whiteSpace': 'pre-wrap',
                            'fontFamily': 'monospace'
                        }
                    )
                )
            
            print(f"🔍 DEBUG: Retornando {len(resultados_html)} componentes HTML (SIMPLIFICADOS)")
            for i, comp in enumerate(resultados_html):
                print(f"  Componente {i}: {type(comp).__name__}")
            
            # Crear el Div contenedor
            contenedor = html.Div(resultados_html, id="contenedor-resultados-fundacion")
            print(f"🔍 DEBUG: Contenedor creado: {type(contenedor).__name__} con id={contenedor.id}")
            print(f"🔍 DEBUG: Contenedor children: {len(contenedor.children)} elementos")
            
            print(f"🔍 DEBUG: RETORNO FINAL - Contenedor con {len(contenedor.children)} elementos")
            print(f"🔍 DEBUG: RETORNO FINAL - Toast: is_open=True, header='Éxito', message='Cálculo completado'")
            
            return contenedor, True, "Éxito", "Cálculo de fundación completado", "success", "success"
            
        except Exception as e:
            print(f"❌ ERROR en cálculo fundación: {e}")
            import traceback
            traceback.print_exc()
            return html.Div([
                dbc.Alert(f"Error en cálculo: {str(e)}", color="danger")
            ]), True, "Error", f"Error en cálculo: {str(e)}", "danger", "danger"
    
    @app.callback(
        [Output("resultados-fundacion", "children", allow_duplicate=True),
         Output("toast-fundacion", "is_open", allow_duplicate=True),
         Output("toast-fundacion", "header", allow_duplicate=True),
         Output("toast-fundacion", "children", allow_duplicate=True),
         Output("toast-fundacion", "icon", allow_duplicate=True),
         Output("toast-fundacion", "color", allow_duplicate=True)],
        [Input("btn-cargar-cache-fundacion", "n_clicks")],
        [State("estructura-actual", "data")],
        prevent_initial_call=True
    )
    def cargar_cache_fundacion(n_clicks, estructura_actual):
        """Cargar resultados desde cache"""
        print(f"🔵 DEBUG: Callback cargar_cache_fundacion ejecutado, n_clicks={n_clicks}")
        
        if not n_clicks:
            print(f"⚠️ DEBUG: cargar_cache n_clicks es {n_clicks}, retornando no_update")
            return dash.no_update, False, "", "", "", ""
        
        try:
            # Recargar estructura actual
            state = AppState()
            estructura_actual = state.estructura_manager.cargar_estructura(DATA_DIR / "actual.estructura.json")
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            print(f"🔵 DEBUG: Cargando cache fundación para {nombre_estructura}")
            
            # Cargar desde cache
            calculo_guardado = CalculoCache.cargar_calculo_fund(nombre_estructura)
            
            if not calculo_guardado:
                return dash.no_update, True, "Advertencia", "No hay cache disponible para esta estructura", "warning", "warning"
            
            # Generar resultados desde cache
            from components.vista_fundacion import generar_resultados_fundacion
            resultados_html = generar_resultados_fundacion(calculo_guardado, estructura_actual)
            
            return resultados_html, True, "Cache", "Resultados cargados desde cache", "info", "info"
            
        except Exception as e:
            print(f"❌ ERROR cargando cache fundación: {e}")
            return dash.no_update, True, "Error", f"Error cargando cache: {str(e)}", "danger", "danger"

    @app.callback(
        [Output("toast-fundacion", "is_open", allow_duplicate=True),
         Output("toast-fundacion", "header", allow_duplicate=True),
         Output("toast-fundacion", "children", allow_duplicate=True),
         Output("toast-fundacion", "icon", allow_duplicate=True),
         Output("toast-fundacion", "color", allow_duplicate=True)],
        [Input("btn-guardar-fundacion", "n_clicks")],
        [State("dropdown-metodo-fundacion", "value"),
         State("dropdown-forma-fundacion", "value"),
         State("dropdown-tipo-base", "value"),
         State("input-t", "value"),
         State("input-a", "value"),
         State("input-b", "value"),
         State("input-fs", "value"),
         State("input-tg-alfa-adm", "value"),
         State("input-t-he-max", "value"),
         State("input-sigma-max-adm", "value"),
         State("input-c", "value"),
         State("input-sigma-adm", "value"),
         State("input-beta", "value"),
         State("input-mu", "value"),
         State("input-dml", "value"),
         State("input-dmf", "value"),
         State("input-dmol", "value"),
         State("input-spc", "value"),
         State("input-pp", "value"),
         State("input-con", "value"),
         State("input-gamma-hor", "value"),
         State("input-gamma-tierra", "value"),
         State("input-cacb", "value"),
         State("input-incremento-calc", "value"),
         State("estructura-actual", "data")],
        prevent_initial_call=True
    )
    def guardar_parametros_fundacion(n_clicks, metodo, forma, tipo_base, t, a, b, fs, tg_alfa_adm, 
                                    t_he_max, sigma_max_adm, c, sigma_adm, beta, mu, dml, dmf, 
                                    dmol, spc, pp, con, gamma_hor, gamma_tierra, cacb, incremento, 
                                    estructura_actual):
        """Guardar parámetros de fundación en archivos de estructura"""
        print(f"🔵 DEBUG: Callback guardar_parametros_fundacion ejecutado, n_clicks={n_clicks}")
        
        if not n_clicks:
            print(f"⚠️ DEBUG: guardar_parametros n_clicks es {n_clicks}, retornando valores por defecto")
            return False, "", "", "", ""
        
        try:
            # Recargar estructura actual
            state = AppState()
            estructura_actual = state.estructura_manager.cargar_estructura(DATA_DIR / "actual.estructura.json")
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            print(f"🔵 DEBUG: Guardando parámetros fundación para {nombre_estructura}")
            
            # Crear objeto con parámetros de fundación
            parametros_fundacion = {
                'metodo': metodo,
                'forma': forma,
                'tipo_base': tipo_base,
                'dimensiones_iniciales': {
                    'tin': t,
                    'ain': a,
                    'bin': b
                },
                'requerimientos': {
                    'fs': fs,
                    'tg_alfa_adm': tg_alfa_adm,
                    't_he_max': t_he_max,
                    'sigma_max_adm': sigma_max_adm
                },
                'datos_tierra': {
                    'c': c,
                    'sigma_adm': sigma_adm,
                    'beta': beta,
                    'mu': mu
                },
                'datos_poste_configurables': {
                    'dml': dml,
                    'dmf': dmf,
                    'dmol': dmol,
                    'spc': spc,
                    'pp': pp,
                    'con': con
                },
                'constantes': {
                    'gamma_hor': gamma_hor,
                    'gamma_tierra': gamma_tierra,
                    'cacb': cacb
                },
                'configuracion_calculo': {
                    'incremento': incremento
                }
            }
            
            # Agregar parámetros a estructura actual
            estructura_actual['fundacion'] = parametros_fundacion
            
            # Guardar en actual.estructura.json
            state.estructura_manager.guardar_estructura(estructura_actual, DATA_DIR / "actual.estructura.json")
            
            # Guardar en archivo específico de la estructura
            archivo_estructura = DATA_DIR / f"{nombre_estructura}.estructura.json"
            if archivo_estructura.exists():
                estructura_especifica = state.estructura_manager.cargar_estructura(archivo_estructura)
                estructura_especifica['fundacion'] = parametros_fundacion
                state.estructura_manager.guardar_estructura(estructura_especifica, archivo_estructura)
            
            print(f"✅ DEBUG: Parámetros fundación guardados en ambos archivos")
            
            return True, "Éxito", "Parámetros de fundación guardados correctamente", "success", "success"
            
        except Exception as e:
            print(f"❌ ERROR guardando parámetros fundación: {e}")
            return True, "Error", f"Error guardando parámetros: {str(e)}", "danger", "danger"

def obtener_parametros_desde_sph(nombre_estructura, estructura_actual):
    """Obtener parámetros de estructura desde SPH (con cálculo encadenado si es necesario)"""
    from utils.calculo_cache import CalculoCache
    
    # Intentar cargar desde cache SPH
    calculo_sph = CalculoCache.cargar_calculo_sph(nombre_estructura)
    
    if calculo_sph:
        # Verificar vigencia del cache
        vigente, _ = CalculoCache.verificar_vigencia(calculo_sph, estructura_actual)
        if vigente:
            print(f"📋 DEBUG: Usando parámetros desde cache SPH válido")
            resultados = calculo_sph.get('resultados', {})
            
            # Obtener hipótesis desde DME (no desde SPH)
            hipotesis_fuerzas = obtener_hipotesis_desde_dme(nombre_estructura, estructura_actual)
            
            return {
                'Gp': resultados.get('peso_total_kg', 4680),
                'he': resultados.get('altura_empotrada_m', 1.5),
                'hipotesis_fuerzas': hipotesis_fuerzas
            }
    
    # Si no hay cache válido, ejecutar SPH automáticamente
    print(f"⚙️ DEBUG: Ejecutando SPH automáticamente (no hay cache válido)...")
    return ejecutar_sph_automatico(nombre_estructura, estructura_actual)

def obtener_hipotesis_desde_dme(nombre_estructura, estructura_actual):
    """Obtener hipótesis de fuerzas desde cache DME"""
    from utils.calculo_cache import CalculoCache
    
    # Cargar desde cache DME
    calculo_dme = CalculoCache.cargar_calculo_dme(nombre_estructura)
    
    if calculo_dme:
        vigente, _ = CalculoCache.verificar_vigencia(calculo_dme, estructura_actual)
        if vigente:
            print(f"📋 DEBUG: Usando hipótesis desde cache DME válido")
            df_reacciones = calculo_dme.get('df_reacciones', {})
            
            print(f"🔍 DEBUG: Claves disponibles en df_reacciones: {list(df_reacciones.keys()) if df_reacciones else 'Vacío'}")
            
            hipotesis_fuerzas = []
            for hipotesis, datos in df_reacciones.items():
                print(f"🔍 DEBUG: Hipótesis {hipotesis}, datos disponibles: {list(datos.keys()) if isinstance(datos, dict) else type(datos)}")
                
                # Usar tiros para X e Y, reacción para Z
                tiro_x = abs(datos.get('Tiro_X_daN', 0))       # Tiro transversal
                tiro_y = abs(datos.get('Tiro_Y_daN', 0))       # Tiro longitudinal
                fuerza_z = datos.get('Reaccion_Fz_daN', 0)     # Fuerza vertical en base (con signo)
                
                print(f"🔍 DEBUG: Fuerzas extraídas - Tiro_x: {tiro_x}, Tiro_y: {tiro_y}, Fz: {fuerza_z}")
                
                hipotesis_fuerzas.append({
                    'hipotesis': hipotesis,
                    'Tiro_x': tiro_x,
                    'Tiro_y': tiro_y,
                    'Tiro_z': fuerza_z
                })
            
            print(f"🔍 DEBUG: Hipótesis extraídas desde DME: {len(hipotesis_fuerzas)} hipótesis")
            return hipotesis_fuerzas
    
    print(f"⚠️ DEBUG: No hay cache DME válido, ejecutando automáticamente...")
    return ejecutar_dme_automatico(nombre_estructura, estructura_actual)

def ejecutar_sph_automatico(nombre_estructura, estructura_actual):
    """Ejecutar SPH automáticamente si no hay cache válido"""
    try:
        # Copiar EXACTAMENTE la lógica completa del controller SPH
        from PostesHormigon import PostesHormigon
        from EstructuraAEA_Geometria import EstructuraAEA_Geometria
        from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
        from HipotesisMaestro_Especial import hipotesis_maestro
        from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
        from models.app_state import AppState
        import pandas as pd
        import io
        import sys
        
        state = AppState()
        
        # Usar parámetros por defecto de la estructura
        forzar_n = estructura_actual.get('FORZAR_N_POSTES', 1)
        orientacion = estructura_actual.get('FORZAR_ORIENTACION', 'No')
        prioridad = estructura_actual.get('PRIORIDAD_DIMENSIONADO', 'altura_libre')
        ancho_cruceta = estructura_actual.get('ANCHO_CRUCETA', 0.3)
        
        # PASO 1: Auto-ejecutar CMC si no existe
        tiene_guardia1 = bool(state.calculo_mecanico.resultados_guardia1)
        tiene_guardia2 = bool(getattr(state.calculo_mecanico, 'resultados_guardia2', None))
        
        if not state.calculo_mecanico.resultados_conductor or not tiene_guardia1:
            calculo_cmc = CalculoCache.cargar_calculo_cmc(nombre_estructura)
            if calculo_cmc:
                vigente, _ = CalculoCache.verificar_vigencia(calculo_cmc, estructura_actual)
                if vigente:
                    state.calculo_mecanico.resultados_conductor = calculo_cmc.get('resultados_conductor', {})
                    state.calculo_mecanico.resultados_guardia1 = calculo_cmc.get('resultados_guardia1', {})
                    if calculo_cmc.get('resultados_guardia2'):
                        state.calculo_mecanico.resultados_guardia2 = calculo_cmc.get('resultados_guardia2', {})
                    if calculo_cmc.get('df_cargas_totales'):
                        state.calculo_mecanico.df_cargas_totales = pd.DataFrame(calculo_cmc['df_cargas_totales'])
                    if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                        state.calculo_objetos.crear_todos_objetos(estructura_actual)
                else:
                    resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                    if not resultado_auto["exito"]:
                        print(f"❌ ERROR en CMC: {resultado_auto['mensaje']}")
                        return None
            else:
                resultado_auto = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                if not resultado_auto["exito"]:
                    print(f"❌ ERROR en CMC: {resultado_auto['mensaje']}")
                    return None
        
        # PASO 2: Auto-ejecutar DGE si no existe
        if not state.calculo_objetos.estructura_geometria:
            if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                state.calculo_objetos.crear_todos_objetos(estructura_actual)
            
            fmax_conductor = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_conductor.values()])
            flechas_guardia = [r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia1.values()]
            if hasattr(state.calculo_mecanico, 'resultados_guardia2') and state.calculo_mecanico.resultados_guardia2:
                flechas_guardia.extend([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia2.values()])
            fmax_guardia = max(flechas_guardia) if flechas_guardia else 0.0
            
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
        
        # PASO 3: Auto-ejecutar DME si no existe
        if not state.calculo_objetos.estructura_mecanica:
            estructura_mecanica = EstructuraAEA_Mecanica(state.calculo_objetos.estructura_geometria)
            # Combinar resultados de guardia para compatibilidad
            resultados_guardia_combinados = state.calculo_mecanico.resultados_guardia1.copy()
            if hasattr(state.calculo_mecanico, 'resultados_guardia2') and state.calculo_mecanico.resultados_guardia2:
                resultados_guardia_combinados.update(state.calculo_mecanico.resultados_guardia2)
            
            estructura_mecanica.asignar_cargas_hipotesis(
                state.calculo_mecanico.df_cargas_totales,
                state.calculo_mecanico.resultados_conductor,
                resultados_guardia_combinados,
                estructura_actual.get('L_vano'),
                hipotesis_maestro,
                estructura_actual.get('t_hielo')
            )
            
            nodes_key = state.calculo_objetos.estructura_geometria.nodes_key
            if "TOP" in nodes_key:
                nodo_cima = "TOP"
            elif "HG1" in nodes_key:
                nodo_cima = "HG1"
            else:
                nodo_cima = max(nodes_key.items(), key=lambda x: x[1][2])[0]
            
            estructura_mecanica.calcular_reacciones_tiros_cima(nodo_apoyo="BASE", nodo_cima=nodo_cima)
            state.calculo_objetos.estructura_mecanica = estructura_mecanica
        
        # PASO 4: Ejecutar SPH
        geometria = state.calculo_objetos.estructura_geometria
        mecanica = state.calculo_objetos.estructura_mecanica
        
        postes = PostesHormigon()
        
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        try:
            resultados = postes.calcular_seleccion_postes(
                geometria=geometria,
                mecanica=mecanica,
                FORZAR_N_POSTES=forzar_n,
                FORZAR_ORIENTACION=orientacion,
                ANCHO_CRUCETA=ancho_cruceta,
                PRIORIDAD_DIMENSIONADO=prioridad
            )
            
            postes.imprimir_desarrollo_seleccion_postes()
            
            desarrollo_texto = buffer.getvalue()
            sys.stdout = old_stdout
            
            # Parsear parámetros de la memoria de cálculo
            import re
            
            # Extraer peso del poste
            peso_match = re.search(r'Peso = (\d+) kg', desarrollo_texto)
            Gp = int(peso_match.group(1)) if peso_match else None
            
            # Extraer altura empotrada
            he_match = re.search(r'Empotramiento final \(He\): ([\d.]+) m', desarrollo_texto)
            he = float(he_match.group(1)) if he_match else None
            
            # Extraer altura libre (aproximada como altura total - he)
            h_total = geometria.h1a + geometria.he if hasattr(geometria, 'h1a') and hasattr(geometria, 'he') else 15.0
            hl = h_total - he if he else 13.5
            
            # Extraer diámetro en cima (aproximado)
            dc = 0.31  # Valor típico, debería extraerse del SPH
            
            # Extraer todas las fuerzas del objeto mecanica
            hipotesis_fuerzas = []
            for nombre_hip, datos in mecanica.resultados_reacciones.items():
                print(f"🔍 DEBUG: Hipótesis {nombre_hip}, claves disponibles: {list(datos.keys())}")
                
                # Usar tiros para X e Y, reacción para Z
                tiro_x = abs(datos.get('Tiro_X_daN', 0))       # Tiro transversal
                tiro_y = abs(datos.get('Tiro_Y_daN', 0))       # Tiro longitudinal
                fuerza_z = datos.get('Reaccion_Fz_daN', 0)     # Fuerza vertical en base (con signo)
                
                print(f"🔍 DEBUG: Fuerzas extraídas - Tiro_x: {tiro_x}, Tiro_y: {tiro_y}, Fz: {fuerza_z}")
                
                hipotesis_fuerzas.append({
                    'hipotesis': nombre_hip,
                    'Tiro_x': tiro_x,
                    'Tiro_y': tiro_y,
                    'Tiro_z': fuerza_z
                })
            
            print(f"🔍 DEBUG: Hipótesis extraídas: {len(hipotesis_fuerzas)} hipótesis")
            for hip in hipotesis_fuerzas[:3]:  # Mostrar primeras 3
                print(f"   {hip['hipotesis']}: Tiro_x={hip['Tiro_x']:.1f}, Tiro_y={hip['Tiro_y']:.1f}, Fz={hip['Tiro_z']:.1f}")
            
            if resultados and Gp and he and hipotesis_fuerzas:
                return {
                    'Gp': Gp,
                    'he': he,
                    'hl': hl,
                    'h': h_total,
                    'dc': dc,
                    'hipotesis_fuerzas': hipotesis_fuerzas
                }
        finally:
            sys.stdout = old_stdout
            
    except Exception as e:
        print(f"❌ ERROR ejecutando SPH automático: {e}")
    
    print(f"❌ ERROR: No se pudo ejecutar SPH automáticamente")
    return None