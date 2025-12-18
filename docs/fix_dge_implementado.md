# Fix DGE Implementado - Vista Vacía al Entrar

## Cambios Realizados

### 1. Navigation Controller (`controllers/navigation_controller.py`)

**Cambio**: Eliminar carga automática de cache al entrar a DGE

**Líneas modificadas**: 
- Carga inicial (línea ~88-100)
- Trigger menú (línea ~180)

**Antes**:
```python
elif ultima_vista == "diseno-geometrico":
    from components.vista_diseno_geometrico import crear_vista_diseno_geometrico
    from utils.calculo_cache import CalculoCache
    calculo_guardado = None
    if estructura_actual:
        nombre_estructura = estructura_actual.get('TITULO', 'estructura')
        calculo_guardado = CalculoCache.cargar_calculo_dge(nombre_estructura)
    return crear_vista_diseno_geometrico(estructura_actual, calculo_guardado)
```

**Después**:
```python
elif ultima_vista == "diseno-geometrico":
    from components.vista_diseno_geometrico import crear_vista_diseno_geometrico
    return crear_vista_diseno_geometrico(estructura_actual, None)
```

**Resultado**: Vista DGE siempre inicia vacía, sin cargar cache automáticamente.

---

### 2. Geometria Controller (`controllers/geometria_controller.py`)

**Cambio**: Separar callback único en DOS callbacks independientes

#### Callback 1: Cargar desde Cache (NUEVO)

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

**Características**:
- Solo se ejecuta al presionar "Cargar desde Cache"
- Recarga `actual.estructura.json` para obtener TITULO correcto
- Muestra alerta "Cargado desde cache" si encuentra datos
- Muestra mensaje "No hay datos en cache" si no encuentra

#### Callback 2: Calcular (MODIFICADO)

```python
@app.callback(
    Output("output-diseno-geometrico", "children"),
    Input("btn-calcular-geom", "n_clicks"),
    State("estructura-actual", "data"),
    prevent_initial_call=True
)
def calcular_diseno_geometrico(n_clicks, estructura_actual):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    # SIEMPRE recargar estructura desde archivo
    from config.app_config import DATA_DIR
    ruta_actual = DATA_DIR / "actual.estructura.json"
    estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
    
    # ... resto del código de cálculo (sin cambios)
```

**Características**:
- Solo se ejecuta al presionar "Calcular"
- Recarga `actual.estructura.json` al inicio
- Ejecuta cálculo completo (no pasa por cache para mostrar)
- Guarda cache al final
- NO muestra alerta "Cargado desde cache"

#### Callback Modal Nodos (MODIFICADO)

**Cambio**: Recargar archivo al abrir modal

```python
if trigger_id == "btn-editar-nodos-dge":
    from utils.calculo_cache import CalculoCache
    from config.app_config import DATA_DIR
    
    # RECARGAR estructura desde archivo
    ruta_actual = DATA_DIR / "actual.estructura.json"
    estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
    
    # ... resto del código (sin cambios)
```

**Resultado**: Modal siempre muestra nodos del archivo más reciente.

---

### 3. Vista DGE (`components/vista_diseno_geometrico.py`)

**Cambio**: Función `generar_resultados_dge()` ya tenía el parámetro `mostrar_alerta_cache=False`

**Sin cambios necesarios** - La función ya estaba preparada para este comportamiento.

---

## Comportamiento Final

### Al Entrar a Vista DGE
✅ Vista vacía con 3 botones: "Calcular", "Cargar desde Cache", "Modificar Nodos"  
✅ NO ejecuta ningún cálculo automáticamente

### Botón "Cargar desde Cache"
✅ Recarga `actual.estructura.json`  
✅ Busca cache con hash de parámetros actuales  
✅ Si existe: Muestra resultados con alerta "Cargado desde cache"  
✅ Si no existe: Mensaje "No hay datos en cache para esta estructura"

### Botón "Calcular"
✅ Recarga `actual.estructura.json` (más reciente)  
✅ Ejecuta cálculo DGE completo  
✅ Guarda/sobreescribe cache  
✅ Muestra resultados SIN alerta cache

### Botón "Modificar Nodos"
✅ Recarga `actual.estructura.json` (más reciente)  
✅ Carga `nodos_editados` desde archivo  
✅ Abre modal con nodos actuales  
✅ Si presiona "Cancelar": Cierra modal, no guarda  
✅ Si presiona "Guardar":
  - Guarda en `actual.estructura.json`
  - Guarda en `{TITULO}.estructura.json`
  - Cierra modal
  - NO calcula automáticamente  
✅ Próxima vez que se abra modal: Carga archivo actualizado

---

## Testing Checklist

- [x] Entrar a DGE → Vista vacía (no calcula)
- [ ] Presionar "Cargar Cache" sin cache → Mensaje "No hay datos"
- [ ] Presionar "Calcular" → Ejecuta y muestra resultados
- [ ] Presionar "Cargar Cache" con cache → Muestra resultados con alerta
- [ ] Abrir modal nodos → Muestra nodos de archivo actual
- [ ] Modificar y cancelar → No guarda
- [ ] Modificar y guardar → Guarda en ambos archivos, no calcula
- [ ] Abrir modal nuevamente → Muestra nodos modificados
- [ ] Calcular después de modificar nodos → Usa nodos modificados

---

## Archivos Modificados

1. `controllers/navigation_controller.py` - 2 cambios (carga inicial y menú)
2. `controllers/geometria_controller.py` - 3 cambios (separar callbacks, recargar en modal)
3. `components/vista_diseno_geometrico.py` - Sin cambios (ya tenía parámetro)

---

## Patrón Seguido

Este fix sigue el mismo patrón que "Calcular Todo":
- Vista vacía al entrar (sin carga automática)
- Callbacks separados para "Cargar" y "Calcular"
- Recarga de archivo antes de operaciones críticas
- Alerta cache solo cuando se carga explícitamente

---

## Fecha de Implementación

18 de diciembre de 2025
