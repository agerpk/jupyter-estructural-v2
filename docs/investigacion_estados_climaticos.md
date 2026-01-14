# Investigación: Estados Climáticos en el Sistema

## Resumen Ejecutivo

Este documento analiza exhaustivamente cómo se utilizan los estados climáticos en todo el sistema AGP, identificando todos los puntos de uso, vínculos con estados específicos, y las implicaciones de añadir nuevos estados climáticos.

---

## 1. Definición de Estados Climáticos

### 1.1 Ubicación de Definición

Los estados climáticos se definen en **dos lugares**:

1. **Archivo de estructura JSON** (`plantilla.estructura.json` y archivos `.estructura.json`):
```json
"estados_climaticos": {
    "I": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, "espesor_hielo": 0},
    "II": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0, "espesor_hielo": 0},
    "III": {"temperatura": 10, "descripcion": "Vmáx", "viento_velocidad": 38.9, "espesor_hielo": 0},
    "IV": {"temperatura": -5, "descripcion": "Vmed", "viento_velocidad": 15.56, "espesor_hielo": 0.01},
    "V": {"temperatura": 8, "descripcion": "TMA", "viento_velocidad": 0, "espesor_hielo": 0}
}
```

2. **Vista de CMC** (`vista_calculo_mecanico.py`): Tabla editable que permite modificar estados.

### 1.2 Estructura de un Estado Climático

Cada estado tiene:
- **ID**: Identificador único (I, II, III, IV, V)
- **temperatura**: Temperatura en °C
- **descripcion**: Descripción legible (Tmáx, Tmín, Vmáx, Vmed, TMA)
- **viento_velocidad**: Velocidad del viento en m/s
- **espesor_hielo**: Espesor del manguito de hielo en metros

---

## 2. Uso de Estados Climáticos en CMC (Cálculo Mecánico de Cables)

### 2.1 Archivo: `CalculoCables.py`

**Función principal**: `calculo_mecanico()`

**Uso**:
- Itera sobre **TODOS** los estados climáticos definidos
- Para cada estado, calcula:
  - Tensión (daN/mm²)
  - Tiro (daN)
  - Flecha vertical (m)
  - Flecha resultante (m)
  - Porcentaje de rotura
  - Carga unitaria (daN/m)

**Código relevante**:
```python
def calculo_mecanico(self, vano, estados_climaticos, parametros_viento, ...):
    # Itera sobre TODOS los estados
    for estado_id, estado_data in estados_climaticos.items():
        resultados[estado_id] = self._calcular_estado(vano, estado_data, t0, q0, parametros_viento)
```

**Implicación**: Si se añaden nuevos estados (VI, VII, etc.), se calcularán automáticamente.

### 2.2 Restricciones por Estado

**Ubicación**: `plantilla.estructura.json`
```json
"restricciones_cables": {
    "conductor": {"I": 0.25, "II": 0.40, "III": 0.40, "IV": 0.40, "V": 0.25},
    "guardia": {"I": 0.7, "II": 0.70, "III": 0.70, "IV": 0.7, "V": 0.7}
}
```

**Uso en `CalculoCables.py`**:
```python
def _verificar_restricciones(self, resultados, restricciones_cable, ...):
    for estado_id, datos in resultados.items():
        tension_max_porcentaje = restricciones_cable.get("tension_max_porcentaje", {}).get(
            estado_id, 0.40  # Valor por defecto si no existe
        )
```

**Implicación**: Si se añade un nuevo estado, debe añadirse su restricción correspondiente.

### 2.3 Estado Básico y Estado de Máxima Tensión

**Método**: `_iterar_estado_basico()`

**Lógica**:
1. Usa el **primer estado** como estado básico inicial
2. Calcula todos los estados
3. Encuentra el estado con **máxima tensión**
4. Si es diferente al estado básico, itera hasta convergencia

**Código**:
```python
estado_basico_1_id = list(estados_climaticos.keys())[0]  # Primer estado
estado_max_tension_id, t_max = self._encontrar_estado_max_tension(resultados_1)
```

**Implicación**: El orden de los estados en el diccionario importa para la convergencia inicial.

---

## 3. Uso de Estados Climáticos en DME (Diseño Mecánico de Estructuras)

### 3.1 Archivo: `EstructuraAEA_Mecanica.py`

**Función principal**: `asignar_cargas_hipotesis()`

**Uso**:
- Las hipótesis de carga **referencian estados específicos** por nombre
- Ejemplo de hipótesis:
```python
"A1": {
    "viento": {"estado": "Vmax", ...},
    "tiro": {"estado": "Vmax", ...}
}
```

**Mapeo de estados**:
```python
self.geometria.ESTADOS_MAPEO = {
    "Tmax": "I",
    "Tmin": "II",
    "Vmax": "III",
    "Vmed": "IV",
    "TMA": "V"
}
```

**Código relevante**:
```python
estado_viento_config = config["viento"]["estado"]  # "Vmax"
estado_viento = self.geometria.ESTADOS_MAPEO.get(estado_viento_config, estado_viento_config)  # "III"
```

**Implicación**: Las hipótesis están **hardcodeadas** para usar estados específicos (I-V).

### 3.2 Hipótesis Maestro

**Archivo**: `HipotesisMaestro_Especial.py`

**Estados referenciados**:
- **TMA** (Estado V): Usado en hipótesis A0, B1
- **Vmax** (Estado III): Usado en hipótesis A1, A2, A3
- **Vmed** (Estado IV): Usado en hipótesis A4, A5, C1
- **Tmin** (Estado II): Usado en hipótesis B2
- **máximo**: Busca el estado con máximo tiro

**Ejemplo**:
```python
"A0": {
    "tiro": {"estado": "TMA", ...}  # Referencia explícita a TMA
}
```

**Implicación**: Si se añade un nuevo estado con mayor flecha/tiro, las hipótesis NO lo usarán automáticamente.

---

## 4. Uso de Estados Climáticos en Gráficos

### 4.1 Archivo: `plot_flechas.py`

**Función**: `crear_grafico_flechas()`

**Uso**:
- Itera sobre **TODOS** los estados en `cable.catenarias_cache`
- Asigna colores específicos a cada estado:
```python
colores_conductor = {
    "I": "#DC143C",    # Rojo oscuro - Tmáx
    "II": "#FF6347",   # Rojo tomate - Tmín
    "III": "#B22222",  # Rojo ladrillo - Vmáx
    "IV": "#CD5C5C",   # Rojo indio - Vmed
    "V": "#F08080"     # Rojo claro - TMA
}
```

**Implicación**: Si se añaden nuevos estados, necesitarán colores definidos.

### 4.2 Cache de Catenarias

**Método**: `_calcular_y_cachear_catenarias()`

**Uso**:
- Calcula catenarias para **TODOS** los estados en `resultados_finales`
- Almacena en `self.catenarias_cache[estado_id]`

**Implicación**: Nuevos estados se cachearán automáticamente.

---

## 5. Vínculos con Estados Específicos

### 5.1 Vínculos Hardcodeados

**Ubicación**: `HipotesisMaestro_Especial.py`

| Hipótesis | Estado Viento | Estado Tiro | Descripción |
|-----------|---------------|-------------|-------------|
| A0 | - | TMA (V) | Estado de diseño |
| A1 | Vmax (III) | Vmax (III) | Viento máximo transversal |
| A2 | Vmax (III) | Vmax (III) | Viento máximo longitudinal |
| A3 | Vmax (III) | Vmax (III) | Viento máximo oblicuo |
| A4 | Vmed (IV) | Vmed (IV) | Viento medio + hielo |
| A5 | - | Vmed (IV) | Tiro unilateral reducido |
| B1 | - | TMA (V) | Sobrecarga construcción |
| B2 | - | Tmin (II) | Pesos x 2.5 unilateral |
| C1 | - | Vmed (IV) o TMA (V) | Carga longitudinal |

**Implicación**: Estas hipótesis NO se adaptarán automáticamente a nuevos estados.

### 5.2 Vínculos Dinámicos

**Estado "máximo"**: Busca el estado con máxima tensión entre todos los disponibles.

```python
if estado_tiro == "máximo":
    tiro_cond_base = max([d["tiro_daN"] for d in resultados_conductor.values()])
```

**Implicación**: Si un nuevo estado tiene mayor tiro, será usado automáticamente.

---

## 6. Búsqueda de Máximos y Mínimos

### 6.1 Búsqueda de Estado con Máxima Tensión

**Método**: `_encontrar_estado_max_tension()`

```python
def _encontrar_estado_max_tension(self, resultados):
    estado_max = None
    t_max = 0
    for estado_id, datos in resultados.items():
        t_actual = datos["tension_daN_mm2"]
        if t_actual > t_max:
            t_max = t_actual
            estado_max = estado_id
    return estado_max, t_max
```

**Implicación**: Busca entre **TODOS** los estados disponibles.

### 6.2 Búsqueda de Máxima Flecha

**Ubicación**: `calculo_mecanico_cables.py`

```python
flecha_max_conductor = max([r["flecha_vertical_m"] for r in self.resultados_conductor.values()])
```

**Implicación**: Busca entre **TODOS** los estados disponibles.

### 6.3 Estado Limitante

**Método**: `_verificar_restricciones()`

Identifica el estado que viola restricciones:
```python
if T_actual > T_max_permitida:
    estado_violador = estado_id
    tipo_violacion = "tension"
```

**Implicación**: Cualquier estado puede ser limitante.

---

## 7. Impacto de Añadir Nuevos Estados

### 7.1 Cambios Automáticos (Sin Modificación de Código)

✅ **CMC**: Nuevos estados se calcularán automáticamente
✅ **Catenarias**: Se cachearán automáticamente
✅ **Búsqueda de máximos**: Incluirá nuevos estados
✅ **Gráficos de flechas**: Mostrará nuevos estados (con color por defecto)

### 7.2 Cambios Manuales Requeridos

❌ **Restricciones**: Añadir restricciones para nuevos estados en JSON
❌ **Colores de gráficos**: Definir colores en `plot_flechas.py`
❌ **Hipótesis**: Actualizar `HipotesisMaestro_Especial.py` si se quiere usar nuevos estados
❌ **Mapeo de estados**: Actualizar `ESTADOS_MAPEO` si se usan nombres descriptivos

### 7.3 Ejemplo: Añadir Estado VI (Tormenta)

**Paso 1**: Añadir en JSON
```json
"estados_climaticos": {
    ...
    "VI": {"temperatura": 15, "descripcion": "Tormenta", "viento_velocidad": 20.0, "espesor_hielo": 0}
}
```

**Paso 2**: Añadir restricciones
```json
"restricciones_cables": {
    "conductor": {..., "VI": 0.35},
    "guardia": {..., "VI": 0.65}
}
```

**Paso 3**: Añadir color en `plot_flechas.py`
```python
colores_conductor = {
    ...
    "VI": "#FFA500"  # Naranja - Tormenta
}
```

**Paso 4** (Opcional): Añadir hipótesis en `HipotesisMaestro_Especial.py`
```python
"A6": {
    "desc": "Tormenta",
    "viento": {"estado": "Tormenta", "direccion": "Transversal", "factor": 1.0},
    "tiro": {"estado": "Tormenta", "patron": "bilateral", ...},
    ...
}
```

**Paso 5** (Opcional): Añadir mapeo
```python
ESTADOS_MAPEO = {
    ...
    "Tormenta": "VI"
}
```

---

## 8. Casos Especiales

### 8.1 Estado con Mayor Flecha Vertical

**Escenario**: Añadir estado con temperatura muy alta (50°C) que genere mayor flecha.

**Comportamiento**:
- CMC calculará automáticamente
- Búsqueda de máxima flecha lo detectará
- Para guardia con objetivo TiroMin, podría convertirse en limitante
- Gráficos lo mostrarán

**Código relevante**:
```python
flecha_max_conductor = max([r["flecha_vertical_m"] for r in self.resultados_conductor.values()])
flecha_max_guardia = flecha_max_conductor * RELFLECHA_MAX_GUARDIA
```

### 8.2 Estado con Mayor Tiro

**Escenario**: Añadir estado con temperatura muy baja (-30°C) que genere mayor tiro.

**Comportamiento**:
- CMC calculará automáticamente
- Búsqueda de máxima tensión lo detectará
- Podría convertirse en estado básico en iteración
- Hipótesis con `estado: "máximo"` lo usarán automáticamente

**Código relevante**:
```python
if estado_tiro == "máximo":
    tiro_cond_base = max([d["tiro_daN"] for d in resultados_conductor.values()])
```

### 8.3 Estado con Mayor Flecha Total (Resultante)

**Escenario**: Añadir estado con viento + hielo que genere mayor flecha resultante.

**Comportamiento**:
- CMC calculará automáticamente
- Flecha resultante se calcula como: `flecha_resultante = (G * L²) / (8 * T)`
- Donde `G = sqrt(peso_total² + carga_viento²)`
- Gráficos mostrarán ambas flechas (vertical y resultante)

---

## 9. Limitaciones Actuales

### 9.1 Número Fijo de Estados en UI

**Vista CMC**: Tabla hardcodeada para 5 estados (I-V)

**Código**:
```python
estados_default = {
    "I": {...},
    "II": {...},
    "III": {...},
    "IV": {...},
    "V": {...}
}
```

**Limitación**: No hay UI para añadir/eliminar estados dinámicamente.

### 9.2 Colores Hardcodeados

**Archivo**: `plot_flechas.py`

**Limitación**: Solo hay colores definidos para 5 estados.

### 9.3 Hipótesis Hardcodeadas

**Archivo**: `HipotesisMaestro_Especial.py`

**Limitación**: Hipótesis referencian estados específicos por nombre.

---

## 10. Recomendaciones para Implementar Sistema Extensible

### 10.1 Arquitectura Propuesta

**Opción 1: Estados Dinámicos con Validación**
```python
def validar_estados_climaticos(estados):
    """Valida que todos los estados tengan campos requeridos"""
    campos_requeridos = ["temperatura", "descripcion", "viento_velocidad", "espesor_hielo"]
    for estado_id, datos in estados.items():
        for campo in campos_requeridos:
            if campo not in datos:
                raise ValueError(f"Estado {estado_id} falta campo {campo}")
```

**Opción 2: Restricciones con Valores por Defecto**
```python
def obtener_restriccion_estado(restricciones, estado_id, tipo_cable):
    """Obtiene restricción con fallback a valor por defecto"""
    return restricciones.get(tipo_cable, {}).get(estado_id, 0.40)
```

**Opción 3: Colores Generados Automáticamente**
```python
def generar_color_estado(estado_id, total_estados):
    """Genera color usando escala de colores"""
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    
    idx = list(estados.keys()).index(estado_id)
    cmap = cm.get_cmap('viridis', total_estados)
    return mcolors.to_hex(cmap(idx))
```

### 10.2 UI Dinámica para Estados

**Propuesta**: Añadir botones "Añadir Estado" / "Eliminar Estado" en vista CMC.

**Funcionalidad**:
- Generar filas dinámicamente según estados en JSON
- Validar que al menos existan 3 estados (mínimo para cálculos)
- Asignar IDs automáticamente (VI, VII, VIII, ...)

### 10.3 Hipótesis Flexibles

**Propuesta**: Permitir seleccionar estado desde dropdown en editor de hipótesis.

**Ejemplo**:
```python
"A1": {
    "viento": {"estado": "III", ...},  # Dropdown con todos los estados disponibles
    "tiro": {"estado": "III", ...}
}
```

---

## 11. Conclusiones

### 11.1 Flexibilidad Actual

✅ **CMC es completamente flexible**: Calcula cualquier número de estados
✅ **Búsquedas de máximos/mínimos son dinámicas**: Funcionan con cualquier número de estados
✅ **Cache es extensible**: Almacena todos los estados calculados

### 11.2 Puntos Rígidos

❌ **UI limitada a 5 estados**: Tabla hardcodeada
❌ **Hipótesis hardcodeadas**: Referencian estados específicos
❌ **Colores hardcodeados**: Solo 5 colores definidos
❌ **Restricciones deben añadirse manualmente**: No hay valores por defecto inteligentes

### 11.3 Viabilidad de Extensión

**Añadir nuevos estados es VIABLE** con modificaciones menores:
1. Actualizar UI para generar tabla dinámicamente
2. Implementar generación automática de colores
3. Añadir validación de restricciones con valores por defecto
4. Permitir selección de estados en editor de hipótesis

**Esfuerzo estimado**: 2-3 días de desarrollo

---

## 12. Casos de Uso Específicos

### 12.1 Estado con Mayor Flecha Vertical que V

**Ejemplo**: Estado VII con temperatura 45°C

**Comportamiento esperado**:
- CMC calculará flecha mayor que estado V
- Si objetivo es FlechaMin, podría no afectar (ya está en máxima tensión)
- Si objetivo es TiroMin, podría convertirse en limitante para guardia
- Gráficos mostrarán la curva más pronunciada

### 12.2 Estado con Mayor Tiro que II

**Ejemplo**: Estado VIII con temperatura -30°C

**Comportamiento esperado**:
- CMC calculará tiro mayor que estado II
- Podría convertirse en estado básico en iteración
- Hipótesis con `estado: "máximo"` lo usarán automáticamente
- Podría violar restricciones de tensión máxima

### 12.3 Estado con Mayor Flecha Total (Viento + Hielo)

**Ejemplo**: Estado IX con viento 25 m/s + hielo 0.02m

**Comportamiento esperado**:
- Flecha resultante será mayor que flecha vertical
- Importante para verificación de distancias de seguridad
- Gráficos mostrarán ambas flechas claramente diferenciadas

---

## Anexo A: Archivos Involucrados

| Archivo | Función | Uso de Estados |
|---------|---------|----------------|
| `CalculoCables.py` | Cálculo mecánico | Itera sobre todos |
| `calculo_mecanico_cables.py` | Orquestación CMC | Pasa estados a Cable_AEA |
| `EstructuraAEA_Mecanica.py` | Asignación de cargas | Referencia estados específicos |
| `HipotesisMaestro_Especial.py` | Definición de hipótesis | Hardcodea estados |
| `plot_flechas.py` | Gráficos de flechas | Asigna colores por estado |
| `vista_calculo_mecanico.py` | UI de CMC | Tabla de 5 estados |
| `plantilla.estructura.json` | Configuración | Define estados y restricciones |

---

## Anexo B: Flujo de Datos de Estados Climáticos

```
plantilla.estructura.json
    ↓
estructura_actual["estados_climaticos"]
    ↓
vista_calculo_mecanico.py (UI editable)
    ↓
calculo_mecanico_cables.py
    ↓
Cable_AEA.calculo_mecanico()
    ↓
_calcular_estado() para cada estado
    ↓
resultados_finales[estado_id]
    ↓
DataFrame con columnas por estado
    ↓
Gráficos con curvas por estado
```

---

**Fecha**: 2024-01-15
**Versión**: 1.0
**Autor**: Amazon Q
