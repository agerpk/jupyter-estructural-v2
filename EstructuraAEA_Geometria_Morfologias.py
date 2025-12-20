"""
Definiciones de morfologías para estructuras eléctricas.
Contiene nodos, conexiones y coordenadas por morfología.
Usa parámetros calculados de EstructuraAEA_Geometria (D_fases, s_estructura, etc.)
"""

import math
from NodoEstructural import NodoEstructural

def crear_nodos_morfologia(morfologia: str, parametros: dict):
    """
    Crea nodos y conexiones según morfología usando parámetros calculados.
    
    Args:
        morfologia: String de morfología (ej: "DOBLE-TRIANGULAR-2HG")
        parametros: Dict con parámetros calculados (D_fases, s_estructura, k, Ka, etc.)
    
    Returns:
        tuple: (nodos_dict, conexiones_list)
    """
    # Morfologías especiales con sufijo AT (Antigua Topología)
    if morfologia.endswith("-AT"):
        return _crear_morfologia_at(morfologia, parametros)
    
    # Morfologías estándar con conexiones específicas
    if morfologia == "SIMPLE-VERTICAL-1HG":
        return _crear_simple_vertical_1hg(parametros)
    elif morfologia == "SIMPLE-TRIANGULAR-NOHG":
        return _crear_simple_triangular_nohg(parametros)
    elif morfologia == "SIMPLE-TRIANGULAR-1HG-DEFASADO":
        return _crear_simple_triangular_1hg_defasado(parametros)
    elif morfologia == "SIMPLE-HORIZONTAL-NOHG":
        return _crear_simple_horizontal_nohg(parametros)
    elif morfologia == "SIMPLE-HORIZONTAL-1HG":
        return _crear_simple_horizontal_1hg(parametros)
    elif morfologia == "SIMPLE-HORIZONTAL-2HG":
        return _crear_simple_horizontal_2hg_at(parametros)  # Usar AT por defecto
    elif morfologia == "DOBLE-VERTICAL-NOHG":
        return _crear_doble_vertical_nohg(parametros)
    elif morfologia == "DOBLE-VERTICAL-1HG":
        return _crear_doble_vertical_1hg(parametros)
    elif morfologia == "DOBLE-VERTICAL-2HG":
        return _crear_doble_vertical_2hg(parametros)
    elif morfologia == "DOBLE-TRIANGULAR-NOHG":
        return _crear_doble_triangular_nohg(parametros)
    elif morfologia == "DOBLE-TRIANGULAR-1HG":
        return _crear_doble_triangular_1hg(parametros)
    elif morfologia == "DOBLE-TRIANGULAR-2HG":
        return _crear_doble_triangular_2hg(parametros)
    else:
        raise ValueError(f"Morfología no implementada: {morfologia}")

def _calcular_altura_total_con_guardia(h1a, h2a, h3a, hhg):
    """Calcula altura total incluyendo guardia si existe"""
    return max(h1a, h2a, h3a, hhg) if hhg > 0 else max(h1a, h2a, h3a)

def _eliminar_top_superpuesto(nodos):
    """Elimina nodo TOP si está superpuesto con otro nodo"""
    if "TOP" not in nodos:
        return nodos
    
    top_coords = nodos["TOP"].coordenadas
    
    for nombre, nodo in nodos.items():
        if nombre != "TOP" and nodo.coordenadas == top_coords:
            # TOP superpuesto con otro nodo, eliminarlo
            del nodos["TOP"]
            break
    
    return nodos

def _crear_nodo_estructural_completo(nombre, coordenadas, tipo, params):
    """Crea NodoEstructural con parámetros completos"""
    cable = None
    if tipo == "conductor":
        cable = params.get('cable_conductor')
    elif tipo == "guardia":
        # Para 2HG: HG1 usa cable_guardia1, HG2 usa cable_guardia2
        if nombre == "HG1":
            cable = params.get('cable_guardia1') or params.get('cable_guardia')
        elif nombre == "HG2":
            cable = params.get('cable_guardia2') or params.get('cable_guardia')
        else:
            cable = params.get('cable_guardia')
    
    alpha_quiebre = params.get('alpha_quiebre', 0.0)
    tipo_fijacion = params.get('tipo_fijacion_base', 'suspensión')
    rotacion_eje_z = params.get('rotacion_eje_z', 0.0)  # Para rotación de cables
    
    return NodoEstructural(
        nombre, coordenadas, tipo, cable, alpha_quiebre, tipo_fijacion, 
        rotacion_eje_z, False, []  # es_editado=False, conectado_a=[]
    )

def _calcular_posicion_conductor_mas_alto(h1a, h2a, h3a, lmen, disposicion, terna, s_estructura, D_fases, theta_max, lk, ancho_cruceta):
    """Calcula la posición del conductor más alto (pcma) - LÓGICA LEGACY"""
    if disposicion == "vertical" and h3a > h2a:
        y = h3a - lk
        x = lmen
    elif disposicion == "triangular" and h2a > h1a:
        y = h2a - lk
        x = lmen
    elif disposicion == "horizontal":
        y = h1a - lk
        # Lógica compleja del legacy
        dist_columna_x = max(lk * math.sin(math.radians(theta_max)) + s_estructura, D_fases / 2)
        dist_conductor_x = dist_columna_x + lk * math.sin(math.radians(theta_max)) + s_estructura + ancho_cruceta/2
        dist_conductor_final = max(D_fases, dist_conductor_x)
        x = dist_conductor_final
    else:
        y = h1a - lk
        x = lmen
    
    return (x, y)

def _calcular_cable_guardia(pcma, D_fases, Dhg, cant_hg, hg_centrado, ang_apantallamiento, hadd_hg, long_mensula_min_guardia):
    """Calcula las posiciones de los cables de guardia - LÓGICA LEGACY"""
    x_pcma, y_pcma = pcma
    ang_rad = math.radians(ang_apantallamiento)
    
    if cant_hg == 0:
        return 0.0, 0.0, (0.0, 0.0), (0.0, 0.0)
    
    # Si hay 1 cable guardia centrado
    if cant_hg == 1 and hg_centrado:
        hhg = x_pcma / math.tan(ang_rad) + y_pcma
        lmenhg = 0.0
        phg1 = (0.0, hhg)
        phg2 = (0.0, 0.0)
        return hhg, lmenhg, phg1, phg2
    
    # Si hay 1 cable guardia NO centrado
    elif cant_hg == 1 and not hg_centrado:
        dvhg = Dhg * math.cos(ang_rad) + hadd_hg
        hhg = y_pcma + dvhg
        term = (dvhg / math.cos(ang_rad)) * math.sin(ang_rad)
        lmenhg_base = x_pcma - term
        lmenhg = max(lmenhg_base, long_mensula_min_guardia)
        phg1 = (lmenhg, hhg)
        phg2 = (0.0, 0.0)
        return hhg, lmenhg, phg1, phg2
    
    # Si hay 2 cables guardia
    elif cant_hg == 2:
        dvhg = Dhg * math.cos(ang_rad) + hadd_hg
        hhg = y_pcma + dvhg
        lmenhg_base = x_pcma - Dhg * math.sin(ang_rad)
        lmenhg = max(lmenhg_base, long_mensula_min_guardia)
        phg1 = (lmenhg, hhg)
        phg2 = (-lmenhg, hhg)
        return hhg, lmenhg, phg1, phg2
    
    else:
        return 0.0, 0.0, (0.0, 0.0), (0.0, 0.0)
    
def _aplicar_ajuste_iterativo_lmenhg(hhg, lmenhg, phg1, phg2, params):
    """Aplica ajuste iterativo de lmenhg si AUTOAJUSTAR_LMENHG=True
    
    Implementa la lógica legacy que ajusta hhg iterativamente para mantener
    el ángulo de apantallamiento cuando Lk > 0.
    """
    autoajustar = params.get('AUTOAJUSTAR_LMENHG', False)
    if not autoajustar:
        return hhg, lmenhg, phg1, phg2
    
    # Parámetros para el ajuste iterativo
    lk = params.get('lk', 0.0)
    ang_apantallamiento = params.get('ang_apantallamiento', 30.0)
    cant_hg = params.get('cant_hg', 0)
    
    if lk <= 0 or cant_hg == 0:
        return hhg, lmenhg, phg1, phg2
    
    # Obtener posición del conductor más alto considerando Lk
    pcma_x, pcma_y = params.get('pcma_x', phg1[0]), params.get('pcma_y', hhg - 2.0)
    
    # Posición real del conductor (restando Lk)
    conductor_real_y = pcma_y - lk
    conductor_real_x = pcma_x
    
    # Calcular hhg necesario para mantener ángulo de apantallamiento
    ang_rad = math.radians(ang_apantallamiento)
    
    # Ajuste iterativo: incrementar/decrementar hhg de a 0.01m hasta lograr apantallamiento
    hhg_ajustado = hhg
    max_iteraciones = 1000  # Límite de seguridad
    paso = 0.01  # Incremento de 0.01m como en legacy
    
    for i in range(max_iteraciones):
        # Calcular ángulo actual desde HG1 al conductor real
        if cant_hg >= 1:
            hg_x, hg_y = phg1[0], hhg_ajustado
            
            # Distancia horizontal y vertical desde guardia a conductor
            dx = abs(conductor_real_x - hg_x)
            dy = hg_y - conductor_real_y
            
            if dx > 0 and dy > 0:
                angulo_actual = math.degrees(math.atan(dx / dy))
                
                # Si el ángulo es menor al requerido, subir HG
                if angulo_actual > ang_apantallamiento:
                    hhg_ajustado += paso
                    # Recalcular posiciones de guardia
                    if cant_hg == 1:
                        phg1 = (phg1[0], hhg_ajustado)
                    else:
                        phg1 = (phg1[0], hhg_ajustado)
                        phg2 = (phg2[0], hhg_ajustado)
                # Si el ángulo es mayor, bajar HG (pero no menos que conductor + margen)
                elif angulo_actual < ang_apantallamiento - 0.5:  # Tolerancia de 0.5°
                    if hhg_ajustado > conductor_real_y + 1.0:  # Margen mínimo 1m
                        hhg_ajustado -= paso
                        if cant_hg == 1:
                            phg1 = (phg1[0], hhg_ajustado)
                        else:
                            phg1 = (phg1[0], hhg_ajustado)
                            phg2 = (phg2[0], hhg_ajustado)
                    else:
                        break  # No bajar más
                else:
                    # Ángulo dentro de tolerancia
                    break
            else:
                break
    
    print(f"🔧 AJUSTE ITERATIVO: hhg {hhg:.3f}m → {hhg_ajustado:.3f}m (Lk={lk}m, ang={ang_apantallamiento}°)")
    
    return hhg_ajustado, lmenhg, phg1, phg2

def _actualizar_dimensiones_morfologia(params, hhg, lmenhg, phg1, phg2, pcma, lmen2c=None):
    """Actualiza dimensiones y variables auxiliares como en legacy"""
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    
    # Actualizar dimensiones similares al legacy
    dimensiones_actualizadas = {
        "h1a": h1a, "h2a": h2a, "h3a": h3a, "hhg": hhg,
        "lmen": params['lmen'], "lmenhg": lmenhg,
        "pcma_x": pcma[0], "pcma_y": pcma[1],
        "phg1_x": phg1[0], "phg1_y": phg1[1],
        "phg2_x": phg2[0], "phg2_y": phg2[1],
        "altura_total": _calcular_altura_total_con_guardia(h1a, h2a, h3a, hhg)
    }
    
    if lmen2c is not None:
        dimensiones_actualizadas["lmen2c"] = lmen2c
    
    return dimensiones_actualizadas

def _crear_morfologia_at(morfologia: str, params):
    """Morfologías AT (Antigua Topología) con nodos Y - Lógica especial preservada"""
    if morfologia == "SIMPLE-HORIZONTAL-2HG-AT":
        return _crear_simple_horizontal_2hg_at(params)
    else:
        raise ValueError(f"Morfología AT no implementada: {morfologia}")

def _crear_simple_horizontal_2hg_at(params):
    """Simple horizontal con 2 HG - Topología AT con nodos Y (PRESERVADA)"""
    nodos = {}
    
    h1a = params['h1a']
    s_estructura = params['s_estructura']
    D_fases = params['D_fases']
    theta_max = params.get('theta_max', 0)
    lk = params.get('lk', 2.5)
    ancho_cruceta = params.get('ancho_cruceta', 0.3)
    ang_apantallamiento = params.get('ang_apantallamiento', 30.0)
    Dhg = params.get('Dhg', 1.0)
    hadd_hg = params.get('hadd_hg', 0.0)
    long_mensula_min_guardia = params.get('long_mensula_min_guardia', 0.2)
    
    # Calcular pcma y guardia (LÓGICA LEGACY)
    pcma = _calcular_posicion_conductor_mas_alto(h1a, h1a, h1a, 0, "horizontal", "Simple", s_estructura, D_fases, theta_max, lk, ancho_cruceta)
    hhg, lmenhg, phg1, phg2 = _calcular_cable_guardia(pcma, D_fases, Dhg, 2, False, ang_apantallamiento, hadd_hg, long_mensula_min_guardia)
    
    # Calcular distancias para horizontal
    dist_columna_x = max(lk * math.sin(math.radians(theta_max)) + s_estructura, D_fases / 2)
    dist_conductor_x = dist_columna_x + lk * math.sin(math.radians(theta_max)) + s_estructura + ancho_cruceta/2
    dist_conductor_final = max(D_fases, dist_conductor_x)
    
    # Nodos estructura (TOPOLOGÍA AT PRESERVADA)
    nodos["BASE"] = NodoEstructural("BASE", (0.0, 0.0, 0.0), "base")
    nodos["V"] = NodoEstructural("V", (0.0, 0.0, hhg * 2/3), "viento")
    nodos["Y1"] = NodoEstructural("Y1", (0.0, 0.0, h1a - 2*lk), "general")
    nodos["Y2"] = NodoEstructural("Y2", (-dist_columna_x, 0.0, h1a - lk), "general")
    nodos["Y3"] = NodoEstructural("Y3", (dist_columna_x, 0.0, h1a - lk), "general")
    nodos["Y4"] = NodoEstructural("Y4", (-dist_columna_x, 0.0, h1a), "general")
    nodos["Y5"] = NodoEstructural("Y5", (dist_columna_x, 0.0, h1a), "general")
    nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, hhg), "general")
    
    # Nodos conductor
    nodos["C1"] = NodoEstructural("C1", (-dist_conductor_final, 0.0, h1a), "conductor")
    nodos["C2"] = NodoEstructural("C2", (0.0, 0.0, h1a), "conductor")
    nodos["C3"] = NodoEstructural("C3", (dist_conductor_final, 0.0, h1a), "conductor")
    
    # Nodos guardia (2 HG) - usar posiciones calculadas
    nodos["HG1"] = NodoEstructural("HG1", (phg1[0], 0.0, phg1[1]), "guardia")
    nodos["HG2"] = NodoEstructural("HG2", (phg2[0], 0.0, phg2[1]), "guardia")
    
    # Conexiones AT (LÓGICA ORIGINAL PRESERVADA)
    conexiones = [
        ("BASE", "V", "columna"),
        ("V", "Y1", "columna"),
        ("Y1", "Y2", "mensula"),
        ("Y1", "Y3", "mensula"),
        ("Y2", "Y4", "columna"),
        ("Y3", "Y5", "columna"),
        ("Y1", "TOP", "columna"),
        ("Y4", "C1", "mensula"),
        ("Y1", "C2", "mensula"),
        ("Y5", "C3", "mensula"),
        ("TOP", "HG1", "mensula"),
        ("TOP", "HG2", "mensula")
    ]
    
    return nodos, conexiones

def _generar_conexiones_estandar(nodos, params):
    """Genera conexiones usando nueva lógica estándar"""
    conexiones = []
    
    # Obtener alturas para determinar altura total
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmenhg = params.get('lmenhg', 0)
    # Calcular hhg aproximado si existe TOP
    hhg = 0
    if "TOP" in nodos:
        hhg = nodos["TOP"].coordenadas[2]
    elif lmenhg > 0:
        hhg = max(h1a, h2a, h3a) + 1.0 + lmenhg
    altura_total = max(h1a, h2a, h3a, hhg)
    
    # 1. BASE → V (nodo viento a 2/3 altura total)
    if "BASE" in nodos and "V" in nodos:
        conexiones.append(("BASE", "V", "columna"))
    
    # 2. V → CROSS (todos los nodos CROSS)
    cross_nodes = [n for n in nodos.keys() if n.startswith("CROSS_")]
    cross_nodes.sort()  # Ordenar por nombre
    
    if "V" in nodos and cross_nodes:
        # Conectar V al primer CROSS
        conexiones.append(("V", cross_nodes[0], "columna"))
        
        # Conectar CROSS entre sí (columna)
        for i in range(len(cross_nodes) - 1):
            conexiones.append((cross_nodes[i], cross_nodes[i+1], "columna"))
        
        # Conectar último CROSS → TOP (si existe)
        if "TOP" in nodos:
            conexiones.append((cross_nodes[-1], "TOP", "columna"))
    
    # 3. CROSS → Cables (conductores y guardias)
    for cross in cross_nodes:
        cross_z = nodos[cross].coordenadas[2]
        cables_en_altura = []
        
        # Buscar cables a misma altura que este CROSS
        for nombre, nodo in nodos.items():
            if (nodo.tipo_nodo in ["conductor", "guardia"] and 
                abs(nodo.coordenadas[2] - cross_z) < 0.1):  # Tolerancia 0.1m
                cables_en_altura.append(nombre)
        
        if len(cables_en_altura) == 1:
            # Un solo cable → MENSULA
            conexiones.append((cross, cables_en_altura[0], "mensula"))
        elif len(cables_en_altura) > 1:
            # Múltiples cables → CRUCETA entre ellos, MENSULA al primero
            cables_en_altura.sort()
            conexiones.append((cross, cables_en_altura[0], "mensula"))
            for i in range(len(cables_en_altura) - 1):
                conexiones.append((cables_en_altura[i], cables_en_altura[i+1], "cruceta"))
    
    # 4. TOP → Guardias (si no están conectadas por CROSS)
    if "TOP" in nodos:
        top_z = nodos["TOP"].coordenadas[2]
        guardias_en_top = []
        
        for nombre, nodo in nodos.items():
            if (nodo.tipo_nodo == "guardia" and 
                abs(nodo.coordenadas[2] - top_z) < 0.1):
                guardias_en_top.append(nombre)
        
        for guardia in guardias_en_top:
            # Verificar que no esté ya conectada por un CROSS
            ya_conectada = any(conn[1] == guardia and conn[0].startswith("CROSS") 
                             for conn in conexiones)
            if not ya_conectada:
                conexiones.append(("TOP", guardia, "mensula"))
    
    return conexiones
    """Simple vertical con 1 HG - Usa lógica de EstructuraAEA_Geometria existente"""
    nodos = {}
    
    # Extraer parámetros calculados
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    s_estructura = params['s_estructura']
    lmenhg = params['lmenhg']
    
    # Nodos estructura
    nodos["BASE"] = NodoEstructural("BASE", (0.0, 0.0, 0.0), "base")
    nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")
    nodos["CROSS_H2"] = NodoEstructural("CROSS_H2", (0.0, 0.0, h2a), "cruce")
    nodos["CROSS_H3"] = NodoEstructural("CROSS_H3", (0.0, 0.0, h3a), "cruce")
    nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, h3a + 1.0 + lmenhg), "general")
    
    # Nodos conductor
    nodos["C1_L"] = NodoEstructural("C1_L", (-s_estructura, 0.0, h1a), "conductor")
    nodos["C2_L"] = NodoEstructural("C2_L", (-s_estructura, 0.0, h2a), "conductor")
    nodos["C3_L"] = NodoEstructural("C3_L", (-s_estructura, 0.0, h3a), "conductor")
    
    # Nodos guardia
    nodos["HG1"] = NodoEstructural("HG1", (-lmenhg, 0.0, h3a + 1.0 + lmenhg), "guardia")
    
    # Conexiones naturales
    conexiones = [
        ("BASE", "CROSS_H1", "columna"),
        ("CROSS_H1", "CROSS_H2", "columna"),
        ("CROSS_H2", "CROSS_H3", "columna"),
        ("CROSS_H3", "TOP", "columna"),
        ("CROSS_H1", "C1_L", "mensula"),
        ("CROSS_H2", "C2_L", "mensula"),
        ("CROSS_H3", "C3_L", "mensula"),
        ("TOP", "HG1", "mensula")
    ]
    
def _crear_simple_vertical_1hg(params):
    """Simple vertical con 1 HG - LÓGICA LEGACY"""
    nodos = {}
    
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmen = params['lmen']
    D_fases = params['D_fases']
    Dhg = params.get('Dhg', 1.0)
    ang_apantallamiento = params.get('ang_apantallamiento', 30.0)
    hadd_hg = params.get('hadd_hg', 0.0)
    long_mensula_min_guardia = params.get('long_mensula_min_guardia', 0.2)
    
    # Calcular pcma y guardia (LÓGICA LEGACY)
    pcma = _calcular_posicion_conductor_mas_alto(h1a, h2a, h3a, lmen, "vertical", "Simple", 0, D_fases, 0, 0, 0)
    hhg, lmenhg, phg1, phg2 = _calcular_cable_guardia(pcma, D_fases, Dhg, 1, False, ang_apantallamiento, hadd_hg, long_mensula_min_guardia)
    
    altura_total = _calcular_altura_total_con_guardia(h1a, h2a, h3a, hhg)
    
    # Nodos estructura
    nodos["BASE"] = _crear_nodo_estructural_completo("BASE", (0.0, 0.0, 0.0), "base", params)
    nodos["V"] = _crear_nodo_estructural_completo("V", (0.0, 0.0, altura_total * 2/3), "viento", params)
    nodos["CROSS_H1"] = _crear_nodo_estructural_completo("CROSS_H1", (0.0, 0.0, h1a), "cruce", params)
    if h2a > h1a:
        nodos["CROSS_H2"] = _crear_nodo_estructural_completo("CROSS_H2", (0.0, 0.0, h2a), "cruce", params)
    if h3a > h2a:
        nodos["CROSS_H3"] = _crear_nodo_estructural_completo("CROSS_H3", (0.0, 0.0, h3a), "cruce", params)
    nodos["TOP"] = _crear_nodo_estructural_completo("TOP", (0.0, 0.0, hhg), "general", params)
    
    # Nodos conductor - LÓGICA LEGACY
    nodos["C1_L"] = _crear_nodo_estructural_completo("C1_L", (lmen, 0.0, h1a), "conductor", params)
    nodos["C2_L"] = _crear_nodo_estructural_completo("C2_L", (lmen, 0.0, h2a), "conductor", params)
    nodos["C3_L"] = _crear_nodo_estructural_completo("C3_L", (lmen, 0.0, h3a), "conductor", params)
    
    # Nodos guardia - usar posición calculada
    nodos["HG1"] = _crear_nodo_estructural_completo("HG1", (phg1[0], 0.0, phg1[1]), "guardia", params)
    
    # Eliminar TOP si está superpuesto
    nodos = _eliminar_top_superpuesto(nodos)
    
    # Conexiones específicas para simple vertical 1HG
    conexiones = [
        ("BASE", "V", "columna"),
        ("V", "CROSS_H1", "columna"),
        ("CROSS_H1", "C1_L", "mensula")
    ]
    
    if h2a > h1a:
        conexiones.extend([
            ("CROSS_H1", "CROSS_H2", "columna"),
            ("CROSS_H2", "C2_L", "mensula")
        ])
    
    if h3a > h2a:
        conexiones.extend([
            ("CROSS_H2", "CROSS_H3", "columna"),
            ("CROSS_H3", "C3_L", "mensula")
        ])
    
    # Conexión a guardia
    if "TOP" in nodos:
        conexiones.append(("CROSS_H3", "TOP", "columna"))
        conexiones.append(("TOP", "HG1", "mensula"))
    else:
        conexiones.append(("CROSS_H3", "HG1", "columna"))
    
    return nodos, conexiones

def _crear_simple_triangular_nohg(params):
    """Simple triangular sin HG - LÓGICA LEGACY"""
    nodos = {}
    
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmen = params['lmen']
    altura_total = max(h1a, h2a, h3a)
    
    # Nodos estructura
    nodos["BASE"] = NodoEstructural("BASE", (0.0, 0.0, 0.0), "base")
    nodos["V"] = NodoEstructural("V", (0.0, 0.0, altura_total * 2/3), "viento")
    nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")
    if h2a > h1a:
        nodos["CROSS_H2"] = NodoEstructural("CROSS_H2", (0.0, 0.0, h2a), "cruce")
    
    # Nodos conductor (triangular) - LÓGICA LEGACY
    nodos["C1_R"] = NodoEstructural("C1_R", (lmen, 0.0, h1a), "conductor")
    nodos["C1_L"] = NodoEstructural("C1_L", (-lmen, 0.0, h1a), "conductor")
    nodos["C2_R"] = NodoEstructural("C2_R", (lmen, 0.0, h2a), "conductor")
    
    # Generar conexiones con nueva lógica
    conexiones = _generar_conexiones_estandar(nodos, params)
    
    return nodos, conexiones

def _crear_simple_triangular_1hg_defasado(params):
    """Simple triangular con 1 HG defasado - LÓGICA LEGACY"""
    nodos = {}
    
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmen = params['lmen']
    D_fases = params['D_fases']
    Dhg = params.get('Dhg', 1.0)
    ang_apantallamiento = params.get('ang_apantallamiento', 30.0)
    hadd_hg = params.get('hadd_hg', 0.0)
    long_mensula_min_guardia = params.get('long_mensula_min_guardia', 0.2)
    
    # Calcular pcma y guardia (LÓGICA LEGACY)
    pcma = _calcular_posicion_conductor_mas_alto(h1a, h2a, h3a, lmen, "triangular", "Simple", 0, D_fases, 0, 0, 0)
    hhg, lmenhg, phg1, phg2 = _calcular_cable_guardia(pcma, D_fases, Dhg, 1, False, ang_apantallamiento, hadd_hg, long_mensula_min_guardia)
    
    altura_total = max(h1a, h2a, h3a, hhg)
    
    # Nodos estructura
    nodos["BASE"] = NodoEstructural("BASE", (0.0, 0.0, 0.0), "base")
    nodos["V"] = NodoEstructural("V", (0.0, 0.0, altura_total * 2/3), "viento")
    nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")
    if h2a > h1a:
        nodos["CROSS_H2"] = NodoEstructural("CROSS_H2", (0.0, 0.0, h2a), "cruce")
    nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, hhg), "general")
    
    # Nodos conductor (triangular) - LÓGICA LEGACY
    nodos["C1_R"] = NodoEstructural("C1_R", (lmen, 0.0, h1a), "conductor")
    nodos["C1_L"] = NodoEstructural("C1_L", (-lmen, 0.0, h1a), "conductor")
    nodos["C2_R"] = NodoEstructural("C2_R", (lmen, 0.0, h2a), "conductor")
    
    # Nodos guardia - usar posición calculada
    nodos["HG1"] = NodoEstructural("HG1", (phg1[0], 0.0, phg1[1]), "guardia")
    
    # Generar conexiones con nueva lógica
    conexiones = _generar_conexiones_estandar(nodos, params)
    
    return nodos, conexiones
    
    return nodos, conexiones

def _crear_simple_horizontal_nohg(params):
    """Simple horizontal sin HG - CON CROSS (legacy)"""
    nodos = {}
    
    h1a = params['h1a']
    s_estructura = params['s_estructura']
    D_fases = params['D_fases']
    theta_max = params.get('theta_max', 0)
    lk = params.get('lk', 2.5)
    ancho_cruceta = params.get('ancho_cruceta', 0.3)
    altura_total = h1a
    
    # Calcular distancias complejas (LÓGICA LEGACY)
    dist_columna_x = max(lk * math.sin(math.radians(theta_max)) + s_estructura, D_fases / 2)
    dist_conductor_x = dist_columna_x + lk * math.sin(math.radians(theta_max)) + s_estructura + ancho_cruceta/2
    dist_conductor_final = max(D_fases, dist_conductor_x)
    
    # Nodos estructura
    nodos["BASE"] = NodoEstructural("BASE", (0.0, 0.0, 0.0), "base")
    nodos["V"] = NodoEstructural("V", (0.0, 0.0, altura_total * 2/3), "viento")
    nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")  # SÍ hay CROSS en NOHG
    
    # Nodos conductor (horizontal - lógica compleja legacy)
    nodos["C1"] = NodoEstructural("C1", (dist_conductor_final, 0.0, h1a), "conductor")
    nodos["C2"] = NodoEstructural("C2", (0.0, 0.0, h1a), "conductor")
    nodos["C3"] = NodoEstructural("C3", (-dist_conductor_final, 0.0, h1a), "conductor")
    
    # Generar conexiones con nueva lógica
    conexiones = _generar_conexiones_estandar(nodos, params)
    
    return nodos, conexiones

def _crear_simple_horizontal_1hg(params):
    """Simple horizontal con 1 HG centrado - SIN CROSS (AT)"""
    nodos = {}
    
    h1a = params['h1a']
    s_estructura = params['s_estructura']
    D_fases = params['D_fases']
    theta_max = params.get('theta_max', 0)
    lk = params.get('lk', 2.5)
    ancho_cruceta = params.get('ancho_cruceta', 0.3)
    ang_apantallamiento = params.get('ang_apantallamiento', 30.0)
    Dhg = params.get('Dhg', 1.0)
    hadd_hg = params.get('hadd_hg', 0.0)
    long_mensula_min_guardia = params.get('long_mensula_min_guardia', 0.2)
    
    # Calcular pcma y guardia (LÓGICA LEGACY)
    pcma = _calcular_posicion_conductor_mas_alto(h1a, h1a, h1a, 0, "horizontal", "Simple", s_estructura, D_fases, theta_max, lk, ancho_cruceta)
    hhg, lmenhg, phg1, phg2 = _calcular_cable_guardia(pcma, D_fases, Dhg, 1, True, ang_apantallamiento, hadd_hg, long_mensula_min_guardia)
    
    # Calcular distancias complejas
    dist_columna_x = max(lk * math.sin(math.radians(theta_max)) + s_estructura, D_fases / 2)
    dist_conductor_x = dist_columna_x + lk * math.sin(math.radians(theta_max)) + s_estructura + ancho_cruceta/2
    dist_conductor_final = max(D_fases, dist_conductor_x)
    
    # Nodos estructura (AT - nodos Y)
    nodos["BASE"] = NodoEstructural("BASE", (0.0, 0.0, 0.0), "base")
    nodos["V"] = NodoEstructural("V", (0.0, 0.0, hhg * 2/3), "viento")
    nodos["Y1"] = NodoEstructural("Y1", (0.0, 0.0, h1a - 2*lk), "general")
    nodos["Y2"] = NodoEstructural("Y2", (dist_columna_x, 0.0, h1a - lk), "general")
    nodos["Y3"] = NodoEstructural("Y3", (-dist_columna_x, 0.0, h1a - lk), "general")
    nodos["Y4"] = NodoEstructural("Y4", (dist_columna_x, 0.0, h1a), "general")
    nodos["Y5"] = NodoEstructural("Y5", (-dist_columna_x, 0.0, h1a), "general")
    # NO hay CROSS en 1HG
    
    # Nodos conductor
    nodos["C1"] = NodoEstructural("C1", (dist_conductor_final, 0.0, h1a), "conductor")
    nodos["C2"] = NodoEstructural("C2", (0.0, 0.0, h1a), "conductor")
    nodos["C3"] = NodoEstructural("C3", (-dist_conductor_final, 0.0, h1a), "conductor")
    
    # Nodos guardia (centrado)
    nodos["HG1"] = NodoEstructural("HG1", (0.0, 0.0, hhg), "guardia")
    
    # Conexiones AT específicas
    conexiones = [
        ("BASE", "V", "columna"),
        ("V", "Y1", "columna"),
        ("Y1", "Y2", "mensula"),
        ("Y1", "Y3", "mensula"),
        ("Y2", "Y4", "columna"),
        ("Y3", "Y5", "columna"),
        ("Y4", "C1", "mensula"),
        ("Y1", "C2", "mensula"),
        ("Y5", "C3", "mensula"),
        ("Y1", "HG1", "columna")  # HG centrado conecta a Y1
    ]
    
    return nodos, conexiones

def _crear_simple_horizontal_2hg(params):
    """Simple horizontal con 2 HG - Nueva lógica estándar (NO AT)"""
    nodos = {}
    
    h1a = params['h1a']
    lmenhg = params['lmenhg']
    D_fases = params['D_fases']  # Usar D_fases para separación horizontal
    altura_total = h1a + 1.0 + lmenhg
    
    # Nodos estructura
    nodos["BASE"] = NodoEstructural("BASE", (0.0, 0.0, 0.0), "base")
    nodos["V"] = NodoEstructural("V", (0.0, 0.0, altura_total * 2/3), "viento")
    nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")
    nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, h1a + 1.0 + lmenhg), "general")
    
    # Nodos conductor (horizontal) - CORREGIDO: usar D_fases
    nodos["C1"] = NodoEstructural("C1", (D_fases, 0.0, h1a), "conductor")
    nodos["C2"] = NodoEstructural("C2", (0.0, 0.0, h1a), "conductor")
    nodos["C3"] = NodoEstructural("C3", (-D_fases, 0.0, h1a), "conductor")
    
    # Nodos guardia (2 HG)
    nodos["HG1"] = NodoEstructural("HG1", (lmenhg, 0.0, h1a + 1.0 + lmenhg), "guardia")
    nodos["HG2"] = NodoEstructural("HG2", (-lmenhg, 0.0, h1a + 1.0 + lmenhg), "guardia")
    
    # Generar conexiones con nueva lógica
    conexiones = _generar_conexiones_estandar(nodos, params)
    
    return nodos, conexiones
    
    return nodos, conexiones

# Aplicar nueva lógica estándar a todas las morfologías dobles
def _crear_doble_vertical_nohg(params):
    """Doble vertical sin HG - Nueva lógica estándar"""
    nodos = {}
    
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmen = params['lmen']  # Usar lmen en lugar de s_estructura
    altura_total = _calcular_altura_total_con_guardia(h1a, h2a, h3a, 0)
    
    # Nodos estructura
    nodos["BASE"] = _crear_nodo_estructural_completo("BASE", (0.0, 0.0, 0.0), "base", params)
    nodos["V"] = _crear_nodo_estructural_completo("V", (0.0, 0.0, altura_total * 2/3), "viento", params)
    nodos["CROSS_H1"] = _crear_nodo_estructural_completo("CROSS_H1", (0.0, 0.0, h1a), "cruce", params)
    if h2a > h1a:
        nodos["CROSS_H2"] = _crear_nodo_estructural_completo("CROSS_H2", (0.0, 0.0, h2a), "cruce", params)
    if h3a > h2a:
        nodos["CROSS_H3"] = _crear_nodo_estructural_completo("CROSS_H3", (0.0, 0.0, h3a), "cruce", params)
    
    # Nodos conductor (doble terna) - CORREGIDO: usar lmen y Y=0
    nodos["C1_R"] = _crear_nodo_estructural_completo("C1_R", (lmen, 0.0, h1a), "conductor", params)
    nodos["C2_R"] = _crear_nodo_estructural_completo("C2_R", (lmen, 0.0, h2a), "conductor", params)
    nodos["C3_R"] = _crear_nodo_estructural_completo("C3_R", (lmen, 0.0, h3a), "conductor", params)
    nodos["C1_L"] = _crear_nodo_estructural_completo("C1_L", (-lmen, 0.0, h1a), "conductor", params)
    nodos["C2_L"] = _crear_nodo_estructural_completo("C2_L", (-lmen, 0.0, h2a), "conductor", params)
    nodos["C3_L"] = _crear_nodo_estructural_completo("C3_L", (-lmen, 0.0, h3a), "conductor", params)
    
    # Conexiones específicas para doble vertical
    conexiones = [
        ("BASE", "V", "columna"),
        ("V", "CROSS_H1", "columna"),
        ("CROSS_H1", "C1_R", "mensula"),
        ("CROSS_H1", "C1_L", "mensula"),
        ("C1_R", "C1_L", "cruceta")
    ]
    
    if h2a > h1a:
        conexiones.extend([
            ("CROSS_H1", "CROSS_H2", "columna"),
            ("CROSS_H2", "C2_R", "mensula"),
            ("CROSS_H2", "C2_L", "mensula"),
            ("C2_R", "C2_L", "cruceta")
        ])
    
    if h3a > h2a:
        conexiones.extend([
            ("CROSS_H2", "CROSS_H3", "columna"),
            ("CROSS_H3", "C3_R", "mensula"),
            ("CROSS_H3", "C3_L", "mensula"),
            ("C3_R", "C3_L", "cruceta")
        ])
    
    return nodos, conexiones

def _crear_doble_vertical_1hg(params):
    """Doble vertical con 1 HG centrado - LÓGICA LEGACY"""
    nodos, _ = _crear_doble_vertical_nohg(params)
    
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmen = params['lmen']
    D_fases = params['D_fases']
    Dhg = params.get('Dhg', 1.0)
    ang_apantallamiento = params.get('ang_apantallamiento', 30.0)
    hadd_hg = params.get('hadd_hg', 0.0)
    long_mensula_min_guardia = params.get('long_mensula_min_guardia', 0.2)
    
    # Calcular pcma y guardia (LÓGICA LEGACY)
    pcma = _calcular_posicion_conductor_mas_alto(h1a, h2a, h3a, lmen, "vertical", "Doble", 0, D_fases, 0, 0, 0)
    hhg, lmenhg, phg1, phg2 = _calcular_cable_guardia(pcma, D_fases, Dhg, 1, True, ang_apantallamiento, hadd_hg, long_mensula_min_guardia)
    
    # Recalcular altura total con guardia
    altura_total = _calcular_altura_total_con_guardia(h1a, h2a, h3a, hhg)
    nodos["V"] = _crear_nodo_estructural_completo("V", (0.0, 0.0, altura_total * 2/3), "viento", params)
    
    # Agregar nodos guardia
    nodos["TOP"] = _crear_nodo_estructural_completo("TOP", (0.0, 0.0, hhg), "general", params)
    nodos["HG1"] = _crear_nodo_estructural_completo("HG1", (0.0, 0.0, hhg), "guardia", params)
    
    # Eliminar TOP si está superpuesto
    nodos = _eliminar_top_superpuesto(nodos)
    
    # Conexiones específicas para doble vertical 1HG
    conexiones = [
        ("BASE", "V", "columna"),
        ("V", "CROSS_H1", "columna"),
        ("CROSS_H1", "CROSS_H2", "columna"),
        ("CROSS_H2", "CROSS_H3", "columna"),
        ("CROSS_H1", "C1_R", "mensula"),
        ("CROSS_H1", "C1_L", "mensula"),
        ("CROSS_H2", "C2_R", "mensula"),
        ("CROSS_H2", "C2_L", "mensula"),
        ("CROSS_H3", "C3_R", "mensula"),
        ("CROSS_H3", "C3_L", "mensula"),
        ("C1_R", "C1_L", "cruceta"),
        ("C2_R", "C2_L", "cruceta"),
        ("C3_R", "C3_L", "cruceta")
    ]
    
    # Agregar conexión a guardia (centrado o TOP)
    if "TOP" in nodos:
        conexiones.append(("CROSS_H3", "TOP", "columna"))
        conexiones.append(("TOP", "HG1", "mensula"))
    else:
        conexiones.append(("CROSS_H3", "HG1", "columna"))
    
    return nodos, conexiones

def _crear_doble_vertical_2hg(params):
    """Doble vertical con 2 HG - LÓGICA LEGACY"""
    nodos, _ = _crear_doble_vertical_nohg(params)
    
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmen = params['lmen']
    D_fases = params['D_fases']
    Dhg = params.get('Dhg', 1.0)
    ang_apantallamiento = params.get('ang_apantallamiento', 30.0)
    hadd_hg = params.get('hadd_hg', 0.0)
    long_mensula_min_guardia = params.get('long_mensula_min_guardia', 0.2)
    
    # Calcular pcma y guardia (LÓGICA LEGACY)
    pcma = _calcular_posicion_conductor_mas_alto(h1a, h2a, h3a, lmen, "vertical", "Doble", 0, D_fases, 0, 0, 0)
    hhg, lmenhg, phg1, phg2 = _calcular_cable_guardia(pcma, D_fases, Dhg, 2, False, ang_apantallamiento, hadd_hg, long_mensula_min_guardia)
    
    # Aplicar ajuste iterativo si está habilitado
    hhg, lmenhg, phg1, phg2 = _aplicar_ajuste_iterativo_lmenhg(hhg, lmenhg, phg1, phg2, params)
    
    # Recalcular altura total con guardia
    altura_total = _calcular_altura_total_con_guardia(h1a, h2a, h3a, hhg)
    nodos["V"] = _crear_nodo_estructural_completo("V", (0.0, 0.0, altura_total * 2/3), "viento", params)
    
    # Agregar nodos guardia - usar posiciones calculadas
    nodos["TOP"] = _crear_nodo_estructural_completo("TOP", (0.0, 0.0, hhg), "general", params)
    nodos["HG1"] = _crear_nodo_estructural_completo("HG1", (phg1[0], 0.0, phg1[1]), "guardia", params)
    nodos["HG2"] = _crear_nodo_estructural_completo("HG2", (phg2[0], 0.0, phg2[1]), "guardia", params)
    
    # Eliminar TOP si está superpuesto
    nodos = _eliminar_top_superpuesto(nodos)
    
    # Actualizar dimensiones
    dimensiones = _actualizar_dimensiones_morfologia(params, hhg, lmenhg, phg1, phg2, pcma)
    
    # Conexiones específicas para doble vertical 2HG
    conexiones = [
        ("BASE", "V", "columna"),
        ("V", "CROSS_H1", "columna"),
        ("CROSS_H1", "CROSS_H2", "columna"),
        ("CROSS_H2", "CROSS_H3", "columna"),
        ("CROSS_H1", "C1_R", "mensula"),
        ("CROSS_H1", "C1_L", "mensula"),
        ("CROSS_H2", "C2_R", "mensula"),
        ("CROSS_H2", "C2_L", "mensula"),
        ("CROSS_H3", "C3_R", "mensula"),
        ("CROSS_H3", "C3_L", "mensula"),
        ("C1_R", "C1_L", "cruceta"),
        ("C2_R", "C2_L", "cruceta"),
        ("C3_R", "C3_L", "cruceta")
    ]
    
    # Conexiones a guardias
    if "TOP" in nodos:
        conexiones.extend([
            ("CROSS_H3", "TOP", "columna"),
            ("TOP", "HG1", "mensula"),
            ("TOP", "HG2", "mensula")
        ])
    else:
        conexiones.extend([
            ("CROSS_H3", "HG1", "mensula"),
            ("CROSS_H3", "HG2", "mensula")
        ])
    
    return nodos, conexiones

def _crear_doble_triangular_nohg(params):
    """Doble triangular sin HG - LÓGICA LEGACY CORREGIDA"""
    nodos = {}
    
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmen = params['lmen']
    # CORREGIDO: lmen2c solo para doble triangular
    lmen2c = lmen + params.get('D_fases', 1.5)
    altura_total = _calcular_altura_total_con_guardia(h1a, h2a, h3a, 0)
    
    # Nodos estructura
    nodos["BASE"] = _crear_nodo_estructural_completo("BASE", (0.0, 0.0, 0.0), "base", params)
    nodos["V"] = _crear_nodo_estructural_completo("V", (0.0, 0.0, altura_total * 2/3), "viento", params)
    nodos["CROSS_H1"] = _crear_nodo_estructural_completo("CROSS_H1", (0.0, 0.0, h1a), "cruce", params)
    if h2a > h1a:
        nodos["CROSS_H2"] = _crear_nodo_estructural_completo("CROSS_H2", (0.0, 0.0, h2a), "cruce", params)
    
    # Nodos conductor (doble triangular) - LÓGICA LEGACY
    # Nivel inferior (h1a): 4 conductores
    nodos["C1_R"] = _crear_nodo_estructural_completo("C1_R", (lmen, 0.0, h1a), "conductor", params)
    nodos["C2_R"] = _crear_nodo_estructural_completo("C2_R", (lmen2c, 0.0, h1a), "conductor", params)
    nodos["C1_L"] = _crear_nodo_estructural_completo("C1_L", (-lmen, 0.0, h1a), "conductor", params)
    nodos["C2_L"] = _crear_nodo_estructural_completo("C2_L", (-lmen2c, 0.0, h1a), "conductor", params)
    
    # Nivel superior (h2a): 2 conductores (si h2a > h1a)
    if h2a > h1a:
        nodos["C3_R"] = _crear_nodo_estructural_completo("C3_R", (lmen, 0.0, h2a), "conductor", params)
        nodos["C3_L"] = _crear_nodo_estructural_completo("C3_L", (-lmen, 0.0, h2a), "conductor", params)
    
    # Conexiones específicas para doble triangular
    conexiones = [
        ("BASE", "V", "columna"),
        ("V", "CROSS_H1", "columna"),
        ("CROSS_H1", "C1_R", "mensula"),
        ("CROSS_H1", "C1_L", "mensula"),
        ("C1_R", "C2_R", "cruceta"),
        ("C1_L", "C2_L", "cruceta")
    ]
    
    if h2a > h1a:
        conexiones.extend([
            ("CROSS_H1", "CROSS_H2", "columna"),
            ("CROSS_H2", "C3_R", "mensula"),
            ("CROSS_H2", "C3_L", "mensula")
        ])
    
    return nodos, conexiones

def _crear_doble_triangular_1hg(params):
    """Doble triangular con 1 HG defasado - LÓGICA LEGACY"""
    nodos, conexiones = _crear_doble_triangular_nohg(params)
    
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmen = params['lmen']
    D_fases = params['D_fases']
    Dhg = params.get('Dhg', 1.0)
    ang_apantallamiento = params.get('ang_apantallamiento', 30.0)
    hadd_hg = params.get('hadd_hg', 0.0)
    long_mensula_min_guardia = params.get('long_mensula_min_guardia', 0.2)
    
    # Calcular pcma y guardia (LÓGICA LEGACY)
    pcma = _calcular_posicion_conductor_mas_alto(h1a, h2a, h3a, lmen, "triangular", "Doble", 0, D_fases, 0, 0, 0)
    hhg, lmenhg, phg1, phg2 = _calcular_cable_guardia(pcma, D_fases, Dhg, 1, False, ang_apantallamiento, hadd_hg, long_mensula_min_guardia)
    
    # Agregar nodo TOP
    nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, hhg), "general")
    
    # Agregar nodo HG - usar posición calculada
    nodos["HG1"] = NodoEstructural("HG1", (phg1[0], 0.0, phg1[1]), "guardia")
    
    # Regenerar conexiones con nueva lógica
    conexiones = _generar_conexiones_estandar(nodos, params)
    
    return nodos, conexiones

def _crear_doble_triangular_2hg(params):
    """Doble triangular con 2 HG - LÓGICA LEGACY"""
    nodos, _ = _crear_doble_triangular_nohg(params)
    
    h1a, h2a, h3a = params['h1a'], params['h2a'], params['h3a']
    lmen = params['lmen']
    lmen2c = lmen + params.get('D_fases', 1.5)  # Solo para doble triangular
    D_fases = params['D_fases']
    Dhg = params.get('Dhg', 1.0)
    ang_apantallamiento = params.get('ang_apantallamiento', 30.0)
    hadd_hg = params.get('hadd_hg', 0.0)
    long_mensula_min_guardia = params.get('long_mensula_min_guardia', 0.2)
    
    # Calcular pcma y guardia (LÓGICA LEGACY)
    pcma = _calcular_posicion_conductor_mas_alto(h1a, h2a, h3a, lmen, "triangular", "Doble", 0, D_fases, 0, 0, 0)
    hhg, lmenhg, phg1, phg2 = _calcular_cable_guardia(pcma, D_fases, Dhg, 2, False, ang_apantallamiento, hadd_hg, long_mensula_min_guardia)
    
    # Aplicar ajuste iterativo si está habilitado
    hhg, lmenhg, phg1, phg2 = _aplicar_ajuste_iterativo_lmenhg(hhg, lmenhg, phg1, phg2, params)
    
    # Recalcular altura total con guardia
    altura_total = _calcular_altura_total_con_guardia(h1a, h2a, h3a, hhg)
    nodos["V"] = _crear_nodo_estructural_completo("V", (0.0, 0.0, altura_total * 2/3), "viento", params)
    
    # Agregar nodos guardia - usar posiciones calculadas
    nodos["TOP"] = _crear_nodo_estructural_completo("TOP", (0.0, 0.0, hhg), "general", params)
    nodos["HG1"] = _crear_nodo_estructural_completo("HG1", (phg1[0], 0.0, phg1[1]), "guardia", params)
    nodos["HG2"] = _crear_nodo_estructural_completo("HG2", (phg2[0], 0.0, phg2[1]), "guardia", params)
    
    # Eliminar TOP si está superpuesto
    nodos = _eliminar_top_superpuesto(nodos)
    
    # Actualizar dimensiones incluyendo lmen2c
    dimensiones = _actualizar_dimensiones_morfologia(params, hhg, lmenhg, phg1, phg2, pcma, lmen2c)
    
    # Conexiones específicas para doble triangular 2HG
    conexiones = [
        ("BASE", "V", "columna"),
        ("V", "CROSS_H1", "columna"),
        ("CROSS_H1", "C1_R", "mensula"),
        ("CROSS_H1", "C1_L", "mensula"),
        ("C1_R", "C2_R", "cruceta"),
        ("C1_L", "C2_L", "cruceta")
    ]
    
    if h2a > h1a:
        conexiones.extend([
            ("CROSS_H1", "CROSS_H2", "columna"),
            ("CROSS_H2", "C3_R", "mensula"),
            ("CROSS_H2", "C3_L", "mensula")
        ])
    
    # Conexiones a guardias
    if "TOP" in nodos:
        if h2a > h1a:
            conexiones.append(("CROSS_H2", "TOP", "columna"))
        else:
            conexiones.append(("CROSS_H1", "TOP", "columna"))
        conexiones.extend([
            ("TOP", "HG1", "mensula"),
            ("TOP", "HG2", "mensula")
        ])
    
    return nodos, conexiones

def extraer_parametros_morfologia(morfologia: str):
    """Extrae parámetros legacy de morfología para compatibilidad"""
    # Manejar morfologías AT
    if morfologia.endswith("-AT"):
        morfologia_base = morfologia[:-3]  # Remover "-AT"
        partes = morfologia_base.split("-")
    else:
        partes = morfologia.split("-")
    
    terna = partes[0]  # SIMPLE o DOBLE
    disposicion = partes[1].lower()  # vertical, triangular, horizontal
    hg_info = partes[2]  # NOHG, 1HG, 2HG
    
    if hg_info == "NOHG":
        cant_hg = 0
        hg_centrado = False
    elif hg_info == "1HG":
        cant_hg = 1
        # HG centrado solo en horizontal simple y doble vertical
        hg_centrado = (disposicion == "horizontal" and terna == "SIMPLE") or \
                     (disposicion == "vertical" and terna == "DOBLE")
    elif hg_info == "2HG":
        cant_hg = 2
        hg_centrado = False
    else:
        raise ValueError(f"Información HG inválida: {hg_info}")
    
    return {
        "TERNA": terna,
        "DISPOSICION": disposicion,
        "CANT_HG": cant_hg,
        "HG_CENTRADO": hg_centrado
    }

def inferir_morfologia_desde_parametros(terna, disposicion, cant_hg, hg_centrado, usar_at=False):
    """Infiere morfología desde parámetros legacy"""
    terna_str = terna.upper()
    disposicion_str = disposicion.upper()
    
    if cant_hg == 0:
        hg_str = "NOHG"
    elif cant_hg == 1:
        if hg_centrado:
            hg_str = "1HG"  # Centrado implícito
        else:
            if disposicion_str == "TRIANGULAR":
                hg_str = "1HG-DEFASADO"
            else:
                hg_str = "1HG"
    elif cant_hg == 2:
        hg_str = "2HG"
    else:
        raise ValueError(f"CANT_HG inválido: {cant_hg}")
    
    morfologia_base = f"{terna_str}-{disposicion_str}-{hg_str}"
    
    # Agregar sufijo AT si se especifica
    if usar_at:
        return f"{morfologia_base}-AT"
    else:
        return morfologia_base