"""Controlador para Editor de Hipótesis: API de alto nivel para listar/cargar/activar"""
from utils.hipotesis_manager import HipotesisManager


def listar_hipotesis():
    """Retorna la lista de archivos de hipótesis disponibles."""
    return HipotesisManager.listar_hipotesis()


def cargar_hipotesis_por_nombre(nombre):
    """Devuelve el contenido del archivo de hipótesis o None si no existe."""
    return HipotesisManager.cargar_hipotesis_por_nombre(nombre)


def establecer_activa(nombre):
    """Establece la hipótesis activa globalmente."""
    return HipotesisManager.establecer_hipotesis_activa(nombre)


def obtener_activa():
    """Retorna el nombre del archivo de hipótesis activa o None."""
    return HipotesisManager.obtener_hipotesis_activa()


def cargar_activa():
    """Carga el contenido de la hipótesis activa y lo retorna o None."""
    return HipotesisManager.cargar_hipotesis_activa()


def validar_hipotesis(hipotesis_maestro):
    """Valida la estructura de un hipotesis_maestro (retorna tuple)."""
    return HipotesisManager.validar_hipotesis(hipotesis_maestro)


def importar_hipotesis(ruta_externa):
    """Importa un JSON de hipótesis desde ruta externa hacia data/hipotesis."""
    return HipotesisManager.importar_hipotesis_desde_archivo(ruta_externa)


# Callbacks mínimos para la vista del Editor de Hipótesis
def register_callbacks(app):
    """Registra callbacks mínimos para la vista del Editor de Hipótesis"""
    from dash.dependencies import Input, Output, State, ALL
    from dash import callback_context, dash
    from dash import html
    import json
    import dash_bootstrap_components as dbc
    from utils.hipotesis_manager import HipotesisManager
    from pathlib import Path
    import base64

    @app.callback(
        Output('hip-list', 'children'),
        Input('menu-editor-hipotesis', 'n_clicks')
    )
    def _llenar_lista(n):
        hip_list = HipotesisManager.listar_hipotesis()
        items = [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in hip_list]
        return items

    @app.callback(
        Output('hip-seleccionada', 'data'),
        Input({'type': 'hip-item', 'name': ALL}, 'n_clicks'),
        State('hip-seleccionada', 'data')
    )
    def _seleccionar(n_clicks_list, current):
        ctx = callback_context
        if not ctx.triggered:
            return current
        prop = ctx.triggered[0]['prop_id'].split('.')[0]
        try:
            obj = json.loads(prop)
            nombre = obj.get('name')
            return nombre
        except Exception:
            return current

    @app.callback(
        Output('hip-detalle', 'children'),
        Input('hip-seleccionada', 'data')
    )
    def _mostrar_detalle(nombre):
        if not nombre:
            return html.Div('Seleccione una hipótesis')
        contenido = HipotesisManager.cargar_hipotesis_por_nombre(nombre.replace('.hipotesis.json',''))
        return html.Pre(json.dumps(contenido, indent=2, ensure_ascii=False))

    @app.callback(
        Output('btn-activar-hip', 'children'),
        Input('btn-activar-hip', 'n_clicks'),
        State('hip-seleccionada', 'data')
    )
    def _activar(n, nombre):
        if not n or not nombre:
            return 'Activar'
        nombre_sin = nombre.replace('.hipotesis.json','')
        HipotesisManager.establecer_hipotesis_activa(nombre_sin)
        return f'Activo: {nombre}'

    @app.callback(
        Output('hip-list', 'children'),
        Input('upload-hipotesis', 'contents'),
        State('upload-hipotesis', 'filename')
    )
    def _importar(contents, filename):
        if not contents or not filename:
            raise dash.exceptions.PreventUpdate
        header, b64 = contents.split(',', 1)
        data = base64.b64decode(b64)
        hip_dir = Path(__file__).parent.parent / 'data' / 'hipotesis'
        hip_dir.mkdir(parents=True, exist_ok=True)
        destino = hip_dir / filename
        destino.write_bytes(data)
        hip_list = HipotesisManager.listar_hipotesis()
        items = [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in hip_list]
        return items


# Placeholder for future callbacks registration (Dash app)
def register_callbacks(app):
    pass