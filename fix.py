with open('c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2/utils/analisis_estatico.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Corregir backtick-n
content = content.replace('`n', '\n')

# 2. Cambiar defaults a lineal
content = content.replace('escala: str = "logaritmica"', 'escala: str = "lineal"')

# 3. Agregar minimo en etiquetas 3D (daN.m)
content = content.replace(
    'ax.text2D(0.02, 0.98, f"Máximo: {vmax:.2f} daN.m"',
    'ax.text2D(0.02, 0.98, f"Máximo: {vmax:.2f}\\nMínimo: {vmin:.2f}"'
)

# 4. Agregar minimo en etiquetas 3D (unidad)
content = content.replace(
    'ax.text2D(0.02, 0.98, f"Máximo: {vmax:.2f} {unidad}"',
    'ax.text2D(0.02, 0.98, f"Máximo: {vmax:.2f}\\nMínimo: {vmin:.2f}"'
)

# 5. Agregar minimo en etiquetas 2D (daN.m)
content = content.replace(
    'ax.text(0.02, 0.98, f"Máximo: {vmax:.2f} daN.m"',
    'ax.text(0.02, 0.98, f"Máximo: {vmax:.2f}\\nMínimo: {vmin:.2f}"'
)

# 6. Agregar minimo en etiquetas 2D (unidad)
content = content.replace(
    'ax.text(0.02, 0.98, f"Máximo: {vmax:.2f} {unidad}"',
    'ax.text(0.02, 0.98, f"Máximo: {vmax:.2f}\\nMínimo: {vmin:.2f}"'
)

with open('c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2/utils/analisis_estatico.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK")
