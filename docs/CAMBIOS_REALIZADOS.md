# Cambios Realizados - Fix Cache Alerts y FutureWarnings

## Problema 1: Mensajes "cargado desde cache" aparecen siempre
**Solución**: Agregar parámetro `mostrar_alerta_cache` (default=False) a todas las funciones de generación de resultados.

### Archivos modificados:

1. **models/app_state.py**
   - Agregada flag `self.cargado_desde_cache = False`

2. **components/vista_calcular_todo.py**
   - `generar_resultados_cmc_lista()`: Agregado parámetro `mostrar_alerta_cache=False`
   - `cargar_resultados_modulares()`: Pasa `mostrar_alerta_cache=True` para todas las vistas
   - Importado `StringIO` al inicio para evitar FutureWarning

3. **components/vista_diseno_geometrico.py**
   - `generar_resultados_dge()`: Agregado parámetro `mostrar_alerta_cache=False`
   - Alerta solo se muestra si `mostrar_alerta_cache=True`

4. **components/vista_diseno_mecanico.py**
   - `generar_resultados_dme()`: Agregado parámetro `mostrar_alerta_cache=False`
   - Alerta solo se muestra si `mostrar_alerta_cache=True`

5. **components/vista_arboles_carga.py**
   - `generar_resultados_arboles()`: Agregado parámetro `mostrar_alerta_cache=False`
   - Alerta solo se muestra si `mostrar_alerta_cache=True`

6. **controllers/calcular_todo_controller.py**
   - `cargar_desde_cache()`: Activa `state.cargado_desde_cache = True`
   - `ejecutar_calculo_completo()`: Desactiva `state.cargado_desde_cache = False`
   - Pasa `mostrar_alerta_cache=False` en todos los cálculos nuevos
   - Pasa `mostrar_alerta_cache=True` solo cuando se carga desde cache

## Problema 2: FutureWarning de pandas
**Solución**: Usar `StringIO` para leer JSON strings con pandas.

### Cambios:
```python
# Antes:
df = pd.read_json(json_string, orient='split')

# Después:
from io import StringIO
df = pd.read_json(StringIO(json_string), orient='split')
```

Aplicado en:
- `components/vista_calcular_todo.py` (3 lugares: conductor, guardia1, guardia2)

## Comportamiento esperado:

### Cálculo Nuevo (botón "Ejecutar Cálculo Completo"):
- ❌ NO muestra "✅ Resultados cargados desde cache"
- ✅ Muestra solo resultados frescos

### Carga desde Cache (botón "Cargar desde Cache"):
- ✅ Muestra "✅ Resultados cargados desde cache (parámetros sin cambios)"
- ✅ Indica vigencia del cache

## Testing:
1. Ejecutar "Calcular Todo" → No debe aparecer mensaje de cache
2. Ejecutar "Cargar desde Cache" → Debe aparecer mensaje de cache en todas las secciones
3. No deben aparecer FutureWarnings en consola
