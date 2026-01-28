"""Util para generar tabla PLS-CADD a partir de EstructuraAEA_Geometria"""

import csv
from pathlib import Path
import pandas as pd
from config.app_config import CACHE_DIR
from utils.calculo_cache import CalculoCache


ALLOWED_INSULATOR_TYPES = ["clamp", "Post", "Strain", "Suspension", "2-Part"]


def generar_tabla_estructura_plscadd(estructura_geometria, estructura_data):
    """Genera DataFrame y CSV con formato PLS-CADD para una estructura.

    Args:
        estructura_geometria: instancia EstructuraAEA_Geometria
        estructura_data: dict con parámetros de estructura (plantilla o cargada)

    Returns:
        tuple(df, csv_filename) donde csv_filename es nombre de archivo en CACHE_DIR
    """
    # Validaciones básicas
    if estructura_geometria is None or estructura_data is None:
        raise ValueError("estructura_geometria y estructura_data son requeridos")

    # Obtener nodos
    nodes_key = getattr(estructura_geometria, 'nodes_key', None) or estructura_geometria.obtener_nodes_key()
    if not nodes_key:
        raise ValueError("No hay nodes_key en la geometría")

    # Parámetros importantes
    titulo = estructura_data.get('TITULO', 'estructura')
    hash_params = CalculoCache.calcular_hash(estructura_data)
    csv_filename = f"{titulo}_{hash_params}.csv"
    csv_path = CACHE_DIR / csv_filename

    Vn = estructura_data.get('Vn', estructura_data.get('TENSION', 220))
    Ka = None
    try:
        Ka = estructura_geometria.dimensiones.get('Ka', 1)
    except Exception:
        Ka = 1

    PCADENA = estructura_data.get('PCADENA', 0.0)  # en daN según decisión: multiplicar por 10
    Lk = estructura_data.get('Lk', 0.0)
    tipo_estructura = (estructura_data.get('TIPO_ESTRUCTURA', '') or '').lower()
    terna = estructura_data.get('TERNA', 'Simple')

    # Calcular alturas
    z_values = [coords[2] for coords in nodes_key.values()]
    altura_max = max(z_values) if z_values else 0.0

    # Clasificar nodos
    nodos_guardia = []
    nodos_conductor = []
    for nombre, coords in nodes_key.items():
        # Heurística: HG* -> guardia, C* not CROSS -> conductor
        if nombre.upper().startswith('HG'):
            nodos_guardia.append((nombre, coords))
        elif nombre.upper().startswith('C') and not nombre.upper().startswith('CROSS'):
            nodos_conductor.append((nombre, coords))
        else:
            # intentar inferir por tipo si existe objeto
            try:
                nodo_obj = estructura_geometria.nodos.get(nombre)
                if getattr(nodo_obj, 'tipo', '').lower() == 'guardia':
                    nodos_guardia.append((nombre, coords))
                elif getattr(nodo_obj, 'tipo', '').lower() == 'conductor':
                    nodos_conductor.append((nombre, coords))
            except Exception:
                pass

    # Asignar sets y phases
    rows = []

    # Set 1: guardia
    phase = 1
    for nombre, coords in sorted(nodos_guardia, key=lambda x: x[0]):
        x, y, z = coords
        insul_type = estructura_data.get('insulator_type_guardia', 'Clamp')
        insul_weight = 0.0
        insul_wind_area = 0.0
        insul_length = 0.0
        attach_trans = x
        attach_dist_below = round(altura_max - z, 3)
        attach_long = y
        min_req = "No Limit"

        rows.append({
            'Set #': 1,
            'Phase #': phase,
            'Dead End Set': 'No',
            'Set Description': 'HG',
            'Insulator Type': insul_type,
            'Insul. Weight (N)': insul_weight,
            'Insul. Wind Area (cm^2)': round(insul_wind_area, 2),
            'Insul. Length (m)': insul_length,
            'Attach. Trans. Offset (m)': round(attach_trans, 3),
            'Attach. Dist. Below Top (m)': round(attach_dist_below, 3),
            'Attach. Longit. Offset (m)': round(attach_long, 3),
            'Min. Req. Vertical Load (uplift) (N)': min_req
        })
        phase += 1

    # Set 2/3: conductores
    # Determinar sets según terna y signo x
    cond_pos = [n for n in nodos_conductor if n[1][0] >= 0]
    cond_neg = [n for n in nodos_conductor if n[1][0] < 0]

    if terna.lower().startswith('simple'):
        # All conductors in Set 2
        set_num = 2
        phase = 1
        for nombre, coords in sorted(nodos_conductor, key=lambda x: (x[1][0], x[0])):
            x, y, z = coords
            insul_type = estructura_data.get('insulator_type_conductor', 'Suspension')
            insul_weight = float(PCADENA) * 10.0  # PCADENA en daN --> N = daN*10
            # Wind area formula
            if 'suspension' in tipo_estructura or 'suspensión' in tipo_estructura:
                insul_wind_area = ((0.5 + Vn / 150.0) * Ka * 0.146) / 10000.0
            else:
                insul_wind_area = ((0.5 + Vn / 75.0) * Ka * 0.146) / 10000.0
            insul_length = Lk
            attach_trans = x
            attach_dist_below = round(altura_max - z, 3)
            attach_long = y
            min_req = "No Uplift" if ('suspension' in tipo_estructura or 'suspensión' in tipo_estructura) else "No Limit"

            rows.append({
                'Set #': set_num,
                'Phase #': phase,
                'Dead End Set': 'No',
                'Set Description': 'COND',
                'Insulator Type': insul_type,
                'Insul. Weight (N)': round(insul_weight, 2),
                'Insul. Wind Area (cm^2)': round(insul_wind_area, 2),
                'Insul. Length (m)': round(insul_length, 3),
                'Attach. Trans. Offset (m)': round(attach_trans, 3),
                'Attach. Dist. Below Top (m)': round(attach_dist_below, 3),
                'Attach. Longit. Offset (m)': round(attach_long, 3),
                'Min. Req. Vertical Load (uplift) (N)': min_req
            })
            phase += 1
    else:
        # Doble terna: categorize pos->set 2, neg->set 3
        # Set 2 (x>=0)
        phase = 1
        for nombre, coords in sorted(cond_pos, key=lambda x: x[0]):
            x, y, z = coords
            insul_type = estructura_data.get('insulator_type_conductor', 'Suspension')
            insul_weight = float(PCADENA) * 10.0
            if 'suspension' in tipo_estructura or 'suspensión' in tipo_estructura:
                insul_wind_area = ((0.5 + Vn / 150.0) * Ka * 0.146) / 10000.0
            else:
                insul_wind_area = ((0.5 + Vn / 75.0) * Ka * 0.146) / 10000.0
            insul_length = Lk
            attach_trans = x
            attach_dist_below = round(altura_max - z, 3)
            attach_long = y
            min_req = "No Uplift" if ('suspension' in tipo_estructura or 'suspensión' in tipo_estructura) else "No Limit"

            rows.append({
                'Set #': 2,
                'Phase #': phase,
                'Dead End Set': 'No',
                'Set Description': '1TERNA',
                'Insulator Type': insul_type,
                'Insul. Weight (N)': round(insul_weight, 2),
                'Insul. Wind Area (cm^2)': round(insul_wind_area, 2),
                'Insul. Length (m)': round(insul_length, 3),
                'Attach. Trans. Offset (m)': round(attach_trans, 3),
                'Attach. Dist. Below Top (m)': round(attach_dist_below, 3),
                'Attach. Longit. Offset (m)': round(attach_long, 3),
                'Min. Req. Vertical Load (uplift) (N)': min_req
            })
            phase += 1

        # Set 3 (x<0)
        phase = 1
        for nombre, coords in sorted(cond_neg, key=lambda x: x[0]):
            x, y, z = coords
            insul_type = estructura_data.get('insulator_type_conductor', 'Suspension')
            insul_weight = float(PCADENA) * 10.0
            if 'suspension' in tipo_estructura or 'suspensión' in tipo_estructura:
                insul_wind_area = ((0.5 + Vn / 150.0) * Ka * 0.146) / 10000.0
            else:
                insul_wind_area = ((0.5 + Vn / 75.0) * Ka * 0.146) / 10000.0
            insul_length = Lk
            attach_trans = x
            attach_dist_below = round(altura_max - z, 3)
            attach_long = y
            min_req = "No Uplift" if ('suspension' in tipo_estructura or 'suspensión' in tipo_estructura) else "No Limit"

            rows.append({
                'Set #': 3,
                'Phase #': phase,
                'Dead End Set': 'No',
                'Set Description': '2TERNA',
                'Insulator Type': insul_type,
                'Insul. Weight (N)': round(insul_weight, 2),
                'Insul. Wind Area (cm^2)': round(insul_wind_area, 2),
                'Insul. Length (m)': round(insul_length, 3),
                'Attach. Trans. Offset (m)': round(attach_trans, 3),
                'Attach. Dist. Below Top (m)': round(attach_dist_below, 3),
                'Attach. Longit. Offset (m)': round(attach_long, 3),
                'Min. Req. Vertical Load (uplift) (N)': min_req
            })
            phase += 1

    # Crear DataFrame
    df = pd.DataFrame(rows)

    # Escribir CSV con formato: cabeceras iniciales de datos generales + tabla
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Structure file name'])
            # Escribir 'Description' como columna separada para evitar comas internas
            writer.writerow(['Description', titulo])
            # Corregir paréntesis y evitar comillas manuales
            writer.writerow(['Height (ground to top of structure) (m)', f'{altura_max:.3f}'])
            writer.writerow(['Embedded length (for report purposes only) (m)', f'{(0.1*altura_max):.3f}'])
            lowest_conductor_z = min([c[1][2] for c in nodos_conductor]) if nodos_conductor else ''
            if lowest_conductor_z != '':
                writer.writerow(['Lowest wire attachment point height above ground (m)', f'{lowest_conductor_z:.12f}'])
            else:
                writer.writerow(['Lowest wire attachment point height above ground (m)', ''])
            writer.writerow([])
            # Escribir columnas y filas
            header = list(df.columns)
            writer.writerow(header)
            for _, row in df.iterrows():
                writer.writerow([row[col] for col in header])

        print(f"✅ CSV PLS-CADD generado: {csv_path}")
    except Exception as e:
        print(f"⚠️ Error generando CSV PLS-CADD: {e}")
        raise

    return df, csv_filename
