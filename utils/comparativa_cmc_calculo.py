"""
Lógica de cálculo para comparativa CMC
Usa el flujo real de CMC: crear objetos, ejecutar cálculo mecánico, generar gráficos
"""

import pandas as pd
from utils.calculo_mecanico_cables import CalculoMecanicoCables
from utils.calculo_objetos import CalculoObjetosAEA
from utils.plot_flechas import crear_grafico_flechas
import json
import time
from config.app_config import DATA_DIR

def ejecutar_comparativa_cmc(comparativa_data):
    """
    Ejecutar cálculo CMC real para múltiples cables usando el flujo completo de CMC
    """
    
    cables_seleccionados = comparativa_data.get("cables_seleccionados", [])
    parametros = comparativa_data.get("parametros_linea", {})
    config = comparativa_data.get("configuracion_calculo", {})
    estados = comparativa_data.get("estados_climaticos", {})
    
    if not cables_seleccionados:
        raise ValueError("No hay cables seleccionados")
    
    resultados = {}
    
    for cable_nombre in cables_seleccionados:
        try:
            print(f"🔄 Calculando {cable_nombre}...")
            inicio = time.time()
            
            # Crear estructura temporal para este cable
            estructura_temp = crear_estructura_temporal_real(cable_nombre, parametros, config, estados)
            
            # Ejecutar cálculo CMC solo conductor
            resultado_cable = ejecutar_cmc_solo_conductor_para_cable(estructura_temp, cable_nombre)
            
            tiempo_calculo = time.time() - inicio
            resultado_cable["tiempo_calculo"] = tiempo_calculo
            
            resultados[cable_nombre] = resultado_cable
            print(f"✅ Cálculo completado para {cable_nombre} en {tiempo_calculo:.1f}s")
            
        except Exception as e:
            print(f"❌ Error calculando {cable_nombre}: {e}")
            resultados[cable_nombre] = {"error": str(e), "convergencia": False}
    
    return resultados

def crear_estructura_temporal_real(cable_nombre, parametros, config, estados):
    """Crear estructura temporal usando el formato real de CMC"""
    
    estructura = {
        "TITULO": f"Comparativa_{cable_nombre}",
        "cable_conductor_id": cable_nombre,
        
        # Parámetros de línea (desde vista)
        "L_vano": parametros.get("L_vano", 150),
        "theta": parametros.get("theta", 0),
        "alpha": 0,
        "Vmax": parametros.get("Vmax", 38.9),
        "Vmed": parametros.get("Vmed", 15.56),
        "t_hielo": parametros.get("t_hielo", 0),
        
        # Configuración de cálculo (desde vista)
        "VANO_DESNIVELADO": config.get("VANO_DESNIVELADO", True),
        "H_PIQANTERIOR": config.get("H_PIQANTERIOR", 0),
        "H_PIQPOSTERIOR": config.get("H_PIQPOSTERIOR", 0),
        "SALTO_PORCENTUAL": config.get("SALTO_PORCENTUAL", 0.05),
        "PASO_AFINADO": config.get("PASO_AFINADO", 0.01),
        "OBJ_CONDUCTOR": config.get("OBJ_CONDUCTOR", "FlechaMin"),
        "RELFLECHA_SIN_VIENTO": config.get("RELFLECHA_SIN_VIENTO", True),
        
        # Parámetros de viento (desde vista - solo conductor)
        "exposicion": parametros.get("exposicion", "C"),
        "clase": parametros.get("clase", "C"),
        "Zco": parametros.get("Zco", 13.0),
        "Cf_cable": parametros.get("Cf_cable", 1.0),
        
        # Estados climáticos
        "estados_climaticos": estados,
        
        # Valores por defecto
        "TENSION": 220,
        "Zona_climatica": "D",
        "TIPO_ESTRUCTURA": "Comparativa CMC"
    }
    
    return estructura

def ejecutar_cmc_solo_conductor_para_cable(estructura, cable_nombre):
    """Ejecutar cálculo CMC solo para conductor (sin guardia)"""
    
    try:
        print(f"  🔧 Creando objeto conductor para {cable_nombre}...")
        
        # 1. Crear objetos conductor solamente
        calculo_objetos = CalculoObjetosAEA()
        resultado_objetos = calculo_objetos.crear_cable_conductor(estructura)
        
        if not resultado_objetos["exito"]:
            return {"error": resultado_objetos["mensaje"], "convergencia": False}
        
        print(f"  📊 Ejecutando cálculo mecánico solo conductor para {cable_nombre}...")
        
        # 2. Crear calculadora mecánica solo para conductor
        from utils.calculo_cmc_solo_conductor import CalculoCMCSoloConductor
        calculo_mecanico = CalculoCMCSoloConductor(calculo_objetos)
        
        # 3. Preparar parámetros solo para conductor
        estados_climaticos = estructura["estados_climaticos"]
        
        # Restricciones solo para conductor
        restricciones = {
            "conductor": {"tension_max_porcentaje": {"I": 0.25, "II": 0.40, "III": 0.40, "IV": 0.40, "V": 0.25}}
        }
        
        params = {
            "L_vano": estructura["L_vano"],
            "alpha": estructura["alpha"],
            "theta": estructura["theta"],
            "Vmax": estructura["Vmax"],
            "Vmed": estructura["Vmed"],
            "t_hielo": estructura["t_hielo"],
            "exposicion": estructura["exposicion"],
            "clase": estructura["clase"],
            "Zco": estructura["Zco"],
            "Cf_cable": estructura["Cf_cable"],
            "SALTO_PORCENTUAL": estructura["SALTO_PORCENTUAL"],
            "PASO_AFINADO": estructura["PASO_AFINADO"],
            "OBJ_CONDUCTOR": estructura["OBJ_CONDUCTOR"],
            "RELFLECHA_SIN_VIENTO": estructura["RELFLECHA_SIN_VIENTO"],
            "VANO_DESNIVELADO": estructura["VANO_DESNIVELADO"],
            "H_PIQANTERIOR": estructura["H_PIQANTERIOR"],
            "H_PIQPOSTERIOR": estructura["H_PIQPOSTERIOR"]
        }
        
        # 4. Ejecutar cálculo solo conductor
        resultado_calculo = calculo_mecanico.calcular_solo_conductor(params, estados_climaticos, restricciones)
        
        if not resultado_calculo["exito"]:
            return {"error": resultado_calculo["mensaje"], "convergencia": False}
        
        print(f"  📈 Generando gráfico solo conductor para {cable_nombre}...")
        
        # 5. Generar solo gráfico de conductor
        graficos = {}
        try:
            if calculo_objetos.cable_conductor:
                from utils.plot_flechas import crear_grafico_flechas_solo_conductor
                fig_conductor = crear_grafico_flechas_solo_conductor(
                    calculo_objetos.cable_conductor,
                    params["L_vano"]
                )
                
                graficos = {
                    "Flecha Conductor": fig_conductor
                }
                    
        except Exception as e:
            print(f"  ⚠️ Error generando gráfico para {cable_nombre}: {e}")
        
        # 6. Retornar resultados solo conductor
        return {
            "cable": cable_nombre,
            "convergencia": True,
            "dataframe_html": calculo_mecanico.df_conductor.to_json(orient='split') if calculo_mecanico.df_conductor is not None else None,
            "graficos": graficos,
            "resultados_conductor": calculo_mecanico.resultados_conductor,
            "df_conductor": calculo_mecanico.df_conductor,
            "console_output": calculo_mecanico.console_output,
            "mensaje": f"Cálculo completado para {cable_nombre}"
        }
        
    except Exception as e:
        import traceback
        print(f"  ❌ Error detallado en {cable_nombre}: {traceback.format_exc()}")
        return {"error": str(e), "convergencia": False}

def obtener_estado_determinante(resultados_conductor):
    """Obtener el estado determinante (mayor porcentaje de rotura)"""
    if not resultados_conductor:
        return "IV"
    
    max_porcentaje = 0
    estado_determinante = "IV"
    
    for estado, resultado in resultados_conductor.items():
        porcentaje = resultado.get('porcentaje_rotura', 0)
        if porcentaje is not None and porcentaje > max_porcentaje:
            max_porcentaje = porcentaje
            estado_determinante = estado
    
    return str(estado_determinante)

def crear_grafico_comparativo(resultados):
    """Crear gráficos comparativos separados de flechas y tiros"""
    
    import plotly.graph_objects as go
    import pandas as pd
    import json
    
    # Estados ordenados: TMAX, TMA, VMAX, VMED, TMIN
    estados_orden = ["I", "V", "III", "IV", "II"]
    estados_nombres = {"I": "TMAX", "V": "TMA", "III": "VMAX", "IV": "VMED", "II": "TMIN"}
    
    # Gráfico de Flechas
    fig_flechas = go.Figure()
    
    # Gráfico de Tiros
    fig_tiros = go.Figure()
    
    for cable_nombre, resultado in resultados.items():
        if "error" in resultado or not resultado.get('dataframe_html'):
            print(f"Saltando {cable_nombre}: sin datos válidos")
            continue
            
        try:
            # Extraer datos reales del DataFrame
            df_data = json.loads(resultado['dataframe_html'])
            df = pd.DataFrame(df_data['data'], columns=df_data['columns'])
            
            print(f"Procesando {cable_nombre}: {len(df)} filas, columnas: {list(df.columns)}")
            
            flechas = []
            tiros = []
            
            for estado in estados_orden:
                # Buscar fila por descripción
                estado_row = None
                for idx, row in df.iterrows():
                    desc = str(row.get('Descrip.', '')).lower()
                    if ((estado == 'I' and 'tmáx' in desc) or 
                        (estado == 'V' and 'tma' in desc) or 
                        (estado == 'III' and 'vmáx' in desc) or 
                        (estado == 'IV' and 'vmed' in desc) or 
                        (estado == 'II' and 'tmín' in desc)):
                        estado_row = row
                        break
                
                if estado_row is not None:
                    # Extraer flecha
                    flecha = 0
                    for col in df.columns:
                        if 'Flecha' in str(col) and ('m]' in str(col) or 'Vertical' in str(col)):
                            val = estado_row[col]
                            flecha = float(val) if val is not None and not pd.isna(val) else 0
                            break
                    
                    # Extraer tiro
                    tiro = 0
                    for col in df.columns:
                        if 'Tiro' in str(col) and 'daN' in str(col):
                            val = estado_row[col]
                            tiro = float(val) if val is not None and not pd.isna(val) else 0
                            break
                    
                    flechas.append(flecha)
                    tiros.append(tiro)
                    print(f"  {estado} ({estados_nombres[estado]}): Flecha={flecha:.3f}m, Tiro={tiro:.0f}daN")
                else:
                    flechas.append(0)
                    tiros.append(0)
                    print(f"  {estado} ({estados_nombres[estado]}): NO ENCONTRADO")
            
            # Estados para eje X
            estados_x = [estados_nombres[e] for e in estados_orden]
            
            # Agregar a gráfico de flechas
            fig_flechas.add_trace(
                go.Scatter(x=estados_x, y=flechas, name=cable_nombre, 
                          line=dict(width=3), mode='lines+markers', marker=dict(size=8),
                          hovertemplate=f"{cable_nombre}<br>Estado: %{{x}}<br>Flecha: %{{y:.3f}} m<extra></extra>")
            )
            
            # Agregar a gráfico de tiros
            fig_tiros.add_trace(
                go.Scatter(x=estados_x, y=tiros, name=cable_nombre,
                          line=dict(width=3), mode='lines+markers', marker=dict(size=8),
                          hovertemplate=f"{cable_nombre}<br>Estado: %{{x}}<br>Tiro: %{{y:.0f}} daN<extra></extra>")
            )
            
        except Exception as e:
            print(f"Error procesando {cable_nombre}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Configurar gráfico de flechas
    fig_flechas.update_layout(
        title="Comparativa de Flecha por Estado Climático",
        xaxis_title="Estados Climáticos",
        yaxis_title="Flecha (m)",
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    
    # Configurar gráfico de tiros
    fig_tiros.update_layout(
        title="Comparativa de Tiro por Estado Climático",
        xaxis_title="Estados Climáticos",
        yaxis_title="Tiro (daN)",
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    
    return fig_flechas, fig_tiros