# Aplicación de Cargas en Estructuras Tipo Terminal

## IMPORTANTE: Ángulo Alpha en Terminal

**Las estructuras Terminal SIEMPRE tienen alpha=0°** porque representan el final de una línea de transmisión donde no hay quiebre.

El sistema fuerza automáticamente `alpha=0` para estructuras Terminal, ignorando cualquier valor configurado en el archivo JSON.

## Resumen Ejecutivo

Las estructuras tipo **Terminal** tienen un comportamiento especial en la aplicación de cargas porque representan el final de una línea de transmisión. A diferencia de las estructuras de suspensión o retención, donde los cables continúan en ambos lados, en una terminal los cables solo llegan desde un lado.

## Hipótesis de Carga para Terminal

### Hipótesis Definidas (HipotesisMaestro_Especial.py)

```python
"Terminal": {
    "A0": {"desc": "EDS (TMA)", "patron": "unilateral"},
    "A1": {"desc": "Vmax Transversal", "patron": "unilateral"},
    "A2": {"desc": "Vmed Transversal + hielo", "patron": "unilateral"},
    "B1": {"desc": "Pesos x 2.5 + Tiro unilateral", "patron": "unilateral"},
    "C1": {"desc": "Eliminación de una fase", "patron": "dos-unilaterales"}
}
```

## Patrones de Tiro

### 1. Patrón "unilateral" (A0, A1, A2, B1)

**Concepto**: Todos los cables (conductores y guardias) se cargan con tiro desde un solo lado.

**Implementación** (línea 89-95 de EstructuraAEA_Mecanica.py):
```python
elif patron_tiro == "unilateral":
    factor_peso_nodo = 0.5
    factor_viento_nodo = 0.5
    factor_cond = config_tiro.get("factor_cond", 1.0)
    tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
        tiro_cond_base, self.geometria.alpha_quiebre, factor_cond
    )
```

**Cálculo de componentes** (línea 68-77):
```python
def _calcular_componentes_tiro_unilateral(self, tiro, angulo_grados, factor=1.0):
    ang_rad = math.radians(angulo_grados / 2)
    
    factor_trans = factor * math.sin(ang_rad)
    factor_long = factor * math.cos(ang_rad)
    
    tiro_trans = factor_trans * tiro
    tiro_long = factor_long * tiro
    
    return tiro_trans, tiro_long
```

**Características**:
- **Tiro transversal**: `T × sin(α/2) × factor`
- **Tiro longitudinal**: `T × cos(α/2) × factor`
- **Factor peso**: 0.5 (solo un lado del vano)
- **Factor viento**: 0.5 (solo un lado del vano)

### 2. Patrón "dos-unilaterales" para Terminal (C1)

**Concepto**: Simula la eliminación de una fase. Todos los cables EXCEPTO uno se cargan con tiro unilateral.

**Implementación** (línea 96-104):
```python
elif patron_tiro == "dos-unilaterales":
    if self.geometria.tipo_estructura == "Terminal":
        # Patrón inverso para Terminal
        tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = \
            self._aplicar_patron_dos_unilaterales_terminal(
                nodo_nombre, config_tiro, tiro_cond_base, es_guardia=False
            )
```

**Lógica del patrón inverso** (línea 127-168):

#### Para Conductores:
```python
def _aplicar_patron_dos_unilaterales_terminal(self, nodo, config_tiro, tiro_base, es_guardia=False):
    if not es_guardia:
        # Identificar todos los conductores
        nodos_conductor = [n for n in nodes_dict.keys() 
                          if n.startswith(('C1_', 'C2_', 'C3_'))]
        
        # Elegir el primero como "eliminado"
        conductor_eliminado = nodos_conductor[0]
        
        if nodo == conductor_eliminado:
            # Este conductor NO se carga (eliminado)
            return 0.0, 0.0, 0.0, 0.0
        else:
            # Los demás conductores se cargan con tiro unilateral
            factor_cond = config_tiro.get("factor_cond", 1.0)
            tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                tiro_base, self.geometria.alpha_quiebre, factor_cond
            )
            return tiro_trans, tiro_long, 0.5, 0.5
```

#### Para Guardias:
```python
    if es_guardia:
        nodos_guardia = [n for n in nodes_dict.keys() if n.startswith('HG')]
        
        if len(nodos_guardia) > 1:
            guardia_eliminado = "HG1"
            if nodo == guardia_eliminado:
                # Este guardia NO se carga (eliminado)
                return 0.0, 0.0, 0.0, 0.0
            else:
                # Los demás guardias se cargan con tiro unilateral
                factor_guardia = config_tiro.get("factor_guardia", 1.0)
                tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                    tiro_base, self.geometria.alpha_quiebre, factor_guardia
                )
                return tiro_trans, tiro_long, 0.5, 0.5
```

**Características**:
- **Conductor eliminado**: Primer conductor de la lista (ej: C1_L) → carga = 0
- **Guardia eliminado**: HG1 (si hay múltiples guardias) → carga = 0
- **Demás cables**: Tiro unilateral completo con factor 0.5 para peso y viento

## Diferencia con Otros Tipos de Estructura

### Suspensión/Retención: Patrón "dos-unilaterales" Normal

En estructuras de suspensión o retención, el patrón "dos-unilaterales" funciona al revés:
- **Solo 2 nodos específicos** (C3_L y HG1) se cargan con tiro unilateral
- **Todos los demás** se cargan con tiro bilateral

```python
# Comportamiento original (NO Terminal)
NODOS_DOS_UNILATERAL = ["C3_L", "HG1"]
es_unilateral = (nodo_nombre in NODOS_DOS_UNILATERAL)

if es_unilateral:
    # Solo C3_L y HG1 con tiro unilateral
    tiro_trans, tiro_long = calcular_unilateral(...)
else:
    # Todos los demás con tiro bilateral
    tiro_trans, tiro_long = calcular_bilateral(...)
```

### Terminal: Patrón "dos-unilaterales" Inverso

En Terminal, el patrón se invierte:
- **Solo 1 conductor y 1 guardia** NO se cargan (eliminados)
- **Todos los demás** se cargan con tiro unilateral

## Ejemplo Práctico: Estructura Terminal 220kV Triangular

### Nodos de la estructura:
- Conductores: C1_L, C2_L, C3_L
- Guardias: HG1, HG2

### Hipótesis C1 - Eliminación de una fase

**Aplicación de cargas**:

| Nodo | Tiro Trans | Tiro Long | Factor Peso | Factor Viento | Observación |
|------|-----------|-----------|-------------|---------------|-------------|
| C1_L | 0.0 | 0.0 | 0.0 | 0.0 | **Eliminado** |
| C2_L | T×sin(α/2) | T×cos(α/2) | 0.5 | 0.5 | Unilateral |
| C3_L | T×sin(α/2) | T×cos(α/2) | 0.5 | 0.5 | Unilateral |
| HG1 | 0.0 | 0.0 | 0.0 | 0.0 | **Eliminado** |
| HG2 | T×sin(α/2) | T×cos(α/2) | 0.5 | 0.5 | Unilateral |

**Resultado**: Simula la rotura de una fase (C1_L) y un guardia (HG1), mientras los demás cables mantienen tensión unilateral.

## Rotación de Cargas

Todas las cargas de tiro se rotan según `rotacion_eje_z` del nodo (líneas 134-139):

```python
# ROTAR TIRO si el cable tiene rotacion_eje_z
if nodo_obj and nodo_obj.rotacion_eje_z != 0:
    rz = math.radians(nodo_obj.rotacion_eje_z)
    tiro_x_rot = tiro_trans * math.cos(rz) - tiro_long * math.sin(rz)
    tiro_y_rot = tiro_trans * math.sin(rz) + tiro_long * math.cos(rz)
    tiro_x, tiro_y = tiro_x_rot, tiro_y_rot
```

Esto es especialmente importante en estructuras Terminal donde los cables pueden tener orientaciones específicas.

## Resumen de Factores

### Patrón Unilateral (A0, A1, A2, B1)
- **Tiro**: Componentes transversal y longitudinal según ángulo de quiebre
  - **NOTA**: Para Terminal, alpha=0° (forzado), por lo tanto:
    - Tiro transversal = 0 daN
    - Tiro longitudinal = Tiro completo
- **Peso**: Factor 0.5 (medio vano)
- **Viento**: Factor 0.5 (medio vano)

### Patrón Dos-Unilaterales Terminal (C1)
- **Cable eliminado**: Todas las cargas = 0
- **Demás cables**: Tiro unilateral con factores 0.5

### Comparación con Bilateral
| Aspecto | Bilateral | Unilateral | Dos-Unilaterales Terminal |
|---------|-----------|------------|---------------------------|
| Tiro Trans | 2×T×sin(α/2) | T×sin(α/2) | T×sin(α/2) o 0 |
| Tiro Long | 0 (si reducción=0) | T×cos(α/2) | T×cos(α/2) o 0 |
| Factor Peso | 1.0 | 0.5 | 0.5 o 0 |
| Factor Viento | 1.0 | 0.5 | 0.5 o 0 |

## Referencias en el Código

- **Definición de hipótesis**: `HipotesisMaestro_Especial.py` líneas 213-247
- **Aplicación de cargas**: `EstructuraAEA_Mecanica.py` método `asignar_cargas_hipotesis`
- **Patrón unilateral**: Líneas 89-95
- **Patrón dos-unilaterales Terminal**: Líneas 96-104, 127-168
- **Cálculo componentes**: Líneas 68-77
