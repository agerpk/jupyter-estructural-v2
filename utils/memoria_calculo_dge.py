"""Generador de Memoria de Cálculo para Diseño Geométrico de Estructura"""
import math

def gen_memoria_calculo_DGE(estructura_geometria):
    """
    Genera memoria de cálculo del Diseño Geométrico de Estructura
    
    Args:
        estructura_geometria: Objeto EstructuraAEA_Geometria con dimensionamiento completo
    
    Returns:
        str: Texto formateado con la memoria de cálculo
    """
    
    # Extraer datos
    dim = estructura_geometria.dimensiones
    
    memoria = []
    memoria.append("DISEÑO GEOMETRICO DE ESTRUCTURA - METODO AEA 95301")
    memoria.append("=" * 80)
    memoria.append("")
    
    # DATOS DE ENTRADA
    memoria.append("DATOS DE ENTRADA")
    memoria.append("-" * 40)
    memoria.append(f"Tipo de estructura: {estructura_geometria.tipo_estructura}")
    memoria.append(f"Tension nominal (Vn): {estructura_geometria.tension_nominal} kV")
    memoria.append(f"Tension maxima (Vm): {estructura_geometria.tension_maxima} kV")
    memoria.append(f"Zona: {estructura_geometria.zona_estructura}")
    memoria.append(f"Disposicion: {estructura_geometria.disposicion}")
    memoria.append(f"Terna: {estructura_geometria.terna}")
    memoria.append(f"Cantidad cables guardia: {estructura_geometria.cant_hg}")
    memoria.append(f"Angulo de quiebre (alpha): {estructura_geometria.alpha_quiebre} grados")
    memoria.append(f"Longitud de cadena (Lk): {estructura_geometria.lk} m")
    memoria.append(f"Altura adicional libre (HADD): {estructura_geometria.hadd} m")
    memoria.append(f"HADD entre amarres: {estructura_geometria.hadd_entre_amarres} m")
    memoria.append(f"Ancho de cruceta: {estructura_geometria.ancho_cruceta} m")
    memoria.append(f"Peso de cadena: {estructura_geometria.peso_cadena} daN")
    memoria.append("")
    
    # PASO 0: COEFICIENTE DE ALTURA
    Ka = dim.get('Ka', 1.0)
    memoria.append("PASO 0: COEFICIENTE DE AJUSTE POR ALTURA MSNM (Ka)")
    memoria.append("-" * 60)
    if Ka != 1.0:
        memoria.append(f"Metodo: {estructura_geometria.metodo_altura_msnm}")
        memoria.append(f"Altura MSNM: {estructura_geometria.altura_msnm} m")
        memoria.append("Formula: Ka = 1 + 0.03 * (H - 1000) / 300")
        memoria.append("Donde:")
        memoria.append("  H = Altura sobre el nivel del mar (m)")
        memoria.append(f"Resultado: Ka = {Ka:.3f}")
    else:
        memoria.append("No se aplica ajuste por altura (altura <= 1000 msnm o desactivado)")
        memoria.append(f"Resultado: Ka = {Ka:.3f}")
    memoria.append("")
    
    # PASO 1: THETA_MAX
    memoria.append("PASO 1: DETERMINACION DEL ANGULO DE DECLINACION THETA_MAX")
    memoria.append("-" * 60)
    
    theta_max = dim.get('theta_max', 0)
    
    if estructura_geometria.tipo_fijacion_base != "suspensión" or estructura_geometria.lk == 0:
        memoria.append("Formula: theta_max = 0 (estructura no es suspension o Lk=0)")
        memoria.append(f"Resultado: theta_max = {theta_max} grados")
    else:
        memoria.append("Formula: theta_max = arctan((Fv + Fca) / (Pc + Pcadena))")
        memoria.append("Donde:")
        memoria.append("  Fv = Fuerza de viento sobre conductor (daN)")
        memoria.append("  Fca = Fuerza de viento sobre cadena de aisladores (daN)")
        memoria.append("  Pc = Peso del conductor en el vano (daN)")
        memoria.append("  Pcadena = Peso de la cadena (daN)")
        memoria.append(f"Resultado: theta_max = {theta_max:.2f} grados")
    memoria.append("")
    
    # PASO 2: COEFICIENTE K
    memoria.append("PASO 2: DETERMINACION DEL COEFICIENTE K")
    memoria.append("-" * 60)
    k = dim.get('k', 0)
    memoria.append("")
    memoria.append("Tabla de coeficientes k segun disposicion y angulo theta_max:")
    memoria.append("")
    memoria.append("  Disposicion    | <45°  | 45° a 55° | 55° a 65° | >65°")
    memoria.append("  ---------------|-------|-----------|-----------|------")
    memoria.append("  Vertical       | 0.70  |   0.75    |   0.85    | 0.95")
    memoria.append("  Triangular     | 0.62  |   0.65    |   0.70    | 0.75")
    memoria.append("  Horizontal     | 0.60  |   0.62    |   0.70    | 0.75")
    memoria.append("")
    memoria.append(f"Segun disposicion '{estructura_geometria.disposicion}' y theta_max = {theta_max:.2f} grados")
    memoria.append(f"Resultado: k = {k:.3f}")
    memoria.append("")
    
    # PASO 3: DISTANCIAS MINIMAS
    paso_num = 3
    memoria.append(f"PASO {paso_num}: CALCULO DE DISTANCIAS MINIMAS")
    memoria.append("-" * 60)
    
    D_fases = dim.get('D_fases', 0)
    s_estructura = dim.get('s_estructura', 0)
    Dhg = dim.get('Dhg', 0)
    termino_flecha = dim.get('termino_flecha', 0)
    
    memoria.append(f"a) Distancia minima entre fases (D):")
    memoria.append(f"   Formula: D = k * √(fmax + Lk) + Ka * Vn / 150")
    memoria.append(f"   Donde:")
    memoria.append(f"     k = {k:.3f}")
    memoria.append(f"     fmax + Lk = {termino_flecha:.3f} m")
    memoria.append(f"     Ka = {Ka:.3f}")
    memoria.append(f"     Vn = {estructura_geometria.tension_nominal} kV")
    memoria.append(f"   Resultado: D = {D_fases:.3f} m")
    memoria.append("")
    
    memoria.append(f"b) Distancia minima fase-estructura (s):")
    memoria.append(f"   Formula: s = max(s_base * Ka, Ka * Vn / 150)")
    memoria.append(f"   Donde:")
    memoria.append(f"     s_base = 0.280 + 0.005 * (Vm - 50)")
    memoria.append(f"     Vm = {estructura_geometria.tension_maxima} kV")
    memoria.append(f"     Ka = {Ka:.3f}")
    memoria.append(f"   Resultado: s = {s_estructura:.3f} m")
    memoria.append("")
    
    memoria.append(f"c) Distancia minima guardia-conductor (Dhg):")
    memoria.append(f"   Formula: Dhg = k * √(fmax + Lk) + Ka * (Vn / √3) / 150")
    memoria.append(f"   Resultado: Dhg = {Dhg:.3f} m")
    memoria.append("")
    
    # PASO 4: COMPONENTE ELECTRICO
    paso_num += 1
    b = dim.get('b', 0)
    h_base_electrica = dim.get('h_base_electrica', 0)
    a = estructura_geometria.ALTURAS_MINIMAS_TERRENO.get(estructura_geometria.zona_estructura, 5.90)
    
    memoria.append(f"PASO {paso_num}: COMPONENTE ELECTRICO Y ALTURA BASE")
    memoria.append("-" * 60)
    memoria.append(f"a) Componente electrico (b):")
    memoria.append(f"   Formula: b = 0.01 * (Vn / sqrt(3) - 22) * Ka  (si Vn > 33)")
    memoria.append(f"   Resultado: b = {b:.3f} m")
    memoria.append("")
    memoria.append(f"b) Altura base electrica:")
    memoria.append(f"   Formula: h_base = max(a + b, altura_minima_cable)")
    memoria.append(f"   Donde:")
    memoria.append("")
    memoria.append("   Tabla de alturas minimas 'a' sobre terreno segun zona:")
    memoria.append("")
    memoria.append("     Zona              | Altura (m)")
    memoria.append("     ------------------|------------")
    memoria.append("     Peatonal          |   4.70")
    memoria.append("     Rural             |   5.90")
    memoria.append("     Urbana            |   8.38")
    memoria.append("     Autopista         |   7.00")
    memoria.append("     Ferrocarril       |   8.50")
    memoria.append("     Linea Electrica   |   1.20")
    memoria.append("")
    memoria.append(f"     a = {a:.2f} m (altura minima sobre terreno para zona {estructura_geometria.zona_estructura})")
    memoria.append(f"     b = {b:.3f} m")
    memoria.append(f"     altura_minima_cable = {estructura_geometria.altura_minima_cable} m")
    memoria.append(f"   Resultado: h_base_electrica = {h_base_electrica:.3f} m")
    memoria.append("")
    
    # PASO 5: ALTURAS DE FASES
    paso_num += 1
    h1a = dim.get('h1a', 0)
    h2a = dim.get('h2a', 0)
    h3a = dim.get('h3a', 0)
    
    memoria.append(f"PASO {paso_num}: CALCULO DE ALTURAS DE SUJECION")
    memoria.append("-" * 60)
    memoria.append(f"a) Primer amarre (h1a):")
    memoria.append(f"   Formula: h1a = HADD + h_base_electrica + fmax + Lk")
    memoria.append(f"   Resultado: h1a = {h1a:.3f} m")
    memoria.append("")
    
    if estructura_geometria.disposicion in ["triangular", "vertical"]:
        memoria.append(f"b) Segundo amarre (h2a):")
        memoria.append(f"   Formula: h2a = h1a + max(HADD_fase + s + Lk + ancho_cruceta, HADD_fase - Lk + D)")
        memoria.append(f"   Resultado: h2a = {h2a:.3f} m")
        memoria.append("")
    
    if estructura_geometria.disposicion == "vertical":
        memoria.append(f"c) Tercer amarre (h3a):")
        memoria.append(f"   Formula: h3a = h2a + max(HADD_fase + s + Lk, HADD_fase - Lk + HADD_fase)")
        memoria.append(f"   Resultado: h3a = {h3a:.3f} m")
        memoria.append("")
    
    # PASO 6: LONGITUD DE MENSULA
    paso_num += 1
    lmen = dim.get('lmen', 0)
    lmen2c = dim.get('lmen2c', 0)
    
    memoria.append(f"PASO {paso_num}: CALCULO DE LONGITUD DE MENSULA")
    memoria.append("-" * 60)
    memoria.append(f"Formula: lmen = max(s + Lk * sin(theta_max) + HADD_lmen, lmen_minima)")
    memoria.append(f"Donde:")
    memoria.append(f"  s = {s_estructura:.3f} m")
    memoria.append(f"  Lk = {estructura_geometria.lk} m")
    memoria.append(f"  theta_max = {theta_max:.2f} grados")
    memoria.append(f"  lmen_minima = {estructura_geometria.long_mensula_min_conductor} m")
    memoria.append(f"Resultado: lmen = {lmen:.3f} m")
    
    if estructura_geometria.disposicion == "triangular" and estructura_geometria.terna == "Doble":
        memoria.append(f"Longitud mensula segundo conductor (terna doble triangular):")
        memoria.append(f"  Formula: lmen2c = lmen + D")
        memoria.append(f"  Resultado: lmen2c = {lmen2c:.3f} m")
    memoria.append("")
    
    # PASO 7: POSICION CONDUCTOR MAS ALTO
    paso_num += 1
    pcma_x = dim.get('pcma_x', 0)
    pcma_y = dim.get('pcma_y', 0)
    
    memoria.append(f"PASO {paso_num}: POSICION DEL CONDUCTOR MAS ALTO")
    memoria.append("-" * 60)
    memoria.append(f"Segun disposicion '{estructura_geometria.disposicion}':")
    memoria.append(f"  x = lmen = {pcma_x:.3f} m")
    memoria.append(f"  y = altura_amarre_mas_alto - Lk = {pcma_y:.3f} m")
    memoria.append("")
    
    # PASO 8: CABLE GUARDIA
    paso_num += 1
    if estructura_geometria.cant_hg > 0:
        hhg = dim.get('hhg', 0)
        lmenhg = dim.get('lmenhg', 0)
        
        memoria.append(f"PASO {paso_num}: CALCULO DE CABLE GUARDIA")
        memoria.append("-" * 60)
        
        if estructura_geometria.cant_hg == 1 and estructura_geometria.hg_centrado:
            memoria.append(f"Configuracion: 1 cable guardia CENTRADO")
            memoria.append(f"Formula: hhg = pcma_x / tan(ang_apantallamiento) + pcma_y")
            memoria.append(f"Donde:")
            memoria.append(f"  pcma_x = {pcma_x:.3f} m")
            memoria.append(f"  pcma_y = {pcma_y:.3f} m")
            memoria.append(f"  ang_apantallamiento = {estructura_geometria.ang_apantallamiento} grados")
            memoria.append(f"Resultado: hhg = {hhg:.3f} m, lmenhg = 0 (centrado)")
        
        elif estructura_geometria.cant_hg == 1 and not estructura_geometria.hg_centrado:
            memoria.append(f"Configuracion: 1 cable guardia NO CENTRADO")
            memoria.append(f"Formula altura: hhg = pcma_y + Dhg * cos(ang_apantallamiento) + HADD_hg")
            memoria.append(f"Formula mensula: lmenhg = max(lmenhg_base, lmenhg_minima)")
            memoria.append(f"  lmenhg_base = pcma_x - (dvhg/cos(ang)) * sin(ang)")
            memoria.append(f"Resultado: hhg = {hhg:.3f} m, lmenhg = {lmenhg:.3f} m")
        
        elif estructura_geometria.cant_hg == 2:
            memoria.append(f"Configuracion: 2 cables guardia")
            memoria.append(f"Formula altura: hhg = pcma_y + Dhg * cos(ang_apantallamiento) + HADD_hg")
            memoria.append(f"Formula mensula: lmenhg = max(pcma_x - Dhg * sin(ang), lmenhg_minima)")
            memoria.append(f"Resultado: hhg = {hhg:.3f} m, lmenhg = {lmenhg:.3f} m")
        
        memoria.append("")
    
    # TABLA RESUMEN
    memoria.append("TABLA RESUMEN DE RESULTADOS")
    memoria.append("-" * 60)
    memoria.append(f"{'Parametro':<40} {'Valor':<15} {'Unidad':<10}")
    memoria.append("-" * 80)
    
    resultados = [
        ("Angulo declinacion (theta_max)", f"{theta_max:.2f}", "grados"),
        ("Coeficiente k", f"{k:.3f}", ""),
        ("Distancia entre fases (D)", f"{D_fases:.3f}", "m"),
        ("Distancia fase-estructura (s)", f"{s_estructura:.3f}", "m"),
        ("Distancia guardia-conductor (Dhg)", f"{Dhg:.3f}", "m"),
        ("Altura base electrica", f"{h_base_electrica:.3f}", "m"),
        ("Altura primer amarre (h1a)", f"{h1a:.3f}", "m"),
        ("Altura segundo amarre (h2a)", f"{h2a:.3f}", "m"),
        ("Altura tercer amarre (h3a)", f"{h3a:.3f}", "m"),
        ("Longitud mensula conductor (lmen)", f"{lmen:.3f}", "m"),
    ]
    
    if lmen2c != lmen:
        resultados.append(("Longitud mensula conductor 2 (lmen2c)", f"{lmen2c:.3f}", "m"))
    
    if estructura_geometria.cant_hg > 0:
        resultados.append(("Altura cable guardia (hhg)", f"{dim.get('hhg', 0):.3f}", "m"))
        resultados.append(("Longitud mensula guardia (lmenhg)", f"{dim.get('lmenhg', 0):.3f}", "m"))
    
    resultados.append(("Altura total estructura", f"{dim.get('altura_total', 0):.3f}", "m"))
    
    if Ka != 1.0:
        resultados.append(("Coeficiente altura (Ka)", f"{Ka:.3f}", ""))
    
    for param, valor, unidad in resultados:
        memoria.append(f"{param:<40} {valor:<15} {unidad:<10}")
    
    memoria.append("=" * 80)
    
    return "\n".join(memoria)
