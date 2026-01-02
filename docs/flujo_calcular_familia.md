# Flujo Completo: Botón "Calcular Familia"

## Resumen Ejecutivo

Al presionar "Calcular Familia", los datos fluyen desde la tabla visual → conversión a formato familia → ejecución secuencial de cálculos por estructura → generación de resultados con pestañas.

---

## Flujo Detallado Paso a Paso

### 1. ORIGEN: Vista Familia (Tabla Visual)

**Archivo**: `components/vista_familia_estructuras.py`

**Componentes clave**:
- `input-nombre-familia`: Campo de texto con nombre de familia
- `tabla-familia`: DataTable con columnas `[Parámetro, Símbolo, Unidad, Descripción, Estr.1, Estr.2, ...]`
- `btn-calcular-familia`: Botón que dispara el cálculo

**Datos en tabla**:
```python
tabla_data = [
    {
        "categoria": "General",
        "parametro": "TITULO",
        "simbolo": "TÍTULO",
        "unidad": "-",
        "descripcion": "Título de la estructura",
        "tipo": "str",
        "Estr.1": "Estructura 1",
        "Estr.2": "Estructura 2",
        # ... más columnas Estr.N
    },
    {
        "categoria": "General",
        "parametro": "cantidad",
        "simbolo": "CANT",
        "unidad": "unidades",
        "descripcion": "Cantidad de estructuras",
        "tipo": "int",
        "Estr.1": 5,
        "Estr.2": 3,
    },
    # ... más filas de parámetros
]
```

**Columnas**:
```python
columnas = [
    {"name": "Parámetro", "id": "parametro"},
    {"name": "Símbolo", "id": "simbolo"},
    {"name": "Unidad", "id": "unidad"},
    {"name": "Descripción", "id": "descripcion"},
    {"name": "Estr.1", "id": "Estr.1"},
    {"name": "Estr.2", "id": "Estr.2"},
    # ... más columnas Estr.N
]
```

---

### 2. CALLBACK: Captura del Click

**Archivo**: `controllers/familia_controller.py`

**Función**: `calcular_familia_completa()`

**Inputs**:
- `Input("btn-calcular-familia", "n_clicks")` - Trigger del botón
- `State("input-nombre-familia", "value")` - Nombre de familia (ej: "Familia_Prueba")
- `State("tabla-familia", "data")` - Lista de diccionarios con todos los datos
- `State("tabla-familia", "columns")` - Lista de definiciones de columnas

**Validación inicial**:
```python
if n_clicks is None:
    raise dash.exceptions.PreventUpdate

if not nombre_familia or not tabla_data or not columnas:
    return (no_update, True, "Error", "Faltan datos para calcular", "danger", "danger")
```

---

### 3. CONVERSIÓN: Tabla → Formato Familia

**Archivo**: `utils/familia_manager.py`

**Función**: `FamiliaManager.tabla_a_familia(tabla_data, columnas, nombre_familia)`

**Proceso**:

1. **Extraer columnas de estructura**:
```python
columnas_estructura = [col['id'] for col in columnas if col['id'].startswith('Estr.')]
# Resultado: ['Estr.1', 'Estr.2', 'Estr.3', ...]
```

2. **Construir diccionario por estructura**:
```python
estructuras = {}
for col_id in columnas_estructura:  # Para cada Estr.N
    estructura_data = {}
    
    for fila in tabla_data:  # Para cada parámetro
        parametro = fila['parametro']  # ej: "TITULO", "L_vano", "TENSION"
        valor = fila.get(col_id, fila.get('valor', ''))  # Valor de esa columna
        tipo = fila.get('tipo', 'str')
        
        # Conversión de tipos
        if tipo == 'int':
            valor = int(valor)
        elif tipo == 'float':
            valor = float(valor)
        elif tipo == 'bool':
            valor = bool(valor)
        
        estructura_data[parametro] = valor
    
    estructuras[col_id] = estructura_data
```

3. **Formato final**:
```python
familia_data = {
    "nombre_familia": "Familia_Prueba",
    "fecha_creacion": "2025-01-15T10:30:00",
    "fecha_modificacion": "2025-01-15T10:30:00",
    "estructuras": {
        "Estr.1": {
            "TITULO": "Estructura 1",
            "cantidad": 5,
            "TENSION": 220,
            "L_vano": 400,
            "TIPO_ESTRUCTURA": "Suspensión",
            # ... todos los parámetros
        },
        "Estr.2": {
            "TITULO": "Estructura 2",
            "cantidad": 3,
            "TENSION": 220,
            "L_vano": 500,
            "TIPO_ESTRUCTURA": "Retención",
            # ... todos los parámetros
        },
        # ... más estructuras
    }
}
```

---

### 4. EJECUCIÓN: Cálculo Familia Completa

**Archivo**: `utils/calcular_familia_logica_encadenada.py`

**Función**: `ejecutar_calculo_familia_completa(familia_data)`

**Input**: `familia_data` (Dict) - Datos de familia ya convertidos desde tabla

**NO carga desde archivo** - Usa los datos pasados directamente

```python
estructuras = familia_data.get("estructuras", {})
resultados_familia = {}
costos_individuales = {}

for nombre_estr, datos_estr in estructuras.items():
    # nombre_estr: "Estr.1", "Estr.2", etc.
    # datos_estr: {"TITULO": "...", "cantidad": 5, "TENSION": 220, ...}
    
    titulo = datos_estr.get("TITULO", nombre_estr)
    cantidad = datos_estr.get("cantidad", 1)
    
    # Ejecutar secuencia completa para esta estructura
    resultado_estr = _ejecutar_secuencia_estructura(datos_estr, titulo)
```

---

### 5. SECUENCIA: Cálculo Individual por Estructura

**Función**: `_ejecutar_secuencia_estructura(datos_estructura, titulo)`

#### 5.1 Crear Archivos Temporales

```python
# Crear archivos temporales completos
archivo_estructura = DATA_DIR / f"{titulo}.estructura.json"
archivo_hipotesis = DATA_DIR / f"{titulo}.hipotesismaestro.json"

# Guardar .estructura.json temporal
with open(archivo_estructura, 'w', encoding='utf-8') as f:
    json.dump(datos_estructura, f, indent=2, ensure_ascii=False)

# Crear .hipotesismaestro.json temporal
from HipotesisMaestro_Especial import hipotesis_maestro
with open(archivo_hipotesis, 'w', encoding='utf-8') as f:
    json.dump(hipotesis_maestro, f, indent=2, ensure_ascii=False)
```

**¿Por qué archivos temporales?**
- Los módulos de cálculo (CMC, DGE, DME, etc.) esperan archivos `.estructura.json` y `.hipotesismaestro.json`
- Se crean temporalmente para cada estructura de la familia
- Se eliminan al finalizar el cálculo

#### 5.2 Crear AppState

```python
state = AppState()
state.set_estructura_actual(datos_estructura)
```

#### 5.3 Ejecutar Secuencia Encadenada

**Orden**: CMC → DGE → DME → Árboles → SPH → Fundación → Costeo

```python
resultados = {}
costo_total = 0

# 1. CMC (Cálculo Mecánico de Cables)
from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
resultado_cmc = ejecutar_calculo_cmc_automatico(datos_estructura, state)
if resultado_cmc.get('exito'):
    resultados["cmc"] = CalculoCache.cargar_calculo_cmc(titulo)
else:
    return {"exito": False, "mensaje": f"Error CMC: {resultado_cmc.get('mensaje')}"}

# 2. DGE (Diseño Geométrico de Estructura)
from controllers.geometria_controller import ejecutar_calculo_dge
resultado_dge = ejecutar_calculo_dge(datos_estructura, state)
if resultado_dge.get('exito'):
    resultados["dge"] = CalculoCache.cargar_calculo_dge(titulo)
else:
    return {"exito": False, "mensaje": f"Error DGE: {resultado_dge.get('mensaje')}"}

# 3. DME (Diseño Mecánico de Estructura)
from controllers.ejecutar_calculos import ejecutar_calculo_dme
resultado_dme = ejecutar_calculo_dme(datos_estructura, state)
if resultado_dme.get('exito'):
    resultados["dme"] = CalculoCache.cargar_calculo_dme(titulo)
else:
    return {"exito": False, "mensaje": f"Error DME: {resultado_dme.get('mensaje')}"}

# 4. Árboles de Carga
from controllers.ejecutar_calculos import ejecutar_calculo_arboles
resultado_arboles = ejecutar_calculo_arboles(datos_estructura, state)
if resultado_arboles.get('exito'):
    resultados["arboles"] = CalculoCache.cargar_calculo_arboles(titulo)
else:
    return {"exito": False, "mensaje": f"Error Árboles: {resultado_arboles.get('mensaje')}"}

# 5. SPH (Selección de Poste de Hormigón)
from controllers.ejecutar_calculos import ejecutar_calculo_sph
resultado_sph = ejecutar_calculo_sph(datos_estructura, state)
if resultado_sph.get('exito'):
    resultados["sph"] = CalculoCache.cargar_calculo_sph(titulo)
else:
    return {"exito": False, "mensaje": f"Error SPH: {resultado_sph.get('mensaje')}"}

# 6. Fundación
from controllers.ejecutar_calculos import ejecutar_calculo_fundacion
resultado_fundacion = ejecutar_calculo_fundacion(datos_estructura, state)
if resultado_fundacion.get('exito'):
    resultados["fundacion"] = CalculoCache.cargar_calculo_fund(titulo)
else:
    return {"exito": False, "mensaje": f"Error Fundación: {resultado_fundacion.get('mensaje')}"}

# 7. Costeo
from controllers.ejecutar_calculos import ejecutar_calculo_costeo
resultado_costeo = ejecutar_calculo_costeo(datos_estructura, state)
if resultado_costeo.get('exito'):
    calculo_costeo = CalculoCache.cargar_calculo_costeo(titulo)
    resultados["costeo"] = calculo_costeo
    # Extraer costo total
    if calculo_costeo and "resultados" in calculo_costeo:
        costo_total = calculo_costeo["resultados"].get("costo_total", 0)
else:
    return {"exito": False, "mensaje": f"Error Costeo: {resultado_costeo.get('mensaje')}"}
```

#### 5.4 Limpiar Archivos Temporales

```python
finally:
    # Eliminar archivos temporales
    if archivo_estructura.exists():
        archivo_estructura.unlink()
    if archivo_hipotesis.exists():
        archivo_hipotesis.unlink()
```

#### 5.5 Retornar Resultados de Estructura

```python
return {
    "exito": True,
    "resultados": resultados,  # Dict con CMC, DGE, DME, Árboles, SPH, Fundación, Costeo
    "costo_total": costo_total  # Float con costo total de esta estructura
}
```

---

### 6. CONSOLIDACIÓN: Resultados de Familia

**Función**: `ejecutar_calculo_familia_completa()` (continuación)

```python
# Después de procesar todas las estructuras
for nombre_estr, datos_estr in estructuras.items():
    titulo = datos_estr.get("TITULO", nombre_estr)
    cantidad = datos_estr.get("cantidad", 1)
    
    resultado_estr = _ejecutar_secuencia_estructura(datos_estr, titulo)
    
    if resultado_estr["exito"]:
        resultados_familia[nombre_estr] = {
            "titulo": titulo,
            "cantidad": cantidad,
            "resultados": resultado_estr["resultados"],  # CMC, DGE, DME, etc.
            "costo_individual": resultado_estr.get("costo_total", 0)
        }
        costos_individuales[titulo] = resultado_estr.get("costo_total", 0)
```

**Formato de `resultados_familia`**:
```python
{
    "Estr.1": {
        "titulo": "Estructura 1",
        "cantidad": 5,
        "resultados": {
            "cmc": {...},      # Resultado completo de CMC
            "dge": {...},      # Resultado completo de DGE
            "dme": {...},      # Resultado completo de DME
            "arboles": {...},  # Resultado completo de Árboles
            "sph": {...},      # Resultado completo de SPH
            "fundacion": {...},# Resultado completo de Fundación
            "costeo": {...}    # Resultado completo de Costeo
        },
        "costo_individual": 15000.50
    },
    "Estr.2": {
        "titulo": "Estructura 2",
        "cantidad": 3,
        "resultados": {...},
        "costo_individual": 18500.75
    },
    # ... más estructuras
}
```

---

### 7. COSTEO GLOBAL: Familia Completa

**Función**: `_generar_costeo_familia(resultados_familia)`

```python
costo_global = 0
costos_parciales = {}
costos_individuales = {}

for nombre_estr, datos in resultados_familia.items():
    if "error" not in datos:
        titulo = datos["titulo"]
        cantidad = datos["cantidad"]
        costo_individual = datos["costo_individual"]
        costo_parcial = costo_individual * cantidad  # Costo × Cantidad
        
        costos_individuales[titulo] = costo_individual
        costos_parciales[titulo] = costo_parcial
        costo_global += costo_parcial

return {
    "costo_global": costo_global,  # Suma de todos los costos parciales
    "costos_individuales": costos_individuales,  # Costo unitario por estructura
    "costos_parciales": costos_parciales  # Costo × cantidad por estructura
}
```

**Ejemplo**:
```python
{
    "costo_global": 131002.75,
    "costos_individuales": {
        "Estructura 1": 15000.50,
        "Estructura 2": 18500.75
    },
    "costos_parciales": {
        "Estructura 1": 75002.50,  # 15000.50 × 5
        "Estructura 2": 55502.25   # 18500.75 × 3
    }
}
```

---

### 8. GRÁFICOS: Visualización de Familia

**Función**: `_generar_graficos_familia(resultados_familia)`

#### 8.1 Gráfico de Barras (Costos Individuales)

```python
# Ordenar de mayor a menor
titulos_ordenados = sorted(costos_individuales.keys(), 
                          key=lambda x: costos_individuales[x], reverse=True)

fig_barras = go.Figure(data=[
    go.Bar(
        x=titulos_ordenados,
        y=[costos_individuales[t] for t in titulos_ordenados],
        name="Costo Individual"
    )
])
fig_barras.update_layout(
    title="Costos Individuales por Estructura",
    xaxis_title="Estructura",
    yaxis_title="Costo [UM]"
)
```

#### 8.2 Gráfico de Torta (Costos Parciales)

```python
fig_torta = go.Figure(data=[
    go.Pie(
        labels=list(costos_parciales.keys()),
        values=list(costos_parciales.values()),
        name="Costo Parcial"
    )
])
fig_torta.update_layout(
    title="Distribución de Costos Parciales (Individual × Cantidad)"
)
```

---

### 9. VISTA: Generación de Pestañas

**Función**: `generar_vista_resultados_familia(resultados_familia)`

**Estructura de pestañas**:
```python
pestanas = [
    dbc.Tab(label="Estructura 1", tab_id="tab-Estr.1"),
    dbc.Tab(label="Estructura 2", tab_id="tab-Estr.2"),
    # ... más pestañas por estructura
    dbc.Tab(label="Costeo Familia", tab_id="tab-costeo-familia")
]
```

**Contenido por pestaña**:

#### 9.1 Pestaña de Estructura Individual

```python
def _crear_contenido_estructura(datos_estructura):
    componentes = []
    
    # CMC
    if "cmc" in resultados:
        componentes.append(html.H4("Cálculo Mecánico de Cables"))
        cmc_lista = generar_resultados_cmc_lista(resultados["cmc"], {})
        componentes.extend(cmc_lista)
    
    # DGE
    if "dge" in resultados:
        componentes.append(html.H4("Diseño Geométrico"))
        componentes.append(generar_resultados_dge(resultados["dge"], {}))
    
    # DME, Árboles, SPH, Fundación, Costeo...
    # (similar para cada módulo)
    
    return html.Div(componentes)
```

#### 9.2 Pestaña de Costeo Familia

```python
def _crear_contenido_costeo_familia(costeo_global, graficos_familia):
    return html.Div([
        html.H4("Costeo Global de Familia"),
        
        # Resumen
        dbc.Card([
            html.H5("Costo Global de Familia"),
            html.H3(f"{costeo_global['costo_global']:,.2f} UM")
        ]),
        
        # Gráfico de barras
        dcc.Graph(figure=graficos_familia["grafico_barras"]),
        
        # Gráfico de torta
        dcc.Graph(figure=graficos_familia["grafico_torta"])
    ])
```

---

### 10. RETORNO: Callback Final

**Archivo**: `controllers/familia_controller.py`

```python
return (
    vista_resultados,  # Output: resultados-familia (children)
    True,              # Output: toast-notificacion (is_open)
    "Éxito",           # Output: toast-notificacion (header)
    "Cálculo de familia completado",  # Output: toast-notificacion (children)
    "success",         # Output: toast-notificacion (icon)
    "success"          # Output: toast-notificacion (color)
)
```

---

## Diagrama de Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. VISTA: tabla-familia (DataTable)                             │
│    - Columnas: [Parámetro, Símbolo, Unidad, Desc, Estr.1, ...] │
│    - Filas: [{parametro: "TITULO", Estr.1: "...", ...}, ...]   │
└────────────────────────┬────────────────────────────────────────┘
                         │ Click btn-calcular-familia
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CALLBACK: calcular_familia_completa()                        │
│    Inputs: nombre_familia, tabla_data, columnas                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. CONVERSIÓN: FamiliaManager.tabla_a_familia()                 │
│    tabla_data → familia_data                                    │
│    {                                                             │
│      "nombre_familia": "...",                                   │
│      "estructuras": {                                           │
│        "Estr.1": {TITULO: "...", cantidad: 5, ...},            │
│        "Estr.2": {TITULO: "...", cantidad: 3, ...}             │
│      }                                                           │
│    }                                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. EJECUCIÓN: ejecutar_calculo_familia_completa()               │
│    Para cada estructura en familia_data["estructuras"]:         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SECUENCIA: _ejecutar_secuencia_estructura()                  │
│    ┌──────────────────────────────────────────────────────────┐│
│    │ 5.1 Crear archivos temporales:                           ││
│    │     - {titulo}.estructura.json                           ││
│    │     - {titulo}.hipotesismaestro.json                     ││
│    └──────────────────────────────────────────────────────────┘│
│    ┌──────────────────────────────────────────────────────────┐│
│    │ 5.2 Crear AppState con datos_estructura                  ││
│    └──────────────────────────────────────────────────────────┘│
│    ┌──────────────────────────────────────────────────────────┐│
│    │ 5.3 Ejecutar secuencia encadenada:                       ││
│    │     CMC → DGE → DME → Árboles → SPH → Fundación → Costeo││
│    │     Cada módulo guarda cache: {titulo}.calculoXXX.json  ││
│    └──────────────────────────────────────────────────────────┘│
│    ┌──────────────────────────────────────────────────────────┐│
│    │ 5.4 Cargar resultados desde cache                        ││
│    │     resultados = {cmc: {...}, dge: {...}, ...}          ││
│    └──────────────────────────────────────────────────────────┘│
│    ┌──────────────────────────────────────────────────────────┐│
│    │ 5.5 Limpiar archivos temporales                          ││
│    └──────────────────────────────────────────────────────────┘│
│    ┌──────────────────────────────────────────────────────────┐│
│    │ 5.6 Retornar: {exito, resultados, costo_total}          ││
│    └──────────────────────────────────────────────────────────┘│
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. CONSOLIDACIÓN: resultados_familia                            │
│    {                                                             │
│      "Estr.1": {                                                │
│        titulo: "...", cantidad: 5,                              │
│        resultados: {cmc, dge, dme, arboles, sph, fund, costeo},│
│        costo_individual: 15000.50                               │
│      },                                                          │
│      "Estr.2": {...}                                            │
│    }                                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. COSTEO GLOBAL: _generar_costeo_familia()                     │
│    {                                                             │
│      costo_global: 131002.75,                                   │
│      costos_individuales: {Estr1: 15000.50, Estr2: 18500.75},  │
│      costos_parciales: {Estr1: 75002.50, Estr2: 55502.25}      │
│    }                                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. GRÁFICOS: _generar_graficos_familia()                        │
│    - Gráfico de barras (costos individuales, mayor a menor)    │
│    - Gráfico de torta (costos parciales = individual × cantidad)│
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. VISTA: generar_vista_resultados_familia()                    │
│    Pestañas:                                                     │
│    - [Estructura 1] → Contenido: CMC, DGE, DME, Árboles, SPH,  │
│                       Fundación, Costeo                          │
│    - [Estructura 2] → Contenido: CMC, DGE, DME, ...            │
│    - [Costeo Familia] → Resumen + Gráficos                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. RETORNO: Callback devuelve vista_resultados                 │
│     Output: resultados-familia (children)                        │
│     Toast: "Cálculo de familia completado"                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Archivos Involucrados

| Archivo | Rol |
|---------|-----|
| `components/vista_familia_estructuras.py` | Vista con tabla y botón |
| `controllers/familia_controller.py` | Callback que captura click |
| `utils/familia_manager.py` | Conversión tabla ↔ familia |
| `utils/calcular_familia_logica_encadenada.py` | Orquestación de cálculos |
| `controllers/geometria_controller.py` | Ejecución CMC y DGE |
| `controllers/ejecutar_calculos.py` | Ejecución DME, Árboles, SPH, Fundación, Costeo |
| `utils/calculo_cache.py` | Guardado/carga de resultados |
| `components/vista_calcular_todo.py` | Generación de vistas CMC |
| `components/vista_diseno_geometrico.py` | Generación de vistas DGE |
| `components/vista_diseno_mecanico.py` | Generación de vistas DME |
| `components/vista_arboles_carga.py` | Generación de vistas Árboles |
| `components/vista_seleccion_poste.py` | Generación de vistas SPH |
| `components/vista_fundacion.py` | Generación de vistas Fundación |
| `components/vista_costeo.py` | Generación de vistas Costeo |

---

## Puntos Clave

1. **Datos de origen**: Tabla visual con columnas `Estr.N` que contienen valores de parámetros
2. **Conversión**: `FamiliaManager.tabla_a_familia()` transforma tabla → diccionario familia
3. **Archivos temporales**: Se crean `.estructura.json` y `.hipotesismaestro.json` por estructura
4. **Secuencia encadenada**: CMC → DGE → DME → Árboles → SPH → Fundación → Costeo
5. **Cache**: Cada módulo guarda resultados en `{titulo}.calculoXXX.json`
6. **Costeo global**: Suma de `costo_individual × cantidad` por estructura
7. **Vista final**: Pestañas por estructura + pestaña de costeo familia con gráficos
