"""
Controller para borrar cache
"""

from dash import callback, Input, Output, State
from utils.borrar_cache import borrar_cache


@callback(
    Output("modal-borrar-cache", "is_open"),
    Input("menu-borrar-cache", "n_clicks"),
    Input("btn-cancelar-borrar-cache", "n_clicks"),
    State("modal-borrar-cache", "is_open"),
    prevent_initial_call=True
)
def toggle_modal_borrar_cache(n_menu, n_cancelar, is_open):
    """Abrir/cerrar modal de borrar cache"""
    return not is_open


@callback(
    Output("toast-notificacion", "is_open", allow_duplicate=True),
    Output("toast-notificacion", "children", allow_duplicate=True),
    Output("toast-notificacion", "header", allow_duplicate=True),
    Output("toast-notificacion", "color", allow_duplicate=True),
    Output("modal-borrar-cache", "is_open", allow_duplicate=True),
    Input("btn-confirmar-borrar-cache", "n_clicks"),
    prevent_initial_call=True
)
def ejecutar_borrar_cache(n_clicks):
    """Ejecutar borrado de cache"""
    if not n_clicks:
        return False, "", "", "info", False
    
    try:
        archivos_borrados, errores = borrar_cache()
        
        if errores:
            mensaje = f"Cache borrado parcialmente. {archivos_borrados} archivos eliminados. Errores: {', '.join(errores[:3])}"
            return True, mensaje, "Advertencia", "warning", False
        
        mensaje = f"Cache borrado exitosamente. {archivos_borrados} archivos eliminados."
        return True, mensaje, "Éxito", "success", False
        
    except Exception as e:
        return True, f"Error al borrar cache: {str(e)}", "Error", "danger", False
