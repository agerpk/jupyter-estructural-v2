import dash_bootstrap_components as dbc
from dash import html, dcc


def crear_modal_descargar_html_familia(modal_id="modal-descargar-html-familia"):
    """Crea el modal para seleccionar secciones a descargar."""
    modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Descargar HTML - Seleccionar contenido")),
        dbc.ModalBody([
            html.P("Seleccione las secciones que desea incluir en el HTML descargado."),
            # Checklist dinámico: options y value se actualizarán por callback
            dbc.Checklist(id="chk-secciones-html-familia", options=[], value=[], inline=False),
            html.Div(id="modal-descargar-html-familia-aviso", className="mt-2 text-muted")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="modal-descargar-html-familia-cancel", color="secondary", className="me-2"),
            dbc.Button("Descargar HTML", id="modal-descargar-html-familia-confirm", color="primary")
        ])
    ], id=modal_id, is_open=False, size="xl", scrollable=True, backdrop="static")

    return modal
