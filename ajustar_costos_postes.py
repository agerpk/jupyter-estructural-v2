import numpy as np

# Datos proporcionados
datos = [
    [7.5, 0.15, 200, 371.06],
    [7.5, 0.15, 300, 410.16],
    [8, 0.15, 300, 463.22],
    [8, 0.15, 450, 508.18],
    [9, 0.15, 300, 553.40],
    [9, 0.15, 450, 644.82],
    [9, 0.15, 600, 752.43],
    [11, 0.17, 300, 759.00],
    [11, 0.17, 450, 848.20],
    [11, 0.17, 600, 931.61],
    [11, 0.17, 800, 1078.25],
    [11, 0.17, 1000, 1270.74],
    [12, 0.19, 300, 877.00],
    [12, 0.19, 450, 998.44],
    [12, 0.19, 600, 1113.67],
    [12, 0.19, 800, 1367.13],
    [12, 0.19, 1000, 1597.54],
    [12, 0.19, 1200, 1835.64],
    [13.5, 0.21, 300, 1265.34],
    [13.5, 0.21, 450, 1411.04],
    [13.5, 0.21, 600, 1664.11],
    [13.5, 0.21, 1000, 1963.96],
    [13.5, 0.21, 1500, 2530.67],
    [15, 0.23, 600, 2370.03],
    [15, 0.23, 800, 2629.97],
    [15, 0.23, 1200, 3287.46],
    [15, 0.23, 2000, 4510.70],
    [18, 0.25, 1200, 4341.29],
    [18, 0.25, 1500, 5032.30],
    [18, 0.25, 2000, 6158.93]
]

# Extraer variables
X = np.array([[1, d[0], d[2]] for d in datos])  # [1, Longitud_m, Resistencia_daN]
y = np.array([d[3] for d in datos])  # COSTO CER

# Ajustar modelo usando mínimos cuadrados: (X^T X)^-1 X^T y
coeficientes = np.linalg.lstsq(X, y, rcond=None)[0]

C = coeficientes[0]  # Término independiente
A = coeficientes[1]  # Coeficiente para Longitud_m
B = coeficientes[2]  # Coeficiente para Resistencia_daN

# Calcular R²
y_pred = X @ coeficientes
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r2 = 1 - (ss_res / ss_tot)

# Mostrar resultados
print("=" * 60)
print("AJUSTE POLINOMIAL: Costo = A × Longitud_m + B × Resistencia_daN + C")
print("=" * 60)
print(f"\nCoeficientes del modelo:")
print(f"  A (Longitud_m):      {A:12.4f}")
print(f"  B (Resistencia_daN): {B:12.6f}")
print(f"  C (Constante):       {C:12.4f}")
print(f"\nCoeficiente de determinación (R²): {r2:.6f}")
print(f"Porcentaje de varianza explicada:  {r2*100:.2f}%")

# Validar con algunos datos
print("\n" + "=" * 60)
print("VALIDACIÓN CON DATOS DE ENTRADA")
print("=" * 60)
print(f"{'Long':>6} {'Resist':>7} {'Real':>10} {'Predicho':>10} {'Error':>10} {'Error%':>8}")
print("-" * 60)

for d in datos[::3]:  # Mostrar cada 3 datos
    longitud, _, resistencia, costo_real = d[0], d[1], d[2], d[3]
    costo_pred = A * longitud + B * resistencia + C
    error = costo_pred - costo_real
    error_pct = (error / costo_real) * 100
    print(f"{longitud:6.1f} {resistencia:7.0f} {costo_real:10.2f} {costo_pred:10.2f} {error:10.2f} {error_pct:7.2f}%")

print("\n" + "=" * 60)
print("FÓRMULA FINAL")
print("=" * 60)
print(f"Costo = {A:.4f} × Longitud_m + {B:.6f} × Resistencia_daN + {C:.4f}")
print("=" * 60)
