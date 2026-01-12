# EstructuraAEA_Geometria_Etapa0.py
from NodoEstructural import NodoEstructural


class GeometriaEtapa0:
    """Etapa 0: Creación del nodo BASE"""
    
    def __init__(self, geometria):
        self.geo = geometria
    
    def ejecutar(self):
        """Crear nodo BASE en (0, 0, 0)"""
        print("🔧 ETAPA 0: Nodo Base")
        self.geo.nodos["BASE"] = NodoEstructural(
            "BASE", (0.0, 0.0, 0.0), "base",
            tipo_fijacion=self.geo.tipo_fijacion_base
        )
        print("   ✅ Nodo BASE creado en (0, 0, 0)")
