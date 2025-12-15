# Project Structure

## Architecture Pattern
MVC (Model-View-Controller) architecture with Dash framework for web-based UI

## Directory Organization

### `/components/` - UI Components
Reusable Dash UI components for different application views:
- `menu.py` - Navigation menu
- `parametro_input.py` - Parameter input widgets
- `editor_hipotesis.py` - Hypothesis editor interface
- `vista_*.py` - View components for each module (home, configuration, calculations, etc.)

### `/controllers/` - Business Logic Controllers
MVC controllers handling application logic and callbacks:
- `navigation_controller.py` - Page routing and navigation
- `file_controller.py` - File operations (save/load structures)
- `estructura_controller.py` - Structure management
- `calculo_controller.py` - Calculation orchestration
- `calcular_todo_controller.py` - Complete calculation workflow
- `cables_controller.py` - Cable database management
- `geometria_controller.py` - Geometric design logic
- `mecanica_controller.py` - Mechanical calculations
- `arboles_controller.py` - Load tree generation
- `parametros_controller.py` - Parameter management
- `seleccion_poste_controller.py` - Pole selection logic
- `ui_controller.py` - UI state management
- `home_controller.py` - Home page logic

### `/models/` - Data Models
Application state and data structures:
- `app_state.py` - Central application state management

### `/views/` - View Layer
Layout definitions:
- `main_layout.py` - Main application layout structure

### `/utils/` - Utility Modules
Shared calculation and helper functions:
- `arboles_carga.py` - Load tree calculations
- `calculo_mecanico_cables.py` - Cable mechanical calculations
- `calculo_objetos.py` - Calculation object definitions
- `memoria_calculo_dge.py` - Geometric design calculations
- `cable_manager.py` - Cable data management
- `estructura_manager.py` - Structure persistence
- `hipotesis_manager.py` - Hypothesis management
- `calculo_cache.py` - Calculation result caching
- `plot_flechas.py` - Sag plotting utilities
- `validaciones.py` - Input validation

### `/config/` - Configuration
Application configuration:
- `app_config.py` - Global settings, paths, constants

### `/data/` - Data Storage
Runtime data storage:
- `*.estructura.json` - Structure definitions
- `*.calculoARBOLES.json` - Load tree results
- `*.calculoCMC.json` - Cable calculation results
- `*.calculoDGE.json` - Geometric design results
- `*.calculoDME.json` - Mechanical design results
- `*.calculoSPH.json` - Pole selection results
- `*.calculoTODO.json` - Complete calculation results
- `*.hipotesismaestro.json` - Hypothesis definitions
- `*.arbolcarga.*.png` - Load tree diagrams
- `Cabezal.*.png` - Structure head diagrams
- `CMC_*.*.png` - Cable calculation charts
- `DME_*.*.png` - Mechanical design charts
- `Estructura.*.png` - Structure diagrams
- `cables.json` - Cable database
- `navegacion_state.json` - Navigation state
- `plantilla.estructura.json` - Default structure template

### `/docs/` - Documentation
Project documentation:
- `sintesis.md` - Project synthesis
- `/superados/` - Archived documentation

### `/notebooks_backup/` - Jupyter Notebooks
Original Jupyter notebook versions (legacy):
- `Estructural_poo_v*.IPYNB` - Previous notebook-based implementations

### Root Level - Core Calculation Modules
Legacy calculation modules (being migrated to MVC):
- `CalculoEstructura.py` - Main structure calculation engine
- `CalculoCables.py` - Cable calculations
- `DatosPostes.py` - Pole data definitions
- `DatosCables.py` - Cable data definitions
- `Estructura3D.py` - 3D structure representation
- `EstructuraAEA_Geometria.py` - AEA standard geometry
- `EstructuraAEA_Mecanica.py` - AEA standard mechanics
- `EstructuraAEA_Graficos.py` - Graphics generation
- `HipotesisMaestro.py` - Hypothesis master class
- `HipotesisMaestro_Especial.py` - Special hypothesis cases
- `ListarCargas.py` - Load listing utilities
- `PostesHormigon.py` - Concrete pole definitions
- `app.py` - Main application entry point
- `app_plotlydash.py` - Alternative Plotly Dash app

## Component Relationships

### Data Flow
1. User interacts with UI components (`/components/`)
2. Controllers (`/controllers/`) handle callbacks and business logic
3. Controllers use utility modules (`/utils/`) for calculations
4. Core calculation modules (root level) perform engineering computations
5. Results stored in `/data/` directory
6. Models (`/models/`) maintain application state
7. Views (`/views/`) render updated UI

### Key Architectural Patterns
- **Separation of Concerns**: Clear MVC boundaries
- **Manager Pattern**: Specialized managers for cables, structures, hypotheses
- **Caching**: Calculation results cached to avoid redundant computations
- **State Management**: Centralized state in AppState model
- **Modular Controllers**: Each feature has dedicated controller
- **Reusable Components**: UI components shared across views
