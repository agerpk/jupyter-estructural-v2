# Diseño de Cabezales por Configuración

## Resumen Ejecutivo

El diseño de cabezales en `EstructuraAEA_Geometria` se realiza mediante el método `_crear_nodos_estructurales_nuevo()` que delega a métodos específicos según la combinación de:
- **TERNA**: Simple, Doble
- **DISPOSICION**: horizontal, vertical, triangular
- **CANT_HG**: 0, 1, 2

## Flujo de Creación de Nodos

### 1. Nodos Base y Estructurales (Comunes a Todas las Configuraciones)

```python
# Siempre se crea:
BASE (0, 0, 0) - tipo: "base"

# Nodos de cruce (poste-ménsula) - según necesidad:
CROSS_H1 (0, 0, h1a) - tipo: "cruce" - NO se crea si horizontal simple
CROSS_H2 (0, 0, h2a) - tipo: "cruce" - Solo si h2a > h1a
CROSS_H3 (0, 0, h3a) - tipo: "cruce" - Solo si h3a > h2a (vertical)

# Nodos auxiliares:
V (0, 0, 2/3*altura_total) - tipo: "viento"
MEDIO (0, 0, (h1a + altura_total)/2) - tipo: "general"
```

## 2. Configuraciones de Conductores

### 2.1 Terna Simple - Disposición Vertical

**Método**: `_crear_nodos_simple_vertical(h1a, h2a, h3a)`

**Nodos Conductor**:
```python
C1_L (lmen, 0, h1a) - conductor inferior
C2_L (lmen, 0, h2a) - conductor medio
C3_L (lmen, 0, h3a) - conductor superior
```

**Características**:
- 3 conductores en línea vertical
- Todos en mismo lado (x = lmen)
- Alturas: h1a < h2a < h3a
- Conexiones: BASE → CROSS_H1 → C1_L, CROSS_H2 → C2_L, CROSS_H3 → C3_L

**Defasaje por Hielo**:
- Puede aplicarse a "primera", "segunda" o "tercera" altura
- Modifica coordenada X de nodos en altura seleccionada

---

### 2.2 Terna Simple - Disposición Triangular

**Método**: `_crear_nodos_simple_triangular(h1a, h2a)`

**Nodos Conductor**:
```python
C1_R (+lmen, 0, h1a) - conductor inferior derecho
C1_L (-lmen, 0, h1a) - conductor inferior izquierdo
C2_R (+lmen, 0, h2a) - conductor superior (vértice)
```

**Características**:
- 3 conductores formando triángulo
- 2 en h1a (base), 1 en h2a (vértice)
- Simetría en X
- h2a > h1a

**Defasaje por Hielo**:
- Puede aplicarse a "primera" o "segunda" altura
- Afecta a C1_R, C1_L si es "primera"
- Afecta a C2_R si es "segunda"

---

### 2.3 Terna Simple - Disposición Horizontal

**Método**: `_crear_nodos_horizontal_default(h1a, s_estructura, D_fases, theta_max)`

**Nodos Estructurales**:
```python
Y1 (0, 0, h1a - 2*Lk) - nodo inferior central
Y2 (+dist_columna_x, 0, h1a - Lk) - columna derecha
Y3 (-dist_columna_x, 0, h1a - Lk) - columna izquierda
Y4 (+dist_columna_x, 0, h1a) - cruceta derecha
Y5 (-dist_columna_x, 0, h1a) - cruceta izquierda
```

**Nodos Conductor**:
```python
C1 (+dist_conductor_final, 0, h1a) - conductor derecho
C2 (0, 0, h1a) - conductor central
C3 (-dist_conductor_final, 0, h1a) - conductor izquierdo
```

**Cálculos**:
```python
dist_columna_x = max(Lk*sin(theta_max) + s_estructura, D_fases/2)
dist_conductor_x = dist_columna_x + Lk*sin(theta_max) + s_estructura + ancho_cruceta/2
dist_conductor_final = max(D_fases, dist_conductor_x)
```

**Características**:
- 3 conductores en línea horizontal (misma altura h1a)
- Estructura en "Y" con brazos laterales
- NO se crea CROSS_H1 (reemplazado por Y1-Y4-Y5)
- Conexiones: BASE → Y1 → Y2 → Y4, Y1 → Y3 → Y5

**Defasaje por Hielo**:
- NO aplica (solo una altura de conductores)

---

### 2.4 Terna Doble - Disposición Vertical

**Método**: `_crear_nodos_doble_vertical(h1a, h2a, h3a)`

**Nodos Conductor**:
```python
# Lado derecho (x+)
C1_R (+lmen, 0, h1a) - inferior derecho
C2_R (+lmen, 0, h2a) - medio derecho
C3_R (+lmen, 0, h3a) - superior derecho

# Lado izquierdo (x-)
C1_L (-lmen, 0, h1a) - inferior izquierdo
C2_L (-lmen, 0, h2a) - medio izquierdo
C3_L (-lmen, 0, h3a) - superior izquierdo
```

**Características**:
- 6 conductores (2 ternas verticales)
- Simetría perfecta en X
- Alturas: h1a < h2a < h3a
- Conexiones: CROSS_H1 → C1_R/C1_L, CROSS_H2 → C2_R/C2_L, CROSS_H3 → C3_R/C3_L

**Defasaje por Hielo**:
- Puede aplicarse a "primera", "segunda" o "tercera" altura
- Afecta a ambos lados simultáneamente

---

### 2.5 Terna Doble - Disposición Triangular

**Método**: `_crear_nodos_doble_triangular(h1a, h2a)`

**Nodos Conductor**:
```python
# Nivel inferior (h1a) - 4 conductores
C1_R (+lmen, 0, h1a) - base derecha interior
C2_R (+lmen2c, 0, h1a) - base derecha exterior
C1_L (-lmen, 0, h1a) - base izquierda interior
C2_L (-lmen2c, 0, h1a) - base izquierda exterior

# Nivel superior (h2a) - 2 conductores
C3_R (+lmen, 0, h2a) - vértice derecho
C3_L (-lmen, 0, h2a) - vértice izquierdo
```

**Características**:
- 6 conductores (2 triángulos)
- 4 en h1a (bases), 2 en h2a (vértices)
- lmen2c = lmen + D_fases (separación entre conductores de base)
- Simetría en X

**Defasaje por Hielo**:
- Puede aplicarse a "primera" o "segunda" altura
- "primera": afecta a C1_R, C2_R, C1_L, C2_L
- "segunda": afecta a C3_R, C3_L

---

### 2.6 Terna Doble - Disposición Horizontal

**Estado**: ❌ NO IMPLEMENTADO

**Mensaje**: "ERROR: Caso no programado"

---

## 3. Configuraciones de Cable Guardia

### 3.1 CANT_HG = 0 (Sin Cable Guardia)

```python
# No se crean nodos guardia
hhg = 0.0
lmenhg = 0.0
```

---

### 3.2 CANT_HG = 1, HG_CENTRADO = True

**Método**: `_crear_nodos_guardia_nuevo()`

**Nodos Guardia**:
```python
HG1 (0, 0, hhg) - guardia centrado
```

**Cálculo de Altura**:
```python
hhg = pcma_x / tan(ang_apantallamiento) + pcma_y
```

**Características**:
- Cable guardia en eje central (x=0)
- NO se crea nodo TOP
- Altura calculada para cubrir conductor más alejado
- Conexión: CROSS_H3 → HG1 (si vertical doble) o BASE → ... → HG1

---

### 3.3 CANT_HG = 1, HG_CENTRADO = False

**Método**: `_crear_nodos_guardia_nuevo()`

**Nodos Guardia**:
```python
TOP (0, 0, hhg) - nodo estructural superior
HG1 (lmenhg, 0, hhg) - guardia en ménsula
```

**Cálculo de Posición**:
```python
dvhg = Dhg * cos(ang_apantallamiento) + HADD_hg
hhg = pcma_y + dvhg
lmenhg_base = pcma_x - (dvhg/cos(ang_apantallamiento)) * sin(ang_apantallamiento)
lmenhg = max(lmenhg_base, long_mensula_min_guardia)
```

**Ajuste Iterativo** (si `autoajustar_lmenhg=True`):
1. Verificar que todos los conductores estén cubiertos (diff >= 0)
2. Si conductor más alto tiene diff > dist_reposicionar_hg, reducir lmenhg
3. Asegurar que al reducir no se descubran otros conductores

**Características**:
- Cable guardia en ménsula lateral
- Se crea nodo TOP en eje central
- Conexión: TOP → HG1

**Aplicable a**:
- Terna simple triangular
- Terna simple horizontal (con ajuste especial)

---

### 3.4 CANT_HG = 2

**Método**: `_crear_nodos_guardia_nuevo()`

**Nodos Guardia**:
```python
TOP (0, 0, hhg) - nodo estructural superior
HG1 (+lmenhg, 0, hhg) - guardia derecho
HG2 (-lmenhg, 0, hhg) - guardia izquierdo
```

**Cálculo de Posición**:
```python
dvhg = Dhg * cos(ang_apantallamiento) + HADD_hg
hhg = pcma_y + dvhg
lmenhg_base = pcma_x - Dhg * sin(ang_apantallamiento)
lmenhg = max(lmenhg_base, long_mensula_min_guardia)
```

**Ajuste Iterativo** (si `autoajustar_lmenhg=True`):
- Similar a CANT_HG=1 no centrado
- Verifica cobertura de conductores del lado derecho (x > 0)
- Simetría automática para HG2

**Características**:
- Dos cables guardia simétricos
- Se crea nodo TOP en eje central
- Conexiones: TOP → HG1, TOP → HG2

**Aplicable a**:
- Terna doble vertical
- Terna doble triangular
- Terna simple vertical (opcional)

---

## 4. Defasaje por Hielo

### Parámetros

```python
defasaje_mensula_hielo: bool  # Activar/desactivar
lmen_extra_hielo: float       # Valor a sumar (puede ser negativo)
mensula_defasar: str          # "primera", "segunda", "tercera", "primera y tercera"
```

### Lógica de Aplicación

**Método**: `_aplicar_defasaje_hielo()`

1. **Recolectar nodos conductor por altura**
2. **Ordenar alturas ascendentemente**
3. **Mapear nombres a índices**:
   - 0: "primera" (altura más baja)
   - 1: "segunda" (altura media)
   - 2: "tercera" (altura más alta)
4. **Aplicar defasaje**:
   - Solo a nodos con x ≠ 0
   - Mantener signo: x_nuevo = x + signo(x) * lmen_extra_hielo

### Casos Especiales

**"primera y tercera"**:
- Aplica defasaje a primera altura
- Luego aplica defasaje a tercera altura
- Segunda altura NO se modifica

**Horizontal**:
- NO aplica (solo una altura de conductores)

---

## 5. Conexiones Estructurales

### Tipos de Tramo

```python
'columna'  # Conexiones verticales en x=0
'mensula'  # Conexiones horizontales desde CROSS a conductores
'cruceta'  # Conexiones horizontales entre conductores
'cadena'   # Conexiones editadas por usuario
```

### Generación Automática

**Método**: `_generar_conexiones()`

1. **Columnas**: Conectar nodos centrales (x=0, y=0) ordenados por z
2. **Ménsulas**: Conectar CROSS → Conductores (mismo z)
3. **Ménsulas Guardia**: Conectar TOP → HG (si no centrado)
4. **Crucetas**: Conectar conductores en misma altura con x opuestos
5. **Cadenas**: Usar `nodo.conectado_a` para conexiones manuales

---

## 6. Matriz de Configuraciones Soportadas

| TERNA | DISPOSICION | CANT_HG | ESTADO | MÉTODO |
|-------|-------------|---------|--------|--------|
| Simple | Vertical | 0 | ✅ | `_crear_nodos_simple_vertical` |
| Simple | Vertical | 1 (centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Simple | Vertical | 1 (no centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Simple | Vertical | 2 | ✅ | + `_crear_nodos_guardia_nuevo` |
| Simple | Triangular | 0 | ✅ | `_crear_nodos_simple_triangular` |
| Simple | Triangular | 1 (centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Simple | Triangular | 1 (no centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Simple | Triangular | 2 | ✅ | + `_crear_nodos_guardia_nuevo` |
| Simple | Horizontal | 0 | ✅ | `_crear_nodos_horizontal_default` |
| Simple | Horizontal | 1 (centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Simple | Horizontal | 1 (no centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Simple | Horizontal | 2 | ✅ | + `_crear_nodos_guardia_nuevo` |
| Doble | Vertical | 0 | ✅ | `_crear_nodos_doble_vertical` |
| Doble | Vertical | 1 (centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Doble | Vertical | 1 (no centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Doble | Vertical | 2 | ✅ | + `_crear_nodos_guardia_nuevo` |
| Doble | Triangular | 0 | ✅ | `_crear_nodos_doble_triangular` |
| Doble | Triangular | 1 (centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Doble | Triangular | 1 (no centrado) | ✅ | + `_crear_nodos_guardia_nuevo` |
| Doble | Triangular | 2 | ✅ | + `_crear_nodos_guardia_nuevo` |
| Doble | Horizontal | * | ❌ | ERROR: Caso no programado |

---

## 7. Parámetros Clave

### Alturas

```python
h1a: float  # Altura primer amarre (siempre existe)
h2a: float  # Altura segundo amarre (triangular, vertical)
h3a: float  # Altura tercer amarre (solo vertical)
hhg: float  # Altura cable guardia
```

### Longitudes de Ménsula

```python
lmen: float     # Longitud ménsula conductor
lmen2c: float   # Longitud ménsula conductor 2 (doble triangular)
lmenhg: float   # Longitud ménsula guardia (0 si centrado)
```

### Distancias Mínimas

```python
D_fases: float       # Distancia mínima entre fases
s_estructura: float  # Distancia mínima fase-estructura
Dhg: float           # Distancia mínima guardia-conductor
```

### Ángulos

```python
theta_max: float           # Ángulo declinación máxima (suspensión)
ang_apantallamiento: float # Ángulo apantallamiento guardia (default 30°)
```

---

## 8. Orden de Ejecución

```python
def dimensionar_unifilar():
    1. calcular_theta_max()
    2. calcular_distancias_minimas()
    3. _calcular_alturas_fases()
    4. _calcular_longitud_mensula()
    5. _calcular_posicion_conductor_mas_alto()
    6. _calcular_cable_guardia()
       - _ajustar_lmenhg_iterativo() si autoajustar_lmenhg=True
    7. _crear_nodos_estructurales_nuevo()
       - _crear_nodos_[configuracion]()
       - _crear_nodos_guardia_nuevo()
    8. _aplicar_defasaje_hielo()
    9. _actualizar_nodes_key()
```

---

## 9. Casos Especiales

### Horizontal Simple

- NO se crea CROSS_H1
- Se crean nodos Y1-Y5 para estructura en "Y"
- Todos los conductores en misma altura
- Cálculo especial de dist_conductor_final

### Guardia Centrado en Doble Vertical

- HG1 conecta directamente a CROSS_H3
- NO se crea nodo TOP
- Conexión: BASE → CROSS_H1 → CROSS_H2 → CROSS_H3 → HG1

### Ajuste Iterativo de lmenhg

- Solo aplica si `autoajustar_lmenhg=True`
- Verifica cobertura de conductores del lado derecho (x > 0)
- Prioridad: cubrir todos > optimizar distancia al más alto
- Respeta `long_mensula_min_guardia`

---

## 10. Validaciones

### Durante Creación

- Verificar que h2a > h1a (si aplica)
- Verificar que h3a > h2a (si aplica)
- Verificar distancia diagonal conductor-guardia >= Dhg
- Verificar ángulo apantallamiento <= 30° (recomendado)

### Post-Creación

- Verificar que todos los conductores estén cubiertos por guardia
- Verificar que no haya nodos duplicados
- Verificar que conexiones sean válidas

---

## 11. Exportación de Nodos

### Formato Estándar

```python
{
    "nombre": str,
    "tipo": str,  # conductor, guardia, base, cruce, general, viento
    "coordenadas": [x, y, z],
    "cable_id": str,
    "rotacion_eje_x": float,
    "rotacion_eje_y": float,
    "rotacion_eje_z": float,
    "angulo_quiebre": float,
    "tipo_fijacion": str,  # suspensión, retención
    "conectado_a": [str],
    "es_editado": bool
}
```

### Métodos

```python
exportar_nodos_editados()  # Solo nodos con es_editado=True
importar_nodos_editados()  # Carga desde lista de dicts
obtener_nodos_dict()       # {nombre: [x,y,z]}
```

---

## 12. Debugging

### Mensajes de Consola

```python
print(f"📐 Configuración {disposicion}")
print(f"   🔍 DEBUG: disposicion='{disposicion}', terna='{terna}'")
print(f"   📍 Horizontal: C1=(...), C2=(...), C3=(...)")
print(f"   🛡️  Cable guardia centrado: HG1 en (0, {hhg:.2f})")
print(f"   ✅ Nodos creados: {len(nodos)} nodos totales")
```

### Verificación Visual

```python
listar_nodos()  # Lista todos los nodos con coordenadas
info_estructura()  # Información completa de la estructura
```

---

## 13. Generación de Gráficos

### Clase Responsable

**Archivo**: `EstructuraAEA_Graficos.py`  
**Clase**: `EstructuraAEA_Graficos`

### Métodos de Visualización

#### 13.1 `graficar_estructura()`

Genera gráfico 2D completo de la estructura en plano XZ (vista lateral).

**Proceso de Dibujo**:

1. **Línea de Terreno**: `plt.axhline(y=0)` - nivel del suelo

2. **Recolección de Nodos**:
   - Nodos estructura: x=0, no son conductores ni guardias
   - Nodos conductor: agrupados por altura
   - Nodos guardia: HG1, HG2

3. **Dibujo de Columnas**:
   
   **Configuración Estándar** (vertical, triangular):
   ```python
   # Conectar nodos centrales ordenados por altura
   for i in range(len(nodos_estructura)-1):
       plt.plot([0, 0], [z1, z2], color='poste', linewidth=4)
   ```
   
   **Configuración Horizontal**:
   ```python
   # BASE → Y1
   plt.plot([base_x, y1_x], [base_z, y1_z])
   # Y1 → Y2 → Y4 (derecha)
   plt.plot([y1_x, y2_x], [y1_z, y2_z])
   plt.plot([y2_x, y4_x], [y2_z, y4_z])
   # Y1 → Y3 → Y5 (izquierda)
   plt.plot([y1_x, y3_x], [y1_z, y3_z])
   plt.plot([y3_x, y5_x], [y3_z, y5_z])
   # HG1 → Y4, HG2 → Y5
   ```

4. **Dibujo de Ménsulas/Crucetas de Conductores**:
   
   **Detección de Tipo**:
   ```python
   hay_izq = any(x < -0.01 for x in conductores_x)
   hay_der = any(x > 0.01 for x in conductores_x)
   
   if hay_izq and hay_der:
       # CRUCETA: línea horizontal completa
       plt.plot([x_min, x_max], [altura, altura])
   else:
       # MENSULA: cada conductor individualmente
       for x_cond in conductores:
           plt.plot([x_cross, x_cond], [z_cross, altura])
   ```

5. **Dibujo de Ménsulas/Crucetas de Guardias**:
   - Similar a conductores
   - Solo si existe nodo TOP
   - Conexiones TOP → HG1, TOP → HG2

6. **Dibujo de Nodos**:
   - Conductores: círculo azul, tamaño 120
   - Guardias: círculo verde, tamaño 120
   - Base: cuadrado negro, tamaño 150
   - TOP: triángulo negro, tamaño 120
   - CROSS: círculo negro, tamaño 80
   - Flechas rojas para rotaciones

7. **Conexiones Editadas**:
   ```python
   for nodo in nodos:
       if nodo.es_editado and nodo.conectado_a:
           plt.plot([x1, x2], [z1, z2], 
                   color='orange', linestyle=':', linewidth=2)
   ```

8. **Anotaciones de Distancias**:
   - Distancias verticales entre nodos centrales
   - Líneas punteadas grises con texto

**Casos Especiales**:
- **Guardia centrado en doble vertical**: Conecta CROSS_H3 → HG1 directamente
- **Horizontal**: No crea CROSS_H1, usa estructura Y

---

#### 13.2 `graficar_cabezal()`

Genera gráfico 2D detallado del cabezal con cadenas, círculos de distancias y apantallamiento.

**Proceso de Dibujo**:

1. **Estructura Base**: Similar a `graficar_estructura()`

2. **Zona de Apantallamiento**:
   ```python
   if nodos_guardia:
       h_guardia = hhg
       h_terminacion = h1a - Lk
       angulo_apant = ang_apantallamiento
       
       # Un guardia
       x_ext_izq = x_hg - (h_guardia - h_terminacion) * tan(angulo_apant)
       x_ext_der = x_hg + (h_guardia - h_terminacion) * tan(angulo_apant)
       plt.plot([x_hg, x_ext_izq], [h_guardia, h_terminacion], '--')
       plt.plot([x_hg, x_ext_der], [h_guardia, h_terminacion], '--')
       plt.fill([x_ext_izq, x_hg, x_ext_der], [h_terminacion, h_guardia, h_terminacion])
   ```

3. **Cadenas con Declinación**:
   
   **Modos de Dibujo**:
   - `declinar_todos=False`: Solo declina conductor crítico
   - `declinar_todos=True`: Dibuja 3 posiciones (izq, centro, der)
   
   **Lógica de Declinación**:
   ```python
   # Horizontal simple
   if es_horizontal_simple:
       angulo_cadena = theta_max if ("C3" in nombre or "C2" in nombre) else 0.0
   # Otras configuraciones
   else:
       angulo_cadena = theta_max if (nombre.endswith('_L') and "C1" in nombre) else 0.0
   ```
   
   **Cálculo de Posición**:
   ```python
   ang_rad = radians(angulo)
   x_conductor = x_amarre + direccion * Lk * sin(ang_rad)
   z_conductor = z_amarre - Lk * cos(ang_rad)
   ```

4. **Círculos de Distancias**:
   
   **Tipos de Círculos** (controlados por flags):
   - `dibujar_circulos_d_fases`: Círculo D_fases (gris, punteado)
   - `dibujar_circulos_s_estructura`: Círculo s_estructura (gris, punteado)
   - `dibujar_areas_s_estructura`: Área s_estructura (azul claro, relleno)
   - `dibujar_circulos_dhg`: Círculo Dhg solo en conductor más alto (gris, punteado)
   
   **Aplicación**:
   ```python
   # D_fases en TODOS los conductores
   plt.Circle((x_conductor, z_conductor), D_fases, fill=False, linestyle='--')
   
   # s_estructura en TODOS los conductores
   plt.Circle((x_conductor, z_conductor), s_estructura, fill=True, alpha=0.15)
   plt.Circle((x_conductor, z_conductor), s_estructura, fill=False, linestyle='--')
   
   # Dhg solo en conductor de altura máxima
   if abs(z_amarre - z_max_conductor) < 0.01:
       plt.Circle((x_conductor, z_conductor), Dhg, fill=False, linestyle='--')
   ```

5. **Etiquetas de Distancias**:
   - Solo en conductores específicos (C1_L, C2_R, C3_L)
   - Posición según configuración (horizontal vs otras)
   - Formato: nombre + valor en metros

---

#### 13.3 `graficar_nodos_coordenadas()`

Genera gráfico 3D interactivo usando Plotly.

**Proceso de Dibujo**:

1. **Recolección de Nodos por Tipo**

2. **Conexiones Editadas** (primero, debajo de nodos):
   ```python
   fig.add_trace(go.Scatter3d(
       x=[x1, x2], y=[y1, y2], z=[z1, z2],
       mode='lines',
       line=dict(color='orange', width=4, dash='dot')
   ))
   ```

3. **Nodos por Tipo**:
   ```python
   fig.add_trace(go.Scatter3d(
       x=x_vals, y=y_vals, z=z_vals,
       mode='markers+text',
       marker=dict(size=8, color='#1f77b4'),
       text=nombres,
       textposition='top center',
       name='Conductores'
   ))
   ```

4. **Plano de Terreno** (Z=0)

5. **Vista Isométrica**:
   ```python
   camera=dict(
       eye=dict(x=1.5, y=-1.5, z=1.2),
       center=dict(x=0, y=0, z=0),
       up=dict(x=0, y=0, z=1)
   )
   ```

6. **Ejes con Grilla**: dtick=1 (cada 1 metro)

**Interactividad**:
- Hover muestra: nombre, coordenadas (x, y, z)
- Zoom, pan, rotación con mouse
- Leyenda clickeable

---

### 13.4 Configuración de Colores

```python
COLORES = {
    'conductor': '#1f77b4',      # Azul
    'guardia': '#2ca02c',        # Verde
    'poste': '#000000',          # Negro
    'cadena': '#717170',         # Gris
    'conductor_end': 'red',      # Rojo
    'circulo': 'gray',           # Gris
    'apantallamiento': '#84FF6B', # Verde claro
    'dhg_circulo': 'gray',       # Gris
    'terreno': '#8B4513',        # Marrón
    'area_s_estructura': 'lightblue'  # Azul claro
}
```

---

### 13.5 Controles Gráficos

```python
OTROS_CONTROLES_GRAFICOS = {
    'declinar_todos': False,
    'dibujar_solo_circulos_declinados_trayectoria': True,
    'dibujar_circulos_s_estructura': True,
    'dibujar_areas_s_estructura': True,
    'dibujar_circulos_d_fases': True,
    'dibujar_circulos_dhg': True,
    'linewidth_cadena': 2,
    'linewidth_estructura': 4,
    'linewidth_cruceta': 3,
    'alpha_circulo': 0.7,
    'alpha_area_s_estructura': 0.15,
    'zoom_cabezal_default': 0.7,
    'zoom_estructura_default': 0.95
}
```

---

### 13.6 Lógica de Detección

**Horizontal Simple**:
```python
tiene_y = any('Y' in nombre for nombre in geometria.nodes_key.keys())
es_horizontal_simple = tiene_y and geometria.terna == "Simple"
```

**Guardia Centrado en Doble Vertical**:
```python
if (geometria.disposicion == 'vertical' and 
    geometria.terna == 'Doble' and 
    geometria.cant_hg == 1 and 
    geometria.hg_centrado):
    # Conectar CROSS_H3 → HG1 directamente
```

**Conductor Más Alto**:
```python
z_max_conductor = max(conductores_por_altura.keys())
# Dhg solo en conductores con z_amarre ≈ z_max_conductor
```

---

### 13.7 Orden de Dibujo (Z-Order)

**Capas de Abajo hacia Arriba**:
1. Áreas s_estructura (zorder=2, alpha=0.15)
2. Círculos s_estructura (zorder=3)
3. Conexiones editadas (zorder=3)
4. Estructura (columnas, ménsulas)
5. Cadenas
6. Nodos (zorder=5)
7. Flechas de rotación (zorder=6)

---

## 14. Referencias

- **Archivo Geometría**: `EstructuraAEA_Geometria.py`
- **Clase Geometría**: `EstructuraAEA_Geometria`
- **Archivo Gráficos**: `EstructuraAEA_Graficos.py`
- **Clase Gráficos**: `EstructuraAEA_Graficos`
- **Métodos principales**:
  - Geometría:
    - `dimensionar_unifilar()`
    - `_crear_nodos_estructurales_nuevo()`
    - `_crear_nodos_[configuracion]()`
    - `_crear_nodos_guardia_nuevo()`
    - `_aplicar_defasaje_hielo()`
    - `_ajustar_lmenhg_iterativo()`
  - Gráficos:
    - `graficar_estructura()`
    - `graficar_cabezal()`
    - `graficar_nodos_coordenadas()`
    - `diagrama_polar_tiros()`
    - `diagrama_barras_tiros()`

---

## 15. Notas Importantes

1. **Orden de rotaciones**: X → Y → Z (importante para cálculos mecánicos)
2. **Sistema de coordenadas**: X=transversal, Y=longitudinal, Z=vertical
3. **Signo de X**: Positivo=derecha, Negativo=izquierda (vista desde vano)
4. **Altura de nodos conductor**: Incluye Lk (altura de amarre, no de conductor)
5. **Posición real del conductor**: z_conductor = z_nodo - Lk
6. **Defasaje por hielo**: Solo afecta coordenada X, no Y ni Z
7. **Ajuste iterativo**: Puede modificar lmenhg después del cálculo inicial
8. **Guardia centrado**: NO crea nodo TOP, conecta directamente a columna
