# consultar_cargas_nodos.py
"""
Utilidades para consultar cargas aplicadas a nodos después de cálculos
"""
import pandas as pd


def consultar_cargas_nodo(estructura_geometria, nombre_nodo, hipotesis=None):
    """
    Consulta cargas de un nodo específico
    
    Args:
        estructura_geometria: Objeto EstructuraAEA_Geometria
        nombre_nodo (str): Nombre del nodo
        hipotesis (str/list, optional): Hipótesis específica(s) o None para todas
    
    Returns:
        dict: {hipotesis: {fx, fy, fz, mx, my, mz}}
    """
    if nombre_nodo not in estructura_geometria.nodos:
        return {}
    
    nodo = estructura_geometria.nodos[nombre_nodo]
    
    # Determinar hipótesis a consultar
    if hipotesis is None:
        hipotesis_list = nodo.listar_hipotesis()
    elif isinstance(hipotesis, str):
        hipotesis_list = [hipotesis]
    else:
        hipotesis_list = hipotesis
    
    resultados = {}
    for hip in hipotesis_list:
        cargas = nodo.obtener_cargas_hipotesis(hip)
        resultados[hip] = cargas
    
    return resultados


def consultar_cargas_todos_nodos(estructura_geometria, hipotesis=None):
    """
    Consulta cargas de todos los nodos
    
    Args:
        estructura_geometria: Objeto EstructuraAEA_Geometria
        hipotesis (str, optional): Hipótesis específica o None para todas
    
    Returns:
        dict: {nombre_nodo: {hipotesis: {fx, fy, fz, mx, my, mz}}}
    """
    resultados = {}
    for nombre_nodo in estructura_geometria.nodos.keys():
        cargas = consultar_cargas_nodo(estructura_geometria, nombre_nodo, hipotesis)
        if cargas:
            resultados[nombre_nodo] = cargas
    
    return resultados


def generar_tabla_cargas_nodo(estructura_geometria, nombre_nodo):
    """
    Genera DataFrame con cargas de un nodo
    
    Args:
        estructura_geometria: Objeto EstructuraAEA_Geometria
        nombre_nodo (str): Nombre del nodo
    
    Returns:
        pd.DataFrame: Tabla con cargas por hipótesis
    """
    cargas = consultar_cargas_nodo(estructura_geometria, nombre_nodo)
    
    if not cargas:
        return pd.DataFrame()
    
    datos = []
    for hip, valores in cargas.items():
        datos.append({
            "Hipótesis": hip,
            "Fx [daN]": round(valores["fx"], 2),
            "Fy [daN]": round(valores["fy"], 2),
            "Fz [daN]": round(valores["fz"], 2),
            "Mx [daN·m]": round(valores["mx"], 2),
            "My [daN·m]": round(valores["my"], 2),
            "Mz [daN·m]": round(valores["mz"], 2)
        })
    
    return pd.DataFrame(datos)


def generar_tabla_cargas_hipotesis(estructura_geometria, hipotesis):
    """
    Genera DataFrame con cargas de todos los nodos para una hipótesis
    
    Args:
        estructura_geometria: Objeto EstructuraAEA_Geometria
        hipotesis (str): Código de hipótesis
    
    Returns:
        pd.DataFrame: Tabla con cargas por nodo
    """
    datos = []
    for nombre_nodo, nodo in estructura_geometria.nodos.items():
        cargas = nodo.obtener_cargas_hipotesis(hipotesis)
        
        # Solo incluir nodos con cargas no nulas
        if any(abs(v) > 0.01 for v in [cargas["fx"], cargas["fy"], cargas["fz"]]):
            datos.append({
                "Nodo": nombre_nodo,
                "Tipo": nodo.tipo_nodo,
                "X [m]": round(nodo.x, 3),
                "Y [m]": round(nodo.y, 3),
                "Z [m]": round(nodo.z, 3),
                "Fx [daN]": round(cargas["fx"], 2),
                "Fy [daN]": round(cargas["fy"], 2),
                "Fz [daN]": round(cargas["fz"], 2),
                "Mx [daN·m]": round(cargas["mx"], 2),
                "My [daN·m]": round(cargas["my"], 2),
                "Mz [daN·m]": round(cargas["mz"], 2)
            })
    
    return pd.DataFrame(datos)


def imprimir_cargas_nodo(estructura_geometria, nombre_nodo):
    """
    Imprime cargas de un nodo en consola
    
    Args:
        estructura_geometria: Objeto EstructuraAEA_Geometria
        nombre_nodo (str): Nombre del nodo
    """
    if nombre_nodo not in estructura_geometria.nodos:
        print(f"Nodo '{nombre_nodo}' no encontrado")
        return
    
    nodo = estructura_geometria.nodos[nombre_nodo]
    print(f"\n{'='*80}")
    print(f"CARGAS DEL NODO: {nombre_nodo}")
    print(f"{'='*80}")
    print(f"Tipo: {nodo.tipo_nodo}")
    print(f"Coordenadas: ({nodo.x:.3f}, {nodo.y:.3f}, {nodo.z:.3f})")
    print(f"Cable: {nodo.cable_asociado.nombre if nodo.cable_asociado else 'Ninguno'}")
    print(f"Rotación Z: {nodo.rotacion_eje_z}°")
    print(f"\nHipótesis con cargas: {len(nodo.listar_hipotesis())}")
    print(f"{'='*80}\n")
    
    cargas = consultar_cargas_nodo(estructura_geometria, nombre_nodo)
    
    for hip, valores in cargas.items():
        print(f"{hip}:")
        print(f"  Fuerzas:  Fx={valores['fx']:8.2f} daN  Fy={valores['fy']:8.2f} daN  Fz={valores['fz']:8.2f} daN")
        print(f"  Momentos: Mx={valores['mx']:8.2f} daN·m  My={valores['my']:8.2f} daN·m  Mz={valores['mz']:8.2f} daN·m")
        print()
