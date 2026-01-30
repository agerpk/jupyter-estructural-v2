from datetime import datetime
from utils.familia_manager import FamiliaManager


def test_guardar_estados_no_sobreescribe_campos(tmp_path):
    FamiliaManager.DATA_DIR = tmp_path

    familia = {
        "nombre_familia": "EstTest",
        "fecha_creacion": datetime.now().isoformat(),
        "fecha_modificacion": datetime.now().isoformat(),
        "estructuras": {
            "Estr.1": {"TITULO": "E1", "cantidad": 2, "L_vano": 400.0},
            "Estr.2": {"TITULO": "E2", "cantidad": 1, "L_vano": 350.0}
        }
    }
    assert FamiliaManager.guardar_familia(familia)

    # Simular guardado de estados (sin tocar tabla)
    estados = {"1": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, "espesor_hielo": 0, "restriccion_conductor": 0.25, "restriccion_guardia": 0.7, "relflecha": 0.9}}

    familia_guardada = FamiliaManager.cargar_familia("EstTest")
    familia_guardada["estados_climaticos"] = estados
    for k in familia_guardada["estructuras"]:
        familia_guardada["estructuras"][k]["estados_climaticos"] = estados

    assert FamiliaManager.guardar_familia(familia_guardada)

    recargada = FamiliaManager.cargar_familia("EstTest")
    # Verificar que L_vano no fue sobreescrito
    assert recargada["estructuras"]["Estr.1"]["L_vano"] == 400.0
    assert recargada["estructuras"]["Estr.2"]["L_vano"] == 350.0
    assert "estados_climaticos" in recargada
