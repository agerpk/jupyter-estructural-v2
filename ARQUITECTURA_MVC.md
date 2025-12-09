# Arquitectura MVC - Gestor de Estructuras

## Estructura del Proyecto

```
jupyter_estructural_v2/
│
├── app.py                          # Punto de entrada principal (MVC)
├── app_plotlydash.py              # Aplicación original (BACKUP)
│
├── config/                         # Configuración
│   ├── __init__.py
│   └── app_config.py              # Constantes y configuración centralizada
│
├── models/                         # Modelos (Lógica de negocio)
│   ├── __init__.py
│   └── app_state.py               # Estado global de la aplicación (Singleton)
│
├── views/                          # Vistas (Layouts)
│   ├── __init__.py
│   └── main_layout.py             # Layout principal
│
├── controllers/                    # Controladores (Callbacks)
│   ├── __init__.py
│   ├── navigation_controller.py   # Navegación entre vistas
│   ├── file_controller.py         # Operaciones de archivo
│   ├── estructura_controller.py   # Gestión de estructuras
│   ├── parametros_controller.py   # Ajuste de parámetros
│   ├── calculo_controller.py      # Cálculos AEA
│   └── ui_controller.py           # Actualizaciones de UI
│
├── components/                     # Componentes reutilizables
│   ├── menu.py
│   ├── vista_home.py
│   ├── vista_ajuste_parametros.py
│   ├── vista_calculo_mecanico.py
│   ├── vista_eliminar_estructura.py
│   └── ...
│
└── utils/                          # Utilidades
    ├── cable_manager.py
    ├── estructura_manager.py
    ├── calculo_objetos.py
    ├── calculo_mecanico_cables.py
    ├── plot_flechas.py
    └── validaciones.py
```

## Responsabilidades por Capa

### 1. **Models** (Modelos)
- **app_state.py**: Singleton que gestiona el estado global
  - Inicializa managers (EstructuraManager, CableManager)
  - Inicializa objetos de cálculo (CalculoObjetosAEA, CalculoMecanicoCables)
  - Proporciona acceso centralizado al estado

### 2. **Views** (Vistas)
- **main_layout.py**: Construye el layout principal
  - Navbar con menús
  - Stores para estado
  - Modales
  - Área de contenido principal
  - Toasts de notificación

### 3. **Controllers** (Controladores)
Cada controlador maneja un dominio específico de callbacks:

- **navigation_controller.py**: Navegación entre vistas
  - Cambio de vista según botones/menús
  - Gestión de botones "Volver"

- **file_controller.py**: Operaciones de archivo
  - Carga desde PC
  - Descarga a PC
  - Modales de carga/guardado

- **estructura_controller.py**: Gestión de estructuras
  - Crear nueva estructura
  - Cargar desde DB
  - Guardar en DB
  - Guardar como
  - Guardar plantilla
  - Eliminar estructura

- **parametros_controller.py**: Ajuste de parámetros
  - Guardar parámetros modificados
  - Validación de tipos de datos

- **calculo_controller.py**: Cálculos AEA
  - Crear objetos (Cable, Cadena, Estructura)
  - Cálculo mecánico de cables
  - Generación de gráficos de flechas
  - Actualización de tabla de estados climáticos

- **ui_controller.py**: Actualizaciones de UI
  - Badge de estructura actual
  - Listas de estructuras disponibles
  - Filtrado de archivos protegidos

### 4. **Config** (Configuración)
- **app_config.py**: Configuración centralizada
  - Rutas de archivos
  - Tema visual (colores)
  - Estilos CSS
  - Constantes de la aplicación
  - Archivos protegidos

## Ventajas de la Arquitectura MVC

### ✅ Separación de Responsabilidades
- Cada capa tiene una responsabilidad clara
- Fácil identificar dónde hacer cambios

### ✅ Mantenibilidad
- Código organizado en módulos pequeños (~100-300 líneas)
- Fácil localizar y corregir bugs

### ✅ Escalabilidad
- Agregar nuevas funcionalidades es simple
- Solo crear nuevo controlador o extender existente

### ✅ Testabilidad
- Cada controlador puede testearse independientemente
- Modelos y utilidades son fáciles de testear

### ✅ Reutilización
- Componentes y utilidades reutilizables
- Estado centralizado evita duplicación

### ✅ Colaboración
- Múltiples desarrolladores pueden trabajar en paralelo
- Menos conflictos de merge

## Flujo de Datos

```
Usuario interactúa con UI
    ↓
Callback en Controller se activa
    ↓
Controller accede a Model (AppState)
    ↓
Model ejecuta lógica de negocio (Managers, Cálculos)
    ↓
Controller actualiza View (Outputs)
    ↓
UI se actualiza para el usuario
```

## Migración desde app_plotlydash.py

### Cambios Principales:
1. **app_plotlydash.py** → **app.py** (nuevo punto de entrada)
2. Callbacks distribuidos en 6 controladores especializados
3. Configuración extraída a `config/app_config.py`
4. Estado global en `models/app_state.py`
5. Layout separado en `views/main_layout.py`

### Compatibilidad:
- ✅ Funcionalidad 100% preservada
- ✅ Misma interfaz de usuario
- ✅ Mismos componentes y utilidades
- ✅ Sin cambios en lógica de negocio

## Ejecución

### Aplicación MVC (Nueva):
```bash
python app.py
```

### Aplicación Original (Backup):
```bash
python app_plotlydash.py
```

## Próximos Pasos

### Mejoras Futuras:
1. **Testing**: Agregar tests unitarios para controladores
2. **Logging**: Implementar logging estructurado
3. **Validación**: Centralizar validaciones en models
4. **Cache**: Implementar cache para cálculos pesados
5. **API**: Separar backend en API REST si es necesario

## Notas Importantes

- **app_plotlydash.py** se mantiene como backup
- Ambas aplicaciones son funcionales
- La nueva arquitectura facilita el crecimiento futuro
- Configuración centralizada simplifica cambios de tema/rutas
