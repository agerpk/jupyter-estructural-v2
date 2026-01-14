"""
Script para migrar t_hielo de primer nivel a estados_climaticos
"""
import re
from pathlib import Path

# Función helper para agregar al inicio de archivos que la necesiten
HELPER_FUNCTION = '''
def _obtener_t_hielo_maximo(estados_climaticos):
    """Obtiene el máximo espesor de hielo de los estados climáticos"""
    return max([e.get("espesor_hielo", 0) for e in estados_climaticos.values()], default=0)
'''

# Patrones a reemplazar
PATTERNS = [
    # Patrón 1: estructura_actual.get('t_hielo')
    (r"estructura_actual\.get\('t_hielo'(?:,\s*[\d.]+)?\)",
     "_obtener_t_hielo_maximo(estructura_actual.get('estados_climaticos', {}))"),
    
    # Patrón 2: estructura_config.get("t_hielo")
    (r'estructura_config\.get\("t_hielo"(?:,\s*[\d.]+)?\)',
     '_obtener_t_hielo_maximo(estructura_config.get("estados_climaticos", {}))'),
    
    # Patrón 3: estructura["t_hielo"]
    (r'estructura\["t_hielo"\]',
     '_obtener_t_hielo_maximo(estructura.get("estados_climaticos", {}))'),
    
    # Patrón 4: params.get('t_hielo')
    (r"params\.get\('t_hielo'(?:,\s*[\d.]+)?\)",
     "_obtener_t_hielo_maximo(params.get('estados_climaticos', {}))"),
    
    # Patrón 5: parametros.get("t_hielo")
    (r'parametros\.get\("t_hielo"(?:,\s*[\d.]+)?\)',
     '_obtener_t_hielo_maximo(parametros.get("estados_climaticos", {}))'),
]

# Archivos a procesar (excluyendo los ya migrados)
FILES_TO_PROCESS = [
    "CalculoCables.py",
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
    "utils/comparar_cables_manager.py",
    "utils/comparativa_cmc_calculo.py",
]

def process_file(filepath):
    """Procesa un archivo aplicando los patrones de reemplazo"""
    path = Path(filepath)
    if not path.exists():
        print(f"Archivo no encontrado: {filepath}")
        return False
    
    content = path.read_text(encoding='utf-8')
    original_content = content
    
    # Aplicar patrones
    for pattern, replacement in PATTERNS:
        content = re.sub(pattern, replacement, content)
    
    # Si hubo cambios, agregar helper function si no existe
    if content != original_content:
        if '_obtener_t_hielo_maximo' not in content:
            # Agregar después de los imports
            import_end = content.rfind('\nimport ')
            if import_end == -1:
                import_end = content.rfind('\nfrom ')
            
            if import_end != -1:
                next_newline = content.find('\n\n', import_end)
                if next_newline != -1:
                    content = content[:next_newline] + '\n' + HELPER_FUNCTION + content[next_newline:]
        
        path.write_text(content, encoding='utf-8')
        print(f"Migrado: {filepath}")
        return True
    else:
        print(f"Sin cambios: {filepath}")
        return False

def main():
    print("Iniciando migracion de t_hielo...\n")
    
    base_path = Path(r"C:\Users\gpesoa\MobiDrive\jupyter_estructural_v2")
    migrated = 0
    for file in FILES_TO_PROCESS:
        if process_file(base_path / file):
            migrated += 1
    
    print(f"\nMigracion completada: {migrated}/{len(FILES_TO_PROCESS)} archivos modificados")

if __name__ == "__main__":
    main()
