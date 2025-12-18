# Fix: Mensajes de Cache

## Problema
Los mensajes "✅ Resultados cargados desde cache" aparecen siempre, incluso cuando se ejecuta un cálculo nuevo.

## Solución
Agregar parámetro `mostrar_alerta_cache` (default=False) a todas las funciones `generar_resultados_*()`:

### Archivos modificados:
1. ✅ `models/app_state.py` - Agregada flag `cargado_desde_cache`
2. ✅ `components/vista_calcular_todo.py` - CMC, DGE, DME, Árboles con parámetro
3. ✅ `components/vista_diseno_geometrico.py` - DGE con parámetro
4. ✅ `components/vista_diseno_mecanico.py` - DME con parámetro
5. ✅ `components/vista_arboles_carga.py` - Árboles con parámetro
6. ✅ `components/vista_seleccion_poste.py` - SPH no usa alerta (no requiere cambios)
7. ✅ `controllers/calcular_todo_controller.py` - Actualizado para pasar parámetros correctos

### Patrón de implementación:
```python
def generar_resultados_xxx(calculo_guardado, estructura_actual, mostrar_alerta_cache=False):
    # ...
    if mostrar_alerta_cache:
        output.append(ViewHelpers.crear_alerta_cache(...))
```

### Uso:
- `mostrar_alerta_cache=True` → Solo cuando se usa botón "Cargar desde Cache"
- `mostrar_alerta_cache=False` → Cuando se ejecuta cálculo nuevo

## FutureWarning de pandas
Cambiar:
```python
pd.read_json(json_string, orient='split')
```
Por:
```python
from io import StringIO
pd.read_json(StringIO(json_string), orient='split')
```
