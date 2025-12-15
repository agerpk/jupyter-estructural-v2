# Technology Stack

## Programming Language
- **Python 3.x** - Primary development language

## Core Framework
- **Dash >= 2.14.0** - Web application framework for building analytical web applications
- **Dash Bootstrap Components >= 1.5.0** - Bootstrap-themed components for Dash

## Data Processing & Scientific Computing
- **Pandas >= 2.0.0** - Data manipulation and analysis
- **NumPy >= 1.24.0** - Numerical computing and array operations

## Visualization
- **Matplotlib >= 3.7.0** - Static plotting and chart generation
- **Plotly >= 5.15.0** - Interactive plotting and visualization
- **Kaleido >= 0.2.1** - Static image export for Plotly figures

## File Processing
- **openpyxl >= 3.1.0** - Excel file reading and writing

## Application Configuration
- **Port**: Configurable via `app_config.py` (default: APP_PORT)
- **Debug Mode**: Configurable via `app_config.py` (DEBUG_MODE)
- **Data Directory**: `./data/` for runtime data storage

## Development Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
python app.py
```

### Alternative Entry Point
```bash
python app_plotlydash.py
```

## Project Structure Standards
- **Configuration**: Centralized in `/config/app_config.py`
- **Data Persistence**: JSON format for structures and calculations
- **Image Storage**: PNG format for diagrams and charts
- **Encoding**: UTF-8 for all text files

## Key Technical Patterns
- **Callback-based Architecture**: Dash callbacks for reactive UI updates
- **JSON Serialization**: All data structures serializable to JSON
- **Path Management**: pathlib.Path for cross-platform file operations
- **State Management**: Singleton-like AppState for application state
- **Lazy Loading**: Calculation results cached and loaded on demand

## External Standards
- **AEA (Asociación Electrotécnica Argentina)**: Electrical engineering standards compliance
- **IEC Standards**: International electrical standards reference

## File Naming Conventions
- Structure files: `{name}.estructura.json`
- Calculation results: `{name}.calculo{TYPE}.json`
- Hypothesis files: `{name}.hipotesismaestro.json`
- Diagrams: `{type}.{hash}.png` or `{name}.arbolcarga.{hash}.{hypothesis}.png`

## Development Environment
- **Operating System**: Cross-platform (Windows, Linux, macOS)
- **IDE**: Compatible with any Python IDE
- **Version Control**: Git (`.gitignore` configured)
