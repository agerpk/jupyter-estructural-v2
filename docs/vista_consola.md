# Vista de Consola

## Descripción
Vista que muestra el output de consola capturado desde el inicio de la aplicación. Permite monitorear todos los mensajes de debug, warnings y errores en tiempo real.

## Características

### Captura Persistente
- Captura TODO el output desde que se inicia la app
- No se borra al cambiar de vista
- Persiste durante toda la sesión
- Límite de 10,000 líneas para evitar problemas de memoria

### Interfaz
- **Botón Actualizar**: Refresca el contenido de la consola manualmente
- **Botón Limpiar**: Borra el buffer de consola (útil para debugging)
- **Área de texto**: Muestra el output con formato monoespaciado
- **Scroll**: Permite navegar por todo el historial
- **Selección**: Permite copiar texto de la consola

### Acceso
- Menú ARCHIVO → 📟 Consola

## Implementación Técnica

### Arquitectura
```
app.py (inicio)
  ↓
console_capture.start() → Redirige sys.stdout/sys.stderr
  ↓
Todos los print() → Capturados en buffer
  ↓
Vista Consola → Muestra buffer
```

### Archivos Involucrados
- `utils/console_capture.py` - Módulo de captura global
- `components/vista_consola.py` - Vista de consola
- `controllers/consola_controller.py` - Callbacks de actualización
- `app.py` - Inicialización de captura

### Sin Interferencias
- NO usa `dcc.Interval` para evitar actualizaciones automáticas en otras vistas
- Actualización manual con botón "Actualizar"
- Callbacks aislados con IDs únicos
- No afecta performance de otras vistas

## Casos de Uso

### Debugging
Ver mensajes de debug en tiempo real sin necesidad de terminal:
```python
print("🔵 DEBUG: Iniciando cálculo CMC")
print(f"📂 DEBUG: Estructura: {nombre}")
```

### Monitoreo de Errores
Capturar excepciones y warnings:
```python
print(f"⚠️  WARNING: Cache no encontrado")
print(f"❌ ERROR: {str(e)}")
```

### Auditoría
Revisar historial de operaciones realizadas durante la sesión.

## Limitaciones
- Buffer limitado a 10,000 líneas (últimas líneas se mantienen)
- No permite input de comandos (solo lectura)
- Se limpia al reiniciar la aplicación

## Mejoras Futuras
- Filtrado por tipo de mensaje (debug, warning, error)
- Búsqueda de texto en consola
- Exportar log a archivo
- Auto-scroll al final
