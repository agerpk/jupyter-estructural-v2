import json
import os
from pathlib import Path

# Nuevos coeficientes
COEF_A = 267.9232
COEF_B = 1.5149
COEF_C = -2662.3376

# Directorio de datos
data_dir = Path("data")

# Buscar todos los archivos .estructura.json y .familia.json
archivos = list(data_dir.glob("*.estructura.json")) + list(data_dir.glob("*.familia.json"))

print(f"Encontrados {len(archivos)} archivos JSON")

for archivo in archivos:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        modificado = False
        
        # Actualizar coeficientes en costeo (nivel raíz)
        if 'costeo' in data:
            if 'coef_a' in data['costeo']:
                data['costeo']['coef_a'] = COEF_A
                modificado = True
            if 'coef_b' in data['costeo']:
                data['costeo']['coef_b'] = COEF_B
                modificado = True
            if 'coef_c' in data['costeo']:
                data['costeo']['coef_c'] = COEF_C
                modificado = True
            
            # También en costeo.postes si existe
            if 'postes' in data['costeo']:
                if 'coef_a' in data['costeo']['postes']:
                    data['costeo']['postes']['coef_a'] = COEF_A
                    modificado = True
                if 'coef_b' in data['costeo']['postes']:
                    data['costeo']['postes']['coef_b'] = COEF_B
                    modificado = True
                if 'coef_c' in data['costeo']['postes']:
                    data['costeo']['postes']['coef_c'] = COEF_C
                    modificado = True
        
        # Para archivos .familia.json, actualizar en estructuras
        if 'estructuras' in data:
            for estructura in data['estructuras']:
                if 'costeo' in estructura and 'postes' in estructura['costeo']:
                    if 'coef_a' in estructura['costeo']['postes']:
                        estructura['costeo']['postes']['coef_a'] = COEF_A
                        modificado = True
                    if 'coef_b' in estructura['costeo']['postes']:
                        estructura['costeo']['postes']['coef_b'] = COEF_B
                        modificado = True
                    if 'coef_c' in estructura['costeo']['postes']:
                        estructura['costeo']['postes']['coef_c'] = COEF_C
                        modificado = True
        
        if modificado:
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"OK {archivo.name}")
        else:
            print(f"SKIP {archivo.name} (sin coeficientes)")
    
    except Exception as e:
        print(f"ERROR {archivo.name}: {e}")

print("\nActualizacion completada")
