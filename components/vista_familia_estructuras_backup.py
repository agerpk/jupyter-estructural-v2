"""
Vista para gestión de Familias de Estructuras - CALLBACKS DESACTIVADOS
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from typing import Dict, List, Any
import json

def crear_vista_familia_estructuras(familia_actual=None):
    """Crear vista principal de Familias de Estructuras"""
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Familia de Estructuras - En Desarrollo", className="mb-0")),
            dbc.CardBody([
                dbc.Alert([
                    html.H5("Vista en Desarrollo", className="alert-heading"),
                    html.P("Esta vista está siendo desarrollada. Los callbacks han sido desactivados temporalmente para evitar conflictos con la navegación principal."),
                    html.Hr(),
                    html.P("Funcionalidad disponible próximamente.", className="mb-0")
                ], color="info")
            ])
        ])
    ])

# Callbacks desactivados temporalmente
# Los callbacks están comentados para evitar conflictos con la navegación