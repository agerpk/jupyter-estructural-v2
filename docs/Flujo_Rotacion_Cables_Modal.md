# Flujo Completo: Rotación de Cables desde Modal de Edición de Nodos

## Resumen Ejecutivo

El sistema permite ingresar valores de rotación de cables (NO de nodos) directamente desde el modal de edición de nodos en DGE. La rotación afecta físicamente las cargas de tiro y viento, recalculándolas según el nuevo ángulo del cable respecto al viento.

## Flujo Completo

### 1. Usuario Ingresa Rotación en Modal

**Ubicación**: Vista DGE → Botón "Editar Nodos" → Modal con tabla editable

**Campos de Rotación**:
- `Rot. X (°)`: Rotación en eje X (0-360°)
- `Rot. Y (°)`: Rotación en eje Y (0-360°)
- `Rot. Z (°)`: Rotación en eje Z (0-360°) - **PRINCIPAL para cables horizontales**

**Ejemplo**: Usuario ingresa `rotacion_eje_z: 270.0` para nodos C1A, C2A, C3A

**Archivo**: `components/vista_diseno_geometrico.py`
- Función: `generar_tabla_editor_nodos()`
- Columnas editables incluyen rotaciones con formato numérico `.1f`

---

### 2. Validación y Guardado en JSON

**Callback**: `guardar_cambios_nodos()` en `controllers/geometria_controller.py`

**Validaciones**:
```python
# Validar rotaciones entre 0-360°
rot_x = float(nodo.get("rotacion_eje_x", 0.0))
rot_y = float(nodo.get("rotacion_eje_y", 0.0))
rot_z = float(nodo.get("rotacion_eje_z", 0.0))
if not (0 <= rot_x <= 360): return error
if not (0 <= rot_y <= 360): return error
if not (0 <= rot_z <= 360): return error
```

**Guardado**:
```python
nodos_editados.append({
    "nombre": nombre,
    "tipo": nodo["tipo"],
    "coordenadas": [x, y, z],
    "cable_id": nodo.get("cable_id", ""),
    "rotacion_eje_x": float(nodo.get("rotacion_eje_x", 0.0)),
    "rotacion_eje_y": float(nodo.get("rotacion_eje_y", 0.0)),
    "rotacion_eje_z": float(nodo.get("rotacion_eje_z", 0.0)),
    "angulo_quiebre": float(nodo.get("angulo_quiebre", 0.0)),
    "tipo_fijacion": nodo.get("tipo_fijacion", "suspensión"),
    "conectado_a": conectados,
    "es_editado": True
})
```

**Persistencia**:
- `estructura_manager.guardar_nodos_editados(nodos_editados)`
- Guarda en `data/actual.estructura.json` y `data/{TITULO}.estructura.json`

---

### 3. Aplicación de Nodos Editados en DGE

**Función**: `aplicar_nodos_editados()` en `controllers/geometria_controller.py`

**Flujo**:
```python
# Crear lib_cables temporal para resolver referencias
lib_cables = LibCables()
lib_cables.agregar_cable(cable_conductor)
lib_cables.agregar_cable(cable_guardia)

# Aplicar nodos editados
estructura_geometria.importar_nodos_editados(nodos_editados, lib_cables)
```

**Archivo**: `EstructuraAEA_Geometria.py`
- Método: `importar_nodos_editados(nodos_editados_list, lib_cables)`
- Resuelve `cable_id` a objeto `Cable_AEA`
- Asigna `nodo.cable_asociado` y `nodo.rotacion_eje_z`

---

### 4. Cálculo de Cargas con Rotación

**Archivo**: `EstructuraAEA_Mecanica.py`
- Método: `asignar_cargas_hipotesis()`

#### 4.1 Rotación de Tiro (Plano XY)

**Código**:
```python
# Calcular componentes transversal y longitudinal
tiro_trans, tiro_long = self._calcular_componentes_tiro(...)

# ROTAR TIRO si el cable tiene rotacion_eje_z
if nodo_obj and nodo_obj.rotacion_eje_z != 0:
    rz = math.radians(nodo_obj.rotacion_eje_z)
    tiro_x_rot = tiro_trans * math.cos(rz) - tiro_long * math.sin(rz)
    tiro_y_rot = tiro_trans * math.sin(rz) + tiro_long * math.cos(rz)
    tiro_x, tiro_y = tiro_x_rot, tiro_y_rot
```

**Física**:
- Cable sin rotar: dirección Y (90°)
- Cable rotado 270°: dirección X (0°)
- Transformación matricial 2D en plano XY

#### 4.2 Recálculo de Viento con Ángulo Relativo

**Código**:
```python
# Determinar ángulo del viento (0° = +X, 90° = +Y)
if direccion_viento == "Transversal":
    angulo_viento_deg = 0
elif direccion_viento == "Longitudinal":
    angulo_viento_deg = 90
elif direccion_viento == "Oblicua":
    angulo_viento_deg = 45

# Cable sin rotar está en dirección Y (90°)
angulo_cable_deg = 90 + (nodo_obj.rotacion_eje_z if nodo_obj else 0)

# Ángulo relativo cable-viento
phi_rel_deg = abs(angulo_viento_deg - angulo_cable_deg)
if phi_rel_deg > 90:
    phi_rel_deg = 180 - phi_rel_deg

# Obtener velocidad de viento según estado
viento_velocidad_actual = estados_climaticos[estado_viento]["viento_velocidad"]

# Recalcular viento si cable rotado
if nodo_obj and nodo_obj.cable_asociado and nodo_obj.rotacion_eje_z != 0 and viento_velocidad_actual > 0:
    resultado_viento = nodo_obj.cable_asociado.cargaViento(
        V=viento_velocidad_actual,
        phi_rel_deg=phi_rel_deg,
        exp="C",
        clase="B",
        Zc=cable_conductor.viento_base_params['Zc'],
        Cf=cable_conductor.viento_base_params['Cf'],
        L_vano=vano,
        d_eff=d_eff
    )
    viento_cond = resultado_viento["fuerza_daN_per_m"] * vano
```

**Física del Viento**:
- Cable paralelo al viento: `phi_rel=0°` → `sin(0°)=0` → carga mínima
- Cable perpendicular: `phi_rel=90°` → `sin(90°)=1` → carga máxima
- Fórmula en `CalculoCables.py`: `cargaViento()` usa `sin(phi_rel)`

#### 4.3 Descomposición Vectorial del Viento

**Código**:
```python
# Descomponer en componentes X, Y según dirección del viento
angulo_viento_rad = math.radians(angulo_viento_deg)
viento_x += viento_cond * math.cos(angulo_viento_rad) * factor_viento * factor_viento_nodo
viento_y += viento_cond * math.sin(angulo_viento_rad) * factor_viento * factor_viento_nodo
```

**Física**:
- Viento transversal (0°): componente X máxima, Y=0
- Viento longitudinal (90°): componente Y máxima, X=0
- Viento oblicuo (45°): componentes X e Y iguales

---

### 5. Consulta de Cargas en Nodos

**Utilidad**: `utils/consultar_cargas_nodos.py`

**Funciones**:
```python
# Consultar cargas de un nodo específico
cargas = consultar_cargas_nodo(estructura_mecanica, "C1A", "HIP_Terminal_A0_EDS_(TMA)")

# Consultar todas las cargas de todos los nodos
todas_cargas = consultar_cargas_todos_nodos(estructura_mecanica)

# Generar tabla HTML
tabla_html = generar_tabla_cargas_nodo(estructura_mecanica, "C1A")
```

**Modal en DME**:
- Botón "Cargas en Nodos" abre modal XL
- Muestra tabla con todas las cargas por nodo e hipótesis
- Indica nodos editados con 🟠 y color naranja

---

## Verificación del Flujo Seamless

### ✅ Paso 1: Modal Editable
- [x] Tabla con columnas `Rot. X (°)`, `Rot. Y (°)`, `Rot. Z (°)`
- [x] Campos numéricos editables con formato `.1f`
- [x] Validación 0-360° en callback de guardado

### ✅ Paso 2: Persistencia
- [x] Guardado en JSON con estructura correcta
- [x] Campo `rotacion_eje_z` incluido en `nodos_editados`
- [x] Recarga desde archivo antes de cálculos

### ✅ Paso 3: Aplicación en Geometría
- [x] `importar_nodos_editados()` asigna `nodo.rotacion_eje_z`
- [x] Resolución de `cable_id` a `cable_asociado`
- [x] Nodos editados aplicados DESPUÉS de dimensionamiento

### ✅ Paso 4: Cálculo de Cargas
- [x] Rotación de tiro en plano XY
- [x] Recálculo de viento con `phi_rel_deg` ajustado
- [x] Descomposición vectorial del viento
- [x] Uso de `cable_asociado` específico por nodo

### ✅ Paso 5: Visualización
- [x] Modal "Cargas en Nodos" en DME
- [x] Indicadores visuales para nodos editados
- [x] Tablas por hipótesis con cargas totales

---

## Ejemplo Práctico

### Estructura: TECPETROL_Edt_mas2 (Terminal 33kV)

**Nodos con Rotación**:
```json
{
  "nombre": "C1A",
  "coordenadas": [0.0, 1.3, 7.01],
  "cable_id": "Al/Ac 70/12",
  "rotacion_eje_z": 270.0
}
```

**Interpretación Física**:
- Cable sin rotar: dirección Y (90°) - perpendicular a viento transversal
- Cable rotado 270°: dirección X (0°) - paralelo a viento transversal
- Resultado: Carga de viento transversal MÍNIMA en C1A

**Hipótesis A0 - Viento Transversal Vmax**:
- Viento: dirección X (0°)
- Cable C1A: dirección X (270° rotado)
- `phi_rel = |0° - 0°| = 0°`
- `sin(0°) = 0` → Carga de viento ≈ 0 daN

**Hipótesis A0 - Viento Longitudinal Vmax**:
- Viento: dirección Y (90°)
- Cable C1A: dirección X (270° rotado)
- `phi_rel = |90° - 0°| = 90°`
- `sin(90°) = 1` → Carga de viento MÁXIMA

---

## Archivos Involucrados

### Frontend (UI)
- `components/vista_diseno_geometrico.py`: Modal con tabla editable
- `components/vista_diseno_mecanico.py`: Modal "Cargas en Nodos"

### Backend (Lógica)
- `controllers/geometria_controller.py`: Callbacks de modal y guardado
- `controllers/mecanica_controller.py`: Callback de consulta de cargas
- `EstructuraAEA_Geometria.py`: Aplicación de nodos editados
- `EstructuraAEA_Mecanica.py`: Cálculo de cargas con rotación
- `CalculoCables.py`: Método `cargaViento()` con `phi_rel_deg`

### Utilidades
- `utils/consultar_cargas_nodos.py`: Funciones de consulta
- `utils/estructura_manager.py`: Guardado de nodos editados
- `utils/calculo_cache.py`: Persistencia de resultados

### Datos
- `data/actual.estructura.json`: Estructura activa
- `data/{TITULO}.estructura.json`: Estructura guardada
- `data/cache/*.json`: Resultados de cálculos

---

## Conclusión

El flujo funciona **seamlessly** desde el modal de edición hasta el cálculo de cargas:

1. Usuario ingresa rotación en modal → Validación → Guardado en JSON
2. Recálculo DGE → Aplicación de nodos editados → Asignación de rotaciones
3. Cálculo DME → Rotación de tiro → Recálculo de viento → Descomposición vectorial
4. Consulta de cargas → Modal DME → Visualización con indicadores

**No se requieren cambios adicionales**. El sistema está completamente implementado y funcional.
