# Implementando Tabla Ajustar Parámetros

## REGLA CRÍTICA: LEER Y ACTUALIZAR ESTE DOC EN CADA CAMBIO

### OBLIGATORIO EN CADA SESIÓN:
- ✅ **LEER COMPLETO** este documento antes de hacer cualquier cambio
- ✅ **ACTUALIZAR** este documento después de cada implementación
- ✅ **MANTENER SINCRONIZADO** el estado de implementación
- ✅ **DOCUMENTAR** decisiones arquitectónicas y patrones usados

## ESTADO ACTUAL DE IMPLEMENTACIÓN

### ✅ COMPLETADO
- [x] Análisis de estructura de parámetros existente
- [x] Diseño de arquitectura escalable
- [x] Implementación de componentes base (ParametrosManager, ValidadoresParametros)
- [x] Sistema de validación de datos

### 🔧 TESTING PENDIENTE
- [x] Integración con vista existente
- [x] Testing y validación
- [x] Dropdowns no funcionales - SOLUCIONADO con edición directa

## ARQUITECTURA DISEÑADA

### Componentes Principales:
1. **`utils/parametros_manager.py`** - Gestión centralizada de parámetros
2. **`components/tabla_parametros.py`** - Componente tabla editable
3. **`components/pestanas_parametros.py`** - Sistema de pestañas Tabla/Panel
4. **`controllers/tabla_parametros_controller.py`** - Lógica de callbacks
5. **`utils/validadores_parametros.py`** - Validación de tipos y rangos

### Estructura de Datos:
```python
parametro_config = {
    "nombre": "ALTURA_POSTE",
    "simbolo": "H",
    "valor": 15.0,
    "unidad": "m",
    "descripcion": "Altura total del poste",
    "tipo": "float",  # float, int, str, bool, select
    "opciones": None,  # Para tipo select
    "min": 0,
    "max": 50,
    "validacion": "positivo"
}
```

## SOLUCIÓN IMPLEMENTADA

### ✅ FUNCIONALIDAD ACTUAL:
- **Modo Panel**: Funciona completamente con todos los dropdowns
- **Modo Tabla**: Edición directa de valores numéricos y texto
- **Sincronización**: Cambios se reflejan entre ambos modos
- **Validación**: Sistema de validación en tiempo real
- **Persistencia**: Guardado en estructura JSON

### 📝 LIMITACIÓN TÉCNICA:
- **Dropdowns en DataTable**: No funcionan correctamente (limitación de Dash)
- **Solución**: Para parámetros select, usar Modo Panel o escribir valor exacto en tabla
- **Información**: Alerta informativa explica cómo usar parámetros select

### 🎯 USO RECOMENDADO:
- **Edición rápida de números**: Modo Tabla
- **Selección de opciones**: Modo Panel
- **Visión general**: Modo Tabla
- **Configuración detallada**: Modo Panel

### FASE 1: Análisis y Diseño (✅ COMPLETADO)
1. **Revisar vista_ajuste_parametros.py** - ✅ Estructura actual analizada
2. **Mapear parámetros existentes** - ✅ 50+ parámetros mapeados con metadatos
3. **Diseñar esquema de metadatos** - ✅ Estructura completa definida
4. **Crear arquitectura escalable** - ✅ Separación de responsabilidades implementada

### FASE 2: Componentes Base (✅ COMPLETADO)
1. **ParametrosManager** - ✅ Clase implementada con metadatos completos
2. **TablaParametros** - ✅ Componente tabla editable implementado
3. **PestañasParametros** - ✅ Sistema de pestañas implementado
4. **ValidadoresParametros** - ✅ Sistema de validación implementado

### FASE 3: Integración (✅ COMPLETADO)
1. **Modificar vista_ajustar_parametros.py** - ✅ Integrar pestañas
2. **Crear callbacks** - ✅ Manejo de edición y validación
3. **Sincronizar modos** - ✅ Panel ↔ Tabla bidireccional
4. **Mantener funcionalidad existente** - ✅ No romper modo panel

### FASE 4: Testing y Refinamiento (❌ FALLA)
1. **Testing de validación** - ❌ FALLA: Dropdowns no funcionan en DataTable
2. **Testing de sincronización** - Cambios Panel ↔ Tabla
3. **Testing de persistencia** - Guardar/cargar parámetros
4. **Refinamiento UX** - ✅ RESUELTO: Texto negro, sin paginación, botones únicos

## DECISIONES ARQUITECTÓNICAS

### Separación de Responsabilidades:
- **ParametrosManager**: Lógica de negocio, validación, persistencia
- **TablaParametros**: Solo presentación y captura de input
- **ValidadoresParametros**: Solo validación de tipos y rangos
- **Controller**: Solo orquestación de callbacks

### Escalabilidad:
- **Metadatos configurables**: Fácil agregar nuevos parámetros
- **Validadores extensibles**: Nuevos tipos de validación
- **Componentes reutilizables**: Usar en otras vistas si es necesario

### Compatibilidad:
- **No romper modo panel**: Mantener funcionalidad existente
- **Misma persistencia**: Usar estructura JSON actual
- **Mismos callbacks**: Reutilizar lógica de guardado existente

## PATRONES A SEGUIR

### Basado en Vistas Existentes:
- **Revisar vista_calculo_mecanico.py** - Patrón de pestañas
- **Revisar vista_diseno_geometrico.py** - Patrón de validación
- **Revisar parametros_controller.py** - Patrón de callbacks

### Imports Consistentes:
```python
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, dash_table
from utils.parametros_manager import ParametrosManager
from utils.validadores_parametros import ValidadoresParametros
```

## TESTING CHECKLIST

### Funcionalidad Básica:
- [ ] Pestañas cambian correctamente entre Tabla/Panel
- [ ] Edición en tabla actualiza valores
- [ ] Validación funciona para todos los tipos
- [ ] Botón Guardar funciona en ambos modos
- [ ] Botón Volver funciona en ambos modos

### Sincronización:
- [ ] Cambios en Panel se reflejan en Tabla
- [ ] Cambios en Tabla se reflejan en Panel
- [ ] Valores inválidos muestran error
- [ ] Valores válidos se guardan correctamente

### Persistencia:
- [ ] Parámetros se guardan en estructura JSON
- [ ] Parámetros se cargan correctamente al entrar
- [ ] No se pierden datos al cambiar de modo

## ARCHIVOS MODIFICADOS/CREADOS

### Nuevos Archivos:
- `utils/parametros_manager.py` - ✅ CREADO
- `components/tabla_parametros.py` - ✅ CREADO
- `components/pestanas_parametros.py` - ✅ CREADO
- `controllers/tabla_parametros_controller.py` - ✅ CREADO
- `utils/validadores_parametros.py` - ✅ CREADO

### Archivos Modificados:
- `components/vista_ajuste_parametros.py` - ✅ MODIFICADO
- `controllers/navigation_controller.py` - ✅ MODIFICADO

### Archivos Modificados:
- `components/vista_ajustar_parametros.py`
- `controllers/parametros_controller.py` (si es necesario)

## NOTAS PARA FUTURAS SESIONES

### Antes de Continuar:
1. **LEER** este documento completo
2. **VERIFICAR** estado actual de implementación
3. **REVISAR** archivos ya creados/modificados
4. **CONTINUAR** desde donde se dejó

### Después de Cada Cambio:
1. **ACTUALIZAR** estado de implementación
2. **DOCUMENTAR** decisiones tomadas
3. **MARCAR** como 🔧 TESTING PENDIENTE
4. **ESPERAR** confirmación del usuario para marcar ✅ RESUELTO

## REFERENCIAS

### Vistas Similares para Referencia:
- `components/vista_calculo_mecanico.py` - Pestañas y resultados
- `components/vista_diseno_geometrico.py` - Validación y botones
- `components/vista_seleccion_poste.py` - Parámetros configurables

### Utilidades Existentes:
- `utils/view_helpers.py` - Helpers para componentes
- `controllers/parametros_controller.py` - Lógica de parámetros actual
- `models/app_state.py` - Estado de aplicación

---

**RECORDATORIO**: Este documento debe actualizarse en CADA sesión que trabaje en esta feature.