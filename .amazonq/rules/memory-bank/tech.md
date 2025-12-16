# Technology Stack

## Programming Language
- **Python 3.x** - Primary development language for all modules

## Core Dependencies

### Web Framework
- **Dash >= 2.14.0** - Interactive web application framework built on Flask, Plotly.js, and React
- **dash-bootstrap-components >= 1.5.0** - Bootstrap components for Dash applications

### Data Processing
- **pandas >= 2.0.0** - Data manipulation and analysis (DataFrames for calculation results)
- **numpy >= 1.24.0** - Numerical computing (array operations, mathematical functions)

### Visualization
- **matplotlib >= 3.7.0** - Static plotting library for engineering diagrams
- **plotly >= 5.15.0** - Interactive plotting library for web-based visualizations
- **kaleido >= 0.2.1** - Static image export for Plotly figures

### File Operations
- **openpyxl >= 3.1.0** - Excel file reading and writing

## Development Environment
- **Operating System**: Windows (based on workspace path structure)
- **IDE**: Compatible with Jupyter notebooks and standard Python IDEs

## Application Architecture

### Frontend
- **Dash/Plotly** - Reactive web interface with callback-based interactivity
- **Bootstrap** - Responsive UI styling and layout
- **Plotly.js** - Client-side interactive charts and 3D visualizations

### Backend
- **Flask** (via Dash) - Web server and routing
- **Python modules** - Core calculation engines and business logic

### Data Storage
- **JSON** - Structure configurations, calculation results, and application state
- **CSV** - Calculation output exports
- **PNG** - Generated diagrams and load trees

## Key Technical Patterns

### Reactive Programming
- Dash callbacks for UI updates
- Input/Output/State decorators for component interactions
- Automatic dependency resolution

### Scientific Computing
- NumPy arrays for vectorized calculations
- Pandas DataFrames for tabular data manipulation
- Matplotlib/Plotly for engineering visualizations

### File-Based Persistence
- JSON serialization for configuration and results
- File naming conventions: `{project_name}.{calculation_type}.json`
- Automatic backup and versioning through file timestamps

## Development Commands

### Installation
```bash
pip install -r requirements.txt
```

### Run Application
```bash
python app.py
```
- Default port: Configured in `config/app_config.py` (APP_PORT)
- Debug mode: Controlled by DEBUG_MODE setting

### Alternative Entry Point
```bash
python app_plotlydash.py
```

## Module Dependencies

### Core Calculation Modules
- `CalculoCables.py` - Standalone cable calculations (no external dependencies beyond numpy/pandas)
- `EstructuraAEA_*.py` - Structure analysis (depends on CalculoCables, matplotlib, plotly)
- `PostesHormigon.py` - Pole library (minimal dependencies)

### Application Modules
- Controllers depend on: Dash, models, utils
- Components depend on: Dash, dash-bootstrap-components
- Utils depend on: pandas, numpy, json, pathlib

## Configuration Management
- Central configuration: `config/app_config.py`
- Environment-specific settings: APP_TITLE, APP_PORT, DEBUG_MODE, DATA_DIR
- Path management: pathlib.Path for cross-platform compatibility
- Style definitions: Inline CSS in APP_STYLES constant

## Data Formats

### Input Formats
- JSON: Structure parameters, cable definitions, pole specifications
- Python dictionaries: Configuration objects, calculation parameters

### Output Formats
- JSON: Calculation results, state persistence
- CSV: Tabular calculation exports
- PNG: Diagrams, load trees, structure visualizations
- HTML: Interactive Dash application interface

## Performance Considerations
- Calculation caching to avoid redundant computations
- Lazy loading of calculation results
- Incremental updates through Dash callbacks
- File-based state persistence for session recovery
