#!/usr/bin/env python3
"""
Test básico del sistema de morfologías
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_morfologias():
    """Test básico de morfologías"""
    try:
        # Importar módulos
        from EstructuraAEA_Geometria_Morfologias import (
            extraer_parametros_morfologia, 
            inferir_morfologia_desde_parametros,
            crear_nodos_morfologia
        )
        
        print("✅ Importación exitosa")
        
        # Test 1: Extraer parámetros de morfología
        morfologia = "DOBLE-TRIANGULAR-2HG"
        params = extraer_parametros_morfologia(morfologia)
        print(f"✅ Morfología '{morfologia}' -> {params}")
        
        # Test 2: Inferir morfología desde parámetros
        morfologia_inferida = inferir_morfologia_desde_parametros("Doble", "triangular", 2, False)
        print(f"✅ Parámetros -> Morfología '{morfologia_inferida}'")
        
        # Test 3: Crear nodos (con parámetros mínimos)
        parametros_test = {
            'h1a': 10.0, 'h2a': 15.0, 'h3a': 20.0,
            's_estructura': 2.5, 'D_fases': 3.0, 'theta_max': 15.0,
            'lmenhg': 1.5, 'a': 2.0
        }
        
        nodos, conexiones = crear_nodos_morfologia("DOBLE-TRIANGULAR-2HG", parametros_test)
        print(f"✅ Nodos creados: {len(nodos)} nodos, {len(conexiones)} conexiones")
        
        # Verificar algunos nodos esperados
        nodos_esperados = ["BASE", "CROSS_H1", "CROSS_H2", "CROSS_H3", "TOP", "HG1", "HG2"]
        for nodo in nodos_esperados:
            if nodo in nodos:
                print(f"  ✅ {nodo}: {nodos[nodo].coordenadas}")
            else:
                print(f"  ❌ {nodo}: NO ENCONTRADO")
        
        print(f"✅ Test completado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_morfologias()