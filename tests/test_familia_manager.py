import json
from datetime import datetime
from utils.familia_manager import FamiliaManager


def test_cargar_familia_name_normalization(tmp_path):
    # Usar un DATA_DIR temporal para pruebas
    FamiliaManager.DATA_DIR = tmp_path

    familia = {
        "nombre_familia": "Mi Familia",
        "fecha_creacion": datetime.now().isoformat(),
        "fecha_modificacion": datetime.now().isoformat(),
        "estructuras": {
            "Estr.1": {"TITULO": "E1", "cantidad": 1}
        }
    }

    # Guardar usando la API
    assert FamiliaManager.guardar_familia(familia) is True

    # Probar distintas variantes de nombre que el usuario podría introducir
    for nombre in ["Mi Familia", "Mi Familia.familia", "Mi Familia.familia.json", "Mi_Familia"]:
        cargada = FamiliaManager.cargar_familia(nombre)
        assert cargada["nombre_familia"] == "Mi Familia"
        assert "estructuras" in cargada
