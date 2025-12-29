# Never Placeholders Rule

## REGLA CRÍTICA: NUNCA USAR IMPLEMENTACIONES FALSAS

### PROHIBIDO ABSOLUTAMENTE:
- ❌ Métodos que no existen (`cable.graficar_flechas()` cuando no existe)
- ❌ Datos simulados o generados con `hash()`, `random()`, etc.
- ❌ Placeholders como `# TODO: Implementar`, `pass`, comentarios vacíos
- ❌ Simulaciones o datos de prueba en lugar de lógica real
- ❌ Funciones dummy o mock que no implementan funcionalidad real
- ❌ Valores hardcodeados que deberían calcularse
- ❌ **VALORES POR DEFECTO CUANDO FALTAN DATOS REALES**
- ❌ **INVENTAR O GENERAR DATOS CUANDO NO EXISTEN**
- ❌ **USAR FALLBACKS CON DATOS FICTICIOS**

### OBLIGATORIO:
- ✅ Usar SOLO métodos y funciones que existen realmente
- ✅ Implementar lógica real y funcional
- ✅ Extraer datos de fuentes reales (DataFrames, objetos, archivos)
- ✅ Verificar que métodos existen antes de usarlos
- ✅ Usar funciones existentes y probadas del proyecto
- ✅ **MOSTRAR ERROR CLARO CUANDO FALTAN DATOS OBLIGATORIOS**
- ✅ **FORZAR AL USUARIO A PROPORCIONAR DATOS REALES**
- ✅ **RETORNAR NULL/NONE CUANDO NO HAY DATOS VÁLIDOS**

### EJEMPLOS DE ERRORES COMUNES:

#### ❌ MAL - Usar valores por defecto cuando faltan datos:
```python
# PROHIBIDO - Inventar datos cuando no existen
if not parametros_sph:
    return {'Gp': 4680, 'Ft': 1030}  # ❌ DATOS INVENTADOS

# PROHIBIDO - Fallback con datos ficticios
tension = datos.get('tension', 2500)  # ❌ VALOR INVENTADO
```

#### ✅ BIEN - Mostrar error cuando faltan datos:
```python
# CORRECTO - Error claro sin inventar datos
if not parametros_sph:
    raise ValueError("Debe ejecutar SPH primero para obtener parámetros")
    
# CORRECTO - Retornar None cuando no hay datos
if not datos_validos:
    return None
```

### SI NO SE PUEDE IMPLEMENTAR CORRECTAMENTE:
1. **MARCAR COMO PENDIENTE** en documentación
2. **AVISAR AL USUARIO** explícitamente que falta implementación
3. **NO CREAR CÓDIGO FALSO** que aparente funcionar
4. **EXPLICAR QUÉ SE NECESITA** para implementar correctamente
5. **MOSTRAR ERROR CLARO** indicando qué datos faltan

### EJEMPLO DE LO QUE NO HACER:
```python
# ❌ PROHIBIDO - Método que no existe
fig = cable.graficar_flechas()

# ❌ PROHIBIDO - Datos simulados
tensiones = [2500 + hash(cable + estado) % 1000 for estado in estados]

# ❌ PROHIBIDO - Valores por defecto inventados
if not sph_data:
    sph_data = {'peso': 4680, 'fuerza': 1030}  # ❌ INVENTADO

# ❌ PROHIBIDO - Placeholder
def calcular_algo():
    # TODO: Implementar después
    return 0
```

### EJEMPLO DE LO QUE SÍ HACER:
```python
# ✅ CORRECTO - Usar función existente
from utils.plot_flechas import crear_grafico_flechas
fig_combinado, fig_conductor, fig_guardia = crear_grafico_flechas(cable, guardia, vano)

# ✅ CORRECTO - Extraer datos reales
df_data = json.loads(resultado['dataframe_html'])
df = pd.DataFrame(df_data['data'], columns=df_data['columns'])
tension_real = df.loc[estado, 'Tiro [daN]']

# ✅ CORRECTO - Error claro cuando faltan datos
if not sph_data:
    raise ValueError("Debe ejecutar SPH primero para obtener parámetros de estructura")

# ✅ CORRECTO - Marcar como pendiente si no se puede
return {"error": "Función no implementada - requiere desarrollo adicional"}
```

## PARA FUTURAS SESIONES:
**ANTES de escribir cualquier código, verificar que:**
1. Los métodos/funciones existen realmente
2. Los datos son reales, no simulados
3. La implementación es funcional, no placeholder
4. Si faltan datos obligatorios, mostrar error claro
5. Si no se puede hacer correctamente, marcar como PENDIENTE y avisar al usuario

**NUNCA fingir que algo funciona cuando no funciona.**
**NUNCA inventar datos cuando no existen.**
**NUNCA usar valores por defecto para datos que deben ser reales.**