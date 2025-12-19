# Rotación de Cargas Puntuales Asociadas a un Cable en un Nodo

## Objetivo

Implementar la capacidad de rotar las cargas de **tiro** y **viento** asociadas a un cable en un nodo específico, sin rotar todo el nodo ni su posición espacial. Esto permite modelar cables que entran a un nodo con una dirección diferente a la estándar.

## Caso de Uso

**Ejemplo**: Nodo `C1A` con `rotacion_eje_z: 270°`
- El cable entra perpendicular a su dirección original (rotado 90° en sentido horario)
- Las cargas de **tiro** deben rotarse 270° en el plano XY
- Las cargas de **viento** deben recalcularse con el nuevo ángulo relativo del cable respecto al viento
- Las cargas de **peso** NO se ven afectadas (dirección Z, rotación en Z)

---

## Análisis del Sistema Actual

### 1. Cálculo de Cargas de Tiro

**Archivo**: `EstructuraAEA_Mecanica.py` línea ~360

```python
# Tiro se calcula en función del ángulo de quiebre (alpha)
tiro_trans, tiro_long = self._calcular_componentes_tiro(
    tiro_base, self.geometria.alpha_quiebre, reduccion, es_guardia
)

# Componentes:
tiro_x = tiro_trans  # Componente transversal (perpendicular al eje del cable)
tiro_y = tiro_long   # Componente longitudinal (paralelo al eje del cable)
tiro_z = 0.0         # Sin componente vertical
```

**Fórmula actual**:
```python
ang_rad = math.radians(angulo_grados / 2)
factor_trans = 2.0 * math.sin(ang_rad)
factor_long = 2.0 * math.cos(ang_rad)
tiro_trans = factor_trans * tiro
tiro_long = factor_long * tiro
```

**Sistema de referencia**: 
- X = transversal (perpendicular al cable)
- Y = longitudinal (paralelo al cable)
- Z = vertical

### 2. Cálculo de Cargas de Viento

**Archivo**: `CalculoCables.py` línea ~200

```python
def cargaViento(self, V, phi_rel_deg=90, ...):
    # phi_rel_deg: Ángulo entre viento y eje del conductor
    # 90° = viento perpendicular al cable (máximo)
    # 0° = viento paralelo al cable (mínimo)
    
    ang_factor = math.sin(math.radians(phi_rel_deg))
    Fu_N_per_m = Q * (Zp * V)**2 * Fc * G * Cf * d_eff * ang_factor
```

**Actualmente en DME** (`EstructuraAEA_Mecanica.py` línea ~400):
```python
# Viento transversal: phi_rel = 90° (perpendicular)
if direccion_viento == "Transversal":
    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "Vc")
    viento_x += viento_cond * factor_viento * factor_viento_nodo

# Viento longitudinal: phi_rel = 0° (paralelo)
elif direccion_viento == "Longitudinal":
    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "VcL")
    viento_y += viento_cond * factor_viento * factor_viento_nodo

# Viento oblicuo: phi_rel = 45°
elif direccion_viento == "Oblicua":
    viento_cond_x = self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_t_1")
    viento_cond_y = self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_l_1")
```

**Problema**: Los códigos de viento (`Vc`, `VcL`, `Vc_o_t_1`) se calculan en CMC con `phi_rel` fijo (90°, 0°, 45°). Si el cable está rotado, el ángulo relativo cambia.

---

## Solución Correcta: Rotar Solo las Cargas del Cable

### Concepto Físico

**Cable sin rotar** (dirección Y estándar):
- Viento transversal (dirección X) → `phi_rel = 90°` → máxima carga
- Viento longitudinal (dirección Y) → `phi_rel = 0°` → mínima carga
- Tiro: componentes en X (transversal) e Y (longitudinal)

**Cable rotado 270° en Z** (dirección X):
- Viento transversal (dirección X) → `phi_rel = 0°` → mínima carga (paralelo al cable)
- Viento longitudinal (dirección Y) → `phi_rel = 90°` → máxima carga (perpendicular al cable)
- Tiro: componentes rotadas en plano XY

### Fase 1: Rotar Tiro del Cable

**Modificación en `EstructuraAEA_Mecanica.py`** después de calcular tiro:

```python
# Calcular tiro en sistema local del cable (sin rotar)
tiro_x = tiro_trans  # Transversal al cable
tiro_y = tiro_long   # Longitudinal al cable
tiro_z = 0.0

# NUEVO: Rotar tiro si el cable tiene rotacion_eje_z
nodo_obj = self.geometria.nodos.get(nodo_nombre)
if nodo_obj and nodo_obj.rotacion_eje_z != 0:
    rz = math.radians(nodo_obj.rotacion_eje_z)
    tiro_x_rot = tiro_x * math.cos(rz) - tiro_y * math.sin(rz)
    tiro_y_rot = tiro_x * math.sin(rz) + tiro_y * math.cos(rz)
    tiro_x, tiro_y = tiro_x_rot, tiro_y_rot
```

### Fase 2: Recalcular Viento con Ángulo Relativo Ajustado

**Problema**: El viento se calcula en CMC con ángulos fijos. Necesitamos recalcular con el ángulo ajustado.

**Cálculo correcto del ángulo relativo**:

```python
# VIENTO EN CABLES - con rotación del cable
nodo_obj = self.geometria.nodos.get(nodo_nombre)

if config["viento"]:
    direccion_viento = config["viento"]["direccion"]
    estado_v = config["viento"]["estado"]
    factor_viento = config["viento"]["factor"]
    
    # Determinar dirección del viento en grados (0° = +X, 90° = +Y)
    if direccion_viento == "Transversal":
        angulo_viento_deg = 0  # Viento en dirección +X
    elif direccion_viento == "Longitudinal":
        angulo_viento_deg = 90  # Viento en dirección +Y
    elif direccion_viento == "Oblicua":
        angulo_viento_deg = 45  # Viento a 45°
    
    # Cable sin rotar está en dirección Y (90°)
    # Cable rotado está en dirección (90° + rotacion_eje_z)
    angulo_cable_deg = 90 + (nodo_obj.rotacion_eje_z if nodo_obj else 0)
    
    # Ángulo relativo = diferencia entre viento y cable
    phi_rel_deg = abs(angulo_viento_deg - angulo_cable_deg)
    
    # Normalizar a [0, 90]
    if phi_rel_deg > 90:
        phi_rel_deg = 180 - phi_rel_deg
    
    # Recalcular viento con ángulo relativo correcto
    if nodo_obj and nodo_obj.cable_asociado and nodo_obj.rotacion_eje_z != 0:
        resultado_viento = nodo_obj.cable_asociado.cargaViento(
            V=viento_velocidad,
            phi_rel_deg=phi_rel_deg,
            exp=parametros_viento["exposicion"],
            clase=parametros_viento["clase"],
            Zc=parametros_viento["Zc"],
            Cf=parametros_viento["Cf"],
            L_vano=vano,
            d_eff=diametro_efectivo
        )
        viento_magnitud = resultado_viento["fuerza_daN_per_m"] * vano
    else:
        # Usar código precalculado
        if direccion_viento == "Transversal":
            viento_magnitud = self._obtener_carga_por_codigo(df_cargas_totales, "Vc")
        elif direccion_viento == "Longitudinal":
            viento_magnitud = self._obtener_carga_por_codigo(df_cargas_totales, "VcL")
    
    # Descomponer en componentes X, Y según dirección del viento
    angulo_viento_rad = math.radians(angulo_viento_deg)
    viento_x = viento_magnitud * math.cos(angulo_viento_rad) * factor_viento * factor_viento_nodo
    viento_y = viento_magnitud * math.sin(angulo_viento_rad) * factor_viento * factor_viento_nodo
```

---

## Implementación Recomendada

### Modificar `asignar_cargas_hipotesis()` en `EstructuraAEA_Mecanica.py`

**Ubicación**: Dentro del loop de conductores, reemplazar cálculo de tiro y viento

```python
# CARGAS EN CONDUCTORES
for nodo_nombre in nodos_conductor:
    nodo_obj = self.geometria.nodos.get(nodo_nombre)
    
    # ... [calcular patron_tiro, tiro_base] ...
    
    # TIRO: Calcular y rotar
    tiro_trans, tiro_long = self._calcular_componentes_tiro(...)
    tiro_x, tiro_y, tiro_z = tiro_trans, tiro_long, 0.0
    
    if nodo_obj and nodo_obj.rotacion_eje_z != 0:
        rz = math.radians(nodo_obj.rotacion_eje_z)
        tiro_x = tiro_trans * math.cos(rz) - tiro_long * math.sin(rz)
        tiro_y = tiro_trans * math.sin(rz) + tiro_long * math.cos(rz)
    
    # PESO: No se ve afectado por rotación en Z
    peso_z = -peso_cond * factor_peso_nodo
    
    # VIENTO: Recalcular con ángulo relativo ajustado
    if config["viento"]:
        direccion_viento = config["viento"]["direccion"]
        
        # Calcular ángulo relativo cable-viento
        if direccion_viento == "Transversal":
            angulo_viento = 0  # Viento en +X
        elif direccion_viento == "Longitudinal":
            angulo_viento = 90  # Viento en +Y
        
        angulo_cable = 90 + (nodo_obj.rotacion_eje_z if nodo_obj else 0)
        phi_rel = abs(angulo_viento - angulo_cable)
        if phi_rel > 90:
            phi_rel = 180 - phi_rel
        
        # Recalcular si hay rotación
        if nodo_obj and nodo_obj.cable_asociado and nodo_obj.rotacion_eje_z != 0:
            resultado = nodo_obj.cable_asociado.cargaViento(
                V=viento_velocidad, phi_rel_deg=phi_rel,
                exp=exp, clase=clase, Zc=Zc, Cf=Cf, L_vano=vano
            )
            viento_mag = resultado["fuerza_daN_per_m"] * vano
        else:
            viento_mag = self._obtener_carga_por_codigo(df_cargas_totales, codigo)
        
        # Descomponer en X, Y
        ang_rad = math.radians(angulo_viento)
        viento_x = viento_mag * math.cos(ang_rad) * factor_viento * factor_viento_nodo
        viento_y = viento_mag * math.sin(ang_rad) * factor_viento * factor_viento_nodo
```

---

## Ejemplo Numérico

### Caso: Nodo C1A con rotacion_eje_z = 270°

**Cable sin rotar** (dirección Y estándar):
- Dirección cable: 90° (eje +Y)
- Viento transversal (dirección X, 0°): `phi_rel = |0° - 90°| = 90°` → perpendicular → máxima carga
- Tiro: `tiro_x = 100 daN` (transversal), `tiro_y = 50 daN` (longitudinal)

**Cable rotado 270°** (dirección X):
- Dirección cable: 90° + 270° = 360° = 0° (eje +X)
- Viento transversal (dirección X, 0°): `phi_rel = |0° - 0°| = 0°` → paralelo → mínima carga
- Viento longitudinal (dirección Y, 90°): `phi_rel = |90° - 0°| = 90°` → perpendicular → máxima carga

**Cálculo de tiro rotado**:
```python
rz = math.radians(270)  # 270° = 4.712 rad
tiro_x_rot = 100 * cos(270°) - 50 * sin(270°) = 0 - (-50) = 50 daN
tiro_y_rot = 100 * sin(270°) + 50 * cos(270°) = -100 + 0 = -100 daN
```

**Cálculo de viento recalculado**:
```python
# Viento transversal (X): phi_rel = 0° → sin(0°) = 0 → carga mínima
viento_trans = 80 * sin(0°) = 0 daN

# Viento longitudinal (Y): phi_rel = 90° → sin(90°) = 1 → carga máxima
viento_long = 80 * sin(90°) = 80 daN

# Componentes globales:
viento_x = 0 daN (viento transversal en X)
viento_y = 80 daN (viento longitudinal en Y)
```

**Resultado físico correcto**: 
- Tiro rotado de transversal a longitudinal
- Viento recalculado: cable paralelo a viento X → carga mínima; cable perpendicular a viento Y → carga máxima

---

## Verificación

### Test 1: Rotación 0° (sin cambios)
- Input: `tiro_x=100, tiro_y=50, rotacion_z=0`
- Output: `tiro_x=100, tiro_y=50` ✓

### Test 2: Rotación 90° (cable perpendicular)
- Input: `tiro_x=100, tiro_y=0, rotacion_z=90`
- Output: `tiro_x=0, tiro_y=100` ✓

### Test 3: Rotación 270° (caso real)
- Input: `tiro_x=100, tiro_y=50, rotacion_z=270`
- Output: `tiro_x=50, tiro_y=-100` ✓

---

## Limitaciones y Mejoras Futuras

### Limitación 1: Viento Oblicuo
El viento oblicuo (45°) requiere descomposición vectorial correcta. Verificar que la suma de componentes X e Y sea consistente.

### Limitación 2: Rotaciones X e Y
Actualmente solo se implementa `rotacion_eje_z`. Rotaciones en X o Y requerirían análisis 3D completo.

### Limitación 3: Cache de Viento
Recalcular viento por nodo en cada hipótesis puede ser costoso. Considerar cachear resultados por (nodo, estado_climatico).

### Mejora Futura: Validación Física
Agregar tests que verifiquen:
- Cable a 0° con viento X → carga mínima
- Cable a 90° con viento X → carga máxima
- Conservación de energía en rotaciones

---

## Archivos a Modificar

1. **`EstructuraAEA_Mecanica.py`**: Agregar rotación de cargas después de calcular tiro y viento
2. **`NodoEstructural.py`**: Ya tiene método `rotar_vector()` implementado ✓
3. **Tests**: Crear tests unitarios para verificar rotaciones

---

## Conclusión

La implementación correcta de rotación de cargas del cable (NO del nodo) requiere:

1. **Tiro**: Rotar componentes transversal/longitudinal en plano XY según `rotacion_eje_z`
2. **Viento**: Recalcular magnitud con ángulo relativo ajustado (`phi_rel = |angulo_viento - angulo_cable|`)
3. **Peso**: No se ve afectado (dirección Z, rotación en Z)

Esta solución respeta la física real:
- Cable paralelo al viento → carga mínima (`sin(0°) = 0`)
- Cable perpendicular al viento → carga máxima (`sin(90°) = 1`)
- Tiro se redistribuye según nueva orientación del cable
