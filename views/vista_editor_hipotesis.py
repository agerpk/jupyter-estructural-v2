"""Vista para el Editor de Hipótesis"""
from dash import html, dcc
import dash_bootstrap_components as dbc
from controllers.hipotesis_controller import listar_hipotesis
from components.editor_hipotesis import crear_modal_editor_hipotesis


def crear_vista_editor_hipotesis():
    hip_list = listar_hipotesis()

    # Lista de hipótesis
    items = []
    for h in hip_list:
        items.append(dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True))

    layout = dbc.Container([
        dbc.Row([
            dbc.Col([html.H3("Editor de Hipótesis"), html.P("Gestiona hipótesis, actívalas, impórtalas o expórtalas.")], md=12)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.H6("Hipótesis disponibles"),
                dbc.ListGroup(items, id="hip-list", style={"maxHeight": "60vh", "overflowY": "auto"})
            ], md=4),
            dbc.Col([
                html.H6("Acciones"),
                dbc.Button("Activar", id="btn-activar-hip", color="primary", className="me-2"),
                dcc.Upload(id='upload-hipotesis', children=dbc.Button("Importar", color="secondary"), multiple=False),
                dbc.Button("Editar", id="btn-editar-hip", color="info", className="ms-2"),
                html.Div(id="hip-detalle", className="mt-3"),
                dcc.Store(id="hip-seleccionada")
            ], md=8)
        ]),

        # Modal editor (se abrirá y cargará según selección)
        crear_modal_editor_hipotesis('default', {})
    ], fluid=True)

    return layout