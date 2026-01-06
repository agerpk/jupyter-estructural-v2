# Vano Económico - Implementación Actualizada

## Resumen

Funcionalidad implementada para analizar el costo total de una familia de estructuras en función del vano, con **cálculo dinámico de cantidades** de estructuras según longitud de traza y criterios configurables.

## NUEVAS DIRECTIVAS IMPLEMENTADAS ✅

### Cálculo Dinámico de Cantidades

#### Validación de Familia
La familia DEBE contener:
- **1 estructura** tipo Suspensión Recta (S)
- **1 estructura** tipo Retención / Ret. Angular con alpha=0 (RR)
- **N estructuras** tipo Retención / Ret. Angular con alpha>0 (RA) - opcional
- **1 estructura** tipo Terminal (T)

Si hay múltiples estructuras del mismo tipo → **Error con mensaje específico**

#### Inputs Adicionales
- `LONGTRAZA` (m) - ENTERO - Longitud total de la traza
- `CRITERIO_RR` - SELECT: "Distancia" / "Suspensiones" / "Manual"
- `cant_RR_manual` - ENTERO - Solo si CRITERIO_RR = "Manual"
- `RR_CADA_X_M` - FLOAT - Retención cada X metros
- `RR_CADA_X_S` - ENTERO - Retención cada X suspensiones

#### Cantidades Calculadas (por iteración)
```python
# Fijas
cant_T = 2  # Siempre 2 terminales

# Desde familia
cant_RA = suma de cantidades de estructuras con alpha>0

# Dinámicas (dependen de L_vano)
cant_S = math.ceil(LONGTRAZA / L_vano)  # roundup

# Según criterio
if CRITERIO_RR == "Distancia":
    cant_RR = math.ceil(LONGTRAZA / RR_CADA_X_M) - 1 - cant_RA
elif CRITERIO_RR == "Suspensiones":
    cant_RR = math.ceil(cant_S / RR_CADA_X_S) - cant_RA
elif CRITERIO_RR == "Manual":
    cant_RR = cant_RR_manual
```

## Archivos Creados/Modificados

### 1. Vista - `components/vista_vano_economico.py`
✅ Controles de vano (mín, máx, salto)
✅ Controles de cantidades (LONGTRAZA, CRITERIO_RR, etc.)
✅ Display de cantidades calculadas (ejemplo con vano medio)
✅ Selector de familia activa
✅ Botones: Calcular y Cargar Cache
✅ Barra de progreso
✅ Área de resultados

### 2. Utilidades - `utils/vano_economico_utils.py`
✅ `validar_familia_vano_economico()` - Valida estructura de familia
✅ `calcular_cantidades()` - Calcula cant_T, cant_S, cant_RR, cant_RA
✅ `obtener_cant_ra_familia()` - Extrae cant_RA de familia
✅ `modificar_vano_y_cantidades_familia()` - Modifica L_vano y Cantidad
✅ `calcular_vano_economico_iterativo()` - REUTILIZA `ejecutar_calculo_familia_completa()`
✅ `generar_grafico_curva_vano_economico()` - Curva con vano óptimo
✅ `generar_grafico_barras_apiladas()` - Distribución por estructura
✅ `generar_vista_resultados_vano_economico()` - Vista completa con botón Descargar HTML

### 3. Controller - `controllers/vano_economico_controller.py`
✅ `cargar_opciones_familias()` - Carga familias disponibles
✅ `cargar_familia_seleccionada()` - Actualiza familia activa
✅ `toggle_manual_rr()` - Habilita/deshabilita input manual
✅ `actualizar_display_cantidades()` - Muestra cantidades con vano medio
✅ `calcular_vano_economico()` - Ejecuta cálculo iterativo con nuevos parámetros
✅ `cargar_cache_vano_economico()` - Carga resultados desde cache

### 4. Cache - `utils/calculo_cache.py`
✅ `guardar_calculo_vano_economico()` - Guarda resultados con nuevos parámetros
✅ `cargar_calculo_vano_economico()` - Carga resultados

## Funcionalidad Implementada

### Reutilización de Código
✅ Usa `ejecutar_calculo_familia_completa()` existente
✅ Modifica `L_vano` y `Cantidad` en cada iteración
✅ No duplica lógica de cálculo encadenado

### IDs Únicos
✅ Prefijo `vano-economico-` en todos los componentes
✅ Sin conflictos con vista familia

### Cálculo Iterativo
✅ Validación de familia antes de calcular
✅ Cálculo dinámico de cantidades por vano
✅ Modificación de campo `Cantidad` según tipo de estructura
✅ Identificación automática de vano óptimo
✅ Captura de cantidades por vano

### Visualización
✅ Curva de vano económico con vano óptimo marcado
✅ Gráfico de barras apiladas por estructura
✅ Tabla de resultados con cantidades (S, RR) y diferencias porcentuales
✅ Resumen con métricas clave
✅ Botón "Descargar HTML" (pendiente implementar callback)

### Cache
✅ Persistencia de resultados con nuevos parámetros
✅ Carga desde cache

## Flujo de Uso

1. **Seleccionar Familia**: Cargar familia existente o usar familia activa
2. **Configurar Vanos**: Definir vano mínimo, máximo y salto
3. **Configurar Cantidades**: 
   - Ingresar LONGTRAZA
   - Seleccionar CRITERIO_RR
   - Configurar parámetros según criterio
4. **Ver Preview**: Cantidades calculadas con vano medio
5. **Calcular**: Ejecutar cálculo iterativo
6. **Visualizar**: Ver curva, gráficos y tabla de resultados
7. **Descargar**: Exportar HTML con resultados completos
8. **Cache**: Guardar/cargar resultados para análisis posterior

## Ejemplo de Uso

```python
# Configuración
vano_min = 300  # m
vano_max = 500  # m
salto = 50      # m
longtraza = 10000  # m
criterio_rr = "Distancia"
rr_cada_x_m = 2000  # m

# Genera vanos: [300, 350, 400, 450, 500]
# Para cada vano:
#   - Calcula cant_S = ceil(10000 / vano)
#   - Calcula cant_RR = ceil(10000 / 2000) - 1 - cant_RA
#   - Modifica L_vano y Cantidad en todas las estructuras
#   - Ejecuta cálculo completo (CMC>DGE>DME>SPH>FUND>COSTEO)
#   - Captura costo_global y cantidades
# Identifica vano óptimo (mínimo costo)
# Genera gráficos y tabla
```

## Resultados Generados

### Resumen
- Vano Óptimo [m]
- Costo Óptimo [UM]
- Vanos Analizados

### Gráfico de Curva
- Línea continua con marcadores
- Vano óptimo marcado con estrella verde
- Hover con información detallada

### Gráfico de Barras Apiladas
- Distribución de costos por estructura
- Comparación entre vanos
- Colores por estructura

### Tabla de Resultados
- Vano [m]
- Cant. S (Suspensiones)
- Cant. RR (Retenciones)
- Costo Total [UM]
- Diferencia vs Óptimo [%]
- Vano óptimo resaltado en verde

### Botón Descargar HTML
- Exporta resultados completos
- Incluye tabla de familia
- Incluye ajustes de vano y cantidades
- Incluye gráficos

## Pendiente

### Callback Descargar HTML
- [ ] Implementar callback en controller
- [ ] Generar HTML con todos los resultados
- [ ] Incluir tabla de familia
- [ ] Incluir parámetros de configuración
- [ ] Incluir gráficos embebidos

## Notas Técnicas

### Validación de Familia
- Verifica estructura antes de calcular
- Mensaje de error específico si falla validación
- Cuenta estructuras por tipo y alpha

### Cálculo de Cantidades
- `cant_T` siempre 2 (fijo)
- `cant_RA` extraído de familia (suma de RA con alpha>0)
- `cant_S` dinámico según vano (roundup)
- `cant_RR` según criterio seleccionado
- Validación: cant_RR no negativo

### Modificación de Estructuras
- Terminal → `Cantidad = cant_T`
- Suspensión → `Cantidad = cant_S`
- RR (alpha=0) → `Cantidad = cant_RR`
- RA (alpha>0) → Mantiene cantidad original

### Performance
- Cálculo iterativo puede tomar tiempo
- Barra de progreso muestra avance
- Cache permite análisis rápido posterior
- Console output detallado por vano

## Testing

1. ✅ Cargar familia con 1S, 1RR, 1T (mínimo)
2. ✅ Configurar vanos: min=300, max=500, salto=50
3. ✅ Configurar LONGTRAZA=10000
4. ✅ Seleccionar criterio "Distancia" con RR_CADA_X_M=2000
5. ✅ Verificar preview de cantidades
6. ✅ Ejecutar cálculo
7. ✅ Verificar gráficos se generan
8. ✅ Verificar tabla incluye cantidades
9. ✅ Verificar vano óptimo identificado
10. ✅ Verificar cache funciona
11. [ ] Verificar descargar HTML funciona

## Estado

🟢 **IMPLEMENTACIÓN COMPLETA**
🟢 **PERSISTENCIA DE AJUSTES IMPLEMENTADA**
🟡 **DESCARGAR HTML PENDIENTE**

Todas las nuevas directivas de cálculo dinámico de cantidades están implementadas.
Los ajustes persisten entre reinicios de la aplicación.

## Notas Finales

### Persistencia de Ajustes
- Los ajustes se guardan en `data/familia_state.json`
- Se cargan automáticamente al entrar a la vista
- Botón "Confirmar Ajustes" guarda todos los valores
- Los valores persisten entre reinicios de la app

### Problema Resuelto: Input Salto
- ID cambiado de `vano-economico-input-salto` a `vano-economico-salto`
- Estructura simplificada del input
- Persistencia implementada correctamente
