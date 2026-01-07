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
    
    # Remove automatic callback - only manual button clicks
    # The view will auto-load content on creation
    
    @app.callback(
        Output("output-calcular-todo", "children", allow_duplicate=True),
        Input("btn-cargar-cache-todo", "n_clicks"),
        [State("estructura-actual", "data"),
         State("checklist-calculos", "value")],
        prevent_initial_call=True
    )
    def cargar_desde_cache_manual(n_clicks, estructura_actual, calculos_activos):
        """Carga manual desde cache (solo cuando se presiona el botón)"""
        if not n_clicks or n_clicks == 0:
            raise dash.exceptions.PreventUpdate
        
        print(f"🔄 MANUAL: Cargando desde cache para estructura: {estructura_actual.get('TITULO', 'N/A') if estructura_actual else 'None'}")
        
        # Recargar estructura actual desde archivo
        from config.app_config import DATA_DIR
        try:
            state.set_estructura_actual(estructura_actual)
            ruta_actual = state.get_estructura_actual_path()
            estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
            print(f"📂 MANUAL: Estructura recargada: {estructura_actual.get('TITULO', 'N/A')}")
        except Exception as e:
            print(f"❌ MANUAL: Error recargando estructura: {e}")
        
        from components.vista_calcular_todo import cargar_resultados_modulares
        resultados = cargar_resultados_modulares(estructura_actual, calculos_activos)
        print(f"✅ MANUAL: Retornando {len(resultados)} componentes desde cache")
        return resultados
    
    @app.callback(
        Output("output-calcular-todo", "children"),
        Output("toast-notificacion", "is_open", allow_duplicate=True),
        Output("toast-notificacion", "header", allow_duplicate=True),
        Output("toast-notificacion", "children", allow_duplicate=True),
        Output("toast-notificacion", "icon", allow_duplicate=True),
        Output("toast-notificacion", "color", allow_duplicate=True),
        Input("btn-calcular-todo", "n_clicks"),
        [State("estructura-actual", "data"),
         State("checklist-calculos", "value")],
        prevent_initial_call=True
    )
    def ejecutar_calculo_completo(n_clicks, estructura_actual, calculos_activos):
        """Ejecuta todos los cálculos en secuencia reutilizando lógica de vistas"""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        
        if not calculos_activos:
            calculos_activos = []
        
        # Guardar checkboxes en persistencia
        state.set_calculos_activos(calculos_activos)
        
        print(f"🚀 INICIANDO CÁLCULO COMPLETO para estructura: {estructura_actual.get('TITULO', 'N/A') if estructura_actual else 'None'}")
        print(f"✅ Checkboxes seleccionados: {calculos_activos}")
        print(f"🔍 Cálculos seleccionados: {calculos_activos}")
        
        # Recargar estructura actual desde archivo
        from config.app_config import DATA_DIR
        try:
            state.set_estructura_actual(estructura_actual)
            ruta_actual = state.get_estructura_actual_path()
            estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
            print(f"📂 Estructura recargada: {estructura_actual.get('TITULO', 'N/A')}")
        except Exception as e:
            print(f"❌ Error recargando estructura: {e}")
            return (
                [dbc.Alert(f"Error cargando estructura: {str(e)}", color="danger")],
                True, "Error", f"Error cargando estructura: {str(e)}", "danger", "danger"
            )
        
        from dash import html
        resultados = []
        
        try:
            # Validar dependencias
            if "dge" in calculos_activos and "cmc" not in calculos_activos:
                return (
                    [dbc.Alert("DGE requiere CMC. Active CMC primero.", color="warning")],
                    True, "Advertencia", "DGE requiere CMC", "warning", "warning"
                )
            if "dme" in calculos_activos and "dge" not in calculos_activos:
                return (
                    [dbc.Alert("DME requiere DGE. Active DGE primero.", color="warning")],
                    True, "Advertencia", "DME requiere DGE", "warning", "warning"
                )
            if ("arboles" in calculos_activos or "sph" in calculos_activos) and "dme" not in calculos_activos:
                return (
                    [dbc.Alert("Árboles/SPH requieren DME. Active DME primero.", color="warning")],
                    True, "Advertencia", "Árboles/SPH requieren DME", "warning", "warning"
                )
            if "fundacion" in calculos_activos and "sph" not in calculos_activos:
                return (
                    [dbc.Alert("Fundación requiere SPH. Active SPH primero.", color="warning")],
                    True, "Advertencia", "Fundación requiere SPH", "warning", "warning"
                )
            if "costeo" in calculos_activos and ("sph" not in calculos_activos or "fundacion" not in calculos_activos):
                return (
                    [dbc.Alert("Costeo requiere SPH y Fundación. Active ambos primero.", color="warning")],
                    True, "Advertencia", "Costeo requiere SPH y Fundación", "warning", "warning"
                )
            
            # 1. CMC
            if "cmc" not in calculos_activos:
                print("⏭️ CMC desactivado, saltando...")
            else:
                from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
                from components.vista_calcular_todo import generar_resultados_cmc_lista
                from utils.calculo_cache import CalculoCache
                
                state.cargado_desde_cache = False
                
                print("🔧 Ejecutando CMC...")
                resultados.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
                resultado_cmc = ejecutar_calculo_cmc_automatico(estructura_actual, state)
                if resultado_cmc.get('exito'):
                    print("✅ CMC exitoso, cargando desde cache...")
                    calculo_cmc = CalculoCache.cargar_calculo_cmc(estructura_actual.get('TITULO', 'estructura'))
                    if calculo_cmc:
                        lista_cmc = generar_resultados_cmc_lista(calculo_cmc, estructura_actual, mostrar_alerta_cache=False)
                        resultados.extend(lista_cmc)
                        print(f"✅ CMC: {len(lista_cmc)} componentes agregados")
                    else:
                        print("❌ CMC: No se pudo cargar desde cache")
                else:
                    print(f"❌ CMC falló: {resultado_cmc.get('mensaje')}")
                    resultados.append(dbc.Alert(f"Error CMC: {resultado_cmc.get('mensaje')}", color="danger"))
            
            # 2. DGE
            if "dge" not in calculos_activos:
                print("⏭️ DGE desactivado, saltando...")
            else:
                from controllers.geometria_controller import ejecutar_calculo_dge
                from components.vista_diseno_geometrico import generar_resultados_dge
                
                print("🔧 Ejecutando DGE...")
                resultados.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
                resultado_dge = ejecutar_calculo_dge(estructura_actual, state)
                if resultado_dge.get('exito'):
                    print("✅ DGE exitoso, cargando desde cache...")
                    calculo_dge = CalculoCache.cargar_calculo_dge(estructura_actual.get('TITULO', 'estructura'))
                    if calculo_dge:
                        lista_dge = generar_resultados_dge(calculo_dge, estructura_actual, mostrar_alerta_cache=False)
                        if isinstance(lista_dge, list):
                            resultados.extend(lista_dge)
                            print(f"✅ DGE: {len(lista_dge)} componentes agregados")
                        else:
                            resultados.append(lista_dge)
                            print("✅ DGE: 1 componente agregado")
                    else:
                        print("❌ DGE: No se pudo cargar desde cache")
                else:
                    print(f"❌ DGE falló: {resultado_dge.get('mensaje')}")
                    resultados.append(dbc.Alert(f"Error DGE: {resultado_dge.get('mensaje')}", color="danger"))
            
            # 3. DME
            if "dme" not in calculos_activos:
                print("⏭️ DME desactivado, saltando...")
            else:
                from controllers.ejecutar_calculos import ejecutar_calculo_dme
                from components.vista_diseno_mecanico import generar_resultados_dme
                
                print("🔧 Ejecutando DME...")
                resultados.append(html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"))
                resultado_dme = ejecutar_calculo_dme(estructura_actual, state)
                if resultado_dme.get('exito'):
                    print("✅ DME exitoso, cargando desde cache...")
                    calculo_dme = CalculoCache.cargar_calculo_dme(estructura_actual.get('TITULO', 'estructura'))
                    if calculo_dme:
                        resultados.append(generar_resultados_dme(calculo_dme, estructura_actual, mostrar_alerta_cache=False))
                        print("✅ DME: 1 componente agregado")
                    else:
                        print("❌ DME: No se pudo cargar desde cache")
                else:
                    print(f"❌ DME falló: {resultado_dme.get('mensaje')}")
                    resultados.append(dbc.Alert(f"Error DME: {resultado_dme.get('mensaje')}", color="danger"))
            
            # 4. Árboles
            if "arboles" not in calculos_activos:
                print("⏭️ Árboles desactivado, saltando...")
            else:
                from controllers.ejecutar_calculos import ejecutar_calculo_arboles
                from components.vista_arboles_carga import generar_resultados_arboles
                
                print("🔧 Ejecutando Árboles...")
                resultados.append(html.H3("4. ÁRBOLES DE CARGA", className="mt-4"))
                resultado_arboles = ejecutar_calculo_arboles(estructura_actual, state)
                if resultado_arboles.get('exito'):
                    print("✅ Árboles exitoso, cargando desde cache...")
                    calculo_arboles = CalculoCache.cargar_calculo_arboles(estructura_actual.get('TITULO', 'estructura'))
                    if calculo_arboles:
                        resultados.append(html.Div(generar_resultados_arboles(calculo_arboles, estructura_actual, mostrar_alerta_cache=False)))
                        print("✅ Árboles: 1 componente agregado")
                    else:
                        print("❌ Árboles: No se pudo cargar desde cache")
                else:
                    print(f"❌ Árboles falló: {resultado_arboles.get('mensaje')}")
                    resultados.append(dbc.Alert(f"Error Árboles: {resultado_arboles.get('mensaje')}", color="danger"))
            
            # 5. SPH
            if "sph" not in calculos_activos:
                print("⏭️ SPH desactivado, saltando...")
            else:
                from controllers.ejecutar_calculos import ejecutar_calculo_sph
                from components.vista_seleccion_poste import _crear_area_resultados
                
                print("🔧 Ejecutando SPH...")
                resultados.append(html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"))
                resultado_sph = ejecutar_calculo_sph(estructura_actual, state)
                if resultado_sph.get('exito'):
                    print("✅ SPH exitoso, cargando desde cache...")
                    calculo_sph = CalculoCache.cargar_calculo_sph(estructura_actual.get('TITULO', 'estructura'))
                    if calculo_sph:
                        resultados.append(html.Div(_crear_area_resultados(calculo_sph, estructura_actual)))
                        print("✅ SPH: 1 componente agregado")
                    else:
                        print("❌ SPH: No se pudo cargar desde cache")
                else:
                    print(f"❌ SPH falló: {resultado_sph.get('mensaje')}")
                    resultados.append(dbc.Alert(f"Error SPH: {resultado_sph.get('mensaje')}", color="danger"))
            
            # 6. Fundación
            if "fundacion" not in calculos_activos:
                print("⏭️ Fundación desactivado, saltando...")
            else:
                from controllers.ejecutar_calculos import ejecutar_calculo_fundacion
                
                print("🔧 Ejecutando Fundación...")
                resultados.append(html.H3("6. FUNDACIÓN", className="mt-4"))
                resultado_fundacion = ejecutar_calculo_fundacion(estructura_actual, state)
                if resultado_fundacion.get('exito'):
                    print("✅ Fundación exitoso, cargando desde cache...")
                    calculo_fundacion = CalculoCache.cargar_calculo_fund(estructura_actual.get('TITULO', 'estructura'))
                    if calculo_fundacion:
                        from components.vista_fundacion import generar_resultados_fundacion
                        resultado_fund = generar_resultados_fundacion(calculo_fundacion, estructura_actual)
                        if isinstance(resultado_fund, list):
                            resultados.extend(resultado_fund)
                            print(f"✅ Fundación: {len(resultado_fund)} componentes agregados")
                        else:
                            resultados.append(resultado_fund)
                            print("✅ Fundación: 1 componente agregado")
                    else:
                        print("❌ Fundación: No se pudo cargar desde cache")
                else:
                    print(f"❌ Fundación falló: {resultado_fundacion.get('mensaje')}")
                    resultados.append(dbc.Alert(f"Error Fundación: {resultado_fundacion.get('mensaje')}", color="danger"))
            
            # 7. Costeo
            if "costeo" not in calculos_activos:
                print("⏭️ Costeo desactivado, saltando...")
            else:
                from controllers.ejecutar_calculos import ejecutar_calculo_costeo
                
                print("🔧 Ejecutando Costeo...")
                resultados.append(html.H3("7. COSTEO", className="mt-4"))
                resultado_costeo = ejecutar_calculo_costeo(estructura_actual, state)
                if resultado_costeo.get('exito'):
                    print("✅ Costeo exitoso, cargando desde cache...")
                    calculo_costeo = CalculoCache.cargar_calculo_costeo(estructura_actual.get('TITULO', 'estructura'))
                    if calculo_costeo:
                        from components.vista_costeo import generar_resultados_costeo
                        resultado_cost = generar_resultados_costeo(calculo_costeo, estructura_actual)
                        if isinstance(resultado_cost, list):
                            resultados.extend(resultado_cost)
                            print(f"✅ Costeo: {len(resultado_cost)} componentes agregados")
                        else:
                            resultados.append(resultado_cost)
                            print("✅ Costeo: 1 componente agregado")
                    else:
                        print("❌ Costeo: No se pudo cargar desde cache")
                else:
                    print(f"❌ Costeo falló: {resultado_costeo.get('mensaje')}")
                    resultados.append(dbc.Alert(f"Error Costeo: {resultado_costeo.get('mensaje')}", color="danger"))
            
            print(f"✅ CÁLCULO COMPLETO FINALIZADO - Retornando {len(resultados)} componentes")
            resultado_final = (
                resultados,
                True, "Éxito", "Cálculo completo finalizado", "success", "success"
            )
            print(f"✅ RETORNANDO {len(resultados)} componentes al callback")
            return resultado_final
            
        except Exception as e:
            import traceback
            error_msg = f"Error en cálculo completo: {str(e)}"
            print(f"❌ ERROR EN CÁLCULO COMPLETO: {traceback.format_exc()}")
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
