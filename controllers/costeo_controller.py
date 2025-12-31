import dash
from dash import Input, Output, State
import dash_bootstrap_components as dbc
import threading
from utils.calculo_cache import CalculoCache
from utils.calculo_costeo import verificar_cadena_completa_costeo, ejecutar_cadena_completa_costeo, extraer_datos_para_costeo, calcular_costeo_completo
from models.app_state import AppState
from config.app_config import DATA_DIR

def registrar_callbacks_costeo(app):
    """Registrar callbacks para la vista de costeo"""
    
    @app.callback(
        Output("resultados-costeo", "children"),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-calcular-costeo", "n_clicks"),
        State("input-coef-a", "value"),
        State("input-coef-b", "value"),
        State("input-coef-c", "value"),
        State("input-precio-vinculos", "value"),
        State("input-precio-crucetas", "value"),
        State("input-precio-mensulas", "value"),
        State("input-precio-hormigon", "value"),
        State("input-factor-hierro", "value"),
        State("input-precio-estructura", "value"),
        State("input-factor-terreno", "value"),
        State("input-adicional-estructura", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def calcular_costeo(n_clicks, coef_a, coef_b, coef_c, precio_vinculos,
                       precio_crucetas, precio_mensulas,
                       precio_hormigon, factor_hierro, precio_estructura,
                       factor_terreno, adicional_estructura, estructura_actual):
        """Ejecutar cálculo de costeo"""
        
        if not n_clicks:
            return dash.no_update, False, "", "", "", ""
        
        try:
            # Recargar estructura actual
            state = AppState()
            state.set_estructura_actual(estructura_actual)
            ruta_actual = state.get_estructura_actual_path()
            estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            # Validar parámetros obligatorios
            if any(param is None for param in [coef_a, coef_b, coef_c, precio_vinculos,
                                              precio_crucetas, precio_mensulas,
                                              precio_hormigon, factor_hierro, precio_estructura,
                                              factor_terreno, adicional_estructura]):
                return dash.no_update, True, "Error", "Faltan parámetros obligatorios", "danger", "danger"
            
            # Verificar cadena completa de prerequisitos
            cadena_completa = verificar_cadena_completa_costeo(nombre_estructura, estructura_actual)
            
            if not cadena_completa:
                exito_cadena = ejecutar_cadena_completa_costeo(nombre_estructura, estructura_actual)
                if not exito_cadena:
                    return dash.no_update, True, "Error", "No se pudo completar la cadena de cálculos prerequisitos (CMC→DGE→DME→SPH→Fundaciones)", "danger", "danger"
            
            # Extraer datos necesarios
            datos_estructura = extraer_datos_para_costeo(nombre_estructura)
            if not datos_estructura:
                return dash.no_update, True, "Error", "No se pudieron extraer datos de SPH y Fundaciones", "danger", "danger"
            
            # Configurar parámetros de precios
            parametros_precios = {
                'postes': {
                    'coef_a': coef_a,
                    'coef_b': coef_b,
                    'coef_c': coef_c
                },
                'accesorios': {
                    'vinculos': precio_vinculos,
                    'crucetas': precio_crucetas,
                    'mensulas': precio_mensulas
                },
                'fundaciones': {
                    'precio_m3_hormigon': precio_hormigon,
                    'factor_hierro': factor_hierro
                },
                'montaje': {
                    'precio_por_estructura': precio_estructura,
                    'factor_terreno': factor_terreno
                },
                'adicional_estructura': adicional_estructura
            }
            
            # Obtener tensión de la estructura
            tension_kv = estructura_actual.get('TENSION', 220)
            
            # Ejecutar cálculo de costeo
            resultados = calcular_costeo_completo(datos_estructura, parametros_precios, tension_kv)
            
            # Guardar en cache en background
            def guardar_async():
                try:
                    CalculoCache.guardar_calculo_costeo(
                        nombre_estructura,
                        estructura_actual,
                        parametros_precios,
                        resultados
                    )
                except Exception as e:
                    print(f"Error guardando cache costeo: {e}")
            
            threading.Thread(target=guardar_async, daemon=True).start()
            
            # Generar componentes de resultado
            from components.vista_costeo import generar_resultados_costeo
            calculo_guardado = {
                'resultados': resultados,
                'parametros_precios': parametros_precios
            }
            
            resultados_html = generar_resultados_costeo(calculo_guardado, estructura_actual, mostrar_alerta_cache=False)
            
            return resultados_html, True, "Éxito", "Cálculo de costeo completado", "success", "success"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return [dbc.Alert(f"Error en cálculo: {str(e)}", color="danger")], True, "Error", f"Error en cálculo: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("resultados-costeo", "children", allow_duplicate=True),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-cargar-cache-costeo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def cargar_cache_costeo(n_clicks, estructura_actual):
        """Cargar resultados desde cache"""
        if not n_clicks:
            return dash.no_update, False, "", "", "", ""
        
        try:
            nombre_estructura = estructura_actual.get('TITULO', 'estructura') if estructura_actual else 'estructura'
            calculo_guardado = CalculoCache.cargar_calculo_costeo(nombre_estructura)
            
            if not calculo_guardado:
                return dash.no_update, True, "Advertencia", "No hay cache disponible para esta estructura", "warning", "warning"
            
            from components.vista_costeo import generar_resultados_costeo
            resultados_html = generar_resultados_costeo(calculo_guardado, estructura_actual, mostrar_alerta_cache=True)
            
            return resultados_html, True, "Cache", "Resultados cargados desde cache", "info", "info"
        except Exception as e:
            return dash.no_update, True, "Error", f"Error: {str(e)}", "danger", "danger"
    
    @app.callback(
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-guardar-costeo", "n_clicks"),
        State("input-coef-a", "value"),
        State("input-coef-b", "value"),
        State("input-coef-c", "value"),
        State("input-precio-vinculos", "value"),
        State("input-precio-crucetas", "value"),
        State("input-precio-mensulas", "value"),
        State("input-precio-hormigon", "value"),
        State("input-factor-hierro", "value"),
        State("input-precio-estructura", "value"),
        State("input-factor-terreno", "value"),
        State("input-adicional-estructura", "value"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def guardar_parametros_costeo(n_clicks, coef_a, coef_b, coef_c, precio_vinculos,
                                 precio_crucetas, precio_mensulas,
                                 precio_hormigon, factor_hierro, precio_estructura,
                                 factor_terreno, adicional_estructura, estructura_actual):
        """Guardar parámetros de costeo en archivos de estructura"""
        
        if not n_clicks:
            return False, "", "", "", ""
        
        try:
            # Recargar estructura actual
            state = AppState()
            state.set_estructura_actual(estructura_actual)
            ruta_actual = state.get_estructura_actual_path()
            estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
            nombre_estructura = estructura_actual.get('TITULO', 'estructura')
            
            # Crear objeto con parámetros de costeo
            parametros_costeo = {
                'postes': {
                    'coef_a': coef_a,
                    'coef_b': coef_b,
                    'coef_c': coef_c
                },
                'accesorios': {
                    'vinculos': precio_vinculos,
                    'crucetas': precio_crucetas,
                    'mensulas': precio_mensulas
                },
                'fundaciones': {
                    'precio_m3_hormigon': precio_hormigon,
                    'factor_hierro': factor_hierro
                },
                'montaje': {
                    'precio_por_estructura': precio_estructura,
                    'factor_terreno': factor_terreno
                },
                'adicional_estructura': adicional_estructura
            }
            
            # Agregar parámetros a estructura actual
            estructura_actual['costeo'] = parametros_costeo
            
            # Guardar usando el sistema unificado
            state.set_estructura_actual(estructura_actual)
            ruta_actual = state.get_estructura_actual_path()
            state.estructura_manager.guardar_estructura(estructura_actual, ruta_actual)
            
            # Guardar en archivo específico de la estructura
            archivo_estructura = DATA_DIR / f"{nombre_estructura}.estructura.json"
            if archivo_estructura.exists():
                estructura_especifica = state.estructura_manager.cargar_estructura(archivo_estructura)
                estructura_especifica['costeo'] = parametros_costeo
                state.estructura_manager.guardar_estructura(estructura_especifica, archivo_estructura)
            
            return True, "Éxito", "Parámetros de costeo guardados correctamente", "success", "success"
            
        except Exception as e:
            return True, "Error", f"Error guardando parámetros: {str(e)}", "danger", "danger"