"""
Módulo para generar memoria de cálculo del Cálculo Mecánico de Cables (CMC)
"""

import math


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
        t_final: Tensión final optimizada (daN/mm²)
        q0_final: Temperatura del estado básico (°C)
        estado_limitante: Estado que limita la optimización
    
    Returns:
        str: Texto formateado con la memoria de cálculo
    """
    
    lineas = []
    
    # ENCABEZADO
    lineas.append("=" * 80)
    lineas.append("CALCULO MECANICO DE CABLES - METODO AEA 95301")
    lineas.append("=" * 80)
    lineas.append("")
    
    # SECCIÓN 1: DATOS DE ENTRADA
    lineas.append("DATOS DE ENTRADA")
    lineas.append("-" * 80)
    lineas.append(f"Cable: {cable_aea.nombre}")
    lineas.append(f"Tipo: {cable_aea.tipocable}")
    lineas.append(f"Material: {cable_aea.propiedades.get('material', 'N/A')}")
    lineas.append("")
    
    # Tabla de propiedades
    lineas.append("PROPIEDADES DEL CABLE")
    lineas.append("-" * 80)
    lineas.extend(_generar_tabla_propiedades_cable(cable_aea))
    lineas.append("")
    
    # Parámetros de cálculo
    lineas.append("PARAMETROS DE CALCULO")
    lineas.append("-" * 80)
    lineas.append(f"Vano regulador: {vano:.1f} m")
    lineas.append(f"Objetivo optimización: {objetivo}")
    lineas.append("")
    
    # Estados climáticos
    lineas.append("Estados climáticos:")
    for estado_id, datos in estados_climaticos.items():
        viento_str = f"{datos.get('viento_velocidad', 0)*3.6:.0f} km/h" if datos.get('viento_velocidad', 0) > 0 else "sin viento"
        hielo_str = f"{datos.get('espesor_hielo', 0)*1000:.0f}mm hielo" if datos.get('espesor_hielo', 0) > 0 else "sin hielo"
        lineas.append(f"  {estado_id} - {datos['descripcion']} ({datos['temperatura']}°C, {viento_str}, {hielo_str})")
    lineas.append("")
    
    # Restricciones
    lineas.append("Restricciones de tensión:")
    for estado_id in estados_climaticos.keys():
        tension_max_porc = restricciones.get("tension_max_porcentaje", {}).get(estado_id, 0.40)
        T_max = tension_max_porc * cable_aea.carga_rotura_dan
        lineas.append(f"  Estado {estado_id}: {tension_max_porc*100:.0f}% de rotura ({T_max:.1f} daN)")
    
    if "relflecha_max" in restricciones:
        lineas.append(f"  Relación flecha máxima: {restricciones['relflecha_max']}")
    lineas.append("")
    
    # Parámetros de viento
    lineas.append("Parámetros de viento:")
    lineas.append(f"  Exposición: {parametros_viento.get('exposicion', 'N/A')}")
    clase = parametros_viento.get('clase', 'N/A')
    Fc = cable_aea.CLASES_LINEA.get(clase, {}).get('Fc', 'N/A')
    lineas.append(f"  Clase de línea: {clase} (Fc = {Fc})")
    lineas.append(f"  Altura efectiva: {parametros_viento.get('Zc', 'N/A')} m")
    lineas.append(f"  Coeficiente de fuerza: {parametros_viento.get('Cf', 'N/A')}")
    lineas.append("")
    
    # SECCIÓN 2: ECUACIONES Y MÉTODOS
    lineas.append("ECUACIONES Y METODOS")
    lineas.append("-" * 80)
    lineas.append("Ecuación de cambio de estado:")
    lineas.append("  t³ + A·t² + B = 0")
    lineas.append("")
    lineas.append("Donde:")
    lineas.append("  A = (L²·E·Go²)/(24·t0²·S²) + α·E·(q-q0) - t0")
    lineas.append("  B = -(L²·E·G²)/(24·S²)")
    lineas.append("")
    lineas.append("Valores:")
    lineas.append(f"  L = {vano:.1f} m")
    lineas.append(f"  E = {cable_aea.modulo_elasticidad_dan_mm2:.1f} daN/mm²")
    lineas.append(f"  S = {cable_aea.seccion_mm2:.1f} mm²")
    lineas.append(f"  α = {cable_aea.coeficiente_dilatacion:.2e} 1/°C")
    lineas.append("")
    lineas.append("Método de resolución: Newton-Raphson para ecuación cúbica")
    lineas.append("Carga vectorial: G = √(peso² + viento²)")
    lineas.append("Flecha: f = (G × L²) / (8 × T)")
    lineas.append("")
    
    # SECCIÓN 3: PROCESO DE OPTIMIZACIÓN
    lineas.append("PROCESO DE OPTIMIZACION")
    lineas.append("-" * 80)
    
    if objetivo == 'FlechaMin':
        t_inicial = 0.01 * cable_aea.carga_rotura_dan / cable_aea.seccion_mm2
        lineas.append("Objetivo: FlechaMin (minimizar flecha, aumentar tensión)")
        lineas.append(f"Tensión inicial: {t_inicial:.3f} daN/mm² (1% de rotura)")
        lineas.append("Búsqueda incremental: pasos de 1% hasta violación")
    else:
        t_inicial = 0.70 * cable_aea.carga_rotura_dan / cable_aea.seccion_mm2
        lineas.append("Objetivo: TiroMin (minimizar tiro, disminuir tensión)")
        lineas.append(f"Tensión inicial: {t_inicial:.3f} daN/mm² (70% de rotura)")
        lineas.append("Búsqueda incremental: pasos de 1% hasta violación")
    
    lineas.append("")
    lineas.append("Ajuste fino triple:")
    lineas.append("  Fase 1: Saltos del 1% hasta violación")
    lineas.append("  Fase 2: Saltos del 0.1% hasta violación")
    lineas.append("  Fase 3: Saltos del 0.01% hasta violación")
    lineas.append("")
    
    # Encontrar estado básico
    estado_basico_id = None
    for estado_id, res in resultados_finales.items():
        if abs(res['temperatura_C'] - q0_final) < 0.1:
            estado_basico_id = estado_id
            break
    
    if estado_basico_id:
        lineas.append(f"Estado básico final: Estado {estado_basico_id} ({estados_climaticos[estado_basico_id]['descripcion']}, {q0_final}°C)")
    else:
        lineas.append(f"Estado básico final: Temperatura {q0_final}°C")
    
    lineas.append(f"Tensión optimizada: {t_final:.2f} daN/mm²")
    lineas.append("")
    
    # SECCIÓN 4: CÁLCULOS POR ESTADO
    lineas.append("CALCULOS POR ESTADO CLIMATICO")
    lineas.append("-" * 80)
    
    for estado_id, res in resultados_finales.items():
        estado_data = estados_climaticos[estado_id]
        
        lineas.append(f"Estado {estado_id} ({estado_data['descripcion']} - {res['temperatura_C']}°C):")
        lineas.append(f"  Carga peso: {cable_aea.peso_unitario_dan_m:.3f} daN/m")
        lineas.append(f"  Carga hielo: {res.get('peso_hielo_daN_m', 0):.3f} daN/m")
        lineas.append(f"  Carga viento: {res.get('carga_viento_daN_m', 0):.3f} daN/m")
        lineas.append(f"  Carga vectorial: {res['carga_unitaria_daN_m']:.3f} daN/m")
        lineas.append("")
        
        # Calcular coeficientes A y B para este estado
        E = cable_aea.modulo_elasticidad_dan_mm2
        S = cable_aea.seccion_mm2
        alfa = cable_aea.coeficiente_dilatacion
        L = vano
        
        # Go (carga estado básico - sin viento ni hielo)
        Go = cable_aea.peso_unitario_dan_m
        G = res['carga_unitaria_daN_m']
        t0 = t_final
        q = res['temperatura_C']
        q0 = q0_final
        
        A = (L**2 * E * Go**2) / (24 * t0**2 * S**2) + alfa * E * (q - q0) - t0
        B = -(L**2 * E * G**2) / (24 * S**2)
        
        lineas.append("  Ecuación cúbica: t³ + A·t² + B = 0")
        lineas.append(f"    A = {A:.2f}")
        lineas.append(f"    B = {B:.2f}")
        lineas.append("")
        
        lineas.append(f"  Tensión: {res['tension_daN_mm2']:.2f} daN/mm²")
        lineas.append(f"  Tiro: {res['tiro_daN']:.1f} daN")
        lineas.append(f"  Flecha vertical: {res['flecha_vertical_m']:.2f} m")
        lineas.append(f"  Flecha resultante: {res['flecha_resultante_m']:.2f} m")
        
        # Marcar estado limitante
        if estado_id == estado_limitante:
            lineas.append(f"  % rotura: {res['porcentaje_rotura']:.1f}% 🟡 LÍMITE")
        else:
            lineas.append(f"  % rotura: {res['porcentaje_rotura']:.1f}%")
        
        lineas.append("")
    
    # SECCIÓN 5: RESULTADOS FINALES
    lineas.append("RESULTADOS FINALES")
    lineas.append("-" * 80)
    
    if estado_limitante and estado_limitante not in ["Límite mínimo físico", "Límite máximo físico"]:
        tipo_restriccion = "restricción de tensión"
        if "relflecha" in str(estado_limitante).lower():
            tipo_restriccion = "restricción de relación de flecha"
        lineas.append(f"Estado limitante: Estado {estado_limitante} ({tipo_restriccion})")
    elif estado_limitante:
        lineas.append(f"Estado limitante: {estado_limitante}")
    else:
        lineas.append("Estado limitante: Ninguno (solución sin violaciones)")
    
    lineas.append(f"Tensión final: {t_final:.2f} daN/mm²")
    T_final = t_final * cable_aea.seccion_mm2
    lineas.append(f"Tiro final: {T_final:.1f} daN")
    
    if estado_basico_id:
        lineas.append(f"Estado básico: Estado {estado_basico_id} ({q0_final}°C)")
    else:
        lineas.append(f"Estado básico: Temperatura {q0_final}°C")
    
    lineas.append("")
    lineas.append("Verificación restricciones:")
    
    for estado_id, res in resultados_finales.items():
        tension_max_porc = restricciones.get("tension_max_porcentaje", {}).get(estado_id, 0.40)
        porc_rotura_actual = res['porcentaje_rotura'] / 100.0
        
        if estado_id == estado_limitante:
            simbolo = "🟡"
            estado_str = "LÍMITE"
        elif porc_rotura_actual <= tension_max_porc:
            simbolo = "✓"
            estado_str = "OK"
        else:
            simbolo = "✗"
            estado_str = "VIOLADO"
        
        lineas.append(f"{simbolo} Estado {estado_id}: {res['porcentaje_rotura']:.1f}% vs {tension_max_porc*100:.0f}% ({estado_str})")
    
    lineas.append("")
    lineas.append("=" * 80)
    
    return "\n".join(lineas)


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
        ("Módulo elasticidad", "E", f"{cable_aea.modulo_elasticidad_dan_mm2:.1f}", "daN/mm²"),
        ("Coeficiente dilatación", "α", f"{cable_aea.coeficiente_dilatacion:.2e}", "1/°C"),
        ("Norma fabricación", "-", props.get("norma_fabricacion", "-"), "-")
    ]
    
    # Formatear tabla
    tabla = []
    tabla.append("Parámetro                    | Símbolo | Valor      | Unidad")
    tabla.append("-" * 80)
    
    for parametro, simbolo, valor, unidad in propiedades_tabla:
        tabla.append(f"{parametro:<28} | {simbolo:<7} | {valor:<10} | {unidad}")
    
    return tabla
