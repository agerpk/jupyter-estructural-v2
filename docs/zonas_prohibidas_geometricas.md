# Especificación: Zonas Prohibidas Geométricas

## Estado: ✅ IMPLEMENTADO

## Descripción General

Los algoritmos de zonas prohibidas generan figuras geométricas completas y verifican si un punto (conductor) está dentro de alguna zona prohibida.

**Implementación**: `utils/geometria_zonas.py`

---

## 1. Elementos que Generan Zonas Prohibidas

### 1.1 Conductores (alturas inferiores)

**Geometría**: Círculo
- **Centro**: Posición del cable (Lk por debajo del nodo conductor)
- **Radio**: `D_fases`
- **Ejemplo**: Conductor C1 en h1a genera círculo de radio D_fases alrededor de (x_C1, 0, h1a - Lk)

```
     ●  Nodo conductor (amarre)
     |
     | Lk (cadena)
     |
     ● ← Cable real (centro del círculo)
   ╱   ╲
  ╱  D  ╲  ← Zona prohibida circular
 ╱  fases ╲
●─────────●
```

### 1.2 Columna (x=0, vertical)

**Geometría**: Franja vertical
- **Ancho**: `2 * s_decmax` (centrada en x=0)
- **Límites**: `x ∈ [-s_decmax, +s_decmax]`
- **Altura**: Desde z=0 hasta altura máxima de estructura
- **Ejemplo**: Franja prohibida de ancho 2*s_decmax en toda la altura

```
    s_decmax  s_decmax
    ←─────→ ←─────→
    
    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ← Zona prohibida (franja vertical)
    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
    ▓▓▓▓▓│││││▓▓▓▓▓  ← Columna en x=0
    ▓▓▓▓▓│││││▓▓▓▓▓
    ▓▓▓▓▓│││││▓▓▓▓▓
    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

### 1.3 Ménsula Horizontal (alturas inferiores)

**Geometría**: Rectángulo + Semicírculo
- **Rectángulo**: Desde nodo CROSS hasta nodo conductor
  - Vértices: 
    - `(x_CROSS, z_CROSS)`
    - `(x_CONDUCTOR, z_CROSS)`
    - `(x_CONDUCTOR, z_CROSS + s_reposo)`
    - `(x_CROSS, z_CROSS + s_reposo)`
- **Semicírculo**: En extremo del conductor
  - Centro: `(x_CONDUCTOR, z_CROSS)`
  - Radio: `s_reposo`
  - Orientación: Hacia afuera de la ménsula

```
Ejemplo: Ménsula h1a desde CROSS_H1 (x=0) hasta C1 (x=Lmen1)

    ╭─────╮  ← Semicírculo (radio s_reposo)
    │     │
────┴─────┴──── ← Rectángulo (altura s_reposo)
CROSS_H1  C1
(x=0)     (x=Lmen1)
```

**Vértices del rectángulo**:
1. `(0, 0, h1a)` - CROSS_H1
2. `(Lmen1, 0, h1a)` - C1
3. `(Lmen1, 0, h1a + s_reposo)` - Arriba de C1
4. `(0, 0, h1a + s_reposo)` - Arriba de CROSS_H1

**Semicírculo**:
- Centro: `(Lmen1, 0, h1a)`
- Radio: `s_reposo`
- Ángulos: 0° a 180° (hacia +x)

---

## 2. Algoritmo de Verificación

### 2.1 Generar Zonas Prohibidas

```python
def generar_zonas_prohibidas(alturas_inferiores):
    zonas = []
    
    # 1. Conductores → Círculos
    for conductor in conductores_alturas_inferiores:
        x, y, z_amarre = conductor.coordenadas
        z_cable = z_amarre - Lk
        zonas.append(Circulo(centro=(x, z_cable), radio=D_fases))
    
    # 2. Columna → Franja vertical
    zonas.append(FranjaVertical(x_min=-s_decmax, x_max=+s_decmax, z_min=0, z_max=h_max))
    
    # 3. Ménsulas → Rectángulo + Semicírculo
    for mensula in mensulas_alturas_inferiores:
        x_inicio, z = mensula.nodo_inicio.coordenadas
        x_fin, _ = mensula.nodo_fin.coordenadas
        
        # Rectángulo
        vertices = [
            (x_inicio, z),
            (x_fin, z),
            (x_fin, z + s_reposo),
            (x_inicio, z + s_reposo)
        ]
        zonas.append(Rectangulo(vertices))
        
        # Semicírculo en extremo
        zonas.append(Semicirculo(centro=(x_fin, z), radio=s_reposo, orientacion='+x'))
    
    return zonas
```

### 2.2 Verificar Punto

```python
def punto_en_zona_prohibida(x, z, zonas):
    for zona in zonas:
        if zona.contiene_punto(x, z):
            return True, zona.descripcion
    return False, None
```

### 2.3 Buscar Altura Óptima

```python
def buscar_altura_optima(x_linea, alturas_inferiores):
    zonas = generar_zonas_prohibidas(alturas_inferiores)
    
    # Buscar altura mínima donde el punto NO está en ninguna zona
    z_min = 0
    for zona in zonas:
        z_necesaria = zona.calcular_altura_minima_para_x(x_linea)
        z_min = max(z_min, z_necesaria)
    
    return z_min + Lk  # Sumar Lk porque retornamos altura de amarre
```

---

## 3. Clases Geométricas Necesarias

### 3.1 Clase Circulo

```python
class Circulo:
    def __init__(self, centro, radio):
        self.centro = centro  # (x, z)
        self.radio = radio
    
    def contiene_punto(self, x, z):
        dist = math.sqrt((x - self.centro[0])**2 + (z - self.centro[1])**2)
        return dist < self.radio
    
    def calcular_altura_minima_para_x(self, x):
        dx = abs(x - self.centro[0])
        if dx >= self.radio:
            return 0  # Fuera del círculo horizontalmente
        dz = math.sqrt(self.radio**2 - dx**2)
        return self.centro[1] + dz
```

### 3.2 Clase FranjaVertical

```python
class FranjaVertical:
    def __init__(self, x_min, x_max, z_min, z_max):
        self.x_min = x_min
        self.x_max = x_max
        self.z_min = z_min
        self.z_max = z_max
    
    def contiene_punto(self, x, z):
        return (self.x_min <= x <= self.x_max and 
                self.z_min <= z <= self.z_max)
    
    def calcular_altura_minima_para_x(self, x):
        if self.x_min <= x <= self.x_max:
            return self.z_max
        return 0
```

### 3.3 Clase Rectangulo

```python
class Rectangulo:
    def __init__(self, vertices):
        self.vertices = vertices  # [(x1,z1), (x2,z2), (x3,z3), (x4,z4)]
    
    def contiene_punto(self, x, z):
        # Algoritmo punto-en-polígono (ray casting)
        pass
    
    def calcular_altura_minima_para_x(self, x):
        # Encontrar z máximo del rectángulo en línea x
        pass
```

### 3.4 Clase Semicirculo

```python
class Semicirculo:
    def __init__(self, centro, radio, orientacion):
        self.centro = centro
        self.radio = radio
        self.orientacion = orientacion  # '+x' o '-x'
    
    def contiene_punto(self, x, z):
        # Verificar si está en semicírculo
        pass
    
    def calcular_altura_minima_para_x(self, x):
        # Similar a Circulo pero solo para un lado
        pass
```

---

## 4. Implementación Actual

**Estado**: ✅ IMPLEMENTADO en `utils/geometria_zonas.py`

**Clases Implementadas**:
- `ZonaProhibida` - Clase base abstracta
- `Circulo` - Zonas circulares (conductores)
- `FranjaVertical` - Franja vertical (columna)
- `Rectangulo` - Rectángulo (ménsula)
- `Semicirculo` - Semicírculo (extremo de ménsula)
- `GeneradorZonasProhibidas` - Generador de zonas a partir de elementos estructurales
- `VerificadorZonasProhibidas` - Verificador de infracciones

**Uso en Etapa2**:
```python
from utils.geometria_zonas import buscar_altura_fuera_zonas_prohibidas

# Buscar altura óptima considerando todas las zonas prohibidas
z_amarre = buscar_altura_fuera_zonas_prohibidas(
    self.geo, x_linea, h1a, D_fases, s_reposo, s_decmax, Lk
)
```

**Características**:
- Geometría completa: círculos, franjas, rectángulos, semicírculos
- Verificación punto-en-zona precisa
- Cálculo de altura mínima por zona
- Generación automática de zonas desde elementos estructurales

---

## 5. Testing y Validación

### Casos de Prueba

1. **Conductor sobre ménsula**: Verificar rectángulo + semicírculo
2. **Conductor cerca de columna**: Verificar franja vertical
3. **Conductores cercanos**: Verificar círculos D_fases
4. **Nodos CROSS**: Verificar círculos s_reposo
5. **Zonas solapadas**: Verificar que se toma la restricción más alta

### Verificación Visual

En gráficos interactivos (Etapa 6):
- Dibujar zonas prohibidas como áreas sombreadas
- Usar colores diferentes por tipo de zona
- Mostrar conductor y verificar visualmente si está en zona prohibida
- Botones para activar/desactivar cada tipo de zona

---

## 6. Próximos Pasos

### Etapa 3 (h3a)
- Aplicar mismo algoritmo geométrico para h3a
- Considerar zonas de h1a y h2a

### Etapa 4 (Cable Guardia)
- Extender para verificar zonas Dhg
- Considerar apantallamiento

### Etapa 6 (Gráficos Interactivos)
- Visualizar zonas prohibidas en gráfico 2D
- Clipping de zonas solapadas (shapely)
- Controles interactivos por nodo

---

## 7. Archivos Relacionados

- `utils/geometria_zonas.py` - Implementación de zonas geométricas ✅
- `EstructuraAEA_Geometria_Etapa2.py` - Uso en cálculo h2a ✅
- `EstructuraAEA_Geometria_Etapa3.py` - Uso en cálculo h3a (pendiente)
- `GraficoCabezal2D.py` - Visualización de zonas (pendiente)
