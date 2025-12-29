import pandas as pd
import numpy as np

# Leer el archivo Excel
archivo = "FUNDACIONES-AGPK-V2.xlsx"

try:
    df = pd.read_excel(archivo, sheet_name='Calculo', header=None)
    
    print("=== ANÁLISIS DETALLADO DE FÓRMULAS ===\n")
    
    # Buscar filas con fórmulas (columna 6)
    formulas = df[6].dropna()
    print("FÓRMULAS ENCONTRADAS:")
    for idx, formula in formulas.items():
        if str(formula) != 'nan' and str(formula) != 'Fórmula':
            print(f"Fila {idx}: {formula}")
    
    print("\n=== PARÁMETROS DE ENTRADA ===")
    # Extraer parámetros con sus valores
    parametros = {}
    for i in range(len(df)):
        if pd.notna(df.iloc[i, 0]) and pd.notna(df.iloc[i, 1]) and pd.notna(df.iloc[i, 2]):
            variable = str(df.iloc[i, 0])
            simbolo = str(df.iloc[i, 1])
            valor = df.iloc[i, 2]
            unidad = str(df.iloc[i, 3]) if pd.notna(df.iloc[i, 3]) else ""
            
            if variable not in ['Variable', 'nan'] and simbolo not in ['Símbolo', 'nan']:
                parametros[simbolo] = {
                    'variable': variable,
                    'valor': valor,
                    'unidad': unidad
                }
                print(f"{simbolo}: {variable} = {valor} {unidad}")
    
    print("\n=== RESULTADOS CALCULADOS ===")
    # Buscar resultados en columnas 7-10
    for i in range(len(df)):
        if pd.notna(df.iloc[i, 7]) and pd.notna(df.iloc[i, 8]) and pd.notna(df.iloc[i, 9]):
            descripcion = str(df.iloc[i, 7])
            simbolo = str(df.iloc[i, 8])
            valor = df.iloc[i, 9]
            verificacion = str(df.iloc[i, 10]) if pd.notna(df.iloc[i, 10]) else ""
            
            if descripcion not in ['Resultados', 'nan']:
                print(f"{simbolo}: {descripcion} = {valor} {verificacion}")
    
    print("\n=== DATOS DE SUELO Y CONSTANTES ===")
    # Buscar datos específicos de suelo
    suelo_keywords = ['tierra', 'suelo', 'presión', 'fricción', 'compresibilidad', 'hormigón', 'densidad']
    for i in range(len(df)):
        if pd.notna(df.iloc[i, 0]):
            variable = str(df.iloc[i, 0]).lower()
            if any(keyword in variable for keyword in suelo_keywords):
                simbolo = str(df.iloc[i, 1]) if pd.notna(df.iloc[i, 1]) else ""
                valor = df.iloc[i, 2] if pd.notna(df.iloc[i, 2]) else ""
                unidad = str(df.iloc[i, 3]) if pd.notna(df.iloc[i, 3]) else ""
                print(f"{simbolo}: {df.iloc[i, 0]} = {valor} {unidad}")

except Exception as e:
    print(f"Error: {e}")