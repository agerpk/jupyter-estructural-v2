# Plan de Implementación: Módulo Servidumbre

## Objetivo
Expandir la vista DGE para incluir cálculo de franja de servidumbre según AEA-95301-2007 9.2-1, sin crear vista nueva.

## Fórmulas AEA-95301-2007 9.2-1

### Ecuación Principal
```
A = C + 2 * (Lk + fi) * sen(theta_max) + 2 * d
```

### Variables
- **A**: Ancho total de franja (m)
- **C**: Distancia transversal entre conductores externos (m) = max(x_conductores) - min(x_conductores)
- **Lk**: Longitud de cadena (m) - de parámetros base
- **fi**: Flecha absoluta máxima (m) - de CMC conductor
- **theta_max**: Ángulo máximo de declinación (°) - de DGE
- **d**: Distancia de seguridad (m) = 1.5 * dm + 2
- **dm**: Distancia mínima (m) = Vs / 150
- **Vs**: Tensión de sobretensión (kV) = μ * 1.2 * 0.82 * Vn
- **μ**: Coeficiente sobretensión máxima = 1.1 (constante)
- **Vn**: Tensión nominal de línea (kV) - de parámetros base

### Zonas del Gráfico
1. **Zona A** (total): Ancho A, altura = nodo más alto, transparencia 0.3
2. **Zonas d** (externas): Ancho = 2 + 1.5*dm, a ambos lados
3. **Zonas Proyección**: Ancho = (Lk + fi)*sen(theta_max), intermedias
4. **Zona C** (central): Ancho = C

Distribución: `[d] [Proyección] [C] [Proyección] [d]`

## Archivos a Crear/Modificar

### 1. CREAR: `utils/servidumbre_aea.py`

```python
"""Cálculo de franja de servidumbre según AEA-95301-2007 9.2-1"""

class ServidumbreAEA:
    def __init__(self, estructura_geometria, flecha_max_conductor, tension_nominal, Lk):
        self.estructura = estructura_geometria
        self.fi = flecha_max_conductor
        self.Vn = tension_nominal
        self.Lk = Lk
        self.theta_max = estructura_geometria.dimensiones['theta_max']
        
        # Constantes
        self.mu = 1.1
        self.factor_enrarecimiento = 1.2
        self.factor_cresta = 0.82
        
        # Calcular
        self.Vs = self.mu * self.factor_enrarecimiento * self.factor_cresta * self.Vn
        self.dm = self.Vs / 150
        self.d = 1.5 * self.dm + 2
        self.C = self._calcular_C()
        self.A = self._calcular_A()
    
    def _calcular_C(self):
        nodos_conductor = {n: coords for n, coords in self.estructura.nodes_key.items() 
                          if self.estructura.nodos[n].tipo_nodo == 'conductor'}
        if not nodos_conductor:
            return 0.0
        x_coords = [coords[0] for coords in nodos_conductor.values()]
        return max(x_coords) - min(x_coords)
    
    def _calcular_A(self):
        import math
        theta_rad = math.radians(self.theta_max)
        return self.C + 2 * (self.Lk + self.fi) * math.sin(theta_rad) + 2 * self.d
    
    def generar_memoria_calculo(self):
        import math
        memoria = []
        memoria.append("=" * 80)
        memoria.append("MEMORIA DE CÁLCULO: FRANJA DE SERVIDUMBRE AEA-95301-2007 9.2-1")
        memoria.append("=" * 80)
        memoria.append("")
        memoria.append("PARÁMETROS DE ENTRADA:")
        memoria.append(f"  Tensión nominal (Vn): {self.Vn:.1f} kV")
        memoria.append(f"  Longitud cadena (Lk): {self.Lk:.3f} m")
        memoria.append(f"  Flecha máxima conductor (fi): {self.fi:.3f} m")
        memoria.append(f"  Ángulo declinación máxima (theta_max): {self.theta_max:.2f}°")
        memoria.append("")
        memoria.append("CONSTANTES:")
        memoria.append(f"  Coeficiente sobretensión (μ): {self.mu}")
        memoria.append(f"  Factor enrarecimiento aire: {self.factor_enrarecimiento}")
        memoria.append(f"  Factor cresta tensión: {self.factor_cresta}")
        memoria.append("")
        memoria.append("CÁLCULOS INTERMEDIOS:")
        memoria.append(f"  Vs = μ * 1.2 * 0.82 * Vn")
        memoria.append(f"  Vs = {self.mu} * {self.factor_enrarecimiento} * {self.factor_cresta} * {self.Vn:.1f}")
        memoria.append(f"  Vs = {self.Vs:.2f} kV")
        memoria.append("")
        memoria.append(f"  dm = Vs / 150")
        memoria.append(f"  dm = {self.Vs:.2f} / 150")
        memoria.append(f"  dm = {self.dm:.3f} m")
        memoria.append("")
        memoria.append(f"  d = 1.5 * dm + 2")
        memoria.append(f"  d = 1.5 * {self.dm:.3f} + 2")
        memoria.append(f"  d = {self.d:.3f} m")
        memoria.append("")
        memoria.append(f"  C = max(x_conductores) - min(x_conductores)")
        memoria.append(f"  C = {self.C:.3f} m")
        memoria.append("")
        memoria.append("CÁLCULO FINAL:")
        theta_rad = math.radians(self.theta_max)
        termino_proyeccion = (self.Lk + self.fi) * math.sin(theta_rad)
        memoria.append(f"  A = C + 2 * (Lk + fi) * sen(theta_max) + 2 * d")
        memoria.append(f"  A = {self.C:.3f} + 2 * ({self.Lk:.3f} + {self.fi:.3f}) * sen({self.theta_max:.2f}°) + 2 * {self.d:.3f}")
        memoria.append(f"  A = {self.C:.3f} + 2 * {termino_proyeccion:.3f} + {2*self.d:.3f}")
        memoria.append(f"  A = {self.A:.3f} m")
        memoria.append("")
        memoria.append("RESULTADOS:")
        memoria.append(f"  Ancho total franja (A): {self.A:.3f} m")
        memoria.append(f"  Distancia conductores externos (C): {self.C:.3f} m")
        memoria.append(f"  Distancia seguridad (d): {self.d:.3f} m")
        memoria.append(f"  Ancho zona proyección (cada lado): {termino_proyeccion:.3f} m")
        memoria.append("=" * 80)
        return "\n".join(memoria)
```

### 2. CREAR: `utils/grafico_servidumbre_aea.py`

```python
"""Gráfico de estructura con zonas de servidumbre"""

def graficar_servidumbre(estructura_geometria, servidumbre_obj, usar_plotly=True):
    import math
    from GraficoEstructura2D import GraficoEstructura2D
    
    if not usar_plotly:
        raise NotImplementedError("Solo Plotly soportado para servidumbre")
    
    # Generar gráfico base de estructura
    grafico_base = GraficoEstructura2D(estructura_geometria)
    fig = grafico_base.generar_completo()
    
    # Obtener altura máxima
    altura_max = max([coords[2] for coords in estructura_geometria.nodes_key.values()])
    
    # Calcular anchos de zonas
    ancho_d = servidumbre_obj.d
    theta_rad = math.radians(servidumbre_obj.theta_max)
    ancho_proyeccion = (servidumbre_obj.Lk + servidumbre_obj.fi) * math.sin(theta_rad)
    
    # Zona A (total) - fondo gris transparente
    fig.add_shape(
        type="rect",
        x0=-servidumbre_obj.A/2, x1=servidumbre_obj.A/2,
        y0=0, y1=altura_max,
        fillcolor="rgba(200,200,200,0.3)",
        line=dict(width=2, color="gray", dash="dash"),
        layer="below"
    )
    
    # Zonas d (seguridad) - externas
    fig.add_shape(
        type="rect",
        x0=-servidumbre_obj.A/2, x1=-servidumbre_obj.A/2 + ancho_d,
        y0=0, y1=altura_max,
        fillcolor="rgba(255,200,200,0.4)",
        line=dict(width=1, color="red"),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=servidumbre_obj.A/2 - ancho_d, x1=servidumbre_obj.A/2,
        y0=0, y1=altura_max,
        fillcolor="rgba(255,200,200,0.4)",
        line=dict(width=1, color="red"),
        layer="below"
    )
    
    # Zonas Proyección - intermedias
    fig.add_shape(
        type="rect",
        x0=-servidumbre_obj.A/2 + ancho_d, 
        x1=-servidumbre_obj.A/2 + ancho_d + ancho_proyeccion,
        y0=0, y1=altura_max,
        fillcolor="rgba(200,255,200,0.4)",
        line=dict(width=1, color="green"),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=servidumbre_obj.A/2 - ancho_d - ancho_proyeccion,
        x1=servidumbre_obj.A/2 - ancho_d,
        y0=0, y1=altura_max,
        fillcolor="rgba(200,255,200,0.4)",
        line=dict(width=1, color="green"),
        layer="below"
    )
    
    # Zona C (central)
    if servidumbre_obj.C > 0:
        fig.add_shape(
            type="rect",
            x0=-servidumbre_obj.C/2, x1=servidumbre_obj.C/2,
            y0=0, y1=altura_max,
            fillcolor="rgba(200,200,255,0.4)",
            line=dict(width=1, color="blue"),
            layer="below"
        )
    
    # Anotaciones
    fig.add_annotation(
        x=0, y=altura_max + 1,
        text=f"A = {servidumbre_obj.A:.2f} m",
        showarrow=False,
        font=dict(size=14, color="black", family="Arial Black")
    )
    
    # Actualizar título
    fig.update_layout(
        title=dict(
            text=f"FRANJA DE SERVIDUMBRE AEA-95301-2007<br>{estructura_geometria.tension_nominal}kV - {estructura_geometria.tipo_estructura.upper()}",
            font=dict(size=14, family="Arial Black")
        )
    )
    
    return fig
```

### 3. MODIFICAR: `utils/calculo_cache.py`

```python
@staticmethod
def guardar_calculo_dge(nombre_estructura, estructura_data, dimensiones, nodes_key, 
                       fig_estructura, fig_cabezal, fig_nodos=None, memoria_calculo=None, 
                       conexiones=None, servidumbre_data=None, fig_servidumbre=None):
    nombre_estructura = nombre_estructura.replace(' ', '_')
    hash_params = CalculoCache.calcular_hash(estructura_data)
    
    # ... código existente para guardar otras figuras ...
    
    # Guardar figura de servidumbre (DUAL: PNG + JSON)
    if fig_servidumbre:
        try:
            png_path = CACHE_DIR / f"Servidumbre.{hash_params}.png"
            fig_servidumbre.write_image(str(png_path), width=1200, height=800)
            
            json_path = CACHE_DIR / f"Servidumbre.{hash_params}.json"
            fig_servidumbre.write_json(str(json_path))
            print(f"✅ Gráfico servidumbre guardado: PNG + JSON")
        except Exception as e:
            print(f"Advertencia: No se pudo guardar gráfico servidumbre: {e}")
    
    nodos_editados = estructura_data.get("nodos_editados", [])
    
    calculo_data = {
        "hash_parametros": hash_params,
        "fecha_calculo": datetime.now().isoformat(),
        "dimensiones": dimensiones,
        "nodes_key": nodes_key,
        "nodos_editados": nodos_editados,
        "conexiones": conexiones if conexiones else [],
        "imagen_estructura": f"Estructura.{hash_params}.png",
        "imagen_cabezal": f"Cabezal.{hash_params}.png",
        "imagen_nodos": f"Nodos.{hash_params}.json" if fig_nodos else None,
        "memoria_calculo": memoria_calculo,
        "servidumbre": servidumbre_data,
        "imagen_servidumbre": f"Servidumbre.{hash_params}.json" if fig_servidumbre else None
    }
    
    archivo = CACHE_DIR / f"{nombre_estructura}.calculoDGE.json"
    archivo.write_text(json.dumps(calculo_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return hash_params
```

### 4. MODIFICAR: `controllers/geometria_controller.py`

#### A) En función `ejecutar_calculo_dge()` - Agregar después de generar gráficos:

```python
# Calcular servidumbre si está habilitado
servidumbre_data = None
fig_servidumbre = None

if estructura_actual.get('mc_servidumbre', False) or estructura_actual.get('plot_servidumbre', False):
    # VALIDACIONES OBLIGATORIAS
    if not fmax_conductor:
        raise ValueError("ERROR: Debe ejecutar CMC primero para obtener flecha máxima del conductor")
    if 'theta_max' not in estructura_geometria.dimensiones:
        raise ValueError("ERROR: theta_max no disponible en dimensiones de DGE")
    if estructura_actual.get('Lk', 0) <= 0:
        raise ValueError("ERROR: Lk debe ser mayor a 0")
    if estructura_actual.get('TENSION', 0) <= 0:
        raise ValueError("ERROR: TENSION debe ser mayor a 0")
    
    from utils.servidumbre_aea import ServidumbreAEA
    from utils.grafico_servidumbre_aea import graficar_servidumbre
    
    servidumbre = ServidumbreAEA(
        estructura_geometria,
        fmax_conductor,
        estructura_actual['TENSION'],
        estructura_actual['Lk']
    )
    
    servidumbre_data = {
        'A': servidumbre.A,
        'C': servidumbre.C,
        'd': servidumbre.d,
        'dm': servidumbre.dm,
        'Vs': servidumbre.Vs,
        'memoria_calculo': servidumbre.generar_memoria_calculo() if estructura_actual.get('mc_servidumbre') else None
    }
    
    # Solo generar gráfico si plot_servidumbre=True Y generar_plots=True
    if estructura_actual.get('plot_servidumbre', False) and generar_plots:
        fig_servidumbre = graficar_servidumbre(estructura_geometria, servidumbre, usar_plotly=True)

# Modificar llamada a guardar_calculo_dge:
CalculoCache.guardar_calculo_dge(
    nombre_estructura,
    estructura_actual,
    dims,
    nodes_key,
    fig_estructura,
    fig_cabezal,
    fig_nodos,
    memoria_calculo,
    estructura_geometria.conexiones,
    servidumbre_data,
    fig_servidumbre
)
```

#### B) En callback `guardar_parametros_geometria` - Agregar States:

```python
@app.callback(
    Output("estructura-actual", "data", allow_duplicate=True),
    # ... otros outputs ...
    Input("btn-guardar-params-geom", "n_clicks"),
    # ... otros states ...
    State("switch-mc-servidumbre", "value"),  # ← AGREGAR
    State("switch-plot-servidumbre", "value"),  # ← AGREGAR
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def guardar_parametros_geometria(n_clicks, ..., mc_servidumbre, plot_servidumbre, estructura_actual):
    # ...
    estructura_actualizada.update({
        # ... parámetros existentes ...
        "mc_servidumbre": mc_servidumbre,
        "plot_servidumbre": plot_servidumbre
    })
```

### 5. MODIFICAR: `components/vista_diseno_geometrico.py`

#### A) En función `crear_vista_diseno_geometrico()` - Agregar controles después de sección de hielo:

```python
html.H5("Cálculo de Servidumbre", className="mb-3 mt-4"),

dbc.Row([
    dbc.Col([
        dbc.Label("Memoria Cálculo Servidumbre", style={"fontSize": "1.125rem"}),
        dbc.Switch(id="switch-mc-servidumbre", value=estructura_actual.get("mc_servidumbre", False)),
    ], md=6),
    dbc.Col([
        dbc.Label("Graficar Servidumbre", style={"fontSize": "1.125rem"}),
        dbc.Switch(id="switch-plot-servidumbre", value=estructura_actual.get("plot_servidumbre", False)),
    ], md=6),
], className="mb-3"),
```

#### B) En función `generar_resultados_dge()` - Agregar ANTES de memoria de cálculo DGE:

```python
# Agregar resultados de servidumbre
servidumbre_data = calculo_guardado.get('servidumbre')
if servidumbre_data:
    output.append(html.H5("FRANJA DE SERVIDUMBRE", className="mb-2 mt-4"))
    
    serv_txt = (
        f"Ancho total franja (A): {servidumbre_data['A']:.3f} m\n" +
        f"Distancia conductores externos (C): {servidumbre_data['C']:.3f} m\n" +
        f"Distancia seguridad (d): {servidumbre_data['d']:.3f} m\n" +
        f"Distancia mínima (dm): {servidumbre_data['dm']:.3f} m\n" +
        f"Tensión sobretensión (Vs): {servidumbre_data['Vs']:.2f} kV"
    )
    output.append(html.Pre(serv_txt, style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.85rem'}))
    
    if servidumbre_data.get('memoria_calculo'):
        output.append(html.Pre(servidumbre_data['memoria_calculo'], style={'backgroundColor': '#1e1e1e', 'color': '#d4d4d4', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '0.85rem', 'maxHeight': '600px', 'overflowY': 'auto', 'whiteSpace': 'pre-wrap', 'fontFamily': 'monospace'}))
    
    # Cargar gráfico interactivo si existe
    hash_params = calculo_guardado.get('hash_parametros')
    if hash_params and calculo_guardado.get('imagen_servidumbre'):
        fig_serv = ViewHelpers.cargar_figura_plotly_json(f"Servidumbre.{hash_params}.json")
        if fig_serv:
            output.append(html.H5("GRAFICO DE SERVIDUMBRE", className="mb-2 mt-4"))
            output.append(dcc.Graph(figure=fig_serv, config={'displayModeBar': True}, style={'height': '800px'}))
```

### 6. MODIFICAR: `data/plantilla.estructura.json`

Agregar al final del JSON (antes del último `}`):

```json
  "mc_servidumbre": false,
  "plot_servidumbre": false
```

### 7. Vista Ajustar Parámetros

Agregar en categoría "DGE":

```python
{"Parámetro": "mc_servidumbre", "Valor": True/False, "Categoría": "DGE"},
{"Parámetro": "plot_servidumbre", "Valor": True/False, "Categoría": "DGE"}
```

### 8. Vista Calcular Familia

Agregar columnas en tabla:

```python
{"name": "MC Serv.", "id": "mc_servidumbre", "type": "text", "editable": True},
{"name": "Plot Serv.", "id": "plot_servidumbre", "type": "text", "editable": True}
```

### 9. MODIFICAR: `utils/descargar_html.py`

#### A) En función de descarga Calcular Todo - Agregar después de sección DGE:

```python
if 'servidumbre' in calculo_dge and calculo_dge['servidumbre']:
    html.append("<h3>Franja de Servidumbre</h3>")
    serv = calculo_dge['servidumbre']
    html.append(f"<p><strong>Ancho total (A):</strong> {serv['A']:.3f} m</p>")
    html.append(f"<p><strong>Distancia conductores (C):</strong> {serv['C']:.3f} m</p>")
    html.append(f"<p><strong>Distancia seguridad (d):</strong> {serv['d']:.3f} m</p>")
    html.append(f"<p><strong>Distancia mínima (dm):</strong> {serv['dm']:.3f} m</p>")
    html.append(f"<p><strong>Tensión sobretensión (Vs):</strong> {serv['Vs']:.2f} kV</p>")
    
    if serv.get('memoria_calculo'):
        html.append(f"<pre style='background:#1e1e1e; color:#d4d4d4; padding:8px;'>{serv['memoria_calculo']}</pre>")
```

#### B) En función de descarga Calcular Familia - Agregar sección similar:

```python
# Agregar en función generar_html_familia() después de sección DGE de cada estructura
if 'servidumbre' in calculo_dge and calculo_dge['servidumbre']:
    html.append("<h4>Franja de Servidumbre</h4>")
    serv = calculo_dge['servidumbre']
    html.append(f"<p><strong>A:</strong> {serv['A']:.3f} m, <strong>C:</strong> {serv['C']:.3f} m, <strong>d:</strong> {serv['d']:.3f} m</p>")
```

## Orden de Implementación

1. ✅ Crear `utils/servidumbre_aea.py` (YA EXISTE)
2. ❌ Crear `utils/grafico_servidumbre_aea.py` (FALTA - CRÍTICO)
3. Modificar `utils/calculo_cache.py` - Agregar parámetros servidumbre
4. Modificar `data/plantilla.estructura.json` - Agregar mc_servidumbre y plot_servidumbre
5. Modificar `components/vista_diseno_geometrico.py`:
   - A) Agregar switches en `crear_vista_diseno_geometrico()`
   - B) Agregar código en `generar_resultados_dge()`
6. Modificar `controllers/geometria_controller.py`:
   - A) Agregar lógica en `ejecutar_calculo_dge()` con validaciones
   - B) Agregar States en callback `guardar_parametros_geometria`
7. Modificar vista ajustar parámetros - Agregar mc_servidumbre y plot_servidumbre en categoría DGE
8. Modificar vista calcular familia - Agregar columnas en tabla
9. Modificar `utils/descargar_html.py`:
   - A) Función descarga Calcular Todo
   - B) Función descarga Calcular Familia
10. Testing completo:
    - Verificar que switches guardan valores
    - Verificar que validaciones funcionan
    - Verificar que gráfico se genera y carga desde cache
    - Verificar compatibilidad con generar_plots=False
    - Verificar en todas las vistas (DGE, Calcular Todo, Familia)

## Validaciones Implementadas

En `controllers/geometria_controller.py` función `ejecutar_calculo_dge()`:

```python
if estructura_actual.get('mc_servidumbre', False) or estructura_actual.get('plot_servidumbre', False):
    # VALIDACIONES OBLIGATORIAS
    if not fmax_conductor:
        raise ValueError("ERROR: Debe ejecutar CMC primero para obtener flecha máxima del conductor")
    if 'theta_max' not in estructura_geometria.dimensiones:
        raise ValueError("ERROR: theta_max no disponible en dimensiones de DGE")
    if estructura_actual.get('Lk', 0) <= 0:
        raise ValueError("ERROR: Lk debe ser mayor a 0")
    if estructura_actual.get('TENSION', 0) <= 0:
        raise ValueError("ERROR: TENSION debe ser mayor a 0")
```

**Sin fallbacks** - El sistema debe fallar con error claro si faltan datos obligatorios.

## Archivos Críticos Faltantes

### ❌ `utils/grafico_servidumbre_aea.py` - NO EXISTE
**Estado:** Código completo en este documento pero archivo no creado
**Impacto:** ImportError al ejecutar cálculo con plot_servidumbre=True
**Prioridad:** CRÍTICA - Debe crearse antes de testing

## Compatibilidad con generar_plots

En `controllers/geometria_controller.py`:
```python
# Solo generar gráfico si AMBOS son True
if estructura_actual.get('plot_servidumbre', False) and generar_plots:
    fig_servidumbre = graficar_servidumbre(...)
```

Esto asegura que:
- Si `generar_plots=False` (ej: en familia), no se genera gráfico aunque `plot_servidumbre=True`
- Si `plot_servidumbre=False`, no se genera gráfico aunque `generar_plots=True`
- Solo se genera si AMBOS son True
