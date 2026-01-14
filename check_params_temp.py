import sys
sys.path.insert(0, r'C:\Users\gpesoa\MobiDrive\jupyter_estructural_v2')

import json
from utils.parametros_manager import ParametrosManager

# Cargar plantilla
with open('data/plantilla.estructura.json', 'r', encoding='utf-8') as f:
    plantilla = json.load(f)

# Obtener metadata
metadata = ParametrosManager.PARAMETROS_METADATA

# Parámetros de primer nivel en plantilla
params_plantilla = set(plantilla.keys())

# Parámetros de primer nivel en metadata (sin puntos)
params_metadata = set([k for k in metadata.keys() if '.' not in k])

# Parámetros en plantilla pero NO en metadata
faltantes = params_plantilla - params_metadata

print("=" * 80)
print("PARÁMETROS EN PLANTILLA PERO NO EN METADATA:")
print("=" * 80)
for p in sorted(faltantes):
    valor = plantilla[p]
    tipo = type(valor).__name__
    print(f"  - {p:40} (tipo: {tipo})")

print(f"\nTotal faltantes: {len(faltantes)}")
