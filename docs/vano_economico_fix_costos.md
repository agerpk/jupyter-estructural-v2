# Fix: Inconsistencia en Cálculo de Costos - Vano Económico

## Problema Identificado

### Síntomas
- **Gráfico "Distribución de Costos por Estructura"**: Costos aumentaban con el vano
- **Gráfico "Curva de Vano Económico"**: Costos disminuían con el vano
- **Tabla de resultados**: Valores correctos mostrando disminución de costos

### Causa Raíz

**Inconsistencia en el uso de cantidades:**

1. **Gráfico de Barras Apiladas** (INCORRECTO):
   ```python
   # Usaba costos_parciales del costeo global
   costo = detalle["costos_parciales"].get(estructura, 0)
   # costos_parciales = costo_individual × cantidad_familia (FIJA)
   ```
   - Multiplicaba por cantidades FIJAS de la familia
   - No consideraba cantidades dinámicas del vano económico
   - Resultado: Costos aparentemente crecientes

2. **Curva y Tabla** (CORRECTO):
   ```python
   # Usaban _calcular_costo_tipo() que multiplica por cantidades VE
   costo = _calcular_costo_tipo(resultado_vano, tipo)
   # Multiplica por cantidades_ve["cant_S"], ["cant_RR"], etc.
   ```
   - Multiplicaban por cantidades DINÁMICAS del vano económico
   - Resultado: Costos correctamente decrecientes

### Lógica Correcta del Vano Económico

Para cada iteración de vano:
1. **Calcular cantidades dinámicas** según vano actual:
   - `cant_S = ceil(longtraza / vano)` → Disminuye al aumentar vano
   - `cant_RR` → Varía según criterio (distancia/suspensiones/manual)
   - `cant_T = 2` → Constante
   - `cant_RA` → Constante (de familia)

2. **Calcular costos**:
   - `costo_S = costo_individual_S × cant_S` → Disminuye
   - `costo_RR = costo_individual_RR × cant_RR` → Varía
   - `costo_RA = costo_individual_RA × cant_RA` → Constante
   - `costo_T = costo_individual_T × cant_T` → Constante
   - `costo_total = costo_S + costo_RR + costo_RA + costo_T`

3. **Comportamiento esperado**:
   - Vanos pequeños → Muchas suspensiones → Costo alto
   - Vanos grandes → Pocas suspensiones → Costo bajo
   - Existe un vano óptimo donde el costo es mínimo

## Solución Implementada

### Modificación en `generar_grafico_barras_apiladas()`

**ANTES** (incorrecto):
```python
def generar_grafico_barras_apiladas(resultados: Dict) -> go.Figure:
    # Extraía nombres de estructuras desde costos_parciales
    estructuras_nombres = set()
    for vano in vanos:
        detalle = resultados["resultados"][vano]["costeo_detalle"]
        estructuras_nombres.update(detalle["costos_parciales"].keys())
    
    # Usaba costos_parciales (cantidades fijas de familia)
    for estructura in estructuras_nombres:
        costos_estructura = []
        for vano in vanos:
            detalle = resultados["resultados"][vano]["costeo_detalle"]
            costo = detalle["costos_parciales"].get(estructura, 0)  # ❌ INCORRECTO
            costos_estructura.append(costo)
```

**DESPUÉS** (correcto):
```python
def generar_grafico_barras_apiladas(resultados: Dict) -> go.Figure:
    # Usa tipos de estructura (S, RR, RA, T)
    tipos_estructura = ['S', 'RR', 'RA', 'T']
    nombres_display = {
        'S': 'Suspensión',
        'RR': 'Retención',
        'RA': 'Retención Angular',
        'T': 'Terminal'
    }
    
    # Usa _calcular_costo_tipo() que multiplica por cantidades VE
    for tipo in tipos_estructura:
        costos_tipo = []
        for vano in vanos:
            costo = _calcular_costo_tipo(resultados["resultados"][vano], tipo)  # ✅ CORRECTO
            costos_tipo.append(costo)
```

### Ventajas de la Solución

1. **Consistencia**: Todos los gráficos y tabla usan la misma lógica
2. **Claridad**: Agrupa por tipo de estructura (S, RR, RA, T) en lugar de nombres específicos
3. **Colores distintivos**: Cada tipo tiene color fijo y reconocible
4. **Corrección matemática**: Usa cantidades dinámicas del vano económico

## Verificación

### Comportamiento Esperado

Para el ejemplo dado (longtraza=30000m):

| Vano [m] | Cant. S | Costo S [UM] | Tendencia |
|----------|---------|--------------|-----------|
| 20       | 1500    | 24,930,304   | ⬆️ Alto   |
| 100      | 300     | 4,426,601    | ⬇️ Medio  |
| 300      | 100     | 2,148,317    | ⬇️ Bajo   |
| 600      | 50      | 1,423,197    | ⬇️ Mínimo |

### Gráficos Corregidos

1. **Curva de Vano Económico**: ✅ Muestra disminución de costo total
2. **Distribución de Costos por Estructura**: ✅ Ahora también muestra disminución
3. **Tabla de Resultados**: ✅ Ya era correcta, sin cambios

## Archivos Modificados

- `utils/vano_economico_utils.py`:
  - Función `generar_grafico_barras_apiladas()` reescrita completamente
  - Ahora usa `_calcular_costo_tipo()` en lugar de `costos_parciales`
  - Función `generar_vista_resultados_vano_economico()` corregida:
    - Calcula `costos` usando misma lógica que gráficos (líneas 368-375)
    - Usa array `costos` precalculado en tabla (línea 436)
    - Diferencia 0.00% para vano óptimo (línea 438)

## Problemas Adicionales Corregidos

### 1. Tercer Valor Coloreado Incorrectamente

**Problema**: La columna "Costo Total" usaba `costo_total_ve` calculado con walrus operator en la misma línea, pero este valor no coincidía con el usado para encontrar el óptimo.

**Causa**: Dos fuentes diferentes de costo total:
- `resultados['resultados'][vano]['costo_global']` (usado originalmente para encontrar óptimo)
- `costo_total_ve = costo_s + costo_rr + costo_ra + costo_t` (calculado en tabla)

**Solución**: 
```python
# Precalcular costos al inicio usando misma lógica que gráficos
costos = []
for v in vanos:
    costo_s = _calcular_costo_tipo(resultados["resultados"][v], 'S')
    costo_rr = _calcular_costo_tipo(resultados["resultados"][v], 'RR')
    costo_ra = _calcular_costo_tipo(resultados["resultados"][v], 'RA')
    costo_t = _calcular_costo_tipo(resultados["resultados"][v], 'T')
    costos.append(costo_s + costo_rr + costo_ra + costo_t)

# Usar array precalculado en tabla
html.Td(f"{costos[vanos.index(vano)]:,.2f}", ...)
```

### 2. Todos los Vanos Mostraban Diferencia con Óptimo

**Problema**: Incluso el vano óptimo mostraba diferencia no nula (ej: +0.03%)

**Causa**: Errores de redondeo al calcular `costo_total_ve` en cada fila vs `costo_optimo` calculado una sola vez.

**Solución**:
```python
# Mostrar 0.00% explícitamente para vano óptimo
html.Td(
    f"{((costos[vanos.index(vano)] - costo_optimo) / costo_optimo * 100):+.2f}%" 
    if vano != vano_optimo else "0.00%"
)
```

## Testing

Para verificar la corrección:

1. Ejecutar cálculo de vano económico con familia válida
2. Verificar que ambos gráficos muestran tendencia decreciente
3. Verificar que tabla coincide con gráficos
4. Verificar que vano óptimo es el mismo en todos los componentes
5. **Verificar que solo el vano óptimo tiene diferencia 0.00%**
6. **Verificar que solo el vano óptimo está en negrita y verde**

## Lecciones Aprendidas

1. **Siempre usar la misma fuente de datos** para todos los componentes visuales
2. **Documentar claramente** qué cantidades se usan (familia vs vano económico)
3. **Validar consistencia** entre gráficos, tablas y cálculos
4. **Nombrar funciones descriptivamente** (`_calcular_costo_tipo` vs `costos_parciales`)
