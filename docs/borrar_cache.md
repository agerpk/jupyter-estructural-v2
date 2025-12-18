# Función Borrar Cache

## Descripción
Función que permite eliminar todos los archivos de cache generados por la aplicación, liberando espacio en disco y forzando el recálculo de resultados.

## Ubicación
**Menú**: Editar → Borrar Cache

## Funcionamiento

### Archivos que se eliminan
- En `/data`:
  - `*.calculoCMC.json` - Resultados de cálculo mecánico de cables
  - `*.calculoDGE.json` - Resultados de diseño geométrico
  - `*.calculoDME.json` - Resultados de diseño mecánico
  - `*.calculoSPH.json` - Resultados de selección de poste
  - `*.calculoARBOLES.json` - Resultados de árboles de carga
  - `*.calculoTODO.json` - Resultados de cálculo completo
  - `*.arbolcarga.*.png` - Imágenes de árboles de carga
  - Archivos `.png` y `.json` generados por cálculos
- En `/data/cache`:
  - Todo el contenido (archivos y subdirectorios)

### Archivos protegidos (NO se eliminan)
- `*.estructura.json` - Todos los archivos de estructuras guardadas
- `*.hipotesismaestro.json` - Archivos de hipótesis maestro
- `cables.json` - Biblioteca de cables
- `navegacion_state.json` - Estado de navegación

## Uso

1. Hacer clic en **Editar** → **Borrar Cache**
2. Aparece modal de confirmación con advertencia
3. Hacer clic en **Borrar Cache** para confirmar o **Cancelar** para abortar
4. Se muestra notificación con resultado:
   - **Éxito**: Cantidad de archivos eliminados
   - **Advertencia**: Archivos eliminados con errores parciales
   - **Error**: Fallo en la operación

## Casos de uso

- Liberar espacio en disco cuando hay muchos cálculos guardados
- Forzar recálculo completo de una estructura
- Limpiar resultados obsoletos después de cambios importantes
- Resolver problemas de cache corrupto

## Implementación

### Archivos involucrados
- `utils/borrar_cache.py` - Lógica de borrado
- `controllers/borrar_cache_controller.py` - Callbacks de Dash
- `components/menu.py` - Botón y modal en UI
- `views/main_layout.py` - Integración en layout

### Flujo de ejecución
1. Usuario hace clic en menú → Abre modal
2. Usuario confirma → Ejecuta `borrar_cache()`
3. Función itera archivos en `/data`
4. Elimina archivos de cache, protege archivos esenciales
5. Retorna cantidad eliminada y errores
6. Controller muestra notificación con resultado
