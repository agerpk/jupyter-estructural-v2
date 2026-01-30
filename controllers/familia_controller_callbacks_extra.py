# Additional callback: persist changes when user toggles checkboxes in modal
from dash import callback_context
import dash
from dash.dependencies import Input, Output, State
from models.app_state import AppState


def register_callbacks(app):
    @app.callback(
        Output("store-seleccion-secciones-html", "data"),
        Input("chk-secciones-html-familia", "value"),
        State("store-secciones-html-familia-options", "data"),
        prevent_initial_call=True
    )
    def guardar_seleccion_secciones(selected_keys, option_keys):
        if option_keys is None:
            raise dash.exceptions.PreventUpdate
        if selected_keys is None:
            selected_keys = []

        # Construir mapping para opciones visibles en el modal
        mapping = {k: (k in selected_keys) for k in option_keys}

        # Merge con persistencia existente (mantener otras claves no relacionadas)
        state = AppState()
        persisted = state.get_descargar_html_secciones() or {}
        persisted.update(mapping)
        state.set_descargar_html_secciones(persisted)

        return mapping

