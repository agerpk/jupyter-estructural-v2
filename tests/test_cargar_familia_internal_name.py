import json
from datetime import datetime
from utils.familia_manager import FamiliaManager


def test_cargar_familia_por_nombre_interno(tmp_path):
    # Preparar DATA_DIR temporal
    FamiliaManager.DATA_DIR = tmp_path

    # Crear archivo cuyo nombre de archivo difiere del campo 'nombre_familia' interno
    archivo = tmp_path / "PSJ_Reticuladas_S_400_450_3100MSNM.familia.json"
    contenido = {
        "nombre_familia": "PSJ_S_Reticuladas_400_450_3100MSNM",
        "fecha_creacion": datetime.now().isoformat(),
        "fecha_modificacion": datetime.now().isoformat(),
        "estructuras": {}
    }
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(contenido, f, indent=2, ensure_ascii=False)

    # Solicitar cargando por el nombre interno (diferente del stem del archivo)
    cargada = FamiliaManager.cargar_familia("PSJ_S_Reticuladas_400_450_3100MSNM")
    assert cargada['nombre_familia'] == "PSJ_S_Reticuladas_400_450_3100MSNM"

    # También debe funcionar usando el stem del archivo
    cargada2 = FamiliaManager.cargar_familia("PSJ_Reticuladas_S_400_450_3100MSNM")
    assert cargada2['nombre_familia'] == "PSJ_S_Reticuladas_400_450_3100MSNM"
