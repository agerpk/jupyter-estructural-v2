# NodoEstructural.py
"""
Clase NodoEstructural - Representa un nodo estructural con propiedades geométricas y cargas
"""
import math

class Carga:
    """Representa una carga con valores para múltiples hipótesis"""
    
    def __init__(self, nombre, hipotesis=None, fuerzas_x=None, fuerzas_y=None, fuerzas_z=None,
                 momentos_x=None, momentos_y=None, momentos_z=None):
        """
        Args:
            nombre (str): Nombre de la carga (ej: "Peso", "Viento", "Tiro")
            hipotesis (list): Lista de códigos de hipótesis
            fuerzas_x, fuerzas_y, fuerzas_z (list): Listas de fuerzas en daN para cada hipótesis
            momentos_x, momentos_y, momentos_z (list): Listas de momentos en daN·m para cada hipótesis
        """
        self.nombre = nombre
        self.hipotesis = hipotesis if hipotesis else []
        self.fuerzas_x = fuerzas_x if fuerzas_x else []
        self.fuerzas_y = fuerzas_y if fuerzas_y else []
        self.fuerzas_z = fuerzas_z if fuerzas_z else []
        self.momentos_x = momentos_x if momentos_x else []
        self.momentos_y = momentos_y if momentos_y else []
        self.momentos_z = momentos_z if momentos_z else []
    
    def agregar_hipotesis(self, codigo_hip, fx=0.0, fy=0.0, fz=0.0, mx=0.0, my=0.0, mz=0.0):
        """Agrega valores para una hipótesis"""
        if codigo_hip in self.hipotesis:
            idx = self.hipotesis.index(codigo_hip)
            self.fuerzas_x[idx] = fx
            self.fuerzas_y[idx] = fy
            self.fuerzas_z[idx] = fz
            self.momentos_x[idx] = mx
            self.momentos_y[idx] = my
            self.momentos_z[idx] = mz
        else:
            self.hipotesis.append(codigo_hip)
            self.fuerzas_x.append(fx)
            self.fuerzas_y.append(fy)
            self.fuerzas_z.append(fz)
            self.momentos_x.append(mx)
            self.momentos_y.append(my)
            self.momentos_z.append(mz)
    
    def obtener_valores(self, codigo_hip):
        """Obtiene valores para una hipótesis específica"""
        if codigo_hip in self.hipotesis:
            idx = self.hipotesis.index(codigo_hip)
            return {
                "fx": self.fuerzas_x[idx],
                "fy": self.fuerzas_y[idx],
                "fz": self.fuerzas_z[idx],
                "mx": self.momentos_x[idx],
                "my": self.momentos_y[idx],
                "mz": self.momentos_z[idx]
            }
        return {"fx": 0.0, "fy": 0.0, "fz": 0.0, "mx": 0.0, "my": 0.0, "mz": 0.0}
    
    def __repr__(self):
        return f"Carga('{self.nombre}', {len(self.hipotesis)} hipótesis)"
    
    def to_dict(self):
        """Exporta a diccionario"""
        return {
            "nombre": self.nombre,
            "hipotesis": self.hipotesis,
            "fuerzas_x": self.fuerzas_x,
            "fuerzas_y": self.fuerzas_y,
            "fuerzas_z": self.fuerzas_z,
            "momentos_x": self.momentos_x,
            "momentos_y": self.momentos_y,
            "momentos_z": self.momentos_z
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea desde diccionario"""
        return cls(
            nombre=data["nombre"],
            hipotesis=data.get("hipotesis", []),
            fuerzas_x=data.get("fuerzas_x", []),
            fuerzas_y=data.get("fuerzas_y", []),
            fuerzas_z=data.get("fuerzas_z", []),
            momentos_x=data.get("momentos_x", []),
            momentos_y=data.get("momentos_y", []),
            momentos_z=data.get("momentos_z", [])
        )


class NodoEstructural:
    """
    Clase que representa un nodo estructural con sus propiedades y cargas
    """
    
    def __init__(self, nombre, coordenadas, tipo_nodo, cable_asociado=None, 
                angulo_quiebre=0, tipo_fijacion=None, rotacion_eje_z=0.0, 
                rotacion_eje_x=0.0, rotacion_eje_y=0.0,
                es_editado=False, conectado_a=None):
        """
        Inicializa un nodo estructural
        
        Args:
            nombre (str): Identificador único del nodo
            coordenadas (tuple): (x, y, z) en metros
            tipo_nodo (str): "conductor", "guardia", "base", "cruce", "general", "viento"
            cable_asociado (Cable_AEA, optional): Objeto cable asociado
            angulo_quiebre (float): Ángulo de quiebre en grados
            tipo_fijacion (str): "suspensión" o "retención"
            rotacion_eje_z (float): Rotación del cable en eje Z (grados)
            es_editado (bool): Flag para nodos editados manualmente
            conectado_a (list/str): Lista de nombres de nodos conectados
        """
        self.nombre = nombre
        self.coordenadas = tuple(coordenadas)  # (x, y, z)
        self.tipo_nodo = tipo_nodo
        self.cable_asociado = cable_asociado
        self.angulo_quiebre = angulo_quiebre if angulo_quiebre is not None else 0.0
        self.rotacion_eje_x = rotacion_eje_x if rotacion_eje_x is not None else 0.0
        self.rotacion_eje_y = rotacion_eje_y if rotacion_eje_y is not None else 0.0
        self.rotacion_eje_z = rotacion_eje_z if rotacion_eje_z is not None else 0.0
        self.es_editado = es_editado
        
        # Convertir conectado_a a lista
        if conectado_a is None:
            self.conectado_a = []
        elif isinstance(conectado_a, str):
            self.conectado_a = [conectado_a] if conectado_a else []
        else:
            self.conectado_a = list(conectado_a)
        
        # Determinar tipo de fijación
        if tipo_fijacion is None:
            if "suspens" in tipo_nodo.lower():
                self.tipo_fijacion = "suspensión"
            else:
                self.tipo_fijacion = "retención"
        else:
            self.tipo_fijacion = tipo_fijacion
        
        # Lista de cargas aplicadas al nodo
        self.cargas = []  # Lista de objetos Carga
        self.cargas_dict = {}  # Dict para compatibilidad: {hip: [fx,fy,fz]}
    
    @property
    def x(self):
        """Coordenada X"""
        return self.coordenadas[0]
    
    @property
    def y(self):
        """Coordenada Y"""
        return self.coordenadas[1]
    
    @property
    def z(self):
        """Coordenada Z"""
        return self.coordenadas[2]
    
    def __str__(self):
        return f"Nodo({self.nombre}, {self.tipo_nodo}, {self.coordenadas})"
    
    def __repr__(self):
        return f"NodoEstructural('{self.nombre}', {self.coordenadas}, '{self.tipo_nodo}')"
    
    def agregar_carga(self, carga):
        """
        Agrega un objeto Carga al nodo
        
        Args:
            carga (Carga): Objeto Carga con valores para múltiples hipótesis
        """
        # Verificar si ya existe una carga con ese nombre
        for i, c in enumerate(self.cargas):
            if c.nombre == carga.nombre:
                self.cargas[i] = carga
                return
        self.cargas.append(carga)
    
    def obtener_carga(self, nombre_carga):
        """
        Obtiene un objeto Carga por nombre
        
        Args:
            nombre_carga (str): Nombre de la carga
        
        Returns:
            Carga: Objeto Carga o None si no existe
        """
        for carga in self.cargas:
            if carga.nombre == nombre_carga:
                return carga
        return None
    
    def obtener_cargas_hipotesis(self, codigo_hip):
        """
        Obtiene todas las cargas sumadas para una hipótesis específica
        
        Args:
            codigo_hip (str): Código de la hipótesis
        
        Returns:
            dict: {"fx": ..., "fy": ..., "fz": ..., "mx": ..., "my": ..., "mz": ...}
        """
        # Compatibilidad: usar cargas_dict si existe
        if hasattr(self, 'cargas_dict') and codigo_hip in self.cargas_dict:
            carga = self.cargas_dict[codigo_hip]
            return {
                "fx": carga[0],
                "fy": carga[1],
                "fz": carga[2],
                "mx": 0.0,
                "my": 0.0,
                "mz": 0.0
            }
        
        # Nueva estructura: sumar objetos Carga
        fx_total, fy_total, fz_total = 0.0, 0.0, 0.0
        mx_total, my_total, mz_total = 0.0, 0.0, 0.0
        
        for carga in self.cargas:
            valores = carga.obtener_valores(codigo_hip)
            fx_total += valores["fx"]
            fy_total += valores["fy"]
            fz_total += valores["fz"]
            mx_total += valores["mx"]
            my_total += valores["my"]
            mz_total += valores["mz"]
        
        return {
            "fx": fx_total,
            "fy": fy_total,
            "fz": fz_total,
            "mx": mx_total,
            "my": my_total,
            "mz": mz_total
        }
    
    def listar_hipotesis(self):
        """
        Lista todas las hipótesis presentes en las cargas del nodo
        
        Returns:
            list: Lista de códigos de hipótesis únicos
        """
        hipotesis_set = set()
        
        # Compatibilidad: usar cargas_dict si existe
        if hasattr(self, 'cargas_dict'):
            hipotesis_set.update(self.cargas_dict.keys())
        
        # Nueva estructura
        for carga in self.cargas:
            hipotesis_set.update(carga.hipotesis)
        
        return sorted(list(hipotesis_set))
    
    def rotar_vector(self, fx, fy, fz, aplicar_rotacion_inversa=False):
        """
        Rota un vector según las rotaciones del nodo (orden: X → Y → Z)
        
        Args:
            fx, fy, fz (float): Componentes del vector
            aplicar_rotacion_inversa (bool): Si True, aplica rotación inversa (para ver desde fuera)
        
        Returns:
            tuple: (fx_rot, fy_rot, fz_rot)
        """
        # Si no hay rotación, retornar sin cambios
        if self.rotacion_eje_x == 0 and self.rotacion_eje_y == 0 and self.rotacion_eje_z == 0:
            return (fx, fy, fz)
        
        # Determinar ángulos (invertir si es rotación inversa)
        factor = -1 if aplicar_rotacion_inversa else 1
        rx = math.radians(self.rotacion_eje_x * factor)
        ry = math.radians(self.rotacion_eje_y * factor)
        rz = math.radians(self.rotacion_eje_z * factor)
        
        # Rotación en X
        if rx != 0:
            fy_temp = fy * math.cos(rx) - fz * math.sin(rx)
            fz = fy * math.sin(rx) + fz * math.cos(rx)
            fy = fy_temp
        
        # Rotación en Y
        if ry != 0:
            fx_temp = fx * math.cos(ry) + fz * math.sin(ry)
            fz = -fx * math.sin(ry) + fz * math.cos(ry)
            fx = fx_temp
        
        # Rotación en Z
        if rz != 0:
            fx_temp = fx * math.cos(rz) - fy * math.sin(rz)
            fy = fx * math.sin(rz) + fy * math.cos(rz)
            fx = fx_temp
        
        return (fx, fy, fz)
    
    def obtener_cargas_hipotesis_rotadas(self, codigo_hip, sistema_referencia="local"):
        """
        Obtiene cargas sumadas para una hipótesis, rotadas según sistema de referencia
        
        Args:
            codigo_hip (str): Código de la hipótesis
            sistema_referencia (str): "local" (sin rotar) o "global" (rotado)
        
        Returns:
            dict: {"fx": ..., "fy": ..., "fz": ..., "mx": ..., "my": ..., "mz": ...}
        """
        cargas = self.obtener_cargas_hipotesis(codigo_hip)
        
        if sistema_referencia == "local":
            return cargas
        
        # Rotar al sistema global
        fx_rot, fy_rot, fz_rot = self.rotar_vector(
            cargas["fx"], cargas["fy"], cargas["fz"], aplicar_rotacion_inversa=True
        )
        mx_rot, my_rot, mz_rot = self.rotar_vector(
            cargas["mx"], cargas["my"], cargas["mz"], aplicar_rotacion_inversa=True
        )
        
        return {
            "fx": fx_rot,
            "fy": fy_rot,
            "fz": fz_rot,
            "mx": mx_rot,
            "my": my_rot,
            "mz": mz_rot
        }
    
    def obtener_coordenadas_dict(self):
        """Devuelve coordenadas en formato de diccionario para compatibilidad"""
        return {self.nombre: list(self.coordenadas)}
    
    def to_dict(self, incluir_cargas=False):
        """
        Exporta nodo a diccionario
        
        Args:
            incluir_cargas (bool): Si True, incluye todas las cargas
        
        Returns:
            dict: Representación del nodo
        """
        data = {
            "nombre": self.nombre,
            "tipo": self.tipo_nodo,
            "coordenadas": list(self.coordenadas),
            "cable_id": self.cable_asociado.nombre if self.cable_asociado else "",
            "rotacion_eje_x": self.rotacion_eje_x,
            "rotacion_eje_y": self.rotacion_eje_y,
            "rotacion_eje_z": self.rotacion_eje_z,
            "angulo_quiebre": self.angulo_quiebre,
            "tipo_fijacion": self.tipo_fijacion,
            "conectado_a": self.conectado_a,
            "es_editado": self.es_editado
        }
        
        if incluir_cargas:
            # Incluir ambas estructuras para compatibilidad
            if hasattr(self, 'cargas_dict') and self.cargas_dict:
                data["cargas_dict"] = self.cargas_dict
            if self.cargas:
                data["cargas"] = [carga.to_dict() for carga in self.cargas]
        
        return data
    
    @classmethod
    def from_dict(cls, data, cable_asociado=None):
        """
        Crea nodo desde diccionario
        
        Args:
            data (dict): Datos del nodo
            cable_asociado (Cable_AEA, optional): Objeto cable si se resuelve externamente
        
        Returns:
            NodoEstructural: Instancia del nodo
        """
        nodo = cls(
            nombre=data["nombre"],
            coordenadas=tuple(data["coordenadas"]),
            tipo_nodo=data.get("tipo", "general"),
            cable_asociado=cable_asociado,
            angulo_quiebre=data.get("angulo_quiebre", 0.0),
            tipo_fijacion=data.get("tipo_fijacion", "suspensión"),
            rotacion_eje_x=data.get("rotacion_eje_x", 0.0),
            rotacion_eje_y=data.get("rotacion_eje_y", 0.0),
            rotacion_eje_z=data.get("rotacion_eje_z", 0.0),
            es_editado=data.get("es_editado", False),
            conectado_a=data.get("conectado_a", [])
        )
        
        # Cargar cargas_dict si existe (compatibilidad)
        if "cargas_dict" in data:
            nodo.cargas_dict = data["cargas_dict"]
        
        # Cargar cargas si existen (nueva estructura)
        if "cargas" in data:
            for carga_dict in data["cargas"]:
                carga = Carga.from_dict(carga_dict)
                nodo.cargas.append(carga)
        
        return nodo
    
    def info_completa(self):
        """Devuelve información completa del nodo"""
        rotaciones = []
        if self.rotacion_eje_x != 0:
            rotaciones.append(f"X:{self.rotacion_eje_x}°")
        if self.rotacion_eje_y != 0:
            rotaciones.append(f"Y:{self.rotacion_eje_y}°")
        if self.rotacion_eje_z != 0:
            rotaciones.append(f"Z:{self.rotacion_eje_z}°")
        
        info = {
            "Nombre": self.nombre,
            "Coordenadas": f"({self.x:.3f}, {self.y:.3f}, {self.z:.3f})",
            "Tipo": self.tipo_nodo,
            "Cable asociado": self.cable_asociado.nombre if self.cable_asociado else "Ninguno",
            "Ángulo quiebre": f"{self.angulo_quiebre}°",
            "Tipo fijación": self.tipo_fijacion,
            "Rotaciones": ", ".join(rotaciones) if rotaciones else "Ninguna",
            "Es editado": "Sí" if self.es_editado else "No",
            "Conectado a": ", ".join(self.conectado_a) if self.conectado_a else "Ninguno",
            "Cargas aplicadas": len(self.cargas),
            "Hipótesis presentes": len(self.listar_hipotesis())
        }
        return info
