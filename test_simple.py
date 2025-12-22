"""Test simple para diagnosticar problema de renderizado"""

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

# Crear app simple
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1("Test Simple"),
    dbc.Button("Test Button", id="test-btn", color="primary"),
    html.Div(id="test-output", children=[
        html.P("Estado inicial")
    ])
])

@app.callback(
    Output("test-output", "children"),
    Input("test-btn", "n_clicks"),
    prevent_initial_call=True
)
def test_callback(n_clicks):
    if not n_clicks:
        return dash.no_update
    
    print(f"Callback ejecutado: {n_clicks} clicks")
    
    # Retornar componentes simples
    return [
        html.H3(f"Test exitoso - Click #{n_clicks}"),
        dbc.Alert("Este es un test simple", color="success"),
        html.P("Si ves esto, el callback funciona correctamente")
    ]

if __name__ == "__main__":
    app.run(debug=False, port=8051)