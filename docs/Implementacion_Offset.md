# Implementación Sistema de Offsets

## Resumen
Sistema de offsets para columnas y ménsulas que amplía las zonas de verificación geométrica y se visualiza en gráficos 2D.

## Parámetros Nuevos

### Activación (Boolean)
- `OFFSET_COLUMNA_BASE`: Activar offset en columna base (z=0 a z=CROSS_H1)
- `OFFSET_COLUMNA_INTER`: Activar offset en columna intermedia (z=CROSS_H1 a z=max)
- `OFFSET_MENSULA`: Activar offset en ménsulas

### Tipo de Offset (String)
- `OFFSET_COLUMNA_BASE_TIPO`: "Recto" | "Trapezoidal" | "Triangular"
- `OFFSET_COLUMNA_INTER_TIPO`: "Recto" | "Trapezoidal" | "Triangular"
- `OFFSET_MENSULA_TIPO`: "Recto" | "Trapezoidal" | "Triangular"

### Valores de Offset (Float, 0.0 a 10.0)
- `OFFSET_COLUMNA_BASE_INICIO`: Offset en z=0 (m)
- `OFFSET_COLUMNA_BASE_FIN`: Offset en z=CROSS_H1 (m)
- `OFFSET_COLUMNA_INTER_INICIO`: Offset en z=CROSS_H1 (m)
- `OFFSET_COLUMNA_INTER_FIN`: Offset en z=max (m)
- `OFFSET_MENSULA_INICIO`: Offset en menor |x| (m)
- `OFFSET_MENSULA_FIN`: Offset en mayor |x| (m)

## Funcionamiento de Tipos de Offset

### Recto
- **Columna**: Suma `OFFSET_INICIO` a ambos lados (±X) en toda la altura
- **Ménsula**: Suma `OFFSET_INICIO` hacia arriba (+Z) en toda la longitud

### Trapezoidal
- **Columna Base**: Interpola de `OFFSET_INICIO` (z=0) a `OFFSET_FIN` (z=CROSS_H1)
- **Columna Inter**: Interpola de `OFFSET_INICIO` (z=CROSS_H1) a `OFFSET_FIN` (z=max)
- **Ménsula**: Interpola de `OFFSET_INICIO` (en menor |x|) a `OFFSET_FIN` (en mayor |x|)

### Triangular
- Igual que Trapezoidal pero fuerza `OFFSET_FIN = 0.0`

## Aplicación de Offsets

### Columna
- **Bilateral**: Aplica ±X (ambos lados)
- **Cómo se aplica**: Expande las zonas prohibidas de columna (NO se suma a distancias s)
- **Zonas afectadas**: Todas las verificaciones de zona columna en Etapas 1-6

### Ménsula
- **Unilateral**: Solo +Z (hacia arriba, NO hacia abajo)
- **Cómo se aplica**: Expande las zonas prohibidas de ménsula (NO se suma a distancias s)
- **Zonas afectadas**: Todas las verificaciones de zona ménsula en Etapas 1-6

## Etapas de Implementación

### ETAPA 1: Módulo de Cálculo
**Archivo**: `utils/offset_geometria.py`

Funciones:
- `calcular_offset_columna(z, z_min, z_max, offset_inicio, offset_fin, tipo)` → float
- `calcular_offset_mensula(x, x_min, x_max, offset_inicio, offset_fin, tipo)` → float

### ETAPA 2: Integración en geometria_zonas
**Archivo**: `utils/geometria_zonas.py`

Modificaciones en `GeneradorZonasProhibidas.__init__`:
- Agregar parámetros de offset al dict `parametros`

Modificaciones en `_generar_zonas_columna`:
- Calcular offset columna base/inter según z
- Aplicar offset bilateral al ancho de FranjaVertical

Modificaciones en `_generar_zonas_mensula`:
- Calcular offset ménsula según x
- Aplicar offset unilateral (+Z) a altura de FranjaHorizontal y radio de Circulo

### ETAPA 3: Integración en EstructuraAEA_Geometria
**Archivo**: `EstructuraAEA_Geometria.py`

Modificaciones en `__init__`:
- Agregar parámetros de offset como atributos
- Leer desde `parametros` dict si existe

### ETAPA 4: Pasar offsets en Etapas 1-6
**Archivos**: `EstructuraAEA_Geometria_Etapa1.py` a `Etapa6.py`

Modificaciones en llamadas a `crear_verificador_desde_nodos`:
- Agregar parámetros de offset al dict `parametros`
- El resto del código permanece sin cambios

### ETAPA 9: Gráfico Cabezal 2D
**Archivo**: `GraficoCabezal2D.py`

Modificaciones en `generar_completo`:
- Dibujar offsets como líneas punteadas grises claras
- Crear función `_dibujar_offsets(fig)`

Elementos a graficar:
- Offset columna base: Líneas verticales punteadas en ±X
- Offset columna inter: Líneas verticales punteadas en ±X
- Offset ménsula: Líneas horizontales punteadas en +Z

### ETAPA 10: Gráfico Estructura 2D
**Archivo**: `GraficoEstructura2D.py` (buscar archivo similar)

Modificaciones similares a GraficoCabezal2D

### ETAPA 11: Vista Ajustar Parámetros
**Archivo**: `components/vista_ajustar_parametros.py`

Agregar en categoría "cabezal":
- 3 switches (OFFSET_COLUMNA_BASE, OFFSET_COLUMNA_INTER, OFFSET_MENSULA)
- 3 dropdowns de tipo (Recto, Trapezoidal, Triangular)
- 6 inputs numéricos (min=0.0, max=10.0, step=0.01)

### ETAPA 12: Vista Diseño Geométrico (Modo Manual)
**Archivo**: `components/vista_diseno_geometrico.py`

Agregar controles interactivos:
- 3 switches con `dbc.Switch`
- 3 dropdowns con `dcc.Dropdown`
- 6 sliders con `dcc.Slider` (min=0, max=10, step=0.01)

### ETAPA 13: Controller Parámetros
**Archivo**: `controllers/parametros_controller.py`

Modificaciones en `guardar_parametros_ajustados`:
- Agregar 12 nuevos parámetros al guardado

### ETAPA 14: Controller Geometría
**Archivo**: `controllers/geometria_controller.py`

Modificaciones en `calcular_diseno_geometrico`:
- Pasar parámetros de offset a `EstructuraAEA_Geometria`

## Orden de Implementación Recomendado

1. **ETAPA 1**: Crear módulo `offset_geometria.py` con funciones de cálculo
2. **ETAPA 2**: Integrar offsets en `geometria_zonas.py` (aplica a TODAS las etapas automáticamente)
3. **ETAPA 3**: Integrar parámetros en `EstructuraAEA_Geometria.__init__`
4. **ETAPA 4**: Pasar parámetros de offset en Etapas 1-6
5. **ETAPA 5-6**: Integrar en gráficos 2D
6. **ETAPA 7-8**: Integrar en vistas (UI)
7. **ETAPA 9-10**: Integrar en controllers

## Notas Importantes

### Ventaja de Implementación Centralizada
- **1 modificación** en `geometria_zonas.py` aplica a TODAS las verificaciones
- **NO** se modifica lógica de Etapas 1-6, solo se pasan parámetros
- **Mantenimiento** simplificado: offsets en un solo lugar

### Compatibilidad
- Valores por defecto: todos los offsets desactivados (false)
- Retrocompatibilidad: estructuras antiguas sin offsets funcionan igual

### Testing
- Verificar con offset recto simple primero
- Luego probar trapezoidal
- Finalmente triangular
- Validar que gráficos muestran offsets correctamente

## Ejemplo de Uso

### Caso: Columna Base Trapezoidal
```python
OFFSET_COLUMNA_BASE = True
OFFSET_COLUMNA_BASE_TIPO = "Trapezoidal"
OFFSET_COLUMNA_BASE_INICIO = 3.3  # En z=0
OFFSET_COLUMNA_BASE_FIN = 0.65     # En z=CROSS_H1
```

Resultado:
- En z=0: zona columna se expande ±3.3m
- En z=CROSS_H1: zona columna se expande ±0.65m
- Interpolación lineal entre ambos puntos

### Caso: Ménsula Triangular
```python
OFFSET_MENSULA = True
OFFSET_MENSULA_TIPO = "Triangular"
OFFSET_MENSULA_INICIO = 1.48  # En x=min
OFFSET_MENSULA_FIN = 0.0      # Forzado por tipo Triangular
```

Resultado:
- En x=min (cerca de columna): zona ménsula se expande +1.48m en Z
- En x=max (extremo ménsula): zona ménsula sin expansión
- Interpolación lineal entre ambos puntos
