# Patch para agregar condicional de escala
import re

with open('c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2/utils/analisis_estatico.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar en generar_diagrama_3d, generar_diagrama_2d, _dibujar_3d, _dibujar_2d
pattern = r'(vmin, vmax = min\(vals\), max\(vals\))\s+norm = mcolors\.LogNorm\(vmin=max\(vmin, 0\.1\), vmax=max\(vmax, 0\.2\)\)'
replacement = r'\1\n            if escala == \'logaritmica\':\n                norm = mcolors.LogNorm(vmin=max(vmin, 0.1), vmax=max(vmax, 0.2))\n            else:\n                norm = mcolors.Normalize(vmin=vmin, vmax=vmax)'

content = re.sub(pattern, replacement, content)

# Agregar parametro escala a generar_diagrama_mqnt
content = content.replace(
    'self._dibujar_3d(ax, valores_dict, valores_subnodos, titulo, unidad, hipotesis, reacciones)',
    'self._dibujar_3d(ax, valores_dict, valores_subnodos, titulo, unidad, hipotesis, reacciones, escala)'
)
content = content.replace(
    'self._dibujar_2d(ax, valores_dict, valores_subnodos, titulo, unidad, hipotesis, reacciones)',
    'self._dibujar_2d(ax, valores_dict, valores_subnodos, titulo, unidad, hipotesis, reacciones, escala)'
)

with open('c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2/utils/analisis_estatico.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch aplicado")
