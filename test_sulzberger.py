import sys
sys.path.append('utils')

from Sulzberger import Sulzberger

# Crear instancia de Sulzberger
sulz = Sulzberger()

# Configurar estructura (datos del Excel)
sulz.configurar_estructura(
    Gp=4680,    # Masa total poste [kg]
    Ft=1030,    # Fuerza transversal [kgf]
    Fl=1060,    # Fuerza longitudinal [kgf]
    h=15.0,     # Altura total [m]
    hl=13.5,    # Altura libre [m]
    he=1.5,     # Altura empotrada [m]
    dc=0.31     # Diámetro en cima [m]
)

print("=== PRUEBA CLASE SULZBERGER ===\n")

# Ejecutar cálculo
resultados = sulz.calcular_fundacion(tin=1.7, ain=1.3, bin=1.3)

print("\n=== RESULTADOS FINALES ===")
for key, value in resultados.items():
    print(f"{key}: {value}")

print("\n=== VERIFICACIONES ===")
for key, value in sulz.verificaciones.items():
    estado = "Verifica" if value else "No Verifica"
    print(f"{key}: {estado}")

print("\n=== DATAFRAME RESULTADOS ===")
df = sulz.obtener_dataframe_resultados()
print(df.to_string(index=False))