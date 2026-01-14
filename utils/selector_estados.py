"""
Selector de Estados Climáticos

Algoritmos inteligentes para seleccionar estados climáticos según criterios físicos.
"""


class SelectorEstados:
    """
    Selecciona estados climáticos dinámicamente según criterios físicos
    """
    
    @staticmethod
    def buscar_max_flecha_vertical(resultados_estados):
        """
        Encuentra estado con máxima flecha vertical
        
        Uso: DGE necesita el estado con mayor flecha para distancias de seguridad
        
        Args:
            resultados_estados (dict): {estado_id: {"flecha_vertical_m": valor, ...}}
        
        Returns:
            str: ID del estado con máxima flecha vertical
            
        Raises:
            ValueError: Si no hay estados con flecha vertical válida
        """
        max_flecha = 0
        estado_max = None
        
        for estado_id, datos in resultados_estados.items():
            flecha = datos.get("flecha_vertical_m", 0)
            if flecha > max_flecha:
                max_flecha = flecha
                estado_max = estado_id
        
        if estado_max is None:
            raise ValueError(
                "No se encontró ningún estado con flecha vertical válida. "
                "Verifique que CMC se haya ejecutado correctamente."
            )
        
        return estado_max
    
    @staticmethod
    def buscar_max_tiro(resultados_estados):
        """
        Encuentra estado con máximo tiro
        
        Uso: Hipótesis con estado "máximo"
        
        Args:
            resultados_estados (dict): {estado_id: {"tiro_daN": valor, ...}}
        
        Returns:
            str: ID del estado con máximo tiro
            
        Raises:
            ValueError: Si no hay estados con tiro válido
        """
        max_tiro = 0
        estado_max = None
        
        for estado_id, datos in resultados_estados.items():
            tiro = datos.get("tiro_daN", 0)
            if tiro > max_tiro:
                max_tiro = tiro
                estado_max = estado_id
        
        if estado_max is None:
            raise ValueError(
                "No se encontró ningún estado con tiro válido. "
                "Verifique que CMC se haya ejecutado correctamente."
            )
        
        return estado_max
    
    @staticmethod
    def buscar_tma_equivalente(estados_climaticos):
        """
        Busca estado equivalente a TMA (Temperatura Media Anual)
        
        Criterios:
        1. Sin viento (velocidad = 0)
        2. Sin hielo (espesor = 0)
        3. Temperatura > 0°C
        4. De los que cumplen, el de menor temperatura
        
        Args:
            estados_climaticos (dict): {estado_id: {temperatura, viento_velocidad, espesor_hielo}}
        
        Returns:
            str: ID del estado equivalente a TMA
            
        Raises:
            ValueError: Si no existe ningún estado que cumpla los criterios
        """
        candidatos = []
        
        for estado_id, datos in estados_climaticos.items():
            if (datos.get("viento_velocidad", 0) == 0 and
                datos.get("espesor_hielo", 0) == 0 and
                datos.get("temperatura", 0) > 0):
                candidatos.append((estado_id, datos["temperatura"]))
        
        if not candidatos:
            raise ValueError(
                "No se encontró ningún estado climático que cumpla los criterios de TMA "
                "(sin viento, sin hielo, temperatura > 0°C). "
                "Defina al menos un estado con estas características."
            )
        
        # Retornar el de menor temperatura
        candidatos.sort(key=lambda x: x[1])
        return candidatos[0][0]
    
    @staticmethod
    def buscar_tmin_equivalente(estados_climaticos):
        """
        Busca estado equivalente a Tmín (Temperatura Mínima)
        
        Criterios:
        1. Temperatura mínima entre todos los estados
        
        Args:
            estados_climaticos (dict): {estado_id: {temperatura, ...}}
        
        Returns:
            str: ID del estado con temperatura mínima
            
        Raises:
            ValueError: Si no hay estados definidos
        """
        if not estados_climaticos:
            raise ValueError("No hay estados climáticos definidos")
        
        min_temp = float('inf')
        estado_min = None
        
        for estado_id, datos in estados_climaticos.items():
            temp = datos.get("temperatura", 0)
            if temp < min_temp:
                min_temp = temp
                estado_min = estado_id
        
        return estado_min
    
    @staticmethod
    def buscar_vmax_equivalente(estados_climaticos):
        """
        Busca estado equivalente a Vmáx (Viento Máximo)
        
        Criterios:
        1. Máxima velocidad de viento entre todos los estados
        
        Args:
            estados_climaticos (dict): {estado_id: {viento_velocidad, ...}}
        
        Returns:
            str: ID del estado con máxima velocidad de viento
            
        Raises:
            ValueError: Si no hay estados con viento definido
        """
        max_viento = 0
        estado_max = None
        
        for estado_id, datos in estados_climaticos.items():
            viento = datos.get("viento_velocidad", 0)
            if viento > max_viento:
                max_viento = viento
                estado_max = estado_id
        
        if estado_max is None:
            raise ValueError(
                "No se encontró ningún estado con viento definido. "
                "Defina al menos un estado con velocidad de viento > 0."
            )
        
        return estado_max
    
    @staticmethod
    def buscar_hielo_max(estados_climaticos):
        """
        Encuentra estado con máximo espesor de hielo
        
        Uso: Hipótesis A4 (carga adicional)
        
        Criterios:
        1. Máximo espesor de hielo entre todos los estados
        
        Args:
            estados_climaticos (dict): {estado_id: {espesor_hielo, ...}}
        
        Returns:
            str: ID del estado con máximo espesor de hielo
            
        Raises:
            ValueError: Si no hay estados con hielo definido
        """
        max_hielo = 0
        estado_max = None
        
        for estado_id, datos in estados_climaticos.items():
            hielo = datos.get("espesor_hielo", 0)
            if hielo > max_hielo:
                max_hielo = hielo
                estado_max = estado_id
        
        if estado_max is None:
            raise ValueError(
                "No se encontró ningún estado con hielo definido. "
                "Defina al menos un estado con espesor de hielo > 0."
            )
        
        return estado_max
