import plotly.graph_objects as go
import numpy as np
import math
from utils.calculo_cache import CalculoCache
from dash import dcc, html
import dash_bootstrap_components as dbc

class GraficoSulzbergerMonobloque:
    """Generador de gráfico 3D para fundación Sulzberger monobloque"""
    
    def __init__(self, nombre_estructura):
        self.nombre_estructura = nombre_estructura
        self.calculo_guardado = None
        self.parametros = None
        self.resultados = None
        self.todas_hipotesis = []
        
    def cargar_datos_cache(self):
        """Cargar datos desde cache de fundación"""
        self.calculo_guardado = CalculoCache.cargar_calculo_fund(self.nombre_estructura)
        if not self.calculo_guardado:
            raise ValueError(f"No hay cache de fundación para {self.nombre_estructura}")
        
        self.parametros = self.calculo_guardado.get('parametros', {})
        self.resultados = self.calculo_guardado.get('resultados', {})
        
        # Extraer todas las hipótesis
        todas_hipotesis = self.resultados.get('resultados', {}).get('todas_hipotesis', [])
        if not todas_hipotesis:
            raise ValueError("No hay hipótesis disponibles en cache")
        
        self.todas_hipotesis = todas_hipotesis
        return todas_hipotesis
    
    def crear_componente_interactivo(self):
        """Crear componente con selector de hipótesis y gráfico"""
        todas_hipotesis = self.cargar_datos_cache()
        
        # Crear opciones para el selector
        opciones_hipotesis = []
        hipotesis_dimensionante = self.resultados.get('resultados', {}).get('hipotesis_dimensionante', '')
        
        for hip in todas_hipotesis:
            nombre = hip['hipotesis']
            es_dimensionante = nombre == hipotesis_dimensionante
            label = f"{nombre} {'🟡' if es_dimensionante else ''}"
            opciones_hipotesis.append({'label': label, 'value': nombre})
        
        # Valor por defecto: hipótesis dimensionante
        valor_defecto = hipotesis_dimensionante if hipotesis_dimensionante else todas_hipotesis[0]['hipotesis']
        
        # Crear gráfico inicial
        fig_inicial = self._crear_grafico_hipotesis(valor_defecto)
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Seleccionar Hipótesis:"),
                    dcc.Dropdown(
                        id={"type": "selector-hipotesis", "index": self.nombre_estructura},
                        options=opciones_hipotesis,
                        value=valor_defecto,
                        clearable=False
                    )
                ], width=6)
            ], className="mb-3"),
            dcc.Graph(
                id={"type": "grafico-fundacion", "index": self.nombre_estructura},
                figure=fig_inicial,
                config={'displayModeBar': True}
            )
        ])
    
    def _crear_grafico_hipotesis(self, nombre_hipotesis):
        """Crear gráfico 3D para una hipótesis específica"""
        # Buscar la hipótesis seleccionada
        hipotesis_seleccionada = None
        for hip in self.todas_hipotesis:
            if hip['hipotesis'] == nombre_hipotesis:
                hipotesis_seleccionada = hip
                break
        
        if not hipotesis_seleccionada:
            return go.Figure()
        
        # Dimensiones del bloque para esta hipótesis
        a = hipotesis_seleccionada['a']
        b = hipotesis_seleccionada['b'] 
        t = hipotesis_seleccionada['t']
        
        # Parámetros de postes
        parametros_estructura = self.parametros.get('estructura', {})
        n_postes = parametros_estructura.get('n_postes', 1)
        dmed = parametros_estructura.get('dmed', 0.31)
        he = parametros_estructura.get('he', 1.5)
        
        parametros_poste = self.parametros.get('poste', {})
        orientacion = parametros_poste.get('orientacion', 'longitudinal')
        dmol = parametros_poste.get('dmol', 0.60)
        
        fig = go.Figure()
        
        # Crear componentes del gráfico
        self._agregar_bloque_hormigon(fig, a, b, t)
        self._agregar_huecos_postes(fig, a, b, n_postes, dmed, he, orientacion)
        self._agregar_moldes_postes(fig, a, b, n_postes, dmol, he, orientacion)
        self._agregar_plano_terreno(fig, a, b)
        
        # Configurar vista
        self._configurar_vista(fig, a, b, t, nombre_hipotesis)
        
        return fig
    
    def _agregar_moldes_postes(self, fig, a, b, n_postes, dmol, he, orientacion):
        """Agregar cilindros de molde (dmol) sombreados en verde"""
        posiciones = self._calcular_posiciones_postes(a, b, n_postes, orientacion)
        
        for i, (x_pos, y_pos) in enumerate(posiciones):
            self._crear_cilindro_molde(fig, x_pos, y_pos, dmol, he, f'Hueco Molde {i+1}')
    
    def _crear_cilindro_molde(self, fig, x_pos, y_pos, diametro, profundidad, nombre):
        """Crear cilindro de hueco para molde sombreado en verde"""
        radio = diametro / 2
        theta = np.linspace(0, 2*np.pi, 20)
        
        # Coordenadas del cilindro
        x_cil = x_pos + radio * np.cos(theta)
        y_cil = y_pos + radio * np.sin(theta)
        
        # Superficie lateral del cilindro (hueco)
        x_surf = np.outer(x_cil, [1, 1]).flatten()
        y_surf = np.outer(y_cil, [1, 1]).flatten()
        z_surf = np.outer(np.ones(len(theta)), [0, -profundidad]).flatten()
        
        fig.add_trace(go.Scatter3d(
            x=x_surf, y=y_surf, z=z_surf,
            mode='lines',
            line=dict(color='green', width=2),
            name=nombre,
            showlegend=True if nombre.endswith('1') else False
        ))
        
        # Círculo superior (borde del hueco molde)
        fig.add_trace(go.Scatter3d(
            x=np.append(x_cil, x_cil[0]),
            y=np.append(y_cil, y_cil[0]),
            z=np.zeros(len(x_cil) + 1),
            mode='lines',
            line=dict(color='darkgreen', width=3),
            showlegend=False
        ))
    
    def _agregar_bloque_hormigon(self, fig, a, b, t):
        """Agregar bloque principal de hormigón gris transparente"""
        # Vértices del bloque (cara superior en z=0, cara inferior en z=-t)
        x = [-a/2, a/2, a/2, -a/2, -a/2, a/2, a/2, -a/2]
        y = [-b/2, -b/2, b/2, b/2, -b/2, -b/2, b/2, b/2]
        z = [0, 0, 0, 0, -t, -t, -t, -t]
        
        # Caras del bloque
        i = [0, 0, 0, 1, 1, 2, 4, 4, 4, 5, 5, 6]
        j = [1, 3, 4, 2, 5, 3, 5, 6, 7, 6, 1, 7]
        k = [2, 7, 7, 6, 6, 7, 6, 7, 0, 2, 0, 2]
        
        fig.add_trace(go.Mesh3d(
            x=x, y=y, z=z,
            i=i, j=j, k=k,
            color='gray',
            opacity=0.3,
            name='Bloque Hormigón',
            showlegend=True
        ))
    
    def _agregar_huecos_postes(self, fig, a, b, n_postes, dmed, he, orientacion):
        """Agregar huecos cilíndricos para postes empotrados"""
        posiciones = self._calcular_posiciones_postes(a, b, n_postes, orientacion)
        
        for i, (x_pos, y_pos) in enumerate(posiciones):
            self._crear_cilindro_hueco(fig, x_pos, y_pos, dmed, he, f'Poste Empotrado {i+1}')
    
    def _calcular_posiciones_postes(self, a, b, n_postes, orientacion):
        """Calcular posiciones de los huecos según número de postes y orientación"""
        if n_postes == 1:
            return [(0, 0)]  # Centrado
        
        elif n_postes == 2:
            separacion = min(a, b) * 0.3  # 30% de la dimensión menor
            if orientacion == 'transversal':
                return [(-separacion/2, 0), (separacion/2, 0)]  # Separados en X
            else:  # longitudinal
                return [(0, -separacion/2), (0, separacion/2)]  # Separados en Y
        
        elif n_postes == 3:
            # Disposición triangular
            radio = min(a, b) * 0.2
            return [
                (0, radio),                                    # Arriba
                (-radio * math.cos(math.pi/6), -radio/2),     # Abajo izquierda
                (radio * math.cos(math.pi/6), -radio/2)       # Abajo derecha
            ]
        
        else:
            # Para más postes, distribución rectangular
            return [(0, 0)]
    
    def _crear_cilindro_hueco(self, fig, x_pos, y_pos, diametro, profundidad, nombre):
        """Crear cilindro hueco individual"""
        radio = diametro / 2
        theta = np.linspace(0, 2*np.pi, 20)
        
        # Coordenadas del cilindro
        x_cil = x_pos + radio * np.cos(theta)
        y_cil = y_pos + radio * np.sin(theta)
        
        # Superficie lateral del cilindro
        x_surf = np.outer(x_cil, [1, 1]).flatten()
        y_surf = np.outer(y_cil, [1, 1]).flatten()
        z_surf = np.outer(np.ones(len(theta)), [0, -profundidad]).flatten()
        
        fig.add_trace(go.Scatter3d(
            x=x_surf, y=y_surf, z=z_surf,
            mode='lines',
            line=dict(color='darkred', width=2),
            name=nombre,
            showlegend=True if nombre.endswith('1') else False
        ))
        
        # Círculo superior (borde del hueco)
        fig.add_trace(go.Scatter3d(
            x=np.append(x_cil, x_cil[0]),
            y=np.append(y_cil, y_cil[0]),
            z=np.zeros(len(x_cil) + 1),
            mode='lines',
            line=dict(color='darkred', width=3),
            showlegend=False
        ))
    
    def _agregar_plano_terreno(self, fig, a, b):
        """Agregar plano de terreno marrón transparente"""
        # Crear plano extendido más allá del bloque
        extension = max(a, b) * 0.5
        x_terreno = [-a/2 - extension, a/2 + extension, a/2 + extension, -a/2 - extension]
        y_terreno = [-b/2 - extension, -b/2 - extension, b/2 + extension, b/2 + extension]
        z_terreno = [0, 0, 0, 0]
        
        fig.add_trace(go.Mesh3d(
            x=x_terreno, y=y_terreno, z=z_terreno,
            i=[0], j=[1], k=[2],
            color='brown',
            opacity=0.2,
            name='Nivel Terreno',
            showlegend=True
        ))
        
        fig.add_trace(go.Mesh3d(
            x=x_terreno, y=y_terreno, z=z_terreno,
            i=[0], j=[2], k=[3],
            color='brown',
            opacity=0.2,
            showlegend=False
        ))
    
    def _configurar_vista(self, fig, a, b, t, nombre_hipotesis):
        """Configurar vista 3D y ejes"""
        max_dim = max(a, b, t)
        
        fig.update_layout(
            title=f'Fundación Sulzberger - {nombre_hipotesis}',
            scene=dict(
                xaxis=dict(title='X [m] - Colineal', range=[-max_dim, max_dim]),
                yaxis=dict(title='Y [m] - Transversal', range=[-max_dim, max_dim]),
                zaxis=dict(title='Z [m] - Profundidad', range=[-t*1.2, t*0.3]),
                aspectmode='cube',
                camera=dict(
                    eye=dict(x=1.5, y=-1.5, z=1.2)
                )
            ),
            width=800,
            height=600,
            showlegend=True
        )

def crear_componente_fundacion_3d(nombre_estructura):
    """Función principal para crear componente interactivo de fundación"""
    try:
        grafico = GraficoSulzbergerMonobloque(nombre_estructura)
        return grafico.crear_componente_interactivo()
    except Exception as e:
        print(f"Error creando componente 3D fundación: {e}")
        return html.Div(f"Error: {e}")

    def _agregar_moldes_postes(self, fig, a, b, n_postes, dmol, he, orientacion):
        """Agregar cilindros de molde (dmol) sombreados en verde"""
        posiciones = self._calcular_posiciones_postes(a, b, n_postes, orientacion)
        
        for i, (x_pos, y_pos) in enumerate(posiciones):
            self._crear_cilindro_molde(fig, x_pos, y_pos, dmol, he, f'Hueco Molde {i+1}')
    
    def _crear_cilindro_molde(self, fig, x_pos, y_pos, diametro, profundidad, nombre):
        """Crear cilindro de hueco para molde sombreado en verde"""
        radio = diametro / 2
        theta = np.linspace(0, 2*np.pi, 20)
        
        # Coordenadas del cilindro
        x_cil = x_pos + radio * np.cos(theta)
        y_cil = y_pos + radio * np.sin(theta)
        
        # Superficie lateral del cilindro (hueco)
        x_surf = np.outer(x_cil, [1, 1]).flatten()
        y_surf = np.outer(y_cil, [1, 1]).flatten()
        z_surf = np.outer(np.ones(len(theta)), [0, -profundidad]).flatten()
        
        fig.add_trace(go.Scatter3d(
            x=x_surf, y=y_surf, z=z_surf,
            mode='lines',
            line=dict(color='green', width=2),
            name=nombre,
            showlegend=True if nombre.endswith('1') else False
        ))
        
        # Círculo superior (borde del hueco molde)
        fig.add_trace(go.Scatter3d(
            x=np.append(x_cil, x_cil[0]),
            y=np.append(y_cil, y_cil[0]),
            z=np.zeros(len(x_cil) + 1),
            mode='lines',
            line=dict(color='darkgreen', width=3),
            showlegend=False
        ))