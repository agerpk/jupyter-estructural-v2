# Próxima Sesión - Contexto y Tareas Pendientes

## Estado Actual del Proyecto

### Fixes Completados en Sesión Anterior ✅

1. **Cache Alert Messages** - Alertas "cargado desde cache" solo aparecen cuando se carga explícitamente
   - Archivos: `vista_calcular_todo.py`, `vista_diseno_geometrico.py`, `vista_diseno_mecanico.py`, `vista_arboles_carga.py`
   - Parámetro `mostrar_alerta_cache=False` por defecto

2. **DataFrame de Cargas** - `df_cargas_completo` ahora se genera y guarda correctamente
   - Archivo: `controllers/ejecutar_calculos.py` líneas 66-69
   - Llama a `estructura_mecanica.generar_dataframe_cargas()` antes de guardar cache

3. **Vista Calcular Todo - Sin Carga Automática** - Vista inicia vacía
   - Archivo: `controllers/navigation_controller.py`
   - Siempre pasa `None` como `calculo_guardado`

4. **Botón Primer Click** - Responde al primer click
   - Archivo: `components/vista_calcular_todo.py`
   - Eliminado `n_clicks=0`

### Sistema Funcionando Correctamente
- Vista "Calcular Todo" funciona con 1 solo click
- DataFrame de cargas se guarda: `17 nodos × 20 columnas`
- Todos los módulos ejecutan sin errores
- Cache se guarda correctamente (PNG + JSON para Plotly)

---

## TAREA PENDIENTE: Fix DGE Comportamiento

### Problema Actual
Vista DGE (Diseño Geométrico de Estructura) calcula automáticamente al entrar. Debe comportarse como "Calcular Todo": vista vacía, solo calcula al presionar botón.

### Comportamiento Requerido

#### Al Entrar a Vista DGE
- Vista vacía con 3 botones: "Calcular", "Cargar desde Cache", "Modificar Nodos"
- NO ejecuta ningún cálculo automáticamente

#### Botón "Cargar desde Cache"
1. Recargar `actual.estructura.json`
2. Calcular hash de parámetros
3. Buscar cache con ese hash
4. Si existe: Mostrar resultados con alerta cache
5. Si no existe: Mensaje "No hay datos en cache"

#### Botón "Calcular"
1. Recargar `actual.estructura.json` (más reciente)
2. Ejecutar cálculo DGE completo (sin pasar por cache)
3. Guardar/sobreescribir cache
4. Mostrar resultados sin alerta cache

#### Botón "Modificar Nodos"
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

---

## Archivos a Modificar

### 1. `controllers/navigation_controller.py`
**Líneas a cambiar**: ~100 (carga inicial) y ~180 (menú)

**Cambio**: Eliminar carga automática de cache al entrar a DGE
```python
# ANTES
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

Aplicar el mismo cambio en el trigger del menú (línea ~180).

### 2. `controllers/geometria_controller.py`
**Línea actual**: 780 - Callback único que maneja ambos botones

**Cambio**: Separar en DOS callbacks independientes

**Callback 1: Cargar desde Cache** (nuevo)
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

**Callback 2: Calcular** (modificar existente)
- Eliminar toda la lógica de "cargar cache"
- Solo ejecutar cálculo cuando trigger es "btn-calcular-geom"
- Recargar `actual.estructura.json` al inicio
- NO pasar por cache para mostrar resultados
- Guardar cache al final

**Callback Modal Nodos** (línea ~350)
- Agregar recarga de `actual.estructura.json` al inicio
- Cargar `nodos_editados` desde archivo recargado

### 3. `components/vista_diseno_geometrico.py`
**Función**: `generar_resultados_dge()`

**Cambio**: Agregar parámetro `mostrar_alerta_cache=False`
```python
def generar_resultados_dge(calculo_guardado, estructura_actual, mostrar_alerta_cache=False):
    resultados = []
    
    if mostrar_alerta_cache:
        resultados.append(ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=True))
    
    # ... resto del código existente
```

---

## Archivos de Referencia para Leer

### CRÍTICO - Leer Primero
1. **`docs/fix_dge_comportamiento.md`** - Plan detallado completo del fix
2. **`docs/18dic2025_12-29pm_fixes.md`** - Fixes completados en sesión anterior

### Para Implementación
3. **`controllers/navigation_controller.py`** - Líneas 100 y 180
4. **`controllers/geometria_controller.py`** - Línea 780 (callback principal)
5. **`components/vista_diseno_geometrico.py`** - Función `generar_resultados_dge()`

### Referencia de Patrón Correcto
6. **`controllers/calcular_todo_controller.py`** - Ejemplo de comportamiento correcto (vista vacía, botones separados)
7. **`components/vista_calcular_todo.py`** - Ejemplo de vista que NO carga cache automáticamente

---

## Patrón a Seguir (Calcular Todo)

### Vista Vacía al Entrar
```python
# navigation_controller.py
return crear_vista_calcular_todo(estructura_actual, None)  # Siempre None
```

### Callbacks Separados
```python
# Callback 1: Cargar Cache
@app.callback(
    Output(..., allow_duplicate=True),
    Input("btn-cargar-cache", "n_clicks"),
    prevent_initial_call=True
)
def cargar_cache(n_clicks):
    # Recargar archivo
    # Buscar cache
    # Mostrar con alerta

# Callback 2: Calcular
@app.callback(
    Output(...),
    Input("btn-calcular", "n_clicks"),
    prevent_initial_call=True
)
def calcular(n_clicks):
    # Recargar archivo
    # Ejecutar cálculo
    # Guardar cache
    # Mostrar sin alerta
```

---

## Testing Checklist

Después de implementar, verificar:

- [ ] Entrar a DGE → Vista vacía (no calcula)
- [ ] Presionar "Cargar Cache" sin cache → Mensaje "No hay datos"
- [ ] Presionar "Calcular" → Ejecuta y muestra resultados
- [ ] Presionar "Cargar Cache" con cache → Muestra resultados con alerta
- [ ] Abrir modal nodos → Muestra nodos de archivo actual
- [ ] Modificar y cancelar → No guarda
- [ ] Modificar y guardar → Guarda en ambos archivos, no calcula
- [ ] Abrir modal nuevamente → Muestra nodos modificados
- [ ] Calcular después de modificar nodos → Usa nodos modificados

---

## Notas Importantes

### Siempre Recargar Archivo
Antes de cualquier operación crítica:
```python
from config.app_config import DATA_DIR
ruta_actual = DATA_DIR / "actual.estructura.json"
estructura_actual = state.estructura_manager.cargar_estructura(ruta_actual)
```

### Dash State es Stale
NO confiar en `State("estructura-actual", "data")` para datos persistentes. Siempre recargar desde archivo.

### Parámetro mostrar_alerta_cache
- `True`: Solo cuando se carga explícitamente desde cache
- `False`: Cuando se calcula nuevo o se ejecuta desde "Calcular Todo"

---

## Comando para Iniciar

```bash
# Leer archivos de referencia
fsRead: docs/fix_dge_comportamiento.md
fsRead: docs/18dic2025_12-29pm_fixes.md
fsRead: controllers/navigation_controller.py
fsRead: controllers/geometria_controller.py (líneas 750-850)
```

---

## Resumen Ejecutivo

**Objetivo**: Hacer que DGE se comporte como "Calcular Todo" - vista vacía al entrar, solo calcula al presionar botón.

**Archivos**: 3 archivos a modificar
**Complejidad**: Media (callback grande a separar)
**Patrón**: Seguir `calcular_todo_controller.py`
**Testing**: 8 casos de prueba

**Próximo paso**: Leer `docs/fix_dge_comportamiento.md` y comenzar implementación.
