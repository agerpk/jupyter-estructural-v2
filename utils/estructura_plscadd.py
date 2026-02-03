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

    import re

    def _extract_trailing_index(name):
        m = re.search(r"(\d+)(?!.*\d)", str(name))
        return int(m.group(1)) if m else None

    def _parse_conductor(name):
        """Intentar extraer índice y lado (r/l) de nombres como C1, C2_r, C3-L, c1r"""
        s = str(name).lower()
        m = re.match(r'c\s*([0-9]+)(?:[_\-\s]?([rl]|right|left))?', s)
        if m:
            idx = int(m.group(1))
            side = m.group(2)
            if side:
                side = 'r' if side.startswith('r') else 'l' if side.startswith('l') else None
            return idx, side
        # Fallback: buscar cualquier número al final
        idx = _extract_trailing_index(s)
        return idx, None

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

    # Set 1: guardia (ordenar por índice si existe: HG1, HG2...)
    phase = 1
    def _guard_sort_key(item):
        nombre = item[0]
        idx = _extract_trailing_index(nombre)
        return (idx if idx is not None else 9999, nombre)

    for nombre, coords in sorted(nodos_guardia, key=_guard_sort_key):
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
            'Insul. Wind Area (cm^2)': f"{insul_wind_area:.4f}",
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
        # All conductors in Set 2 — order by conductor index (C1,C2,C3) if available, else by x coordinate
        set_num = 2
        phase = 1

        def _cond_simple_sort(item):
            nombre, coords = item
            idx, _ = _parse_conductor(nombre)
            if idx is not None:
                return (0, idx)
            # fallback: ordenar por Z ascendente (altura de enganche), luego por X
            return (1, coords[2], coords[0], nombre)

        for nombre, coords in sorted(nodos_conductor, key=_cond_simple_sort):
            x, y, z = coords
            insul_type = estructura_data.get('insulator_type_conductor', 'Suspension')
            insul_weight = float(PCADENA) * 10.0  # PCADENA en daN --> N = daN*10
            # Wind area formula (corrección: multiplicar por 10000)
            if 'suspension' in tipo_estructura or 'suspensión' in tipo_estructura:
                insul_wind_area = ((0.5 + Vn / 150.0) * Ka * 0.146) * 10000.0
            else:
                insul_wind_area = ((0.5 + Vn / 75.0) * Ka * 0.146) * 10000.0
            insul_length = Lk
            attach_trans = x
            attach_dist_below = round(altura_max - z, 3)
            attach_long = y
            min_req = "No Uplift" if ('suspension' in tipo_estructura or 'suspensión' in tipo_estructura) else "No Limit"
            # Dead End: sólo No si la estructura es tipo suspension
            dead_end = 'No' if ('suspension' in tipo_estructura or 'suspensión' in tipo_estructura) else 'Yes'

            rows.append({
                'Set #': set_num,
                'Phase #': phase,
                'Dead End Set': dead_end,
                'Set Description': 'COND',
                'Insulator Type': insul_type,
                'Insul. Weight (N)': round(insul_weight, 2),
                'Insul. Wind Area (cm^2)': f"{insul_wind_area:.4f}",
                'Insul. Length (m)': round(insul_length, 3),
                'Attach. Trans. Offset (m)': round(attach_trans, 3),
                'Attach. Dist. Below Top (m)': round(attach_dist_below, 3),
                'Attach. Longit. Offset (m)': round(attach_long, 3),
                'Min. Req. Vertical Load (uplift) (N)': min_req
            })
            phase += 1
    else:
        # Doble terna: queremos orden: c1_r,c2_r,c3_r, c1_l,c2_l,c3_l — usar sufijo si existe, sino usar signo de x
        # Clasificar según lado
        right_nodes = []
        left_nodes = []
        for nombre, coords in nodos_conductor:
            idx, side = _parse_conductor(nombre)
            if side == 'r':
                right_nodes.append((nombre, coords, idx))
            elif side == 'l':
                left_nodes.append((nombre, coords, idx))
            else:
                # fallback según posición x
                if coords[0] >= 0:
                    right_nodes.append((nombre, coords, idx))
                else:
                    left_nodes.append((nombre, coords, idx))

        # Ordenar por índice (si existe) o por X
        def _sort_nodes_by_idx_or_x(item):
            nombre, coords, idx = item
            if idx is not None:
                return (idx, nombre)
            # fallback: ordenar por Z ascendente, luego por X
            return (9999, coords[2], coords[0], nombre)

        right_nodes_sorted = sorted(right_nodes, key=_sort_nodes_by_idx_or_x)
        left_nodes_sorted = sorted(left_nodes, key=_sort_nodes_by_idx_or_x)

        # Set 2 (right)
        phase = 1
        for nombre, coords, _ in right_nodes_sorted:
            x, y, z = coords
            insul_type = estructura_data.get('insulator_type_conductor', 'Suspension')
            insul_weight = float(PCADENA) * 10.0
            if 'suspension' in tipo_estructura or 'suspensión' in tipo_estructura:
                insul_wind_area = ((0.5 + Vn / 150.0) * Ka * 0.146) * 10000.0
            else:
                insul_wind_area = ((0.5 + Vn / 75.0) * Ka * 0.146) * 10000.0
            insul_length = Lk
            attach_trans = x
            attach_dist_below = round(altura_max - z, 3)
            attach_long = y
            min_req = "No Uplift" if ('suspension' in tipo_estructura or 'suspensión' in tipo_estructura) else "No Limit"
            dead_end = 'No' if ('suspension' in tipo_estructura or 'suspensión' in tipo_estructura) else 'Yes'

            rows.append({
                'Set #': 2,
                'Phase #': phase,
                'Dead End Set': dead_end,
                'Set Description': '1TERNA',
                'Insulator Type': insul_type,
                'Insul. Weight (N)': round(insul_weight, 2),
                'Insul. Wind Area (cm^2)': f"{insul_wind_area:.4f}",
                'Insul. Length (m)': round(insul_length, 3),
                'Attach. Trans. Offset (m)': round(attach_trans, 3),
                'Attach. Dist. Below Top (m)': round(attach_dist_below, 3),
                'Attach. Longit. Offset (m)': round(attach_long, 3),
                'Min. Req. Vertical Load (uplift) (N)': min_req
            })
            phase += 1

        # Set 3 (left)
        phase = 1
        for nombre, coords, _ in left_nodes_sorted:
            x, y, z = coords
            insul_type = estructura_data.get('insulator_type_conductor', 'Suspension')
            insul_weight = float(PCADENA) * 10.0
            if 'suspension' in tipo_estructura or 'suspensión' in tipo_estructura:
                insul_wind_area = ((0.5 + Vn / 150.0) * Ka * 0.146) * 10000.0
            else:
                insul_wind_area = ((0.5 + Vn / 75.0) * Ka * 0.146) * 10000.0
            insul_length = Lk
            attach_trans = x
            attach_dist_below = round(altura_max - z, 3)
            attach_long = y
            min_req = "No Uplift" if ('suspension' in tipo_estructura or 'suspensión' in tipo_estructura) else "No Limit"
            dead_end = 'No' if ('suspension' in tipo_estructura or 'suspensión' in tipo_estructura) else 'Yes'

            rows.append({
                'Set #': 3,
                'Phase #': phase,
                'Dead End Set': dead_end,
                'Set Description': '2TERNA',
                'Insulator Type': insul_type,
                'Insul. Weight (N)': round(insul_weight, 2),
                'Insul. Wind Area (cm^2)': f"{insul_wind_area:.4f}",
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
