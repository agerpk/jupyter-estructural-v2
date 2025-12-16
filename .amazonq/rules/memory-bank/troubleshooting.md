# Troubleshooting Guide

## Common Issues and Solutions

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

---

## Performance Optimization

### Avoid Redundant Callbacks

- Don't add Inputs that aren't related to the callback's purpose
- Use `prevent_initial_call=True` liberally
- Return `dash.no_update` when no update is needed

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
