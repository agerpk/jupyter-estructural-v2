"""Vista para Diseño Mecánico de Estructura"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import base64
from pathlib import Path
from config.app_config import DATA_DIR


def generar_resultados_dme(calculo_guardado, estructura_actual):
    """Generar HTML de resultados desde cálculo guardado"""
    try:
        df_reacciones_dict = calculo_guardado.get('df_reacciones', {})
        if not df_reacciones_dict:
            return None
        
        if isinstance(df_reacciones_dict, dict):
            df_reacciones = pd.DataFrame.from_dict(df_reacciones_dict, orient='index')
        else:
            df_reacciones = pd.DataFrame(df_reacciones_dict)
        
        # Verificar que el DataFrame tiene datos y columnas necesarias
        columnas_requeridas = ['Reaccion_Fx_daN', 'Reaccion_Fy_daN', 'Reaccion_Fz_daN', 
                               'Reaccion_Mx_daN_m', 'Reaccion_My_daN_m', 'Reaccion_Mz_daN_m',
                               'Tiro_X_daN', 'Tiro_Y_daN', 'Tiro_resultante_daN', 'Angulo_grados']
        
        if df_reacciones.empty or not all(col in df_reacciones.columns for col in columnas_requeridas):
            return None
        
        hash_params = calculo_guardado.get('hash_parametros')
        
        # Preparar DataFrame con nombres legibles
        df_display = df_reacciones.copy()
        df_display.index = [idx.split('_')[-2] if len(idx.split('_')) >= 2 else idx for idx in df_display.index]
        df_display.index.name = 'Hipótesis'
        df_display = df_display.reset_index()
        
        # Renombrar columnas
        df_display = df_display[['Hipótesis'] + columnas_requeridas]
        df_display.columns = ['Hipótesis', 'Fx [daN]', 'Fy [daN]', 'Fz [daN]', 'Mx [daN·m]', 'My [daN·m]', 
                              'Mz [daN·m]', 'Tiro_X [daN]', 'Tiro_Y [daN]', 'Tiro_Res [daN]', 'Ángulo [°]']
        
        # Resumen ejecutivo
        max_tiro = df_reacciones['Tiro_resultante_daN'].max()
        min_fz = df_reacciones['Reaccion_Fz_daN'].min()
        hip_max_tiro = df_reacciones['Tiro_resultante_daN'].idxmax()
        hip_min_fz = df_reacciones['Reaccion_Fz_daN'].idxmin()
        altura_efectiva = df_reacciones['Altura_efectiva_m'].iloc[0]
        nodo_apoyo = df_reacciones['Nodo_apoyo'].iloc[0]
        nodo_cima = df_reacciones['Nodo_cima'].iloc[0]
        
        resumen_txt = (
            f"Estructura: {estructura_actual.get('TENSION')}kV - {estructura_actual.get('TIPO_ESTRUCTURA')}\n" +
            f"Altura efectiva: {altura_efectiva:.2f} m\n" +
            f"Nodo apoyo: {nodo_apoyo}, Nodo cima: {nodo_cima}\n\n" +
            f"🔴 Hipótesis más desfavorable por tiro en cima:\n" +
            f"   {hip_max_tiro}: {max_tiro:.1f} daN\n\n" +
            f"🔴 Hipótesis más desfavorable por carga vertical:\n" +
            f"   {hip_min_fz}: {min_fz:.1f} daN"
        )
        
        # Tabla de reacciones
        resultados_html = [
            dbc.Alert("Resultados cargados desde cálculo anterior", color="info", className="mb-3"),
            
            html.H5("RESUMEN EJECUTIVO", className="mb-2 mt-4"),
            html.Pre(resumen_txt, style={"backgroundColor": "#1e1e1e", "color": "#d4d4d4", "padding": "10px", "borderRadius": "5px", "fontSize": "0.9rem"}),
            
            html.H5("TABLA RESUMEN DE REACCIONES Y TIROS", className="mb-2 mt-4"),
            dbc.Table.from_dataframe(df_display, striped=True, bordered=True, hover=True, size="sm"),
        ]
        
        # Cargar imágenes guardadas
        if hash_params:
            img_polar = DATA_DIR / f"DME_Polar.{hash_params}.png"
            if img_polar.exists():
                with open(img_polar, 'rb') as f:
                    img_str = base64.b64encode(f.read()).decode()
                resultados_html.extend([
                    html.H5("DIAGRAMA POLAR DE TIROS", className="mb-2 mt-4"),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%', 'maxWidth': '1000px'})
                ])
            
            img_barras = DATA_DIR / f"DME_Barras.{hash_params}.png"
            if img_barras.exists():
                with open(img_barras, 'rb') as f:
                    img_str = base64.b64encode(f.read()).decode()
                resultados_html.extend([
                    html.H5("DIAGRAMA DE BARRAS", className="mb-2 mt-4"),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%', 'maxWidth': '1200px'})
                ])
        
        return html.Div(resultados_html)
    except Exception as e:
        return dbc.Alert(f"Error cargando resultados: {str(e)}", color="warning")


def crear_vista_diseno_mecanico(estructura_actual, calculo_guardado=None):
    """Vista para diseño mecánico con parámetros y cálculo"""
    
    # Generar resultados si hay cálculo guardado
    resultados_previos = None
    if calculo_guardado:
        resultados_previos = generar_resultados_dme(calculo_guardado, estructura_actual)
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Diseño Mecánico de Estructura", className="mb-0")),
            dbc.CardBody([
                html.H5("Parámetros de Configuración", className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("TIPO_ESTRUCTURA", style={"fontSize": "1.125rem"}),
                        dbc.Select(
                            id="select-tipo-estructura-dme",
                            value=estructura_actual.get("TIPO_ESTRUCTURA", "Suspensión Recta"),
                            options=[
                                {"label": "Suspensión Recta", "value": "Suspensión Recta"},
                                {"label": "Suspensión Angular", "value": "Suspensión Angular"},
                                {"label": "Retención / Ret. Angular", "value": "Retención / Ret. Angular"},
                                {"label": "Terminal", "value": "Terminal"}
                            ]
                        ),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("MOSTRAR_C2", style={"fontSize": "1.125rem"}),
                        dbc.Switch(
                            id="switch-mostrar-c2",
                            value=estructura_actual.get("MOSTRAR_C2", False)
                        ),
                    ], md=6),
                ], className="mb-3"),
                
                html.H5("Configuración Gráficos", className="mb-3 mt-4"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("ZOOM_CABEZAL", style={"fontSize": "1.125rem"}),
                        dcc.Slider(
                            id="slider-zoom-cabezal",
                            min=0.5, max=1.5, step=0.05,
                            value=estructura_actual.get("ZOOM_CABEZAL", 0.95),
                            marks={i/10: str(i/10) for i in range(5, 16, 5)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("REEMPLAZAR_TITULO_GRAFICO", style={"fontSize": "1.125rem"}),
                        dbc.Switch(
                            id="switch-reemplazar-titulo",
                            value=estructura_actual.get("REEMPLAZAR_TITULO_GRAFICO", False)
                        ),
                    ], md=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Guardar Parámetros", id="btn-guardar-params-dme", color="primary", size="lg", className="w-100"),
                    ], md=6),
                    dbc.Col([
                        dbc.Button("Calcular Diseño Mecánico", id="btn-calcular-dme", color="success", size="lg", className="w-100"),
                    ], md=6),
                ], className="mb-4"),
                
                html.Hr(),
                
                # Área de resultados
                html.Div(id="output-diseno-mecanico", children=resultados_previos)
            ])
        ])
    ])
