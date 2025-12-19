# Feature: Árboles de Carga 3D (ADC_3D)

## Descripción
Nuevo parámetro `ADC_3D` que permite generar árboles de carga en visualización 3D interactiva usando Plotly, con el mismo estilo visual que el gráfico de nodos 3D de la vista DGE.

## Archivos Modificados

### 1. Archivos JSON de Estructura
- `data/plantilla.estructura.json`
- `data/actual.estructura.json`
- `data/TECPETROL_Edt_mas2.estructura.json`

**Cambio**: Agregado parámetro `"ADC_3D": true` en sección de configuración de visualización.

### 2. Configuración Centralizada
- `config/parametros_controles.py`

**Cambio**: Agregado `ADC_3D` como switch en `CONTROLES_PARAMETROS`:
```python
"ADC_3D": {
    "tipo": "switch"
}
```

### 3. Vista de Ajuste de Parámetros
- `components/vista_ajuste_parametros.py`

**Cambio**: Agregado campo `ADC_3D` en bloque "CONFIGURACIÓN DE VISUALIZACIÓN":
```python
("ADC_3D", bool, "Árboles de carga en 3D", None)
```

### 4. Vista de Árboles de Carga
- `components/vista_arboles_carga.py`

**Cambios**:
1. Agregado switch `param-adc-3d` en configuración de visualización
2. Actualizado `generar_resultados_arboles()` para detectar y mostrar gráficos 3D interactivos (JSON) o 2D estáticos (PNG)
3. Gráficos 3D se muestran en columnas de ancho completo (lg=12) con `dcc.Graph`
4. Gráficos 2D se muestran en columnas de mitad de ancho (lg=5) con `html.Img`

### 5. Controlador de Árboles
- `controllers/arboles_controller.py`

**Cambios**:
1. Agregado `State("param-adc-3d", "value")` al callback de generación
2. Parámetro `usar_3d` pasado a `generar_arboles_carga()`
3. Actualizado `cargar_arboles_desde_cache()` para detectar y cargar gráficos 3D interactivos

### 6. Generador de Árboles
- `utils/arboles_carga.py`

**Cambios principales**:
1. Agregado parámetro `usar_3d=True` a `generar_arboles_carga()`
2. Nueva función `generar_arbol_3d()` con estilo DGE:
   - Colores consistentes: conductor (#1f77b4), guardia (#2ca02c), poste (#000000)
   - Nodos agrupados por tipo con leyenda
   - Plano de terreno (#8B4513) con opacidad 0.3
   - Vista isométrica: `eye=dict(x=1.5, y=-1.5, z=1.2)`
   - Grilla cada 1 metro en todos los ejes
   - Fondo blanco con grilla gris claro
3. Nueva función `dibujar_lineas_estructura_3d()` para estructura en 3D
4. Nueva función `dibujar_flechas_3d()` con:
   - Flechas con conos (go.Cone)
   - Etiquetas de magnitud en punto medio
   - Colores: rojo (X), verde (Y), azul (Z)
   - Hover con información de carga
5. Guardado dual: PNG (exportar) + JSON (interactividad)

## Comportamiento

### Modo 2D (ADC_3D = false)
- Genera gráficos 2D en plano XZ usando Matplotlib
- Guarda solo archivos PNG
- Muestra imágenes estáticas en vista
- Ocupa mitad de ancho de pantalla

### Modo 3D (ADC_3D = true)
- Genera gráficos 3D interactivos usando Plotly
- Guarda PNG (exportar) + JSON (interactividad)
- Muestra gráficos interactivos con `dcc.Graph`
- Ocupa ancho completo de pantalla
- Permite zoom, pan, rotación
- Hover muestra información de nodos y cargas

## Estilo Visual (Consistente con DGE)

### Colores
- Conductor: `#1f77b4` (azul)
- Guardia: `#2ca02c` (verde)
- Estructura: `#000000` (negro)
- Terreno: `#8B4513` (marrón)
- Flechas: rojo (X), verde (Y), azul (Z)

### Layout
- Título: Arial Black, tamaño 16
- Ejes: Grilla cada 1 metro, fondo blanco
- Cámara: Vista isométrica con Y negativo para Z=0 abajo
- Leyenda: Esquina superior izquierda con fondo blanco semi-transparente
- Dimensiones: 1200x800 px

### Nodos
- Tamaño: 8
- Borde blanco: 2px
- Texto: Tamaño 9, posición arriba
- Hover: Muestra nombre y coordenadas (X, Y, Z)

### Flechas de Carga
- Línea: Ancho 6
- Cono: Tamaño 0.3
- Etiqueta: Magnitud en punto medio
- Hover: Nombre de nodo y tipo de carga

## Uso

1. **Ajustar Parámetros**: Activar/desactivar switch "Árboles de carga en 3D" en vista de parámetros
2. **Vista ADC**: Activar/desactivar switch "Gráficos 3D" en configuración de visualización
3. **Generar**: Click en "Generar Árboles de Carga"
4. **Resultado**: 
   - Si 3D: Gráficos interactivos con controles de zoom/pan/rotación
   - Si 2D: Imágenes estáticas tradicionales

## Persistencia

- Parámetro `ADC_3D` se guarda en archivo `.estructura.json`
- Gráficos 3D se guardan como:
  - `{titulo}.arbolcarga.{hash}.{hipotesis}.png` (exportar)
  - `{titulo}.arbolcarga.{hash}.{hipotesis}.json` (interactividad)
- Cache detecta automáticamente formato disponible al cargar

## Compatibilidad

- Archivos antiguos sin `ADC_3D`: Default `true` (modo 3D)
- Gráficos 2D existentes: Se muestran correctamente como imágenes estáticas
- Gráficos 3D: Requieren JSON para interactividad, PNG como fallback
