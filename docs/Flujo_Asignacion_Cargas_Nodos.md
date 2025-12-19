# Flujo de Asignación de Cargas desde cable_id hasta Cargas Reales

## Resumen Ejecutivo

El sistema ahora usa el cable específico de cada nodo (`cable_asociado`) para calcular cargas (peso, viento, tiro) en lugar de usar cables globales. Esto permite que diferentes nodos tengan diferentes cables y reciban cargas correctas según sus propiedades.

---

## Flujo Completo: De cable_id a Cargas

### 1. Definición en JSON (Nodos Editados)

El usuario define nodos editados en el archivo `.estructura.json`:

```json
{
  "nodos_editados": [
    {
      "nombre": "C1_R",
      "tipo": "general",
      "coordenadas": [1.3, 0.0, 11.378],
      "cable_id": "Al/Ac 70/12",
      "rotacion_eje_z": 0.0,
      "tipo_fijacion": "suspensión"
    },
    {
      "nombre": "HG1",
      "tipo": "general",
      "coordenadas": [0.0, 0.0, 16.629],
      "cable_id": "OPGW FiberHome 24FO 58mm2",
      "rotacion_eje_z": 0.0,
      "tipo_fijacion": "suspensión"
    }
  ]
}
```

**Campo clave**: `cable_id` es un string que identifica el cable (ej: "Al/Ac 70/12")

---

### 2. Resolución de cable_id → Objeto Cable_AEA

**Archivo**: `controllers/geometria_controller.py`  
**Función**: `aplicar_nodos_editados()` (línea ~90)

```python
# Crear biblioteca de cables disponibles
lib_cables = LibCables()
lib_cables.agregar_cable(state.calculo_objetos.cable_conductor)
lib_cables.agregar_cable(state.calculo_objetos.cable_guardia)
if state.calculo_objetos.cable_guardia2:
    lib_cables.agregar_cable(state.calculo_objetos.cable_guardia2)

# Pasar lib_cables para resolver cable_id
estructura_geometria.importar_nodos_editados(nodos_editados, lib_cables)
```

**Archivo**: `EstructuraAEA_Geometria.py`  
**Método**: `importar_nodos_editados()` (línea ~660)

```python
# Resolver cable_id a objeto Cable_AEA
if nodo_dict.get("cable_id") and lib_cables:
    cable = lib_cables.obtener_cable(nodo_dict["cable_id"])  # "Al/Ac 70/12" → objeto Cable_AEA
    nodo.cable_asociado = cable  # Asignar objeto completo al nodo
```

**Resultado**: Cada nodo tiene `nodo.cable_asociado` como objeto `Cable_AEA` completo con todas sus propiedades:
- `peso_unitario_dan_m` (peso por metro)
- `diametro_total_mm` (diámetro)
- `carga_rotura_minima_dan` (resistencia)
- Método `_calcular_peso_hielo(t_hielo)` (peso con hielo)

---

### 3. Asignación de Cargas por Nodo (DME)

**Archivo**: `EstructuraAEA_Mecanica.py`  
**Método**: `asignar_cargas_hipotesis()` (línea ~240)

#### 3.1 Conductores

```python
for nodo_nombre in nodos_conductor:
    # Obtener cable específico del nodo o usar global
    nodo_obj = self.geometria.nodos.get(nodo_nombre)
    if nodo_obj and nodo_obj.cable_asociado:
        # USAR CABLE ESPECÍFICO DEL NODO
        peso_conductor_base = nodo_obj.cable_asociado.peso_unitario_dan_m
        peso_hielo_conductor = nodo_obj.cable_asociado._calcular_peso_hielo(t_hielo)
    else:
        # Fallback: usar cable global
        peso_conductor_base = peso_conductor_base_global
        peso_hielo_conductor = peso_hielo_conductor_global
    
    # Calcular peso del conductor para ESTE nodo
    if config["peso"]["hielo"]:
        peso_cond = (peso_conductor_base + peso_hielo_conductor) * vano * factor_peso
    else:
        peso_cond = peso_conductor_base * vano * factor_peso
    
    # Asignar peso Z
    peso_z = -peso_cond * factor_peso_nodo
```

#### 3.2 Guardias

```python
for nodo_nombre in nodos_guardia:
    # Obtener cable específico del nodo o usar lógica global
    nodo_obj = self.geometria.nodos.get(nodo_nombre)
    if nodo_obj and nodo_obj.cable_asociado:
        # USAR CABLE ESPECÍFICO DEL NODO
        peso_guardia1_base = nodo_obj.cable_asociado.peso_unitario_dan_m
        peso_hielo_guardia1 = nodo_obj.cable_asociado._calcular_peso_hielo(t_hielo)
        tiro_guardia_base = tiro_guardia1_base
        sufijo_viento = "1"
    else:
        # Lógica global original (HG1 vs HG2)
        if nodo_nombre == "HG1" or nodes_dict[nodo_nombre][0] > 0:
            peso_guardia1_base = peso_guardia1_base_global
            tiro_guardia_base = tiro_guardia1_base
        else:
            peso_guardia1_base = peso_guardia2_base
            tiro_guardia_base = tiro_guardia2_base
    
    # Calcular peso del guardia para ESTE nodo
    if config["peso"]["hielo"]:
        peso_guardia = (peso_guardia1_base + peso_hielo_guardia1) * vano * factor_peso
    else:
        peso_guardia = peso_guardia1_base * vano * factor_peso
    
    # Asignar peso Z
    peso_z = -peso_guardia * factor_peso_nodo
```

---

### 4. Tipos de Cargas Calculadas

Para cada nodo, se calculan 3 tipos de cargas:

#### 4.1 Peso (Gravedad)
- **Fuente**: `cable_asociado.peso_unitario_dan_m`
- **Fórmula**: `peso = peso_unitario * vano * factor_peso`
- **Con hielo**: `peso = (peso_unitario + peso_hielo) * vano * factor_peso`
- **Componentes**: `(0, 0, -peso)` (solo Z negativo)

#### 4.2 Viento
- **Fuente**: DataFrame de cargas totales (calculado en CMC)
- **Depende de**: Diámetro del cable, velocidad del viento, dirección
- **Componentes**: `(viento_x, viento_y, 0)` según dirección (transversal, longitudinal, oblicua)

#### 4.3 Tiro
- **Fuente**: Resultados CMC (tensión del cable en estado climático)
- **Depende de**: Ángulo de quiebre, patrón de tiro (bilateral, unilateral, dos-unilaterales)
- **Componentes**: `(tiro_trans, tiro_long, 0)` según geometría

---

### 5. Almacenamiento de Cargas en Nodos

Las cargas se guardan en el objeto `NodoEstructural`:

```python
# Cargas separadas por tipo
nodo_obj.obtener_carga("Peso").agregar_hipotesis(nombre_hipotesis, peso_x, peso_y, peso_z)
nodo_obj.obtener_carga("Viento").agregar_hipotesis(nombre_hipotesis, viento_x, viento_y, viento_z)
nodo_obj.obtener_carga("Tiro").agregar_hipotesis(nombre_hipotesis, tiro_x, tiro_y, tiro_z)

# Carga total (compatibilidad)
carga_total_x = peso_x + viento_x + tiro_x
carga_total_y = peso_y + viento_y + tiro_y
carga_total_z = peso_z + viento_z + tiro_z
nodo_obj.cargas_dict[nombre_hipotesis] = [carga_total_x, carga_total_y, carga_total_z]
```

---

## Ejemplo Práctico

### Estructura con 2 Cables Diferentes

```json
{
  "cable_conductor_id": "Al/Ac 435/55",
  "cable_guardia_id": "OPGW FiberHome 24FO 58mm2",
  "nodos_editados": [
    {
      "nombre": "C1_R",
      "cable_id": "Al/Ac 70/12"  // Cable DIFERENTE al global
    },
    {
      "nombre": "C2_R",
      "cable_id": "Al/Ac 435/55"  // Cable IGUAL al global
    },
    {
      "nombre": "HG1",
      "cable_id": "OPGW FiberHome 24FO 58mm2"
    }
  ]
}
```

### Resultado de Cargas

**Hipótesis A0 (Peso sin viento)**:

| Nodo | Cable | Peso Unitario | Peso Total (150m vano) |
|------|-------|---------------|------------------------|
| C1_R | Al/Ac 70/12 | 0.283 daN/m | -42.45 daN |
| C2_R | Al/Ac 435/55 | 1.653 daN/m | -247.95 daN |
| HG1 | OPGW 24FO | 0.580 daN/m | -87.00 daN |

**Antes de la mejora**: Todos los conductores usaban 1.653 daN/m (cable global)  
**Después de la mejora**: Cada nodo usa su cable específico

---

## Ventajas del Sistema Mejorado

1. **Flexibilidad**: Diferentes nodos pueden tener diferentes cables
2. **Precisión**: Cargas calculadas con propiedades exactas de cada cable
3. **Compatibilidad**: Fallback a cables globales si no hay `cable_asociado`
4. **Trazabilidad**: Cada nodo sabe qué cable tiene asignado
5. **Validación**: Posible verificar que cables asignados existen en biblioteca

---

## Verificación de Cargas

Para consultar las cargas de un nodo después de DME:

```python
from utils.consultar_cargas_nodos import consultar_cargas_nodo, imprimir_cargas_nodo

# Consultar cargas de un nodo específico
cargas = consultar_cargas_nodo(estructura_mecanica, "C1_R")
imprimir_cargas_nodo(cargas)

# Ver en modal de DME
# Botón "Cargas en Nodos" → Tabla con todas las cargas por hipótesis
```

---

## Archivos Modificados

1. **`EstructuraAEA_Mecanica.py`**: Método `asignar_cargas_hipotesis()` usa `nodo.cable_asociado`
2. **`EstructuraAEA_Geometria.py`**: Método `importar_nodos_editados()` resuelve `cable_id`
3. **`controllers/geometria_controller.py`**: Función `aplicar_nodos_editados()` pasa `lib_cables`

---

## Limitaciones Actuales

1. **Tiro**: Actualmente usa tiro del cable global (no hay resultados CMC por nodo)
2. **Viento**: Usa códigos de viento del cable global (no recalcula por cable específico)
3. **Solución futura**: Ejecutar CMC por cada cable único y usar resultados específicos

---

## Conclusión

El sistema ahora respeta el `cable_id` asignado a cada nodo editado, calculando cargas de peso correctamente según las propiedades del cable específico. Esto permite diseños más flexibles donde diferentes nodos pueden usar diferentes cables según necesidades del proyecto.
