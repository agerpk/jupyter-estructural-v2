# Regla: Reutilizar Soluciones

## REGLA CRÍTICA: SIEMPRE REVISAR CÓDIGO EXISTENTE ANTES DE IMPLEMENTAR

### OBLIGATORIO:
- ✅ **ANTES de implementar cualquier funcionalidad**, buscar si ya existe una implementación similar en el proyecto
- ✅ **REVISAR archivos relacionados** para entender patrones y estructuras existentes
- ✅ **COPIAR Y ADAPTAR** soluciones probadas en lugar de crear desde cero
- ✅ **MANTENER CONSISTENCIA** con patrones arquitectónicos existentes
- ✅ **USAR MISMOS IMPORTS** y estructuras que otras partes del código

### PROHIBIDO:
- ❌ Improvisar soluciones cuando ya existen implementaciones similares
- ❌ Crear nuevos patrones cuando ya hay patrones establecidos
- ❌ Usar diferentes imports o estructuras sin justificación
- ❌ Reinventar funcionalidades que ya están implementadas

### PROCESO OBLIGATORIO:

#### 1. IDENTIFICAR FUNCIONALIDAD SIMILAR
- Buscar archivos que implementen funcionalidad parecida
- Revisar controllers, vistas, y utilidades relacionadas
- Identificar patrones de imports, estructura, y lógica

#### 2. ANALIZAR IMPLEMENTACIÓN EXISTENTE
- Estudiar cómo se resolvió el problema similar
- Identificar imports necesarios
- Entender la estructura de datos y flujo
- Revisar manejo de errores y casos edge

#### 3. ADAPTAR SOLUCIÓN EXISTENTE
- Copiar estructura base de la implementación similar
- Adaptar solo lo necesario para el nuevo caso
- Mantener mismos imports y patrones
- Preservar manejo de errores y validaciones

### EJEMPLOS DE APLICACIÓN:

#### ✅ CORRECTO - Reutilizar patrón de vista CMC:
```python
# Revisar vista_calculo_mecanico.py primero
# Copiar estructura de resultados_html
# Usar mismos imports: dbc, html, ViewHelpers
# Mantener patrón de dbc.Table.from_dataframe()
```

#### ❌ INCORRECTO - Improvisar nueva estructura:
```python
# Crear nueva forma de mostrar tablas
# Usar diferentes imports
# Inventar nueva estructura de componentes
```

### CASOS COMUNES:

1. **Nuevas vistas**: Revisar vistas existentes similares
2. **Callbacks**: Copiar estructura de callbacks similares
3. **Manejo de datos**: Usar patrones de ViewHelpers existentes
4. **Imports**: Mantener consistencia con archivos similares
5. **Estructura HTML**: Reutilizar patrones de componentes

### BENEFICIOS:
- **Consistencia**: Toda la aplicación sigue los mismos patrones
- **Confiabilidad**: Soluciones ya probadas y funcionando
- **Mantenibilidad**: Código predecible y familiar
- **Velocidad**: Menos tiempo implementando, más tiempo adaptando
- **Menos errores**: Evita problemas ya resueltos

### PARA FUTURAS SESIONES:
**SIEMPRE preguntar: "¿Dónde se hizo algo similar en este proyecto?" antes de implementar cualquier funcionalidad nueva.**

## Aplicación Inmediata:
- Error `dbc is not defined` → Revisar imports de vista_calculo_mecanico.py
- Estructura de resultados → Copiar patrón exacto de CMC
- Manejo de DataFrames → Usar mismo patrón de otras vistas