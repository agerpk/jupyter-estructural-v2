import json
from pathlib import Path

COEF_A = 267.9232
COEF_B = 1.5149
COEF_C = -2662.3376

data_dir = Path("data")
archivos = list(data_dir.glob("*.estructura.json")) + list(data_dir.glob("*.familia.json"))

for archivo in archivos:
    with open(archivo, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mod = False
    
    if 'costeo' in data and 'postes' in data['costeo']:
        data['costeo']['postes']['coef_a'] = COEF_A
        data['costeo']['postes']['coef_b'] = COEF_B
        data['costeo']['postes']['coef_c'] = COEF_C
        mod = True
    
    if 'estructuras' in data:
        for est in data['estructuras']:
            if 'costeo' in est and 'postes' in est['costeo']:
                est['costeo']['postes']['coef_a'] = COEF_A
                est['costeo']['postes']['coef_b'] = COEF_B
                est['costeo']['postes']['coef_c'] = COEF_C
                mod = True
    
    if mod:
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"OK {archivo.name}")

print("Completado")
