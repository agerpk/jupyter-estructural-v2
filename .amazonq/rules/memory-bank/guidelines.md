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
