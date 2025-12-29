import json
from pathlib import Path

def convertir_cables():
    # Factores de conversión
    SQIN_TO_MM2 = 645.16  # 1 sq in = 645.16 mm²
    IN_TO_MM = 25.4       # 1 in = 25.4 mm
    LBS_KFT_TO_DAN_M = 0.001488  # 1 lbs/kft = 0.001488 daN/m
    LBS_TO_DAN = 0.4448   # 1 lbs = 0.4448 daN
    
    # Constantes de materiales
    E_AL, ALPHA_AL = 6900, 23.0e-6
    E_AC, ALPHA_AC = 20000, 11.5e-6
    
    # Cargar archivos desde directorio local
    script_dir = Path(__file__).parent
    
    with open(script_dir / 'CompararCABLES - Copy.json', 'r', encoding='utf-8') as f:
        comparar_cables = json.load(f)
    
    cables_nuevos = {}
    
    for nombre, datos in comparar_cables['cables'].items():
        mec = datos['mecanicas']
        elec = datos['electricas']
        
        # Conversiones básicas
        seccion_total_mm2 = float(mec['Seccion_Total_sqin']) * SQIN_TO_MM2
        seccion_al_mm2 = float(mec['Seccion_Al_sqin']) * SQIN_TO_MM2
        diametro_mm = float(mec['Diametro_Exterior_in']) * IN_TO_MM
        peso_dan_m = float(mec['Peso_Total_lbs_kft']) * LBS_KFT_TO_DAN_M
        
        # Buscar la resistencia más alta entre todos los campos disponibles
        resistencias_posibles = [
            'Resistencia_MA2_lbs', 'Resistencia_MA3_HS_lbs', 'Resistencia_MA5_UHS_lbs',
            'Resistencia_Standard_lbs', 'Resistencia_ULS_lbs', 'Resistencia_GA2_lbs'
        ]
        
        resistencia_maxima = 0
        resistencia_key_usado = None
        
        for key in resistencias_posibles:
            if key in mec and mec[key]:
                valor = float(mec[key])
                if valor > resistencia_maxima:
                    resistencia_maxima = valor
                    resistencia_key_usado = key
        
        if resistencia_maxima == 0:
            print(f"No se encontro resistencia para {nombre}")
            continue
            
        carga_rotura_dan = resistencia_maxima * LBS_TO_DAN
        print(f"{nombre}: Resistencia maxima {resistencia_maxima} lbs ({resistencia_key_usado}) = {carga_rotura_dan:.1f} daN")
        
        # Propiedades estimadas
        prop_al = seccion_al_mm2 / seccion_total_mm2
        prop_ac = 1 - prop_al
        modulo_elasticidad = prop_al * E_AL + prop_ac * E_AC
        coef_dilatacion = prop_al * ALPHA_AL + prop_ac * ALPHA_AC
        
        # Propiedades del acero (solo si hay acero en el cable)
        seccion_acero_mm2 = None
        modulo_elasticidad_acero_dan_mm2 = None
        coeficiente_dilatacion_acero_1_c = None
        
        if "ACSS" in datos['Tipo'] or "ACSR" in datos['Tipo']:
            # Calcular sección de acero
            seccion_acero_sqin = float(mec['Seccion_Total_sqin']) - float(mec['Seccion_Al_sqin'])
            seccion_acero_mm2 = seccion_acero_sqin * SQIN_TO_MM2
            
            # Propiedades típicas del acero
            modulo_elasticidad_acero_dan_mm2 = E_AC  # 20000 daN/mm²
            coeficiente_dilatacion_acero_1_c = ALPHA_AC  # 11.5e-6 1/°C
        
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
            'seccion_acero_mm2': round(seccion_acero_mm2, 2) if seccion_acero_mm2 is not None else None,
            'diametro_total_mm': round(diametro_mm, 2),
            'peso_unitario_dan_m': round(peso_dan_m, 4),
            'coeficiente_dilatacion_1_c': coef_dilatacion,
            'coeficiente_dilatacion_acero_1_c': coeficiente_dilatacion_acero_1_c,
            'modulo_elasticidad_dan_mm2': round(modulo_elasticidad, 1),
            'modulo_elasticidad_acero_dan_mm2': modulo_elasticidad_acero_dan_mm2,
            'carga_rotura_minima_dan': round(carga_rotura_dan, 1),
            'tension_rotura_minima': round(carga_rotura_dan / seccion_total_mm2, 2),
            'carga_max_trabajo': round(carga_rotura_dan * 0.25, 1),
            'tension_max_trabajo': round(carga_rotura_dan * 0.25 / seccion_total_mm2, 2),
            'norma_fabricacion': norma_map.get(datos['Tipo'], 'ASTM B232'),
            'resistencia_maxima_usada': resistencia_key_usado,
            
            # Datos originales extendidos
            'datos_originales': {
                'tipo_original': datos['Tipo'],
                'mecanicas': {
                    'tamano_kcmil': float(mec['Tamaño_kcmil']),
                    'seccion_total_sqin': float(mec['Seccion_Total_sqin']),
                    'seccion_al_sqin': float(mec['Seccion_Al_sqin']),
                    'diametro_exterior_in': float(mec['Diametro_Exterior_in']),
                    'peso_total_lbs_kft': float(mec['Peso_Total_lbs_kft']),
                    resistencia_key_usado.lower(): resistencia_maxima
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
        
        # Agregar campos específicos según tipo
        if 'Trenzado_Al' in mec:
            cable_compatible['datos_originales']['mecanicas']['trenzado_al'] = mec['Trenzado_Al']
        if 'Trenzado_Acero' in mec:
            cable_compatible['datos_originales']['mecanicas']['trenzado_acero'] = mec['Trenzado_Acero']
        if 'Peso_Al_lbs_kft' in mec:
            cable_compatible['datos_originales']['mecanicas']['peso_al_lbs_kft'] = float(mec['Peso_Al_lbs_kft'])
        if 'Peso_Acero_lbs_kft' in mec:
            cable_compatible['datos_originales']['mecanicas']['peso_acero_lbs_kft'] = float(mec['Peso_Acero_lbs_kft'])
        if 'No_Al_Wires' in mec:
            cable_compatible['datos_originales']['mecanicas']['no_al_wires'] = int(mec['No_Al_Wires'])
        if 'Composite_Core_OD_in' in mec:
            cable_compatible['datos_originales']['mecanicas']['composite_core_od_in'] = float(mec['Composite_Core_OD_in'])
        if 'Peso_Core_lbs_kft' in mec:
            cable_compatible['datos_originales']['mecanicas']['peso_core_lbs_kft'] = float(mec['Peso_Core_lbs_kft'])
        
        # Campos eléctricos específicos
        if 'Ampacidad_75C_STD_ohm_kft' in elec:
            cable_compatible['datos_originales']['electricas']['ampacidad_75c_std'] = float(elec['Ampacidad_75C_STD_ohm_kft'])
        elif 'Ampacidad_75C_STD' in elec:
            cable_compatible['datos_originales']['electricas']['ampacidad_75c_std'] = float(elec['Ampacidad_75C_STD'])
        
        if 'Ampacidad_75C_EX3' in elec:
            cable_compatible['datos_originales']['electricas']['ampacidad_75c_ex3'] = float(elec['Ampacidad_75C_EX3'])
        
        if 'Resistencia_AC_200C' in elec:
            cable_compatible['datos_originales']['electricas']['resistencia_ac_200c'] = float(elec['Resistencia_AC_200C'])
        
        if 'Ampacidad_200C_STD' in elec:
            cable_compatible['datos_originales']['electricas']['ampacidad_200c_std'] = float(elec['Ampacidad_200C_STD'])
        
        if 'Ampacidad_180C_STD' in elec:
            cable_compatible['datos_originales']['electricas']['ampacidad_180c_std'] = float(elec['Ampacidad_180C_STD'])
        
        cables_nuevos[nombre] = cable_compatible
    
    # Guardar archivo en directorio local
    output_file = script_dir / 'cables_convertido_SI.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cables_nuevos, f, indent=2, ensure_ascii=False)
    
    print(f"Convertidos {len(cables_nuevos)} cables")
    print(f"Archivo guardado: {output_file}")
    
    # Mostrar resumen de resistencias usadas
    print("\nResumen de resistencias maximas usadas:")
    for nombre, cable in cables_nuevos.items():
        resistencia_usada = cable.get('resistencia_maxima_usada', 'N/A')
        carga_rotura = cable.get('carga_rotura_minima_dan', 0)
        print(f"  {nombre}: {resistencia_usada} -> {carga_rotura:.0f} daN")

if __name__ == "__main__":
    convertir_cables()