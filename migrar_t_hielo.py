"""
Script de migración: t_hielo de primer nivel -> estados_climaticos
"""
import re
from pathlib import Path

def migrar_archivo(ruta):
    """Migra un archivo Python para usar estados_climaticos en lugar de t_hielo"""
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    original = contenido
    
    # Patrón 1: estructura_actual.get('t_hielo') -> obtener de estado 4 (Vmed con hielo)
    contenido = re.sub(
        r"estructura_actual\.get\(['\"]t_hielo['\"]\s*,?\s*[\d.]*\)",
        "estructura_actual.get('estados_climaticos', {}).get('4', {}).get('espesor_hielo', 0.01)",
        contenido
    )
    
    # Patrón 2: estructura_actual['t_hielo'] -> obtener de estado 4
    contenido = re.sub(
        r"estructura_actual\[['\"]t_hielo['\"]\]",
        "estructura_actual.get('estados_climaticos', {}).get('4', {}).get('espesor_hielo', 0.01)",
        contenido
    )
    
    # Patrón 3: estructura['t_hielo'] -> obtener de estado 4
    contenido = re.sub(
        r"estructura\[['\"]t_hielo['\"]\]",
        "estructura.get('estados_climaticos', {}).get('4', {}).get('espesor_hielo', 0.01)",
        contenido
    )
    
    # Patrón 4: params.get('t_hielo') -> obtener de estado 4
    contenido = re.sub(
        r"params\.get\(['\"]t_hielo['\"]\s*,?\s*[\d.]*\)",
        "params.get('estados_climaticos', {}).get('4', {}).get('espesor_hielo', 0)",
        contenido
    )
    
    # Patrón 5: "t_hielo": float(t_hielo) -> comentar (ya no se guarda en primer nivel)
    contenido = re.sub(
        r'(\s+)"t_hielo":\s*float\(t_hielo\)',
        r'\1# "t_hielo": float(t_hielo)  # MIGRADO: ahora en estados_climaticos',
        contenido
    )
    
    if contenido != original:
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return True
    return False

# Archivos a migrar
archivos = [
    "ListarCargas.py",
    "EstructuraAEA_Mecanica.py",
    "controllers/aee_controller.py",
    "controllers/arboles_controller.py",
    "controllers/calculo_controller.py",
    "controllers/ejecutar_calculos.py",
    "controllers/fundacion_controller.py",
    "controllers/geometria_controller.py",
    "controllers/mecanica_controller.py",
    "controllers/parametros_controller.py",
    "controllers/seleccion_poste_controller.py",
    "utils/calculo_mecanico_cables.py",
    "utils/calculo_objetos.py",
    "utils/comparativa_cmc_calculo.py"
]

print("🔄 INICIANDO MIGRACIÓN t_hielo -> estados_climaticos\n")

base_path = Path("c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2")
migrados = 0

for archivo in archivos:
    ruta = base_path / archivo
    if ruta.exists():
        if migrar_archivo(ruta):
            print(f"✅ Migrado: {archivo}")
            migrados += 1
        else:
            print(f"⏭️  Sin cambios: {archivo}")
    else:
        print(f"⚠️  No encontrado: {archivo}")

print(f"\n✅ Migración completada: {migrados} archivos modificados")
print("\n📝 NOTA: t_hielo permanece en plantilla.estructura.json para compatibilidad")
print("   pero el código ahora usa estados_climaticos['4']['espesor_hielo']")
