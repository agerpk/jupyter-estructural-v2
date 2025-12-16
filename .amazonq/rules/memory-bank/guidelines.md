# Development Guidelines

## Code Quality Standards

### File Organization
- Empty `__init__.py` files mark packages without exposing internal APIs
- Package structure follows clear separation: components, controllers, models, utils, views
- Core calculation modules remain at root level for backward compatibility with notebooks

### Naming Conventions
- **Variables**: Snake_case with descriptive names (e.g., `cable_conductor_id`, `TIPO_ESTRUCTURA`)
- **Constants**: UPPERCASE_WITH_UNDERSCORES for configuration values (e.g., `ALTURA_MINIMA_CABLE`, `TENSION`)
- **Functions**: snake_case with verb prefixes (e.g., `cargar_datos_postes`, `agregar_cable`)
- **Classes**: PascalCase with descriptive suffixes (e.g., `Cable_AEA`, `EstructuraAEA_Geometria`, `PostesHormigon`)
- **Files**: snake_case for modules, PascalCase for class-based modules (e.g., `DatosCables.py`, `PostesHormigon.py`)

### Documentation Standards
- Module-level docstrings in triple quotes describing purpose
- Function docstrings explaining return values and purpose
- Inline comments for complex logic or important notes
- Spanish language used throughout for domain-specific terminology

### Code Formatting
- Indentation: 4 spaces (standard Python)
- Line continuation: Use backslash or implicit continuation within parentheses
- String formatting: f-strings preferred for readability
- Dictionary formatting: Multi-line with proper indentation for large data structures

## Structural Conventions

### Data Storage Patterns
- **Nested dictionaries** for hierarchical data (pole specifications, cable properties)
- **Dictionary keys**: String identifiers matching domain terminology
- **Tuple values**: (diameter, weight) pairs for pole specifications
- **JSON files**: Configuration persistence and calculation results
- **CSV exports**: Tabular calculation outputs

### Configuration Management
- Global configuration variables at module/notebook top
- Grouped by logical sections with comment headers (e.g., `# ===== CONFIGURACIÓN DISEÑO DE CABEZAL =====`)
- Boolean flags for feature toggles (e.g., `MOSTRAR_C2`, `HG_CENTRADO`)
- Numeric constants with units in comments (e.g., `L_vano = 400.0 # m`)

### Error Handling
- Validation at controller level before calculations
- Graceful degradation with default values
- User-friendly error messages in Spanish

## Semantic Patterns

### Data Structure Patterns

#### Hierarchical Dictionary Pattern
Used extensively for organizing related data by categories:
```python
datos = {
    'category_name': {
        'rango': (min_value, max_value),
        'longitudes': [list_of_values],
        'datos': {}  # Nested data
    }
}
```
Frequency: Very high (pole data, cable data, calculation results)

#### Property Dictionary Pattern
Objects defined as dictionaries with standardized keys:
```python
cable_properties = {
    "material": "Al/Ac",
    "seccion_nominal": "435/55",
    "diametro_total_mm": 28.8,
    "peso_unitario_dan_m": 1.653,
    "carga_rotura_minima_dan": 13645.0
}
```
Frequency: High (cable definitions, structure configurations)

#### Tuple Unpacking Pattern
Compact data storage with positional meaning:
```python
# (diameter, weight) tuples
{7.0: (170, 504), 7.5: (170, 555)}
```
Frequency: Very high in pole specifications

### Calculation Patterns

#### State-Based Calculation Pattern
Calculations organized by climatic states:
```python
estados_climaticos = {
    "I": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0},
    "II": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0}
}
```
Frequency: High in mechanical calculations

#### Restriction Dictionary Pattern
Constraints defined per state and component:
```python
restricciones = {
    "conductor": {"tension_max_porcentaje": {"I": 0.25, "II": 0.40}},
    "guardia": {"tension_max_porcentaje": {"I": 0.7, "II": 0.70}}
}
```
Frequency: Medium (design constraints)

### Object-Oriented Patterns

#### Factory Pattern
Library classes create and manage object instances:
```python
lib_cables = LibCables()
cable = Cable_AEA(id_cable=nombre, nombre=nombre, propiedades=props)
lib_cables.agregar_cable(cable)
```
Frequency: High for cable and structure management

#### Separation of Concerns Pattern
Classes split by responsibility:
- `EstructuraAEA_Geometria`: Geometric definitions
- `EstructuraAEA_Mecanica`: Mechanical calculations
- `EstructuraAEA_Graficos`: Visualization
Frequency: High in core modules

### File Naming Patterns

#### Calculation Result Files
Format: `{project_name}.{calculation_type}.json`
Examples:
- `proyecto.calculoCMC.json` - Cable mechanical calculations
- `proyecto.calculoDGE.json` - Geometric design
- `proyecto.calculoDME.json` - Mechanical design
- `proyecto.calculoSPH.json` - Pole selection
Frequency: Very high (all calculation outputs)

#### Load Tree Diagrams
Format: `{project_name}.arbolcarga.{hash}.HIP_{hypothesis_name}.png`
Example: `proyecto.arbolcarga.5f1946585285b45b359d01968e8bd008.HIP_Suspension_Recta_A0_EDS_(TMA).png`
Frequency: High (one per hypothesis)

### Common Code Idioms

#### Dictionary Comprehension for Data Loading
```python
for rotura, datos_rotura in {
    300: {7.0: (170, 504), 7.5: (170, 555)},
    350: {7.0: (170, 506), 7.5: (170, 558)}
}.items():
    target_dict[rotura] = datos_rotura
```
Frequency: Very high in data initialization

#### String Formatting for File Paths
```python
tipoestructura_nombre_archivo = f"{TIPO_ESTRUCTURA.replace(' ', '_').replace('ó','o').replace('/','_').lower()}"
folder = f"{TITULO}/{tipoestructura_nombre_archivo}"
```
Frequency: High for file operations

#### Conditional Defaults Pattern
```python
TITULO_REEMPLAZO = TITULO if REEMPLAZAR_TITULO_GRAFICO else TIPO_ESTRUCTURA
```
Frequency: Medium for configuration

## Best Practices

### Engineering Calculations
- Always include units in variable names or comments
- Use descriptive variable names matching engineering terminology
- Separate configuration from calculation logic
- Cache expensive calculations to avoid redundancy

### Dash Callback Management
- **CRITICAL**: Avoid adding menu actions (like `menu-guardar-estructura`, `menu-nueva-estructura`) as Inputs to navigation callbacks
- Navigation callbacks should ONLY respond to explicit navigation actions (menu items that change views)
- Use `State` instead of `Input` for data stores (`estructura-actual`) to prevent unwanted callback triggers
- Use `prevent_initial_call=True` on callbacks that update UI elements to avoid initialization cascades
- Return `dash.no_update` instead of empty components to preserve existing content on error
- Use `allow_duplicate=True` when multiple callbacks update the same Output

### Data Persistence
- Use JSON for structured configuration and results
- Include metadata (version, creation date, modification date)
- Maintain backward compatibility with existing file formats
- Use hash-based naming for uniqueness when needed
- Store Plotly figures as JSON to preserve interactivity (zoom, pan, hover)
- Serialize DataFrames with `to_json(orient='split')` to maintain exact format
- Use multiple encoding fallbacks (utf-8, latin-1, cp1252) for Spanish characters

### User Interface
- Spanish language for all user-facing text
- Descriptive labels matching engineering standards
- Validation feedback in real-time
- Progress indicators for long calculations

### Code Reusability
- Core calculation modules independent of UI framework
- Utility functions in dedicated modules
- Manager classes for common operations (cables, structures, files)
- Configuration-driven behavior over hardcoded values
- Centralized view helpers (ViewHelpers class) for cache loading/saving
- Avoid code duplication across views with shared helper methods

### Testing and Validation
- Validate inputs at controller level
- Compare results against known benchmarks
- Export calculation reports for verification
- Visual validation through plots and diagrams

## Domain-Specific Patterns

### AEA Standards Compliance
- Load hypothesis naming follows AEA conventions (A0-A5, B1-B2, C1-C2)
- Climatic states defined per AEA specifications
- Safety factors applied per component type
- Altitude adjustments using AEA formulas

### Electrical Engineering Conventions
- Voltage levels in kV (e.g., 220kV)
- Structure types: Suspensión, Retención, Angular, Terminal
- Cable types: Conductor (Al/Ac), Guard wire (OPGW, Ac)
- Disposition types: triangular, horizontal, vertical

### Structural Engineering Conventions
- Forces in daN (decanewtons)
- Lengths in meters
- Areas in m²
- Angles in degrees
- Pole resistance ratings in daN

## Migration Notes

### From Jupyter to Web Application
- Original notebook cells preserved in `notebooks_backup/`
- Core calculation logic extracted to standalone modules
- UI rebuilt using Dash framework
- State management centralized in AppState model
- File-based persistence maintained for compatibility


## Cache System Architecture

### Cache Storage (calculo_cache.py)
- **Static class**: `CalculoCache` manages all persistence
- **Location**: All cache files stored in `data/cache/` directory
- **Hashing**: MD5 hash of structure parameters (excludes `fecha_creacion`, `fecha_modificacion`, `version`)
- **File naming**: `{nombre}.{tipo_calculo}.json` (e.g., `proyecto.calculoCMC.json`)
- **Image naming**: `{tipo}_{nombre}.{hash}.png` or `.json` for Plotly
- **Git ignore**: Entire `data/cache/` directory ignored

### Cache Types
1. **CMC** - Cable Mechanical Calculations
   - DataFrames: conductor, guardia1, guardia2 (serialized as JSON)
   - Images: CMC_Combinado, CMC_Conductor, CMC_Guardia (PNG + JSON)
   - Console output: Full calculation log

2. **DGE** - Geometric Design
   - Dimensions, structural nodes, calculation memory
   - Images: Estructura, Cabezal

3. **DME** - Mechanical Design
   - DataFrame of reactions per hypothesis
   - Images: DME_Polar, DME_Barras

4. **SPH** - Pole Selection
   - Selected configuration, dimensions, development text
   - No images

5. **ARBOLES** - Load Trees
   - List of images, DataFrame with MultiIndex
   - Images: One per hypothesis

6. **TODO** - Complete Calculation
   - Combined results from all calculation types

### View Helpers (view_helpers.py)
Centralized utilities for cache operations:

#### Image Operations
- `cargar_imagen_base64()` - Load image as base64 string
- `crear_img_component()` - Create html.Img component
- `cargar_imagenes_por_hash()` - Load multiple images by hash pattern
- `guardar_imagen_plotly()` - Save Plotly figure as PNG
- `guardar_imagen_matplotlib()` - Save Matplotlib figure as PNG
- `guardar_imagenes_calculo()` - Save multiple calculation images

#### Interactive Plotly Graphs
- `guardar_figura_plotly_json()` - Save Plotly figure as JSON (preserves interactivity)
- `cargar_figura_plotly_json()` - Load Plotly JSON with multi-encoding support
- `crear_grafico_interactivo()` - Create dcc.Graph from JSON file
- `cargar_graficos_interactivos_por_hash()` - Load multiple interactive graphs

#### UI Components
- `crear_alerta_cache()` - Standard cache alert with validity status
- `crear_pre_output()` - Styled console output component
- `crear_tabla_desde_dataframe()` - Bootstrap table from DataFrame
- `crear_tabla_html_iframe()` - HTML table in iframe

#### Data Formatting
- `limpiar_emojis()` - Remove emojis from text
- `formatear_parametros_estructura()` - Format structure parameters

### Cache Loading Pattern in Views
```python
def generar_resultados_XXX(calculo_guardado, estructura_actual):
    # 1. Extract data from JSON
    datos = calculo_guardado.get('resultados')
    hash_params = calculo_guardado.get('hash_parametros')
    
    # 2. Load DataFrames from JSON
    df = pd.read_json(datos['df_html'], orient='split')
    
    # 3. Load interactive graphs
    patrones = [("Grafico.{hash}.json", "Título", {})]
    graficos = ViewHelpers.cargar_graficos_interactivos_por_hash(hash_params, patrones)
    
    # 4. Create UI components
    alerta = ViewHelpers.crear_alerta_cache(mostrar_vigencia=True, vigente=True)
    tabla = ViewHelpers.crear_tabla_desde_dataframe(df, responsive=False)
    
    return html.Div([alerta, tabla] + graficos)
```

### Cache Saving Pattern in Controllers
```python
# 1. Generate DataFrames and figures
df_conductor = generar_dataframe_conductor(...)
fig_combinado = generar_grafico_plotly(...)

# 2. Save in background thread
def guardar_async():
    # Save images (PNG + JSON for Plotly)
    guardados = ViewHelpers.guardar_imagenes_calculo(hash_params, [
        (fig_combinado, "plotly", "CMC_Combinado.{hash}.png", True, {})
    ])
    
    # Save cache with DataFrames as JSON
    CalculoCache.guardar_calculo_cmc(
        nombre_estructura,
        parametros,
        resultados,
        df_conductor_html=df_conductor.to_json(orient='split'),
        df_guardia1_html=df_guardia1.to_json(orient='split')
    )

threading.Thread(target=guardar_async, daemon=True).start()
```

### Critical Implementation Details

#### DataFrame Preservation
- **Problem**: Reconstructing DataFrames from dict loses formatting (word wrap, column widths)
- **Solution**: Serialize complete DataFrame as JSON with `orient='split'`
- **Loading**: `pd.read_json(json_str, orient='split')` preserves exact structure
- **Display**: Pass directly to `dbc.Table.from_dataframe()` without wrappers

#### Interactive Graph Preservation
- **Problem**: PNG loses interactivity (zoom, pan, hover, cursor data)
- **Solution**: Save Plotly figure as JSON using `fig.write_json()`
- **Loading**: Load JSON dict and create `dcc.Graph(figure=fig_dict)`
- **Config**: Include `config={'displayModeBar': True}` for toolbar
- **No wrappers**: Use `dcc.Graph` directly, avoid responsive containers

#### Encoding Handling
- **Problem**: Spanish characters (°, á, é, etc.) cause UTF-8 decode errors
- **Solution**: Try multiple encodings in order: utf-8 → latin-1 → cp1252
- **Fallback**: Use `errors='ignore'` as last resort
- **Logging**: Print which encoding succeeded for debugging

#### Table Formatting
- **Problem**: `table-responsive` wrapper changes table width and word wrap
- **Solution**: Remove wrapper, use `dbc.Table.from_dataframe()` directly
- **Responsive**: Only use for tables that need horizontal scrolling

#### Image Rendering in Dash
- **Problem**: `ViewHelpers.crear_img_component()` creates components but Dash doesn't render them
- **Solution**: Use `cargar_imagen_base64()` directly and create `html.Img()` inline
- **Pattern**: `img_str = ViewHelpers.cargar_imagen_base64(filename)` then `html.Img(src=f'data:image/png;base64,{img_str}')`
- **Don't use**: Helper methods that wrap `html.Img` - create components directly in view

### Cache Validity Checking
- **CMC behavior**: Shows warning if parameters changed, but keeps old results
- **Other views**: Discard cache if parameters changed, force recalculation
- **Verification**: `CalculoCache.verificar_vigencia(calculo_guardado, estructura_actual)`
- **Hash comparison**: MD5 of current parameters vs saved hash

### Best Practices
1. **Always save dual format** for Plotly: PNG (export) + JSON (interactivity)
2. **Serialize DataFrames** as JSON, not as reconstructed dicts
3. **Use ViewHelpers** for base64 loading, create components inline
4. **Test encoding** with Spanish characters (°, á, ñ, etc.)
5. **Preserve exact format** - no wrappers, no responsive containers
6. **Background saving** - use threads to avoid blocking UI
7. **Images in Dash** - use `cargar_imagen_base64()` + inline `html.Img()`, not helper wrappers
