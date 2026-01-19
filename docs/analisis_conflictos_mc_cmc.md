# Análisis de Conflictos - Memoria de Cálculo CMC

## Resumen Ejecutivo

**ESTADO**: ✅ **NO HAY CONFLICTOS CRÍTICOS**

La implementación propuesta de `gen_memoria_calculo_CMC()` es compatible con la arquitectura actual. Los parámetros necesarios están disponibles en el flujo de ejecución.

---

## Parámetros Requeridos por `gen_memoria_calculo_CMC()`

```python
def gen_memoria_calculo_CMC(
    cable_aea,              # Objeto Cable_AEA
    vano,                   # float
    estados_climaticos,     # dict
    parametros_viento,      # dict
    restricciones,          # dict
    objetivo,               # str: 'FlechaMin' o 'TiroMin'
    resultados_finales,     # dict
    t_final,                # float
    q0_final,               # float
    estado_limitante        # str
):
```

---

## Análisis de Disponibilidad de Parámetros

### ✅ Parámetros Disponibles en `calculo_mecanico()`

| Parámetro | Fuente | Disponibilidad |
|-----------|--------|----------------|
| `cable_aea` | `self` | ✅ Disponible (objeto Cable_AEA) |
| `vano` | Argumento `vano` | ✅ Disponible |
| `estados_climaticos` | Argumento `estados_climaticos` | ✅ Disponible |
| `parametros_viento` | Argumento `parametros_viento` | ✅ Disponible |
| `restricciones` | Argumento `restricciones` | ✅ Disponible |
| `objetivo` | Argumento `objetivo` | ✅ Disponible |
| `resultados_finales` | Variable `resultados_final` | ✅ Disponible |
| `t_final` | Variable `t_final` | ✅ Disponible |
| `q0_final` | Variable `q0_final` | ✅ Disponible |
| `estado_limitante` | Variable `estado_limitante` | ✅ Disponible |

### 📋 Estructura de Parámetros

#### `parametros_viento` (dict)
```python
{
    "exposicion": "C",      # str: "B", "C", "D"
    "clase": "C",           # str: "B", "BB", "C", "D", "E"
    "Zc": 13.0,            # float: Altura efectiva
    "Cf": 1.0,             # float: Coeficiente de fuerza
    "L_vano": 400.0        # float: Longitud de vano
}
```

#### `restricciones` (dict)
```python
{
    "tension_max_porcentaje": {
        "I": 0.25,
        "II": 0.40,
        "III": 0.40,
        "IV": 0.40,
        "V": 0.25
    },
    "relflecha_max": 0.9  # Solo para guardia
}
```

#### `estados_climaticos` (dict)
```python
{
    "I": {
        "temperatura": 35,
        "descripcion": "Tmáx",
        "viento_velocidad": 0,
        "espesor_hielo": 0
    },
    "II": {...},
    ...
}
```

---

## Flujo de Ejecución Actual

### 1. Llamada desde `calculo_controller.py`

```python
# controllers/calculo_controller.py (línea ~180)
resultado = state.calculo_mecanico.calcular(params, estados_climaticos, restricciones_dict)
```

### 2. Ejecución en `calculo_mecanico_cables.py`

```python
# utils/calculo_mecanico_cables.py (línea ~50)
self.df_conductor, self.resultados_conductor, estado_limitante_cond = \
    self.calculo_objetos.cable_conductor.calculo_mecanico(
        vano=L_vano,
        estados_climaticos=estados_climaticos,
        parametros_viento=parametros_viento,
        restricciones=restricciones["conductor"],
        objetivo=OBJ_CONDUCTOR,
        es_guardia=False,
        flecha_max_permitida=3.0,
        salto_porcentual=SALTO_PORCENTUAL,  # ⚠️ IGNORADO
        paso_afinado=PASO_AFINADO,          # ⚠️ IGNORADO
        relflecha_sin_viento=RELFLECHA_SIN_VIENTO
    )
```

### 3. Método `calculo_mecanico()` en `CalculoCables.py`

```python
# CalculoCables.py (línea ~650)
def calculo_mecanico(self, vano, estados_climaticos, parametros_viento, 
                    restricciones=None, objetivo='FlechaMin', es_guardia=False,
                    resultados_conductor=None, flecha_max_permitida=None,
                    relflecha_sin_viento=True, **kwargs):
    
    # ... cálculos ...
    
    # PUNTO DE INSERCIÓN PROPUESTO:
    # Al final del método, antes del return
    
    # ✅ TODOS LOS PARÁMETROS DISPONIBLES AQUÍ
    memoria_calculo = gen_memoria_calculo_CMC(
        cable_aea=self,
        vano=vano,
        estados_climaticos=estados_climaticos,
        parametros_viento=parametros_viento,
        restricciones=restricciones,
        objetivo=objetivo,
        resultados_finales=resultados_final,
        t_final=t_final,
        q0_final=q0_final,
        estado_limitante=estado_limitante
    )
    
    return df_resultados[columnas_base], resultados_final, estado_limitante, memoria_calculo
```

---

## ⚠️ Advertencias y Consideraciones

### 1. Parámetros Ignorados (No Afectan MC)

Los siguientes parámetros se pasan pero NO se usan en el algoritmo:
- `salto_porcentual` → Algoritmo usa valores fijos (1%, 0.1%, 0.01%)
- `paso_afinado` → Algoritmo usa valores fijos

**Impacto en MC**: ✅ Ninguno - La memoria documenta el algoritmo real usado.

### 2. Cambio en Firma del Método

**ANTES**:
```python
return df_resultados[columnas_base], resultados_final, estado_limitante
```

**DESPUÉS**:
```python
return df_resultados[columnas_base], resultados_final, estado_limitante, memoria_calculo
```

**Impacto**: ⚠️ Requiere actualizar TODOS los callers:
- `utils/calculo_mecanico_cables.py` (3 llamadas)
- Cualquier otro código que llame directamente a `calculo_mecanico()`

### 3. Almacenamiento en Cache

**Actualizar**: `utils/calculo_cache.py`

```python
def guardar_calculo_cmc(nombre, estructura_data, resultados_conductor, 
                       resultados_guardia1, df_cargas_totales, 
                       fig_combinado, fig_conductor, fig_guardia1,
                       resultados_guardia2=None, console_output=None,
                       df_conductor_html=None, df_guardia1_html=None, 
                       df_guardia2_html=None,
                       memoria_conductor=None,      # ✅ NUEVO
                       memoria_guardia1=None,       # ✅ NUEVO
                       memoria_guardia2=None):      # ✅ NUEVO
```

---

## 📝 Plan de Implementación Seguro

### Fase 1: Crear Función MC (Sin Integrar)

1. Crear `utils/memoria_calculo_cmc.py`
2. Implementar `gen_memoria_calculo_CMC()`
3. Implementar funciones auxiliares
4. **NO modificar** `CalculoCables.py` todavía

### Fase 2: Testing Aislado

```python
# Script de prueba independiente
from CalculoCables import Cable_AEA
from utils.memoria_calculo_cmc import gen_memoria_calculo_CMC

# Crear cable de prueba
cable = Cable_AEA(...)

# Ejecutar cálculo
df, resultados, estado_lim = cable.calculo_mecanico(...)

# Generar memoria (llamada externa)
memoria = gen_memoria_calculo_CMC(
    cable_aea=cable,
    vano=400.0,
    estados_climaticos={...},
    parametros_viento={...},
    restricciones={...},
    objetivo='FlechaMin',
    resultados_finales=resultados,
    t_final=5.58,
    q0_final=-20,
    estado_limitante="II"
)

print(memoria)
```

### Fase 3: Integración Gradual

1. **Modificar `CalculoCables.py`**:
   - Agregar generación de memoria
   - Cambiar return para incluir memoria

2. **Actualizar `calculo_mecanico_cables.py`**:
   ```python
   # ANTES
   self.df_conductor, self.resultados_conductor, estado_limitante_cond = \
       cable.calculo_mecanico(...)
   
   # DESPUÉS
   self.df_conductor, self.resultados_conductor, estado_limitante_cond, memoria_cond = \
       cable.calculo_mecanico(...)
   
   # Guardar memoria
   self.memoria_conductor = memoria_cond
   ```

3. **Actualizar `calculo_cache.py`**:
   - Agregar campos de memoria en `guardar_calculo_cmc()`
   - Agregar campos de memoria en `cargar_calculo_cmc()`

4. **Actualizar vistas**:
   - Mostrar memoria en `vista_calculo_mecanico.py`
   - Agregar botón "Ver Memoria de Cálculo"

---

## 🔍 Validación de Parámetros Internos

### Parámetros Calculados Internamente (Disponibles para MC)

| Parámetro | Cálculo | Línea en CalculoCables.py |
|-----------|---------|---------------------------|
| `t_inicial` | `0.01 * carga_rotura / seccion` (FlechaMin) | ~550 |
| `paso_inicial` | `0.01` (1% de rotura) | ~553 |
| `t_valida` | Última tensión válida de búsqueda | ~560 |
| `t_violadora` | Primera tensión que viola restricción | ~580 |
| `A`, `B` | Coeficientes ecuación cúbica | ~350 |
| `Go` | Carga estado básico | ~345 |
| `G` | Carga vectorial por estado | ~330 |

**Todos estos valores están disponibles en el contexto de ejecución** y pueden documentarse en la memoria.

---

## ✅ Conclusión

### No Hay Conflictos Críticos

1. ✅ Todos los parámetros requeridos están disponibles
2. ✅ El flujo de ejecución permite la integración
3. ✅ No hay dependencias circulares
4. ⚠️ Requiere actualizar callers (cambio controlado)

### Recomendaciones

1. **Implementar en fases** (crear → probar → integrar)
2. **Mantener compatibilidad** con código existente durante transición
3. **Documentar cambios** en firma del método
4. **Agregar tests** para validar memoria generada

### Riesgo: BAJO ✅

La implementación es segura y no introduce conflictos arquitectónicos.
