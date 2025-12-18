# Troubleshooting Guide

## Common Issues and Solutions

### Plotly Graphs Not Appearing When Loading from Cache

**Problem**: Interactive Plotly graphs appear when calculated directly in a view, but disappear when loading from cache or executing from "Calcular Todo".

**Root Cause**: Only PNG files were being saved with `fig.write_image()`, but JSON files are required for `dcc.Graph` to display interactive Plotly figures.

**Solution**: Save BOTH formats when caching Plotly figures:
```python
# PNG for static export
fig.write_image(str(png_path), width=1200, height=600)
# JSON for interactive display
fig.write_json(str(json_path))
```

**Key Learning**: Plotly figures require JSON format for interactivity in Dash. Always save both PNG (export) and JSON (display) when caching.

---

### View Reloading After Calculation

**Problem**: After clicking "Calcular" in CMC view, results appear briefly then the view reloads showing cached results instead of fresh ones.

**Root Cause**: Navigation callback had `Input("menu-guardar-estructura", "n_clicks")` which triggered whenever parameters were saved, causing unwanted view reloads.

**Solution**: Remove non-navigation menu items from navigation callback Inputs. Only include menu items that explicitly change views:
```python
@app.callback(
    Output("contenido-principal", "children"),
    Input("btn-inicio", "n_clicks"),
    Input("menu-calculo-mecanico", "n_clicks"),
    # DO NOT include: Input("menu-guardar-estructura", "n_clicks")
    State("estructura-actual", "data"),
)
```

**Key Learning**: Navigation callbacks should ONLY respond to navigation actions, not to save/update actions.

---

### Callbacks Triggering on Page Load

**Problem**: Callbacks execute automatically when page loads, causing unnecessary computations or UI updates.

**Solution**: Add `prevent_initial_call=True` to callback decorator:
```python
@app.callback(
    Output("badge-estructura-actual", "children"),
    Input("estructura-actual", "data"),
    prevent_initial_call=True
)
```

---

### Results Disappearing on Error

**Problem**: When calculation fails, previous results are cleared from the view.

**Solution**: Return `dash.no_update` instead of empty components on error:
```python
try:
    # calculation logic
    return results_html, True, "Éxito", "Cálculo completado", "success", "success"
except Exception as e:
    return dash.no_update, True, "Error", f"Error: {str(e)}", "danger", "danger"
```

---

### Multiple Callbacks Updating Same Output

**Problem**: Dash raises error when multiple callbacks try to update the same Output.

**Solution**: Use `allow_duplicate=True` on all but the first callback:
```python
@app.callback(
    Output("resultados-cmc", "children", allow_duplicate=True),
    Input("btn-calcular-cmc", "n_clicks"),
    prevent_initial_call=True
)
```

---

### State vs Input Confusion

**Problem**: Callback triggers when data changes even though it shouldn't.

**Key Difference**:
- `Input`: Triggers callback when value changes
- `State`: Provides value but does NOT trigger callback

**Example**:
```python
@app.callback(
    Output("contenido-principal", "children"),
    Input("menu-calculo-mecanico", "n_clicks"),  # Triggers on click
    State("estructura-actual", "data"),  # Provides data but doesn't trigger
)
```

---

## Debugging Tips

### Identify Which Callback is Triggering

Use `dash.callback_context` to see what triggered the callback:
```python
ctx = dash.callback_context
if ctx.triggered:
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    print(f"Triggered by: {trigger_id}")
```

### Prevent Unwanted Triggers

Return `dash.no_update` early if trigger is not expected:
```python
ctx = dash.callback_context
if not ctx.triggered:
    return dash.no_update

trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
if trigger_id not in ["expected-button-1", "expected-button-2"]:
    return dash.no_update
```

### Cache Management

When results show as "from cache" unexpectedly:
1. Check if `CalculoCache.verificar_vigencia()` is being called
2. Ensure cache loading doesn't verify vigencia when you want to preserve results
3. Remove vigencia checks from navigation callbacks to always show cached results

### Missing Function Arguments

**Problem**: Function call fails with "missing required positional arguments" error.

**Example**: `CalculoCache.guardar_calculo_sph()` called with single dict argument instead of separate parameters.

**Solution**: Check function signature and pass arguments individually:
```python
# Wrong
CalculoCache.guardar_calculo_sph(nombre, calculo_dict)

# Correct
CalculoCache.guardar_calculo_sph(nombre, parametros, resultados, desarrollo_texto)
```

**Key Learning**: Always verify function signatures when calling from different contexts (direct call vs. orchestrated call).

---

### Orchestrated Calculations

**Pattern**: When implementing "Calcular Todo" or similar orchestration:
1. Reuse existing calculation functions from individual controllers
2. Reuse existing result generation functions from individual views
3. Don't duplicate logic - call the same functions used in individual views
4. Ensure all cache operations save complete data (including JSON for Plotly)
5. Test that cached results display identically whether calculated individually or orchestrated

**Anti-pattern**: Creating separate calculation logic for orchestrated workflows leads to inconsistencies.

---

## Performance Optimization

### Avoid Redundant Callbacks

- Don't add Inputs that aren't related to the callback's purpose
- Use `prevent_initial_call=True` liberally
- Return `dash.no_update` when no update is needed

### List Building for Dash Components

**Problem**: Components not appearing when using `.extend([component1, component2])`.

**Solution**: Use `.append()` for each component individually:
```python
# Preferred
resultados.append(html.H6("Title"))
resultados.append(dcc.Graph(figure=fig))

# Avoid
resultados.extend([html.H6("Title"), dcc.Graph(figure=fig)])
```

**Key Learning**: Individual `.append()` calls ensure proper component registration in Dash's component tree.

### Minimize File I/O in Callbacks

- Cache file reads in memory when possible
- Avoid reading navigation state file on every callback
- Use Dash Stores for frequently accessed data

### Async Operations

For long-running calculations, use threading to avoid blocking:
```python
import threading

def guardar_async():
    CalculoCache.guardar_calculo_cmc(...)

threading.Thread(target=guardar_async, daemon=True).start()
```

---

## Lessons Learned

### Dual Format Storage for Plotly

**Context**: Implementing "Calcular Todo" feature that orchestrates multiple calculations.

**Issue**: Plotly graphs appeared when calculated in individual views but not when executed from orchestrated workflow or loaded from cache.

**Root Cause**: Cache system only saved PNG files (`fig.write_image()`), but Dash's `dcc.Graph` component requires JSON format to display interactive Plotly figures.

**Resolution**:
1. Modified `CalculoCache.guardar_calculo_cmc()` to save both PNG and JSON
2. Added `fig.write_json()` call for each Plotly figure
3. Updated `ejecutar_calculo_cmc_automatico()` to generate and pass all figure objects including `fig_guardia2`

**Key Takeaway**: When caching Plotly figures for Dash applications:
- PNG: For static export and documentation
- JSON: For interactive display in `dcc.Graph` components
- Both formats must be saved during the same cache operation
- Missing JSON files cause graphs to silently fail to render

---

### Cache File Naming with Spaces

**Context**: Implementing node editor feature with cache persistence.

**Issue**: Cache files saved with structure name "2x220 DTT SAN JORGE PRUEBAS" but loaded with different name "KACHI-1x220-Sst-0a1500". Cache appeared to save successfully but couldn't be loaded.

**Root Cause**: 
1. `estructura_actual` State in Dash callbacks contains stale data from previous session
2. File names with spaces cause path resolution issues
3. Different TITULO values between save and load operations

**Resolution**:
1. Replace spaces with underscores in ALL cache methods: `nombre_estructura.replace(' ', '_')`
2. Applied to: `guardar_calculo_cmc()`, `cargar_calculo_cmc()`, `guardar_calculo_dge()`, `cargar_calculo_dge()`, `guardar_calculo_dme()`, `cargar_calculo_dme()`, `guardar_calculo_sph()`, `cargar_calculo_sph()`, `guardar_calculo_arboles()`, `cargar_calculo_arboles()`, `guardar_calculo_todo()`, `cargar_calculo_todo()`
3. Ensures consistent file naming across all cache operations

**Key Takeaway**: 
- Always sanitize file names by replacing spaces with underscores
- Apply sanitization consistently in BOTH save and load operations
- File system paths with spaces can cause silent failures
- Dash State can contain stale data - reload from file when critical

---

### Nodos Editados Persistence

**Context**: Implementing editable nodes feature in DGE with persistence across calculations.

**Issue**: Nodes saved in JSON but not appearing in calculations or cache after reload.

**Root Cause**:
1. `estructura_actual` State not updated after saving nodes
2. `nodes_key` updated BEFORE applying edited nodes instead of AFTER
3. Cache saved with 14 nodes (pre-edit) instead of 15 nodes (post-edit)

**Resolution**:
1. Force reload `estructura_actual` from file after saving: `state.estructura_manager.cargar_estructura(ruta_actual)`
2. Call `_actualizar_nodes_key()` AFTER `importar_nodos_editados()` completes
3. Move `listar_nodos()` to AFTER nodes are applied
4. Sequence: dimensionar → aplicar nodos → actualizar nodes_key → listar → guardar cache

**Key Takeaway**:
- Dash State is NOT automatically synchronized with file changes
- Always reload from file when persistence is critical
- Update derived data structures (like `nodes_key`) AFTER modifications complete
- Cache must capture final state, not intermediate state

---

### Estructura Actual Path Configuration

**Context**: Loading structures from DB and saving parameters.

**Issue**: When loading structure from DB, `actual.estructura.json` was not being updated. Cache was saved/loaded with wrong structure name.

**Root Cause**:
1. `ARCHIVO_ACTUAL = Path("actual.estructura.json")` was relative path pointing to project root
2. Should be `DATA_DIR / "actual.estructura.json"` to point to `data/` directory
3. Callbacks were saving to wrong location, file never updated

**Resolution**:
1. Changed `app_config.py`: `ARCHIVO_ACTUAL = DATA_DIR / "actual.estructura.json"`
2. All callbacks now correctly save/load from `data/actual.estructura.json`

**Key Takeaway**:
- Always use absolute paths or paths relative to known directories (like DATA_DIR)
- Verify file paths are correct when implementing file operations
- Test file save/load operations to ensure files are created in expected locations

---

### Dash State Staleness in Callbacks

**Context**: Loading structure from DB, adjusting parameters, then calculating DGE.

**Issue**: Even after loading new structure and saving parameters, calculations used old structure data.

**Root Cause**:
1. Dash State (`estructura-actual`) is passed to callbacks but not automatically updated when files change
2. Callbacks that modify files don't automatically refresh State for other callbacks
3. State becomes stale across multiple callback executions

**Resolution**:
1. **Always reload from file** at the start of critical callbacks:
   ```python
   from config.app_config import DATA_DIR
   estructura_actual = state.estructura_manager.cargar_estructura(DATA_DIR / "actual.estructura.json")
   ```
2. Applied to: `guardar_parametros_ajustados()`, `calcular_diseno_geometrico()`, all calculation callbacks
3. Don't trust State data for file-backed information - always reload

**Key Takeaway**:
- Dash State is NOT a reliable source of truth for file-backed data
- Always reload from file when data consistency is critical
- State is useful for UI state, not for persistent data
- Pattern: Load from file → Process → Save to file → Return updated data to State

---

### Nodos Editados Contamination

**Context**: Creating new structure file from configuration cell.

**Issue**: New structure file contained `nodos_editados` from previous structure (220kV horizontal) which contaminated new structure (33kV vertical).

**Root Cause**:
1. Template file or source structure had `nodos_editados` array populated
2. When creating new structure, copied entire structure including old nodes
3. Nodes from different structure geometry applied to new structure

**Resolution**:
1. Always initialize `nodos_editados: []` when creating new structures
2. Added check in `cargar_estructura_desde_db()` to ensure `nodos_editados` is initialized
3. Clear nodos_editados when structure parameters change significantly (tension, disposition, terna)

**Key Takeaway**:
- Always initialize `nodos_editados` as empty array for new structures
- Validate that nodos_editados are compatible with current structure geometry
- Consider clearing nodos_editados when major structure parameters change

---

### Estados Climáticos Configuration

**Context**: Implementing automatic CMC calculation from DGE without passing through CMC view.

**Issue**: Estados climáticos were hardcoded in `ejecutar_calculo_cmc_automatico()` with Tmax=35°C, but some structures need Tmax=40°C.

**Root Cause**:
1. Estados climáticos defined as constants in code instead of configuration
2. No way to customize estados per structure
3. Different zones (A, B, C, D, E) have different temperature requirements per AEA 95301

**Resolution**:
1. Added `estados_climaticos` field to structure JSON files
2. Modified `ejecutar_calculo_cmc_automatico()` to read from `estructura_actual.get("estados_climaticos", {...defaults...})`
3. Updated plantilla.estructura.json with AEA 95301 zona D estados
4. Each structure can now define custom estados climáticos

**Key Takeaway**:
- Configuration should be data-driven, not hardcoded
- Store configuration in JSON files for easy customization
- Provide sensible defaults but allow overrides
- Follow standards (AEA 95301) for default values per zone

---

### DGE Vista Vacía - Comportamiento Similar a Calcular Todo

**Context**: Implementando fix para que vista DGE no cargue cache automáticamente al entrar.

**Issue**: Vista DGE calculaba/cargaba automáticamente al entrar, sin dar control al usuario sobre cuándo cargar cache vs. calcular nuevo.

**Root Cause**:
1. Navigation controller cargaba cache automáticamente: `calculo_guardado = CalculoCache.cargar_calculo_dge(nombre_estructura)`
2. Callback único manejaba ambos botones (Calcular y Cargar Cache) juntos
3. No había separación clara entre "cargar desde cache" y "calcular nuevo"

**Resolution**:
1. **Navigation Controller**: Siempre pasar `None` como `calculo_guardado`
   ```python
   return crear_vista_diseno_geometrico(estructura_actual, None)
   ```
2. **Separar callbacks**: Crear DOS callbacks independientes
   - `cargar_cache_dge()`: Solo carga cuando se presiona "Cargar desde Cache"
   - `calcular_diseno_geometrico()`: Solo calcula cuando se presiona "Calcular"
3. **Recargar archivo**: Ambos callbacks recargan `actual.estructura.json` al inicio
4. **Alerta cache**: Solo mostrar cuando se carga explícitamente (`mostrar_alerta_cache=True`)

**Key Takeaway**:
- Vista debe iniciar vacía, dar control explícito al usuario
- Separar callbacks mejora claridad y debugging
- Siempre recargar archivo antes de operaciones críticas
- Patrón: Vista vacía → Usuario elige acción → Ejecutar acción específica

---

### Modal Nodos - Callback Ejecutándose en Carga Inicial

**Context**: Implementando modal de edición de nodos en DGE.

**Issue**: Al cargar la app o navegar a DGE, el callback del modal se ejecutaba automáticamente mostrando mensaje "No hay nodos disponibles" sin que el usuario presionara el botón.

**Root Cause**:
1. Callback con `prevent_initial_call=True` pero sin verificación de clicks reales
2. Dash ejecuta callback si hay `ctx.triggered` incluso en carga inicial
3. Botones pueden tener valores iniciales que disparan el callback

**Resolution**:
1. Agregar verificación explícita de clicks antes de procesar:
   ```python
   # Verificar que realmente hubo un click (no carga inicial)
   if not n_abrir and not n_cancelar and not n_guardar:
       return dash.no_update, dash.no_update, ...
   ```
2. Agregar Toast de notificación cuando no hay nodos disponibles
3. Agregar mensajes debug para diagnosticar el problema

**Key Takeaway**:
- `prevent_initial_call=True` NO es suficiente para evitar ejecuciones no deseadas
- Siempre verificar que los Inputs tienen valores válidos (clicks reales)
- Usar mensajes debug para identificar cuándo y por qué se ejecutan callbacks
- Pattern: Verificar clicks → Verificar trigger → Procesar acción

---

### Toast Notifications para Feedback de Usuario

**Context**: Usuario presiona "Editar Nodos" sin haber ejecutado DGE primero.

**Issue**: Modal no abría y no había feedback sobre por qué no funcionaba.

**Root Cause**:
1. Callback retornaba sin abrir modal ni mostrar mensaje
2. Usuario no sabía que necesitaba ejecutar DGE primero
3. Falta de comunicación clara de requisitos previos

**Resolution**:
1. Agregar outputs de Toast al callback del modal:
   ```python
   Output("toast-notificacion", "is_open", allow_duplicate=True),
   Output("toast-notificacion", "header", allow_duplicate=True),
   Output("toast-notificacion", "children", allow_duplicate=True),
   Output("toast-notificacion", "icon", allow_duplicate=True),
   Output("toast-notificacion", "color", allow_duplicate=True),
   ```
2. Mostrar mensaje claro cuando no hay nodos:
   ```python
   return False, dash.no_update, dash.no_update, True, "Advertencia", \
          "Ejecute primero el cálculo DGE para crear nodos que luego puedan ser editados.", \
          "warning", "warning"
   ```
3. Usar `allow_duplicate=True` para evitar conflictos con otros callbacks

**Key Takeaway**:
- Siempre dar feedback al usuario cuando una acción no puede completarse
- Explicar claramente qué debe hacer el usuario (requisitos previos)
- Toast notifications son ideales para mensajes temporales
- Usar colores apropiados: warning (amarillo) para advertencias, danger (rojo) para errores

---

### Debug Messages para Troubleshooting

**Context**: Diagnosticando por qué el modal de nodos no abría.

**Issue**: Sin mensajes debug, era difícil saber dónde estaba fallando el callback.

**Resolution**:
1. Agregar mensajes debug en puntos clave del callback:
   ```python
   print("🔵 DEBUG: Botón 'Editar Nodos' presionado")
   print(f"📂 DEBUG: Estructura recargada: {estructura_actual.get('TITULO', 'N/A')}")
   print("⚠️  DEBUG: No hay nodos disponibles")
   print(f"✅ DEBUG: {len(nodos_dict)} nodos encontrados, generando tabla...")
   print(f"✅ DEBUG: Tabla generada, abriendo modal con {len(nodos_data)} nodos")
   ```
2. Usar emojis para identificar rápidamente el tipo de mensaje
3. Incluir información relevante (nombres, cantidades, estados)

**Key Takeaway**:
- Mensajes debug son esenciales para troubleshooting
- Usar emojis para identificar visualmente tipos de mensajes
- Incluir información contextual (nombres, cantidades, estados)
- Dejar mensajes debug en producción para facilitar soporte
- Pattern: 🔵 Acción iniciada → 📂 Datos cargados → ⚠️ Advertencia → ✅ Éxito

---

### Gráfico 3D de Nodos con Plotly

**Context**: Implementando gráfico 3D isométrico de nodos para DGE.

**Issue 1**: Nombres de nodos aparecían en eje X y coordenadas Z aparecían como etiquetas de texto.

**Root Cause**: Orden incorrecto al desempaquetar tuplas. La tupla era `(nombre, x, y, z)` pero se desempaquetaba como si fuera `(x, y, z, nombre)`.

**Resolution**:
```python
# Incorrecto - nombres en X, coordenadas en text
for nombre, x, y, z in nodos_todos:
    nodos_conductor.append((nombre, x, y, z))

# Correcto - coordenadas en X/Y/Z, nombres en text
for nombre, x, y, z in nodos_todos:
    nodos_conductor.append((x, y, z, nombre))
```

**Issue 2**: JSON completo del gráfico se imprimía en consola, spameando el terminal.

**Root Cause**: `fig.show()` en Plotly imprime la representación JSON completa de la figura.

**Resolution**: Eliminar `fig.show()` y solo retornar la figura. Dash se encarga de renderizarla.
```python
# Incorrecto
fig.show()
return fig

# Correcto
return fig
```

**Issue 3**: Grilla cada 2 metros en lugar de cada 1 metro.

**Root Cause**: Plotly usa `dtick` automático basado en rango de datos.

**Resolution**: Especificar `dtick=1` explícitamente en cada eje.
```python
xaxis=dict(
    title='X [m]',
    type='linear',
    dtick=1  # Grilla cada 1 metro
)
```

**Key Takeaway**:
- Orden de tuplas es crítico: siempre desempaquetar en el orden correcto (x, y, z, nombre)
- `fig.show()` en Plotly imprime JSON completo - solo usar en notebooks, no en aplicaciones
- Usar `dtick` para controlar espaciado de grilla en gráficos 3D
- `type='linear'` fuerza ejes numéricos, evita que Plotly use categorías
- Vista isométrica: `camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2))` con Y negativo para Z=0 abajo
