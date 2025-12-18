# PLAN DE ACCIÓN: UNIFICACIÓN DE NODOS Y REFACTORIZACIÓN (ACTUALIZADO)

## OBJETIVO
Unificar la gestión de nodos estructurales eliminando la duplicación entre `nodos{}` y `nodes_key{}`, agregando soporte para momentos y rotaciones en 3 ejes, y simplificando el flujo de cálculo.

---

## FASE 1: PREPARACIÓN (✅ COMPLETADA)

### 1.1. Crear `NodoEstructural.py`
- ✅ Archivo independiente con clase `NodoEstructural`
- ✅ Nueva clase `CargaNodo` para fuerzas (Fx, Fy, Fz) y momentos (Mx, My, Mz)
- ✅ Métodos `sumar_fuerzas()` y `sumar_momentos()`
- ✅ Propiedades `x`, `y`, `z` para acceso directo
- ✅ Métodos `to_dict()` y `from_dict()` para serialización
- ✅ **Soporte para rotaciones en 3 ejes** (rotacion_eje_x, rotacion_eje_y, rotacion_eje_z)
- ✅ **Método `rotar_vector()`** para aplicar rotaciones (orden X→Y→Z)
- ✅ **Método `obtener_carga_rotada()`** para sistema local/global
- ✅ **Métodos `sumar_fuerzas_rotadas()` y `sumar_momentos_rotados()`**

### 1.2. Características de rotación implementadas

**Rotaciones:**
- Orden de aplicación: X → Y → Z (estándar)
- Sentido antihorario positivo
- Rotación inversa para ver desde sistema global

**Ejemplo de uso:**
```python
# Crear nodo con rotación
nodo = NodoEstructural("C1A", (0, 1.3, 7.0), "conductor", rotacion_eje_z=90.0)

# Agregar carga en sistema local del nodo
nodo.agregar_carga("HIP_A0", fx=100, fy=0, fz=-200)

# Obtener carga en sistema global (rotada)
carga_global = nodo.obtener_carga_rotada("HIP_A0", "global")
# fx_global ≈ 0, fy_global ≈ 100 (rotado 90° en Z)
```

---

## FASE 2: REFACTORIZACIÓN DE `EstructuraAEA_Geometria.py`

### 2.1. Importar nueva clase
```python
from NodoEstructural import NodoEstructural, CargaNodo
```

### 2.2. Eliminar definición antigua
- Eliminar líneas 5-91 de `EstructuraAEA_Geometria.py`

### 2.3. Actualizar creación de nodos
```python
# ANTES
self.nodos[nombre] = NodoEstructural(
    nombre, coordenadas, tipo, cable, angulo, fijacion, rotacion_z
)

# DESPUÉS
self.nodos[nombre] = NodoEstructural(
    nombre, coordenadas, tipo, cable, angulo, fijacion,
    rotacion_eje_z=rotacion_z,
    rotacion_eje_x=0.0,  # Por defecto
    rotacion_eje_y=0.0   # Por defecto
)
```

### 2.4. Eliminar `nodes_key` y métodos relacionados
- Eliminar `self.nodes_key = {}`
- Eliminar método `_actualizar_nodes_key()`
- Agregar método `obtener_nodos_dict()` para compatibilidad

---

## FASE 3: REFACTORIZACIÓN DE `EstructuraAEA_Mecanica.py`

### 3.1. Eliminar método `_rotar_carga_eje_z()`
**Este método ya no es necesario - usar `nodo.rotar_vector()` en su lugar**

```python
# ELIMINAR ESTE MÉTODO COMPLETO
def _rotar_carga_eje_z(self, fx, fy, fz, angulo_grados):
    # ... código antiguo ...
```

### 3.2. Actualizar `asignar_cargas_hipotesis()`

**Cambio 1: Eliminar rotación manual**
```python
# ANTES (líneas ~450)
# APLICAR ROTACIÓN EN EJE Z SI EL NODO LO REQUIERE
nodo_obj = self.geometria.nodos.get(nodo)
if nodo_obj and hasattr(nodo_obj, 'rotacion_eje_z') and nodo_obj.rotacion_eje_z != 0:
    carga_x, carga_y, carga_z = self._rotar_carga_eje_z(
        carga_x, carga_y, carga_z, nodo_obj.rotacion_eje_z
    )

# DESPUÉS
# NO HACER NADA - La rotación se maneja al obtener la carga
```

**Cambio 2: Agregar cargas en sistema LOCAL del nodo**
```python
# Las cargas se agregan en sistema local (sin rotar)
self.geometria.nodos[nodo_nombre].agregar_carga(
    nombre_completo, 
    fx=carga_x, fy=carga_y, fz=carga_z,
    mx=0.0, my=0.0, mz=0.0
)
```

### 3.3. Actualizar `calcular_reacciones_tiros_cima()`

**Usar cargas rotadas al sistema global:**
```python
# ANTES
for nodo, carga in cargas_nodo.items():
    x, y, z = self.geometria.nodes_key[nodo]
    Fx_n, Fy_n, Fz_n = carga

# DESPUÉS
for nodo_nombre in cargas_nodo.keys():
    nodo_obj = self.geometria.nodos[nodo_nombre]
    
    # Obtener carga en sistema GLOBAL (rotada)
    carga_obj = nodo_obj.obtener_carga_rotada(nombre_hipotesis, "global")
    Fx_n, Fy_n, Fz_n = carga_obj.fx, carga_obj.fy, carga_obj.fz
    
    # Sumar fuerzas
    Fx += Fx_n
    Fy += Fy_n
    Fz += Fz_n
    
    # Vector posición relativa
    rx = nodo_obj.x - x_apoyo
    ry = nodo_obj.y - y_apoyo
    rz = nodo_obj.z - z_apoyo
    
    # Momentos por producto vectorial r × F
    Mx += (ry * Fz_n) - (rz * Fy_n)
    My += (rz * Fx_n) - (rx * Fz_n)
    Mz += (rx * Fy_n) - (ry * Fx_n)
    
    # NUEVO: Sumar momentos directos del nodo
    Mx += carga_obj.mx
    My += carga_obj.my
    Mz += carga_obj.mz
```

### 3.4. Nuevo método: `calcular_cargas_agregadas()`

**Agregar método para sumar cargas de múltiples nodos:**

```python
def calcular_cargas_agregadas(self, nodo_destino, lista_nodos="todos", 
                              codigos_hipotesis=None, incluir_momentos=True):
    """
    Calcula fuerzas y momentos agregados de múltiples nodos en un nodo destino
    
    Args:
        nodo_destino (str): Nombre del nodo donde se agregan las cargas
        lista_nodos (str/list): "todos" o lista de nombres de nodos
        codigos_hipotesis (list): Lista de hipótesis a considerar
        incluir_momentos (bool): Si True, calcula momentos por producto vectorial
    
    Returns:
        dict: {codigo_hip: {"fx": ..., "fy": ..., "fz": ..., "mx": ..., "my": ..., "mz": ...}}
    """
    if nodo_destino not in self.geometria.nodos:
        raise ValueError(f"Nodo destino '{nodo_destino}' no existe")
    
    nodo_dest = self.geometria.nodos[nodo_destino]
    
    # Determinar lista de nodos
    if lista_nodos == "todos":
        nodos_a_sumar = [n for n in self.geometria.nodos.keys() if n != nodo_destino]
    else:
        nodos_a_sumar = [n for n in lista_nodos if n in self.geometria.nodos and n != nodo_destino]
    
    # Determinar hipótesis
    if codigos_hipotesis is None:
        codigos_hipotesis = set()
        for nodo_nombre in nodos_a_sumar:
            codigos_hipotesis.update(self.geometria.nodos[nodo_nombre].cargas.keys())
        codigos_hipotesis = list(codigos_hipotesis)
    
    resultados = {}
    
    for codigo_hip in codigos_hipotesis:
        fx_total, fy_total, fz_total = 0.0, 0.0, 0.0
        mx_total, my_total, mz_total = 0.0, 0.0, 0.0
        
        for nodo_nombre in nodos_a_sumar:
            nodo = self.geometria.nodos[nodo_nombre]
            
            # Obtener carga en sistema GLOBAL (rotada)
            carga = nodo.obtener_carga_rotada(codigo_hip, "global")
            
            # Sumar fuerzas
            fx_total += carga.fx
            fy_total += carga.fy
            fz_total += carga.fz
            
            if incluir_momentos:
                # Sumar momentos directos
                mx_total += carga.mx
                my_total += carga.my
                mz_total += carga.mz
                
                # Calcular momentos por producto vectorial r × F
                rx = nodo.x - nodo_dest.x
                ry = nodo.y - nodo_dest.y
                rz = nodo.z - nodo_dest.z
                
                mx_total += (ry * carga.fz) - (rz * carga.fy)
                my_total += (rz * carga.fx) - (rx * carga.fz)
                mz_total += (rx * carga.fy) - (ry * carga.fx)
        
        resultados[codigo_hip] = {
            "fx": round(fx_total, 2),
            "fy": round(fy_total, 2),
            "fz": round(fz_total, 2),
            "mx": round(mx_total, 2),
            "my": round(my_total, 2),
            "mz": round(mz_total, 2)
        }
    
    return resultados
```

---

## FASE 4: ACTUALIZACIÓN DE CONTROLADORES Y VISTAS

### 4.1. `geometria_controller.py`

**Actualizar serialización de nodos editados:**
```python
# Agregar rotaciones X e Y al guardar
nodos_editados.append({
    "nombre": nombre,
    "tipo": nodo["tipo"],
    "coordenadas": [float(nodo["x"]), float(nodo["y"]), float(nodo["z"])],
    "cable_id": nodo.get("cable_id", ""),
    "rotacion_eje_x": float(nodo.get("rotacion_eje_x", 0.0)),  # NUEVO
    "rotacion_eje_y": float(nodo.get("rotacion_eje_y", 0.0)),  # NUEVO
    "rotacion_eje_z": float(nodo.get("rotacion_eje_z", 0.0)),
    "angulo_quiebre": float(nodo.get("angulo_quiebre", 0.0)),
    "tipo_fijacion": nodo.get("tipo_fijacion", "suspensión"),
    "conectado_a": conectados,
    "es_editado": True
})
```

### 4.2. `vista_diseno_geometrico.py`

**Actualizar tabla de editor de nodos:**
```python
columns=[
    {"name": "Nombre", "id": "nombre", "editable": True},
    {"name": "Tipo", "id": "tipo", "editable": True, "presentation": "dropdown"},
    {"name": "X (m)", "id": "x", "type": "numeric", "editable": True},
    {"name": "Y (m)", "id": "y", "type": "numeric", "editable": True},
    {"name": "Z (m)", "id": "z", "type": "numeric", "editable": True},
    {"name": "Cable", "id": "cable_id", "editable": True, "presentation": "dropdown"},
    {"name": "Rot. X (°)", "id": "rotacion_eje_x", "type": "numeric", "editable": True},  # NUEVO
    {"name": "Rot. Y (°)", "id": "rotacion_eje_y", "type": "numeric", "editable": True},  # NUEVO
    {"name": "Rot. Z (°)", "id": "rotacion_eje_z", "type": "numeric", "editable": True},
    {"name": "Áng. Quiebre (°)", "id": "angulo_quiebre", "type": "numeric", "editable": True},
    {"name": "Fijación", "id": "tipo_fijacion", "editable": True, "presentation": "dropdown"},
    {"name": "Conectado A", "id": "conectado_a", "editable": False},
    {"name": "Editar", "id": "editar_conexiones", "editable": False},
]
```

---

## FASE 5: TESTING

### 5.1. Test de rotaciones
```python
def test_rotacion_z_90_grados():
    nodo = NodoEstructural("C1A", (0, 1.3, 7.0), "conductor", rotacion_eje_z=90.0)
    nodo.agregar_carga("HIP_A0", fx=100, fy=0, fz=-200)
    
    # Sistema local
    carga_local = nodo.obtener_carga("HIP_A0")
    assert carga_local.fx == 100
    assert carga_local.fy == 0
    
    # Sistema global (rotado 90° en Z)
    carga_global = nodo.obtener_carga_rotada("HIP_A0", "global")
    assert abs(carga_global.fx) < 0.01  # ≈ 0
    assert abs(carga_global.fy - 100) < 0.01  # ≈ 100

def test_agregacion_cargas():
    # Crear estructura con 3 nodos
    geometria = crear_geometria_test()
    mecanica = EstructuraAEA_Mecanica(geometria)
    
    # Agregar cargas
    geometria.nodos["C1"].agregar_carga("HIP_A0", fx=100, fy=0, fz=-200)
    geometria.nodos["C2"].agregar_carga("HIP_A0", fx=150, fy=50, fz=-250)
    
    # Calcular agregadas en BASE
    resultados = mecanica.calcular_cargas_agregadas("BASE", ["C1", "C2"], ["HIP_A0"])
    
    assert resultados["HIP_A0"]["fx"] == 250
    assert resultados["HIP_A0"]["fy"] == 50
    assert resultados["HIP_A0"]["fz"] == -450
```

---

## BENEFICIOS ADICIONALES

### Rotaciones en 3 ejes
- ✅ Soporte completo para rotaciones X, Y, Z
- ✅ Orden estándar de aplicación (X→Y→Z)
- ✅ Conversión automática entre sistema local/global

### Agregación de cargas
- ✅ Método para sumar cargas de múltiples nodos
- ✅ Cálculo automático de momentos por producto vectorial
- ✅ Soporte para filtrar por hipótesis

### Momentos directos
- ✅ Soporte para momentos aplicados directamente en nodos
- ✅ Suma de momentos directos + momentos por fuerzas

---

## CRONOGRAMA ACTUALIZADO

- **Fase 1:** ✅ COMPLETADA (2 horas)
- **Fase 2:** Refactorización Geometría (2-3 horas)
- **Fase 3:** Refactorización Mecánica (3-4 horas) ← Aumentado por nuevos métodos
- **Fase 4:** Actualización Controladores (2-3 horas) ← Aumentado por rotaciones
- **Fase 5:** Testing (3-4 horas) ← Aumentado por tests de rotación
- **Fase 6:** Migración gradual (1 hora)

**TOTAL ESTIMADO:** 13-17 horas de trabajo

---

**Tokens used/total (58% session). Monthly limit: <1%**
