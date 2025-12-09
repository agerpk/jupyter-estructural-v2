# Guía Rápida - Arquitectura MVC

## 🚀 Inicio Rápido

### Ejecutar la Aplicación
```bash
# Nueva aplicación MVC
python app.py

# Aplicación original (backup)
python app_plotlydash.py
```

### Verificar Arquitectura
```bash
python test_mvc.py
```

## 📁 ¿Dónde Está Cada Cosa?

### Quiero modificar...

#### 🎨 **Colores o Tema Visual**
📂 `config/app_config.py`
```python
THEME = {
    "background": "#0e1012",
    "text": "#d1d5db",
    "primary": "#2084f2"  # ← Cambiar aquí
}
```

#### 🧭 **Navegación entre Vistas**
📂 `controllers/navigation_controller.py`
- Agregar nueva vista al menú
- Cambiar comportamiento de botones

#### 📁 **Operaciones de Archivo**
📂 `controllers/file_controller.py`
- Cargar/Descargar archivos
- Modales de archivo
- Upload desde PC

#### 🏗️ **Gestión de Estructuras**
📂 `controllers/estructura_controller.py`
- Crear/Eliminar estructuras
- Guardar en DB
- Cargar desde DB

#### ⚙️ **Parámetros de Estructura**
📂 `controllers/parametros_controller.py`
- Guardar parámetros modificados
- Validación de tipos

#### 🔢 **Cálculos AEA**
📂 `controllers/calculo_controller.py`
- Cálculo mecánico de cables
- Crear objetos (Cable, Cadena, Estructura)
- Gráficos de flechas

#### 🖥️ **Interfaz de Usuario**
📂 `controllers/ui_controller.py`
- Badge de estructura actual
- Listas dinámicas
- Actualizaciones de UI

#### 🎭 **Layout Principal**
📂 `views/main_layout.py`
- Estructura HTML principal
- Navbar
- Modales
- Stores

#### 📦 **Estado Global**
📂 `models/app_state.py`
- Managers (EstructuraManager, CableManager)
- Objetos de cálculo
- Estado compartido

## 🔧 Tareas Comunes

### 1. Agregar Nuevo Callback

**Ejemplo: Agregar exportación a PDF**

```python
# 1. Abrir el controlador apropiado
# controllers/file_controller.py

def register_callbacks(app):
    state = AppState()
    
    # ... callbacks existentes ...
    
    # 2. Agregar nuevo callback
    @app.callback(
        Output("download-pdf", "data"),
        Input("btn-exportar-pdf", "n_clicks"),
        State("estructura-actual", "data"),
        prevent_initial_call=True
    )
    def exportar_a_pdf(n_clicks, estructura_actual):
        # Tu lógica aquí
        pass
```

### 2. Cambiar Configuración

```python
# config/app_config.py

# Cambiar puerto
APP_PORT = 8080  # Era 8050

# Cambiar directorio de datos
DATA_DIR = Path("mis_datos")  # Era "data"

# Agregar nuevo color al tema
THEME = {
    "background": "#0e1012",
    "text": "#d1d5db",
    "primary": "#2084f2",
    "secondary": "#64748b"  # ← Nuevo
}
```

### 3. Agregar Nueva Vista

```python
# 1. Crear componente en components/
# components/vista_nueva.py
def crear_vista_nueva():
    return html.Div([
        html.H2("Nueva Vista"),
        # ... contenido ...
    ])

# 2. Agregar navegación en controllers/navigation_controller.py
@app.callback(...)
def navegar_vistas(...):
    # ...
    elif trigger_id == "menu-nueva-vista":
        return crear_vista_nueva()
```

### 4. Modificar Estado Global

```python
# models/app_state.py

class AppState:
    def __init__(self):
        # ... inicialización existente ...
        
        # Agregar nuevo manager
        self.nuevo_manager = NuevoManager()
        
    def nuevo_metodo(self):
        """Agregar nueva funcionalidad"""
        pass
```

## 🎯 Patrones de Uso

### Acceder al Estado en Callbacks

```python
from models.app_state import AppState

def register_callbacks(app):
    state = AppState()  # Singleton - siempre la misma instancia
    
    @app.callback(...)
    def mi_callback(...):
        # Usar managers
        estructuras = state.estructura_manager.listar_estructuras()
        cables = state.cable_manager.obtener_cables()
        
        # Usar objetos de cálculo
        resultado = state.calculo_objetos.crear_objetos_cable(...)
```

### Usar Configuración

```python
from config.app_config import DATA_DIR, THEME, ARCHIVOS_PROTEGIDOS

# Usar rutas
archivo = DATA_DIR / "mi_archivo.json"

# Usar colores
color_primario = THEME["primary"]

# Usar constantes
if archivo.name not in ARCHIVOS_PROTEGIDOS:
    # Permitir operación
    pass
```

### Registrar Controlador

```python
# app.py

from controllers import mi_nuevo_controller

# Registrar callbacks
mi_nuevo_controller.register_callbacks(app)
```

## 📋 Checklist para Nuevas Funcionalidades

- [ ] ¿Es configuración? → `config/app_config.py`
- [ ] ¿Es estado/lógica de negocio? → `models/`
- [ ] ¿Es layout/vista? → `views/` o `components/`
- [ ] ¿Es callback? → `controllers/` (elegir controlador apropiado)
- [ ] ¿Es utilidad reutilizable? → `utils/`
- [ ] ¿Necesita nuevo controlador? → Crear en `controllers/` y registrar en `app.py`

## 🐛 Debugging

### Ver qué controlador maneja un callback

```python
# Buscar por ID del componente
# Ejemplo: "btn-calcular-cmc"

# 1. Buscar en controllers/
grep -r "btn-calcular-cmc" controllers/

# 2. Encontrarás el archivo y callback específico
# controllers/calculo_controller.py:
#   @app.callback(Output(...), Input("btn-calcular-cmc", ...))
```

### Verificar estado

```python
# En cualquier callback
from models.app_state import AppState

state = AppState()
print(f"Managers: {dir(state)}")
print(f"Estructuras: {state.estructura_manager.listar_estructuras()}")
```

### Verificar configuración

```python
from config.app_config import *

print(f"DATA_DIR: {DATA_DIR}")
print(f"THEME: {THEME}")
print(f"APP_PORT: {APP_PORT}")
```

## 📚 Documentación Adicional

- **ARQUITECTURA_MVC.md**: Explicación completa de la arquitectura
- **COMPARACION_ANTES_DESPUES.md**: Comparación detallada con versión anterior
- **test_mvc.py**: Script de verificación de la arquitectura

## 💡 Tips

1. **Un controlador por dominio**: No mezclar callbacks de diferentes dominios
2. **Estado centralizado**: Siempre usar `AppState()` para acceder a managers
3. **Configuración en config/**: No hardcodear valores en código
4. **Callbacks pequeños**: Si un callback es muy largo, considerar extraer lógica a utils/
5. **Nombres descriptivos**: Los IDs de componentes deben ser claros sobre su función

## ⚠️ Importante

- **NO modificar** `app_plotlydash.py` (es backup)
- **NO duplicar** lógica entre controladores
- **NO hardcodear** configuración en callbacks
- **SÍ usar** AppState para estado global
- **SÍ separar** responsabilidades por controlador
- **SÍ documentar** nuevos callbacks con docstrings
