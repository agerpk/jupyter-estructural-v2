# Sistema de Cache para Familias de Estructuras

## Arquitectura

El sistema de cache para familias utiliza un **patrón de referencias** en lugar de duplicar datos, aprovechando los caches individuales ya existentes de cada estructura.

### Flujo de Guardado

```
Calcular Familia
    ↓
Crear archivos temporales: {titulo}.estructura.json
    ↓
Ejecutar secuencia CMC>DGE>DME>SPH>FUND>COSTEO
    ↓
Generar caches individuales: {titulo}.calculoCMC.json, etc.
    ↓
Guardar cache familia: {nombre}.calculoFAMILIA.json (solo referencias)
    ↓
Eliminar archivos temporales
```

### Flujo de Carga

```
Cargar Cache Familia
    ↓
Leer {nombre}.calculoFAMILIA.json
    ↓
Verificar hash (vigencia)
    ↓
Reconstruir desde caches individuales
    ↓
Generar vista con pestañas
```

## Estructura de Archivos

### Cache de Familia (`{nombre}.calculoFAMILIA.json`)

```json
{
  "hash_parametros": "abc123...",
  "fecha_calculo": "2026-01-02T10:00:00",
  "estructuras": {
    "Estr.1": {
      "titulo": "Estructura Terminal",
      "cantidad": 2,
      "costo_individual": 15000.50,
      "cache_refs": {
        "cmc": "Estructura_Terminal.calculoCMC.json",
        "dge": "Estructura_Terminal.calculoDGE.json",
        "dme": "Estructura_Terminal.calculoDME.json",
        "arboles": "Estructura_Terminal.calculoARBOLES.json",
        "sph": "Estructura_Terminal.calculoSPH.json",
        "fundacion": "Estructura_Terminal.calculoFUND.json",
        "costeo": "Estructura_Terminal.calculoCOSTEO.json"
      }
    },
    "Estr.2": { ... }
  },
  "costeo_global": {
    "costo_global": 45000.75,
    "costos_individuales": { ... },
    "costos_parciales": { ... }
  }
}
```

### Caches Individuales (ya existentes)

- `{titulo}.calculoCMC.json` - Resultados CMC + referencias a imágenes
- `{titulo}.calculoDGE.json` - Resultados DGE + referencias a imágenes
- `{titulo}.calculoDME.json` - Resultados DME + referencias a imágenes
- `{titulo}.calculoARBOLES.json` - Resultados árboles + referencias a imágenes
- `{titulo}.calculoSPH.json` - Resultados SPH
- `{titulo}.calculoFUND.json` - Resultados fundación + referencias a imágenes
- `{titulo}.calculoCOSTEO.json` - Resultados costeo

## Ventajas del Sistema de Referencias

### ✅ Eficiencia de Almacenamiento
- **Sin duplicación**: No se duplican datos de cálculos individuales
- **Tamaño reducido**: Cache familia solo guarda referencias (~5KB vs ~50MB)
- **Reutilización**: Caches individuales sirven para vistas individuales y familia

### ✅ Consistencia
- **Única fuente de verdad**: Caches individuales son la fuente autoritativa
- **Sincronización automática**: Cambios en caches individuales se reflejan en familia
- **Validación unificada**: Hash de familia valida toda la configuración

### ✅ Mantenibilidad
- **Limpieza simple**: Eliminar cache familia no afecta caches individuales
- **Debugging fácil**: Cada cache individual es independiente y verificable
- **Escalabilidad**: Agregar estructuras no aumenta exponencialmente el tamaño

## Métodos Implementados

### `CalculoCache.calcular_hash_familia(familia_data)`
Calcula hash MD5 de familia excluyendo fechas.

### `CalculoCache.guardar_calculo_familia(nombre, familia_data, resultados)`
Guarda referencias a caches individuales + costeo global.

### `CalculoCache.cargar_calculo_familia(nombre)`
Carga cache y reconstruye desde caches individuales.

### `CalculoCache.verificar_vigencia_familia(cache, familia_actual)`
Verifica si hash coincide con configuración actual.

## Callbacks Implementados

### `calcular_familia_completa()`
1. Convierte tabla a formato familia
2. Ejecuta cálculo completo
3. Guarda cache en background (threading)
4. Genera vista con pestañas

### `cargar_cache_familia()`
1. Carga cache de familia
2. Verifica vigencia (hash)
3. Reconstruye desde caches individuales
4. Genera vista con pestañas

## Testing

### Caso 1: Calcular y Guardar Cache
```
1. Crear familia con 2 estructuras
2. Presionar "Calcular Familia"
3. Verificar que se crea {nombre}.calculoFAMILIA.json en /data/cache/
4. Verificar que existen caches individuales para cada estructura
5. Verificar tamaño del cache familia (~5KB)
```

### Caso 2: Cargar Cache Válido
```
1. Con familia calculada, presionar "Cargar desde Cache"
2. Verificar que carga instantáneamente
3. Verificar que muestra todas las pestañas
4. Verificar que gráficos son interactivos
```

### Caso 3: Cache Inválido (Hash No Coincide)
```
1. Cargar familia con cache existente
2. Modificar un parámetro en tabla (ej: L_vano)
3. Presionar "Cargar desde Cache"
4. Verificar toast: "Hash no coincide, recalcular"
```

### Caso 4: Cache No Disponible
```
1. Crear nueva familia sin calcular
2. Presionar "Cargar desde Cache"
3. Verificar toast: "Cache no disponible"
```

## Limitaciones y Consideraciones

### Dependencia de Caches Individuales
- Si se eliminan caches individuales, la carga de familia falla parcialmente
- Solución: Mantener caches individuales mientras exista cache familia

### Archivos Temporales
- Durante cálculo se crean `{titulo}.estructura.json` temporales
- Se eliminan automáticamente después de calcular
- Si falla el cálculo, pueden quedar archivos huérfanos

### Sincronización
- Cache familia no se actualiza automáticamente si cambian caches individuales
- Solución: Recalcular familia si se modifican estructuras individuales

## Mejoras Futuras

### Validación de Integridad
- Verificar que todos los caches individuales existen antes de cargar
- Mostrar advertencia si faltan caches parciales

### Limpieza Automática
- Eliminar caches individuales huérfanos cuando se elimina familia
- Limpiar archivos temporales en caso de error

### Compresión
- Comprimir referencias si familia tiene muchas estructuras
- Usar formato binario para caches muy grandes

## Conclusión

El sistema de cache por referencias es **eficiente, escalable y mantenible**, aprovechando la infraestructura existente de caches individuales sin duplicar datos innecesariamente.
