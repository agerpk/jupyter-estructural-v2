import json

def verificar_duplicados():
    with open('c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2/data/cables_2.json', 'r', encoding='utf-8') as f:
        cables = json.load(f)
    
    nombres = list(cables.keys())
    print(f"Total cables: {len(nombres)}")
    print(f"Nombres únicos: {len(set(nombres))}")
    
    # Buscar duplicados por nombre
    duplicados_nombre = []
    for i, nombre in enumerate(nombres):
        if nombres.count(nombre) > 1 and nombre not in duplicados_nombre:
            duplicados_nombre.append(nombre)
    
    if duplicados_nombre:
        print(f"Cables duplicados por nombre: {duplicados_nombre}")
    else:
        print("No hay cables duplicados por nombre")
    
    # Buscar duplicados por sección nominal
    secciones = {}
    for nombre, cable in cables.items():
        seccion = cable.get('seccion_nominal', 'N/A')
        if seccion not in secciones:
            secciones[seccion] = []
        secciones[seccion].append(nombre)
    
    print("\nCables por sección nominal:")
    for seccion in sorted(secciones.keys(), key=lambda x: (x is None, x)):
        nombres_cables = secciones[seccion]
        if len(nombres_cables) > 1:
            print(f"  {seccion}: {nombres_cables}")

if __name__ == "__main__":
    verificar_duplicados()