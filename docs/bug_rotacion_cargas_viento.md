# Bug: Rotación de Cargas de Viento en Nodos Rotados

## Problema Identificado

Los nodos con `rotacion_eje_z = 90°` (C1A, C2A, C3A) muestran cargas de viento idénticas a los nodos sin rotación del mismo conductor, cuando deberían tener las componentes X e Y intercambiadas.

## Análisis del Código

### Estructura Actual (actual.estructura.json)

Nodos rotados 90° en eje Z:
- C1A: coordenadas (0.0, 1.3, 7.01), rotacion_eje_z: 90.0
- C2A: coordenadas (0.0, 0.0, 7.01), rotacion_eje_z: 90.0  
- C3A: coordenadas (0.0, -1.3, 7.01), rotacion_eje_z: 90.0

Nodos sin rotación:
- C1_R: coordenadas (1.3, 0.0, 11.378), rotacion_eje_z: 0.0
- C1_L: coordenadas (-1.3, 0.0, 11.378), rotacion_eje_z: 0.0

### Flujo de Cálculo de Cargas

1. **Asignación de cargas** (`EstructuraAEA_Mecanica.py`, línea ~300-500):
   - Las cargas se calculan en el sistema LOCAL del cable
   - Para viento transversal: carga en X (perpendicular al cable)
   - Para viento longitudinal: carga en Y (paralelo al cable)
   - Las cargas se guardan SIN rotar en `nodo.obtener_carga("Viento").agregar_hipotesis(...)`

2. **Cálculo de reacciones** (`EstructuraAEA_Mecanica.py`, línea 336):
   ```python
   if nodo_obj.rotacion_eje_x != 0 or nodo_obj.rotacion_eje_y != 0 or nodo_obj.rotacion_eje_z != 0:
       cargas_rotadas = nodo_obj.obtener_cargas_hipotesis_rotadas(nombre_hipotesis, "global")
   ```

3. **Rotación de cargas** (`NodoEstructural.py`, línea 283):
   ```python
   # Rotar al sistema global
   fx_rot, fy_rot, fz_rot = self.rotar_vector(
       cargas["fx"], cargas["fy"], cargas["fz"], aplicar_rotacion_inversa=True
   )
   ```

4. **Método rotar_vector** (`NodoEstructural.py`, línea 254):
   ```python
   # Determinar ángulos (invertir si es rotación inversa)
   factor = -1 if aplicar_rotacion_inversa else 1
   rx = math.radians(self.rotacion_eje_x * factor)
   ry = math.radians(self.rotacion_eje_y * factor)
   rz = math.radians(self.rotacion_eje_z * factor)
   ```

## Causa Raíz

El parámetro `aplicar_rotacion_inversa=True` invierte el signo del ángulo de rotación:
- Rotación almacenada: +90° (cable rotado 90° antihorario)
- Con `aplicar_rotacion_inversa=True`: se aplica -90° (rotación horaria)

**Esto es INCORRECTO** porque:
- Las cargas están en sistema LOCAL del cable (rotado 90°)
- Para transformar al sistema GLOBAL, necesitamos aplicar la MISMA rotación (+90°), no la inversa
- La rotación inversa sería necesaria si quisiéramos ir de GLOBAL a LOCAL

## Ejemplo Numérico

Cable rotado 90° en eje Z con viento transversal:
- Sistema LOCAL del cable: Viento_X = 100 daN (perpendicular al cable)
- Sistema GLOBAL esperado: Viento_Y = 100 daN (porque el cable apunta en Y)

Con código actual (`aplicar_rotacion_inversa=True`):
```
rz = -90° (invertido)
fx_rot = fx * cos(-90°) - fy * sin(-90°) = 100 * 0 - 0 * (-1) = 0
fy_rot = fx * sin(-90°) + fy * cos(-90°) = 100 * (-1) + 0 * 0 = -100
```
Resultado: (0, -100, 0) ❌ INCORRECTO

Con código corregido (`aplicar_rotacion_inversa=False`):
```
rz = +90°
fx_rot = fx * cos(90°) - fy * sin(90°) = 100 * 0 - 0 * 1 = 0
fy_rot = fx * sin(90°) + fy * cos(90°) = 100 * 1 + 0 * 0 = 100
```
Resultado: (0, 100, 0) ✅ CORRECTO

## Solución

Cambiar en `NodoEstructural.py`, línea 283:

```python
# ANTES (incorrecto)
fx_rot, fy_rot, fz_rot = self.rotar_vector(
    cargas["fx"], cargas["fy"], cargas["fz"], aplicar_rotacion_inversa=True
)

# DESPUÉS (correcto)
fx_rot, fy_rot, fz_rot = self.rotar_vector(
    cargas["fx"], cargas["fy"], cargas["fz"], aplicar_rotacion_inversa=False
)
```

## Verificación

Después de aplicar el fix, verificar que:
1. Nodos C1A, C2A, C3A (rotados 90°) tienen cargas de viento en Y
2. Nodos C1_R, C1_L (sin rotación) tienen cargas de viento en X
3. Las magnitudes son similares (mismo cable, misma altura)

## Archivos Afectados

- `NodoEstructural.py` - Línea 283 (método `obtener_cargas_hipotesis_rotadas`)
- `EstructuraAEA_Mecanica.py` - Línea 336 (llamada al método)

## Estado

✅ **RESUELTO** - 2025-01-18

### Cambio Aplicado

Archivo: `NodoEstructural.py`, línea 283

```python
# Rotar al sistema global (aplicar rotación directa, no inversa)
# Las cargas están en sistema local del cable, necesitamos transformarlas al sistema global
fx_rot, fy_rot, fz_rot = self.rotar_vector(
    cargas["fx"], cargas["fy"], cargas["fz"], aplicar_rotacion_inversa=False
)
mx_rot, my_rot, mz_rot = self.rotar_vector(
    cargas["mx"], cargas["my"], cargas["mz"], aplicar_rotacion_inversa=False
)
```

### Próximos Pasos

1. Ejecutar DGE para regenerar nodos
2. Ejecutar DME para recalcular reacciones
3. Verificar que nodos rotados 90° tienen cargas intercambiadas correctamente
4. Comparar magnitudes de cargas entre nodos rotados y no rotados
