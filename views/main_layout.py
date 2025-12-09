"""Layout principal de la aplicación"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from components.menu import (
    crear_menu_archivo, 
    crear_menu_editar,
    crear_menu_calcular,
    crear_modal_cargar_db, 
    crear_modal_guardar_como,
    crear_modal_guardar_plantilla,
    crear_modal_nueva_estructura
)
from components.vista_home import crear_vista_home
from models.app_state import AppState
from config.app_config import TOAST_DURATION


def crear_layout():
    """Crear el layout principal de la aplicación"""
    
    state = AppState()
    
    return html.Div([
        # Almacenamiento de estado
        dcc.Store(id="estructura-actual", data=state.cargar_estructura_actual()),
        dcc.Store(id="estructuras-disponibles", data=state.estructura_manager.listar_estructuras()),
        
        # Barra de navegación superior
        dbc.Navbar(
            dbc.Container([
                # Logo y botón INICIO
                dbc.Row([
                    dbc.Col(html.I(className="fas fa-bolt fa-2x text-warning"), width="auto"),
                    dbc.Col(
                        dbc.Button(
                            "INICIO",
                            id="btn-inicio",
                            color="link",
                            className="text-white fw-bold",
                            style={"textDecoration": "none", "fontSize": "1.25rem"}
                        ),
                        width="auto"
                    ),
                ], align="center", className="g-0"),
                
                # Menús
                dbc.Nav([
                    crear_menu_archivo(),
                    crear_menu_editar(),
                    crear_menu_calcular(),
                ], navbar=True),
                
                # Información de estructura actual
                dbc.Nav([
                    dbc.NavItem(
                        dbc.Badge(
                            id="badge-estructura-actual",
                            color="info",
                            className="ms-2"
                        )
                    ),
                ], navbar=True, className="ms-auto"),
            ]),
            color="dark",
            dark=True,
            className="mb-4",
        ),
        
        # Contenedor principal
        dbc.Container([
            # Modales
            crear_modal_cargar_db(state.estructura_manager.listar_estructuras()),
            crear_modal_guardar_como(""),
            crear_modal_guardar_plantilla(),
            crear_modal_nueva_estructura(),
    
            # Área de contenido principal
            html.Div(id="contenido-principal", children=crear_vista_home()),
        ], fluid=True),
        
        # Toasts para notificaciones
        dbc.Toast(
            id="toast-notificacion",
            header="Notificación",
            is_open=False,
            dismissable=True,
            duration=TOAST_DURATION,
            className="position-fixed top-0 end-0 m-3",
            style={"zIndex": 1000},
        ),
        
        # Componente para cargar archivos
        dcc.Upload(
            id="upload-estructura",
            children=html.Div(["Arrastra o ", html.A("Selecciona un archivo")]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px',
                'display': 'none'
            },
            multiple=False,
            accept='.json,.estructura.json'
        ),
        dcc.Download(id="download-estructura"),
    ])
