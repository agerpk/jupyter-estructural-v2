# Plan de Implementación: Update AEE

## Objetivo
Agregar parámetros de configuración, plots interactivos, resumen comparativo y compatibilidad completa con Calcular Todo y Familia.

---

## Fase 1: Nuevos Parámetros en Estructura

### 1.1 Actualizar `plantilla.estructura.json`
**Archivo**: `data/plantilla.estructura.json`

```json
"AnalisisEstaticoEsfuerzos": {
    "ACTIVAR_AEE": true,
    "DIAGRAMAS_ACTIVOS": {
        "MQNT": true,
        "MRT": true,
        "MFE": true
    },
    "GRAFICOS_3D_AEE": true,
    "escala_graficos": "logaritmica",
    "n_segmentar_conexion_corta": 10,
    "n_segmentar_conexion_larga": 30,
    "percentil_separacion_corta_larga": 50,
    "mostrar_tablas_resultados_por_elemento": false,
    "plots_interactivos": true
}
```

**Cambios**:
- Agregar `"mostrar_tablas_resultados_por_elemento": false`
- Agregar `"plots_interactivos": true`

---

## Fase 2: Vista AEE - UI de Parámetros

### 2.1 Actualizar `components/vista_analisis_estatico.py`

**Modificar función `crear_vista_analisis_estatico()`**:

Agregar controles en la sección de parámetros:

```python
dbc.Row([
    dbc.Col([
        html.Label("Mostrar tablas por elemento"),
        dbc.Switch(
            id="aee-mostrar-tablas",
            value=aee_params.get('mostrar_tablas_resultados_por_elemento', False)
        )
    ], width=6),
    dbc.Col([
        html.Label("Plots interactivos"),
        dbc.Switch(
            id="aee-plots-interactivos",
            value=aee_params.get('plots_interactivos', True)
        )
    ], width=6)
], className="mb-3")
```

---

## Fase 3: Controller AEE - Guardar Parámetros

### 3.1 Actualizar `controllers/aee_controller.py`

**Modificar callback `guardar_parametros_aee()`**:

Agregar States:
```python
State("aee-mostrar-tablas", "value"),
State("aee-plots-interactivos", "value")
```

Actualizar estructura:
```python
estructura_actual['AnalisisEstaticoEsfuerzos']['mostrar_tablas_resultados_por_elemento'] = mostrar_tablas
estructura_actual['AnalisisEstaticoEsfuerzos']['plots_interactivos'] = plots_interactivos
```

---

## Fase 4: Lógica de Doble Guardado (PNG + JSON)

### 4.1 Actualizar `controllers/aee_controller.py`

**Modificar función `ejecutar_analisis_aee()`**:

```python
plots_interactivos = parametros_aee.get('plots_interactivos', True)

# Generar diagramas MQNT
if diagramas_activos.get('MQNT', True):
    try:
        fig = analizador.generar_diagrama_mqnt(esfuerzos, hip, graficos_3d, escala_graficos)
        
        filename_png = f"AEE_MQNT_{hip}.{hash_params}.png"
        filename_json = f"AEE_MQNT_{hip}.{hash_params}.json"
        filepath_png = Path("data/cache") / filename_png
        filepath_json = Path("data/cache") / filename_json
        
        # Guardar PNG (siempre)
        fig.savefig(str(filepath_png), dpi=150, bbox_inches='tight')
        
        # Guardar JSON si plots_interactivos
        if plots_interactivos:
            fig.write_json(str(filepath_json))
        
        plt.close(fig)
        
        resultados['diagramas'][f'MQNT_{hip}'] = filename_png
    except Exception as e:
        print(f"❌ Error guardando MQNT para {hip}: {e}")
```

**Aplicar mismo patrón para MRT y MFE**.

---

## Fase 5: Vista AEE - Cargar Plots Interactivos

### 5.1 Actualizar `components/vista_analisis_estatico.py`

**Modificar función `generar_resultados_aee()`**:

```python
# Sección de diagramas
diagramas = resultados.get('diagramas', {})
plots_interactivos = estructura_actual.get('AnalisisEstaticoEsfuerzos', {}).get('plots_interactivos', True)

if diagramas:
    componentes.append(html.H5("Diagramas de Esfuerzos", className="mt-4 mb-3"))
    
    for nombre_diagrama in diagramas.keys():
        # Intentar cargar JSON si plots_interactivos
        if plots_interactivos:
            json_filename = f"AEE_{nombre_diagrama}.{hash_params}.json"
            fig_dict = ViewHelpers.cargar_figura_plotly_json(json_filename)
            
            if fig_dict:
                componentes.append(html.H6(nombre_diagrama.replace('_', ' '), className="mt-3"))
                componentes.append(dcc.Graph(
                    figure=fig_dict,
                    config={'displayModeBar': True}
                ))
                continue
        
        # Fallback a PNG
        img_filename = f"AEE_{nombre_diagrama}.{hash_params}.png"
        img_str = ViewHelpers.cargar_imagen_base64(img_filename)
        
        if img_str:
            componentes.append(html.Div([
                html.H6(nombre_diagrama.replace('_', ' '), className="mt-3"),
                html.Img(
                    src=f'data:image/png;base64,{img_str}',
                    style={'width': '100%', 'maxWidth': '1200px'}
                )
            ]))
```

**Modificar sección de tablas por elemento**:

```python
# Tablas de resultados por hipótesis
mostrar_tablas = estructura_actual.get('AnalisisEstaticoEsfuerzos', {}).get('mostrar_tablas_resultados_por_elemento', False)

if mostrar_tablas and esfuerzos:
    componentes.append(html.H5("Resultados por Elemento", className="mt-4 mb-3"))
    
    for hip_nombre, hip_data in esfuerzos.items():
        if 'df_resultados' in hip_data:
            df_dict = hip_data['df_resultados']
            df = pd.DataFrame(df_dict['data'], columns=df_dict['columns'])
            
            componentes.extend([
                html.H6(f"Hipótesis: {hip_nombre}", className="mt-3"),
                ViewHelpers.crear_tabla_html_iframe(
                    df,
                    altura_fila=25,
                    altura_min=200,
                    altura_max=600
                )
            ])
```

---

## Fase 6: Resumen Comparativo AEE

### 6.1 Actualizar `controllers/aee_controller.py`

**Agregar función `generar_resumen_comparativo()`**:

```python
def generar_resumen_comparativo(resultados, geometria):
    """Genera resumen comparativo con máximos por conexión"""
    import pandas as pd
    
    esfuerzos = resultados.get('esfuerzos', {})
    conexiones_info = resultados.get('conexiones_info', [])
    
    # Estructura: {(nodo_i, nodo_j): {M_max, M_hip, Q_max, Q_hip, N_max, N_hip, T_max, T_hip}}
    maximos_por_conexion = {}
    
    for hip_nombre, hip_data in esfuerzos.items():
        if 'df_resultados' not in hip_data:
            continue
        
        df_dict = hip_data['df_resultados']
        df = pd.DataFrame(df_dict['data'], columns=df_dict['columns'])
        
        for _, row in df.iterrows():
            nodo_i = row['Nodo_Inicio']
            nodo_j = row['Nodo_Fin']
            key = (nodo_i, nodo_j)
            
            if key not in maximos_por_conexion:
                maximos_por_conexion[key] = {
                    'M_max': 0, 'M_hip': '',
                    'Q_max': 0, 'Q_hip': '',
                    'N_max': 0, 'N_hip': '',
                    'T_max': 0, 'T_hip': '',
                    'tipo': row.get('Tipo', 'N/A')
                }
            
            # Actualizar máximos
            if abs(row['M_daN_m']) > abs(maximos_por_conexion[key]['M_max']):
                maximos_por_conexion[key]['M_max'] = row['M_daN_m']
                maximos_por_conexion[key]['M_hip'] = hip_nombre
            
            if abs(row['Q_daN']) > abs(maximos_por_conexion[key]['Q_max']):
                maximos_por_conexion[key]['Q_max'] = row['Q_daN']
                maximos_por_conexion[key]['Q_hip'] = hip_nombre
            
            if abs(row['N_daN']) > abs(maximos_por_conexion[key]['N_max']):
                maximos_por_conexion[key]['N_max'] = row['N_daN']
                maximos_por_conexion[key]['N_hip'] = hip_nombre
            
            if abs(row['T_daN_m']) > abs(maximos_por_conexion[key]['T_max']):
                maximos_por_conexion[key]['T_max'] = row['T_daN_m']
                maximos_por_conexion[key]['T_hip'] = hip_nombre
    
    # Crear DataFrame
    filas = []
    for (nodo_i, nodo_j), maximos in maximos_por_conexion.items():
        filas.append({
            'Nodo Inicio': nodo_i,
            'Nodo Fin': nodo_j,
            'Tipo Conexión': maximos['tipo'],
            'Momento Flector [daN.m]': f"{maximos['M_max']:.2f}",
            'Hipótesis M': maximos['M_hip'],
            'Corte [daN]': f"{maximos['Q_max']:.2f}",
            'Hipótesis Q': maximos['Q_hip'],
            'Axial [daN]': f"{maximos['N_max']:.2f}",
            'Hipótesis N': maximos['N_hip'],
            'Torsión [daN.m]': f"{maximos['T_max']:.2f}",
            'Hipótesis T': maximos['T_hip']
        })
    
    df_resumen = pd.DataFrame(filas)
    return df_resumen
```

**Modificar `ejecutar_analisis_aee()` para incluir resumen**:

```python
# Al final de la función, antes del return
df_resumen = generar_resumen_comparativo(resultados, geometria)
resultados['resumen_comparativo'] = df_resumen.to_dict(orient='split')
```

---

### 6.2 Actualizar `components/vista_analisis_estatico.py`

**Agregar sección de resumen en `generar_resultados_aee()`**:

```python
# Resumen Comparativo AEE
if resultados.get('resumen_comparativo'):
    df_dict = resultados['resumen_comparativo']
    df_resumen = pd.DataFrame(df_dict['data'], columns=df_dict['columns'])
    
    componentes.append(html.H5("Resumen Comparativo - Máximos por Conexión", className="mt-4 mb-3"))
    componentes.append(dbc.Table.from_dataframe(
        df_resumen,
        striped=True,
        bordered=True,
        hover=True,
        size="sm"
    ))
```

---

## Fase 7: Vista Ajustar Parámetros - Tabla

### 7.1 Actualizar `utils/parametros_manager.py`

**Agregar metadata para nuevos parámetros**:

```python
"mostrar_tablas_resultados_por_elemento": {
    "categoria": "AEE",
    "simbolo": "TablasElem",
    "unidad": "-",
    "descripcion": "Mostrar tablas detalladas por elemento",
    "tipo": "bool"
},
"plots_interactivos": {
    "categoria": "AEE",
    "simbolo": "Interactivo",
    "unidad": "-",
    "descripcion": "Gráficos interactivos (Plotly JSON)",
    "tipo": "bool"
}
```

---

## Fase 8: Calcular Todo - Integración

### 8.1 Actualizar `components/vista_calcular_todo.py`

**Ya incluye checkbox AEE** - No requiere cambios.

### 8.2 Verificar `controllers/calcular_todo_controller.py`

**Asegurar que ejecuta AEE con plots_interactivos**:

```python
if "aee" in calculos_seleccionados:
    from controllers.aee_controller import ejecutar_analisis_aee
    
    resultado_aee = ejecutar_analisis_aee(estructura_actual, calculo_dge, calculo_dme)
    
    # Guardar cache
    CalculoCache.guardar_calculo_aee(
        nombre_estructura,
        estructura_actual,
        resultado_aee
    )
```

---

## Fase 9: Descargar HTML - Calcular Todo

### 9.1 Actualizar `utils/descargar_html.py`

**Agregar función `generar_seccion_aee()`**:

```python
def generar_seccion_aee(calculo_aee, estructura_actual):
    """Genera HTML para sección AEE"""
    html = ['<h3>8. ANÁLISIS ESTÁTICO DE ESFUERZOS (AEE)</h3>']
    
    resultados = calculo_aee.get('resultados', {})
    hash_params = calculo_aee.get('hash_parametros')
    
    # Resumen Comparativo
    if resultados.get('resumen_comparativo'):
        df_dict = resultados['resumen_comparativo']
        df_resumen = pd.DataFrame(df_dict['data'], columns=df_dict['columns'])
        html.append('<h5>Resumen Comparativo - Máximos por Conexión</h5>')
        html.append(df_resumen.to_html(classes='table table-striped table-bordered table-hover table-sm', index=False))
    
    # Tablas de nodos y conexiones
    if resultados.get('nodos_info'):
        nodos_data = []
        for nombre, info in resultados['nodos_info'].items():
            nodos_data.append({
                'Nodo': nombre,
                'X [m]': f"{info['x']:.2f}",
                'Y [m]': f"{info['y']:.2f}",
                'Z [m]': f"{info['z']:.2f}",
                'Tipo': info['tipo']
            })
        df_nodos = pd.DataFrame(nodos_data)
        html.append('<h5>Nodos de la Estructura</h5>')
        html.append(df_nodos.to_html(classes='table table-striped table-bordered table-sm', index=False))
    
    # Diagramas (PNG)
    diagramas = resultados.get('diagramas', {})
    if diagramas and hash_params:
        html.append('<h5>Diagramas de Esfuerzos</h5>')
        for nombre_diagrama in diagramas.keys():
            img_filename = f"AEE_{nombre_diagrama}.{hash_params}.png"
            img_str = ViewHelpers.cargar_imagen_base64(img_filename)
            if img_str:
                html.append(f'<h6>{nombre_diagrama.replace("_", " ")}</h6>')
                html.append(f'<img src="data:image/png;base64,{img_str}" alt="{nombre_diagrama}">')
    
    return '\n'.join(html)
```

**Modificar `generar_html_completo()` para incluir AEE**:

```python
# 8. AEE
calculo_aee = CalculoCache.cargar_calculo_aee(nombre_estructura)
if calculo_aee:
    secciones.append(generar_seccion_aee(calculo_aee, estructura_actual))
```

---

## Fase 10: Familia - Integración

### 10.1 Verificar `components/vista_familia_estructuras.py`

**Ya incluye checkbox AEE** - No requiere cambios.

### 10.2 Verificar `controllers/familia_controller.py`

**Asegurar que ejecuta AEE en familia**:

```python
if "aee" in calculos_activos:
    from controllers.aee_controller import ejecutar_analisis_aee
    
    resultado_aee = ejecutar_analisis_aee(estructura, calculo_dge, calculo_dme)
    
    CalculoCache.guardar_calculo_aee(
        estructura['TITULO'],
        estructura,
        resultado_aee
    )
```

---

## Fase 11: Descargar HTML - Familia

### 11.1 Actualizar `utils/descargar_html_familia_completo.py`

**Agregar sección AEE en función `generar_html_familia()`**:

```python
# 8. AEE
if "aee" in checklist_activo:
    calculo_aee = CalculoCache.cargar_calculo_aee(nombre_estructura)
    if calculo_aee:
        from utils.descargar_html import generar_seccion_aee
        html_estructura.append(generar_seccion_aee(calculo_aee, estructura))
```

---

## Fase 12: Plots Interactivos - Hover con Información

### 12.1 Actualizar `utils/analisis_estatico.py`

**Modificar `generar_diagrama_mqnt()` para agregar hover data**:

```python
def generar_diagrama_mqnt(self, esfuerzos, hipotesis, graficos_3d=True, escala='logaritmica'):
    """Genera diagrama MQNT con hover interactivo"""
    import plotly.graph_objects as go
    
    # Extraer datos de esfuerzos
    elementos_data = []
    for elem_key, subelems in esfuerzos.get('resultados_por_elemento', {}).items():
        for subelem in subelems:
            elementos_data.append({
                'elemento': elem_key,
                'tipo': subelem.get('tipo_elemento', 'N/A'),
                'M': subelem['M'],
                'Q': subelem['Q'],
                'N': subelem['N'],
                'T': subelem['T'],
                'nodo_i': subelem.get('nodo_i'),
                'nodo_j': subelem.get('nodo_j')
            })
    
    # Crear traces con hover customizado
    traces = []
    for elem_data in elementos_data:
        nodo_i = self.geometria.nodos[elem_data['nodo_i']]
        nodo_j = self.geometria.nodos[elem_data['nodo_j']]
        
        hover_text = (
            f"<b>{elem_data['elemento']}</b><br>"
            f"Tipo: {elem_data['tipo']}<br>"
            f"M: {elem_data['M']:.2f} daN.m<br>"
            f"Q: {elem_data['Q']:.2f} daN<br>"
            f"N: {elem_data['N']:.2f} daN<br>"
            f"T: {elem_data['T']:.2f} daN.m"
        )
        
        trace = go.Scatter3d(
            x=[nodo_i.x, nodo_j.x],
            y=[nodo_i.y, nodo_j.y],
            z=[nodo_i.z, nodo_j.z],
            mode='lines',
            line=dict(
                color=elem_data['M'],  # Color por momento
                width=5,
                colorscale='RdYlGn_r'
            ),
            hovertext=hover_text,
            hoverinfo='text',
            name=elem_data['elemento']
        )
        traces.append(trace)
    
    fig = go.Figure(data=traces)
    
    fig.update_layout(
        title=f'MQNT - {hipotesis}',
        scene=dict(
            xaxis_title='X [m]',
            yaxis_title='Y [m]',
            zaxis_title='Z [m]'
        ),
        hovermode='closest'
    )
    
    return fig
```

---

## Resumen de Archivos Modificados

### Crear:
- Ninguno (solo modificaciones)

### Modificar:
1. `data/plantilla.estructura.json` - Agregar parámetros
2. `components/vista_analisis_estatico.py` - UI parámetros, cargar plots interactivos, resumen
3. `controllers/aee_controller.py` - Guardar parámetros, doble guardado, resumen comparativo
4. `utils/parametros_manager.py` - Metadata nuevos parámetros
5. `utils/descargar_html.py` - Sección AEE con resumen
6. `utils/descargar_html_familia_completo.py` - Incluir AEE
7. `utils/analisis_estatico.py` - Hover interactivo en plots

---

## Testing

### Test 1: Parámetros
- [ ] Guardar parámetros desde vista AEE
- [ ] Verificar en JSON estructura
- [ ] Verificar en tabla ajustar parámetros

### Test 2: Plots Interactivos
- [ ] Calcular AEE con plots_interactivos=True
- [ ] Verificar JSON guardado en cache
- [ ] Verificar PNG guardado en cache
- [ ] Cargar desde cache - debe mostrar plot interactivo
- [ ] Hover muestra información correcta

### Test 3: Plots Estáticos
- [ ] Calcular AEE con plots_interactivos=False
- [ ] Verificar solo PNG guardado
- [ ] Cargar desde cache - debe mostrar PNG

### Test 4: Resumen Comparativo
- [ ] Calcular AEE
- [ ] Verificar tabla resumen aparece
- [ ] Verificar máximos correctos por conexión

### Test 5: Calcular Todo
- [ ] Ejecutar con AEE activado
- [ ] Verificar plots interactivos si configurado
- [ ] Descargar HTML - verificar sección AEE con resumen

### Test 6: Familia
- [ ] Calcular familia con AEE
- [ ] Verificar cada estructura tiene AEE
- [ ] Descargar HTML familia - verificar AEE incluido

---

## Notas Importantes

1. **Doble guardado**: Siempre guardar PNG (fallback), JSON solo si `plots_interactivos=True`
2. **Hover data**: Incluir tipo de elemento, valores MQNT en hover
3. **Resumen comparativo**: Tabla con máximos por conexión, todas las hipótesis
4. **Compatibilidad**: Mantener compatibilidad con estructuras sin nuevos parámetros (defaults)
5. **Performance**: Plots interactivos pueden ser más pesados - dar opción de desactivar
