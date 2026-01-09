import re

with open('c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2/utils/analisis_estatico.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Corregir backtick-n a newline real
content = content.replace('`n', '\n')

# Cambiar defaults a lineal
content = re.sub(r'escala: str = "logaritmica"', 'escala: str = "lineal"', content)
content = re.sub(r"escala: str = 'logaritmica'", 'escala: str = "lineal"', content)

# Agregar minimo en etiquetas (3D)
content = re.sub(
    r'ax\.text2D\(0\.02, 0\.98, f"Máximo: \{vmax:.2f\} daN\.m"',
    r'ax.text2D(0.02, 0.98, f"Máximo: {vmax:.2f}\\nMínimo: {vmin:.2f}"',
    content
)
content = re.sub(
    r'ax\.text2D\(0\.02, 0\.98, f"Máximo: \{vmax:.2f\} \{unidad\}"',
    r'ax.text2D(0.02, 0.98, f"Máximo: {vmax:.2f}\\nMínimo: {vmin:.2f}"',
    content
)

# Agregar minimo en etiquetas (2D)
content = re.sub(
    r'ax\.text\(0\.02, 0\.98, f"Máximo: \{vmax:.2f\} daN\.m"',
    r'ax.text(0.02, 0.98, f"Máximo: {vmax:.2f}\\nMínimo: {vmin:.2f}"',
    content
)
content = re.sub(
    r'ax\.text\(0\.02, 0\.98, f"Máximo: \{vmax:.2f\} \{unidad\}"',
    r'ax.text(0.02, 0.98, f"Máximo: {vmax:.2f}\\nMínimo: {vmin:.2f}"',
    content
)

with open('c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2/utils/analisis_estatico.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo corregido")
