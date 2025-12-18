"""Controlador para Calcular Todo - Orquestador modular"""

import dash
from dash import Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState


def register_callbacks(app):
    """Registrar callbacks de calcular todo"""
    
    from dash import dcc
    import base64
    from datetime import datetime
    
    state = AppState()
    
    @app.callback(
        Output("output-calcular-todo", "children", allow_duplicate=True),
        Input("btn-cargar-cache-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def cargar_desde_cache(n_clicks, estructura_actual):
        """Carga modular desde cachés individuales"""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        state.cargado_desde_cache = True
        from components.vista_calcular_todo import cargar_resultados_modulares
        return cargar_resultados_modulares(estructura_actual)
    
    @app.callback(
        Output("output-calcular-todo", "children"),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-calcular-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def ejecutar_calculo_completo(n_clicks, estructura_actual):
        """Ejecuta todos los cálculos en secuencia reutilizando lógica de vistas"""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        from dash import html
        resultados = []
        
        try:
            # 1. CMC
            from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
            from components.vista_calcular_todo import generar_resultados_cmc_lista
            from utils.calculo_cache import CalculoCache
            
            state.cargado_desde_cache = False
            
            resultados.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
            resultado_cmc = ejecutar_calculo_cmc_automatico(estructura_actual, state)
            if resultado_cmc.get('exito'):
                calculo_cmc = CalculoCache.cargar_calculo_cmc(estructura_actual.get('TITULO', 'estructura'))
                if calculo_cmc:
                    lista_cmc = generar_resultados_cmc_lista(calculo_cmc, estructura_actual, mostrar_alerta_cache=False)
                    resultados.extend(lista_cmc)
            else:
                resultados.append(dbc.Alert(f"Error CMC: {resultado_cmc.get('mensaje')}", color="danger"))
            
            # 2. DGE
            from controllers.geometria_controller import ejecutar_calculo_dge
            from components.vista_diseno_geometrico import generar_resultados_dge
            
            resultados.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
            resultado_dge = ejecutar_calculo_dge(estructura_actual, state)
            if resultado_dge.get('exito'):
                calculo_dge = CalculoCache.cargar_calculo_dge(estructura_actual.get('TITULO', 'estructura'))
                if calculo_dge:
                    resultados.append(generar_resultados_dge(calculo_dge, estructura_actual, mostrar_alerta_cache=False))
            else:
                resultados.append(dbc.Alert(f"Error DGE: {resultado_dge.get('mensaje')}", color="danger"))
            
            # 3. DME
            from controllers.ejecutar_calculos import ejecutar_calculo_dme
            from components.vista_diseno_mecanico import generar_resultados_dme
            
            resultados.append(html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"))
            resultado_dme = ejecutar_calculo_dme(estructura_actual, state)
            if resultado_dme.get('exito'):
                calculo_dme = CalculoCache.cargar_calculo_dme(estructura_actual.get('TITULO', 'estructura'))
                if calculo_dme:
                    resultados.append(generar_resultados_dme(calculo_dme, estructura_actual, mostrar_alerta_cache=False))
            else:
                resultados.append(dbc.Alert(f"Error DME: {resultado_dme.get('mensaje')}", color="danger"))
            
            # 4. Árboles
            from controllers.ejecutar_calculos import ejecutar_calculo_arboles
            from components.vista_arboles_carga import generar_resultados_arboles
            
            resultados.append(html.H3("4. ÁRBOLES DE CARGA", className="mt-4"))
            resultado_arboles = ejecutar_calculo_arboles(estructura_actual, state)
            if resultado_arboles.get('exito'):
                calculo_arboles = CalculoCache.cargar_calculo_arboles(estructura_actual.get('TITULO', 'estructura'))
                if calculo_arboles:
                    resultados.append(html.Div(generar_resultados_arboles(calculo_arboles, estructura_actual, mostrar_alerta_cache=False)))
            else:
                resultados.append(dbc.Alert(f"Error Árboles: {resultado_arboles.get('mensaje')}", color="danger"))
            
            # 5. SPH
            from controllers.ejecutar_calculos import ejecutar_calculo_sph
            from components.vista_seleccion_poste import _crear_area_resultados
            
            resultados.append(html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"))
            resultado_sph = ejecutar_calculo_sph(estructura_actual, state)
            if resultado_sph.get('exito'):
                calculo_sph = CalculoCache.cargar_calculo_sph(estructura_actual.get('TITULO', 'estructura'))
                if calculo_sph:
                    resultados.append(html.Div(_crear_area_resultados(calculo_sph, estructura_actual)))
            else:
                resultados.append(dbc.Alert(f"Error SPH: {resultado_sph.get('mensaje')}", color="danger"))
            
            return (
                resultados,
                True, "Éxito", "Cálculo completo finalizado", "success", "success"
            )
            
        except Exception as e:
            import traceback
            error_msg = f"Error en cálculo completo: {str(e)}"
            print(traceback.format_exc())
            return (
                [dbc.Alert(error_msg, color="danger")],
                True, "Error", error_msg, "danger", "danger"
            )
    
    @app.callback(
        Output("download-html-todo", "data"),
        Input("btn-descargar-html-todo", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def descargar_html(n_clicks, estructura_actual):
        """Descarga el contenido actual como HTML"""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        try:
            from utils.descargar_html import generar_html_completo
            
            html_completo = generar_html_completo(estructura_actual)
            
            nombre_estructura = estructura_actual.get('TITULO', 'estructura') if estructura_actual else 'estructura'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            return dcc.send_string(html_completo, f"{nombre_estructura}_calculo_completo_{timestamp}.html")
            
        except Exception as e:
            import traceback
            print(f"Error generando HTML: {traceback.format_exc()}")
            raise dash.exceptions.PreventUpdate
