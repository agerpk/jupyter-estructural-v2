from utils.parametros_manager import ParametrosManager
from utils.familia_manager import FamiliaManager
import json


def test_parametro_presente_en_tabla_plantilla():
    # Cargar plantilla
    with open("data/plantilla.estructura.json", "r", encoding="utf-8") as f:
        plantilla = json.load(f)

    tabla = ParametrosManager.estructura_a_tabla(plantilla)

    assert any(r['parametro'] == 'hipotesis_a5_dme_15pc_si_lk_mayor_2_5' for r in tabla), \
        "El parámetro hipotesis_a5_dme_15pc_si_lk_mayor_2_5 debe aparecer en la tabla de plantilla"


def test_parametro_presente_en_tabla_familia():
    # Crear familia sencilla basada en la plantilla
    with open("data/plantilla.estructura.json", "r", encoding="utf-8") as f:
        plantilla = json.load(f)

    familia = {
        "nombre_familia": "TestFam",
        "estructuras": {"Estr.1": plantilla}
    }

    tabla_data, columnas = FamiliaManager.familia_a_tabla(familia)

    assert any(r['parametro'] == 'hipotesis_a5_dme_15pc_si_lk_mayor_2_5' for r in tabla_data), \
        "La tabla de familia debe contener la fila del parámetro hipotesis_a5_dme_15pc_si_lk_mayor_2_5"


def test_tabla_a_familia_preserva_bool():
    # Cargar plantilla y generar tabla
    with open("data/plantilla.estructura.json", "r", encoding="utf-8") as f:
        plantilla = json.load(f)

    tabla = ParametrosManager.estructura_a_tabla(plantilla)

    # Encontrar fila del parámetro y forzar valor False para Estr.1
    for fila in tabla:
        if fila['parametro'] == 'hipotesis_a5_dme_15pc_si_lk_mayor_2_5':
            fila['Estr.1'] = False
            break

    # Construir columnas para tabla (simular familia con una columna Estr.1)
    columnas = [
        {"name": "Parámetro", "id": "parametro"},
        {"name": "Estr.1", "id": "Estr.1"}
    ]

    familia_result = FamiliaManager.tabla_a_familia(tabla, columnas, "TestFam2")

    assert familia_result['estructuras']['Estr.1']['hipotesis_a5_dme_15pc_si_lk_mayor_2_5'] is False, \
        "Al convertir la tabla a familia, el valor booleano debe preservarse"
