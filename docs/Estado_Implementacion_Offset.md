# Estado de Implementación - Sistema de Offsets


## 🔄 PENDIENTE - TODAS LAS ETAPAS

### ETAPA 1: Módulo de Cálculo
- ⏳ Crear archivo `utils/offset_geometria.py`
- ⏳ Función `calcular_offset_columna()`
- ⏳ Función `calcular_offset_mensula()`

### ETAPA 2: Integración en EstructuraAEA_Geometria
- ⏳ Agregar parámetros a `__init__`
- ⏳ Lectura desde `parametros` dict
- ⏳ Valores por defecto

### ETAPA 3: Integración en Etapa1
- ⏳ Import de `offset_geometria`
- ⏳ Modificar verificaciones con offset columna base
- ⏳ Modificar verificaciones con offset ménsula

### ETAPA 4: Integración en Etapa2
- ⏳ Import de `offset_geometria`
- ⏳ Modificar `_buscar_altura_fuera_zonas_prohibidas_h1a`
- ⏳ Modificar `_checkear_zonas_prohibicion_s`

### ETAPA 5: Integración en Etapa3
- ⏳ Import de `offset_geometria`
- ⏳ Modificar `_buscar_altura_fuera_zonas_prohibidas_h2a`
- ⏳ Modificar `_checkear_zonas_prohibicion_s`

### ETAPA 6: Integración en Etapa4
- ⏳ Import de `offset_geometria`
- ⏳ Modificar verificaciones Dhg

### ETAPA 7: Integración en Etapa5
- ⏳ Import de `offset_geometria`
- ⏳ Modificar checkeos

### ETAPA 8: Integración en Etapa6
- ⏳ Import de `offset_geometria`
- ⏳ Modificar checkeos finales

### ETAPA 9: Gráfico Cabezal 2D
- ⏳ Crear función `_dibujar_offsets(fig)`
- ⏳ Dibujar offsets como líneas punteadas grises

### ETAPA 10: Gráfico Estructura 2D
- ⏳ Buscar archivo
- ⏳ Implementar similar a GraficoCabezal2D

### ETAPA 11: Vista Ajustar Parámetros
- ⏳ Agregar controles en categoría "cabezal"

### ETAPA 12: Vista Diseño Geométrico
- ⏳ Agregar controles interactivos

### ETAPA 13: Controller Parámetros
- ⏳ Modificar `guardar_parametros_ajustados`

### ETAPA 14: Controller Geometría
- ⏳ Pasar parámetros de offset

### Plantilla
- ⏳ Agregar parámetros a `plantilla.estructura.json`

## CORRECCIONES CRÍTICAS APLICADAS

1. ✅ Nombre correcto: `OFFSET_COLUMNA_INTER_INICIO` (con N)
2. ✅ Offset expande zonas prohibidas (NO se suma a distancias s)
3. ✅ Ménsula: INICIO es el valor de offset en menor |x|, FIN es el valor de offset en mayor |x|
4. ✅ Offset ménsula SOLO hacia arriba (+Z)

## Próximos Pasos

Esperar confirmación del usuario para comenzar implementación completa.
