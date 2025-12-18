# ANÁLISIS DE POSIBLES FALLOS - REFACTORIZACIÓN NODOS

## ⚠️ FALLO CRÍTICO IDENTIFICADO

### 1. INCOMPATIBILIDAD EN ASIGNACIÓN DE CARGAS

**Ubicación**: `EstructuraAEA_Mecanica.py` línea ~520

**Problema**:
```python
# CÓDIGO ACTUAL (INCORRECTO)
nueva_carga = Carga(
    nombre=nombre_completo,  # ❌ Usa nombre de hipótesis como nombre de carga
    hipotesis=[nombre_completo],
    fuerzas_x=[carga[0]],
    fuerzas_y=[carga[1]],
    fuerzas_z=[carga[2]]
)
nodo.cargas.append(nueva_carga)
```

**Por qué falla**:
1. Cada hipótesis crea una `Carga` separada con nombre = hipótesis completa
2. Un nodo con 10 hipótesis tendrá 10 objetos `Carga` diferentes
3. El diseño esperaba: 1 `Carga` llamada "Total" con 10 hipótesis

**Impacto**:
- ❌ Nodo con 20 hipótesis = 20 objetos Carga (debería ser 1-3)
- ❌ No se pueden agrupar cargas por tipo (Peso, Viento, Tiro)
- ❌ Método `obtener_cargas_hipotesis()` funciona pero es ineficiente

**Solución Requerida**:
```python
# OPCIÓN A: Una carga por nodo con todas las hipótesis
carga_total = nodo.obtener_carga("Total")
if not carga_total:
    carga_total = Carga(nombre="Total")
    nodo.agregar_carga(carga_total)
carga_total.agregar_hipotesis(nombre_completo, carga[0], carga[1], carga[2])

# OPCIÓN B: Cargas por tipo (Peso, Viento, Tiro) - REQUIERE REFACTORIZACIÓN MAYOR
# Separar cálculo de cargas por componente
```

---

## ⚠️ FALLOS POTENCIALES IDENTIFICADOS

### 2. MÉTODO `agregar_carga()` OBSOLETO EN NODOS

**Ubicación**: `NodoEstructural.py` línea ~175

**Problema**:
```python
def agregar_carga(self, carga):
    """Agrega un objeto Carga al nodo"""
    # ✅ Método correcto: recibe objeto Carga
    for i, c in enumerate(self.cargas):
        if c.nombre == carga.nombre:
            self.cargas[i] = carga
            return
    self.cargas.append(carga)
```

**Pero en código antiguo (si existe)**:
```python
# ❌ Firma antigua que ya no existe
nodo.agregar_carga(codigo_hip, fx, fy, fz)
```

**Impacto**:
- Si hay código que llama `agregar_carga(hip, fx, fy, fz)` → TypeError
- Búsqueda necesaria en todo el código

**Solución**: Buscar y reemplazar todas las llamadas antiguas

---

### 3. ACCESO A `nodo.cargas` COMO DICCIONARIO

**Ubicación**: Cualquier código que asuma `nodo.cargas` es dict

**Problema**:
```python
# ❌ CÓDIGO ANTIGUO (FALLA)
carga = nodo.cargas[codigo_hip]  # TypeError: list indices must be integers

# ❌ CÓDIGO ANTIGUO (FALLA)
if codigo_hip in nodo.cargas:  # Siempre False (busca en lista de objetos)
```

**Código correcto**:
```python
# ✅ NUEVO
cargas_dict = nodo.obtener_cargas_hipotesis(codigo_hip)
fx = cargas_dict["fx"]
```

**Impacto**:
- Cualquier código que acceda directamente a `nodo.cargas[hip]` fallará
- Necesario revisar: EstructuraAEA_Graficos, controllers, utils

---

### 4. SERIALIZACIÓN/DESERIALIZACIÓN DE NODOS

**Ubicación**: `importar_nodos_editados()`, cache, JSON

**Problema**:
```python
# Al guardar nodos editados
nodos_editados = estructura.exportar_nodos_editados()
# ¿Incluye cargas? ¿Cómo se serializan objetos Carga?

# Al cargar
estructura.importar_nodos_editados(nodos_list, lib_cables)
# ¿Se pierden las cargas?
```

**Impacto**:
- Si se guarda estructura con cargas y se recarga → cargas se pierden
- Cache de DGE no incluye cargas (solo geometría)
- Cache de DME debe incluir cargas pero ¿cómo?

**Solución**:
- Verificar que `to_dict(incluir_cargas=True)` se usa en cache DME
- Verificar que `from_dict()` reconstruye cargas correctamente

---

### 5. COMPATIBILIDAD CON `generar_dataframe_cargas()`

**Ubicación**: `EstructuraAEA_Mecanica.py` línea ~650

**Problema**:
```python
# Método usa self.cargas_key (dict) para generar DataFrame
# Pero ahora cargas están en nodo.cargas (lista de objetos Carga)
```

**Estado actual**:
- ✅ `self.cargas_key` se sigue manteniendo como dict
- ✅ DataFrame se genera desde `cargas_key`, no desde nodos
- ⚠️ Duplicación: cargas en `cargas_key` Y en `nodo.cargas`

**Impacto**:
- Funciona pero hay duplicación de datos
- Si se modifica `nodo.cargas` no se refleja en `cargas_key`

---

### 6. ROTACIONES NO APLICADAS EN CÁLCULO DE REACCIONES

**Ubicación**: `calcular_reacciones_tiros_cima()`

**Problema**:
```python
# Método usa cargas desde self.cargas_key (sin rotación)
for nodo_nombre, carga in cargas_nodo.items():
    Fx_n, Fy_n, Fz_n = carga  # ❌ No considera rotación del nodo
```

**Impacto**:
- Nodos con rotación no aplican transformación en reacciones
- Cálculo de momentos puede ser incorrecto

**Solución**:
```python
# Obtener cargas rotadas
nodo_obj = self.geometria.nodos[nodo_nombre]
cargas_rotadas = nodo_obj.obtener_cargas_hipotesis_rotadas(nombre_hipotesis, "global")
Fx_n = cargas_rotadas["fx"]
Fy_n = cargas_rotadas["fy"]
Fz_n = cargas_rotadas["fz"]
```

---

## 🔍 PUNTOS DE VERIFICACIÓN NECESARIOS

### A. Buscar Llamadas Antiguas a `agregar_carga()`
```bash
# Buscar patrón: nodo.agregar_carga(hip, fx, fy, fz)
grep -r "\.agregar_carga(" --include="*.py"
```

### B. Buscar Acceso Directo a `nodo.cargas[hip]`
```bash
# Buscar patrón: nodo.cargas[...]
grep -r "\.cargas\[" --include="*.py"
```

### C. Verificar Serialización en Cache
- `CalculoCache.guardar_calculo_dme()` → ¿Incluye cargas de nodos?
- `CalculoCache.cargar_calculo_dme()` → ¿Reconstruye cargas?

### D. Verificar Gráficos y Visualización
- `EstructuraAEA_Graficos.py` → ¿Accede a cargas de nodos?
- `arboles_carga.py` → ¿Usa `cargas_key` o `nodo.cargas`?

---

## 🛠️ CORRECCIONES URGENTES NECESARIAS

### CORRECCIÓN 1: Refactorizar Asignación de Cargas

**Archivo**: `EstructuraAEA_Mecanica.py`

**Cambio**:
```python
# REEMPLAZAR bloque de asignación de cargas (línea ~520)
# DE:
nueva_carga = Carga(
    nombre=nombre_completo,
    hipotesis=[nombre_completo],
    ...
)
nodo.cargas.append(nueva_carga)

# A:
# Buscar o crear carga "Total" para el nodo
carga_total = nodo.obtener_carga("Total")
if not carga_total:
    carga_total = Carga(nombre="Total")
    nodo.agregar_carga(carga_total)

# Agregar hipótesis a la carga total
carga_total.agregar_hipotesis(
    nombre_completo,
    fx=carga[0],
    fy=carga[1],
    fz=carga[2]
)
```

### CORRECCIÓN 2: Aplicar Rotaciones en Reacciones

**Archivo**: `EstructuraAEA_Mecanica.py`

**Cambio**: Usar `obtener_cargas_hipotesis_rotadas()` en lugar de acceso directo

---

## 📊 RESUMEN DE RIESGOS

| Riesgo | Severidad | Probabilidad | Impacto |
|--------|-----------|--------------|---------|
| Asignación incorrecta de cargas | 🔴 ALTA | 100% | Estructura de datos incorrecta |
| Llamadas antiguas a agregar_carga() | 🟡 MEDIA | 30% | TypeError en runtime |
| Acceso directo a nodo.cargas[hip] | 🟡 MEDIA | 20% | TypeError en runtime |
| Pérdida de cargas en serialización | 🟡 MEDIA | 50% | Datos incompletos en cache |
| Rotaciones no aplicadas | 🟠 BAJA | 10% | Cálculos incorrectos |
| Duplicación cargas_key vs nodo.cargas | 🟢 INFO | 100% | Ineficiencia, no fallo |

---

## ✅ PLAN DE ACCIÓN INMEDIATO

1. **CRÍTICO**: Corregir asignación de cargas en `asignar_cargas_hipotesis()`
2. **IMPORTANTE**: Buscar y eliminar llamadas antiguas a `agregar_carga(hip, fx, fy, fz)`
3. **IMPORTANTE**: Verificar serialización en cache
4. **RECOMENDADO**: Aplicar rotaciones en cálculo de reacciones
5. **OPCIONAL**: Eliminar duplicación `cargas_key` (refactorización mayor)

---

## 🧪 TESTS CRÍTICOS ANTES DE USAR

```python
# Test 1: Verificar estructura de cargas
nodo = geometria.nodos['C1_R']
assert len(nodo.cargas) <= 5  # No debe haber 20+ cargas
carga_total = nodo.obtener_carga("Total")
assert carga_total is not None
assert len(carga_total.hipotesis) > 0

# Test 2: Verificar obtención de cargas
cargas = nodo.obtener_cargas_hipotesis("HIP_Terminal_A0_...")
assert "fx" in cargas
assert isinstance(cargas["fx"], (int, float))

# Test 3: Verificar serialización
nodo_dict = nodo.to_dict(incluir_cargas=True)
assert "cargas" in nodo_dict
nodo_nuevo = NodoEstructural.from_dict(nodo_dict)
assert len(nodo_nuevo.cargas) == len(nodo.cargas)
```
