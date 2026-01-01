# Regla: LEER Implementando Familias

## REGLA OBLIGATORIA PARA TODAS LAS SESIONES

### ANTES DE CUALQUIER TRABAJO EN FAMILIAS DE ESTRUCTURAS:

1. **LEER COMPLETO** el documento `docs/Implementacion_familias.md`
2. **ENTENDER** el estado actual de la implementación
3. **IDENTIFICAR** qué fase/tarea está pendiente
4. **REVISAR** los patrones a reutilizar especificados

### DESPUÉS DE CUALQUIER CAMBIO:

1. **ACTUALIZAR** el documento `docs/Implementacion_familias.md`
2. **MARCAR** tareas completadas con ✅
3. **MARCAR** nuevas tareas pendientes con ❌
4. **AGREGAR** entrada en "Log de Cambios" con fecha y descripción
5. **ACTUALIZAR** "Última actualización" en el encabezado

### ESTADOS DE TAREAS:
- ✅ **COMPLETADO**: Tarea implementada y funcionando
- 🔧 **TESTING PENDIENTE**: Implementado, esperando confirmación usuario
- ❌ **PENDIENTE**: No implementado aún
- ⚠️ **BLOQUEADO**: Depende de otra tarea

### FORMATO LOG DE CAMBIOS:
```markdown
### YYYY.MM.DD
- ✅ Tarea completada
- 🔧 Tarea implementada (testing pendiente)
- ❌ Nueva tarea identificada
- ⚠️ Problema encontrado
```

### IMPORTANTE:
- **NO DUPLICAR CÓDIGO** - Siempre revisar qué se puede reutilizar
- **MANTENER CONSISTENCIA** - Seguir patrones existentes
- **DOCUMENTAR CAMBIOS** - Cada modificación debe quedar registrada
- **RESPETAR FASES** - No implementar Vano Económico hasta que Familia esté completa

### ARCHIVOS CLAVE A REVISAR:
- `components/vista_ajustar_parametros.py` - Para tabla multi-columna
- `controllers/calcular_todo_controller.py` - Para orquestación cálculos
- `utils/calculo_cache.py` - Para sistema cache
- `utils/descargar_html.py` - Para descarga HTML

**Esta regla es OBLIGATORIA y debe seguirse en TODAS las sesiones que trabajen con Familias de Estructuras.**