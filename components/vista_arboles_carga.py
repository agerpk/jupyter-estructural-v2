"""Vista para Árboles de Carga 2D"""

from dash import html
import dash_bootstrap_components as dbc


def crear_vista_arboles_carga(estructura_actual, calculo_guardado=None):
    """Crear vista de árboles de carga"""
    
    # Cargar resultados previos si existen
    resultados_previos = None
    if calculo_guardado:
        resultados_previos = generar_resultados_arboles(calculo_guardado, estructura_actual)
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("Árboles de Carga 2D", className="mb-4"),
                dbc.Button("← Volver", id={"type": "btn-volver", "index": "arboles-carga"}, 
                          color="secondary", size="sm", className="mb-3"),
            ])
        ]),
        
        # Información
        dbc.Alert([
            html.H5("Generación de Árboles de Carga", className="alert-heading"),
            html.P("Esta herramienta genera diagramas 2D (plano XZ) mostrando las cargas aplicadas en cada hipótesis."),
        ], color="info", className="mb-3"),
        
        # Configuración
        dbc.Card([
            dbc.CardHeader(html.H5("Configuración de Visualización")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Zoom"),
                        dbc.Input(id="param-zoom-arboles", type="number", value=0.5, step=0.1, min=0.1, max=2.0)
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Escala de Flechas"),
                        dbc.Input(id="param-escala-flechas", type="number", value=1.8, step=0.1, min=0.5, max=3.0)
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Grosor de Líneas"),
                        dbc.Input(id="param-grosor-lineas", type="number", value=3.5, step=0.5, min=1.0, max=10.0)
                    ], md=3),
                    dbc.Col([
                        dbc.Checklist(
                            id="param-mostrar-nodos",
                            options=[{"label": "Mostrar etiquetas de nodos", "value": True}],
                            value=[True],
                            switch=True,
                            className="mt-4"
                        )
                    ], md=3),
                ])
            ])
        ], className="mb-3"),
        
        # Botón generar
        dbc.Row([
            dbc.Col([
                dbc.Button("Generar Árboles de Carga", id="btn-generar-arboles", 
                          color="success", size="lg", className="w-100"),
            ])
        ], className="mb-4"),
        
        # Área de resultados
        html.Div(id="resultados-arboles-carga", children=resultados_previos, className="mt-4")
    ])


def generar_resultados_arboles(calculo_guardado, estructura_actual):
    """Generar HTML de resultados desde cálculo guardado"""
    try:
        import base64
        from config.app_config import DATA_DIR
        
        imagenes = calculo_guardado.get('imagenes', [])
        
        if not imagenes:
            return dbc.Alert("No hay imágenes guardadas", color="info")
        
        imagenes_html = [
            dbc.Alert(f"✓ Resultados cargados desde cálculo anterior ({len(imagenes)} imágenes)", 
                     color="info", className="mb-3")
        ]
        
        for img_info in imagenes:
            img_path = DATA_DIR / img_info['nombre']
            
            if not img_path.exists():
                continue
            
            # Leer imagen y convertir a base64
            with open(img_path, 'rb') as f:
                img_str = base64.b64encode(f.read()).decode()
            
            imagenes_html.extend([
                html.H5(f"Hipótesis: {img_info['hipotesis']}", className="mt-4"),
                html.P(f"Archivo: {img_info['nombre']}", className="text-muted small"),
                html.Img(src=f'data:image/png;base64,{img_str}', 
                        style={'width': '100%', 'maxWidth': '1200px'}, 
                        className="mb-4")
            ])
        
        return html.Div(imagenes_html)
        
    except Exception as e:
        return dbc.Alert(f"Error cargando resultados: {str(e)}", color="warning")
