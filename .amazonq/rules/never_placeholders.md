# Never Placeholders Rule

## REGLA CRÍTICA: NUNCA USAR IMPLEMENTACIONES FALSAS

### PROHIBIDO ABSOLUTAMENTE:
- ❌ Métodos que no existen (`cable.graficar_flechas()` cuando no existe)
- ❌ Datos simulados o generados con `hash()`, `random()`, etc.
- ❌ Placeholders como `# TODO: Implementar`, `pass`, comentarios vacíos
- ❌ Simulaciones o datos de prueba en lugar de lógica real
- ❌ Funciones dummy o mock que no implementan funcionalidad real
- ❌ Valores hardcodeados que deberían calcularse

### OBLIGATORIO:
- ✅ Usar SOLO métodos y funciones que existen realmente
- ✅ Implementar lógica real y funcional
- ✅ Extraer datos de fuentes reales (DataFrames, objetos, archivos)
- ✅ Verificar que métodos existen antes de usarlos
- ✅ Usar funciones existentes y probadas del proyecto

### SI NO SE PUEDE IMPLEMENTAR CORRECTAMENTE:
1. **MARCAR COMO PENDIENTE** en documentación
2. **AVISAR AL USUARIO** explícitamente que falta implementación
3. **NO CREAR CÓDIGO FALSO** que aparente funcionar
4. **EXPLICAR QUÉ SE NECESITA** para implementar correctamente

### EJEMPLO DE LO QUE NO HACER:
```python
# ❌ PROHIBIDO - Método que no existe
fig = cable.graficar_flechas()

# ❌ PROHIBIDO - Datos simulados
tensiones = [2500 + hash(cable + estado) % 1000 for estado in estados]

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

# ✅ CORRECTO - Marcar como pendiente si no se puede
return {"error": "Función no implementada - requiere desarrollo adicional"}
```

## PARA FUTURAS SESIONES:
**ANTES de escribir cualquier código, verificar que:**
1. Los métodos/funciones existen realmente
2. Los datos son reales, no simulados
3. La implementación es funcional, no placeholder
4. Si no se puede hacer correctamente, marcar como PENDIENTE y avisar al usuario

**NUNCA fingir que algo funciona cuando no funciona.**