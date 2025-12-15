# Development Guidelines

## Code Quality Standards

### Documentation Patterns
- **Module-level docstrings**: Every module starts with triple-quoted docstring describing purpose
- **Class docstrings**: Classes include description of purpose and responsibilities
- **Method docstrings**: Methods document parameters with Args section, return values, and purpose
- **Inline comments**: Used sparingly for complex logic, prefixed with single #
- **Spanish in user-facing text**: Print statements and user messages in Spanish
- **English in code**: Variable names, function names, and technical comments in English

### Naming Conventions
- **Classes**: PascalCase (e.g., `NodoEstructural`, `Estructura_AEA`, `EstructuraAEA_Geometria`)
- **Functions/Methods**: snake_case (e.g., `dimensionar_unifilar`, `calcular_reacciones_tiros_cima`)
- **Variables**: snake_case (e.g., `altura_total`, `peso_conductor_base`, `df_cargas_totales`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `TABLA_TENSION_MAXIMA`, `COLORES`, `APP_TITLE`)
- **Private methods**: Prefix with underscore (e.g., `_calcular_parametros_cabezal`, `_crear_nodos_estructurales`)
- **Dictionary keys**: snake_case for internal data, PascalCase for user-facing configuration

### Code Structure
- **Imports**: Standard library first, then third-party, then local imports, separated by blank lines
- **Class organization**: Constants → __init__ → public methods → private methods
- **Method length**: Keep methods focused; extract complex logic into private helper methods
- **Line length**: Generally under 120 characters, break long lines logically
- **Indentation**: 4 spaces (no tabs)

## Architectural Patterns

### MVC Architecture
- **Models** (`/models/`): Data structures and state management (e.g., `AppState`)
- **Views** (`/views/`): Layout definitions using Dash components
- **Controllers** (`/controllers/`): Business logic and Dash callbacks
- **Separation**: Controllers never directly manipulate DOM, views never contain logic

### Manager Pattern
- Specialized manager classes for domain concerns:
  - `EstructuraManager`: Structure persistence and file operations
  - `CableManager`: Cable database operations
  - `HipotesisManager`: Hypothesis configuration management
  - `CalculoCache`: Calculation result caching
- Managers encapsulate file I/O and data transformation logic

### State Management
- Centralized `AppState` singleton pattern
- State contains references to managers and calculation objects
- Controllers access state for data operations
- Dash stores (`dcc.Store`) for client-side state persistence

### Callback Registration
- Each controller module has `register_callbacks(app)` function
- Callbacks registered in main `app.py` during initialization
- Use `prevent_initial_call=True` to avoid unnecessary initial executions
- Use `dash.exceptions.PreventUpdate` to skip updates when conditions not met

## Common Implementation Patterns

### Data Validation
```python
# Validate required parameters with clear error messages
if self.peso_estructura == 0:
    raise ValueError("El parámetro 'peso_estructura' es requerido y debe ser mayor a 0")

# Check for None values before operations
if self.peso_cadena is None:
    raise ValueError("El parámetro 'peso_cadena' es requerido para el cálculo de theta_max")
```

### Dictionary-based Configuration
```python
# Use dictionaries for lookup tables and configuration
TABLA_TENSION_MAXIMA = {
    13.2: 13.8, 33: 36, 66: 72.5, 132: 145, 220: 245, 500: 550
}

# Access with .get() for safe defaults
self.tension_maxima = self.TABLA_TENSION_MAXIMA.get(
    self.tension_nominal, self.tension_nominal * 1.1
)
```

### Calculation Result Storage
```python
# Store results in dictionaries with descriptive keys
self.resultados_reacciones[nombre_hipotesis] = {
    'Reaccion_Fx_daN': round(Fx, 1),
    'Reaccion_Fy_daN': round(Fy, 1),
    'Tiro_resultante_daN': round(Tiro_resultante, 1),
    'Angulo_grados': round(angulo_grados, 1)
}

# Convert to DataFrame for tabular display
self.df_reacciones = pd.DataFrame.from_dict(self.resultados_reacciones, orient='index')
```

### Progress Reporting
```python
# Use emoji and Spanish for user-friendly console output
print(f"✅ DIMENSIONAMIENTO COMPLETADO")
print(f"📐 DIMENSIONANDO ESTRUCTURA UNIFILAR...")
print(f"❌ Error en hipótesis {codigo_hip}: {e}")
print(f"⚠️ Advertencia: {mensaje}")
```

### File Operations
```python
# Use pathlib.Path for cross-platform compatibility
from pathlib import Path
ruta_archivo = DATA_DIR / f"{nombre}.json"

# Ensure directories exist before writing
ruta_archivo.parent.mkdir(parents=True, exist_ok=True)

# Use context managers for file operations
with open(ruta_archivo, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

### Matplotlib Figure Management
```python
# Create figures with explicit size
plt.figure(figsize=(12, 10))

# Always close figures after saving to prevent memory leaks
plt.savefig(ruta_imagen, dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)

# Use matplotlib.use('Agg') for non-interactive backend in production
import matplotlib
matplotlib.use('Agg')
```

### DataFrame Operations
```python
# Create DataFrames with explicit column names
df = pd.DataFrame([parametros])

# Use .iloc[0] to access first row safely
valor = self.parametros_cabezal['theta_max'].iloc[0]

# Filter DataFrames with boolean indexing
filtro = (df['Elemento'] == 'Conductor') & (df['Estado'] == 'Vmax')
resultado = df[filtro]['Magnitud'].iloc[0]
```

### Error Handling
```python
# Use try-except with specific error messages
try:
    resultado = calcular_valor()
except Exception as e:
    print(f"❌ Error calculando theta_max: {e}")
    return valor_default

# Return structured results from functions
return {
    'exito': True,
    'mensaje': 'Cálculo completado exitosamente',
    'datos': resultados
}
```

### Dash Callback Patterns
```python
@app.callback(
    Output("component-id", "property"),
    Input("trigger-id", "n_clicks"),
    State("data-store", "data"),
    prevent_initial_call=True
)
def callback_function(n_clicks, stored_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    # Process data
    result = process(stored_data)
    
    return result
```

### Hash-based Caching
```python
# Generate hash from structure parameters for cache keys
import hashlib
import json

estructura_str = json.dumps(estructura_dict, sort_keys=True)
hash_estructura = hashlib.md5(estructura_str.encode()).hexdigest()

# Use hash in filenames for cache invalidation
nombre_archivo = f"{titulo}.{hash_estructura}.png"
```

## Testing Patterns

### Console Output Validation
- Use print statements with clear formatting for debugging
- Include section headers with emoji for visual separation
- Display calculated values with appropriate precision (e.g., `:.2f` for meters)

### Data Validation
- Verify DataFrame shapes before operations
- Check for empty DataFrames with `.empty` property
- Validate dictionary keys exist before access with `.get()`

## Performance Considerations

### Lazy Evaluation
- Calculate expensive values only when needed
- Cache calculation results to avoid redundant computations
- Use `hasattr()` to check if calculations already performed

### Memory Management
- Close matplotlib figures after use
- Clear large DataFrames when no longer needed
- Use generators for large data processing when possible

## Common Idioms

### Coordinate Handling
```python
# Unpack coordinates from tuples
x, y, z = coordenadas
x_nodo, y_nodo, z_nodo = self.nodes_key[nodo]

# Filter nodes by plane (XZ plane only)
if abs(y) > 0.001:
    continue
```

### Rounding for Display
```python
# Round to 2 decimals for display
valor_display = round(valor, 2)

# Format strings with precision
texto = f"Altura: {altura:.2f} m"
```

### List Comprehensions
```python
# Filter and transform in single expression
nodos_conductor = [n for n in self.nodes_key.keys() if n.startswith(('C1_', 'C2_', 'C3_'))]

# Extract values from dictionaries
alturas = [coord[2] for coord in nodes_key.values()]
```

### Dictionary Comprehensions
```python
# Initialize dictionaries with default values
cargas_hipotesis = {nombre: [0.00, 0.00, 0.00] for nombre in self.nodes_key.keys()}

# Filter dictionaries
nodos_cat = {k: v for k, v in nodes_key.items() if k.startswith(prefijo)}
```
