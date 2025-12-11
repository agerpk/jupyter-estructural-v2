# Guía Rápida - Arquitectura MVC

## 📊 ANÁLISIS RESUMIDO DE LA APLICACIÓN

### Nombre del Sistema
**AGP - Análisis General de Postaciones**

### Arquitectura
**Patrón MVC (Model-View-Controller)** con Dash/Plotly
- **Models**: Gestión de datos y lógica de negocio
- **Views**: Componentes visuales (HTML/Dash)
- **Controllers**: Callbacks que conectan vistas con modelos

### Estructura de Directorios
```
jupyter_estructural_v2/
├── app.py                          # Punto de entrada principal
├── config/
│   └── app_config.py              # Configuración centralizada (tema, puertos, paths)
├── models/
│   └── app_state.py               # Estado global (Singleton) con managers
├── views/
│   └── main_layout.py             # Layout principal (navbar, modales, stores)
├── components/                     # Vistas individuales (una por funcionalidad)
│   ├── vista_home.py
│   ├── vista_ajuste_parametros.py
│   ├── vista_calculo_mecanico.py
│   ├── vista_diseno_geometrico.py
│   ├── vista_diseno_mecanico.py
│   ├── vista_arboles_carga.py
│   ├── vista_seleccion_poste.py
│   ├── vista_calcular_todo.py
│   └── vista_gestion_cables.py
├── controllers/                    # Callbacks organizados por dominio
│   ├── navigation_controller.py   # Navegación entre vistas
│   ├── file_controller.py         # Operaciones de archivo
│   ├── estructura_controller.py   # CRUD de estructuras
│   ├── parametros_controller.py   # Edición de parámetros
│   ├── geometria_controller.py    # Cálculo CMC y DGE
│   ├── mecanica_controller.py     # Cálculo DME
│   ├── arboles_controller.py      # Árboles de carga
│   ├── seleccion_poste_controller.py  # SPH
│   ├── calcular_todo_controller.py    # Ejecución secuencial completa
│   ├── cables_controller.py       # Gestión de cables
│   └── ui_controller.py           # Actualizaciones de UI
├── utils/                          # Utilidades reutilizables
│   ├── calculo_cache.py           # Persistencia de resultados
│   ├── estructura_manager.py      # Gestión de archivos .estructura.json
│   ├── cable_manager.py           # Gestión de cables.json
│   ├── hipotesis_manager.py       # Gestión de hipótesis de carga
│   ├── plot_flechas.py            # Gráficos Plotly de flechas
│   ├── arboles_carga.py           # Generación de árboles de carga
│   └── memoria_calculo_dge.py     # Generación de memorias de cálculo
└── data/                           # Datos persistentes
    ├── *.estructura.json          # Archivos de estructuras
    ├── *.calculoXXX.json          # Cache de cálculos (CMC, DGE, DME, etc.)
    ├── *.png                       # Imágenes generadas
    └── cables.json                 # Base de datos de cables
```

### Flujo de Datos
1. **Usuario interactúa** → Componente Dash (botón, input)
2. **Callback se dispara** → Controller específico
3. **Controller accede** → AppState (singleton) para obtener managers
4. **Manager ejecuta** → Lógica de negocio (cálculos, I/O)
5. **Resultado retorna** → Controller actualiza Output
6. **Vista se actualiza** → Usuario ve cambios

### Sistema de Cache
**Estrategia**: Hash MD5 de parámetros de estructura
- Cada cálculo (CMC, DGE, DME, Árboles, SPH) tiene su propio archivo `.calculoXXX.json`
- Las imágenes se guardan con el hash en el nombre: `CMC_Combinado.{hash}.png`
- Al cambiar parámetros, el hash cambia y se invalida el cache
- Al reiniciar la app, se cargan resultados desde cache si el hash coincide

### Vistas Principales y sus Callbacks

| Vista | Componente | Controller | Función |
|-------|-----------|------------|----------|
| Home | `vista_home.py` | `navigation_controller.py` | Pantalla inicial |
| Ajustar Parámetros | `vista_ajuste_parametros.py` | `parametros_controller.py` | Editar parámetros de estructura |
| CMC | `vista_calculo_mecanico.py` | `geometria_controller.py` | Cálculo Mecánico de Cables |
| DGE | `vista_diseno_geometrico.py` | `geometria_controller.py` | Diseño Geométrico de Estructura |
| DME | `vista_diseno_mecanico.py` | `mecanica_controller.py` | Diseño Mecánico de Estructura |
| Árboles | `vista_arboles_carga.py` | `arboles_controller.py` | Árboles de Carga |
| SPH | `vista_seleccion_poste.py` | `seleccion_poste_controller.py` | Selección de Postes |
| Calcular Todo | `vista_calcular_todo.py` | `calcular_todo_controller.py` | Ejecución secuencial (CMC→DGE→DME→Árboles→SPH) |
| Gestión Cables | `vista_gestion_cables.py` | `cables_controller.py` | CRUD de cables |

### Secuencia de Cálculo (Calcular Todo)
```
CMC (Cálculo Mecánico de Cables)
  ↓ genera: flechas máximas, tiros, cargas de viento
DGE (Diseño Geométrico de Estructura)
  ↓ genera: dimensiones, nodos, gráficos de estructura
DME (Diseño Mecánico de Estructura)
  ↓ genera: reacciones en base, gráficos polares
Árboles de Carga
  ↓ genera: diagramas de carga por hipótesis
SPH (Selección de Postes de Hormigón)
  ↓ genera: postes seleccionados, orientación
```

### Estado Global (AppState)
**Singleton Pattern** - Una única instancia compartida
```python
class AppState:
    estructura_manager: EstructuraManager  # CRUD de estructuras
    cable_manager: CableManager            # CRUD de cables
    calculo_objetos: CalculoObjetosAEA     # Objetos de cálculo (Cable, Cadena, Estructura)
    calculo_mecanico: CalculoMecanicoCables # Resultados CMC
    archivo_actual: Path                    # Ruta del archivo actual
```

### Persistencia de Navegación
- Al cambiar de vista, se guarda en `data/navegacion_state.json`
- Al reiniciar la app, se carga la última vista visitada
- Permite recuperar el estado de trabajo después de cerrar

### Criterios de Diseño
1. **Separación de responsabilidades**: Cada controller maneja un dominio específico
2. **Reutilización**: Lógica común en `utils/`, no duplicada en controllers
3. **Cache inteligente**: Evita recálculos innecesarios usando hash de parámetros
4. **Actualización progresiva**: "Calcular Todo" muestra resultados a medida que se generan (dcc.Interval)
5. **Exportación completa**: HTML con imágenes embebidas en base64

### Cómo Escalar la Aplicación
1. **Nueva vista de cálculo**: Crear componente en `components/`, controller en `controllers/`, registrar en `app.py`
2. **Nuevo tipo de cache**: Agregar métodos en `utils/calculo_cache.py` (guardar/cargar)
3. **Nueva funcionalidad**: Identificar dominio → agregar callback en controller apropiado
4. **Nuevo manager**: Crear en `utils/`, agregar a `AppState` en `models/app_state.py`
5. **Nueva configuración**: Agregar constante en `config/app_config.py`

---

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
