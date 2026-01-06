"""Lógica de cálculo de costeo"""

import pandas as pd
from utils.calculo_cache import CalculoCache

def verificar_cadena_completa_costeo(nombre_estructura, estructura_actual):
    """Verificar si existe cache válido de toda la cadena CMC→DGE→DME→SPH→Fundaciones"""
    
    # Verificar cada componente
    componentes = ['CMC', 'DGE', 'DME', 'SPH', 'FUND']
    metodos_carga = [
        CalculoCache.cargar_calculo_cmc,
        CalculoCache.cargar_calculo_dge,
        CalculoCache.cargar_calculo_dme,
        CalculoCache.cargar_calculo_sph,
        CalculoCache.cargar_calculo_fund
    ]
    
    for componente, metodo_carga in zip(componentes, metodos_carga):
        calculo = metodo_carga(nombre_estructura)
        if not calculo:
            print(f"❌ No hay cache {componente}")
            return None
        vigente, _ = CalculoCache.verificar_vigencia(calculo, estructura_actual)
        if not vigente:
            print(f"❌ Cache {componente} no vigente")
            return None
    
    print("✅ Toda la cadena CMC→DGE→DME→SPH→Fundaciones tiene cache válido")
    return True

def ejecutar_cadena_completa_costeo(nombre_estructura, estructura_actual):
    """Ejecutar cadena completa CMC→DGE→DME→SPH→Fundaciones si no hay cache completo"""
    try:
        print(f"🔄 Ejecutando cadena completa para costeo: {nombre_estructura}")
        
        from controllers.geometria_controller import ejecutar_calculo_cmc_automatico, ejecutar_calculo_dge
        from controllers.ejecutar_calculos import ejecutar_calculo_dme, ejecutar_calculo_sph
        from controllers.fundacion_controller import ejecutar_cadena_completa
        from models.app_state import AppState
        
        state = AppState()
        
        # Ejecutar cadena completa hasta SPH
        resultado_sph = ejecutar_cadena_completa(nombre_estructura, estructura_actual)
        if not resultado_sph:
            print("❌ Error ejecutando cadena hasta SPH")
            return False
        
        # Ejecutar Fundaciones (requiere SPH completo)
        # Por ahora asumimos que fundaciones ya está calculado o se puede calcular
        calculo_fund = CalculoCache.cargar_calculo_fund(nombre_estructura)
        if not calculo_fund:
            print("⚠️ No hay cache de fundaciones, se requiere cálculo manual")
            return False
        
        print("✅ Cadena completa ejecutada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando cadena completa: {e}")
        return False

def extraer_datos_para_costeo(nombre_estructura):
    """Extraer datos necesarios desde cache SPH, DGE y Fundaciones"""
    
    # Cargar datos desde SPH
    calculo_sph = CalculoCache.cargar_calculo_sph(nombre_estructura)
    if not calculo_sph:
        raise ValueError("No hay cache SPH disponible")
    
    resultados_sph = calculo_sph.get('resultados', {})
    
    # Cargar datos desde DGE para accesorios
    calculo_dge = CalculoCache.cargar_calculo_dge(nombre_estructura)
    if not calculo_dge:
        raise ValueError("No hay cache DGE disponible")
    
    resultados_dge = calculo_dge.get('resultados', {})
    
    # Cargar datos desde Fundaciones
    calculo_fund = CalculoCache.cargar_calculo_fund(nombre_estructura)
    if not calculo_fund:
        raise ValueError("No hay cache Fundaciones disponible")
    
    resultados_fund = calculo_fund.get('resultados', {})
    
    # Extraer datos obligatorios de SPH
    n_postes = resultados_sph.get('config_seleccionada')
    if n_postes == 'Monoposte':
        n_postes = 1
    elif n_postes in ['Biposte_TRANSVERSAL', 'Biposte_LONGITUDINAL']:
        n_postes = 2
    elif n_postes == 'Triposte':
        n_postes = 3
    else:
        raise ValueError(f"Configuración SPH no reconocida: {n_postes}")
    
    dimensiones = resultados_sph.get('dimensiones', {})
    longitud_total_m = dimensiones.get('Ht_comercial')
    if longitud_total_m is None:
        raise ValueError("SPH no contiene Ht_comercial en dimensiones")
    
    # Extraer resistencia adoptada (Rc_adopt)
    resistencia_dan = resultados_sph.get('Rc_adopt')
    if resistencia_dan is None:
        raise ValueError("SPH no contiene Rc_adopt")
    
    # Extraer cantidades de vínculos desde SPH desarrollo_texto
    desarrollo = calculo_sph.get('desarrollo_texto', '')
    cantidad_vinculos = 0
    for linea in desarrollo.split('\n'):
        if 'vínculos' in linea.lower() or 'vinculos' in linea.lower():
            if 'No requiere vínculos' in linea:
                cantidad_vinculos = 0
                break
            else:
                # Buscar números en la línea de vínculos
                import re
                numeros = re.findall(r'\d+', linea)
                if numeros:
                    cantidad_vinculos = int(numeros[0])
                    break
    
    # Extraer cantidades de crucetas y ménsulas desde DGE por altura
    cantidad_crucetas = 0
    cantidad_mensulas = 0
    
    print(f"🔍 DEBUG: Cache DGE completo: {list(calculo_dge.keys())}")
    
    # Buscar conexiones y dimensiones directamente en el cache DGE
    if 'conexiones' in calculo_dge and 'nodes_key' in calculo_dge:
        conexiones = calculo_dge['conexiones']
        nodes_key = calculo_dge['nodes_key']
        
        print(f"🔍 DEBUG: Analizando {len(conexiones)} conexiones y {len(nodes_key)} nodos")
        
        # Agrupar alturas por tipo, crucetas tienen prioridad
        alturas_crucetas = set()
        alturas_mensulas = set()
        
        # Primero identificar todas las alturas con crucetas
        for conexion in conexiones:
            if len(conexion) >= 3 and conexion[2] == 'cruceta':
                nodo_origen = conexion[0]
                if nodo_origen in nodes_key:
                    altura = round(nodes_key[nodo_origen][2], 3)
                    alturas_crucetas.add(altura)
                    print(f"🔧 Cruceta encontrada en altura {altura}m (nodo {nodo_origen})")
        
        # Luego identificar alturas con ménsulas, excluyendo las que ya tienen crucetas
        for conexion in conexiones:
            if len(conexion) >= 3 and conexion[2] == 'mensula':
                nodo_origen = conexion[0]
                if nodo_origen in nodes_key:
                    altura = round(nodes_key[nodo_origen][2], 3)
                    if altura not in alturas_crucetas:
                        alturas_mensulas.add(altura)
                        print(f"🔗 Ménsula encontrada en altura {altura}m (nodo {nodo_origen})")
        
        cantidad_crucetas = len(alturas_crucetas)
        cantidad_mensulas = len(alturas_mensulas)
        
    elif 'dimensiones' in calculo_dge:
        dimensiones = calculo_dge['dimensiones']
        print(f"📐 Dimensiones disponibles: {list(dimensiones.keys())}")
        
        # Contar alturas únicas de amarre (h1a, h2a, h3a)
        alturas_amarre = set()
        for key in ['h1a', 'h2a', 'h3a']:
            if key in dimensiones:
                altura = round(dimensiones[key], 3)
                alturas_amarre.add(altura)
        
        cantidad_crucetas = len(alturas_amarre)
        
        # Ménsula de guardia si existe hhg
        if 'hhg' in dimensiones:
            altura_hg = round(dimensiones['hhg'], 3)
            if altura_hg not in alturas_amarre:
                cantidad_mensulas = 1
        
        print(f"📐 Desde dimensiones: {cantidad_crucetas} crucetas, {cantidad_mensulas} ménsulas")
    
    # Validar que se encontraron accesorios
    if cantidad_crucetas == 0 and cantidad_mensulas == 0:
        print(f"❌ ERROR: No se encontraron crucetas ni ménsulas en DGE")
        raise ValueError("No se pudieron extraer cantidades de accesorios desde DGE")
    
    # Extraer volumen de hormigón desde fundaciones
    if 'dataframe_html' not in resultados_fund:
        raise ValueError("Fundaciones no contiene dataframe_html")
    
    try:
        from io import StringIO
        df_fund = pd.read_json(StringIO(resultados_fund['dataframe_html']), orient='split')
        
        # Buscar volumen máximo (hipótesis dimensionante)
        vol_cols = [col for col in df_fund.columns if 'volumen' in col.lower() or 'v_' in col.lower()]
        if not vol_cols:
            raise ValueError("No se encontró columna de volumen en fundaciones")
        
        if len(df_fund) == 0:
            raise ValueError("DataFrame de fundaciones está vacío")
        
        # Usar el volumen máximo (hipótesis dimensionante)
        volumen_hormigon_m3 = df_fund[vol_cols[0]].max()
        
    except Exception as e:
        raise ValueError(f"Error extrayendo volumen de fundaciones: {e}")
    
    datos = {
        'n_postes': n_postes,
        'longitud_total_m': longitud_total_m,
        'resistencia_dan': resistencia_dan,
        'cantidad_crucetas': cantidad_crucetas,
        'cantidad_mensulas': cantidad_mensulas,
        'cantidad_vinculos': cantidad_vinculos,
        'volumen_hormigon_m3': volumen_hormigon_m3
    }
    
    print(f"✅ Datos extraídos: {datos}")
    return datos

def calcular_costeo_completo(datos_estructura, parametros_precios, tension_kv=220):
    """Aplicar fórmulas de costeo y generar resultados completos
    
    Fórmula Postes: Costo = A × Longitud_m + B × Resistencia_daN + C
    """
    
    # Extraer parámetros
    postes = parametros_precios.get('postes', {})
    accesorios = parametros_precios.get('accesorios', {})
    fundaciones = parametros_precios.get('fundaciones', {})
    montaje = parametros_precios.get('montaje', {})
    adicional = parametros_precios.get('adicional_estructura', 0)
    
    # 1. Costo Postes (coeficientes interpolados R²=0.989)
    coef_a = postes.get('coef_a', 127.384729)
    coef_b = postes.get('coef_b', 1.543826)
    coef_c = postes.get('coef_c', -631.847156)
    
    costo_unitario_poste = coef_a * datos_estructura['longitud_total_m'] + coef_b * datos_estructura['resistencia_dan'] + coef_c
    costo_postes = datos_estructura['n_postes'] * costo_unitario_poste
    
    # 2. Costo Accesorios - precios únicos sin diferenciación por tensión
    precio_cruceta = accesorios.get('crucetas', 580.0)
    precio_mensula = accesorios.get('mensulas', 320.0)
    precio_vinculo = accesorios.get('vinculos', 320.0)
    
    costo_crucetas = datos_estructura['cantidad_crucetas'] * precio_cruceta
    costo_mensulas = datos_estructura['cantidad_mensulas'] * precio_mensula
    costo_vinculos = datos_estructura['cantidad_vinculos'] * precio_vinculo
    costo_accesorios = costo_crucetas + costo_mensulas + costo_vinculos
    
    # 3. Costo Fundaciones
    precio_m3 = fundaciones.get('precio_m3_hormigon', 250.0)
    factor_hierro = fundaciones.get('factor_hierro', 1.2)
    costo_fundaciones = datos_estructura['volumen_hormigon_m3'] * precio_m3 * factor_hierro
    
    # 4. Costo Montaje
    precio_estructura = montaje.get('precio_por_estructura', 5000.0)
    factor_terreno = montaje.get('factor_terreno', 1.0)
    costo_montaje = precio_estructura * factor_terreno
    
    # 5. Costo Total
    costo_total = costo_postes + costo_accesorios + costo_fundaciones + costo_montaje + adicional
    
    # Crear tabla detallada
    tabla_datos = [
        ['Postes', datos_estructura['n_postes'], f'{costo_unitario_poste:.0f}', f'{costo_postes:.0f}'],
        ['Crucetas', datos_estructura['cantidad_crucetas'], f'{precio_cruceta:.0f}', f'{costo_crucetas:.0f}'],
        ['Ménsulas', datos_estructura['cantidad_mensulas'], f'{precio_mensula:.0f}', f'{costo_mensulas:.0f}'],
        ['Vínculos', datos_estructura['cantidad_vinculos'], f'{precio_vinculo:.0f}', f'{costo_vinculos:.0f}'],
        ['Fundaciones', f"{datos_estructura['volumen_hormigon_m3']:.2f} m³", f'{precio_m3 * factor_hierro:.0f}', f'{costo_fundaciones:.0f}'],
        ['Montaje y Logística', '1', f'{precio_estructura * factor_terreno:.0f}', f'{costo_montaje:.0f}'],
        ['Adicional Estructura', '1', f'{adicional:.0f}', f'{adicional:.0f}']
    ]
    
    df_costos = pd.DataFrame(tabla_datos, columns=['Elemento', 'Cantidad', 'Precio Unitario [UM]', 'Costo Total [UM]'])
    
    # Agregar fila de total
    df_total = pd.DataFrame([['TOTAL', '', '', f'{costo_total:.0f}']], columns=df_costos.columns)
    df_costos = pd.concat([df_costos, df_total], ignore_index=True)
    
    # Resumen
    resumen_costos = {
        'costo_postes': costo_postes,
        'costo_accesorios': costo_accesorios,
        'costo_fundaciones': costo_fundaciones,
        'costo_montaje': costo_montaje,
        'costo_adicional': adicional,
        'costo_total': costo_total
    }
    
    resultados = {
        'tabla_costos': df_costos.to_json(orient='split'),
        'resumen_costos': resumen_costos,
        'datos_estructura': datos_estructura,
        'parametros_precios': parametros_precios
    }
    
    print(f"✅ Costeo calculado - Total: {costo_total:,.0f} UM")
    return resultados