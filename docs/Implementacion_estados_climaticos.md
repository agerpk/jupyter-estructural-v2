# Implementación: Sistema de Múltiples Estados Climáticos

## Resumen Ejecutivo

Sistema de múltiples estados climáticos con IDs numéricos autogenerados (1, 2, 3...) y algoritmos inteligentes que seleccionan automáticamente el estado apropiado según criterios físicos.

---

## FASE 1: Modal de Estados Climáticos y Restricciones

### 1.1 Crear Modal Unificado

**Archivo**: `components/modal_estados_climaticos.py` (NUEVO)

**Funcionalidad**:
- Modal con tabla dinámica
- Botones: "Agregar Estado", "Copiar Estados Desde", "Guardar", "Cancelar"
- Cada fila con botón "X" para eliminar (confirmación)
- Campos por fila:
  - **ID** (numérico autogenerado, NO editable, incremental)
  - Temperatura (°C)
  - Descripción (ej: Tmáx, Tmín, Tormenta)
  - Velocidad viento (m/s)
  - Espesor hielo (m)
  - Restricción conductor (% rotura)
  - Restricción guardia (% rotura)
  - Relación de flecha (relflecha, float, default 0.9)

**Sistema de IDs**:
- IDs numéricos: 1, 2, 3, 4, 5...
- Autogenerados al agregar
- NO editables por usuario
- Si se elimina estado 3, el próximo agregado toma ID 3 (reutiliza huecos)

**Validaciones**:
- Mínimo 1 estado requerido
- Temperatura: mín -273 max 400
- Descripcion: string (sin validacion)
- Velocidad viento: float positivo
- Espesor hielo: float positivo
- Restricción conductor, restricción guardia: float positivo, max 1.0
- Relación de flecha: float positivo, sin max

---

### 1.1.1 Sub-Modal "Copiar Estados Desde"

**Archivo**: `components/modal_copiar_estados.py` (NUEVO)

**Funcionalidad**:
- Modal secundario que se abre desde "Copiar Estados Desde"
- Dropdown con lista de estructuras en DB
- Botones: "Confirmar", "Cancelar"

**Lógica de copia**:
```python
def copiar_estados_desde_estructura(estructura_origen):
    """
    Copia estados de estructura origen a actual
    
    - Si detecta IDs legacy (I, II, III, IV, V): descarta y convierte resto a numéricos
    - REEMPLAZA completamente la tabla actual (elimina todas las filas existentes)
    - Crea nueva tabla con estados copiados
    - Asigna IDs numéricos incrementales (1, 2, 3...)
    """
    estados_origen = estructura_origen.get("estados_climaticos", {})
    
    # Detectar y convertir legacy
    if any(id in ["I", "II", "III", "IV", "V"] for id in estados_origen.keys()):
        # Descartar IDs legacy, convertir resto
        estados_nuevos = {}
        nuevo_id = 1
        for id_origen, datos in estados_origen.items():
            if id_origen not in ["I", "II", "III", "IV", "V"]:
                estados_nuevos[str(nuevo_id)] = datos
                nuevo_id += 1
        return estados_nuevos
    
    # Si no es legacy, copiar directo con IDs numéricos
    estados_nuevos = {}
    nuevo_id = 1
    for datos in estados_origen.values():
        estados_nuevos[str(nuevo_id)] = datos
        nuevo_id += 1
    
    return estados_nuevos

# Ejemplo de diferencia de filas:
# Estructura actual: 3 estados (IDs 1, 2, 3)
# Estructura origen: 7 estados
# Resultado: REEMPLAZA tabla completa con 7 nuevas filas (IDs 1-7)

# Estructura actual: 10 estados (IDs 1-10)
# Estructura origen: 4 estados
# Resultado: REEMPLAZA tabla completa con 4 nuevas filas (IDs 1-4)
```
---

### 1.2 Integrar Modal en Menú y Vistas

**Archivos a modificar**:
- `components/menu.py` - Opción "Estados Climáticos y Restricciones" en Editar
- `components/vista_calculo_mecanico.py` - Botón "Editar Estados Climáticos y Restricciones"
- `components/vista_familia_estructuras.py` - Botón "Editar Estados Climáticos y Restricciones de Familia"

---

### 1.3 Controller del Modal

**Archivos**: 
- `controllers/estados_climaticos_controller.py` (NUEVO) - Para estructuras
- `controllers/estados_climaticos_familia_controller.py` (NUEVO) - Para familias

**Callbacks**:

#### Agregar estado
```python
def agregar_estado(n_clicks, estados_actuales):
    # Encontrar primer ID disponible
    ids_usados = [int(id) for id in estados_actuales.keys()]
    nuevo_id = 1
    while nuevo_id in ids_usados:
        nuevo_id += 1
    
    # Copiar datos de último estado
    ultimo_estado = list(estados_actuales.values())[-1]
    nuevo_estado = ultimo_estado.copy()
    
    estados_actuales[str(nuevo_id)] = nuevo_estado
```

#### Copiar estados desde otra estructura
```python
@app.callback(
    Output("modal-copiar-estados", "is_open"),
    Input("btn-copiar-estados-desde", "n_clicks"),
    prevent_initial_call=True
)
def abrir_modal_copiar(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    return True  # Abrir sub-modal

@app.callback(
    Output("tabla-estados-dinamica", "children", allow_duplicate=True),
    Output("modal-copiar-estados", "is_open", allow_duplicate=True),
    Input("btn-confirmar-copiar-estados", "n_clicks"),
    State("dropdown-estructuras-db", "value"),
    prevent_initial_call=True
)
def confirmar_copiar_estados(n_clicks, estructura_id):
    if not n_clicks or not estructura_id:
        raise PreventUpdate
    
    # Cargar estructura origen desde DB
    estructura_origen = cargar_estructura_desde_db(estructura_id)
    estados_origen = estructura_origen.get("estados_climaticos", {})
    
    # Detectar y convertir legacy
    if any(id in ["I", "II", "III", "IV", "V"] for id in estados_origen.keys()):
        estados_nuevos = {}
        nuevo_id = 1
        for id_origen, datos in estados_origen.items():
            if id_origen not in ["I", "II", "III", "IV", "V"]:
                estados_nuevos[str(nuevo_id)] = datos
                nuevo_id += 1
    else:
        # Copiar con IDs numéricos secuenciales
        estados_nuevos = {}
        nuevo_id = 1
        for datos in estados_origen.values():
            estados_nuevos[str(nuevo_id)] = datos
            nuevo_id += 1
    
    # REEMPLAZAR tabla completa: elimina todas las filas actuales
    # y crea nueva tabla con estados copiados
    nueva_tabla = generar_tabla_desde_estados(estados_nuevos)
    
    # Ejemplos:
    # - Tabla actual: 3 filas → Origen: 7 estados → Nueva tabla: 7 filas
    # - Tabla actual: 10 filas → Origen: 4 estados → Nueva tabla: 4 filas
    # - Tabla actual: 5 filas → Origen: 5 estados → Nueva tabla: 5 filas (datos diferentes)
    
    return nueva_tabla, False  # Actualizar tabla, cerrar sub-modal
```

#### Guardar estados (Estructura)
```python
@app.callback(
    Output("estructura-actual", "data"),
    Output("modal-estados-estructura", "is_open"),
    Output("toast-notificacion", "is_open"),
    Input("btn-guardar-estados", "n_clicks"),
    State("tabla-estados-dinamica", "children"),
    State("estructura-actual", "data")
)
def guardar_estados_estructura(n_clicks, tabla, estructura_actual):
    if not n_clicks:
        raise PreventUpdate
    
    # Extraer estados de tabla
    estados_climaticos = extraer_estados_de_tabla(tabla)
    restricciones_cables = extraer_restricciones_de_tabla(tabla)
    
    # Actualizar estructura_actual
    estructura_actual["estados_climaticos"] = estados_climaticos
    estructura_actual["restricciones_cables"] = restricciones_cables
    
    # Guardar en archivo .estructura.json
    nombre = estructura_actual.get("TITULO", "estructura")
    archivo = DATA_DIR / f"{nombre}.estructura.json"
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(estructura_actual, f, indent=2, ensure_ascii=False)
    
    return estructura_actual, False, True  # Cerrar modal, mostrar toast
```

#### Guardar estados (Familia)
```python
@app.callback(
    Output("familia-actual", "data"),
    Output("modal-estados-familia", "is_open"),
    Output("toast-notificacion", "is_open"),
    Input("btn-guardar-estados-familia", "n_clicks"),
    State("tabla-estados-dinamica", "children"),
    State("familia-actual", "data")
)
def guardar_estados_familia(n_clicks, tabla, familia_actual):
    if not n_clicks:
        raise PreventUpdate
    
    # Extraer estados de tabla
    estados_climaticos = extraer_estados_de_tabla(tabla)
    restricciones_cables = extraer_restricciones_de_tabla(tabla)
    
    # Actualizar familia_actual
    familia_actual["estados_climaticos"] = estados_climaticos
    familia_actual["restricciones_cables"] = restricciones_cables
    
    # Guardar en archivo .familia.json
    nombre = familia_actual.get("nombre", "familia")
    archivo = DATA_DIR / f"{nombre}.familia.json"
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(familia_actual, f, indent=2, ensure_ascii=False)
    
    return familia_actual, False, True  # Cerrar modal, mostrar toast
```

#### Cancelar
```python
@app.callback(
    Output("modal-estados-estructura", "is_open"),
    Input("btn-cancelar-estados", "n_clicks")
)
def cancelar_modal(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    return False  # Cerrar modal sin guardar
```

---

## FASE 2: Algoritmos Inteligentes de Selección de Estados

### 2.1 Crear Módulo de Selección Inteligente

**Archivo**: `utils/selector_estados.py` (NUEVO)

**Métodos principales**:

```python
class SelectorEstados:
    
    @staticmethod
    def buscar_max_flecha_vertical(resultados_estados):
        """Encuentra estado con máxima flecha vertical (para DGE)"""
        max_flecha = 0
        estado_max = None
        for estado_id, datos in resultados_estados.items():
            if datos.get("flecha_vertical_m", 0) > max_flecha:
                max_flecha = datos["flecha_vertical_m"]
                estado_max = estado_id
        return estado_max
    
    @staticmethod
    def buscar_max_tiro(resultados_estados):
        """Encuentra estado con máximo tiro (para hipótesis 'máximo')"""
        max_tiro = 0
        estado_max = None
        for estado_id, datos in resultados_estados.items():
            if datos.get("tiro_daN", 0) > max_tiro:
                max_tiro = datos["tiro_daN"]
                estado_max = estado_id
        return estado_max
    
    @staticmethod
    def buscar_tma_equivalente(estados_climaticos):
        """
        Busca TMA: sin viento, sin hielo, temp>0, menor temperatura
        """
        candidatos = []
        for estado_id, datos in estados_climaticos.items():
            if (datos.get("viento_velocidad", 0) == 0 and
                datos.get("espesor_hielo", 0) == 0 and
                datos.get("temperatura", 0) > 0):
                candidatos.append((estado_id, datos["temperatura"]))
        
        if not candidatos:
            # Fallback: primer estado sin viento ni hielo
            for estado_id, datos in estados_climaticos.items():
                if (datos.get("viento_velocidad", 0) == 0 and
                    datos.get("espesor_hielo", 0) == 0):
                    return estado_id
            return list(estados_climaticos.keys())[0]
        
        candidatos.sort(key=lambda x: x[1])
        return candidatos[0][0]
    
    @staticmethod
    def buscar_tmin_equivalente(estados_climaticos):
        """Temperatura mínima"""
        min_temp = float('inf')
        estado_min = None
        for estado_id, datos in estados_climaticos.items():
            if datos.get("temperatura", 0) < min_temp:
                min_temp = datos["temperatura"]
                estado_min = estado_id
        return estado_min
    
    @staticmethod
    def buscar_vmax_equivalente(estados_climaticos):
        """Máxima velocidad de viento"""
        max_viento = 0
        estado_max = None
        for estado_id, datos in estados_climaticos.items():
            if datos.get("viento_velocidad", 0) > max_viento:
                max_viento = datos["viento_velocidad"]
                estado_max = estado_id
        return estado_max
    
    @staticmethod
    def buscar_hielo_max(estados_climaticos):
        """Encuentra estado con máximo espesor de hielo ("carga adicional")"""
        max_hielo = 0
        estado_max = None
        for estado_id, datos in estados_climaticos.items():
            if datos.get("espesor_hielo", 0) > max_hielo:
                max_hielo = datos["espesor_hielo"]
                estado_max = estado_id
        return estado_max

```

---

### 2.2 Uso en Hipótesis

**Archivo**: `EstructuraAEA_Mecanica.py`

Las hipótesis referencian funciones que se resuelven dinámicamente:

```python
from utils.selector_estados import SelectorEstados

# En asignar_cargas_hipotesis():

# Obtener referencia a función desde hipótesis
estado_config = config["tiro"]["estado"]  # "buscar_tma_equivalente"

# Resolver usando getattr
if not hasattr(SelectorEstados, estado_config):
    raise ValueError(f"Función '{estado_config}' no existe en SelectorEstados")

funcion = getattr(SelectorEstados, estado_config)

# Llamar función según parámetros requeridos
if estado_config == "buscar_max_tiro":
    estado_id = funcion(resultados_conductor)  # Requiere resultados CMC
else:
    estado_id = funcion(self.geometria.estados_climaticos)  # Requiere estados
```

---

## FASE 3: Actualizar CMC (Cálculo Mecánico de Cables)

### 3.1 CalculoCables.py

**Estado**: ✅ Ya compatible (itera dinámicamente, defaults para restricciones)

---

### 3.2 Colores Dinámicos para Gráficos

**Archivo**: `utils/plot_flechas.py`

```python
def generar_colores_estados(estados_climaticos):
    """Genera colores usando colormap"""
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    
    estados_ids = sorted(estados_climaticos.keys(), key=lambda x: int(x))
    n_estados = len(estados_ids)
    
    cmap = cm.get_cmap('tab10' if n_estados <= 10 else 'tab20', n_estados)
    
    colores = {}
    for i, estado_id in enumerate(estados_ids):
        colores[estado_id] = mcolors.to_hex(cmap(i))
    
    return colores
```

---

## FASE 4: Actualizar DGE (Diseño Geométrico)

### 4.1 Selección Inteligente de Estados

**Archivo**: `EstructuraAEA_Geometria.py`

```python
from utils.selector_estados import SelectorEstados

# ANTES:
flecha_max = resultados_conductor["V"]["flecha_vertical_m"]

# DESPUÉS:
estado_max_flecha = SelectorEstados.buscar_max_flecha_vertical(resultados_conductor)
flecha_max = resultados_conductor[estado_max_flecha]["flecha_vertical_m"]
```

---

## FASE 5: Actualizar DME (Diseño Mecánico) e Hipótesis

### 5.1 Hipótesis Maestro

**Archivo**: `HipotesisMaestro_Especial.py`

**Estado**: 🔧 Requiere modificación

**Acción**: Cambiar nombres de estados por referencias a funciones de `SelectorEstados`.

```python
# ANTES (nombres hardcodeados):
"A0": {
    "tiro": {"estado": "TMA", "patron": "bilateral", ...}
}

# DESPUÉS (referencia a función):
"A0": {
    "tiro": {"estado": "buscar_tma_equivalente", "patron": "bilateral", ...}
}

# Ejemplos de referencias:
"A0": {"estado": "buscar_tma_equivalente"}      # TMA
"A1": {"estado": "buscar_vmax_equivalente"}     # Viento máximo
"A4": {"estado": "buscar_hielo_max"}            # Hielo máximo
"B2": {"estado": "buscar_tmin_equivalente"}     # Temperatura mínima
"C1": {"estado": "buscar_max_tiro"}             # Tiro máximo (requiere resultados CMC)
```

---

## FASE 6: Actualizar Familias de Estructuras

**Archivo**: `controllers/familia_controller.py`

Guardar estados en `.familia.json`. Al aplicar familia, copiar estados a estructuras miembro.

---

## FASE 7: Validación y Testing

### 7.1 Casos de Prueba

**Test 1**: Estructura con 5 estados (IDs 1-5)
```python
estados = {
    "1": {"temperatura": 35, "descripcion": "Tmáx", ...},
    "2": {"temperatura": -20, "descripcion": "Tmín", ...},
    "3": {"temperatura": 10, "descripcion": "Vmáx", ...},
    "4": {"temperatura": -5, "descripcion": "Vmed", ...},
    "5": {"temperatura": 8, "descripcion": "TMA", ...}
}
```

**Test 2**: Eliminar estado 3, agregar nuevo → toma ID 3

**Test 3**: Estado 6 con mayor flecha → DGE usa estado 6

**Test 4**: Estado 7 con mayor tiro → Hipótesis "máximo" usa estado 7

---

### 7.2 Validaciones

**Modal**:
- Mínimo 2 estados
- Campos numéricos válidos
- Restricciones entre 0 y 1
- IDs autogenerados (no editables)

**SelectorEstados**:
- Fallbacks robustos
- Manejo de casos edge

---

## FASE 8: Documentación

**Archivo**: `docs/guia_estados_climaticos.md` (NUEVO)

Guía de usuario con ejemplos.

---

## Orden de Implementación

### Prioridad 1 (Base)
1. FASE 2.1: Crear `utils/selector_estados.py`
2. FASE 2.2: Modificar `EstructuraAEA_Mecanica.py`

### Prioridad 2 (UI)
3. FASE 1.1: Crear `components/modal_estados_climaticos.py`
4. FASE 1.2: Integrar modal en menú y vistas
5. FASE 1.3: Crear `controllers/estados_climaticos_controller.py`

### Prioridad 3 (Cálculos)
6. FASE 3.2: Modificar `utils/plot_flechas.py`
7. FASE 4.1: Modificar `EstructuraAEA_Geometria.py`

### Prioridad 4 (Avanzado)
8. FASE 6: Modificar `controllers/familia_controller.py`

### Prioridad 5 (Validación)
9. FASE 7: Testing
10. FASE 8: Documentación

---

## Migración de Archivos Antiguos

### Conversión Automática

Archivos antiguos con IDs "I", "II", "III", "IV", "V" se convierten a "1", "2", "3", "4", "5":

```python
def migrar_estados_antiguos(estados_antiguos):
    """Convierte IDs romanos a numéricos"""
    mapeo = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5"}
    estados_nuevos = {}
    
    for id_antiguo, datos in estados_antiguos.items():
        id_nuevo = mapeo.get(id_antiguo, id_antiguo)
        estados_nuevos[id_nuevo] = datos
    
    return estados_nuevos
```

---

## Impacto en Módulos

### Sin modificación (2)
- ✅ `CalculoCables.py` - Ya compatible
- ✅ Módulos que usan resultados de DME

### Modificación menor (5)
- 🔧 `utils/plot_flechas.py` - Colores dinámicos
- 🔧 `EstructuraAEA_Geometria.py` - Selector max flecha
- 🔧 `EstructuraAEA_Mecanica.py` - Selector resolver estados
- 🔧 `HipotesisMaestro_Especial.py` - Eliminar nombres de estados
- 🔧 `controllers/familia_controller.py` - Estados en familias

### Creación nueva (4)
- ➕ `utils/selector_estados.py`
- ➕ `components/modal_estados_climaticos.py`
- ➕ `components/modal_copiar_estados.py`
- ➕ `controllers/estados_climaticos_controller.py`

---

## Resumen de Archivos

**Nuevos (4)**:
1. `utils/selector_estados.py`
2. `components/modal_estados_climaticos.py`
3. `components/modal_copiar_estados.py`
4. `controllers/estados_climaticos_controller.py`

**Modificados (8)**:
1. `components/menu.py`
2. `components/vista_calculo_mecanico.py`
3. `components/vista_familia_estructuras.py`
4. `utils/plot_flechas.py`
5. `EstructuraAEA_Geometria.py`
6. `EstructuraAEA_Mecanica.py`
7. `HipotesisMaestro_Especial.py`
8. `controllers/familia_controller.py`

**Sin cambios (2)**:
1. `CalculoCables.py`
2. Módulos que usan resultados de DME

---

**Fecha**: 2024-01-15  
**Versión**: 2.0  
**Estado**: Diseño completo - IDs numéricos autogenerados
