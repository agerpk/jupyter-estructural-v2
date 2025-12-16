"""Configuración centralizada de la aplicación"""

from pathlib import Path

# Directorios
DATA_DIR = Path("data")
CABLES_PATH = DATA_DIR / "cables.json"
ARCHIVO_ACTUAL = Path("actual.estructura.json")

# Configuración de la aplicación
import os

APP_TITLE = "AGP - Análisis General de Postaciones"
APP_PORT = int(os.environ.get("PORT", 8050))
DEBUG_MODE = True

# Tema visual
THEME = {
    "background": "#0e1012",
    "text": "#d1d5db",
    "card_bg": "#1a1d21",
    "border": "#2d3139",
    "primary": "#2084f2"
}

# Estilos CSS
APP_STYLES = f'''
body {{
    background-color: {THEME["background"]} !important;
    color: {THEME["text"]} !important;
}}
.navbar {{
    background-color: {THEME["background"]} !important;
}}
.container-fluid, .container {{
    background-color: {THEME["background"]} !important;
}}
.card {{
    background-color: {THEME["card_bg"]} !important;
    border-color: {THEME["border"]} !important;
    color: {THEME["text"]} !important;
}}
.modal-content {{
    background-color: {THEME["card_bg"]} !important;
    color: {THEME["text"]} !important;
}}
.form-control, .form-select {{
    background-color: {THEME["card_bg"]} !important;
    border-color: {THEME["border"]} !important;
    color: {THEME["text"]} !important;
}}
.btn-primary {{
    background-color: {THEME["primary"]} !important;
    border-color: {THEME["primary"]} !important;
}}
.badge {{
    background-color: {THEME["primary"]} !important;
}}
'''

# Archivos excluidos de operaciones
ARCHIVOS_PROTEGIDOS = ["actual.estructura.json", "plantilla.estructura.json"]

# Configuración de notificaciones
TOAST_DURATION = 4000

# Persistencia de navegación
NAVEGACION_STATE_FILE = DATA_DIR / "navegacion_state.json"
