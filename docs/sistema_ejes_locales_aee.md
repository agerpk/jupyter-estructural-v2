# Sistema de Ejes Locales en Análisis Estático de Esfuerzos (AEE)

## Problema Resuelto

OpenSeesPy entrega resultados de `eleForce()` en **ejes locales** del elemento, no en ejes globales. Esto causaba:
- **Subestimación de flexión** en postes verticales
- **Sobreestimación de torsión** donde no existe
- **Interpretación incorrecta** de momentos

## Solución Implementada

### 1. Cálculo Explícito de Ejes Locales

Para cada elemento, se calculan los ejes locales siguiendo la convención de OpenSeesPy:

```python
# Eje X local = dirección del elemento (de nodo i a nodo j)
vec_x_local = (cj - ci) / longitud

# Eje Z local = perpendicular a X y vector de referencia
vec_z_local = cross(vec_x_local, vec_ref) / norm(...)

# Eje Y local = perpendicular a X y Z
vec_y_local = cross(vec_z_local, vec_x_local)

# Matriz de transformación (columnas = ejes locales)
ejes_locales = [vec_x_local | vec_y_local | vec_z_local]
```

**Vector de referencia**:
- Elementos verticales (dz > dx, dy): `vec_ref = [0, 1, 0]` (Y global)
- Elementos horizontales/inclinados: `vec_ref = [0, 0, 1]` (Z global)

### 2. Transformación de Resultados a Ejes Globales

Los momentos se transforman de ejes locales a globales:

```python
# Momentos en ejes locales (de OpenSeesPy)
M_local = [Mx_local, My_local, Mz_local]

# Transformación a ejes globales
M_global = ejes_locales @ M_local

# Separación en Flexión y Torsión
T = |M_global · vec_x_local|  # Proyección en dirección del elemento
M_perp = M_global - T * vec_x_local  # Componente perpendicular
M = |M_perp|  # Magnitud de flexión
```

### 3. Interpretación Física Correcta

**Momento Flector (M)**:
- Componente del momento perpendicular al eje del elemento
- Causa flexión (dobla la barra)
- Crítico en postes verticales

**Momento Torsor (T)**:
- Componente del momento paralelo al eje del elemento
- Causa torsión (tuerce la barra)
- Generalmente pequeño en postes verticales

## Uso del Sistema

### Ejecutar Análisis

```python
analizador = AnalizadorEstatico(geometria, mecanica, parametros_aee)
resultado = analizador.resolver_sistema("HIP_Suspension_Recta_A0")

# resultado contiene:
# - 'valores': {nodo: [N, Q, M, T, ...]}
# - 'reacciones': {nodo_base: {Fx, Fy, Fz, Mx, My, Mz}}
# - 'elementos_dict': {elem_id: {..., 'ejes_locales': matriz 3x3}}
```

### Visualizar Ejes Locales

```python
# Generar diagrama de ejes locales
fig = analizador.generar_diagrama_ejes_locales(
    resultado['elementos_dict'], 
    "HIP_Suspension_Recta_A0"
)
fig.savefig("ejes_locales.png")
```

**Interpretación del diagrama**:
- **Rojo**: Eje X local (dirección longitudinal del elemento)
- **Verde**: Eje Y local
- **Azul**: Eje Z local

### Diagnóstico en Consola

Al ejecutar `resolver_sistema()`, se imprime:

```
📊 Diagnóstico de Ejes Locales (primeros 5 elementos):
   Elem 1 (BASE1-M1):
      X_local: [ 0.000,  0.000,  1.000]  # Vertical
      Y_local: [ 1.000,  0.000,  0.000]
      Z_local: [ 0.000,  1.000,  0.000]
   Elem 2 (M1-C1A):
      X_local: [ 0.707,  0.000,  0.707]  # Inclinado
      Y_local: [ 0.000,  1.000,  0.000]
      Z_local: [-0.707,  0.000,  0.707]
```

## Verificación de Resultados

### Caso de Prueba: Poste Vertical con Carga Horizontal

**Configuración**:
- Poste vertical de 10m
- Carga horizontal de 1000 daN en tope

**Resultados Esperados**:
- M_base ≈ 10000 daN·m (flexión)
- T_base ≈ 0 daN·m (sin torsión)

**Antes del fix**:
- M_base ≈ 0 daN·m ❌
- T_base ≈ 10000 daN·m ❌

**Después del fix**:
- M_base ≈ 10000 daN·m ✅
- T_base ≈ 0 daN·m ✅

## Convenciones de OpenSeesPy

### Fuerzas en Ejes Locales

`ops.eleForce(elem_id)` retorna 12 valores:

**Nodo i (0-5)**:
- `[0]`: N (axial)
- `[1]`: Qy (cortante Y local)
- `[2]`: Qz (cortante Z local)
- `[3]`: Mx (momento alrededor X local)
- `[4]`: My (momento alrededor Y local)
- `[5]`: Mz (momento alrededor Z local)

**Nodo j (6-11)**: Misma estructura

### geomTransf

Define el vector de referencia para calcular ejes locales:

```python
ops.geomTransf('Linear', 1, 0., 1., 0.)  # vecxz = [0, 1, 0] (Y global)
ops.geomTransf('Linear', 2, 0., 0., 1.)  # vecxz = [0, 0, 1] (Z global)
```

## Archivos Modificados

- `utils/analisis_estatico.py`:
  - Cálculo de ejes locales en preparación de elementos
  - Transformación de resultados a ejes globales
  - Función `generar_diagrama_ejes_locales()`
  - Diagnóstico de ejes en consola

## Referencias

- OpenSeesPy Documentation: Element Forces
- Mechanics of Materials: Coordinate Transformations
- Structural Analysis: Local vs Global Coordinate Systems
