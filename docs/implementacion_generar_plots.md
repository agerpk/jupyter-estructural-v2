# Plan de Implementación: Parámetro generar_plots

## Objetivo
Agregar parámetro opcional `generar_plots=True` para desactivar generación de gráficos 2D/3D en cálculos de vano económico, acelerando el proceso sin afectar familias ni calcular todo.

## Estrategia
- Parámetro opcional con default `True` → no afecta código existente
- Solo vano económico pasa `False` → acelera su ejecución
- Familias y calcular todo usan default `True` → mantienen comportamiento actual

---

## Archivos a Modificar

### 1. utils/vano_economico_utils.py
**Línea:** ~95  
**Función:** `calcular_vano_economico_iterativo()`  
**Cambio:**
```python
# ANTES
resultado = ejecutar_calculo_familia_completa(familia_modificada)

# DESPUÉS
resultado = ejecutar_calculo_familia_completa(familia_modificada, generar_plots=False)
```

---

### 2. utils/calcular_familia_logica_encadenada.py

#### 2.1 Función principal
**Línea:** ~13  
**Función:** `ejecutar_calculo_familia_completa()`  
**Cambio:**
```python
# ANTES
def ejecutar_calculo_familia_completa(familia_data: Dict) -> Dict:

# DESPUÉS
def ejecutar_calculo_familia_completa(familia_data: Dict, generar_plots: bool = True) -> Dict:
```

**Línea:** ~50 (dentro de la función)  
**Cambio:**
```python
# ANTES
resultado_estr = _ejecutar_secuencia_estructura(datos_estr, titulo)

# DESPUÉS
resultado_estr = _ejecutar_secuencia_estructura(datos_estr, titulo, generar_plots)
```

#### 2.2 Función de secuencia
**Línea:** ~95  
**Función:** `_ejecutar_secuencia_estructura()`  
**Cambio:**
```python
# ANTES
def _ejecutar_secuencia_estructura(datos_estructura: Dict, titulo: str) -> Dict:

# DESPUÉS
def _ejecutar_secuencia_estructura(datos_estructura: Dict, titulo: str, generar_plots: bool = True) -> Dict:
```

**Líneas:** ~130-180 (dentro de la función)  
**Cambios:**
```python
# ANTES
resultado_cmc = ejecutar_calculo_cmc_automatico(datos_estructura, state)
resultado_dge = ejecutar_calculo_dge(datos_estructura, state)
resultado_dme = ejecutar_calculo_dme(datos_estructura, state)
resultado_arboles = ejecutar_calculo_arboles(datos_estructura, state)
resultado_fundacion = ejecutar_calculo_fundacion(datos_estructura, state)

# DESPUÉS
resultado_cmc = ejecutar_calculo_cmc_automatico(datos_estructura, state, generar_plots)
resultado_dge = ejecutar_calculo_dge(datos_estructura, state, generar_plots)
resultado_dme = ejecutar_calculo_dme(datos_estructura, state, generar_plots)
resultado_arboles = ejecutar_calculo_arboles(datos_estructura, state, generar_plots)
resultado_fundacion = ejecutar_calculo_fundacion(datos_estructura, state, generar_plots)
```

---

### 3. controllers/geometria_controller.py

#### 3.1 Función CMC
**Línea:** ~180  
**Función:** `ejecutar_calculo_cmc_automatico()`  
**Cambio firma:**
```python
# ANTES
def ejecutar_calculo_cmc_automatico(estructura_actual, state):

# DESPUÉS
def ejecutar_calculo_cmc_automatico(estructura_actual, state, generar_plots=True):
```

**Líneas:** ~240-260 (generación de gráficos)  
**Cambio:**
```python
# ANTES
from utils.plot_flechas import crear_grafico_flechas

fig_combinado, fig_conductor, fig_guardia1, fig_guardia2 = None, None, None, None
try:
    if state.calculo_mecanico.resultados_guardia2:
        fig_combinado, fig_conductor, fig_guardia1, fig_guardia2 = crear_grafico_flechas(...)
    else:
        fig_combinado, fig_conductor, fig_guardia1 = crear_grafico_flechas(...)
except Exception as e:
    print(f"Error generando gráficos: {e}")
    pass

# DESPUÉS
fig_combinado, fig_conductor, fig_guardia1, fig_guardia2 = None, None, None, None
if generar_plots:
    try:
        from utils.plot_flechas import crear_grafico_flechas
        if state.calculo_mecanico.resultados_guardia2:
            fig_combinado, fig_conductor, fig_guardia1, fig_guardia2 = crear_grafico_flechas(...)
        else:
            fig_combinado, fig_conductor, fig_guardia1 = crear_grafico_flechas(...)
    except Exception as e:
        print(f"Error generando gráficos: {e}")
        pass
```

#### 3.2 Función DGE
**Línea:** ~20  
**Función:** `ejecutar_calculo_dge()`  
**Cambio firma:**
```python
# ANTES
def ejecutar_calculo_dge(estructura_actual, state):

# DESPUÉS
def ejecutar_calculo_dge(estructura_actual, state, generar_plots=True):
```

**Líneas:** ~110-140 (generación de gráficos)  
**Cambio:**
```python
# ANTES
estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica_temp)

estructura_graficos.graficar_estructura(...)
fig_estructura = plt.gcf()

estructura_graficos.graficar_cabezal(...)
fig_cabezal = plt.gcf()

fig_nodos = estructura_graficos.graficar_nodos_coordenadas(...)

# DESPUÉS
if generar_plots:
    estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica_temp)
    
    estructura_graficos.graficar_estructura(...)
    fig_estructura = plt.gcf()
    
    estructura_graficos.graficar_cabezal(...)
    fig_cabezal = plt.gcf()
    
    fig_nodos = estructura_graficos.graficar_nodos_coordenadas(...)
else:
    fig_estructura = None
    fig_cabezal = None
    fig_nodos = None
```

---

### 4. controllers/ejecutar_calculos.py

#### 4.1 Función DME
**Línea:** ~3  
**Función:** `ejecutar_calculo_dme()`  
**Cambio firma:**
```python
# ANTES
def ejecutar_calculo_dme(estructura_actual, state):

# DESPUÉS
def ejecutar_calculo_dme(estructura_actual, state, generar_plots=True):
```

**Líneas:** ~35-45 (generación de gráficos)  
**Cambio:**
```python
# ANTES
estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica)
estructura_graficos.diagrama_polar_tiros()
fig_polar = plt.gcf()
estructura_graficos.diagrama_barras_tiros(mostrar_c2=estructura_actual.get('MOSTRAR_C2', False))
fig_barras = plt.gcf()

# DESPUÉS
if generar_plots:
    estructura_graficos = EstructuraAEA_Graficos(estructura_geometria, estructura_mecanica)
    estructura_graficos.diagrama_polar_tiros()
    fig_polar = plt.gcf()
    estructura_graficos.diagrama_barras_tiros(mostrar_c2=estructura_actual.get('MOSTRAR_C2', False))
    fig_barras = plt.gcf()
else:
    fig_polar = None
    fig_barras = None
```

#### 4.2 Función Árboles
**Línea:** ~55  
**Función:** `ejecutar_calculo_arboles()`  
**Cambio firma:**
```python
# ANTES
def ejecutar_calculo_arboles(estructura_actual, state):

# DESPUÉS
def ejecutar_calculo_arboles(estructura_actual, state, generar_plots=True):
```

**Líneas:** ~70-95 (generación de árboles)  
**Cambio:**
```python
# ANTES
resultado_arboles = generar_arboles_carga(
    estructura_mecanica, estructura_actual,
    zoom=config["zoom"], 
    escala_flecha=config["escala_flecha"], 
    grosor_linea=config["grosor_linea"],
    mostrar_nodos=config["mostrar_nodos"], 
    fontsize_nodos=config["fontsize_nodos"], 
    fontsize_flechas=config["fontsize_flechas"], 
    mostrar_sismo=config["mostrar_sismo"],
    usar_3d=config["usar_3d"],
    estructura_geometria=state.calculo_objetos.estructura_geometria
)

# DESPUÉS
if generar_plots:
    resultado_arboles = generar_arboles_carga(
        estructura_mecanica, estructura_actual,
        zoom=config["zoom"], 
        escala_flecha=config["escala_flecha"], 
        grosor_linea=config["grosor_linea"],
        mostrar_nodos=config["mostrar_nodos"], 
        fontsize_nodos=config["fontsize_nodos"], 
        fontsize_flechas=config["fontsize_flechas"], 
        mostrar_sismo=config["mostrar_sismo"],
        usar_3d=config["usar_3d"],
        estructura_geometria=state.calculo_objetos.estructura_geometria
    )
else:
    resultado_arboles = {'exito': True, 'imagenes': [], 'mensaje': 'Árboles omitidos (generar_plots=False)'}
```

#### 4.3 Función Fundación
**Línea:** ~125  
**Función:** `ejecutar_calculo_fundacion()`  
**Cambio firma:**
```python
# ANTES
def ejecutar_calculo_fundacion(estructura_actual, state):

# DESPUÉS
def ejecutar_calculo_fundacion(estructura_actual, state, generar_plots=True):
```

**Líneas:** ~220-235 (generación gráfico 3D)  
**Cambio:**
```python
# ANTES
fig_3d = None
try:
    from utils.grafico_sulzberger_monobloque import GraficoSulzbergerMonobloque
    grafico_obj = GraficoSulzbergerMonobloque(nombre_estructura)
    grafico_obj.parametros = {...}
    grafico_obj.todas_hipotesis = resultados['todas_hipotesis']
    
    hipotesis_dim = resultados['hipotesis_dimensionante']
    fig_3d = grafico_obj._crear_grafico_hipotesis(hipotesis_dim)
except Exception as e:
    print(f"Advertencia: No se pudo generar gráfico 3D: {e}")

# DESPUÉS
fig_3d = None
if generar_plots:
    try:
        from utils.grafico_sulzberger_monobloque import GraficoSulzbergerMonobloque
        grafico_obj = GraficoSulzbergerMonobloque(nombre_estructura)
        grafico_obj.parametros = {...}
        grafico_obj.todas_hipotesis = resultados['todas_hipotesis']
        
        hipotesis_dim = resultados['hipotesis_dimensionante']
        fig_3d = grafico_obj._crear_grafico_hipotesis(hipotesis_dim)
    except Exception as e:
        print(f"Advertencia: No se pudo generar gráfico 3D: {e}")
```

---

## Funciones que NO se modifican

### SPH (ejecutar_calculos.py)
- Solo genera texto y tablas
- No tiene plots pesados
- **No requiere modificación**

### Costeo (ejecutar_calculos.py)
- Solo genera tablas
- No tiene plots
- **No requiere modificación**

---

## Verificación de Propagación

### Flujo con generar_plots=False (Vano Económico):
```
vano_economico_utils.py
  └─> ejecutar_calculo_familia_completa(generar_plots=False)
       └─> _ejecutar_secuencia_estructura(generar_plots=False)
            ├─> ejecutar_calculo_cmc_automatico(generar_plots=False) → sin gráficos
            ├─> ejecutar_calculo_dge(generar_plots=False) → sin gráficos
            ├─> ejecutar_calculo_dme(generar_plots=False) → sin gráficos
            ├─> ejecutar_calculo_arboles(generar_plots=False) → sin árboles
            ├─> ejecutar_calculo_sph() → sin cambios
            ├─> ejecutar_calculo_fundacion(generar_plots=False) → sin gráfico 3D
            └─> ejecutar_calculo_costeo() → sin cambios
```

### Flujo con generar_plots=True (Familias, Calcular Todo, Vistas individuales):
```
calcular_familia_logica_encadenada.py (sin parámetro)
  └─> ejecutar_calculo_familia_completa() → usa default True
       └─> _ejecutar_secuencia_estructura() → usa default True
            ├─> ejecutar_calculo_cmc_automatico() → genera gráficos
            ├─> ejecutar_calculo_dge() → genera gráficos
            ├─> ejecutar_calculo_dme() → genera gráficos
            ├─> ejecutar_calculo_arboles() → genera árboles
            ├─> ejecutar_calculo_sph() → sin cambios
            ├─> ejecutar_calculo_fundacion() → genera gráfico 3D
            └─> ejecutar_calculo_costeo() → sin cambios
```

---

## Resumen de Cambios

| Archivo | Funciones Modificadas | Líneas Aprox |
|---------|----------------------|--------------|
| vano_economico_utils.py | 1 función (llamada) | 1 línea |
| calcular_familia_logica_encadenada.py | 2 funciones (firmas + propagación) | 8 líneas |
| geometria_controller.py | 2 funciones (CMC, DGE) | 20 líneas |
| ejecutar_calculos.py | 3 funciones (DME, Árboles, Fundación) | 25 líneas |
| **TOTAL** | **8 modificaciones** | **~54 líneas** |

---

## Beneficios Esperados

### Vano Económico (generar_plots=False):
- ❌ Sin 4 gráficos Plotly (CMC)
- ❌ Sin 3 gráficos (2 matplotlib + 1 Plotly 3D) (DGE)
- ❌ Sin 2 gráficos matplotlib (DME)
- ❌ Sin múltiples imágenes PNG (Árboles)
- ❌ Sin gráfico 3D Plotly (Fundación)
- ✅ **Aceleración significativa** (estimado 50-70% más rápido)

### Familias y Calcular Todo (generar_plots=True):
- ✅ Mantienen todos los gráficos
- ✅ Sin cambios en comportamiento
- ✅ Compatibilidad total

---

## Testing

### Casos de prueba:
1. **Vano Económico**: Verificar que calcula sin errores y más rápido
2. **Familias**: Verificar que genera todos los gráficos normalmente
3. **Calcular Todo**: Verificar que genera todos los gráficos normalmente
4. **Vistas individuales**: Verificar que generan gráficos normalmente

### Métricas:
- Tiempo de ejecución vano económico (antes vs después)
- Verificar que cache se guarda correctamente con `fig=None`
- Verificar que vistas cargan correctamente con `fig=None`
