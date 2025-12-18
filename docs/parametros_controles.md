# Controles de Parámetros Centralizados

## Ubicación
`config/parametros_controles.py`

## Propósito
Definir en un solo lugar todos los controles (sliders, inputs, selects, switches) para parámetros de estructura. Esto asegura consistencia entre todas las vistas (Ajustar Parámetros, DGE, CMC, etc.).

## Estructura

Cada parámetro tiene una configuración que define:
- **tipo**: `slider`, `slider_input`, `select`, `switch`, `input`
- **Propiedades específicas** según el tipo:
  - Slider: `min`, `max`, `step`, `marks`
  - Select: `opciones` (lista de valores)
  - Input: `input_type` (`number` o `text`)

## Uso en Vistas

### Importar configuración
```python
from config.parametros_controles import CONTROLES_PARAMETROS, obtener_config_control
```

### Crear slider desde configuración
```python
config = obtener_config_control("HADD")
if config and config["tipo"] == "slider":
    slider = dcc.Slider(
        id="slider-hadd-geom",
        min=config["min"],
        max=config["max"],
        step=config["step"],
        value=estructura_actual.get("HADD", 0.4),
        marks=config["marks"],
        tooltip={"placement": "bottom", "always_visible": True}
    )
```

### Crear select desde configuración
```python
config = obtener_config_control("DISPOSICION")
if config and config["tipo"] == "select":
    select = dbc.Select(
        id="select-disposicion-geom",
        value=estructura_actual.get("DISPOSICION", "triangular"),
        options=[{"label": opt, "value": opt} for opt in config["opciones"]]
    )
```

## Actualizar Controles

Para cambiar un control en toda la aplicación:
1. Editar `config/parametros_controles.py`
2. Modificar la configuración del parámetro
3. Los cambios se aplicarán automáticamente en todas las vistas que usen `obtener_config_control()`

## Ejemplo: Cambiar step de HADD

**Antes** (código duplicado en cada vista):
```python
# vista_diseno_geometrico.py
dcc.Slider(id="slider-hadd-geom", min=0, max=4, step=1, ...)

# vista_ajuste_parametros.py  
dcc.Slider(id="slider-hadd", min=0, max=4, step=0.05, ...)  # Inconsistente!
```

**Después** (centralizado):
```python
# config/parametros_controles.py
"HADD": {
    "tipo": "slider",
    "min": 0,
    "max": 4,
    "step": 0.05,  # Un solo lugar para cambiar
    "marks": {i: str(i) for i in range(5)}
}
```

## Parámetros Definidos

### Sliders
- Ángulos: `alpha`, `theta`, `ANG_APANTALLAMIENTO`
- Distancias: `Lk`, `HADD`, `HADD_HG`, `HADD_LMEN`, `HADD_ENTRE_AMARRES`
- Ménsulas: `LONGITUD_MENSULA_MINIMA_CONDUCTOR`, `LONGITUD_MENSULA_MINIMA_GUARDIA`
- Alturas: `ALTURA_MINIMA_CABLE`, `Altura_MSNM`
- Otros: `TENSION`, `CANT_HG`, `ANCHO_CRUCETA`, `DIST_REPOSICIONAR_HG`

### Selects
- Estructura: `TIPO_ESTRUCTURA`, `DISPOSICION`, `TERNA`, `Zona_estructura`
- Normativa: `clase`, `exposicion`, `Zona_climatica`
- Configuración: `FORZAR_ORIENTACION`, `PRIORIDAD_DIMENSIONADO`, `METODO_ALTURA_MSNM`
- Objetivos: `OBJ_CONDUCTOR`, `OBJ_GUARDIA`

### Switches
- `VANO_DESNIVELADO`, `AJUSTAR_POR_ALTURA_MSNM`, `HG_CENTRADO`
- `AUTOAJUSTAR_LMENHG`, `RELFLECHA_SIN_VIENTO`, `REEMPLAZAR_TITULO_GRAFICO`

### Inputs
- Numéricos: `L_vano`, `Vmax`, `Vmed`, `PCADENA`, `PESTRUCTURA`, etc.
- Texto: `TITULO`, `fecha_creacion`, `version`

## Migración de Vistas Existentes

Para migrar una vista a usar controles centralizados:

1. Identificar parámetros con controles
2. Reemplazar definiciones hardcodeadas con `obtener_config_control()`
3. Verificar que los IDs de componentes sean consistentes
4. Probar que los valores se guardan correctamente

## Beneficios

- ✅ Consistencia entre vistas
- ✅ Mantenimiento simplificado
- ✅ Un solo lugar para cambiar rangos/steps
- ✅ Fácil agregar nuevos parámetros
- ✅ Documentación implícita de todos los controles
