"""Controlador de diseño geométrico"""

import dash
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc
from models.app_state import AppState


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
        State("input-ang-apantallamiento", "value"),
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
            
            # Verificar que existen objetos de cálculo
            if not state.calculo_objetos.cable_conductor or not state.calculo_objetos.cable_guardia:
                return dbc.Alert("Error: Primero debe crear los objetos Cable en Cálculo Mecánico", color="danger")
            
            if not state.calculo_mecanico.resultados_conductor or not state.calculo_mecanico.resultados_guardia:
                return dbc.Alert("Error: Primero debe ejecutar el Cálculo Mecánico de Cables", color="danger")
            
            # Obtener flechas máximas
            fmax_conductor = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_conductor.values()])
            fmax_guardia = max([r["flecha_vertical_m"] for r in state.calculo_mecanico.resultados_guardia.values()])
            
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
            
            # Generar output
            nodes_key = estructura_geometria.obtener_nodes_key()
            altura_total = estructura_geometria.dimensiones.get('altura_total', 0)
            
            output = [
                dbc.Alert("✅ Diseño Geométrico Completado", color="success"),
                html.H5(f"Altura Total: {altura_total:.2f} m", className="mb-3"),
                html.H6("Nodos Estructurales:", className="mb-2"),
                html.Pre("\n".join([f"{k}: ({v[0]:.2f}, {v[1]:.2f}, {v[2]:.2f})" for k, v in nodes_key.items()]))
            ]
            
            return html.Div(output)
            
        except Exception as e:
            return dbc.Alert(f"Error en cálculo: {str(e)}", color="danger")
