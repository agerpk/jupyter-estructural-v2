# Persistencia de Familia Activa

## Problema Resuelto
La familia activa no persistía entre sesiones de la aplicación. Al recargar la app, se perdía la referencia a la familia que estaba siendo trabajada.

## Solución Implementada

### 1. Archivo de Persistencia
- **Archivo**: `data/familia_state.json`
- **Formato**: `{"familia_activa": "nombre_familia"}`
- **Ubicación**: Definido en `config/app_config.py` como `FAMILIA_STATE_FILE`

### 2. Cambios en AppState (`models/app_state.py`)

#### Métodos Nuevos:
- `_cargar_familia_activa_persistente()`: Carga familia activa desde archivo al iniciar AppState
- `_guardar_familia_activa_persistente(nombre_familia)`: Guarda familia activa en archivo

#### Métodos Modificados:
- `__init__()`: Ahora carga familia activa persistente automáticamente
- `set_familia_activa(nombre_familia)`: Ahora persiste el cambio automáticamente

### 3. Cambios en Controller (`controllers/familia_controller.py`)

#### Callbacks Modificados:
- `cargar_familia_seleccionada()`: Llama a `state.set_familia_activa()` al cargar familia
- `guardar_familia()`: Llama a `state.set_familia_activa()` al guardar familia
- `guardar_como_familia()`: Llama a `state.set_familia_activa()` al guardar como

### 4. Cambios en Vista (`components/vista_familia_estructuras.py`)

#### Función Modificada:
- `crear_vista_familia_estructuras()`: Ahora intenta cargar familia activa desde AppState si no se proporciona una

## Flujo de Persistencia

### Al Iniciar la App:
1. AppState se inicializa
2. `_cargar_familia_activa_persistente()` lee `data/familia_state.json`
3. Si existe familia activa, se carga en `_familia_activa_nombre`
4. Vista familia intenta cargar familia activa automáticamente

### Al Cargar/Guardar Familia:
1. Usuario carga o guarda familia
2. Controller llama a `state.set_familia_activa(nombre_familia)`
3. AppState actualiza `_familia_activa_nombre`
4. `_guardar_familia_activa_persistente()` escribe en `data/familia_state.json`

### Al Recargar la App:
1. AppState carga familia activa desde archivo
2. Vista familia detecta familia activa y la carga automáticamente
3. Usuario continúa trabajando donde dejó

## Archivos Modificados
- `config/app_config.py` - Agregada constante `FAMILIA_STATE_FILE`
- `models/app_state.py` - Implementada persistencia automática
- `controllers/familia_controller.py` - Actualizado para usar `set_familia_activa()`
- `components/vista_familia_estructuras.py` - Carga automática de familia activa

## Testing
1. Cargar una familia desde dropdown → Verificar que se guarda en `data/familia_state.json`
2. Guardar una familia → Verificar que se establece como activa
3. Recargar la app → Verificar que la familia activa se carga automáticamente
4. Verificar mensajes en consola: "✅ Familia activa: nombre" y "💾 Familia activa guardada en persistencia"

## Estado
✅ IMPLEMENTADO - Listo para testing
