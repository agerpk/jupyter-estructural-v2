import json
from pathlib import Path

# Factores de conversión
SQIN_TO_MM2 = 645.16  # 1 sq in = 645.16 mm²
IN_TO_MM = 25.4       # 1 in = 25.4 mm
LBS_KFT_TO_DAN_M = 0.001488  # 1 lbs/kft = 0.001488 daN/m
LBS_TO_DAN = 0.4448   # 1 lbs = 0.4448 daN

# Constantes de materiales
E_AL, ALPHA_AL = 6900, 23.0e-6
E_AC, ALPHA_AC = 20000, 11.5e-6

# Cargar archivos
with open('data/cables.json', 'r', encoding='utf-8') as f:
    cables_existentes = json.load(f)

with open('CompararCables/CompararCABLES.json', 'r', encoding='utf-8') as f:
    comparar_cables = json.load(f)

cables_nuevos = cables_existentes.copy()

for nombre, datos in comparar_cables['cables'].items():
    mec = datos['mecanicas']
    elec = datos['electricas']
    
    # Conversiones básicas
    seccion_total_mm2 = float(mec['Seccion_Total_sqin']) * SQIN_TO_MM2
    seccion_al_mm2 = float(mec['Seccion_Al_sqin']) * SQIN_TO_MM2
    diametro_mm = float(mec['Diametro_Exterior_in']) * IN_TO_MM
    peso_dan_m = float(mec['Peso_Total_lbs_kft']) * LBS_KFT_TO_DAN_M
    
    # Resistencia según tipo
    if datos['Tipo'] == 'ACSS' or datos['Tipo'] == 'ACSS/TW':
        resistencia_key = 'Resistencia_MA2_lbs'
    elif 'ACCC' in datos['Tipo']:
        resistencia_key = 'Resistencia_Standard_lbs'
    else:
        resistencia_key = 'Resistencia_GA2_lbs'
    
    carga_rotura_dan = float(mec[resistencia_key]) * LBS_TO_DAN
    
    # Propiedades estimadas
    prop_al = seccion_al_mm2 / seccion_total_mm2
    prop_ac = 1 - prop_al
    modulo_elasticidad = prop_al * E_AL + prop_ac * E_AC
    coef_dilatacion = prop_al * ALPHA_AL + prop_ac * ALPHA_AC
    
    # Material según tipo
    material_map = {
        'ACSR': 'Al/Ac',
        'ACSS': 'Al/Ac',
        'ACSR/TW': 'Al/Ac',
        'ACSS/TW': 'Al/Ac',
        'ACCC/TW': 'Al/Composite'
    }
    
    # Norma según tipo
    norma_map = {
        'ACSR': 'ASTM B232',
        'ACSS': 'ASTM B856',
        'ACSR/TW': 'ASTM B232',
        'ACSS/TW': 'ASTM B856',
        'ACCC/TW': 'ASTM B987'
    }
    
    # Cable compatible con sistema
    cable_compatible = {
        'tipo': datos['Tipo'],
        'material': material_map.get(datos['Tipo'], 'Al/Ac'),
        'seccion_nominal': mec['Tamaño_kcmil'],
        'seccion_total_mm2': round(seccion_total_mm2, 2),
        'diametro_total_mm': round(diametro_mm, 2),
        'peso_unitario_dan_m': round(peso_dan_m, 4),
        'coeficiente_dilatacion_1_c': coef_dilatacion,
        'modulo_elasticidad_dan_mm2': round(modulo_elasticidad, 1),
        'carga_rotura_minima_dan': round(carga_rotura_dan, 1),
        'tension_rotura_minima': round(carga_rotura_dan / seccion_total_mm2, 2),
        'carga_max_trabajo': round(carga_rotura_dan * 0.25, 1),
        'tension_max_trabajo': round(carga_rotura_dan * 0.25 / seccion_total_mm2, 2),
        'norma_fabricacion': norma_map.get(datos['Tipo'], 'ASTM B232'),
        
        # Datos originales extendidos
        'datos_originales': {
            'tipo_original': datos['Tipo'],
            'mecanicas': {
                'tamano_kcmil': float(mec['Tamaño_kcmil']),
                'trenzado_al': mec['Trenzado_Al'],
                'trenzado_acero': mec['Trenzado_Acero'],
                'seccion_total_sqin': float(mec['Seccion_Total_sqin']),
                'seccion_al_sqin': float(mec['Seccion_Al_sqin']),
                'diametro_exterior_in': float(mec['Diametro_Exterior_in']),
                'peso_total_lbs_kft': float(mec['Peso_Total_lbs_kft']),
                'peso_al_lbs_kft': float(mec['Peso_Al_lbs_kft']),
                'peso_acero_lbs_kft': float(mec.get('Peso_Acero_lbs_kft', mec.get('Peso_Core_lbs_kft', 0))),
                'porcentaje_peso_al': float(mec['Porcentaje_Peso_Al_lbs_kft'].replace('%', '')),
                'porcentaje_peso_acero': float(mec.get('Porcentaje_Peso_Acero_lbs_kft', '0%').replace('%', '')),
                resistencia_key.lower(): float(mec[resistencia_key])
            },
            'electricas': {
                'resistencia_dc_20c_ohm_kft': float(elec['Resistencia_DC_20C_ohm_kft']),
                'resistencia_ac_25c_ohm_kft': float(elec['Resistencia_AC_25C_ohm_kft']),
                'resistencia_ac_75c_ohm_kft': float(elec['Resistencia_AC_75C_ohm_kft']),
                'radio_medio_generico_ft': float(elec['Radio_Medio_Generico_ft']),
                'reactancia_industrial_ohm_kft': float(elec['Reactancia_Industrial_ohm_kft']),
                'reactancia_capacitiva_mohm_kft': float(elec['Reactancia_Capacitiva_Mohm_kft'])
            }
        }
    }
    
    # Agregar ampacidades según disponibilidad
    if 'Ampacidad_75C_STD_ohm_kft' in elec:
        cable_compatible['datos_originales']['electricas']['ampacidad_75c_std'] = float(elec['Ampacidad_75C_STD_ohm_kft'])
    elif 'Ampacidad_75C_STD' in elec:
        cable_compatible['datos_originales']['electricas']['ampacidad_75c_std'] = float(elec['Ampacidad_75C_STD'])
    
    if 'Ampacidad_75C_EX3' in elec:
        cable_compatible['datos_originales']['electricas']['ampacidad_75c_ex3'] = float(elec['Ampacidad_75C_EX3'])
    
    # Agregar campos específicos si existen
    if 'Resistencia_AC_200C' in elec:
        cable_compatible['datos_originales']['electricas']['resistencia_ac_200c'] = float(elec['Resistencia_AC_200C'])
    
    if 'Ampacidad_200C_STD' in elec:
        cable_compatible['datos_originales']['electricas']['ampacidad_200c_std'] = float(elec['Ampacidad_200C_STD'])
    
    if 'Ampacidad_200C_EX3' in elec:
        cable_compatible['datos_originales']['electricas']['ampacidad_200c_ex3'] = float(elec['Ampacidad_200C_EX3'])
    
    if 'Ampacidad_180C_STD' in elec:
        cable_compatible['datos_originales']['electricas']['ampacidad_180c_std'] = float(elec['Ampacidad_180C_STD'])
    
    if 'Ampacidad_180C_EX3' in elec:
        cable_compatible['datos_originales']['electricas']['ampacidad_180c_ex3'] = float(elec['Ampacidad_180C_EX3'])
    
    cables_nuevos[nombre] = cable_compatible

# Guardar archivo combinado
with open('data/cables_2.json', 'w', encoding='utf-8') as f:
    json.dump(cables_nuevos, f, indent=2, ensure_ascii=False)

print(f"Convertidos {len(comparar_cables['cables'])} cables nuevos")
print(f"Total cables en cables_2.json: {len(cables_nuevos)}")