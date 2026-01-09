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
        dcc.Store(id="hip-seleccionada"),
        dcc.Store(id="hip-modal-datos"),
        dcc.Store(id="hip-modal-tipo"),
        html.Div(id='hip-toasts-container'),

        dbc.Row([
            dbc.Col(html.H3("Editor de Hipótesis"), md=12)
        ], className="mb-2"),

        dbc.Row([
            dbc.Col(
                dbc.Alert(
                    [
                        html.Span("Hipótesis Activa: ", className="fw-bold"),
                        html.Span("Ninguna", id="hip-activa-nombre")
                    ], 
                    id="hip-activa-display",
                    color="success",
                    className="d-flex justify-content-between align-items-center"
                )
            )
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                html.H5("Hipótesis Disponibles"),
                dbc.ListGroup(items, id="hip-list", style={"maxHeight": "50vh", "overflowY": "auto"})
            ], md=12)
        ]),

        dbc.Row([
            dbc.Col(
                dbc.ButtonGroup([
                    dbc.Button("Crear Nueva", id="btn-crear-hip", color="success"),
                    dbc.Button("Editar", id="btn-editar-hip", color="info"),
                    dbc.Button("Activar", id="btn-activar-hip", color="primary"),
                    dcc.Upload(id='upload-hipotesis', children=dbc.Button("Importar", color="secondary"), multiple=False),
                    dbc.Button("Eliminar", id="btn-eliminar-hip", color="danger"),
                ], className="mt-3 w-100"),
                md=12
            )
        ]),

        # Modals
        dbc.Modal(id="modal-editor-hipotesis"),
        html.Div(id="modal-container"), # Contenedor para el modal de edición y creación
        dbc.Modal(
            [
                dbc.ModalHeader("Crear Nueva Hipótesis"),
                dbc.ModalBody([
                    dbc.Label("Nombre para la nueva hipótesis (copiada de la activa):"),
                    dbc.Input(id="crear-hip-nombre-input", placeholder="Ej: Proyecto_ABC", type="text"),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancelar", id="crear-hip-cancelar-btn", className="ms-auto", n_clicks=0),
                    dbc.Button("Guardar", id="crear-hip-guardar-btn", className="ms-2", color="primary", n_clicks=0),
                ]),
            ],
            id="modal-crear-hip",
            is_open=False,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader("Confirmar Eliminación"),
                dbc.ModalBody(id="delete-hip-confirm-body"),
                dbc.ModalFooter([
                    dbc.Button("Cancelar", id="delete-hip-cancelar-btn", className="ms-auto", n_clicks=0),
                    dbc.Button("Eliminar", id="delete-hip-confirmar-btn", color="danger", n_clicks=0),
                ]),
            ],
            id="modal-delete-hip",
            is_open=False,
        ),
    ], fluid=True)

    return layout