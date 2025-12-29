import dash
from dash import Input, Output, State, callback_context, html
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
         State("input-sigma-adm", "value"),
         State("input-gamma-hor", "value"),
         State("input-gamma-tierra", "value"),
         State("input-mu", "value"),
         State("input-c", "value"),
         State("input-beta", "value"),
         State("input-cacb", "value"),
         State("input-fs", "value"),
         State("input-tg-alfa-adm", "value"),
         State("input-t-he-max", "value"),
         State("input-sigma-max-adm", "value"),
         State("input-incremento", "value"),
         State("input-t-max", "value"),
         State("input-max-iter", "value"),
         State("input-factor-rombica", "value"),
         State("input-t", "value"),
         State("input-gamma-hor", "value"),
         State("input-gamma-tierra", "value"),
         State("input-mu", "value"),
         State("input-t", "value"),
         State("input-a", "value"),
         State("input-b", "value"),
         State("dropdown-tipo-base", "value"),
         State("estructura-actual", "data")],
        prevent_initial_call=True
    )
    def calcular_fundacion(n_clicks, metodo, sigma_adm, gamma_hor, gamma_tierra, mu, c, beta, cacb,
                          fs, tg_alfa_adm, t_he_max, sigma_max_adm, incremento, t_max, max_iter, factor_rombica,
                          t, a, b, tipo_base, estructura_actual):
        """Ejecutar cálculo de fundación"""
        if not n_clicks:
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
            
            # Validar parámetros de suelo y cálculo
            if any(param is None for param in [sigma_adm, gamma_hor, gamma_tierra, mu, c, beta, cacb, fs, tg_alfa_adm, 
                                              t_he_max, sigma_max_adm, incremento, t_max, max_iter, 
                                              factor_rombica, t, a, b]):
                return dash.no_update, True, "Error", "Faltan parámetros obligatorios", "danger", "danger"
            
            # Obtener parámetros de estructura desde SPH
            print(f"🔍 DEBUG: Obteniendo parámetros desde SPH...")
            parametros_estructura = obtener_parametros_desde_sph(nombre_estructura, estructura_actual)
            
            if not parametros_estructura:
                return dash.no_update, True, "Error", "No se pudieron obtener parámetros de SPH", "danger", "danger"
            print(f"✅ DEBUG: Parámetros SPH obtenidos: Gp={parametros_estructura['Gp']}, Ft={parametros_estructura['Ft']}, Fl={parametros_estructura['Fl']}, he={parametros_estructura['he']}")
            
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
                't_max': t_max,
                'max_iteraciones': max_iter,
                'factor_rombica': factor_rombica,
                'cacb': cacb
            }
            
            # Crear instancia Sulzberger
            sulzberger = Sulzberger(
                parametros_estructura=parametros_estructura,
                parametros_suelo=parametros_suelo,
                parametros_calculo=parametros_calculo
            )
            
            # Ejecutar cálculo
            resultados = sulzberger.calcular_fundacion(
                tin=t, ain=a, bin=b, tipo_base=tipo_base
            )
            
            # Generar DataFrame y memoria
            df_resultados = sulzberger.obtener_dataframe_resultados()
            memoria_calculo = sulzberger.obtener_memoria_calculo()
            
            print(f"✅ DEBUG: Cálculo completado en {resultados['iteraciones']} iteraciones")
            
            # Guardar en cache en background
            def guardar_async():
                try:
                    parametros_cache = {
                        'estructura': parametros_estructura,
                        'suelo': parametros_suelo,
                        'calculo': parametros_calculo,
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
            
            # Crear componentes de resultado
            tabla = ViewHelpers.crear_tabla_desde_dataframe(df_resultados, responsive=False)
            memoria_pre = ViewHelpers.crear_pre_output(memoria_calculo)
            
            componentes = [
                ViewHelpers.crear_alerta_cache(mostrar_vigencia=False, vigente=True),
                html.H5("Resultados del Cálculo"),
                tabla,
                html.H5("Memoria de Cálculo", className="mt-4"),
                memoria_pre
            ]
            
            return html.Div(componentes), True, "Éxito", "Cálculo de fundación completado", "success", "success"
            
        except Exception as e:
            print(f"❌ ERROR en cálculo fundación: {e}")
            return dash.no_update, True, "Error", f"Error en cálculo: {str(e)}", "danger", "danger"
    
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
        if not n_clicks:
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
def obtener_parametros_desde_sph(nombre_estructura, estructura_actual):
    """Obtener parámetros de estructura desde SPH (con cálculo encadenado si es necesario)"""
    from utils.calculo_cache import CalculoCache
    
    # Intentar cargar desde cache SPH
    calculo_sph = CalculoCache.cargar_calculo_sph(nombre_estructura)
    
    if calculo_sph:
        # Verificar vigencia del cache
        vigente, _ = CalculoCache.verificar_vigencia(calculo_sph, estructura_actual)
        if vigente:
            print(f"📋 DEBUG: Usando parámetros desde cache SPH")
            resultados = calculo_sph.get('resultados', {})
            return {
                'Gp': resultados.get('peso_total_kg', 4680),
                'Ft': resultados.get('fuerza_transversal_kgf', 1030), 
                'Fl': resultados.get('fuerza_longitudinal_kgf', 1060),
                'he': resultados.get('altura_empotrada_m', 1.5)
            }
    
    # Si no hay cache válido, ejecutar SPH automáticamente
    print(f"⚙️ DEBUG: Ejecutando SPH automáticamente...")
    try:
        from controllers.seleccion_poste_controller import ejecutar_seleccion_poste_automatico
        resultados_sph = ejecutar_seleccion_poste_automatico(estructura_actual)
        
        if resultados_sph:
            return {
                'Gp': resultados_sph.get('peso_total_kg', 4680),
                'Ft': resultados_sph.get('fuerza_transversal_kgf', 1030),
                'Fl': resultados_sph.get('fuerza_longitudinal_kgf', 1060), 
                'he': resultados_sph.get('altura_empotrada_m', 1.5)
            }
    except Exception as e:
        print(f"❌ ERROR ejecutando SPH automático: {e}")
    
    # Valores por defecto si falla todo
    print(f"⚠️ DEBUG: Usando valores por defecto")
    return {
        'Gp': 4680,
        'Ft': 1030, 
        'Fl': 1060,
        'he': 1.5
    }