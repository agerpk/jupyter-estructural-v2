# Vista Vano Económico - Especificación de Implementación

## Objetivo
Analizar el costo total de una familia de estructuras en función del vano, generando curvas de costo vs vano para determinar el vano económico óptimo.

## Requisitos Previos
✅ Vista Familia de Estructuras funcional
✅ Persistencia de familia activa implementada
✅ Lógica de cálculo de familia en `utils/calcular_familia_logica_encadenada.py`

## IMPORTANTE: Cálculo Dinámico de Cantidades

### Validación de Familia
La familia DEBE contener:
- **1 estructura** tipo Suspensión Recta (S)
- **1 estructura** tipo Retención / Ret. Angular con alpha=0 (RR)
- **N estructuras** tipo Retención / Ret. Angular con alpha>0 (RA) - opcional
- **1 estructura** tipo Terminal (T)

Si existen múltiples estructuras del mismo tipo → **Error: "Existen múltiples estructuras de tipo (X)"**

### Inputs Adicionales en Vista
- `LONGTRAZA` (m) - ENTERO - Longitud total de la traza
- `CRITERIO_RR` - SELECT: "Distancia" / "Suspensiones" / "Manual"
- `cant_RR_manual` - ENTERO - Solo si CRITERIO_RR = "Manual"
- `RR_CADA_X_M` - FLOAT - Retención cada X metros (si Distancia)
- `RR_CADA_X_S` - ENTERO - Retención cada X suspensiones (si Suspensiones)

### Cálculo de Cantidades (por iteración de vano)
```python
# Fijas
cant_T = 2  # Siempre 2 terminales

# Desde familia
cant_RA = suma de cantidades de estructuras con tipo="Retención / Ret. Angular" y alpha>0

# Dinámicas (dependen de L_vano)
cant_S = math.ceil(LONGTRAZA / L_vano)  # roundup

# Según criterio
if CRITERIO_RR == "Distancia":
    cant_RR = math.ceil(LONGTRAZA / RR_CADA_X_M) - 1 - cant_RA
elif CRITERIO_RR == "Suspensiones":
    cant_RR = math.ceil(cant_S / RR_CADA_X_S) - cant_RA
elif CRITERIO_RR == "Manual":
    cant_RR = cant_RR_manual
```

### Modificación en Cada Iteración
Para cada vano de la lista:
1. Modificar `L_vano` en TODAS las estructuras
2. Calcular `cant_S` con nuevo vano
3. Calcular `cant_RR` según criterio
4. Modificar campo `Cantidad` en cada estructura:
   - Terminal → `Cantidad = cant_T`
   - Suspensión → `Cantidad = cant_S`
   - RR (alpha=0) → `Cantidad = cant_RR`
   - RA (alpha>0) → Mantener cantidad del .familia.json
5. Ejecutar `ejecutar_calculo_familia_completa()`
6. Capturar `costo_global`

## Arquitectura - Reutilización de Código

### 1. Cargar Familia
**REUTILIZAR**: Lógica de `vista_familia_estructuras.py`
- Dropdown con familias disponibles
- Cargar familia activa desde AppState
- Mismo patrón de callbacks que vista familia

### 2. Cálculo Iterativo
**REUTILIZAR**: `ejecutar_calculo_familia_completa()` de `calcular_familia_logica_encadenada.py`

**ESTRATEGIA**:
1. **Validar familia** (1 S, 1 RR, N RA, 1 T)
2. Generar lista de vanos: `[vano_min, vano_min+salto, ..., vano_max]`
3. Para cada vano:
   - Crear copia de `familia_data`
   - Modificar `L_vano` en TODAS las estructuras
   - **Calcular cantidades dinámicas** (cant_S, cant_RR)
   - **Modificar campo `Cantidad`** en cada estructura
   - Llamar a `ejecutar_calculo_familia_completa(familia_modificada)`
   - Capturar `costeo_global["costo_global"]`
   - Emitir progreso: `(vano_actual_index / total_vanos) * 100`
4. Retornar: `{vano: {costo_global, cant_S, cant_RR}}` para todos los vanos

**NO DUPLICAR**:
- ❌ NO reimplementar secuencia CMC>DGE>DME>SPH>FUND>COSTEO
- ❌ NO crear nueva lógica de cálculo
- ✅ SOLO modificar `L_vano` y `Cantidad`, reutilizar función existente

### 3. Callbacks - Evitar Conflictos
**PATRÓN**: Usar IDs únicos con prefijo `vano-economico-`

Ejemplos de IDs únicos:
- `vano-economico-input-min`
- `vano-economico-input-max`
- `vano-economico-input-salto`
- `vano-economico-btn-calcular`
- `vano-economico-select-familia`
- `vano-economico-progress`
- `vano-economico-resultados`

**EVITAR**: Reutilizar IDs de vista familia (`select-familia-existente`, `btn-calcular-familia`, etc.)

## Componentes a Crear

### 1. Vista (`components/vista_vano_economico.py`)

```python
def crear_vista_vano_economico():
    """Vista principal de Vano Económico"""
    
    # Cargar familia activa
    state = AppState()
    nombre_familia_activa = state.get_familia_activa()
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Vano Económico")),
            dbc.CardBody([
                # Familia activa
                crear_seccion_familia_activa(nombre_familia_activa),
                
                # Controles de vano
                crear_controles_vano(),
                
                # Botón calcular
                dbc.Button("Calcular Vano Económico", 
                          id="vano-economico-btn-calcular", 
                          color="primary"),
                
                # Barra de progreso
                dbc.Progress(id="vano-economico-progress", 
                            value=0, 
                            className="mb-3"),
                
                # Área de resultados
                html.Div(id="vano-economico-resultados")
            ])
        ])
    ])

def crear_seccion_familia_activa(nombre_familia):
    """Sección para mostrar/cargar familia"""
    return dbc.Row([
        dbc.Col([
            html.Label("Familia Activa:", className="fw-bold"),
            html.P(nombre_familia or "Ninguna", id="vano-economico-familia-actual")
        ], width=6),
        dbc.Col([
            html.Label("Cargar otra familia:"),
            dbc.Select(id="vano-economico-select-familia")
        ], width=6)
    ])

def crear_controles_vano():
    """Controles para configurar rango de vanos"""
    return dbc.Row([
        dbc.Col([
            html.Label("Vano Mínimo [m]:"),
            dbc.Input(id="vano-economico-input-min", 
                     type="number", value=300, step=10)
        ], width=4),
        dbc.Col([
            html.Label("Vano Máximo [m]:"),
            dbc.Input(id="vano-economico-input-max", 
                     type="number", value=500, step=10)
        ], width=4),
        dbc.Col([
            html.Label("Salto [m]:"),
            dbc.Input(id="vano-economico-input-salto", 
                     type="number", value=50, step=10)
        ], width=4)
    ], className="mb-3")

def crear_controles_cantidades():
    """Controles para cálculo dinámico de cantidades"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Configuración de Cantidades")),
        dbc.CardBody([
            # LONGTRAZA
            dbc.Row([
                dbc.Col([
                    html.Label("Longitud de Traza [m]:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-longtraza", 
                             type="number", value=10000, step=100, min=100)
                ], width=12)
            ], className="mb-3"),
            
            # Criterio RR
            dbc.Row([
                dbc.Col([
                    html.Label("Criterio para Retenciones:", className="fw-bold"),
                    dbc.Select(id="vano-economico-select-criterio-rr",
                              options=[
                                  {"label": "Por Distancia", "value": "Distancia"},
                                  {"label": "Por Suspensiones", "value": "Suspensiones"},
                                  {"label": "Manual", "value": "Manual"}
                              ],
                              value="Distancia")
                ], width=6),
                dbc.Col([
                    html.Label("RR cada X metros:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-rr-cada-x-m", 
                             type="number", value=2000, step=100, min=100)
                ], width=3),
                dbc.Col([
                    html.Label("RR cada X suspensiones:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-rr-cada-x-s", 
                             type="number", value=5, step=1, min=1)
                ], width=3)
            ], className="mb-3"),
            
            # Manual
            dbc.Row([
                dbc.Col([
                    html.Label("Cantidad RR Manual:", className="fw-bold"),
                    dbc.Input(id="vano-economico-input-cant-rr-manual", 
                             type="number", value=4, step=1, min=0,
                             disabled=True)
                ], width=6)
            ], id="vano-economico-row-manual", style={"display": "none"}),
            
            html.Hr(),
            
            # Display calculado
            html.H6("Cantidades Calculadas (ejemplo con vano medio):", className="text-muted"),
            html.Div(id="vano-economico-display-cantidades")
        ])
    ], className="mb-3")
```

### 2. Controller (`controllers/vano_economico_controller.py`)

```python
def register_callbacks(app):
    """Registrar callbacks de vano económico"""
    
    @app.callback(
        [Output("vano-economico-select-familia", "options"),
         Output("vano-economico-select-familia", "value")],
        Input("vano-economico-select-familia", "id"),
        prevent_initial_call=False
    )
    def cargar_opciones_familias(component_id):
        """Cargar familias disponibles"""
        from utils.familia_manager import FamiliaManager
        archivos = FamiliaManager.obtener_archivos_familia()
        opciones = [{"label": f, "value": f} for f in archivos]
        return opciones, None
    
    @app.callback(
        [Output("vano-economico-familia-actual", "children"),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("vano-economico-select-familia", "value"),
        prevent_initial_call=True
    )
    def cargar_familia_seleccionada(nombre_familia):
        """Cargar familia seleccionada"""
        if not nombre_familia:
            raise dash.exceptions.PreventUpdate
        
        state = AppState()
        state.set_familia_activa(nombre_familia)
        
        return (nombre_familia, True, "Éxito", 
                f"Familia '{nombre_familia}' cargada", 
                "success", "success")
    
    @app.callback(
        [Output("vano-economico-resultados", "children"),
         Output("vano-economico-progress", "value"),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "icon", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("vano-economico-btn-calcular", "n_clicks"),
        [State("vano-economico-input-min", "value"),
         State("vano-economico-input-max", "value"),
         State("vano-economico-input-salto", "value")],
        prevent_initial_call=True
    )
    def calcular_vano_economico(n_clicks, vano_min, vano_max, salto):
        """Ejecutar cálculo de vano económico"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        # Validar inputs
        if not all([vano_min, vano_max, salto]):
            return (no_update, 0, True, "Error", 
                   "Complete todos los campos", "danger", "danger")
        
        # Cargar familia activa
        state = AppState()
        nombre_familia = state.get_familia_activa()
        
        if not nombre_familia:
            return (no_update, 0, True, "Error", 
                   "No hay familia activa", "danger", "danger")
        
        try:
            # Ejecutar cálculo iterativo
            from utils.vano_economico_utils import calcular_vano_economico_iterativo
            resultados = calcular_vano_economico_iterativo(
                nombre_familia, vano_min, vano_max, salto
            )
            
            # Generar vista de resultados
            vista_resultados = generar_vista_resultados_vano_economico(resultados)
            
            return (vista_resultados, 100, True, "Éxito", 
                   "Cálculo completado", "success", "success")
            
        except Exception as e:
            return (no_update, 0, True, "Error", 
                   f"Error: {str(e)}", "danger", "danger")
```

### 3. Utilidades (`utils/vano_economico_utils.py`)

```python
def generar_lista_vanos(vano_min: float, vano_max: float, salto: float) -> List[float]:
    """Generar lista de vanos según especificación"""
    vanos = [vano_min]
    vano_actual = vano_min + salto
    
    while vano_actual < vano_max:
        vanos.append(vano_actual)
        vano_actual += salto
    
    vanos.append(vano_max)
    return vanos

def calcular_vano_economico_iterativo(nombre_familia: str, 
                                      vano_min: float, 
                                      vano_max: float, 
                                      salto: float) -> Dict:
    """
    Calcular costo de familia para cada vano
    REUTILIZA: ejecutar_calculo_familia_completa()
    """
    from utils.familia_manager import FamiliaManager
    from utils.calcular_familia_logica_encadenada import ejecutar_calculo_familia_completa
    
    # Cargar familia base
    familia_base = FamiliaManager.cargar_familia(nombre_familia)
    
    # Generar lista de vanos
    vanos = generar_lista_vanos(vano_min, vano_max, salto)
    
    resultados_por_vano = {}
    
    for i, vano in enumerate(vanos):
        print(f"🔄 Calculando vano {vano}m ({i+1}/{len(vanos)})...")
        
        # Crear copia de familia con L_vano modificado
        familia_modificada = modificar_vano_familia(familia_base, vano)
        
        # REUTILIZAR función existente
        resultado = ejecutar_calculo_familia_completa(familia_modificada)
        
        if resultado.get("exito"):
            costo_global = resultado["costeo_global"]["costo_global"]
            resultados_por_vano[vano] = {
                "costo_global": costo_global,
                "costeo_detalle": resultado["costeo_global"]
            }
            print(f"✅ Vano {vano}m: {costo_global:.2f} UM")
        else:
            print(f"❌ Error en vano {vano}m")
        
        # Progreso se maneja en callback
    
    return {
        "vanos": vanos,
        "resultados": resultados_por_vano,
        "familia_nombre": nombre_familia
    }

def modificar_vano_familia(familia_data: Dict, nuevo_vano: float) -> Dict:
    """Modificar L_vano en todas las estructuras de la familia"""
    import copy
    familia_modificada = copy.deepcopy(familia_data)
    
    for nombre_estr, datos_estr in familia_modificada["estructuras"].items():
        datos_estr["L_vano"] = nuevo_vano
    
    return familia_modificada

def generar_grafico_curva_vano_economico(resultados: Dict) -> go.Figure:
    """Generar gráfico de curva vano vs costo"""
    import numpy as np
    from scipy.interpolate import make_interp_spline
    
    vanos = resultados["vanos"]
    costos = [resultados["resultados"][v]["costo_global"] for v in vanos]
    
    # Ajuste polinómico
    if len(vanos) > 3:
        x_smooth = np.linspace(min(vanos), max(vanos), 300)
        spl = make_interp_spline(vanos, costos, k=3)
        y_smooth = spl(x_smooth)
    else:
        x_smooth = vanos
        y_smooth = costos
    
    fig = go.Figure()
    
    # Curva suavizada
    fig.add_trace(go.Scatter(
        x=x_smooth, y=y_smooth,
        mode='lines',
        name='Curva ajustada',
        line=dict(color='blue', width=2)
    ))
    
    # Puntos calculados
    fig.add_trace(go.Scatter(
        x=vanos, y=costos,
        mode='markers',
        name='Puntos calculados',
        marker=dict(size=10, color='red')
    ))
    
    fig.update_layout(
        title="Curva de Vano Económico",
        xaxis_title="Vano [m]",
        yaxis_title="Costo Total Familia [UM]"
    )
    
    return fig

def generar_grafico_barras_apiladas(resultados: Dict) -> go.Figure:
    """Generar gráfico de barras apiladas por estructura"""
    vanos = resultados["vanos"]
    
    # Extraer costos por estructura para cada vano
    estructuras_nombres = set()
    for vano in vanos:
        detalle = resultados["resultados"][vano]["costeo_detalle"]
        estructuras_nombres.update(detalle["costos_parciales"].keys())
    
    fig = go.Figure()
    
    for estructura in estructuras_nombres:
        costos_estructura = []
        for vano in vanos:
            detalle = resultados["resultados"][vano]["costeo_detalle"]
            costo = detalle["costos_parciales"].get(estructura, 0)
            costos_estructura.append(costo)
        
        fig.add_trace(go.Bar(
            name=estructura,
            x=vanos,
            y=costos_estructura
        ))
    
    fig.update_layout(
        barmode='stack',
        title="Distribución de Costos por Estructura y Vano",
        xaxis_title="Vano [m]",
        yaxis_title="Costo [UM]"
    )
    
    return fig
```

## Actualización de Navegación

### `components/menu.py`
Agregar en sección HERRAMIENTAS:
```python
dbc.DropdownMenuItem("Vano Económico", id="menu-vano-economico")
```

### `controllers/navigation_controller.py`
Agregar caso en callback de navegación:
```python
elif trigger_id == "menu-vano-economico":
    from components.vista_vano_economico import crear_vista_vano_economico
    return crear_vista_vano_economico()
```

### `app.py`
Registrar callbacks:
```python
import controllers.vano_economico_controller as vano_economico_controller
vano_economico_controller.register_callbacks(app)
```

## Progreso de Implementación

### Fase 1: Estructura Base
- [ ] Crear `components/vista_vano_economico.py`
- [ ] Crear `controllers/vano_economico_controller.py`
- [ ] Crear `utils/vano_economico_utils.py`
- [ ] Actualizar menú y navegación

### Fase 2: Lógica de Cálculo
- [ ] Implementar `generar_lista_vanos()`
- [ ] Implementar `modificar_vano_familia()`
- [ ] Implementar `calcular_vano_economico_iterativo()`
- [ ] Testing con familia de prueba

### Fase 3: Visualización
- [ ] Implementar `generar_grafico_curva_vano_economico()`
- [ ] Implementar `generar_grafico_barras_apiladas()`
- [ ] Implementar `generar_vista_resultados_vano_economico()`

### Fase 4: Exportación
- [ ] Implementar exportación HTML
- [ ] Incluir tabla de familia
- [ ] Incluir ajustes de vano
- [ ] Incluir gráficos

## Notas Críticas

### ✅ HACER:
- Reutilizar `ejecutar_calculo_familia_completa()`
- Usar IDs únicos con prefijo `vano-economico-`
- Modificar solo `L_vano` en estructuras
- Capturar `costeo_global["costo_global"]`

### ❌ NO HACER:
- Duplicar lógica de cálculo encadenado
- Reutilizar IDs de vista familia
- Reimplementar secuencia CMC>DGE>DME>SPH>FUND>COSTEO
- Crear nueva lógica de costeo

## Testing
1. Cargar familia con 2-3 estructuras
2. Configurar vanos: min=300, max=500, salto=50
3. Ejecutar cálculo
4. Verificar progreso actualiza correctamente
5. Verificar gráficos se generan
6. Verificar exportación HTML funciona
