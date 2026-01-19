"""
Generador de Memoria de Cálculo para CMC (Cálculo Mecánico de Cables)
Basado en el patrón de memoria_calculo_dge.py
"""

def gen_memoria_calculo_CMC(cable_aea, vano, estados_climaticos, parametros_viento, 
                           restricciones, objetivo, resultados_finales, t_final, 
                           q0_final, estado_limitante):
    """
    Genera memoria de cálculo del Cálculo Mecánico de Cables
    
    Args:
        cable_aea: Objeto Cable_AEA con propiedades y métodos
        vano: Longitud del vano en metros
        estados_climaticos: Dict con estados climáticos
        parametros_viento: Dict con parámetros de viento
        restricciones: Dict con restricciones aplicadas
        objetivo: 'FlechaMin' o 'TiroMin'
        resultados_finales: Dict con resultados por estado
        t_final: Tensión final optimizada
        q0_final: Temperatura del estado básico
        estado_limitante: Estado que limita la optimización
    
    Returns:
        str: Texto formateado con la memoria de cálculo
    """
    
    memoria = []
    
    # Encabezado
    memoria.append("=" * 80)
    memoria.append("MEMORIA DE CÁLCULO - CÁLCULO MECÁNICO DE CABLES (CMC)")
    memoria.append("=" * 80)
    memoria.append("")
    
    # SECCIÓN 1: DATOS DE ENTRADA
    memoria.append("1. DATOS DE ENTRADA")
    memoria.append("-" * 50)
    memoria.append("")
    
    # Identificación del cable
    memoria.append("1.1 IDENTIFICACIÓN DEL CABLE")
    memoria.append(f"Cable ID: {cable_aea.id_cable}")
    memoria.append(f"Nombre: {cable_aea.nombre}")
    memoria.append(f"Tipo: {cable_aea.propiedades.get('material', 'N/A')}")
    memoria.append("")
    
    # Tabla de propiedades del cable
    memoria.append("1.2 PROPIEDADES DEL CABLE")
    memoria.extend(_generar_tabla_propiedades_cable(cable_aea))
    memoria.append("")
    
    # Parámetros de vano
    memoria.append("1.3 PARÁMETROS DE VANO")
    memoria.append(f"Longitud de vano: L = {vano} m")
    memoria.append("")
    
    # Estados climáticos
    memoria.append("1.4 ESTADOS CLIMÁTICOS")
    for estado_id, estado_data in estados_climaticos.items():
        memoria.append(f"Estado {estado_id}: {estado_data.get('descripcion', 'N/A')}")
        memoria.append(f"  Temperatura: {estado_data.get('temperatura', 0)} °C")
        memoria.append(f"  Velocidad viento: {estado_data.get('viento_velocidad', 0)} m/s")
        memoria.append(f"  Espesor hielo: {estado_data.get('espesor_hielo', 0)} m")
    memoria.append("")
    
    # Parámetros de viento
    memoria.append("1.5 PARÁMETROS DE VIENTO AEA 95301")
    memoria.append(f"Exposición: {parametros_viento.get('exposicion', 'C')}")
    memoria.append(f"Clase de línea: {parametros_viento.get('clase', 'B')}")
    memoria.append(f"Altura efectiva: Zc = {parametros_viento.get('Zc', 10.0)} m")
    memoria.append(f"Coeficiente de fuerza: Cf = {parametros_viento.get('Cf', 1.0)}")
    memoria.append(f"Longitud de vano: L_vano = {parametros_viento.get('L_vano', 400.0)} m")
    memoria.append("")
    
    # Restricciones
    memoria.append("1.6 RESTRICCIONES")
    for tipo_cable, rest_data in restricciones.items():
        memoria.append(f"{tipo_cable.capitalize()}:")
        for estado, porcentaje in rest_data.get('tension_max_porcentaje', {}).items():
            memoria.append(f"  Estado {estado}: Tensión máxima = {porcentaje*100:.1f}% de rotura")
    memoria.append("")
    
    # Objetivo de optimización
    memoria.append("1.7 OBJETIVO DE OPTIMIZACIÓN")
    memoria.append(f"Objetivo: {objetivo}")
    if objetivo == "FlechaMin":
        memoria.append("Minimizar flecha hasta alcanzar tensión máxima permitida")
    else:
        memoria.append("Minimizar tiro hasta alcanzar flecha máxima permitida")
    memoria.append("")
    
    # SECCIÓN 2: ECUACIONES Y MÉTODOS
    memoria.append("2. ECUACIONES Y MÉTODOS")
    memoria.append("-" * 50)
    memoria.append("")
    
    # Ecuación de cambio de estado
    memoria.append("2.1 ECUACIÓN DE CAMBIO DE ESTADO")
    memoria.append("Para el cambio de estado entre dos condiciones climáticas:")
    memoria.append("t³ + A·t² + B = 0")
    memoria.append("")
    memoria.append("Donde:")
    memoria.append("t = tensión en el estado final [daN/mm²]")
    memoria.append("A = coeficiente función de propiedades del cable y estados")
    memoria.append("B = coeficiente función de propiedades del cable y estados")
    memoria.append("")
    
    # Método de resolución
    memoria.append("2.2 MÉTODO DE RESOLUCIÓN")
    memoria.append("Ecuación cúbica resuelta por método Newton-Raphson")
    memoria.append("f(t) = t³ + A·t² + B")
    memoria.append("f'(t) = 3t² + 2A·t")
    memoria.append("t_{n+1} = t_n - f(t_n)/f'(t_n)")
    memoria.append("")
    
    # Carga de peso
    memoria.append("2.3 CARGA DE PESO")
    memoria.append("Peso del cable: p = peso_unitario [daN/m]")
    memoria.append("Peso del hielo: p_hielo = ρ_hielo × g × π × (r_ext² - r_int²) / 10")
    memoria.append("Donde:")
    memoria.append("  ρ_hielo = 900 kg/m³")
    memoria.append("  g = 9.81 m/s²")
    memoria.append("  r_ext = radio cable + espesor hielo")
    memoria.append("  r_int = radio cable")
    memoria.append("Peso total: p_total = p + p_hielo")
    memoria.append("")
    
    # Carga de viento AEA 95301
    memoria.append("2.4 CARGA DE VIENTO AEA 95301")
    memoria.extend(_generar_detalle_viento_aea(cable_aea, parametros_viento))
    memoria.append("")
    
    # Carga vectorial
    memoria.append("2.5 CARGA VECTORIAL")
    memoria.append("G = √(peso_total² + viento²)")
    memoria.append("")
    
    # Flecha
    memoria.append("2.6 FLECHA")
    memoria.append("f = (G × L²) / (8 × T)")
    memoria.append("Donde:")
    memoria.append("  G = carga vectorial [daN/m]")
    memoria.append("  L = longitud de vano [m]")
    memoria.append("  T = tiro horizontal [daN]")
    memoria.append("")
    
    # SECCIÓN 3: PROCESO DE OPTIMIZACIÓN
    memoria.append("3. PROCESO DE OPTIMIZACIÓN")
    memoria.append("-" * 50)
    memoria.append("")
    
    memoria.append("3.1 ESTADO BÁSICO INICIAL")
    memoria.append(f"Estado básico: {list(estados_climaticos.keys())[0]}")
    memoria.append("Iteración hasta convergencia de todos los estados")
    memoria.append("")
    
    memoria.append("3.2 BÚSQUEDA INCREMENTAL")
    if objetivo == "FlechaMin":
        memoria.append("Incrementar tensión hasta alcanzar restricción")
    else:
        memoria.append("Decrementar tensión hasta alcanzar restricción")
    memoria.append("")
    
    memoria.append("3.3 VERIFICACIÓN DE RESTRICCIONES")
    memoria.append("Por cada estado climático:")
    memoria.append("- Verificar tensión máxima")
    memoria.append("- Verificar flecha máxima (si aplica)")
    memoria.append("")
    
    memoria.append("3.4 AJUSTE FINO")
    memoria.append("Fases de refinamiento:")
    memoria.append("- Fase 1: 1% de precisión")
    memoria.append("- Fase 2: 0.1% de precisión")
    memoria.append("- Fase 3: 0.01% de precisión")
    memoria.append("")
    
    # SECCIÓN 4: CÁLCULOS POR ESTADO
    memoria.append("4. CÁLCULOS POR ESTADO")
    memoria.append("-" * 50)
    memoria.append("")
    
    for estado_id, estado_data in estados_climaticos.items():
        memoria.extend(_generar_calculo_estado(cable_aea, estado_id, estado_data, 
                                             parametros_viento, resultados_finales))
        memoria.append("")
    
    # SECCIÓN 5: RESULTADOS FINALES
    memoria.append("5. RESULTADOS FINALES")
    memoria.append("-" * 50)
    memoria.append("")
    
    # Tabla resumen
    memoria.append("5.1 TABLA RESUMEN")
    memoria.append("Estado | Temp[°C] | Viento[m/s] | Tensión[daN/mm²] | Tiro[daN] | Flecha[m] | %Rotura")
    memoria.append("-" * 85)
    
    for estado_id, resultado in resultados_finales.items():
        estado_data = estados_climaticos.get(estado_id, {})
        temp = estado_data.get('temperatura', 0)
        viento = estado_data.get('viento_velocidad', 0)
        tension = resultado.get('tension', 0)
        tiro = resultado.get('tiro', 0)
        flecha = resultado.get('flecha', 0)
        porcentaje = (tension / cable_aea.tension_rotura_dan_mm2) * 100 if cable_aea.tension_rotura_dan_mm2 > 0 else 0
        
        memoria.append(f"{estado_id:^6} | {temp:^8.1f} | {viento:^11.2f} | {tension:^16.2f} | {tiro:^9.1f} | {flecha:^9.3f} | {porcentaje:^7.1f}")
    
    memoria.append("")
    
    # Estado limitante
    memoria.append("5.2 ESTADO LIMITANTE")
    memoria.append(f"Estado que determina la solución: {estado_limitante}")
    memoria.append("")
    
    # Tensión optimizada
    memoria.append("5.3 TENSIÓN OPTIMIZADA")
    memoria.append(f"Tensión final: {t_final:.3f} daN/mm²")
    memoria.append(f"Temperatura estado básico: {q0_final:.1f} °C")
    memoria.append("")
    
    # Verificación restricciones
    memoria.append("5.4 VERIFICACIÓN DE RESTRICCIONES")
    for estado_id, resultado in resultados_finales.items():
        tension = resultado.get('tension', 0)
        porcentaje = (tension / cable_aea.tension_rotura_dan_mm2) * 100 if cable_aea.tension_rotura_dan_mm2 > 0 else 0
        
        # Obtener restricción para este estado
        restriccion_pct = 25.0  # Default
        for tipo_cable, rest_data in restricciones.items():
            if estado_id in rest_data.get('tension_max_porcentaje', {}):
                restriccion_pct = rest_data['tension_max_porcentaje'][estado_id] * 100
                break
        
        cumple = "✓" if porcentaje <= restriccion_pct else "✗"
        memoria.append(f"Estado {estado_id}: {porcentaje:.1f}% ≤ {restriccion_pct:.1f}% {cumple}")
    
    memoria.append("")
    memoria.append("=" * 80)
    memoria.append("FIN DE MEMORIA DE CÁLCULO")
    memoria.append("=" * 80)
    
    return "\n".join(memoria)


def _generar_tabla_propiedades_cable(cable_aea):
    """Genera tabla formateada de propiedades del cable"""
    props = cable_aea.propiedades
    
    # Mapeo de propiedades a formato tabla
    propiedades_tabla = [
        ("Sección nominal", "Sn", props.get("seccion_nominal", "-"), "mm²"),
        ("Sección total", "S", f"{cable_aea.seccion_mm2:.1f}", "mm²"),
        ("Diámetro total", "d", f"{cable_aea.diametro_m*1000:.1f}", "mm"),
        ("Peso unitario", "p", f"{cable_aea.peso_unitario_dan_m:.3f}", "daN/m"),
        ("Carga rotura mínima", "Pr", f"{cable_aea.carga_rotura_dan:.1f}", "daN"),
        ("Tensión rotura mínima", "σr", f"{cable_aea.carga_rotura_dan/cable_aea.seccion_mm2:.1f}", "daN/mm²"),
        ("Módulo elasticidad", "E", f"{cable_aea.modulo_elasticidad_dan_mm2:.2f}", "daN/mm²"),
        ("Coeficiente dilatación", "α", f"{cable_aea.coeficiente_dilatacion:.2e}", "1/°C"),
        ("Norma fabricación", "-", props.get("norma_fabricacion", "-"), "-")
    ]
    
    # Formatear tabla
    tabla = []
    tabla.append("Parámetro                    | Símbolo | Valor      | Unidad")
    tabla.append("-" * 60)
    
    for parametro, simbolo, valor, unidad in propiedades_tabla:
        tabla.append(f"{parametro:<28} | {simbolo:<7} | {valor:<10} | {unidad}")
    
    return tabla


def _generar_detalle_viento_aea(cable_aea, parametros_viento):
    """Genera detalle completo del cálculo de viento AEA 95301"""
    detalle = []
    
    exp = parametros_viento.get("exposicion", "C")
    clase = parametros_viento.get("clase", "B")
    Zc = parametros_viento.get("Zc", 10.0)
    Cf = parametros_viento.get("Cf", 1.0)
    L_vano = parametros_viento.get("L_vano", 400.0)
    
    # Obtener parámetros de exposición
    expo = cable_aea.EXPOSICIONES[exp]
    alpha_expo = expo["alpha"]
    k = expo["k"]
    Ls = expo["Ls"]
    Zs = expo["Zs"]
    Fc = cable_aea.CLASES_LINEA[clase]["Fc"]
    
    detalle.append("Fórmula general AEA 95301:")
    detalle.append("Fu = Q × (Zp × V)² × Fc × Gw × Cf × d_eff × sin(φ)")
    detalle.append("")
    detalle.append("Donde:")
    detalle.append("Q = 0.613 N·s²/m⁴ (presión dinámica base)")
    detalle.append("Zp = factor de altura")
    detalle.append("V = velocidad del viento [m/s]")
    detalle.append("Fc = factor de clase de línea")
    detalle.append("Gw = factor de ráfaga para cables")
    detalle.append("Cf = coeficiente de fuerza")
    detalle.append("d_eff = diámetro efectivo [m]")
    detalle.append("sin(φ) = factor angular (= 1.0 para cables)")
    detalle.append("")
    
    detalle.append(f"Parámetros de exposición {exp}:")
    detalle.append(f"α = {alpha_expo}")
    detalle.append(f"k = {k}")
    detalle.append(f"Ls = {Ls} m")
    detalle.append(f"Zs = {Zs} m")
    detalle.append("")
    
    detalle.append(f"Factor de clase {clase}:")
    detalle.append(f"Fc = {Fc}")
    detalle.append("")
    
    detalle.append("Factor de altura:")
    detalle.append("Zp = 1.61 × (Zc/Zs)^(1/α)")
    detalle.append(f"   = 1.61 × ({Zc}/{Zs})^(1/{alpha_expo})")
    Zp = cable_aea._factor_Zp(Zc, Zs, alpha_expo)
    detalle.append(f"   = {Zp:.3f}")
    detalle.append("")
    
    detalle.append("Factor de ráfaga para cables:")
    detalle.append("E = 4.9 × √k × (10/Zc)^(1/α)")
    E = 4.9 * (k**0.5) * ((10/Zc)**(1/alpha_expo))
    detalle.append(f"  = 4.9 × √{k} × (10/{Zc})^(1/{alpha_expo})")
    detalle.append(f"  = {E:.3f}")
    detalle.append("")
    
    detalle.append("Bw = 1 / (1 + 0.8 × (L_vano/Ls))")
    Bw = 1 / (1 + 0.8 * (L_vano/Ls))
    detalle.append(f"   = 1 / (1 + 0.8 × ({L_vano}/{Ls}))")
    detalle.append(f"   = {Bw:.3f}")
    detalle.append("")
    
    detalle.append("Gw = (1 + 2.7 × E × √Bw) / kv²")
    detalle.append("kv = 1.425 (factor de conversión)")
    Gw = (1 + 2.7 * E * (Bw**0.5)) / (1.425**2)
    detalle.append(f"   = (1 + 2.7 × {E:.3f} × √{Bw:.3f}) / 1.425²")
    detalle.append(f"   = {Gw:.3f}")
    detalle.append("")
    
    return detalle


def _generar_calculo_estado(cable_aea, estado_id, estado_data, parametros_viento, resultados_finales):
    """Genera cálculo detallado para un estado específico"""
    detalle = []
    
    detalle.append(f"4.{estado_id} ESTADO {estado_id}: {estado_data.get('descripcion', 'N/A')}")
    detalle.append("-" * 40)
    
    # Condiciones
    temp = estado_data.get('temperatura', 0)
    viento = estado_data.get('viento_velocidad', 0)
    hielo = estado_data.get('espesor_hielo', 0)
    
    detalle.append("Condiciones:")
    detalle.append(f"Temperatura: {temp} °C")
    detalle.append(f"Velocidad viento: {viento} m/s")
    detalle.append(f"Espesor hielo: {hielo} m")
    detalle.append("")
    
    # Cargas aplicadas
    detalle.append("Cargas aplicadas:")
    
    # Peso cable
    peso_cable = cable_aea.peso_unitario_dan_m
    detalle.append(f"Peso cable: p = {peso_cable:.3f} daN/m")
    
    # Peso hielo
    peso_hielo = 0
    if hielo > 0:
        r_cable = cable_aea.diametro_m / 2
        r_ext = r_cable + hielo
        peso_hielo = 900 * 9.81 * 3.14159 * (r_ext**2 - r_cable**2) / 10
        detalle.append(f"Peso hielo: p_hielo = 900 × 9.81 × π × ({r_ext:.4f}² - {r_cable:.4f}²) / 10")
        detalle.append(f"                   = {peso_hielo:.3f} daN/m")
    
    peso_total = peso_cable + peso_hielo
    detalle.append(f"Peso total: p_total = {peso_total:.3f} daN/m")
    detalle.append("")
    
    # Carga viento
    if viento > 0:
        detalle.append("Carga viento (AEA 95301):")
        detalle.extend(_generar_detalle_calculo_viento_estado(cable_aea, parametros_viento, estado_data))
        
        # Calcular viento
        Fu = cable_aea.cargaViento(viento, hielo, parametros_viento.get('Zc', 10.0), 
                                  parametros_viento.get('exposicion', 'C'),
                                  parametros_viento.get('clase', 'B'),
                                  parametros_viento.get('Cf', 1.0),
                                  parametros_viento.get('L_vano', 400.0))
        detalle.append(f"Resultado: Fu = {Fu:.3f} daN/m")
    else:
        Fu = 0
        detalle.append("Sin viento: Fu = 0 daN/m")
    
    detalle.append("")
    
    # Carga vectorial
    G = (peso_total**2 + Fu**2)**0.5
    detalle.append("Carga vectorial:")
    detalle.append(f"G = √(peso_total² + viento²)")
    detalle.append(f"  = √({peso_total:.3f}² + {Fu:.3f}²)")
    detalle.append(f"  = {G:.3f} daN/m")
    detalle.append("")
    
    # Resultados del estado
    if estado_id in resultados_finales:
        resultado = resultados_finales[estado_id]
        tension = resultado.get('tension', 0)
        tiro = resultado.get('tiro', 0)
        flecha = resultado.get('flecha', 0)
        
        detalle.append("Resultados:")
        detalle.append(f"Tensión: σ = {tension:.3f} daN/mm²")
        detalle.append(f"Tiro: T = {tiro:.1f} daN")
        detalle.append(f"Flecha: f = {flecha:.3f} m")
        
        # Porcentaje de rotura
        porcentaje = (tension / cable_aea.tension_rotura_dan_mm2) * 100 if cable_aea.tension_rotura_dan_mm2 > 0 else 0
        detalle.append(f"% Rotura: {porcentaje:.1f}%")
    
    return detalle


def _generar_detalle_calculo_viento_estado(cable_aea, parametros_viento, estado_data):
    """Genera detalle específico del cálculo de viento para un estado"""
    V = estado_data.get("viento_velocidad", 0)
    if V == 0:
        return ["Sin viento (V = 0 m/s)"]
    
    exp = parametros_viento.get("exposicion", "C")
    clase = parametros_viento.get("clase", "B")
    Zc = parametros_viento.get("Zc", 10.0)
    Cf = parametros_viento.get("Cf", 1.0)
    L_vano = parametros_viento.get("L_vano", 400.0)
    
    # Obtener parámetros de exposición
    expo = cable_aea.EXPOSICIONES[exp]
    alpha_expo = expo["alpha"]
    k = expo["k"]
    Ls = expo["Ls"]
    Zs = expo["Zs"]
    Fc = cable_aea.CLASES_LINEA[clase]["Fc"]
    
    # Calcular factores
    Zp = cable_aea._factor_Zp(Zc, Zs, alpha_expo)
    G, E, B = cable_aea._factor_Gw(Zc, alpha_expo, k, Ls, L_vano)
    
    # Diámetro efectivo
    espesor_hielo = estado_data.get("espesor_hielo", 0)
    d_eff = cable_aea.diametro_equivalente(espesor_hielo)
    
    detalle = []
    detalle.append(f"V = {V} m/s")
    detalle.append(f"Zp = {Zp:.3f}")
    detalle.append(f"Fc = {Fc}")
    detalle.append(f"Gw = {G:.3f}")
    detalle.append(f"Cf = {Cf}")
    detalle.append(f"d_eff = {d_eff*1000:.1f} mm")
    detalle.append("")
    detalle.append("Fu = 0.613 × (Zp × V)² × Fc × Gw × Cf × d_eff × sin(φ)")
    detalle.append(f"   = 0.613 × ({Zp:.3f} × {V})² × {Fc} × {G:.3f} × {Cf} × {d_eff:.4f} × 1.0")
    
    # Calcular resultado
    Fu = 0.613 * (Zp * V)**2 * Fc * G * Cf * d_eff * 1.0 * 0.1  # Convertir a daN/m
    detalle.append(f"   = {Fu:.3f} daN/m")
    
    return detalle