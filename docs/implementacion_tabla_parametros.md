# Plan de Implementación: Sistema Tabla de Parámetros

## RESUMEN EJECUTIVO

Implementar vista de tabla editable para parámetros de estructura con pestañas "Modo Tabla" y "Modo Panel", manteniendo funcionalidad existente y agregando capacidades de edición tabular con validación.

## ANÁLISIS DE REQUERIMIENTOS

### Funcionalidades Requeridas:
1. **Pestañas**: "Modo Tabla" y "Modo Panel" 
2. **Tabla Editable**: Columnas Parámetro, Símbolo, Valor, Unidad, Descripción
3. **Validación**: Por tipo de dato (string, bool, int, float)
4. **Controles**: Dropdown para select, input numérico para números
5. **Botones**: Guardar Parámetros y Volver en ambos modos
6. **Persistencia**: Guardar en estructura JSON activa

### Restricciones:
- No romper funcionalidad existente del modo panel
- Arquitectura escalable y modular
- No sobrecargar un solo archivo
- Sincronización bidireccional entre modos

## ARQUITECTURA PROPUESTA

### Estructura de Archivos:
```
/utils/
  parametros_manager.py          # Gestión centralizada de parámetros
  validadores_parametros.py      # Validación por tipos
  
/components/
  tabla_parametros.py            # Componente tabla editable
  pestanas_parametros.py         # Sistema de pestañas
  vista_ajustar_parametros.py    # Vista principal (modificar)
  
/controllers/
  tabla_parametros_controller.py # Callbacks para tabla
  parametros_controller.py       # Callbacks existentes (modificar)
```

### Flujo de Datos:
```
Usuario → Pestaña → Componente (Tabla/Panel) → Controller → ParametrosManager → JSON
```

## DISEÑO DETALLADO

### 1. ParametrosManager (utils/parametros_manager.py)

**Responsabilidades:**
- Cargar/guardar parámetros desde/hacia JSON
- Definir metadatos de parámetros (tipo, validación, opciones)
- Convertir entre formato interno y formato tabla
- Validar valores según tipo

**Métodos Principales:**
```python
class ParametrosManager:
    def obtener_metadatos_parametros() -> dict
    def estructura_a_tabla(estructura: dict) -> list
    def tabla_a_estructura(tabla_data: list) -> dict
    def validar_valor(parametro: str, valor: any) -> tuple[bool, str]
    def obtener_opciones_parametro(parametro: str) -> list
```

### 2. ValidadoresParametros (utils/validadores_parametros.py)

**Responsabilidades:**
- Validar tipos de datos (int, float, str, bool)
- Validar rangos numéricos
- Validar opciones de select
- Generar mensajes de error descriptivos

### 3. TablaParametros (components/tabla_parametros.py)

**Responsabilidades:**
- Renderizar tabla editable con dash_table.DataTable
- Configurar columnas editables/no editables
- Aplicar validación visual
- Manejar tipos de input (dropdown, numérico, texto)

### 4. PestañasParametros (components/pestanas_parametros.py)

**Responsabilidades:**
- Renderizar pestañas "Modo Tabla" y "Modo Panel"
- Manejar cambio entre modos
- Mantener estado activo de pestaña

### 5. TablaParametrosController (controllers/tabla_parametros_controller.py)

**Responsabilidades:**
- Callback para cambio de pestañas
- Callback para edición de tabla
- Callback para validación en tiempo real
- Sincronización entre modos

## IMPLEMENTACIÓN POR FASES

### FASE 1: Análisis y Preparación
**Objetivo:** Entender estructura actual y diseñar metadatos

**Tareas:**
1. Revisar `components/vista_ajustar_parametros.py`
2. Mapear todos los parámetros existentes
3. Definir esquema de metadatos
4. Crear estructura de datos para tabla

**Entregables:**
- Inventario completo de parámetros
- Esquema de metadatos definido
- Estructura de datos diseñada

### FASE 2: Componentes Base
**Objetivo:** Crear componentes reutilizables

**Tareas:**
1. Implementar `ParametrosManager`
2. Implementar `ValidadoresParametros`
3. Implementar `TablaParametros`
4. Implementar `PestañasParametros`

**Entregables:**
- Componentes base funcionales
- Tests unitarios básicos
- Documentación de API

### FASE 3: Integración
**Objetivo:** Integrar con vista existente

**Tareas:**
1. Modificar `vista_ajustar_parametros.py`
2. Crear `tabla_parametros_controller.py`
3. Modificar `parametros_controller.py` si necesario
4. Implementar sincronización bidireccional

**Entregables:**
- Vista integrada con pestañas
- Callbacks funcionando
- Sincronización Panel ↔ Tabla

### FASE 4: Testing y Refinamiento
**Objetivo:** Validar funcionalidad completa

**Tareas:**
1. Testing exhaustivo de validación
2. Testing de sincronización
3. Testing de persistencia
4. Refinamiento de UX

**Entregables:**
- Feature completamente funcional
- Documentación actualizada
- Testing checklist completado

## ESPECIFICACIONES TÉCNICAS

### Metadatos de Parámetros:
```python
PARAMETROS_METADATA = {
    "ALTURA_POSTE": {
        "simbolo": "H",
        "unidad": "m",
        "descripcion": "Altura total del poste",
        "tipo": "float",
        "min": 0,
        "max": 50,
        "validacion": "positivo"
    },
    "TIPO_ESTRUCTURA": {
        "simbolo": "TE",
        "unidad": "-",
        "descripcion": "Tipo de estructura",
        "tipo": "select",
        "opciones": ["Suspensión", "Retención", "Angular", "Terminal"]
    }
}
```

### Estructura de Tabla:
```python
tabla_data = [
    {
        "parametro": "ALTURA_POSTE",
        "simbolo": "H",
        "valor": 15.0,
        "unidad": "m",
        "descripcion": "Altura total del poste"
    }
]
```

### Configuración DataTable:
```python
dash_table.DataTable(
    columns=[
        {"name": "Parámetro", "id": "parametro", "editable": False},
        {"name": "Símbolo", "id": "simbolo", "editable": False},
        {"name": "Valor", "id": "valor", "editable": True, "type": "any"},
        {"name": "Unidad", "id": "unidad", "editable": False},
        {"name": "Descripción", "id": "descripcion", "editable": False}
    ],
    editable=True,
    row_deletable=False,
    style_cell={'textAlign': 'left'},
    style_data_conditional=[
        {
            'if': {'column_id': 'valor'},
            'backgroundColor': '#f8f9fa'
        }
    ]
)
```

## CONSIDERACIONES DE UX

### Validación Visual:
- Celdas con error: fondo rojo claro
- Celdas válidas: fondo normal
- Tooltips con mensajes de error
- Indicadores de tipo de dato

### Sincronización:
- Cambios en tabla se reflejan inmediatamente en panel
- Cambios en panel se reflejan inmediatamente en tabla
- Estado de validación se mantiene entre modos

### Performance:
- Validación en tiempo real sin lag
- Carga rápida de tabla con muchos parámetros
- Sincronización eficiente entre modos

## TESTING STRATEGY

### Unit Tests:
- ParametrosManager: conversión de datos
- ValidadoresParametros: validación por tipo
- Componentes: renderizado correcto

### Integration Tests:
- Sincronización Panel ↔ Tabla
- Persistencia en JSON
- Validación end-to-end

### User Acceptance Tests:
- Flujo completo de edición
- Manejo de errores
- Usabilidad de pestañas

## RIESGOS Y MITIGACIONES

### Riesgo: Romper funcionalidad existente
**Mitigación:** Mantener modo panel intacto, solo agregar funcionalidad

### Riesgo: Performance con muchos parámetros
**Mitigación:** Paginación en tabla, lazy loading

### Riesgo: Sincronización compleja
**Mitigación:** Estado centralizado, callbacks bien definidos

### Riesgo: Validación inconsistente
**Mitigación:** Validadores centralizados, tests exhaustivos

## MÉTRICAS DE ÉXITO

### Funcionalidad:
- ✅ Pestañas cambian correctamente
- ✅ Tabla permite edición de valores
- ✅ Validación funciona para todos los tipos
- ✅ Sincronización bidireccional funciona
- ✅ Persistencia mantiene datos

### Performance:
- ✅ Carga de tabla < 2 segundos
- ✅ Cambio de pestañas < 0.5 segundos
- ✅ Validación en tiempo real < 0.2 segundos

### Usabilidad:
- ✅ Interfaz intuitiva
- ✅ Mensajes de error claros
- ✅ No pérdida de datos al cambiar modos

---

**PRÓXIMOS PASOS:**
1. Revisar y aprobar este plan
2. Iniciar FASE 1: Análisis y Preparación
3. Actualizar documento de implementación con progreso