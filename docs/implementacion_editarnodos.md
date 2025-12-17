# Implementación: Editor de Nodos en DGE

## Objetivo
Permitir editar, agregar y eliminar nodos estructurales después del dimensionamiento automático en DGE, con capacidad de asignar cables y rotación en eje Z para modificar la aplicación de cargas.

## Modificaciones vs Plan Original
- **Edición de nodos existentes**: Además de agregar, permitir modificar nodos ya creados
- **Rotación eje Z**: Se define la rotacion en eje z (plano xy) del cable, sentido antihorario positivo. Esto cambiara la direccion de las cargas transversales, longitudinales.
- **Recálculo automático**: Los outputs de DGE se regeneran cada vez que se editan nodos

## Arquitectura de Datos

### Estructura de Nodo Adicional/Editado
```python
{
    "nombre": "C1_R",  # Nombre único del nodo
    "tipo": "conductor",  # conductor, guardia, general, cruce, base, viento
    "coordenadas": [x, y, z],  # Posición en metros
    "cable_id": "Al/Ac 435/55",  # ID del cable asociado (None para nodos sin cable)
    "rotacion_eje_z": 0.0,  # Rotación del cable en grados (0-360)
    "angulo_quiebre": 0.0,  # Ángulo de quiebre del cable
    "tipo_fijacion": "suspensión",  # suspensión o retención
    "es_editado": True,  # Flag para distinguir nodos editados de originales
    "conectado_a": ["CROSS_H1", "Y2"]  # Lista de nodos a los que se conecta (opcional)
}
```

### Persistencia en JSON
```json
{
  "parametros": {...},
  "nodos_editados": [
    {
      "nombre": "C1_R",
      "tipo": "conductor",
      "coordenadas": [2.5, 0.0, 15.0],
      "cable_id": "Al/Ac 435/55",
      "rotacion_eje_z": 45.0,
      "angulo_quiebre": 0.0,
      "tipo_fijacion": "suspensión",
      "es_editado": true,
      "conectado_a": ["CROSS_H1", "Y2"]
    }
  ]
}
```

## Secuencia de Implementación

### FASE 1: Modelo de Datos y Backend

#### 1.1 Modificar `NodoEstructural` (EstructuraAEA_Geometria.py)
- [x] Agregar atributo `rotacion_eje_z` (default 0.0)
- [x] Agregar atributo `es_editado` (default False)
- [x] Agregar atributo `conectado_a` (default None)
- [x] Actualizar método `__init__` para aceptar estos parámetros
- [x] Actualizar método `info_completa()` para mostrar nuevos atributos

#### 1.2 Agregar métodos de gestión de nodos en `EstructuraAEA_Geometria`
- [x] `agregar_nodo_manual(nombre, tipo, coords, cable, rotacion_z, angulo_quiebre, tipo_fijacion, conectado_a)`
  - Validar que nombre no exista
  - Validar que cable existe en LibCables si se especifica
  - Validar que nodo conectado existe si se especifica
  - Crear NodoEstructural con `es_editado=True`
  - Agregar a `self.nodos`
  - Actualizar `self.nodes_key`
  
- [x] `editar_nodo(nombre, **kwargs)`
  - Validar que nodo existe
  - Actualizar atributos especificados
  - Marcar como `es_editado=True`
  - Actualizar `self.nodes_key`
  
- [x] `eliminar_nodo(nombre)`
  - Validar que nodo existe
  - Validar que no es nodo crítico (BASE)
  - Eliminar de `self.nodos`
  - Actualizar `self.nodes_key`
  
- [x] `exportar_nodos_editados()`
  - Retornar lista de nodos con `es_editado=True` en formato dict
  
- [x] `importar_nodos_editados(nodos_list)`
  - Cargar nodos editados desde lista de dicts
  - Aplicar después de dimensionamiento automático

#### 1.3 Modificar `EstructuraAEA_Mecanica` para rotación de cargas
- [x] Agregar método `_rotar_carga_eje_z(fx, fy, fz, angulo_grados)`
  - Rotar vector de carga en eje Z
  - Retornar (fx_rot, fy_rot, fz)
  
- [x] Modificar `asignar_cargas_hipotesis()`
  - Detectar nodos con `rotacion_eje_z != 0`
  - Aplicar rotación después de calcular cargas
  - Aplicar a nodos conductor y guardia

### FASE 2: Persistencia y Cache

#### 2.1 Modificar `estructura_manager.py`
- [x] Agregar campo `nodos_editados` al JSON de estructura
- [x] Método `guardar_nodos_editados(nodos_list)`
  - Guardar en `actual.estructura.json`
  - Guardar en `{titulo}.estructura.json`
  - Crear diccionario con nodos nuevos y cambios de nodos automáticos
- [x] Método `cargar_nodos_editados()` retorna lista o None

#### 2.2 Modificar `calculo_cache.py`
- [x] Incluir `nodos_editados` en hash de parámetros para DGE
- [x] Invalidar cache DGE si nodos_editados cambia (automático por hash)
- [x] Guardar `nodos_editados` en cache DGE

### FASE 3: Controlador

#### 3.1 Modificar `geometria_controller.py`
- [x] Función `aplicar_nodos_editados(estructura_geometria, nodos_editados_list)`
  - Llamar después de `dimensionar_unifilar()`
  - Aplicar cada nodo editado (agregar/editar/eliminar)
  - Marcar nodos con `es_editado=True` automáticamente
  
- [x] Modificar `ejecutar_calculo_dge()`
  - Cargar `nodos_editados` desde estructura_actual
  - Llamar `aplicar_nodos_editados()` después de dimensionar
  - Regenerar gráficos con nodos editados
  - Actualizar cache de objetos EstructuraAEA
  
- [x] Modificar `calcular_diseno_geometrico()` callback
  - Cargar `nodos_editados` desde estructura_actual
  - Llamar `aplicar_nodos_editados()` después de dimensionar
  - Regenerar outputs con nodos editados
  
- [x] Callback `guardar_cambios_nodos_modal()` (requiere UI - Fase 4)
  - Input: tabla completa de nodos desde modal
  - Validar todos los datos
  - Detectar cambios vs nodos originales
  - Marcar `es_editado=True` para nodos nuevos o modificados
  - Guardar en `actual.estructura.json`
  - Guardar en `{titulo}.estructura.json`
  - Actualizar `estructura_actual['nodos_editados']`
  - Recalcular DGE completo
  - Regenerar outputs
  - Retornar éxito/error

### FASE 4: Vista (UI)

#### 4.1 Componente Editor de Nodos (`vista_diseno_geometrico.py`)
- [x] Botón "Editar Nodos" en vista DGE (abre modal)
- [x] Modal con tabla editable de nodos:
  - **Tabla con una fila por nodo** (todos los nodos visibles simultáneamente)
  - Columnas editables inline:
    - **Nombre**: Input text editable (string)
    - **Tipo**: Dropdown (conductor, guardia, general, cruce, base, viento)
    - **Coord X**: Input number editable (float)
    - **Coord Y**: Input number editable (float)
    - **Coord Z**: Input number editable (float)
    - **Cable ID**: Dropdown con cables de CMC (actualizado dinámicamente)
    - **Rotación Eje Z**: Input number (float, grados 0-360)
    - **Ángulo Quiebre**: Input number (float, grados)
    - **Tipo Fijación**: Dropdown (suspensión, retención, none)
    - **Conectado A**: Botón que abre submodal con checkboxes de nodos existentes
  - Botón "Agregar Fila" para crear nuevo nodo
  - Botón "Eliminar" por fila (icono X)
  - **es_editado**: NO aparece en UI, se autocompleta automáticamente
    - Se marca True si nodo es creado en modal
    - Se marca True si nodo existente es modificado
  
- [ ] Botones del modal:
  - **Cancelar**: Cierra modal sin guardar cambios
  - **Guardar**: Guarda cambios y ejecuta:
    - Guardar en `actual.estructura.json`
    - Guardar en `{titulo}.estructura.json`
    - Actualizar cache de objetos EstructuraAEA (geometria, mecanica, graficos)
    - Recalcular DGE con nodos editados
    - Regenerar outputs

#### 4.2 Callbacks de UI
- [x] `toggle_modal_editor_nodos()` - Abrir/cerrar modal y cargar nodos actuales
- [x] `guardar_cambios_nodos()` - Validar, guardar JSON, actualizar estructura_actual
- [ ] `abrir_submodal_conexiones(nodo_index)` - Abrir submodal con checkboxes de nodos
- [ ] `guardar_conexiones_nodo(nodo_index, nodos_seleccionados)` - Guardar lista de conexiones

### FASE 5: Integración y Validación

#### 5.1 Validaciones
- [x] Validar coordenadas (no negativas en Z, rangos razonables)
- [x] Validar que nodo conectado existe
- [x] Validar que nombre es único
- [x] Validar que tipo de nodo es válido
- [x] Validar rotación (0-360°)
- [x] Validar nombres no vacíos

#### 5.2 Flujo completo
- [x] Usuario ejecuta DGE normal → genera nodos automáticos
- [x] Usuario presiona botón "Editar Nodos" → abre modal
- [x] Modal muestra tabla con todos los nodos (una fila por nodo)
- [x] Usuario edita celdas inline (nombre, tipo, coordenadas, cable, rotación, etc.)
- [x] Usuario elimina filas con DataTable row_deletable
- [x] Usuario presiona "Guardar":
  - [x] Sistema valida todos los datos
  - [x] Sistema marca `es_editado=True` automáticamente
  - [x] Sistema guarda en `actual.estructura.json`
  - [x] Sistema guarda en `{titulo}.estructura.json`
  - [x] Sistema actualiza estructura_actual
- [x] Usuario presiona "Cancelar" → cierra modal sin cambios
- [x] Usuario recalcula DGE → aplica nodos editados automáticamente

#### 5.3 Propagación a etapas posteriores
- [x] DME: Usar nodos editados para asignar cargas (implementado en Fase 1.3)
- [x] DME: Aplicar rotación de cargas según `rotacion_eje_z` (implementado en Fase 1.3)
- [x] ADC: Usar nodos editados para árbol de cargas (automático, usa estructura_mecanica)
- [x] SPH: Usar reacciones con nodos editados (automático, usa estructura_mecanica)

### FASE 6: Visualización

#### 6.1 Modificar `EstructuraAEA_Graficos.py`
- [x] Distinguir visualmente nodos editados (color naranja #FF6B00, marcador cuadrado)
- [x] Mostrar rotación de cable con flecha/indicador (flechas rojas)
- [x] Mostrar conexiones entre nodos (líneas punteadas naranjas)
- [x] Leyenda indicando nodos originales vs editados
- [x] Etiquetas con asterisco (*) para nodos editados

## Archivos Afectados

### Backend (Core)
1. `EstructuraAEA_Geometria.py` - Gestión de nodos
2. `EstructuraAEA_Mecanica.py` - Rotación de cargas
3. `EstructuraAEA_Graficos.py` - Visualización de nodos editados

### Persistencia
4. `utils/estructura_manager.py` - Guardar/cargar nodos editados
5. `utils/calculo_cache.py` - Cache con nodos editados

### Controlador
6. `controllers/geometria_controller.py` - Lógica de edición y recálculo

### Vista
7. `components/vista_diseno_geometrico.py` - UI del editor

### Modelo
8. `models/app_state.py` - Estado de nodos editados (si necesario)

## Orden de Implementación Recomendado

1. **Backend primero**: Fase 1 (modelo de datos)
2. **Persistencia**: Fase 2 (guardar/cargar)
3. **Controlador**: Fase 3 (lógica de negocio)
4. **Vista**: Fase 4 (UI)
5. **Integración**: Fase 5 (validaciones y flujo completo)
6. **Visualización**: Fase 6 (gráficos mejorados)

## Notas de Implementación

### Rotación de Cargas en Eje Z
La rotación se aplica DESPUÉS de calcular las cargas según hipótesis:
```python
# Cargas originales calculadas
fx, fy, fz = calcular_cargas_nodo(...)

# Si nodo tiene rotación
if nodo.rotacion_eje_z != 0:
    fx_rot, fy_rot, fz = _rotar_carga_eje_z(fx, fy, fz, nodo.rotacion_eje_z)
```

### Nodos Críticos No Editables
- BASE: Editable pero no eliminable (advertencia si se modifica)
- Todos los demás nodos: Totalmente editables y eliminables

### Guardado de Cambios
Al presionar "Guardar" en modal:
1. Validar todos los datos de la tabla
2. Crear diccionario `nodos_editados` con:
   - Nodos nuevos (agregados en modal)
   - Nodos modificados (cambios vs nodos automáticos)
3. Guardar en `actual.estructura.json` y `{titulo}.estructura.json`
4. Actualizar cache de objetos EstructuraAEA (geometria, mecanica, graficos)
5. Recalcular DGE completo aplicando nodos editados
6. Regenerar todos los outputs (gráficos, tablas, memoria)

### Detección Automática de Cambios
- Sistema compara nodos actuales vs nodos originales (del dimensionamiento)
- Si hay diferencias → marca `es_editado=True` automáticamente
- Usuario NO ve ni edita campo `es_editado` en UI

### Actualización Dinámica de Dropdowns y Submodal
- **Cable ID**: Se actualiza con cables disponibles en CMC al abrir modal
- **Conectado A**: Submodal con checkboxes
  - Se actualiza con lista de nodos existentes en tiempo real
  - Permite selección múltiple de nodos
  - Callback actualiza opciones cuando se agregan/eliminan filas
  - Muestra nodos seleccionados como texto en celda principale conductor/guardia: Totalmente editables

### Recálculo Automático
Cada vez que se editan nodos:
1. Se invalida cache DGE
2. Se regeneran gráficos
3. Se recalculan dimensiones afectadas
4. Se propaga a DME si ya fue calculado

## Estado Actual
- [x] Documento creado
- [x] Revisión de arquitectura completada
- [x] FASE 1 COMPLETADA
  - [x] 1.1: NodoEstructural modificado (rotacion_eje_z, es_editado, conectado_a como lista)
  - [x] 1.2: Métodos de gestión de nodos agregados
  - [x] 1.3: Rotación de cargas implementada en EstructuraAEA_Mecanica
- [x] FASE 2 COMPLETADA
  - [x] 2.1: estructura_manager con guardar/cargar nodos_editados
  - [x] 2.2: calculo_cache incluye nodos_editados en hash y cache DGE
- [x] FASE 3 COMPLETADA (Backend)
  - [x] 3.1: Función aplicar_nodos_editados implementada
  - [x] 3.2: ejecutar_calculo_dge aplica nodos editados automáticamente
  - [x] 3.3: calcular_diseno_geometrico aplica nodos editados
  - [x] 3.4: Callback guardar_cambios_nodos_modal
- [x] FASE 4 COMPLETADA (UI Básica)
  - [x] 4.1: Botón "Editar Nodos" y modal con tabla editable
  - [x] 4.2: Callbacks básicos (abrir/cerrar modal, guardar cambios)
  - [ ] 4.3: Submodal de conexiones (opcional, se puede usar texto separado por comas)
- [x] FASE 5 COMPLETADA (Integración y Validación)
  - [x] 5.1: Validaciones completas implementadas
  - [x] 5.2: Flujo completo funcional
  - [x] 5.3: Propagación automática a DME/ADC/SPH
- [x] FASE 6 COMPLETADA (Visualización)
  - [x] 6.1: Nodos editados con color naranja y marcador cuadrado
  - [x] 6.2: Flechas rojas indicando dirección de rotación de cargas
  - [x] 6.3: Líneas punteadas naranjas mostrando conexiones entre nodos
  - [x] 6.4: Leyenda actualizada con elementos de nodos editados
  - [x] 6.5: Etiquetas con asterisco (*) para nodos editados en gráficos y tablas

## Implementación Completada - TODAS LAS FASES

**Sistema completo con Fases 1-6 implementadas:**
- ✅ **Fase 1 - Backend**: Gestión completa de nodos editados con rotación de cargas
- ✅ **Fase 2 - Persistencia**: Guardado/carga automático en JSON y cache
- ✅ **Fase 3 - Controlador**: Aplicación automática en flujo DGE
- ✅ **Fase 4 - UI**: Modal con tabla editable (conexiones como texto separado por comas)
- ✅ **Fase 5 - Validaciones**: Completas con mensajes específicos y propagación automática
- ✅ **Fase 6 - Visualización**: Nodos editados distinguibles visualmente en todos los gráficos

**Características visuales implementadas:**
- Nodos editados: Color naranja (#FF6B00) con marcador cuadrado
- Rotación de cargas: Flechas rojas indicando dirección
- Conexiones: Líneas punteadas naranjas entre nodos conectados
- Etiquetas: Asterisco (*) marca nodos editados
- Leyenda: Incluye todos los elementos de nodos editados
