# Implementación AEE - Análisis Estático de Esfuerzos

## ESTADO DE IMPLEMENTACIÓN

### ✅ COMPLETADO - LISTO PARA TESTEAR
- **Fase 1**: Parámetros en plantilla.estructura.json
- **Fase 2**: Vista Ajustar Parámetros (tabla + panel)
- **Fase 3**: Utility analisis_estatico.py
- **Fase 4**: Vista AEE
- **Fase 5**: Controller AEE
- **Fase 6**: Integración app.py + menú
- **Fase 9 (parcial)**: Cache System (guardar/cargar)

### ⏳ PENDIENTE
- **Fase 7**: Vista Calcular Todo
- **Fase 8**: Familia de Estructuras
- **Fase 10**: Descargar HTML
- **Fase 11**: Testing completo
- **Fase 12**: Optimizaciones

### 📦 ARCHIVOS CREADOS
- `utils/analisis_estatico.py` - Clase AnalizadorEstatico
- `components/vista_analisis_estatico.py` - Vista AEE
- `controllers/aee_controller.py` - Controller con callbacks

### 🔧 ARCHIVOS MODIFICADOS
- `data/plantilla.estructura.json` - Parámetros AEE
- `data/2x220 DTT SAN JORGE PRUEBAS.estructura.json` - Parámetros AEE
- `components/vista_ajuste_parametros.py` - Sección AEE
- `utils/parametros_manager.py` - Metadatos AEE
- `utils/calculo_cache.py` - Métodos guardar/cargar AEE
- `app.py` - Import y registro de aee_controller
- `components/menu.py` - Entrada "Análisis Estático Esfuerzos (AEE)"
- `controllers/navigation_controller.py` - Ruta menu-analisis-estatico

---

# Implementación AEE - Análisis Estático de Esfuerzos

## Resumen Ejecutivo

Nueva feature para análisis estático de estructuras sin propiedades E, I, A. Utiliza numpy para cálculos de esfuerzos MQNT (Momento, Corte, Normal, Torsión) y genera diagramas 2D/3D estáticos (PNG) con escala de colores.

**Unidades:** Todas las unidades en daN y daN.m
**Gráficos:** Individuales, estáticos (PNG), no interactivos
**Fuente de datos:** DataFrames de EstructuraAEA_Mecanica con cargas por hipótesis
**Conexiones:** Usa las mismas conexiones de EstructuraAEA_Geometria (usadas en gráficos de estructura/cabezal)
**Segmentación:** Divide conexiones en elementos para mayor definición en gradientes

## Fase 1: Parámetros en plantilla.estructura.json

### Nuevos parámetros a agregar:

```json
"AnalisisEstaticoEsfuerzos": {
    "GRAFICOS_3D_AEE": true,
    "DIAGRAMAS_ACTIVOS": {
        "M": true,
        "Q": true,
        "N": true,
        "T": true,
        "MRT": true,
        "MFE": true
    },
    "VALORES_REFERENCIA": {
        "M_ref": 1000,
        "N_ref": 5000,
        "V_ref": 500
    },
    "PONDERACION": {
        "w_M": 0.5,
        "w_N": 0.4,
        "w_V": 0.1
    },
    "n_segmentar_conexion_corta": 10,
    "n_segmentar_conexion_larga": 30
}
```

## Fase 2: Vista Ajustar Parámetros

### Modificar: `components/vista_ajustar_parametros.py`

Agregar sección para parámetros AEE:

```python
def crear_seccion_aee(parametros):
    config = parametros.get("AnalisisEstaticoEsfuerzos", {})
    
    return dbc.Card([
        dbc.CardHeader("Análisis Estático de Esfuerzos"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Gráficos 3D"),
                    dbc.Checklist(
                        id="check-graficos-3d-aee",
                        options=[{"label": "Activar", "value": "3D"}],
                        value=["3D"] if config.get("GRAFICOS_3D_AEE") else []
                    )
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Segmentación Conexiones Cortas"),
                    dbc.Input(id="input-n-seg-corta", type="number", 
                             value=config.get("n_segmentar_conexion_corta", 10))
                ], width=6),
                dbc.Col([
                    dbc.Label("Segmentación Conexiones Largas"),
                    dbc.Input(id="input-n-seg-larga", type="number",
                             value=config.get("n_segmentar_conexion_larga", 30))
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Diagramas Activos"),
                    dbc.Checklist(
                        id="check-diagramas-aee",
                        options=[
                            {"label": "Momento (M)", "value": "M"},
                            {"label": "Corte (Q)", "value": "Q"},
                            {"label": "Normal (N)", "value": "N"},
                            {"label": "Torsión (T)", "value": "T"},
                            {"label": "Momento Resultante Total", "value": "MRT"},
                            {"label": "Momento Flector Equivalente", "value": "MFE"}
                        ],
                        value=list(config.get("DIAGRAMAS_ACTIVOS", {}).keys())
                    )
                ])
            ])
        ])
    ])
```

## Fase 3: Nuevo Utility - analisis_estatico.py

### Crear: `utils/analisis_estatico.py`

```python
import numpy as np
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize

class AnalizadorEstatico:
    def __init__(self, estructura_geometria, estructura_mecanica, parametros_aee):
        self.geometria = estructura_geometria
        self.mecanica = estructura_mecanica
        self.parametros = parametros_aee
        self.nodos = estructura_geometria.nodos
        
        # Extraer conexiones desde geometria (mismas que usa EstructuraAEA_Graficos)
        self.conexiones = self._extraer_conexiones_geometria()
        
        # Segmentar conexiones para mayor definición
        self.nodos_segmentados, self.elementos = self._segmentar_conexiones()
        
    def _extraer_conexiones_geometria(self):
        """Extrae conexiones desde EstructuraAEA_Geometria (mismas que gráficos estructura/cabezal)"""
        conexiones = []
        
        # Las conexiones están en geometria.conexiones o geometria.barras
        if hasattr(self.geometria, 'conexiones'):
            conexiones = self.geometria.conexiones
        elif hasattr(self.geometria, 'barras'):
            for barra in self.geometria.barras:
                conexiones.append((barra.nodo_i, barra.nodo_j))
        
        return conexiones
    
    def _segmentar_conexiones(self):
        """Divide conexiones en elementos según su longitud"""
        # Calcular longitudes de todas las conexiones
        longitudes = []
        for nodo_i, nodo_j in self.conexiones:
            pos_i = np.array(self.nodos[nodo_i].coordenadas)
            pos_j = np.array(self.nodos[nodo_j].coordenadas)
            longitud = np.linalg.norm(pos_j - pos_i)
            longitudes.append(longitud)
        
        # Percentil 50 para clasificar cortas/largas
        longitud_mediana = np.median(longitudes)
        
        n_corta = self.parametros.get('n_segmentar_conexion_corta', 10)
        n_larga = self.parametros.get('n_segmentar_conexion_larga', 30)
        
        nodos_segmentados = dict(self.nodos)  # Copiar nodos originales
        elementos = []
        contador_nodo = 0
        
        for idx, (nodo_i, nodo_j) in enumerate(self.conexiones):
            longitud = longitudes[idx]
            n_segmentos = n_corta if longitud <= longitud_mediana else n_larga
            
            pos_i = np.array(self.nodos[nodo_i].coordenadas)
            pos_j = np.array(self.nodos[nodo_j].coordenadas)
            
            # Crear nodos intermedios "invisibles"
            nodos_elemento = [nodo_i]
            for i in range(1, n_segmentos):
                t = i / n_segmentos
                pos_intermedia = pos_i + t * (pos_j - pos_i)
                
                # Crear nodo temporal
                nombre_temp = f"_temp_{contador_nodo}"
                nodos_segmentados[nombre_temp] = type('obj', (object,), {
                    'coordenadas': pos_intermedia,
                    'nombre': nombre_temp,
                    'temporal': True
                })
                nodos_elemento.append(nombre_temp)
                contador_nodo += 1
            
            nodos_elemento.append(nodo_j)
            
            # Crear elementos entre nodos consecutivos
            for i in range(len(nodos_elemento) - 1):
                elementos.append((nodos_elemento[i], nodos_elemento[i+1]))
        
        return nodos_segmentados, elementos
    
    def _identificar_nodos_base(self):
        """Identifica nodos con apoyo fijo (empotrado)"""
        nodos_base = []
        for nombre, nodo in self.nodos.items():
            if hasattr(nodo, 'restricciones'):
                if all(nodo.restricciones):  # Todos restringidos = empotrado
                    nodos_base.append(nombre)
        return nodos_base
    
    def ensamblar_matriz_rigidez(self):
        """Ensambla matriz de rigidez global (sin E, I, A)"""
        n_nodos = len(self.nodos)
        n_gdl = n_nodos * 6  # 6 DOF por nodo
        K = np.zeros((n_gdl, n_gdl))
        # Implementar ensamblaje basado en geometría
        return K
    
    def _obtener_cargas_desde_dataframe(self, hipotesis_nombre):
        """Obtiene cargas desde DataFrames de EstructuraAEA_Mecanica"""
        cargas = {}
        
        # Los DataFrames están en mecanica con cargas por hipótesis
        for nombre_nodo, nodo in self.mecanica.geometria.nodos.items():
            if hasattr(nodo, 'obtener_cargas_hipotesis'):
                carga = nodo.obtener_cargas_hipotesis(hipotesis_nombre)
                if carga and any(abs(c) > 0.01 for c in carga):  # Filtrar cargas pequeñas
                    cargas[nombre_nodo] = carga
        
        return cargas
    
    def resolver_sistema(self, hipotesis_nombre):
        """Resuelve sistema de ecuaciones para obtener esfuerzos (en daN y daN.m)"""
        # Obtener cargas desde DataFrames de mecanica
        cargas = self._obtener_cargas_desde_dataframe(hipotesis_nombre)
        
        # Ensamblar y resolver
        K = self.ensamblar_matriz_rigidez()
        F = self._ensamblar_vector_cargas(cargas)
        
        # Aplicar condiciones de contorno
        K_red, F_red = self._aplicar_restricciones(K, F)
        
        # Resolver
        u = np.linalg.solve(K_red, F_red)
        
        # Calcular esfuerzos en elementos segmentados
        return self._calcular_esfuerzos_elementos(u)
    
    def calcular_momento_resultante_total(self, esfuerzos):
        """MRT = √(My² + Mz² + T²) [daN.m]"""
        resultados = {}
        for elemento, esf in esfuerzos.items():
            My = esf.get('My', 0)
            Mz = esf.get('Mz', 0)
            T = esf.get('T', 0)
            resultados[elemento] = np.sqrt(My**2 + Mz**2 + T**2)
        return resultados
    
    def calcular_momento_flector_equivalente(self, esfuerzos):
        """MFE = √(My² + Mz²) + |T| [daN.m]"""
        resultados = {}
        for elemento, esf in esfuerzos.items():
            My = esf.get('My', 0)
            Mz = esf.get('Mz', 0)
            T = esf.get('T', 0)
            resultados[elemento] = np.sqrt(My**2 + Mz**2) + abs(T)
        return resultados
    
    def generar_diagrama_2d(self, valores, tipo_diagrama, hipotesis):
        """Genera diagrama 2D estático con escala de colores (PNG)"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Normalizar valores para colormap
        vals = list(valores.values())
        norm = Normalize(vmin=min(vals), vmax=max(vals))
        cmap = cm.get_cmap('RdYlGn_r')  # Rojo=alto, Verde=bajo
        
        # Dibujar elementos con colores
        for elemento, valor in valores.items():
            nodo_i, nodo_j = elemento
            pos_i = self.nodos_segmentados[nodo_i].coordenadas
            pos_j = self.nodos_segmentados[nodo_j].coordenadas
            
            color = cmap(norm(valor))
            ax.plot([pos_i[0], pos_j[0]], [pos_i[2], pos_j[2]], 
                   color=color, linewidth=3)
        
        ax.set_xlabel('X [m]')
        ax.set_ylabel('Z [m]')
        ax.set_title(f'{tipo_diagrama} - {hipotesis} [daN.m]')
        ax.grid(True, alpha=0.3)
        
        # Colorbar
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, label=f'{tipo_diagrama} [daN.m]')
        
        return fig
    
    def generar_diagrama_3d(self, valores, tipo_diagrama, hipotesis):
        """Genera diagrama 3D estático con escala de colores (PNG)"""
        from mpl_toolkits.mplot3d import Axes3D
        
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Normalizar valores
        vals = list(valores.values())
        norm = Normalize(vmin=min(vals), vmax=max(vals))
        cmap = cm.get_cmap('RdYlGn_r')
        
        # Dibujar elementos
        for elemento, valor in valores.items():
            nodo_i, nodo_j = elemento
            pos_i = self.nodos_segmentados[nodo_i].coordenadas
            pos_j = self.nodos_segmentados[nodo_j].coordenadas
            
            color = cmap(norm(valor))
            ax.plot([pos_i[0], pos_j[0]], 
                   [pos_i[1], pos_j[1]], 
                   [pos_i[2], pos_j[2]], 
                   color=color, linewidth=3)
        
        ax.set_xlabel('X [m]')
        ax.set_ylabel('Y [m]')
        ax.set_zlabel('Z [m]')
        ax.set_title(f'{tipo_diagrama} - {hipotesis} [daN.m]')
        
        # Colorbar
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        fig.colorbar(sm, ax=ax, label=f'{tipo_diagrama} [daN.m]')
        
        return fig
```

## Fase 4: Vista AEE

### Crear: `components/vista_analisis_estatico.py`

```python
import dash_bootstrap_components as dbc
from dash import html, dcc

def crear_vista_analisis_estatico(estructura_actual, calculo_guardado=None):
    if calculo_guardado:
        return generar_resultados_aee(calculo_guardado, estructura_actual)
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader("Análisis Estático de Esfuerzos (AEE)"),
            dbc.CardBody([
                html.P("Análisis de esfuerzos sin propiedades E, I, A"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Analizar", id="btn-analizar-aee", color="primary"),
                        dbc.Button("Cargar desde Cache", id="btn-cargar-cache-aee", 
                                 color="secondary", className="ms-2"),
                        dbc.Button("Guardar Parámetros", id="btn-guardar-params-aee",
                                 color="info", className="ms-2")
                    ])
                ])
            ])
        ]),
        html.Div(id="resultados-aee", className="mt-3")
    ])

def generar_resultados_aee(calculo_guardado, estructura_actual):
    datos = calculo_guardado.get('resultados', {})
    hash_params = calculo_guardado.get('hash_parametros')
    
    componentes = [
        ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=True)
    ]
    
    # Cargar diagramas
    diagramas_activos = estructura_actual.get('AnalisisEstaticoEsfuerzos', {}).get('DIAGRAMAS_ACTIVOS', {})
    
    for tipo_diagrama in diagramas_activos:
        if datos.get(f'diagrama_{tipo_diagrama}'):
            componentes.append(html.H5(f"Diagrama {tipo_diagrama}"))
            # Cargar imagen estática PNG
            img_str = ViewHelpers.cargar_imagen_base64(f"AEE_{tipo_diagrama}.{hash_params}.png")
            if img_str:
                componentes.append(html.Img(src=f'data:image/png;base64,{img_str}', 
                                           style={'width': '100%', 'maxWidth': '1200px'}))
    
    return html.Div(componentes)
```

## Fase 5: Controller AEE

### Crear: `controllers/aee_controller.py`

```python
import dash
from dash import Input, Output, State, no_update
from utils.analisis_estatico import AnalizadorEstatico
from utils.calculo_cache import CalculoCache
from utils.view_helpers import ViewHelpers
import threading

def register_callbacks(app):
    
    @app.callback(
        [Output("resultados-aee", "children", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-analizar-aee", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def analizar_aee(n_clicks, estructura_actual):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        try:
            # Recargar estructura desde archivo activo
            from models.app_state import AppState
            state = AppState()
            ruta_actual = state.estructura_manager.ruta_estructura_actual
            if ruta_actual:
                estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
            else:
                return no_update, True, "Error", "No hay estructura activa", "danger", "danger"
            
            # Verificar DGE/DME
            calculo_dge = CalculoCache.cargar_calculo_dge(estructura_actual['TITULO'])
            calculo_dme = CalculoCache.cargar_calculo_dme(estructura_actual['TITULO'])
            
            if not calculo_dge or not calculo_dme:
                return no_update, True, "Error", "Debe ejecutar DGE y DME primero", "danger", "danger"
            
            # Ejecutar análisis
            resultados = ejecutar_analisis_aee(estructura_actual, calculo_dge, calculo_dme)
            
            # Guardar cache en background
            threading.Thread(target=guardar_cache_aee, 
                           args=(estructura_actual, resultados), 
                           daemon=True).start()
            
            # Generar vista
            from components.vista_analisis_estatico import generar_resultados_aee
            vista = generar_resultados_aee({'resultados': resultados, 
                                           'hash_parametros': resultados['hash']}, 
                                          estructura_actual)
            
            return vista, True, "Éxito", "Análisis completado", "success", "success"
            
        except Exception as e:
            return no_update, True, "Error", str(e), "danger", "danger"

def ejecutar_analisis_aee(estructura_actual, calculo_dge, calculo_dme):
    """Ejecuta análisis estático de esfuerzos (unidades: daN, daN.m)"""
    # Crear objetos de estructura
    from EstructuraAEA_Geometria import EstructuraAEA_Geometria
    from EstructuraAEA_Mecanica import EstructuraAEA_Mecanica
    
    geometria = calculo_dge['resultados']['estructura_geometria']
    mecanica = calculo_dme['resultados']['estructura_mecanica']
    
    # Parámetros AEE
    parametros_aee = estructura_actual.get('AnalisisEstaticoEsfuerzos', {})
    
    # Crear analizador
    analizador = AnalizadorEstatico(geometria, mecanica, parametros_aee)
    
    # Obtener hipótesis
    hipotesis = estructura_actual.get('hipotesis_activas', [])
    
    resultados = {
        'esfuerzos': {},
        'diagramas': {}
    }
    
    # Analizar cada hipótesis
    for hip in hipotesis:
        esfuerzos = analizador.resolver_sistema(hip)
        resultados['esfuerzos'][hip] = esfuerzos
        
        # Calcular índices y generar diagramas
        diagramas_activos = estructura_actual['AnalisisEstaticoEsfuerzos']['DIAGRAMAS_ACTIVOS']
        graficos_3d = estructura_actual['AnalisisEstaticoEsfuerzos'].get('GRAFICOS_3D_AEE', True)
        
        if diagramas_activos.get('MRT'):
            valores_mrt = analizador.calcular_momento_resultante_total(esfuerzos)
            resultados['diagramas'][f'MRT_{hip}'] = valores_mrt
            
            # Generar gráfico estático (PNG)
            if graficos_3d:
                fig = analizador.generar_diagrama_3d(valores_mrt, 'MRT', hip)
            else:
                fig = analizador.generar_diagrama_2d(valores_mrt, 'MRT', hip)
            
            # Guardar PNG
            ViewHelpers.guardar_imagen_matplotlib(fig, f"AEE_MRT_{hip}", resultados['hash'])
            plt.close(fig)
        
        if diagramas_activos.get('MFE'):
            valores_mfe = analizador.calcular_momento_flector_equivalente(esfuerzos)
            resultados['diagramas'][f'MFE_{hip}'] = valores_mfe
            
            # Generar gráfico estático (PNG)
            if graficos_3d:
                fig = analizador.generar_diagrama_3d(valores_mfe, 'MFE', hip)
            else:
                fig = analizador.generar_diagrama_2d(valores_mfe, 'MFE', hip)
            
            # Guardar PNG
            ViewHelpers.guardar_imagen_matplotlib(fig, f"AEE_MFE_{hip}", resultados['hash'])
            plt.close(fig)
    
    return resultados
```

## Fase 6: Integración en app.py

```python
# En app.py, agregar:
from controllers import aee_controller

# Registrar callbacks
aee_controller.register_callbacks(app)

# En navigation_controller, agregar ruta:
elif trigger_id == "menu-analisis-estatico":
    from components.vista_analisis_estatico import crear_vista_analisis_estatico
    calculo_aee = CalculoCache.cargar_calculo_aee(nombre_estructura)
    return crear_vista_analisis_estatico(estructura_actual, calculo_aee)
```

## Fase 7: Vista Calcular Todo

### Modificar: `components/vista_calcular_todo.py`

Agregar checkbox para AEE:

```python
dbc.Checklist(
    id="check-incluir-aee",
    options=[{"label": "Análisis Estático de Esfuerzos (AEE)", "value": "AEE"}],
    value=[]
)
```

### Modificar: `controllers/calcular_todo_controller.py`

```python
# En callback de calcular_todo:
if "AEE" in calculos_seleccionados:
    resultado_aee = ejecutar_analisis_aee(estructura_actual, resultado_dge, resultado_dme)
    resultados['AEE'] = resultado_aee
```

## Fase 8: Familia de Estructuras

### Modificar: `*.familia.json`

Agregar campo:

```json
{
    "calculos_activos": {
        "CMC": true,
        "DGE": true,
        "DME": true,
        "SPH": true,
        "ARBOLES": true,
        "AEE": true
    }
}
```

### Modificar: `controllers/familia_controller.py`

Incluir AEE en lógica de cálculo de familia.

## Fase 9: Cache System

### Modificar: `utils/calculo_cache.py`

```python
@staticmethod
def guardar_calculo_aee(nombre, parametros, resultados):
    """Guardar cálculo AEE en cache (solo PNG, no JSON de Plotly)"""
    nombre = nombre.replace(' ', '_')
    archivo = CACHE_DIR / f"{nombre}.calculoAEE.json"
    
    calculo = {
        'tipo': 'AEE',
        'nombre': nombre,
        'fecha_creacion': datetime.now().isoformat(),
        'hash_parametros': CalculoCache.calcular_hash(parametros),
        'parametros': parametros,
        'resultados': resultados
    }
    
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(calculo, f, indent=2, ensure_ascii=False)

@staticmethod
def cargar_calculo_aee(nombre):
    """Cargar cálculo AEE desde cache"""
    nombre = nombre.replace(' ', '_')
    archivo = CACHE_DIR / f"{nombre}.calculoAEE.json"
    
    if not archivo.exists():
        return None
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando cache AEE: {e}")
        return None

@staticmethod
def cargar_calculo_aee(nombre):
    nombre = nombre.replace(' ', '_')
    archivo = CACHE_DIR / f"{nombre}.calculoAEE.json"
    
    if archivo.exists():
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None
```

## Fase 10: Menú de Navegación

### Modificar: `components/menu.py`

Agregar ítem de menú:

```python
dbc.DropdownMenuItem("Análisis Estático (AEE)", id="menu-analisis-estatico")
```

## Resumen de Archivos a Crear/Modificar

### Crear:
- `utils/analisis_estatico.py`
- `components/vista_analisis_estatico.py`
- `controllers/aee_controller.py`

### Modificar:
- `data/plantilla.estructura.json`
- `components/vista_ajustar_parametros.py`
- `components/menu.py`
- `components/vista_calcular_todo.py`
- `controllers/calcular_todo_controller.py`
- `controllers/familia_controller.py`
- `controllers/navigation_controller.py`
- `utils/calculo_cache.py`
- `app.py`

## Notas Importantes

1. **Unidades:** Todas en daN (fuerzas) y daN.m (momentos)
2. **Gráficos:** Estáticos (PNG), individuales, NO interactivos
3. **Fuente de datos:** DataFrames de EstructuraAEA_Mecanica con cargas por hipótesis
4. **Conexiones:** Usa las mismas de EstructuraAEA_Geometria (gráficos estructura/cabezal)
5. **Segmentación:** 
   - Analiza longitudes de todas las conexiones
   - Percentil 50 separa cortas/largas
   - Cortas: n_segmentar_conexion_corta elementos (default: 10)
   - Largas: n_segmentar_conexion_larga elementos (default: 30)
   - Crea nodos temporales "invisibles" para mayor definición en gradientes
6. **Análisis:** NO requiere propiedades E, I, A (solo geometría)
7. **Numpy:** Cálculos matriciales para resolver sistema de ecuaciones
8. **Matplotlib:** Generación de diagramas con escala de colores
9. **Cache:** Solo guarda PNG (no JSON de Plotly)
10. **Integración:** Compatible con Calcular Todo y Familia de Estructuras


## Fase 10: Menú de Navegación

### Modificar: `components/menu.py`

Agregar entrada en el menú:

```python
dbc.NavLink("Análisis Estático Esfuerzos", href="#", id="menu-analisis-estatico", 
           className="nav-link-custom")
```

## Fase 11: Integración con Descargar HTML

### Modificar: `utils/descargar_html.py`

Agregar sección AEE en la función de descarga HTML completa:

```python
def generar_html_completo(estructura_actual, calculos):
    # ... código existente ...
    
    # Sección AEE
    if 'AEE' in calculos:
        html_sections.append(generar_seccion_aee(calculos['AEE'], estructura_actual))

def generar_seccion_aee(calculo_aee, estructura_actual):
    """Generar sección HTML para AEE"""
    html = ['<div class="seccion-aee">']
    html.append('<h2>Análisis Estático de Esfuerzos (AEE)</h2>')
    
    # Agregar imágenes PNG de diagramas
    hash_params = calculo_aee.get('hash_parametros')
    diagramas = calculo_aee.get('resultados', {}).get('diagramas', {})
    
    for tipo_diagrama, datos in diagramas.items():
        img_path = CACHE_DIR / f"AEE_{tipo_diagrama}.{hash_params}.png"
        if img_path.exists():
            img_base64 = ViewHelpers.cargar_imagen_base64(str(img_path))
            html.append(f'<h3>Diagrama {tipo_diagrama}</h3>')
            html.append(f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%"/>')
    
    html.append('</div>')
    return '\n'.join(html)
```

## Fase 12: Validación de Prerequisitos

### Crear: `utils/validacion_prerequisitos.py` (si no existe)

Agregar validación para AEE:

```python
def validar_prerequisitos_aee(estructura_actual):
    """Validar que DGE y DME estén ejecutados antes de AEE"""
    from utils.calculo_cache import CalculoCache
    
    nombre = estructura_actual.get('TITULO')
    
    # Verificar DGE
    calculo_dge = CalculoCache.cargar_calculo_dge(nombre)
    if not calculo_dge:
        return False, "Debe ejecutar DGE primero"
    
    vigente_dge, _ = CalculoCache.verificar_vigencia(calculo_dge, estructura_actual)
    if not vigente_dge:
        return False, "Cache DGE no vigente, recalcular DGE"
    
    # Verificar DME
    calculo_dme = CalculoCache.cargar_calculo_dme(nombre)
    if not calculo_dme:
        return False, "Debe ejecutar DME primero"
    
    vigente_dme, _ = CalculoCache.verificar_vigencia(calculo_dme, estructura_actual)
    if not vigente_dme:
        return False, "Cache DME no vigente, recalcular DME"
    
    return True, "Prerequisitos cumplidos"
```

## Fase 13: Testing y Debugging

### Agregar logs de debugging en `analisis_estatico.py`:

```python
class AnalizadorEstatico:
    def __init__(self, geometria, mecanica, parametros_aee):
        print(f"🔵 DEBUG AEE: Inicializando analizador")
        print(f"   - Nodos totales: {len(geometria.nodos)}")
        print(f"   - Conexiones totales: {len(geometria.conexiones)}")
        print(f"   - Hipótesis disponibles: {len(mecanica.resultados_reacciones)}")
        # ... resto del código
    
    def segmentar_conexiones(self):
        print(f"🔵 DEBUG AEE: Segmentando conexiones")
        print(f"   - n_corta: {self.n_segmentar_corta}")
        print(f"   - n_larga: {self.n_segmentar_larga}")
        # ... resto del código
```

## Consideraciones Adicionales Identificadas

### 1. Extracción de Conexiones desde EstructuraAEA_Geometria

**CRÍTICO**: Las conexiones entre nodos NO están explícitamente almacenadas en un atributo `conexiones`. Debes extraerlas desde:

```python
# En EstructuraAEA_Geometria, las conexiones se definen implícitamente en:
# - self.barras_estructura (lista de tuplas de nodos)
# - Método _crear_barras_estructura() que genera las conexiones

def extraer_conexiones_desde_geometria(geometria):
    """Extraer conexiones desde estructura geometría"""
    conexiones = []
    
    # Revisar si existe atributo barras_estructura
    if hasattr(geometria, 'barras_estructura'):
        for barra in geometria.barras_estructura:
            if isinstance(barra, tuple) and len(barra) == 2:
                conexiones.append(barra)
    
    # Alternativa: extraer desde gráficos
    if hasattr(geometria, 'estructura_graficos'):
        # Usar misma lógica que EstructuraAEA_Graficos
        pass
    
    return conexiones
```

### 2. Manejo de Nodos Rotados

Los nodos pueden tener rotaciones (`rotacion_eje_x`, `rotacion_eje_y`, `rotacion_eje_z`). El análisis estático debe:

```python
def aplicar_rotacion_cargas(cargas, nodo):
    """Aplicar rotación de nodo a las cargas"""
    if nodo.rotacion_eje_z != 0:
        # Rotar cargas según sistema local del nodo
        # Usar matriz de rotación 3D
        pass
    return cargas_rotadas
```

### 3. Unidades Consistentes

**TODAS las unidades en daN y daN.m**:
- Fuerzas: daN
- Momentos: daN.m
- Longitudes: m
- NO usar kN, N, kg, etc.

### 4. Compatibilidad con Calcular Todo

En `controllers/calcular_todo_controller.py`, agregar:

```python
def ejecutar_calculo_aee_automatico(estructura_actual):
    """Ejecutar AEE automáticamente desde Calcular Todo"""
    from controllers.aee_controller import ejecutar_analisis_aee
    from utils.calculo_cache import CalculoCache
    
    nombre = estructura_actual.get('TITULO')
    
    # Cargar prerequisitos
    calculo_dge = CalculoCache.cargar_calculo_dge(nombre)
    calculo_dme = CalculoCache.cargar_calculo_dme(nombre)
    
    if not calculo_dge or not calculo_dme:
        return {"exito": False, "mensaje": "Faltan prerequisitos DGE/DME"}
    
    try:
        resultados = ejecutar_analisis_aee(estructura_actual, calculo_dge, calculo_dme)
        return {"exito": True, "resultados": resultados}
    except Exception as e:
        return {"exito": False, "mensaje": str(e)}
```

### 5. Persistencia en Familia

En `utils/familia_manager.py`, agregar campo AEE:

```python
def crear_familia_desde_tabla(tabla_data, nombre_familia):
    # ... código existente ...
    
    familia_data['calculos_activos'] = {
        'CMC': True,
        'DGE': True,
        'DME': True,
        'SPH': True,
        'ARBOLES': True,
        'AEE': False  # Por defecto desactivado
    }
```

### 6. Orden de Ejecución en Calcular Familia

En `utils/calcular_familia_logica_encadenada.py`:

```python
# Orden correcto:
# CMC → DGE → DME → ARBOLES → SPH → FUNDACION → AEE → COSTEO
#                                                  ↑
#                                    AEE depende de DME
```

### 7. Manejo de Errores Específicos

```python
class AEEError(Exception):
    """Excepción específica para errores de AEE"""
    pass

class ConexionesNoEncontradasError(AEEError):
    """No se pudieron extraer conexiones de la geometría"""
    pass

class NodosInsuficientesError(AEEError):
    """No hay suficientes nodos para análisis"""
    pass
```

### 8. Formato de Salida de Diagramas

Los diagramas PNG deben tener:
- Resolución: 1200x800 px mínimo
- DPI: 150
- Formato: PNG con transparencia
- Colormap: 'RdYlGn_r' (Rojo=alto, Verde=bajo)
- Barra de colores con unidades

```python
fig.savefig(
    ruta_png,
    dpi=150,
    bbox_inches='tight',
    transparent=False,
    facecolor='white'
)
```

## Resumen de Archivos a Crear/Modificar

### Nuevos Archivos:
1. `utils/analisis_estatico.py` - Lógica principal de análisis
2. `components/vista_analisis_estatico.py` - Vista UI
3. `controllers/aee_controller.py` - Controller con callbacks

### Archivos a Modificar:
1. `data/plantilla.estructura.json` - Agregar parámetros AEE
2. `components/vista_ajustar_parametros.py` - Agregar controles AEE
3. `components/pestanas_parametros.py` - Agregar pestaña AEE
4. `config/parametros_controles.py` - Definir controles AEE
5. `app.py` - Registrar controller
6. `controllers/navigation_controller.py` - Agregar ruta
7. `components/vista_calcular_todo.py` - Agregar checkbox
8. `controllers/calcular_todo_controller.py` - Integrar AEE
9. `utils/calculo_cache.py` - Métodos guardar/cargar AEE
10. `utils/descargar_html.py` - Sección AEE en HTML
11. `components/menu.py` - Entrada de menú
12. `utils/familia_manager.py` - Campo AEE en familias
13. `utils/calcular_familia_logica_encadenada.py` - Integrar AEE

## Checklist de Implementación

- [ ] Fase 1: Parámetros en plantilla.estructura.json
- [ ] Fase 2: Vista Ajustar Parámetros (tabla + panel)
- [ ] Fase 3: Utility analisis_estatico.py
- [ ] Fase 4: Vista AEE
- [ ] Fase 5: Controller AEE
- [ ] Fase 6: Integración en app.py
- [ ] Fase 7: Vista Calcular Todo
- [ ] Fase 8: Familia de Estructuras
- [ ] Fase 9: Sistema de Cache
- [ ] Fase 10: Menú de Navegación
- [ ] Fase 11: Descargar HTML
- [ ] Fase 12: Validación Prerequisitos
- [ ] Fase 13: Testing y Debugging
- [ ] Testing: Estructura simple (suspensión recta)
- [ ] Testing: Estructura compleja (doble terna)
- [ ] Testing: Calcular Todo con AEE
- [ ] Testing: Familia con AEE activado
- [ ] Documentación: Actualizar memory bank


## Aspectos Críticos del Memory Bank

### 1. Callback Registration (CRÍTICO)

**SOLO usar patrón de registro basado en función:**

```python
def register_callbacks(app):
    """Registrar callbacks del controller AEE"""
    
    @app.callback(
        [Output("resultados-aee", "children", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-analizar-aee", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def analizar_aee(n_clicks, estructura_actual):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        # ... lógica
```

**NUNCA usar decorador @callback directamente** (causa conflictos de registro)

### 2. Validación de n_clicks

```python
# ✅ CORRECTO
if n_clicks is None:
    raise dash.exceptions.PreventUpdate

# ❌ INCORRECTO
if not n_clicks:  # Falla con n_clicks=0
    return dash.no_update
```

### 3. Toast Outputs (5 outputs obligatorios)

```python
Output("toast-notificacion", "is_open", allow_duplicate=True),
Output("toast-notificacion", "header", allow_duplicate=True),
Output("toast-notificacion", "children", allow_duplicate=True),
Output("toast-notificacion", "icon", allow_duplicate=True),  # NO OLVIDAR
Output("toast-notificacion", "color", allow_duplicate=True)
```

### 4. Imports Estándar en Controllers

```python
import dash
from dash import Input, Output, State, no_update
import dash_bootstrap_components as dbc
from dash import html
```

### 5. Debug Prints con Emojis Distintivos

```python
print(f"🔵 DEBUG AEE: Iniciando análisis")
print(f"📊 DEBUG AEE: Nodos segmentados: {n_nodos}")
print(f"✅ DEBUG AEE: Análisis completado")
print(f"❌ ERROR AEE: {error_msg}")
print(f"⚠️ WARNING AEE: {warning_msg}")
```

### 6. Guardado en Background Thread

```python
def guardar_async():
    try:
        # Guardar imágenes PNG
        for fig, nombre in figuras:
            fig.savefig(f"AEE_{nombre}.{hash}.png", dpi=150)
            plt.close(fig)
        
        # Guardar cache JSON
        CalculoCache.guardar_calculo_aee(nombre, parametros, resultados)
    except Exception as e:
        print(f"❌ ERROR guardando cache AEE: {e}")

threading.Thread(target=guardar_async, daemon=True).start()
```

### 7. Recargar Estructura Actual en Callbacks

```python
# SIEMPRE recargar desde archivo en callbacks críticos
from config.app_config import DATA_DIR
from models.app_state import AppState

state = AppState()
state.set_estructura_actual(estructura_actual)
ruta_actual = state.get_estructura_actual_path()
estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
```

### 8. Manejo de Encoding para Español

```python
# Al cargar archivos con caracteres españoles
encodings = ['utf-8', 'latin-1', 'cp1252']
for encoding in encodings:
    try:
        with open(archivo, 'r', encoding=encoding) as f:
            data = json.load(f)
        print(f"✅ Archivo cargado con encoding: {encoding}")
        break
    except UnicodeDecodeError:
        continue
```

### 9. Naming Conventions

- **Variables**: `snake_case` (e.g., `n_segmentar_conexion_corta`)
- **Constantes**: `UPPERCASE` (e.g., `GRAFICOS_3D_AEE`)
- **Funciones**: `snake_case` con verbos (e.g., `calcular_momento_resultante`)
- **Clases**: `PascalCase` (e.g., `AnalizadorEstatico`)
- **Archivos**: `snake_case` (e.g., `analisis_estatico.py`)

### 10. File Naming Pattern para Cache

```python
# Formato estándar
"{nombre_estructura}.calculoAEE.json"
"AEE_{tipo_diagrama}.{hash}.png"

# Ejemplo
"2x220_DTT_SAN_JORGE_PRUEBAS.calculoAEE.json"
"AEE_MRT_HIP_Suspension_Recta_A0.be566ad815c15bebb7337fe15590919a.png"
```

### 11. Hash Calculation (excluir campos temporales)

```python
def calcular_hash(parametros):
    """Calcular MD5 hash excluyendo campos temporales"""
    params_copy = parametros.copy()
    # Excluir campos que cambian sin afectar cálculo
    params_copy.pop('fecha_creacion', None)
    params_copy.pop('fecha_modificacion', None)
    params_copy.pop('version', None)
    
    import hashlib
    import json
    params_str = json.dumps(params_copy, sort_keys=True)
    return hashlib.md5(params_str.encode()).hexdigest()
```

### 12. Matplotlib Figure Cleanup

```python
# SIEMPRE cerrar figuras después de guardar
fig = analizador.generar_diagrama_3d(valores, 'MRT', hip)
fig.savefig(ruta_png, dpi=150, bbox_inches='tight')
plt.close(fig)  # ✅ CRÍTICO para evitar memory leaks
```

### 13. DataFrame Serialization

```python
# ✅ CORRECTO - Preserva formato exacto
df_json = df.to_json(orient='split')

# ❌ INCORRECTO - Pierde formato
df_dict = df.to_dict()
```

### 14. Component List Building

```python
# ✅ CORRECTO - Usar .append() individual
componentes = []
componentes.append(html.H5("Título"))
componentes.append(dcc.Graph(figure=fig))

# ❌ INCORRECTO - .extend() puede descomponer componentes
componentes.extend([html.H5("Título"), dcc.Graph(figure=fig)])
```

### 15. Error Messages en Español

```python
# Mensajes de error para usuario
"Debe ejecutar DGE y DME primero"
"No se encontraron conexiones en la estructura"
"Error en cálculo de esfuerzos: {detalle}"
"Parámetros de segmentación inválidos"
```

### 16. Estructura de Resultados JSON

```python
{
    "tipo": "AEE",
    "nombre": "estructura_nombre",
    "fecha_creacion": "2025-01-07T10:30:00",
    "hash_parametros": "abc123...",
    "parametros": {
        "AnalisisEstaticoEsfuerzos": {...}
    },
    "resultados": {
        "esfuerzos": {...},
        "diagramas": {...},
        "nodos_segmentados": [...],
        "conexiones_analizadas": [...]
    }
}
```

### 17. Verificación de Vigencia de Cache

```python
from utils.calculo_cache import CalculoCache

calculo_guardado = CalculoCache.cargar_calculo_aee(nombre)
if calculo_guardado:
    vigente, mensaje = CalculoCache.verificar_vigencia(
        calculo_guardado, 
        estructura_actual
    )
    if not vigente:
        print(f"⚠️ Cache no vigente: {mensaje}")
```

### 18. Integración con AppState

```python
from models.app_state import AppState

state = AppState()

# Acceder a objetos de cálculo
geometria = state.calculo_objetos.estructura_geometria
mecanica = state.calculo_objetos.estructura_mecanica

# Verificar disponibilidad
if not geometria or not mecanica:
    raise ValueError("Debe ejecutar DGE y DME primero")
```

### 19. Extracción de Conexiones (CRÍTICO)

```python
def extraer_conexiones_desde_geometria(geometria):
    """
    Extraer conexiones desde EstructuraAEA_Geometria.
    Las conexiones NO están en un atributo directo, 
    deben extraerse desde la lógica de gráficos.
    """
    conexiones = []
    
    # Método 1: Desde barras_estructura (si existe)
    if hasattr(geometria, 'barras_estructura'):
        for barra in geometria.barras_estructura:
            if isinstance(barra, tuple) and len(barra) == 2:
                conexiones.append(barra)
    
    # Método 2: Desde lógica de EstructuraAEA_Graficos
    # Revisar método _crear_barras_estructura()
    
    # Método 3: Inferir desde nodos y topología
    # BASE conecta con CROSS_H1, CROSS_H2
    # CROSS conecta con conductores y guardias
    
    return conexiones
```

### 20. Orden de Ejecución en Calcular Todo

```python
# Orden correcto de dependencias:
# 1. CMC (cables)
# 2. DGE (geometría) - depende de CMC
# 3. DME (mecánica) - depende de DGE
# 4. ARBOLES (árboles de carga) - depende de DME
# 5. SPH (selección poste) - depende de DME
# 6. FUNDACION - depende de SPH
# 7. AEE (análisis estático) - depende de DME ← AQUÍ
# 8. COSTEO - depende de SPH

# AEE se ejecuta DESPUÉS de DME y ANTES de COSTEO
```

## Checklist Final de Verificación

### Pre-implementación:
- [ ] Leer notebook `Ejemplo_conAnalisisEstatico_nooutput.ipynb`
- [ ] Entender extracción de conexiones desde geometría
- [ ] Verificar patrón de callbacks en controllers existentes
- [ ] Revisar estructura de cache en otros cálculos

### Durante implementación:
- [ ] Usar SOLO función `register_callbacks(app)`
- [ ] Incluir 5 outputs de toast (con "icon")
- [ ] Validar `n_clicks is None` correctamente
- [ ] Agregar debug prints con emojis
- [ ] Cerrar figuras matplotlib con `plt.close()`
- [ ] Guardar en background thread
- [ ] Recargar estructura en callbacks críticos

### Post-implementación:
- [ ] Verificar registro en `app.py`
- [ ] Probar con estructura simple
- [ ] Probar con estructura compleja
- [ ] Verificar cache guarda/carga correctamente
- [ ] Probar integración con Calcular Todo
- [ ] Probar integración con Familia
- [ ] Actualizar memory bank con lecciones aprendidas


## Lecciones del Troubleshooting Guide

### 1. Filtrar Campos Internos en Componentes Dash

```python
# ❌ INCORRECTO - Pasa campo interno 'tipo'
dcc.Slider(**obtener_config_control("n_segmentar_corta"))

# ✅ CORRECTO - Filtrar campos internos
config = obtener_config_control("n_segmentar_corta")
dcc.Slider(**{k: v for k, v in config.items() if k != "tipo"})
```

### 2. Callbacks No Deben Estar en Navigation

```python
# ❌ INCORRECTO - Incluir botones de guardado
@app.callback(
    Output("contenido-principal", "children"),
    Input("menu-analisis-estatico", "n_clicks"),
    Input("btn-guardar-aee", "n_clicks"),  # ❌ NO
)

# ✅ CORRECTO - Solo navegación
@app.callback(
    Output("contenido-principal", "children"),
    Input("menu-analisis-estatico", "n_clicks"),
)
```

### 3. Resultados No Desaparecen en Error

```python
# ❌ INCORRECTO - Borra resultados previos
except Exception as e:
    return [], True, "Error", str(e), "danger", "danger"

# ✅ CORRECTO - Preserva resultados
except Exception as e:
    return dash.no_update, True, "Error", str(e), "danger", "danger"
```

### 4. Identificar Trigger con callback_context

```python
from dash import callback_context

ctx = callback_context
if ctx.triggered:
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    print(f"🔵 DEBUG AEE: Triggered by: {trigger_id}")
    
    # Validar trigger esperado
    if trigger_id not in ["btn-analizar-aee", "btn-cargar-cache-aee"]:
        return dash.no_update
```

### 5. Verificación Explícita de Clicks

```python
# ❌ INCORRECTO - prevent_initial_call=True no es suficiente
@app.callback(...)
def callback(n_clicks):
    # Se ejecuta en carga inicial

# ✅ CORRECTO - Verificar clicks explícitamente
@app.callback(..., prevent_initial_call=True)
def callback(n_clicks):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    # Ahora sí es seguro procesar
```

### 6. Toast Feedback para Prerequisitos

```python
# Cuando faltan prerequisitos
if not calculo_dge or not calculo_dme:
    return (
        dash.no_update,  # No cambiar resultados
        True,  # Abrir toast
        "Advertencia",  # Header
        "Debe ejecutar DGE y DME primero para realizar análisis AEE",  # Message
        "warning",  # Icon
        "warning"  # Color
    )
```

### 7. Capturar Retornos de Funciones (NO usar plt.gcf())

```python
# ❌ INCORRECTO - Captura figura equivocada
analizador.generar_diagrama_3d(valores, 'MRT', hip)
fig = plt.gcf()  # Obtiene Matplotlib, no la figura correcta

# ✅ CORRECTO - Capturar retorno directo
fig = analizador.generar_diagrama_3d(valores, 'MRT', hip)
```

### 8. Usar .append() Individual para Componentes

```python
# ❌ INCORRECTO - .extend() puede descomponer
componentes.extend([
    html.H5("Diagrama MRT"),
    dcc.Graph(figure=fig)
])

# ✅ CORRECTO - .append() individual
componentes.append(html.H5("Diagrama MRT"))
componentes.append(dcc.Graph(figure=fig))
```

### 9. Filtrar Fuerzas Insignificantes

```python
# Filtrar ruido numérico en visualización
UMBRAL_FUERZA = 0.01  # daN

for nombre_nodo, cargas in esfuerzos.items():
    # Verificar magnitud
    if any(abs(val) > UMBRAL_FUERZA for val in cargas):
        cargas_significativas[nombre_nodo] = cargas
```

### 10. Coordenadas Globales para Visualización

```python
# ❌ INCORRECTO - Coordenadas rotadas
if nodo.rotacion_eje_z != 0:
    cargas = nodo.obtener_cargas_hipotesis_rotadas(hip, "global")

# ✅ CORRECTO - Coordenadas globales para visualización
cargas = nodo.obtener_cargas_hipotesis(hip)
```

### 11. Extracción Basada en Nodos (NO DataFrame)

```python
# ❌ INCORRECTO - DataFrame puede tener nombres inconsistentes
for hip in hipotesis:
    if hip in df_cargas.columns:
        cargas = df_cargas[hip]

# ✅ CORRECTO - Extraer desde nodos directamente
for nombre_nodo, nodo in geometria.nodos.items():
    cargas = nodo.obtener_cargas_hipotesis(hip)
```

### 12. Sanitizar Nombres de Archivo

```python
# SIEMPRE reemplazar espacios en nombres de archivo
nombre_estructura = estructura_actual.get('TITULO')
nombre_sanitizado = nombre_estructura.replace(' ', '_')

# Usar nombre sanitizado en todas las operaciones de archivo
archivo = CACHE_DIR / f"{nombre_sanitizado}.calculoAEE.json"
```

### 13. Recargar Estructura en Callbacks Críticos

```python
def analizar_aee(n_clicks, estructura_actual):
    # SIEMPRE recargar desde archivo
    from config.app_config import DATA_DIR
    from models.app_state import AppState
    
    state = AppState()
    state.set_estructura_actual(estructura_actual)
    ruta_actual = state.get_estructura_actual_path()
    estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
    
    # Ahora estructura_actual tiene datos frescos del archivo
```

### 14. Orden de Tuplas en Plotly 3D

```python
# ❌ INCORRECTO - Orden equivocado
for nombre, x, y, z in nodos:
    scatter_data.append((nombre, x, y, z))  # Nombre en X

# ✅ CORRECTO - Coordenadas primero, nombre en text
for nombre, x, y, z in nodos:
    scatter_data.append((x, y, z, nombre))  # Coordenadas en X/Y/Z
```

### 15. NO Usar fig.show() en Aplicaciones

```python
# ❌ INCORRECTO - Imprime JSON completo en consola
fig = generar_diagrama_3d(...)
fig.show()  # Spam en consola
return fig

# ✅ CORRECTO - Solo retornar
fig = generar_diagrama_3d(...)
return fig  # Dash lo renderiza automáticamente
```

### 16. Especificar dtick en Gráficos 3D

```python
# Para grilla cada 1 metro
fig.update_layout(
    scene=dict(
        xaxis=dict(title='X [m]', type='linear', dtick=1),
        yaxis=dict(title='Y [m]', type='linear', dtick=1),
        zaxis=dict(title='Z [m]', type='linear', dtick=1)
    )
)
```

### 17. Implementar Interfaz Completa para stdout

```python
class ConsoleCapture:
    def write(self, text):
        # Implementación
        
    def flush(self):
        # Implementación
        
    def isatty(self):
        return self.original_stdout.isatty()
    
    def fileno(self):
        return self.original_stdout.fileno()
    
    def __getattr__(self, name):
        # Delegar atributos no implementados
        return getattr(self.original_stdout, name)
```

### 18. Try-Except en Callbacks de Vista Específica

```python
@app.callback(
    Output("resultados-aee", "children"),
    Input("btn-actualizar-aee", "n_clicks"),
    prevent_initial_call=False
)
def actualizar_resultados(n_clicks):
    try:
        # Lógica del callback
        return resultados
    except:
        # Componente no existe (vista no activa)
        return dash.no_update
```

### 19. Patrones de Búsqueda Flexibles

```python
# ❌ INCORRECTO - Patrón único hardcodeado
if 'Peso estimado:' in texto:
    peso = extraer_numero(texto)

# ✅ CORRECTO - Múltiples patrones
for linea in texto.split('\n'):
    if 'Peso =' in linea or 'Peso estimado:' in linea or 'Peso total:' in linea:
        import re
        numeros = re.findall(r'\d+', linea)
        if numeros:
            peso = int(numeros[0])
            break
```

### 20. Retornar Lista de Componentes (NO Div)

```python
# ❌ INCORRECTO - Retorna Div envuelto
def generar_contenido_aee():
    componentes = [...]
    return html.Div(componentes)  # Causa problemas en pestañas

# ✅ CORRECTO - Retorna lista directa
def generar_contenido_aee():
    componentes = [...]
    return componentes  # Lista de componentes
```

## Checklist Anti-Errores para AEE

### Antes de Implementar:
- [ ] Revisar todos los troubleshooting patterns
- [ ] Identificar callbacks similares en otros controllers
- [ ] Verificar estructura de cache en cálculos existentes
- [ ] Entender extracción de conexiones desde geometría

### Durante Implementación:
- [ ] Usar SOLO `register_callbacks(app)` pattern
- [ ] Validar `n_clicks is None` correctamente
- [ ] Incluir 5 outputs de toast (con "icon")
- [ ] Filtrar campos internos antes de pasar a componentes
- [ ] Usar `.append()` individual para componentes complejos
- [ ] Capturar retornos de funciones (NO `plt.gcf()`)
- [ ] Sanitizar nombres de archivo (reemplazar espacios)
- [ ] Recargar estructura en callbacks críticos
- [ ] Cerrar figuras matplotlib con `plt.close()`
- [ ] NO usar `fig.show()` en aplicaciones
- [ ] Especificar `dtick=1` en gráficos 3D
- [ ] Filtrar fuerzas < 0.01 daN
- [ ] Usar coordenadas globales para visualización
- [ ] Extraer cargas desde nodos (NO DataFrame)
- [ ] Retornar listas de componentes (NO Div)

### Testing:
- [ ] Verificar callbacks se ejecutan (debug prints)
- [ ] Probar con estructura simple
- [ ] Probar con estructura compleja
- [ ] Verificar cache guarda/carga correctamente
- [ ] Verificar gráficos aparecen en vista
- [ ] Verificar gráficos aparecen en Calcular Todo
- [ ] Verificar integración con Familia
- [ ] Probar prerequisitos (sin DGE/DME)
- [ ] Probar con nombres con espacios
- [ ] Verificar no hay memory leaks (figuras cerradas)


## Notas sobre Estructura Activa

**IMPORTANTE**: El proyecto NO usa `actual.estructura.json`. En su lugar:

1. **State en Dash**: `estructura-actual` contiene datos de la estructura activa
2. **Recargar desde archivo**: Usar `state.estructura_manager.ruta_estructura_actual` para obtener ruta
3. **Patrón en callbacks**:
```python
from models.app_state import AppState
state = AppState()
ruta_actual = state.estructura_manager.ruta_estructura_actual
if ruta_actual:
    estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
```

Este patrón se aplica en TODOS los callbacks críticos de AEE.
