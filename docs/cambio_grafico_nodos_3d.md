# Cambio: Gráfico de Nodos 3D Isométrico

## Fecha
2025-01-XX

## Descripción del Cambio
Se modificó el gráfico de nodos de DGE (Diseño Geométrico de Estructura) de un gráfico 2D plano (Matplotlib) a un gráfico 3D isométrico interactivo (Plotly).

## Motivación
- **Visualización completa**: El gráfico 2D solo mostraba el plano XZ (y ≈ 0), ocultando nodos con coordenadas Y significativas
- **Interactividad**: Plotly permite rotar, hacer zoom y explorar la estructura en 3D
- **Mejor comprensión**: La vista isométrica facilita entender la geometría espacial de la estructura

## Archivos Modificados

### 1. `EstructuraAEA_Graficos.py`
**Método modificado**: `graficar_nodos_coordenadas()`

**Cambios**:
- Cambió de Matplotlib 2D a Plotly 3D
- Ahora incluye TODOS los nodos (X, Y, Z) en lugar de solo plano XZ
- Retorna figura Plotly en lugar de usar `plt.show()`
- Vista isométrica configurada con `camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))`
- Nodos agrupados por tipo con colores y leyenda
- Plano de terreno (Z=0) como superficie semitransparente
- Hover interactivo muestra coordenadas exactas

**Código anterior**:
```python
def graficar_nodos_coordenadas(self, titulo_reemplazo=None):
    """Grafica solo los nodos con lista de coordenadas"""
    fig, ax = plt.subplots(figsize=(10, 12))
    # ... código 2D con matplotlib
    plt.show()
```

**Código nuevo**:
```python
def graficar_nodos_coordenadas(self, titulo_reemplazo=None):
    """Grafica nodos en 3D isométrico usando Plotly"""
    import plotly.graph_objects as go
    # ... código 3D con plotly
    return fig
```

### 2. `controllers/geometria_controller.py`
**Función modificada**: `calcular_diseno_geometrico()`

**Cambios**:
- Captura retorno de `graficar_nodos_coordenadas()` en lugar de `plt.gcf()`
- Muestra figura Plotly con `dcc.Graph()` en lugar de convertir a PNG

**Código anterior**:
```python
estructura_graficos.graficar_nodos_coordenadas(...)
fig_nodos = plt.gcf()
# ... luego convierte a PNG con savefig()
```

**Código nuevo**:
```python
fig_nodos = estructura_graficos.graficar_nodos_coordenadas(...)
# ... luego usa dcc.Graph(figure=fig_nodos)
```

### 3. `utils/calculo_cache.py`
**Método modificado**: `guardar_calculo_dge()`

**Cambios**:
- Guarda figura de nodos como JSON (Plotly) en lugar de PNG (Matplotlib)
- Archivo: `Nodos.{hash}.json` en lugar de `Nodos.{hash}.png`
- Usa `fig_nodos.write_json()` en lugar de `fig_nodos.savefig()`

**Código anterior**:
```python
if fig_nodos:
    img_path = CACHE_DIR / f"Nodos.{hash_params}.png"
    fig_nodos.savefig(str(img_path), format='png', dpi=150, bbox_inches='tight')
```

**Código nuevo**:
```python
if fig_nodos:
    json_path = CACHE_DIR / f"Nodos.{hash_params}.json"
    fig_nodos.write_json(str(json_path))
```

### 4. `components/vista_diseno_geometrico.py`
**Función modificada**: `generar_resultados_dge()`

**Cambios**:
- Carga figura de nodos desde JSON con `ViewHelpers.cargar_figura_plotly_json()`
- Muestra con `dcc.Graph()` en lugar de `html.Img()`

**Código anterior**:
```python
img_str_nodos = ViewHelpers.cargar_imagen_base64(f"Nodos.{hash_params}.png")
if img_str_nodos:
    output.extend([
        html.H5("GRAFICO DE NODOS Y COORDENADAS", ...),
        html.Img(src=f'data:image/png;base64,{img_str_nodos}', ...)
    ])
```

**Código nuevo**:
```python
fig_nodos_json = ViewHelpers.cargar_figura_plotly_json(f"Nodos.{hash_params}.json")
if fig_nodos_json:
    output.extend([
        html.H5("GRAFICO 3D DE NODOS Y COORDENADAS", ...),
        dcc.Graph(figure=fig_nodos_json, config={'displayModeBar': True}, style={'height': '800px'})
    ])
```

## Características del Nuevo Gráfico 3D

### Visualización
- **Ejes**: X (horizontal), Y (profundidad), Z (altura)
- **Vista**: Isométrica con ángulo eye=(1.5, 1.5, 1.2)
- **Tamaño**: 1200x800 px
- **Fondo**: Blanco con grilla gris claro

### Elementos Visualizados
1. **Nodos por tipo**:
   - Conductores (azul): C1, C2, C3
   - Guardias (verde): HG1, HG2
   - Estructura (negro): BASE, TOP, CROSS, Y1-Y5
   - Otros (gris): Nodos generales

2. **Conexiones editadas**: Líneas naranjas punteadas entre nodos conectados

3. **Terreno**: Plano semitransparente en Z=0 (color marrón)

4. **Etiquetas**: Nombres de nodos sobre cada punto

### Interactividad
- **Rotación**: Click y arrastrar para rotar la vista
- **Zoom**: Scroll o pinch para acercar/alejar
- **Pan**: Shift + click y arrastrar para desplazar
- **Hover**: Muestra nombre y coordenadas exactas (X, Y, Z)
- **Toolbar**: Botones para resetear vista, guardar imagen, etc.

## Compatibilidad con Cache

### Archivos Generados
- **Antes**: `Nodos.{hash}.png` (imagen estática)
- **Ahora**: `Nodos.{hash}.json` (figura interactiva)

### Migración
Los cálculos DGE existentes con cache antiguo (PNG) seguirán funcionando:
- Si existe `Nodos.{hash}.png`, se ignora
- Si existe `Nodos.{hash}.json`, se carga como gráfico interactivo
- Si no existe ninguno, no se muestra gráfico de nodos

### Recálculo Necesario
Para obtener el nuevo gráfico 3D, es necesario:
1. Ir a vista DGE
2. Presionar "Calcular Diseño Geométrico"
3. El nuevo gráfico 3D se generará y guardará en cache

## Beneficios

1. **Visualización completa**: Ahora se ven TODOS los nodos, incluyendo aquellos con Y ≠ 0 (configuraciones horizontales)

2. **Mejor comprensión espacial**: La vista 3D isométrica facilita entender la geometría de estructuras complejas

3. **Interactividad**: El usuario puede explorar la estructura desde cualquier ángulo

4. **Información detallada**: Hover muestra coordenadas exactas sin necesidad de leer la tabla

5. **Exportable**: El toolbar de Plotly permite guardar la vista actual como PNG

## Limitaciones

1. **Tamaño de archivo**: JSON es más grande que PNG (~50-100 KB vs ~20-30 KB)

2. **Rendimiento**: Gráficos 3D con muchos nodos (>100) pueden ser lentos en navegadores antiguos

3. **Compatibilidad**: Requiere JavaScript habilitado en el navegador

## Pruebas Recomendadas

1. **Estructura vertical simple**: Verificar que todos los nodos se muestran correctamente
2. **Estructura horizontal**: Verificar que nodos con Y ≠ 0 aparecen
3. **Estructura con nodos editados**: Verificar que conexiones editadas se muestran
4. **Cache**: Verificar que gráfico se carga correctamente desde cache
5. **Interactividad**: Probar rotación, zoom, hover

## Notas Técnicas

### Dependencias
- Requiere `plotly` instalado (ya incluido en requirements.txt)
- Usa `plotly.graph_objects` para crear figura 3D
- Usa `dcc.Graph` de Dash para renderizar en web

### Configuración de Cámara
```python
camera=dict(
    eye=dict(x=1.5, y=1.5, z=1.2),  # Vista isométrica
    center=dict(x=0, y=0, z=0),
    up=dict(x=0, y=0, z=1)  # Z hacia arriba
)
```

### Aspectos de Diseño
- `aspectmode='data'`: Mantiene proporciones reales de coordenadas
- `showlegend=True`: Muestra leyenda con tipos de nodos
- `hovertemplate`: Formato personalizado para hover

## Futuras Mejoras

1. **Animación**: Agregar transición animada al cargar el gráfico
2. **Filtros**: Permitir ocultar/mostrar tipos de nodos
3. **Mediciones**: Agregar herramienta para medir distancias entre nodos
4. **Exportar 3D**: Permitir exportar modelo 3D en formatos estándar (OBJ, STL)
5. **Comparación**: Mostrar dos estructuras lado a lado para comparar
