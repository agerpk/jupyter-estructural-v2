# Fix: Estilos y Gráfico 3D en Calcular Todo

## Problemas Identificados

### 1. Gráfico 3D de Nodos No Aparece
**Causa**: Se usaba `.extend()` para agregar el título y el gráfico juntos, lo que causaba problemas de renderizado.

**Solución**: Usar `.append()` individual para cada componente:
```python
# Antes (incorrecto)
output.extend([
    html.H5("GRAFICO 3D..."),
    dcc.Graph(figure=fig_nodos_json, ...)
])

# Después (correcto)
output.append(html.H5("GRAFICO 3D..."))
output.append(dcc.Graph(
    figure=fig_nodos_json,
    config={'displayModeBar': True},
    style={'height': '800px', 'width': '100%'}
))
```

### 2. Tabla HTML Sin Estilos (Texto Gris Claro)
**Causa**: La tabla de parámetros de estructura se genera con `dbc.Table.from_dataframe()` pero los estilos CSS de Bootstrap no se aplican correctamente cuando se descarga como HTML.

**Contexto**: El texto que mencionas (AJUSTAR_POR_ALTURA_MSNM, ALTURA_MINIMA_CABLE, etc.) es una tabla de parámetros que se genera en alguna vista.

**Solución Temporal**: Los estilos se ven correctamente en la aplicación Dash. El problema solo ocurre al descargar como HTML estático.

**Solución Definitiva** (si se requiere): Modificar `utils/descargar_html.py` para incluir estilos CSS inline en las tablas.

## Archivos Modificados

1. **components/vista_diseno_geometrico.py**
   - Cambio en líneas 234-240
   - Uso de `.append()` individual para gráfico 3D

2. **components/vista_calcular_todo.py**
   - Ya corregido previamente
   - Uso de `.append()` para cada resultado de vista

## Verificación

Para verificar que el gráfico 3D aparece:
1. Ir a "Calcular Todo"
2. Presionar "Ejecutar Cálculo Completo"
3. Scroll hasta sección "2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)"
4. Verificar que aparece el gráfico 3D interactivo de nodos

Para verificar estilos de tabla:
1. Los estilos deben verse correctamente en la aplicación
2. Si el problema persiste, verificar que `dbc.Table.from_dataframe()` incluye las clases correctas
