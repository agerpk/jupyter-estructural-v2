import pandas as pd

# Leer el archivo Excel
archivo = "FUNDACIONES-AGPK-V2.xlsx"

try:
    # Intentar leer con diferentes engines
    try:
        # Intentar con openpyxl
        excel_file = pd.ExcelFile(archivo, engine='openpyxl')
    except:
        try:
            # Intentar con xlrd
            excel_file = pd.ExcelFile(archivo, engine='xlrd')
        except:
            # Último intento sin especificar engine
            excel_file = pd.ExcelFile(archivo)
    
    print("Hojas disponibles:", excel_file.sheet_names)
    
    # Leer la primera hoja
    primera_hoja = excel_file.sheet_names[0]
    print(f"\nAnalizando la primera hoja: '{primera_hoja}'")
    
    # Leer con pandas para análisis
    df = pd.read_excel(archivo, sheet_name=primera_hoja, header=None)
    
    print(f"\nDimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
    print("\nPrimeras 20 filas de la primera hoja:")
    
    # Convertir a string y limpiar caracteres problemáticos
    df_clean = df.copy()
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].astype(str).str.encode('ascii', errors='ignore').str.decode('ascii')
    
    print(df_clean.head(20).to_string())
    
    # Mostrar información sobre valores no nulos
    print(f"\nInformación de la hoja:")
    print(f"Celdas con datos: {df.count().sum()}")
    print(f"Celdas vacías: {df.isna().sum().sum()}")
    
    # Buscar patrones en las primeras columnas
    print(f"\nPrimeras 5 columnas con datos:")
    for col in range(min(5, df.shape[1])):
        valores_unicos = df[col].dropna().unique()
        if len(valores_unicos) > 0:
            print(f"Columna {col}: {len(valores_unicos)} valores únicos")
            if len(valores_unicos) <= 10:
                print(f"  Valores: {list(valores_unicos)}")
            else:
                print(f"  Primeros valores: {list(valores_unicos[:10])}")

except Exception as e:
    print(f"Error al leer el archivo: {e}")