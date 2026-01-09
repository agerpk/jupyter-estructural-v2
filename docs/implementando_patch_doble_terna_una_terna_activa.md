# Plan de Implementación: Patch Doble Terna con Una Terna Activa

## Objetivo
Implementar parámetro `doble_terna_una_terna_activa` (True/False, default False) que, cuando está activo en estructuras "Terminal Doble", anula todas las cargas de la terna del lado negativo X en DME.

## Alcance
- Agregar nuevo parámetro en todos los puntos de configuración
- Modificar lógica de asignación de cargas en DME
- Integrar en flujo completo de cálculo

---

## 1. AGREGAR PARÁMETRO EN PLANTILLA

### Archivo: `data/plantilla.estructura.json`

**Ubicación**: Después de `TIPO_ESTRUCTURA` (línea 2)

**Código a agregar**:
```json
"doble_terna_una_terna_activa": false,
```

**Justificación**: Va junto con `TIPO_ESTRUCTURA` porque es una configuración estructural que modifica el comportamiento de cálculo.

---

## 2. AGREGAR METADATOS EN PARAMETROS_MANAGER

### Archivo: `utils/parametros_manager.py`

**Ubicación**: En `PARAMETROS_METADATA`, después de `TIPO_ESTRUCTURA` (aprox. línea 30)

**Código a agregar**:
```python
"doble_terna_una_terna_activa": {
    "simbolo": "DT1A",
    "unidad": "-",
    "descripcion": "Doble terna con una terna activa (anula cargas lado X-)",
    "tipo": "bool",
    "categoria": "General"
},
```

**Justificación**: Define metadatos para que el parámetro aparezca en la tabla de parámetros con descripción clara.

---

## 3. AGREGAR CONTROL EN CONFIGURACIÓN

### Archivo: `config/parametros_controles.py`

**Ubicación**: Después de `TIPO_ESTRUCTURA` en `CONTROLES_PARAMETROS`

**Código a agregar**:
```python
"doble_terna_una_terna_activa": {
    "tipo": "bool",
    "label": "Doble terna con una terna activa",
    "descripcion": "Anula cargas de la terna del lado X- en DME (solo Terminal Doble)",
    "default": False
},
```

**Justificación**: Define el control UI para el parámetro.

---

## 4. MODIFICAR LÓGICA DE ASIGNACIÓN DE CARGAS EN DME

### Archivo: `EstructuraAEA_Mecanica.py`

**Ubicación**: Método `asignar_cargas_hipotesis`, al inicio después de validaciones (aprox. línea 250)

**Código a agregar**:
```python
# Verificar si se debe anular cargas de una terna
anular_terna_negativa_x = False
if (self.geometria.tipo_estructura == "Terminal Doble" and 
    hasattr(self.geometria, 'doble_terna_una_terna_activa') and 
    self.geometria.doble_terna_una_terna_activa):
    anular_terna_negativa_x = True
    print("⚠️  Doble terna con una terna activa: anulando cargas de la terna del lado negativo X")
```

**Ubicación 2**: Dentro del loop de conductores, antes de calcular cargas (aprox. línea 450)

**Código a agregar**:
```python
# ANULAR CARGAS SI NODO EN LADO X- Y PARÁMETRO ACTIVO
if anular_terna_negativa_x:
    nodo_obj = self.geometria.nodos.get(nodo_nombre)
    if nodo_obj and nodo_obj.x < 0:
        # Nodo en lado X negativo - anular todas las cargas
        peso_x, peso_y, peso_z = 0.0, 0.0, 0.0
        viento_x, viento_y, viento_z = 0.0, 0.0, 0.0
        tiro_x, tiro_y, tiro_z = 0.0, 0.0, 0.0
        
        # Guardar cargas nulas
        nodo_obj.obtener_carga("Peso").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
        nodo_obj.obtener_carga("Viento").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
        nodo_obj.obtener_carga("Tiro").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
        
        if not hasattr(nodo_obj, 'cargas_dict'):
            nodo_obj.cargas_dict = {}
        nodo_obj.cargas_dict[nombre_completo] = [0.0, 0.0, 0.0]
        cargas_hipotesis[nodo_nombre] = [0.0, 0.0, 0.0]
        
        continue  # Saltar al siguiente nodo
```

**Ubicación 3**: Dentro del loop de guardias, antes de calcular cargas (aprox. línea 650)

**Código a agregar** (mismo código que para conductores):
```python
# ANULAR CARGAS SI NODO EN LADO X- Y PARÁMETRO ACTIVO
if anular_terna_negativa_x:
    nodo_obj = self.geometria.nodos.get(nodo_nombre)
    if nodo_obj and nodo_obj.x < 0:
        # Nodo en lado X negativo - anular todas las cargas
        peso_x, peso_y, peso_z = 0.0, 0.0, 0.0
        viento_x, viento_y, viento_z = 0.0, 0.0, 0.0
        tiro_x, tiro_y, tiro_z = 0.0, 0.0, 0.0
        
        # Guardar cargas nulas
        nodo_obj.obtener_carga("Peso").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
        nodo_obj.obtener_carga("Viento").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
        nodo_obj.obtener_carga("Tiro").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
        
        if not hasattr(nodo_obj, 'cargas_dict'):
            nodo_obj.cargas_dict = {}
        nodo_obj.cargas_dict[nombre_completo] = [0.0, 0.0, 0.0]
        cargas_hipotesis[nodo_nombre] = [0.0, 0.0, 0.0]
        
        continue  # Saltar al siguiente nodo
```

**Justificación**: Anula todas las cargas (peso, viento, tiro) para nodos con coordenada X negativa cuando el parámetro está activo.

---

## 5. PASAR PARÁMETRO A GEOMETRÍA

### Archivo: `EstructuraAEA_Geometria.py`

**Ubicación**: Método `__init__`, después de asignar `tipo_estructura` (aprox. línea 50)

**Código a agregar**:
```python
self.doble_terna_una_terna_activa = parametros.get("doble_terna_una_terna_activa", False)
```

**Justificación**: Almacena el parámetro en la instancia de geometría para que esté disponible en mecánica.

---

## 6. ACTUALIZAR VISTA AJUSTAR PARÁMETROS (TABLA)

### Archivo: `components/tabla_parametros.py`

**Acción**: No requiere cambios - el parámetro aparecerá automáticamente en la tabla porque está definido en `PARAMETROS_METADATA`.

**Verificación**: El parámetro debe aparecer en la categoría "General" con tipo bool (checkbox).

---

## 7. ACTUALIZAR VISTA CREAR FAMILIA

### Archivo: `components/vista_familia_estructuras.py`

**Acción**: No requiere cambios - la tabla de familia usa el mismo sistema de `ParametrosManager` que la tabla de parámetros.

**Verificación**: El parámetro debe aparecer en la tabla de familia junto con otros parámetros generales.

---

## 8. ACTUALIZAR CONTROLLERS

### Archivo: `controllers/parametros_controller.py`

**Acción**: No requiere cambios - el controller usa `ParametrosManager.tabla_a_estructura()` que procesa automáticamente todos los parámetros definidos en `PARAMETROS_METADATA`.

**Verificación**: Al guardar parámetros, el nuevo campo debe incluirse en el JSON.

---

## 9. ACTUALIZAR CALCULAR TODO

### Archivo: `controllers/calcular_todo_controller.py`

**Acción**: No requiere cambios - el flujo de cálculo pasa `estructura_actual` completo a todos los cálculos, incluyendo el nuevo parámetro.

**Verificación**: El parámetro debe estar disponible en `estructura_actual` cuando se ejecuta DME desde "Calcular Todo".

---

## 10. ACTUALIZAR CONTROLLER DME

### Archivo: `controllers/mecanica_controller.py`

**Ubicación**: Método `calcular_diseno_mecanico`, al crear objetos de cálculo (aprox. línea 100)

**Verificación**: Asegurar que `estructura_actual` se pasa completo a `EstructuraAEA_Geometria`, incluyendo el nuevo parámetro.

**Código existente** (no modificar, solo verificar):
```python
estructura_geometria = EstructuraAEA_Geometria(
    parametros=estructura_actual,
    cable_conductor=cable_conductor,
    cable_guardia1=cable_guardia1,
    cable_guardia2=cable_guardia2
)
```

---

## 11. TESTING MANUAL (USUARIO)

### Test Manual 1: Verificar parámetro en tabla
**Objetivo**: Confirmar que el parámetro aparece y se puede editar

1. Abrir aplicación
2. Ir a vista "Ajustar Parámetros"
3. Buscar parámetro "doble_terna_una_terna_activa" en categoría "General"
4. Verificar que aparece como checkbox con descripción clara
5. Cambiar valor a True y guardar
6. Recargar estructura y verificar que el valor se guardó

**Resultado esperado**: ✅ Parámetro visible, editable y persistente

---

### Test Manual 2: Verificar anulación de cargas (parámetro activo)
**Objetivo**: Confirmar que las cargas se anulan correctamente

1. Cargar o crear estructura "Terminal Doble"
2. Ir a "Ajustar Parámetros"
3. Activar `doble_terna_una_terna_activa = True`
4. Guardar parámetros
5. Ir a vista "Consola" (para ver mensajes)
6. Ejecutar DME
7. Verificar mensaje en consola: "⚠️ Doble terna con una terna activa: anulando cargas de la terna del lado negativo X"
8. Revisar resultados de DME - verificar que nodos con X < 0 tienen cargas = 0

**Resultado esperado**: ✅ Mensaje visible, cargas anuladas en lado X-

---

### Test Manual 3: Verificar comportamiento por defecto (parámetro inactivo)
**Objetivo**: Confirmar que el comportamiento normal no se afecta

1. Cargar o crear estructura "Terminal Doble"
2. Ir a "Ajustar Parámetros"
3. Desactivar `doble_terna_una_terna_activa = False`
4. Guardar parámetros
5. Ejecutar DME
6. Verificar que NO aparece mensaje de anulación en consola
7. Verificar que nodos con X < 0 tienen cargas normales (no cero)

**Resultado esperado**: ✅ Sin mensaje, cargas normales en ambos lados

---

### Test Manual 4: Verificar en "Calcular Todo"
**Objetivo**: Confirmar integración en flujo completo

1. Cargar estructura "Terminal Doble"
2. Activar `doble_terna_una_terna_activa = True`
3. Guardar parámetros
4. Ir a vista "Calcular Todo"
5. Ejecutar cálculo completo
6. Verificar mensaje en consola durante DME
7. Verificar resultados de DME en vista "Calcular Todo"

**Resultado esperado**: ✅ Funciona correctamente en flujo orquestado

---

### Test Manual 5: Verificar que NO afecta otros tipos de estructura
**Objetivo**: Confirmar que solo aplica a "Terminal Doble"

1. Cargar estructura "Suspensión Recta" o "Angular"
2. Activar `doble_terna_una_terna_activa = True`
3. Ejecutar DME
4. Verificar que NO aparece mensaje de anulación
5. Verificar que cargas son normales

**Resultado esperado**: ✅ Parámetro ignorado en otros tipos de estructura

---

## 12. DOCUMENTACIÓN

### Archivo: `docs/parametro_doble_terna_una_terna_activa.md`

**Crear nuevo archivo** con documentación del parámetro:

```markdown
# Parámetro: doble_terna_una_terna_activa

## Descripción
Parámetro booleano que controla el comportamiento de cálculo de cargas en estructuras "Terminal Doble".

## Comportamiento
- **False (default)**: Todas las ternas se cargan normalmente
- **True**: Anula todas las cargas (peso, viento, tiro) de la terna del lado negativo X

## Aplicación
- Solo aplica a estructuras con `TIPO_ESTRUCTURA = "Terminal Doble"`
- Afecta el cálculo de DME (Diseño Mecánico de Estructura)
- Los nodos con coordenada X < 0 quedan completamente descargados

## Uso
1. Configurar en vista "Ajustar Parámetros" → Categoría "General"
2. O editar directamente en archivo `.estructura.json`:
   ```json
   "doble_terna_una_terna_activa": true
   ```

## Mensaje de Consola
Cuando está activo, imprime:
```
⚠️  Doble terna con una terna activa: anulando cargas de la terna del lado negativo X
```

## Casos de Uso
- Análisis de estructuras con una terna fuera de servicio
- Estudios de falla de una terna
- Dimensionado conservador con carga asimétrica
```

---

## 13. RESUMEN DE ARCHIVOS MODIFICADOS

### Archivos a modificar:
1. ✅ `data/plantilla.estructura.json` - Agregar parámetro default
2. ✅ `utils/parametros_manager.py` - Agregar metadatos
3. ✅ `config/parametros_controles.py` - Agregar control UI
4. ✅ `EstructuraAEA_Geometria.py` - Almacenar parámetro en instancia
5. ✅ `EstructuraAEA_Mecanica.py` - Implementar lógica de anulación

### Archivos que NO requieren cambios:
- `components/tabla_parametros.py` - Usa `PARAMETROS_METADATA` automáticamente
- `components/vista_familia_estructuras.py` - Usa `PARAMETROS_METADATA` automáticamente
- `controllers/parametros_controller.py` - Usa `ParametrosManager` automáticamente
- `controllers/calcular_todo_controller.py` - Pasa `estructura_actual` completo
- `controllers/mecanica_controller.py` - Pasa `estructura_actual` completo

### Archivos nuevos:
- `docs/parametro_doble_terna_una_terna_activa.md` - Documentación

---

## 14. ORDEN DE IMPLEMENTACIÓN

### Paso 1: Configuración base
1. Modificar `data/plantilla.estructura.json`
2. Modificar `utils/parametros_manager.py`
3. Modificar `config/parametros_controles.py`

### Paso 2: Lógica de cálculo
4. Modificar `EstructuraAEA_Geometria.py`
5. Modificar `EstructuraAEA_Mecanica.py`

### Paso 3: Testing
6. Ejecutar tests de validación (sección 11)

### Paso 4: Documentación
7. Crear `docs/parametro_doble_terna_una_terna_activa.md`

---

## 15. CRITERIOS DE ACEPTACIÓN

✅ El parámetro aparece en plantilla.estructura.json con valor false
✅ El parámetro aparece en tabla de parámetros (categoría General)
✅ El parámetro aparece en tabla de familia de estructuras
✅ Al activar el parámetro en "Terminal Doble", se imprime mensaje en consola
✅ Los nodos con X < 0 tienen cargas = 0 cuando parámetro activo
✅ Los nodos con X < 0 tienen cargas normales cuando parámetro inactivo
✅ El parámetro funciona en "Calcular Todo"
✅ El parámetro se guarda correctamente en archivos JSON
✅ El parámetro NO afecta otros tipos de estructura
✅ Documentación completa creada

---

## 16. NOTAS IMPORTANTES

### Identificación de nodos en lado X-
- Los nodos con `x < 0` son considerados del lado negativo X
- Esto incluye conductores (C1_L, C2_L, C3_L) y guardias (HG2 si x < 0)
- La verificación se hace con `nodo_obj.x < 0`

### Tipos de cargas anuladas
- **Peso**: Peso propio del cable + hielo
- **Viento**: Viento sobre cables
- **Tiro**: Tiro de cables (bilateral/unilateral)

### Compatibilidad
- El parámetro es compatible con todos los patrones de tiro existentes
- No interfiere con otros parámetros de configuración
- Es específico para "Terminal Doble" pero no causa errores en otros tipos

### Performance
- La verificación `if anular_terna_negativa_x` es muy rápida (O(1))
- No afecta performance de cálculo cuando está inactivo
- Reduce tiempo de cálculo cuando está activo (menos nodos a procesar)

---

## 17. TROUBLESHOOTING

### Problema: Parámetro no aparece en tabla
**Solución**: Verificar que `PARAMETROS_METADATA` en `parametros_manager.py` contiene el parámetro con categoría "General"

### Problema: Mensaje no aparece en consola
**Solución**: Verificar que `tipo_estructura == "Terminal Doble"` y parámetro es `True`

### Problema: Cargas no se anulan
**Solución**: Verificar que nodos tienen coordenada `x < 0` y que el código de anulación está antes del cálculo de cargas

### Problema: Parámetro no se guarda
**Solución**: Verificar que `ParametrosManager.tabla_a_estructura()` procesa el parámetro correctamente

---

## 18. EXTENSIONES FUTURAS

### Posibles mejoras:
1. Permitir seleccionar qué terna anular (X+ o X-)
2. Permitir anulación parcial (solo peso, solo viento, etc.)
3. Agregar visualización gráfica de nodos anulados
4. Agregar reporte de cargas anuladas en memoria de cálculo

### Parámetros relacionados:
- `TIPO_ESTRUCTURA`: Determina si el parámetro aplica
- `TERNA`: Debe ser "Doble" para que tenga sentido
- `DISPOSICION`: Afecta qué nodos están en X-

---

## FIN DEL PLAN
