# Fix: Árboles de Carga 3D - Conexiones y Generación

## Problemas Identificados

### 1. Reinicio de Vista sin Intervención del Usuario
**Síntoma**: Después de generar árboles, la vista se recarga automáticamente sin que el usuario haga nada.

**Causa**: El callback `cargar_arboles_desde_cache` estaba desactivado pero aún registrado, causando interferencias.

**Solución**: Ya estaba desactivado con `raise dash.exceptions.PreventUpdate` al inicio del callback.

### 2. Conexiones Erróneas Entre Nodos
**Síntoma**: Los árboles de carga 3D muestran conexiones que no coinciden con las definidas en DGE. Aparecen líneas entre nodos que no deberían estar conectados.

**Causa**: La función `dibujar_lineas_estructura_3d()` usaba lógica hardcodeada para determinar conexiones en lugar de usar el campo `conectado_a` de cada nodo.

**Solución**: 
- Modificar `dibujar_lineas_estructura_3d()` para aceptar parámetro `estructura_geometria`
- Si se proporciona `estructura_geometria`, iterar sobre `estructura_geometria.nodos` y usar `nodo.conectado_a` para dibujar conexiones
- Mantener lógica fallback para compatibilidad con código que no pasa `estructura_geometria`

```python
def dibujar_lineas_estructura_3d(fig, nodes_key, estructura_geometria=None):
    if estructura_geometria and hasattr(estructura_geometria, 'nodos'):
        for nombre_nodo, nodo in estructura_geometria.nodos.items():
            if hasattr(nodo, 'conectado_a') and nodo.conectado_a:
                for nodo_destino in nodo.conectado_a:
                    if nombre_nodo in nodes_key and nodo_destino in nodes_key:
                        # Dibujar línea
```

### 3. Error al Generar Después de Editar Conexiones en DGE
**Síntoma**: Después de editar nodos y conexiones en DGE, al ir a ADC y generar árboles, sale error "No se generaron imágenes 3D".

**Causa**: Nodos editados (como C1A, C2A, C3A) no tienen cargas asignadas porque son nodos personalizados que no participan en cálculos mecánicos. Al intentar obtener cargas de estos nodos, se generaba error o se saltaban todas las hipótesis.

**Solución**: 
- Verificar que el nodo tenga `cargas_dict` antes de intentar obtener cargas
- Solo procesar nodos que realmente tienen cargas asignadas

```python
for nombre_nodo, nodo in estructura_mecanica.geometria.nodos.items():
    # Solo procesar nodos que tienen cargas asignadas
    if not hasattr(nodo, 'cargas_dict') or not nodo.cargas_dict:
        continue
    # ... resto del código
```

### 4. No se Generaron Imágenes 3D
**Síntoma**: Mensaje "No se generaron imágenes 3D" al intentar generar árboles.

**Causa**: Combinación de los problemas 2 y 3 - nodos sin cargas causaban que `todas_cargas_hipotesis` quedara vacío.

**Solución**: Aplicar fix del problema 3 para filtrar nodos sin cargas.

## Archivos Modificados

### `utils/arboles_carga.py`
1. **`dibujar_lineas_estructura_3d()`**: Agregar parámetro `estructura_geometria` y usar `conectado_a`
2. **`generar_arboles_carga()`**: Agregar parámetro `estructura_geometria` y pasarlo a funciones hijas
3. **`generar_arbol_3d_interactivo()`**: Agregar parámetro `estructura_geometria` y pasarlo a `dibujar_lineas_estructura_3d()`
4. **Recolección de cargas**: Verificar `cargas_dict` antes de procesar nodos

### `controllers/arboles_controller.py`
1. **`generar_arboles_callback()`**: Pasar `state.calculo_objetos.estructura_geometria` a `generar_arboles_carga()`

## Verificación

1. Editar nodos en DGE y definir conexiones personalizadas
2. Ir a vista ADC
3. Generar árboles de carga con ADC_3D activado
4. Verificar que:
   - Las conexiones coinciden exactamente con las definidas en `conectado_a`
   - Se genera el gráfico 3D interactivo
   - No hay errores en consola
   - No hay recargas automáticas de vista

## Key Takeaways

- **Usar datos de nodos**: Siempre usar `conectado_a` de cada nodo en lugar de lógica hardcodeada
- **Verificar existencia de datos**: Antes de acceder a `cargas_dict`, verificar que exista
- **Pasar contexto completo**: Pasar `estructura_geometria` a funciones de visualización para acceder a información completa de nodos
- **Nodos editados**: Los nodos editados pueden no tener cargas asignadas - manejar este caso gracefully
