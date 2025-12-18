# EJEMPLO DE USO: NodoEstructural con Cargas

## Estructura de Cargas

### Concepto
- Un **Nodo** tiene una **lista de Cargas**
- Cada **Carga** tiene:
  - `nombre`: Identificador (ej: "Peso", "Viento", "Tiro")
  - `hipotesis`: Lista de códigos de hipótesis
  - `fuerzas_x`, `fuerzas_y`, `fuerzas_z`: Listas de fuerzas en daN
  - `momentos_x`, `momentos_y`, `momentos_z`: Listas de momentos en daN·m

---

## Ejemplo 1: Crear nodo y agregar cargas

```python
from NodoEstructural import NodoEstructural, Carga

# Crear nodo
nodo = NodoEstructural("C1_R", (1.3, 0.0, 9.0), "conductor")

# Crear carga de PESO (constante para todas las hipótesis)
carga_peso = Carga("Peso")
carga_peso.agregar_hipotesis("HIP_A0", fx=0, fy=0, fz=-200)
carga_peso.agregar_hipotesis("HIP_A1", fx=0, fy=0, fz=-200)
carga_peso.agregar_hipotesis("HIP_B1", fx=0, fy=0, fz=-500)  # Peso x 2.5

# Crear carga de VIENTO (varía según hipótesis)
carga_viento = Carga("Viento")
carga_viento.agregar_hipotesis("HIP_A0", fx=0, fy=0, fz=0)      # Sin viento
carga_viento.agregar_hipotesis("HIP_A1", fx=150, fy=0, fz=0)    # Vmax transversal
carga_viento.agregar_hipotesis("HIP_B1", fx=0, fy=0, fz=0)      # Sin viento

# Crear carga de TIRO (varía según hipótesis)
carga_tiro = Carga("Tiro")
carga_tiro.agregar_hipotesis("HIP_A0", fx=50, fy=100, fz=0)
carga_tiro.agregar_hipotesis("HIP_A1", fx=75, fy=150, fz=0)
carga_tiro.agregar_hipotesis("HIP_B1", fx=50, fy=100, fz=0)

# Agregar cargas al nodo
nodo.agregar_carga(carga_peso)
nodo.agregar_carga(carga_viento)
nodo.agregar_carga(carga_tiro)
```

---

## Ejemplo 2: Obtener cargas sumadas para una hipótesis

```python
# Obtener todas las cargas sumadas para HIP_A1
cargas_a1 = nodo.obtener_cargas_hipotesis("HIP_A1")

print(f"HIP_A1:")
print(f"  Fx = {cargas_a1['fx']} daN")  # 0 + 150 + 75 = 225 daN
print(f"  Fy = {cargas_a1['fy']} daN")  # 0 + 0 + 150 = 150 daN
print(f"  Fz = {cargas_a1['fz']} daN")  # -200 + 0 + 0 = -200 daN

# Obtener cargas para HIP_B1
cargas_b1 = nodo.obtener_cargas_hipotesis("HIP_B1")
print(f"HIP_B1:")
print(f"  Fx = {cargas_b1['fx']} daN")  # 0 + 0 + 50 = 50 daN
print(f"  Fy = {cargas_b1['fy']} daN")  # 0 + 0 + 100 = 100 daN
print(f"  Fz = {cargas_b1['fz']} daN")  # -500 + 0 + 0 = -500 daN
```

---

## Ejemplo 3: Nodo con rotación

```python
# Crear nodo rotado 90° en Z
nodo_rotado = NodoEstructural("C1A", (0, 1.3, 7.0), "conductor", rotacion_eje_z=90.0)

# Agregar carga en sistema LOCAL del nodo
carga_tiro = Carga("Tiro")
carga_tiro.agregar_hipotesis("HIP_A0", fx=100, fy=0, fz=-200)  # En sistema local
nodo_rotado.agregar_carga(carga_tiro)

# Obtener en sistema LOCAL (sin rotar)
cargas_local = nodo_rotado.obtener_cargas_hipotesis("HIP_A0")
print(f"Sistema LOCAL:")
print(f"  Fx = {cargas_local['fx']} daN")  # 100
print(f"  Fy = {cargas_local['fy']} daN")  # 0

# Obtener en sistema GLOBAL (rotado 90° en Z)
cargas_global = nodo_rotado.obtener_cargas_hipotesis_rotadas("HIP_A0", "global")
print(f"Sistema GLOBAL:")
print(f"  Fx = {cargas_global['fx']:.1f} daN")  # ≈ 0
print(f"  Fy = {cargas_global['fy']:.1f} daN")  # ≈ 100
```

---

## Ejemplo 4: Modificar una carga existente

```python
# Obtener carga existente
carga_peso = nodo.obtener_carga("Peso")

# Agregar nueva hipótesis
carga_peso.agregar_hipotesis("HIP_C1", fx=0, fy=0, fz=-300)

# Modificar hipótesis existente
carga_peso.agregar_hipotesis("HIP_A0", fx=0, fy=0, fz=-250)  # Actualiza valor
```

---

## Ejemplo 5: Listar hipótesis presentes

```python
# Listar todas las hipótesis que tienen valores en el nodo
hipotesis = nodo.listar_hipotesis()
print(f"Hipótesis presentes: {hipotesis}")
# Output: ['HIP_A0', 'HIP_A1', 'HIP_B1', 'HIP_C1']
```

---

## Ejemplo 6: Uso en EstructuraAEA_Mecanica

```python
# En asignar_cargas_hipotesis()

for nodo_nombre in nodos_conductor:
    # Crear carga de PESO
    carga_peso = Carga("Peso_Conductor")
    
    # Crear carga de VIENTO
    carga_viento = Carga("Viento_Conductor")
    
    # Crear carga de TIRO
    carga_tiro = Carga("Tiro_Conductor")
    
    # Para cada hipótesis, agregar valores
    for codigo_hip, config in hipotesis_dict.items():
        # Calcular peso
        peso = calcular_peso(...)
        carga_peso.agregar_hipotesis(codigo_hip, fx=0, fy=0, fz=-peso)
        
        # Calcular viento
        viento_x, viento_y = calcular_viento(...)
        carga_viento.agregar_hipotesis(codigo_hip, fx=viento_x, fy=viento_y, fz=0)
        
        # Calcular tiro
        tiro_x, tiro_y = calcular_tiro(...)
        carga_tiro.agregar_hipotesis(codigo_hip, fx=tiro_x, fy=tiro_y, fz=0)
    
    # Agregar todas las cargas al nodo
    nodo = self.geometria.nodos[nodo_nombre]
    nodo.agregar_carga(carga_peso)
    nodo.agregar_carga(carga_viento)
    nodo.agregar_carga(carga_tiro)
```

---

## Ejemplo 7: Calcular reacciones

```python
# En calcular_reacciones_tiros_cima()

for codigo_hip in lista_hipotesis:
    Fx_total, Fy_total, Fz_total = 0.0, 0.0, 0.0
    Mx_total, My_total, Mz_total = 0.0, 0.0, 0.0
    
    for nodo_nombre, nodo in self.geometria.nodos.items():
        if nodo_nombre == "BASE":
            continue
        
        # Obtener cargas en sistema GLOBAL (rotadas)
        cargas = nodo.obtener_cargas_hipotesis_rotadas(codigo_hip, "global")
        
        # Sumar fuerzas
        Fx_total += cargas["fx"]
        Fy_total += cargas["fy"]
        Fz_total += cargas["fz"]
        
        # Calcular momentos por producto vectorial r × F
        rx = nodo.x - x_apoyo
        ry = nodo.y - y_apoyo
        rz = nodo.z - z_apoyo
        
        Mx_total += (ry * cargas["fz"]) - (rz * cargas["fy"])
        My_total += (rz * cargas["fx"]) - (rx * cargas["fz"])
        Mz_total += (rx * cargas["fy"]) - (ry * cargas["fx"])
        
        # Sumar momentos directos
        Mx_total += cargas["mx"]
        My_total += cargas["my"]
        Mz_total += cargas["mz"]
```

---

## Ventajas de esta estructura

1. **Claridad**: Cada carga tiene nombre identificable
2. **Flexibilidad**: Fácil agregar/modificar hipótesis
3. **Trazabilidad**: Se puede ver qué carga contribuye cuánto
4. **Eficiencia**: No duplicar datos, listas compactas
5. **Extensibilidad**: Fácil agregar nuevos tipos de cargas

---

**Tokens used/total (62% session). Monthly limit: <1%**
