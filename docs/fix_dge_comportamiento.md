# Fix DGE: Comportamiento Similar a Calcular Todo

## Problema
DGE calcula automáticamente al entrar a la vista. Debe comportarse como "Calcular Todo": vista vacía, solo calcula al presionar botón.

## Comportamiento Requerido

### Al Entrar a Vista
- Vista vacía con 3 botones: "Calcular", "Cargar desde Cache", "Modificar Nodos"
- NO ejecuta ningún cálculo automáticamente

### Botón "Cargar desde Cache"
1. Recargar `actual.estructura.json`
2. Calcular hash de parámetros
3. Buscar cache con ese hash
4. Si existe: Mostrar resultados
5. Si no existe: Mensaje "No hay datos en cache"

### Botón "Calcular"
1. Recargar `actual.estructura.json` (más reciente)
2. Ejecutar cálculo DGE completo
3. Guardar/sobreescribir cache
4. Mostrar resultados

### Botón "Modificar Nodos"
1. Recargar `actual.estructura.json` (más reciente)
2. Cargar `nodos_editados` desde archivo
3. Abrir modal con nodos actuales
4. Si presiona "Cancelar": Cerrar modal, no guardar
5. Si presiona "Guardar":
   - Guardar en `actual.estructura.json`
   - Guardar en `{TITULO}.estructura.json`
   - Cerrar modal
   - NO calcular automáticamente
6. Próxima vez que se abra modal: Cargar archivo actualizado

## Cambios Necesarios

### 1. Navigation Controller
**Archivo**: `controllers/navigation_controller.py`

Cambiar líneas donde se carga DGE al entrar:
```python
# ANTES (línea ~100)
elif ultima_vista == "diseno-geometrico":
    from components.vista_diseno_geometrico import crear_vista_diseno_geometrico
    from utils.calculo_cache import CalculoCache
    calculo_guardado = None
    if estructura_actual:
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        calculo_guardado = CalculoCache.cargar_calculo_dge(nombre_estructura)
    return crear_vista_diseno_geometrico(estructura_actual, calculo_guardado)

# DESPUÉS
elif ultima_vista == "diseno-geometrico":
    from components.vista_diseno_geometrico import crear_vista_diseno_geometrico
    return crear_vista_diseno_geometrico(estructura_actual, None)
```

Y también en el trigger del menú (línea ~180):
```python
# ANTES
elif trigger_id == "menu-diseno-geometrico":
    guardar_navegacion_state("diseno-geometrico")
    from components.vista_diseno_geometrico import crear_vista_diseno_geometrico
    from utils.calculo_cache import CalculoCache
    calculo_guardado = None
    if estructura_actual:
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        calculo_guardado = CalculoCache.cargar_calculo_dge(nombre_estructura)
    return crear_vista_diseno_geometrico(estructura_actual, calculo_guardado)

# DESPUÉS
elif trigger_id == "menu-diseno-geometrico":
    guardar_navegacion_state("diseno-geometrico")
    from components.vista_diseno_geometrico import crear_vista_diseno_geometrico
    return crear_vista_diseno_geometrico(estructura_actual, None)
```

### 2. Callback DGE - Separar Calcular y Cargar
**Archivo**: `controllers/geometria_controller.py`

El callback actual (línea 780) maneja ambos botones juntos. Debe separarse en DOS callbacks:

**Callback 1: Cargar desde Cache**
```python
@app.callback(
    Output("output-diseno-geometrico", "children", allow_duplicate=True),
    Input("btn-cargar-cache-dge", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def cargar_cache_dge(n_clicks, estructura_actual):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    from utils.calculo_cache import CalculoCache
    from components.vista_diseno_geometrico import generar_resultados_dge
    from config.app_config import DATA_DIR
    
    # Recargar estructura desde archivo
    ruta_actual = DATA_DIR / "actual.estructura.json"
    estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
    nombre_estructura = estructura_actual.get('TITULO', 'estructura')
    
    calculo_guardado = CalculoCache.cargar_calculo_dge(nombre_estructura)
    
    if calculo_guardado:
        return generar_resultados_dge(calculo_guardado, estructura_actual, mostrar_alerta_cache=True)
    else:
        return dbc.Alert("No hay datos en cache para esta estructura", color="warning")
```

**Callback 2: Calcular (sin cargar cache)**
```python
@app.callback(
    Output("output-diseno-geometrico", "children"),
    Input("btn-calcular-geom", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def calcular_dge(n_clicks, estructura_actual):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    from config.app_config import DATA_DIR
    
    # Recargar estructura desde archivo
    ruta_actual = DATA_DIR / "actual.estructura.json"
    estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
    
    # Ejecutar cálculo (sin pasar por cache)
    resultado = ejecutar_calculo_dge(estructura_actual, state)
    
    if resultado["exito"]:
        # Generar y mostrar resultados
        from components.vista_diseno_geometrico import generar_resultados_dge_directo
        return generar_resultados_dge_directo(resultado, estructura_actual)
    else:
        return dbc.Alert(f"Error: {resultado['mensaje']}", color="danger")
```

### 3. Modal Modificar Nodos
**Archivo**: `controllers/geometria_controller.py`

Callback que abre modal (línea ~350) debe recargar archivo:
```python
if trigger_id == "btn-editar-nodos-dge":
    from utils.calculo_cache import CalculoCache
    from config.app_config import DATA_DIR
    
    # RECARGAR estructura desde archivo
    ruta_actual = DATA_DIR / "actual.estructura.json"
    estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
    
    # Cargar nodos_editados desde archivo
    nodos_editados_guardados = estructura_actual.get("nodos_editados", [])
    
    # ... resto del código para generar tabla
```

Callback que guarda nodos (línea ~650) ya recarga archivo, está OK.

### 4. Vista DGE - Agregar parámetro mostrar_alerta_cache
**Archivo**: `components/vista_diseno_geometrico.py`

Función `generar_resultados_dge()` debe aceptar parámetro:
```python
def generar_resultados_dge(calculo_guardado, estructura_actual, mostrar_alerta_cache=False):
    # ... código existente
    
    if mostrar_alerta_cache:
        resultados.insert(0, ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=True))
    
    # ... resto del código
```

## Resumen de Archivos a Modificar
1. `controllers/navigation_controller.py` - 2 lugares (carga inicial y menú)
2. `controllers/geometria_controller.py` - Separar callback en 2, actualizar modal
3. `components/vista_diseno_geometrico.py` - Agregar parámetro mostrar_alerta_cache

## Testing
1. Entrar a DGE → Vista vacía ✓
2. Presionar "Cargar Cache" sin cache → Mensaje "No hay datos" ✓
3. Presionar "Calcular" → Ejecuta y muestra resultados ✓
4. Presionar "Cargar Cache" con cache → Muestra resultados con alerta ✓
5. Abrir modal nodos → Muestra nodos de archivo actual ✓
6. Modificar y cancelar → No guarda ✓
7. Modificar y guardar → Guarda en ambos archivos, no calcula ✓
8. Abrir modal nuevamente → Muestra nodos modificados ✓
