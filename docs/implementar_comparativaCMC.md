# Implementación Comparativa CMC

## Estado Actual: 🔧 TESTING PENDIENTE

### Problema Identificado: ❌ FALLA
**Vista CC (Comparativa cables) no funciona correctamente**
- Error: Cable conductor 'Catbird' no encontrado
- Error: unsupported format string passed to NoneType.__format__
- La lógica no usaba métodos reales de Cable_AEA para generar gráficos de flechas
- Gráfico comparativo usaba datos simulados en lugar de resultados reales

### Fix Implementado: 🔧 TESTING PENDIENTE
**Fecha**: 2024-12-19
**Cambios realizados**:

1. **Corregido problema de cables no encontrados** en `utils/calculo_objetos.py`:
   - Modificado `_cargar_datos_cables()` para usar `cables_2.json` primero
   - Fallback a `DatosCables.py` si no existe cables_2.json
   - Cable 'Catbird' ahora disponible desde cables_2.json

2. **Eliminados errores de format string**:
   - Removidos f-strings problemáticos que causaban "unsupported format string passed to NoneType.__format__"
   - Cambiados a concatenación de strings normal
   - Validación de valores None antes de formatear

3. **Corregida lógica de gráficos** en `utils/comparativa_cmc_calculo.py`:
   - Cambiado de métodos inexistentes `cable_conductor.graficar_flechas()` a `utils.plot_flechas.crear_grafico_flechas()`
   - Usa la función existente que funciona en CMC normal
   - Solo incluye gráfico del conductor para comparativa

4. **Mejorado gráfico comparativo**:
   - Cambiado de datos simulados (hash) a datos reales del DataFrame
   - Busca filas por descripción de estado climático (Tmáx, Tmín, Vmáx, Vmed, TMA)
   - Extrae valores reales de Tiro [daN] y Flecha Vertical [m]
   - Manejo robusto de columnas con nombres variables

5. **Arquitectura corregida**:
   - Usa `crear_grafico_flechas()` existente que funciona en CMC
   - Mantiene compatibilidad con lógica CMC real
   - Genera gráficos individuales por cable usando métodos probados

### Nueva Feature Implementada: 🔧 TESTING PENDIENTE
**Fecha**: 2024-12-19
**Tabla Comparativa de Cables**:

6. **Agregada tabla comparativa en pestaña Comparativa**:
   - Función `crear_tabla_comparativa()` en `vista_comparar_cables.py`
   - Primera columna: "Valores/Cable" con propiedades y resultados
   - Columnas adicionales: Una por cada cable seleccionado
   - Filas incluyen:
     - **Propiedades del cable**: Sección nominal, diámetro, peso, carga rotura, módulo elasticidad, coef. dilatación
     - **Resultados calculados**: Flecha máxima, tiro máximo
   - Datos extraídos de `cables.json` y DataFrames de resultados
   - Tabla responsive con formato Bootstrap

7. **Integración en resultados**:
   - Tabla aparece en pestaña "Comparativa" antes de los gráficos
   - Funciona tanto en cálculo directo como en carga desde cache
   - Manejo de errores robusto si faltan datos
   - Formato numérico apropiado (decimales, separadores de miles)

### Estado: ❌ FALLA → 🔧 TESTING PENDIENTE
**Lógica de comparativa CMC completamente reimplementada**
- Usa flujo real de CMC: CalculoObjetosAEA → CalculoMecanicoCables → crear_grafico_flechas
- Elimina lógica falsa que completaba en 0.0s sin cálculo real
- Implementa creación de objetos Cable_AEA con parámetros de viento
- Ejecuta cálculo mecánico real con optimización (FlechaMin/TiroMin)
- Genera gráficos reales usando plot_flechas existente
- Tiempo de cálculo ahora refleja procesamiento real
- Corregidos errores de cables no encontrados y format strings
- **NUEVA**: Tabla comparativa con propiedades y resultados de cables

### Verificación Requerida:
- [ ] Probar "Calcular Comparativa" con cable 'Catbird' (debe encontrarse)
- [ ] Verificar que no aparecen errores de format string
- [ ] Confirmar tiempo de cálculo real (>0.1s por cable)
- [ ] Verificar que se ejecuta optimización mecánica real
- [ ] Confirmar que gráficos muestran datos calculados, no simulados
- [ ] **NUEVA**: Verificar que tabla comparativa aparece en pestaña "Comparativa"
- [ ] **NUEVA**: Confirmar que tabla muestra propiedades correctas de cada cable
- [ ] **NUEVA**: Verificar que resultados calculados (flecha/tiro máx) son correctos
- [x] **CORREGIDO**: Coeficiente dilatación ahora muestra valores correctos (era campo incorrecto)
- [x] **VERIFICADO**: Módulo elasticidad valores son correctos (6900-8000 daN/mm² típicos para Al/Ac)

**SOLO EL USUARIO PUEDE MARCAR COMO ✅ RESUELTO DESPUÉS DE TESTING EXITOSO**

## Notas Técnicas

### Lógica Implementada
La vista CC ahora:
1. Usa `ejecutar_comparativa_cmc()` que crea estructura temporal por cable
2. Ejecuta `ejecutar_cmc_real_para_cable()` usando lógica CMC completa
3. Genera gráficos con `crear_grafico_flechas()` (función existente y probada)
4. Crea gráfico comparativo con datos reales extraídos del DataFrame
5. **NUEVA**: Genera tabla comparativa con propiedades y resultados

### Tabla Comparativa
- **Fuente de datos**: `cables.json` para propiedades, DataFrames para resultados
- **Estructura**: Primera columna "Valores/Cable", columnas por cable
- **Propiedades mostradas**: Sección, diámetro, peso, rotura, elasticidad, dilatación
- **Resultados mostrados**: Flecha máxima, tiro máximo (de todos los estados)
- **Formato**: Bootstrap table responsive con hover y striped

### Integración con CMC
- Reutiliza `CalculoObjetosAEA` y `CalculoMecanicoCables`
- Usa mismos parámetros y restricciones que CMC normal
- Genera DataFrames con mismo formato que CMC individual
- Mantiene compatibilidad con cache y persistencia
- **NUEVA**: Tabla comparativa integrada en pestaña principal

### Próximos Pasos
Una vez confirmado el funcionamiento:
1. Optimizar performance para múltiples cables
2. Agregar más opciones de comparación (porcentaje rotura, etc.)
3. Mejorar UI con filtros y opciones de visualización
4. **NUEVA**: Considerar exportar tabla comparativa a Excel/CSV