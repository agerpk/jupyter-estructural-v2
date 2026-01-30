import json
from datetime import datetime
from utils.familia_manager import FamiliaManager


def test_tabla_a_familia_preserves_existing_values(tmp_path):
    # Preparar DATA_DIR temporal
    FamiliaManager.DATA_DIR = tmp_path

    # Guardar familia existente con valores iniciales
    familia = {
        "nombre_familia": "TestFam",
        "fecha_creacion": datetime.now().isoformat(),
        "fecha_modificacion": datetime.now().isoformat(),
        "estructuras": {
            "Estr.1": {
                "TITULO": "E1",
                "cantidad": 1,
                "L_vano": 350.0,
                "costeo": {"postes": {"coef_a": 100.0}}
            }
        }
    }
    assert FamiliaManager.guardar_familia(familia) is True

    # Crear tabla donde la mayoría de celdas están vacías (simula modal de estados)
    tabla = [
        {"parametro": "TITULO", "tipo": "str", "valor": "E1"},
        {"parametro": "cantidad", "tipo": "int", "valor": "1"},
        {"parametro": "L_vano", "tipo": "float", "valor": ""},
        {"parametro": "costeo.postes.coef_a", "tipo": "float", "valor": ""}
    ]
    columnas = [
        {"id": "parametro"},
        {"id": "Estr.1"}
    ]

    familia_result = FamiliaManager.tabla_a_familia(tabla, columnas, "TestFam")

    # Comprobar que se preservaron los valores existentes (no convertidos a 0)
    assert "estructuras" in familia_result
    estr1 = familia_result["estructuras"]["Estr.1"]
    assert estr1["L_vano"] == 350.0
    assert estr1["costeo"]["postes"]["coef_a"] == 100.0
