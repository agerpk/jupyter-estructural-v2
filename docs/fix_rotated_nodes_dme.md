# Fix: Nodos Rotados en Cálculo DME

## Problema Identificado

En la vista DME, las cargas de los nodos custom con cables rotados (C1A, C2A, C3A con `rotacion_eje_z = -90°`) no se estaban sumando correctamente en el cálculo de reacciones finales.

### Síntomas
- Los nodos individuales mostraban cargas correctas (ej: C1A con Fx=557.26, Fy=0)
- La tabla final de reacciones mostraba valores "fantasma" (ej: Fx=1.1 en lugar de la suma real)

## Causa Raíz

El método `calcular_reacciones_tiros_cima()` en `EstructuraAEA_Mecanica.py` estaba aplicando rotación doble:

1. **Primera rotación**: Durante `asignar_cargas_hipotesis()`, las fuerzas ya se rotan del sistema local del cable al sistema global de la estructura
2. **Segunda rotación**: En `calcular_reacciones_tiros_cima()`, se volvía a aplicar rotación con `obtener_cargas_hipotesis_rotadas(nombre_hipotesis, "global")`

## Solución Implementada

### 1. Simplificar `obtener_cargas_hipotesis_rotadas()`
```python
# Antes: aplicaba rotación adicional
fx_rot, fy_rot, fz_rot = self.rotar_vector(cargas["fx"], cargas["fy"], cargas["fz"])

# Después: las cargas ya están en sistema global
return cargas  # Sin rotación adicional
```

### 2. Simplificar cálculo de reacciones
```python
# Antes: lógica condicional para nodos rotados
if nodo_obj.rotacion_eje_x != 0 or nodo_obj.rotacion_eje_y != 0 or nodo_obj.rotacion_eje_z != 0:
    cargas_rotadas = nodo_obj.obtener_cargas_hipotesis_rotadas(nombre_hipotesis, "global")

# Después: usar cargas directamente (ya rotadas)
cargas = nodo_obj.obtener_cargas_hipotesis(nombre_hipotesis)
```

## Verificación

Después del fix, la tabla de reacciones debe mostrar:
- Fx: suma correcta incluyendo fuerzas rotadas de nodos custom
- Fy: suma correcta incluyendo fuerzas rotadas de nodos custom
- Valores coherentes con las cargas individuales mostradas en "Cargas en Nodos"

## Archivos Modificados

- `NodoEstructural.py`: Método `obtener_cargas_hipotesis_rotadas()`
- `EstructuraAEA_Mecanica.py`: Método `calcular_reacciones_tiros_cima()`