# Project Structure

## Directory Organization

### `/components/` - UI Components
Reusable Dash components for the web interface:
- `menu.py` - Navigation menu component
- `parametro_input.py` - Parameter input widgets
- `vista_*.py` - View components for each application section (home, configuration, geometric design, mechanical design, cable management, pole selection, load trees, calculation execution)
- `editor_hipotesis.py` - Load hypothesis editor interface

### `/config/` - Application Configuration
- `app_config.py` - Central configuration file with constants, paths, and application settings

### `/controllers/` - Business Logic (MVC Controllers)
Controllers implementing application logic and callbacks:
- `navigation_controller.py` - Page routing and navigation
- `file_controller.py` - File operations (save/load structures)
- `estructura_controller.py` - Structure management
- `parametros_controller.py` - Parameter validation and updates
- `calculo_controller.py` - Calculation orchestration
- `geometria_controller.py` - Geometric design calculations
- `mecanica_controller.py` - Mechanical analysis
- `cables_controller.py` - Cable library management
- `seleccion_poste_controller.py` - Pole selection logic
- `arboles_controller.py` - Load tree generation
- `calcular_todo_controller.py` - Complete calculation workflow
- `ejecutar_calculos.py` - Calculation execution utilities
- `home_controller.py` - Home page logic
- `ui_controller.py` - UI state management

### `/models/` - Data Models
- `app_state.py` - Application state management and data persistence

### `/utils/` - Utility Functions
Helper modules for specific tasks:
- `cable_manager.py` - Cable data management
- `estructura_manager.py` - Structure file operations
- `hipotesis_manager.py` - Load hypothesis management
- `calculo_mecanico_cables.py` - Cable mechanical calculations
- `calculo_objetos.py` - Calculation object creation
- `arboles_carga.py` - Load tree generation utilities
- `memoria_calculo_dge.py` - Geometric design calculation reports
- `plot_flechas.py` - Cable sag plotting
- `format_helpers.py` - Data formatting utilities
- `validaciones.py` - Input validation functions
- `calculo_cache.py` - Calculation result caching

### `/views/` - View Layer
- `main_layout.py` - Main application layout definition

### `/data/` - Application Data
Runtime data storage:
- `*.estructura.json` - Structure configuration files
- `*.calculoCMC.json` - Cable mechanical calculation results
- `*.calculoDGE.json` - Geometric design results
- `*.calculoDME.json` - Mechanical design results
- `*.calculoSPH.json` - Pole selection results
- `*.calculoARBOLES.json` - Load tree results
- `*.hipotesismaestro.json` - Load hypothesis definitions
- `*.arbolcarga.*.png` - Load tree diagrams
- `cables.json` - Cable library data
- `navegacion_state.json` - Navigation state persistence

### `/docs/` - Documentation
- `sintesis.md` - Project synthesis and overview
- `/superados/` - Archived documentation from previous versions

### `/notebooks_backup/` - Jupyter Notebooks
Backup of original Jupyter notebook implementations:
- `Estructural_poo_v*.IPYNB` - Various versions of the structural analysis notebook

### Root Level - Core Calculation Modules
Python modules implementing core engineering calculations:
- `CalculoCables.py` - Cable calculation classes (Cable_AEA, Elemento_AEA, LibCables)
- `CalculoEstructura.py` - Structural analysis engine
- `DatosCables.py` - Cable property database
- `DatosPostes.py` - Concrete pole specifications database
- `PostesHormigon.py` - Concrete pole library and selection
- `EstructuraAEA_Geometria.py` - Geometric structure definition (NodoEstructural, EstructuraAEA_Geometria)
- `EstructuraAEA_Mecanica.py` - Mechanical analysis calculations
- `EstructuraAEA_Graficos.py` - Structure visualization and plotting
- `Estructura3D.py` - 3D structure rendering
- `HipotesisMaestro.py` - Standard load hypothesis definitions
- `HipotesisMaestro_Especial.py` - Special load hypothesis cases
- `ListarCargas.py` - Load enumeration utilities
- `app.py` - Main application entry point
- `app_plotlydash.py` - Alternative Plotly Dash application

## Core Components and Relationships

### MVC Architecture
The application follows Model-View-Controller pattern:
- **Models** (`/models/`): AppState manages application data and persistence
- **Views** (`/views/`, `/components/`): Dash components render UI
- **Controllers** (`/controllers/`): Handle user interactions and orchestrate calculations

### Calculation Flow
1. User configures structure parameters via UI components
2. Controllers validate inputs and update AppState
3. Core calculation modules (CalculoCables, EstructuraAEA_*) perform engineering analysis
4. Results stored in `/data/` as JSON files
5. Visualization components render results (plots, diagrams, tables)

### Data Flow
```
User Input → Controllers → AppState → Core Modules → Results (JSON) → Visualization
                ↓                           ↓
            Validation              Calculation Cache
```

## Architectural Patterns

### Separation of Concerns
- UI components separated from business logic
- Calculation engines independent of web framework
- Data persistence abstracted through managers

### Object-Oriented Design
- Cable objects (Cable_AEA) encapsulate cable properties and calculations
- Structure objects (EstructuraAEA_*) separate geometry, mechanics, and graphics
- Pole library (PostesHormigon) provides standardized pole selection

### Configuration-Driven
- Central configuration in `app_config.py`
- Structure parameters stored as JSON for portability
- Load hypotheses defined declaratively

### Caching Strategy
- Calculation results cached to avoid redundant computations
- State persistence enables session recovery
- Incremental recalculation when parameters change
