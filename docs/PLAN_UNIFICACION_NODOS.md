# PLAN DE ACCIÓN: UNIFICACIÓN DE NODOS Y REFACTORIZACIÓN

## OBJETIVO
Unificar la gestión de nodos estructurales eliminando la duplicación entre `nodos{}` y `nodes_key{}`, agregando soporte para momentos, y simplificando el flujo de cálculo.

---

## FASE 1: PREPARACIÓN (COMPLETADA ✅)

### 1.1. Crear `NodoEstructural.py`
- ✅ Archivo independiente con clase `NodoEstructural`
- ✅ Nueva clase `CargaNodo` para fuerzas y momentos
- ✅ Métodos `sumar_fuerzas()` y `sumar_momentos()`
- ✅ Propiedades `x`, `y`, `z` para acceso directo
- ✅ Métodos `to_dict()` y `from_dict()` para serialización

---

## FASE 2: REFACTORIZACIÓN DE `EstructuraAEA_Geometria.py`

### 2.1. Importar nueva clase
```python
from NodoEstructural import NodoEstructural, CargaNodo
```

### 2.2. Eliminar definición antigua de `NodoEstructural`
- Eliminar líneas 5-91 de `EstructuraAEA_Geometria.py`

### 2.3. Eliminar `nodes_key` y usar solo `nodos`
**CAMBIOS:**

```python
# ANTES
self.nodos = {}
self.nodes_key = {}

# DESPUÉS
self.nodos = {}  # ÚNICA fuente de verdad
```

### 2.4. Modificar métodos que usan `nodes_key`

**Método `obtener_nodes_key()` → DEPRECAR**
```python
def obtener_nodes_key(self):
    """DEPRECATED: Usar obtener_nodos_dict() en su lugar"""
    import warnings
    warnings.warn("obtener_nodes_key() está deprecado. Usar obtener_nodos_dict()", DeprecationWarning)
    return self.obtener_nodos_dict()

def obtener_nodos_dict(self):
    """Devuelve diccionario {nombre: [x, y, z]} para compatibilidad"""
    return {nombre: list(nodo.coordenadas) for nombre, nodo in self.nodos.items()}
```

**Método `_actualizar_nodes_key()` → ELIMINAR**
```python
# ELIMINAR COMPLETAMENTE - Ya no es necesario
```

**Método `listar_nodos()` → SIMPLIFICAR**
```python
def listar_nodos(self):
    """Lista todos los nodos de la estructura"""
    print(f"\n📋 NODOS DE LA ESTRUCTURA ({len(self.nodos)} nodos):")
    print("=" * 80)
    
    tipos_orden = ["base", "cruce", "conductor", "guardia", "general", "viento"]
    
    for tipo in tipos_orden:
        nodos_tipo = [(nombre, nodo) for nombre, nodo in self.nodos.items() 
                     if nodo.tipo_nodo == tipo]
        if nodos_tipo:
            print(f"\n{tipo.upper()}:")
            for nombre, nodo in sorted(nodos_tipo, key=lambda x: x[0]):
                cable_info = f" - {nodo.cable_asociado.nombre}" if nodo.cable_asociado else ""
                print(f"  {nombre}: ({nodo.x:.3f}, {nodo.y:.3f}, {nodo.z:.3f}){cable_info}")
```

### 2.5. Modificar `_generar_conexiones()`
```python
def _generar_conexiones(self):
    """Genera lista de conexiones entre nodos"""
    self.conexiones = []
    
    # 1. COLUMNAS: Conexiones verticales en x=0
    nodos_centrales = []
    for nombre, nodo in self.nodos.items():
        if abs(nodo.x) < 0.001 and abs(nodo.y) < 0.001:
            if not nombre.startswith(('C1', 'C2', 'C3', 'HG')):
                nodos_centrales.append((nodo.z, nombre))
    
    nodos_centrales.sort(key=lambda x: x[0])
    for i in range(len(nodos_centrales)-1):
        self.conexiones.append((nodos_centrales[i][1], nodos_centrales[i+1][1], 'columna'))
    
    # ... resto del código usando self.nodos en lugar de self.nodes_key
```

---

## FASE 3: REFACTORIZACIÓN DE `EstructuraAEA_Mecanica.py`

### 3.1. Actualizar `asignar_cargas_hipotesis()`

**CAMBIO CRÍTICO: Usar `agregar_carga()` con 6 parámetros**

```python
# ANTES
self.geometria.nodos[nodo_nombre].agregar_carga(
    nombre_completo, carga[0], carga[1], carga[2]
)

# DESPUÉS
self.geometria.nodos[nodo_nombre].agregar_carga(
    nombre_completo, 
    fx=carga[0], fy=carga[1], fz=carga[2],
    mx=0.0, my=0.0, mz=0.0  # Por ahora momentos en 0
)
```

### 3.2. Actualizar `calcular_reacciones_tiros_cima()`

**Usar propiedades del nodo directamente:**

```python
# ANTES
x, y, z = self.geometria.nodes_key[nodo]
Fx_n, Fy_n, Fz_n = carga

# DESPUÉS
nodo_obj = self.geometria.nodos[nodo]
carga_obj = nodo_obj.obtener_carga(nombre_hipotesis)
Fx_n, Fy_n, Fz_n = carga_obj.fx, carga_obj.fy, carga_obj.fz

# Vector posición relativa
rx, ry, rz = nodo_obj.x - x_apoyo, nodo_obj.y - y_apoyo, nodo_obj.z - z_apoyo
```

### 3.3. Eliminar `self.cargas_key` (OPCIONAL - Fase posterior)

**Justificación:** Las cargas ya están en `nodo.cargas{}`, no necesitamos duplicarlas.

**Alternativa:** Mantener `cargas_key` temporalmente para compatibilidad con código existente.

---

## FASE 4: ACTUALIZACIÓN DE CONTROLADORES Y VISTAS

### 4.1. `geometria_controller.py`

**Cambios en `ejecutar_calculo_dge()`:**

```python
# ANTES
nodes_key = estructura_geometria.obtener_nodes_key()

# DESPUÉS
nodes_key = estructura_geometria.obtener_nodos_dict()
```

**Cambios en callbacks de editor de nodos:**

```python
# ANTES
nodos_dict = state.calculo_objetos.estructura_geometria.nodes_key

# DESPUÉS
nodos_dict = state.calculo_objetos.estructura_geometria.obtener_nodos_dict()
```

### 4.2. `vista_diseno_geometrico.py`

**Cambios en `generar_resultados_dge()`:**

```python
# ANTES
nodes_key = calculo_guardado.get('nodes_key', {})

# DESPUÉS
# Reconstruir nodos desde cache
nodos_data = calculo_guardado.get('nodos', [])
nodos_dict = {n['nombre']: n['coordenadas'] for n in nodos_data}
```

### 4.3. `calculo_cache.py`

**Actualizar `guardar_calculo_dge()`:**

```python
def guardar_calculo_dge(nombre_estructura, parametros, dimensiones, 
                       nodos, fig_estructura, fig_cabezal, fig_nodos, 
                       memoria_calculo, conexiones):
    """
    Args:
        nodos (dict): Diccionario de objetos NodoEstructural
    """
    # Serializar nodos completos
    nodos_serializados = [nodo.to_dict(incluir_cargas=False) 
                         for nodo in nodos.values()]
    
    calculo = {
        "tipo": "DGE",
        "nombre_estructura": nombre_estructura,
        "parametros": parametros,
        "hash_parametros": hash_params,
        "dimensiones": dimensiones,
        "nodos": nodos_serializados,  # ← NUEVO: nodos completos
        "nodes_key": {n: list(nodo.coordenadas) for n, nodo in nodos.items()},  # ← Compatibilidad
        "conexiones": conexiones,
        "memoria_calculo": memoria_calculo,
        "fecha_calculo": datetime.datetime.now().isoformat()
    }
    # ... resto del código
```

**Actualizar `cargar_calculo_dge()`:**

```python
def cargar_calculo_dge(nombre_estructura):
    # ... código de carga ...
    
    # Reconstruir nodos si existen
    if "nodos" in calculo:
        # Versión nueva: nodos completos
        nodos_dict = {}
        for nodo_data in calculo["nodos"]:
            nodo = NodoEstructural.from_dict(nodo_data)
            nodos_dict[nodo.nombre] = nodo
        calculo["nodos_objetos"] = nodos_dict
    
    return calculo
```

---

## FASE 5: ACTUALIZACIÓN DE GRÁFICOS

### 5.1. `EstructuraAEA_Graficos.py`

**Cambios en métodos de graficación:**

```python
# ANTES
for nombre, coords in self.geometria.nodes_key.items():
    x, y, z = coords

# DESPUÉS
for nombre, nodo in self.geometria.nodos.items():
    x, y, z = nodo.x, nodo.y, nodo.z
```

---

## FASE 6: TESTING Y VALIDACIÓN

### 6.1. Tests unitarios para `NodoEstructural`

```python
# tests/test_nodo_estructural.py
def test_crear_nodo():
    nodo = NodoEstructural("C1_R", (1.3, 0.0, 9.0), "conductor")
    assert nodo.x == 1.3
    assert nodo.y == 0.0
    assert nodo.z == 9.0

def test_agregar_carga():
    nodo = NodoEstructural("C1_R", (1.3, 0.0, 9.0), "conductor")
    nodo.agregar_carga("HIP_A0", fx=100, fy=50, fz=-200, mx=10, my=20, mz=5)
    carga = nodo.obtener_carga("HIP_A0")
    assert carga.fx == 100
    assert carga.mx == 10

def test_sumar_fuerzas():
    nodo = NodoEstructural("C1_R", (1.3, 0.0, 9.0), "conductor")
    nodo.agregar_carga("HIP_A0", fx=100, fy=50, fz=-200)
    nodo.agregar_carga("HIP_A1", fx=150, fy=80, fz=-250)
    fx, fy, fz = nodo.sumar_fuerzas()
    assert fx == 250
    assert fy == 130
    assert fz == -450
```

### 6.2. Tests de integración

```python
def test_flujo_completo_cmc_dge_dme():
    # 1. Ejecutar CMC
    # 2. Ejecutar DGE
    # 3. Verificar que nodos tienen coordenadas correctas
    # 4. Ejecutar DME
    # 5. Verificar que nodos tienen cargas asignadas
    # 6. Verificar que sumar_fuerzas() da resultados correctos
    pass
```

---

## FASE 7: MIGRACIÓN GRADUAL

### 7.1. Estrategia de compatibilidad hacia atrás

**Mantener `nodes_key` temporalmente:**

```python
@property
def nodes_key(self):
    """DEPRECATED: Propiedad de compatibilidad"""
    import warnings
    warnings.warn("nodes_key está deprecado. Usar obtener_nodos_dict()", DeprecationWarning)
    return self.obtener_nodos_dict()
```

### 7.2. Orden de implementación

1. ✅ **Crear `NodoEstructural.py`** (COMPLETADO)
2. **Actualizar `EstructuraAEA_Geometria.py`**
   - Importar nueva clase
   - Eliminar definición antigua
   - Mantener `nodes_key` como propiedad deprecada
3. **Actualizar `EstructuraAEA_Mecanica.py`**
   - Usar nuevos métodos de `NodoEstructural`
   - Agregar soporte para momentos
4. **Actualizar controladores**
   - Usar `obtener_nodos_dict()` en lugar de `nodes_key`
5. **Actualizar cache**
   - Guardar nodos completos
   - Mantener `nodes_key` para compatibilidad
6. **Testing completo**
   - Verificar que CMC → DGE → DME funciona
   - Verificar que cache funciona
   - Verificar que editor de nodos funciona
7. **Eliminar código deprecado**
   - Eliminar propiedad `nodes_key`
   - Eliminar método `_actualizar_nodes_key()`

---

## FASE 8: BENEFICIOS ESPERADOS

### 8.1. Simplificación
- ❌ Elimina duplicación `nodos{}` vs `nodes_key{}`
- ❌ Elimina necesidad de `_actualizar_nodes_key()`
- ✅ Una sola fuente de verdad: `self.nodos{}`

### 8.2. Funcionalidad mejorada
- ✅ Soporte para momentos (Mx, My, Mz)
- ✅ Métodos `sumar_fuerzas()` y `sumar_momentos()`
- ✅ Acceso directo a coordenadas con `nodo.x`, `nodo.y`, `nodo.z`

### 8.3. Mantenibilidad
- ✅ Código más limpio y fácil de entender
- ✅ Menos propenso a errores de sincronización
- ✅ Más fácil de extender en el futuro

### 8.4. Serialización mejorada
- ✅ `to_dict()` y `from_dict()` para JSON
- ✅ Opción de incluir/excluir cargas en serialización
- ✅ Reconstrucción completa de nodos desde cache

---

## RIESGOS Y MITIGACIONES

### Riesgo 1: Romper código existente
**Mitigación:** Mantener `nodes_key` como propiedad deprecada durante transición

### Riesgo 2: Pérdida de datos en cache antiguo
**Mitigación:** Código de carga debe soportar ambos formatos (antiguo y nuevo)

### Riesgo 3: Performance con muchos nodos
**Mitigación:** `obtener_nodos_dict()` genera dict bajo demanda, no lo mantiene en memoria

---

## CRONOGRAMA ESTIMADO

- **Fase 1:** ✅ COMPLETADA (1 hora)
- **Fase 2:** Refactorización Geometría (2-3 horas)
- **Fase 3:** Refactorización Mecánica (2-3 horas)
- **Fase 4:** Actualización Controladores (2 horas)
- **Fase 5:** Actualización Gráficos (1 hora)
- **Fase 6:** Testing (2-3 horas)
- **Fase 7:** Migración gradual (1 hora)
- **Fase 8:** Limpieza final (1 hora)

**TOTAL ESTIMADO:** 12-16 horas de trabajo

---

## PRÓXIMOS PASOS INMEDIATOS

1. **Revisar y aprobar este plan**
2. **Comenzar Fase 2:** Actualizar `EstructuraAEA_Geometria.py`
3. **Crear branch de desarrollo:** `feature/unificar-nodos`
4. **Implementar cambios incrementalmente**
5. **Testing continuo después de cada fase**

---

## NOTAS ADICIONALES

### Compatibilidad con JSON existente
Los archivos `*.estructura.json` existentes tienen `nodos_editados` en formato antiguo. El código debe:
1. Detectar formato antiguo vs nuevo
2. Convertir automáticamente si es necesario
3. Guardar siempre en formato nuevo

### Extensiones futuras
Una vez completada la unificación, será más fácil:
- Agregar validación geométrica de nodos
- Implementar editor gráfico 3D
- Agregar historial de cambios en nodos
- Implementar sistema de templates de nodos

---

**Tokens used/total (50% session). Monthly limit: <1%**
