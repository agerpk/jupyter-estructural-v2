# Implementando Fundaciones

## Estado Actual de Implementación

### ✅ RESUELTO - Unificación de archivos estructura.json

**Cambio realizado**: Se unificó el sistema de archivos de estructura eliminando la duplicación entre `actual.estructura.json` y `{titulo}.estructura.json`.

**Implementación**:

1. **AppState actualizado** (`models/app_state.py`):
   - Agregado campo `_estructura_actual_titulo` para rastrear el título actual
   - Nuevos métodos:
     - `get_estructura_actual_path()`: Retorna ruta del archivo unificado
     - `set_estructura_actual()`: Actualiza el título interno
     - `get_estructura_actual_titulo()`: Obtiene el título actual

2. **EstructuraManager actualizado** (`utils/estructura_manager.py`):
   - `actualizar_parametros()`: Usa sistema unificado
   - `guardar_nodos_editados()`: Usa sistema unificado  
   - `cargar_nodos_editados()`: Usa sistema unificado

3. **Controladores actualizados**:
   - `parametros_controller.py`: Usa `state.get_estructura_actual_path()`
   - `geometria_controller.py`: Todas las referencias actualizadas
   - `estructura_controller.py`: Operaciones de carga/guardado unificadas
   - `file_controller.py`: Upload usa sistema unificado
   - `calcular_todo_controller.py`: Ambas referencias actualizadas
   - `arboles_controller.py`: Actualizado
   - `fundacion_controller.py`: Parcialmente actualizado
   - `mecanica_controller.py`: Actualizado

4. **Layout principal actualizado** (`views/main_layout.py`):
   - Inicialización correcta del estado con estructura actual

**Funcionamiento**:
- Solo existe un archivo por estructura: `{TITULO}.estructura.json`
- El sistema rastrea automáticamente qué estructura está activa
- Todas las operaciones (guardar parámetros, nodos editados, etc.) van al archivo unificado
- Se elimina la duplicación y sincronización manual

**Archivos modificados**:
- `models/app_state.py`
- `utils/estructura_manager.py`
- `views/main_layout.py`
- 8 controladores actualizados

### 🔧 TESTING PENDIENTE - Fundaciones Controller

**Pendiente**: Completar actualización de `fundacion_controller.py` - quedan 2 referencias a `actual.estructura.json` sin actualizar.

**Próximos pasos**:
1. Actualizar las referencias restantes en fundacion_controller
2. Verificar que no queden referencias a `actual.estructura.json` en otros archivos
3. Testing completo del sistema unificado
4. Eliminar archivo `actual.estructura.json` legacy si existe

## Cambios Realizados en Esta Sesión

### Unificación del Sistema de Archivos de Estructura

**Problema identificado**: Duplicación entre `actual.estructura.json` y `{titulo}.estructura.json` causaba:
- Sincronización manual compleja
- Posibles inconsistencias de datos
- Código duplicado para mantener ambos archivos

**Solución implementada**:
- Sistema unificado que usa solo `{titulo}.estructura.json`
- AppState rastrea automáticamente la estructura activa
- Métodos centralizados para obtener la ruta correcta
- Eliminación de lógica de sincronización dual

**Beneficios**:
- Código más simple y mantenible
- Eliminación de duplicación de datos
- Consistencia garantizada
- Menos puntos de falla

## Próximos Pasos Pendientes

1. **Completar fundacion_controller**: Actualizar las 2 referencias restantes
2. **Testing integral**: Verificar que todas las operaciones funcionen correctamente
3. **Limpieza**: Eliminar referencias legacy a `actual.estructura.json`
4. **Documentación**: Actualizar documentación técnica sobre el nuevo sistema

## Problemas Identificados y Estados

### ❌ FALLA - Referencias legacy pendientes
- **Archivo**: `fundacion_controller.py` líneas ~320 y ~393
- **Descripción**: Quedan 2 referencias a `DATA_DIR / "actual.estructura.json"` sin actualizar
- **Impacto**: Funcionalidad de fundaciones podría no usar el sistema unificado

## Notas Técnicas y Decisiones de Arquitectura

### Decisión: Sistema de Rastreo de Estructura Actual
- **Opción elegida**: Campo privado `_estructura_actual_titulo` en AppState
- **Alternativas consideradas**: Variable global, archivo de configuración separado
- **Justificación**: Mantiene el estado centralizado y es thread-safe con el patrón Singleton

### Decisión: Métodos de Acceso Centralizados
- **Implementación**: `get_estructura_actual_path()` y `set_estructura_actual()`
- **Beneficio**: Punto único de control para cambios futuros
- **Patrón**: Encapsulación del estado interno

### Decisión: Actualización Gradual vs Completa
- **Opción elegida**: Actualización gradual controlador por controlador
- **Justificación**: Menor riesgo, testing incremental, rollback más fácil

## Compatibilidad y Migración

### Compatibilidad hacia atrás
- El sistema puede cargar estructuras existentes
- Fallback a `actual.estructura.json` si no existe el archivo con título
- Migración automática al guardar

### Migración de datos existentes
- No se requiere migración manual
- Los archivos existentes se mantienen funcionales
- Primera operación de guardado migra automáticamente al nuevo sistema