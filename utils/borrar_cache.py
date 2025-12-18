"""
Utilidad para borrar archivos de cache
"""

from pathlib import Path
from config.app_config import DATA_DIR, CACHE_DIR
import shutil

def borrar_cache():
    """
    Borra todos los archivos de cache en /data excepto archivos protegidos
    
    Returns:
        tuple: (cantidad_archivos_borrados, lista_errores)
    """
    archivos_protegidos = {
        "cables.json",
        "navegacion_state.json"
    }
    
    extensiones_cache = {
        ".calculoCMC.json",
        ".calculoDGE.json", 
        ".calculoDME.json",
        ".calculoSPH.json",
        ".calculoARBOLES.json",
        ".calculoTODO.json",
        ".arbolcarga.",
        ".png",
        ".json"
    }
    
    archivos_borrados = 0
    errores = []
    
    # Borrar archivos en /data
    try:
        for archivo in DATA_DIR.iterdir():
            if not archivo.is_file():
                continue
                
            # Proteger archivos esenciales
            if archivo.name in archivos_protegidos:
                continue
            
            # Proteger archivos .estructura.json y .hipotesismaestro.json
            if archivo.name.endswith(".estructura.json") or archivo.name.endswith(".hipotesismaestro.json"):
                continue
            
            # Borrar archivos de cache
            es_cache = any(ext in archivo.name for ext in extensiones_cache)
            
            if es_cache:
                try:
                    archivo.unlink()
                    archivos_borrados += 1
                except Exception as e:
                    errores.append(f"{archivo.name}: {str(e)}")
    
    except Exception as e:
        errores.append(f"Error al acceder a /data: {str(e)}")
    
    # Borrar todo el contenido de /data/cache
    try:
        if CACHE_DIR.exists():
            for item in CACHE_DIR.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                        archivos_borrados += 1
                    elif item.is_dir():
                        shutil.rmtree(item)
                        archivos_borrados += 1
                except Exception as e:
                    errores.append(f"{item.name}: {str(e)}")
    except Exception as e:
        errores.append(f"Error al acceder a /data/cache: {str(e)}")
    
    return archivos_borrados, errores
