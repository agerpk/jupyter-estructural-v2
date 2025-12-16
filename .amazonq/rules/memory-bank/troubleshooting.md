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
