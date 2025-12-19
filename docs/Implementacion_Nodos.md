# Implementación: Sistema de Nodos Estructurales

## Resumen Ejecutivo

Sistema completo para gestión de nodos estructurales con edición manual, rotaciones, cargas por hipótesis y visualización 3D interactiva.

**Estado**: ✅ COMPLETADO - Todas las fases implementadas

---

## Arquitectura del Sistema

### Clase `NodoEstructural`
Ubicación: `NodoEstructural.py` (raíz del proyecto)

**Propiedades principales**:
- `nombre` (str): Identificador único
- `coordenadas` (tuple): (x, y, z) en metros
- `tipo_nodo` (str): conductor, guardia, base, cruce, general, viento
- `cable_asociado` (Cable_AEA): Cable asociado al nodo
- `rotacion_eje_x`, `rotacion_eje_y`, `rotacion_eje_z` (float): Rotaciones en grados
- `angulo_quiebre` (float): Ángulo de quiebre del cable
- `tipo_fijacion` (str): suspensión o retención
- `es_editado` (bool): Flag para nodos editados manualmente
- `conectado_a` (list): Lista de nombres de nodos conectados
- `cargas` (list): Lista de objetos `Carga` con valores por hipótesis

### Clase `Carga`
Representa cargas con valores para múltiples hipótesis.

**Propiedades**:
- `nombre` (str): Identificador de la carga (ej: "Peso", "Viento", "Tiro")
- `hipotesis` (list): Lista de códigos de hipótesis
- `fuerzas_x`, `fuerzas_y`, `fuerzas_z` (list): Fuerzas en daN por hipótesis
- `momentos_x`, `momentos_y`, `momentos_z` (list): Momentos en daN·m por hipótesis

---

## Funcionalidades Implementadas

### 1. Gestión de Nodos (Backend)

**Archivo**: `EstructuraAEA_Geometria.py`

**Métodos**:
- `agregar_nodo_manual()`: Crea nodo con validaciones
- `editar_nodo()`: Modifica propiedades de nodo existente
- `eliminar_nodo()`: Elimina nodo (excepto BASE)
- `exportar_nodos_editados()`: Serializa nodos editados a dict
- `importar_nodos_editados()`: Carga nodos desde lista de dicts

### 2. Rotación de Cargas

**Archivo**: `EstructuraAEA_Mecanica.py`

**Método**: `_rotar_carga_eje_z(fx, fy, fz, angulo_grados)`
- Rota vector de carga en eje Z (plano XY)
- Aplicado automáticamente en `asignar_cargas_hipotesis()`
- Afecta cargas transversales y longitudinales del cable

**Uso**: Nodos con `rotacion_eje_z != 0` tienen sus cargas rotadas automáticamente al sistema global.

### 3. Persistencia

**Archivo**: `utils/estructura_manager.py`

**Métodos**:
- `guardar_nodos_editados(nodos_list)`: Guarda en JSON
- `cargar_nodos_editados()`: Carga desde JSON

**Estructura JSON**:
```json
{
  "nodos_editados": [
    {
      "nombre": "C1_R",
      "tipo": "general",
      "coordenadas": [1.3, 0.0, 11.378],
      "cable_id": "Al/Ac 70/12",
      "rotacion_eje_x": 0.0,
      "rotacion_eje_y": 0.0,
      "rotacion_eje_z": 0.0,
      "angulo_quiebre": 0.0,
      "tipo_fijacion": "suspensión",
      "conectado_a": [],
      "es_editado": true
    }
  ]
}
```

### 4. Cache

**Archivo**: `utils/calculo_cache.py`

- `nodos_editados` incluido en hash de parámetros DGE
- Cache se invalida automáticamente cuando nodos cambian
- Nodos completos guardados en cache DGE

### 5. Editor de Nodos (UI)

**Archivo**: `components/vista_diseno_geometrico.py`

**Componentes**:
- Botón "Editar Nodos" en vista DGE
- Modal con tabla editable (DataTable)
- Columnas: Nombre, Tipo, X, Y, Z, Cable, Rot. Z, Áng. Quiebre, Fijación, Conectado A
- Botones: Guardar, Cancelar
- Agregar/eliminar filas con `row_deletable=True`

**Callbacks** (`controllers/geometria_controller.py`):
- `toggle_modal_editor_nodos()`: Abre/cierra modal
- `guardar_cambios_nodos()`: Valida, guarda y recalcula DGE

### 6. Visualización

**Archivo**: `EstructuraAEA_Graficos.py`

**Características visuales**:
- Nodos editados: Color naranja (#FF6B00), marcador cuadrado
- Nodos originales: Colores por tipo (azul conductor, verde guardia, negro estructura)
- Rotación de cargas: Flechas rojas indicando dirección
- Conexiones: Líneas punteadas naranjas entre nodos conectados
- Etiquetas: Asterisco (*) marca nodos editados
- Leyenda: Incluye todos los elementos

### 7. Gráfico 3D Interactivo

**Cambio**: De Matplotlib 2D → Plotly 3D isométrico

**Características**:
- Vista isométrica: `camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))`
- Interactividad: Rotar, zoom, pan, hover con coordenadas
- Todos los nodos visibles (X, Y, Z)
- Plano de terreno (Z=0) semitransparente
- Guardado dual: PNG (exportar) + JSON (interactividad)

**Archivos modificados**:
- `EstructuraAEA_Graficos.py`: `graficar_nodos_coordenadas()` retorna figura Plotly
- `controllers/geometria_controller.py`: Captura retorno directo
- `utils/calculo_cache.py`: Guarda JSON con `fig.write_json()`
- `components/vista_diseno_geometrico.py`: Carga con `dcc.Graph()`

---

## Flujo de Trabajo

### Flujo Normal
1. Usuario ejecuta DGE → Genera nodos automáticos
2. Usuario presiona "Editar Nodos" → Abre modal con tabla
3. Usuario modifica celdas inline (coordenadas, cables, rotaciones)
4. Usuario presiona "Guardar":
   - Sistema valida datos
   - Marca `es_editado=True` automáticamente
   - Guarda en `actual.estructura.json` y `{titulo}.estructura.json`
   - Actualiza cache de objetos EstructuraAEA
   - Recalcula DGE con nodos editados
   - Regenera gráficos y tablas
5. Nodos editados se aplican automáticamente en DME, ADC, SPH

### Aplicación Automática
**Archivo**: `controllers/geometria_controller.py`

**Función**: `aplicar_nodos_editados(estructura_geometria, nodos_editados_list)`
- Llamada después de `dimensionar_unifilar()`
- Aplica cada nodo editado (agregar/editar)
- Marca automáticamente con `es_editado=True`

---

## Validaciones

**Archivo**: `controllers/geometria_controller.py`

- Coordenadas no negativas en Z
- Nombres únicos y no vacíos
- Tipos de nodo válidos
- Rotación 0-360°
- Cable existe en librería
- Nodos conectados existen

---

## Propagación a Etapas Posteriores

### DME (Diseño Mecánico)
- Usa nodos editados para asignar cargas
- Aplica rotación de cargas según `rotacion_eje_z`
- Calcula reacciones con nodos editados

### ADC (Árboles de Carga)
- Usa estructura_mecanica con nodos editados
- Propagación automática

### SPH (Selección de Postes)
- Usa reacciones calculadas con nodos editados
- Propagación automática

---

## Troubleshooting

### Modal no abre sin DGE ejecutado
**Solución**: Toast de advertencia implementado
- Mensaje: "Ejecute primero el cálculo DGE para crear nodos que luego puedan ser editados."
- Color: warning (amarillo)

### Gráfico 3D no aparece en cache
**Causa**: Solo se guardaba PNG, faltaba JSON para Plotly
**Solución**: Guardar dual format (PNG + JSON)
```python
fig.write_image(str(png_path))
fig.write_json(str(json_path))
```

### Nodos con espacios en nombre de estructura
**Solución**: Sanitizar nombres reemplazando espacios con guiones bajos
```python
nombre_estructura.replace(' ', '_')
```

### Dash State desactualizado
**Solución**: Recargar desde archivo al inicio de callbacks críticos
```python
estructura_actual = state.estructura_manager.cargar_estructura(DATA_DIR / "actual.estructura.json")
```

---

## Archivos del Sistema

### Core
- `NodoEstructural.py` - Clases NodoEstructural y Carga
- `EstructuraAEA_Geometria.py` - Gestión de nodos
- `EstructuraAEA_Mecanica.py` - Rotación de cargas
- `EstructuraAEA_Graficos.py` - Visualización

### Persistencia
- `utils/estructura_manager.py` - Guardar/cargar JSON
- `utils/calculo_cache.py` - Cache con nodos editados

### Controlador
- `controllers/geometria_controller.py` - Lógica de edición y callbacks

### Vista
- `components/vista_diseno_geometrico.py` - UI del editor

---

## Ejemplo de Uso

### Crear nodo con rotación
```python
nodo = NodoEstructural("C1A", (0, 1.3, 7.0), "conductor", rotacion_eje_z=90.0)
```

### Agregar carga
```python
carga_peso = Carga("Peso")
carga_peso.agregar_hipotesis("HIP_A0", fx=0, fy=0, fz=-200)
nodo.agregar_carga(carga_peso)
```

### Obtener cargas rotadas
```python
# Sistema local (sin rotar)
cargas_local = nodo.obtener_cargas_hipotesis("HIP_A0")

# Sistema global (rotado)
cargas_global = nodo.obtener_cargas_hipotesis_rotadas("HIP_A0", "global")
```

---

## Mejoras Futuras (Opcionales)

- Submodal de conexiones con checkboxes (actualmente texto separado por comas)
- Rotaciones en ejes X e Y (estructura existe, solo Z implementado)
- Momentos directos en nodos (estructura existe, no se usa activamente)
- Validación geométrica de nodos
- Editor gráfico 3D interactivo
- Historial de cambios en nodos
- Templates de nodos

---

## Fecha de Implementación

Diciembre 2024 - Enero 2025

**Todas las fases completadas**: Backend, Persistencia, Controlador, UI, Validaciones, Visualización
