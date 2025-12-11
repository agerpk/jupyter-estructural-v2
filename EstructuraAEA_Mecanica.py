# EstructuraAEA_Mecanica.py
import pandas as pd
import math

class EstructuraAEA_Mecanica:
    """
    Clase especializada en cálculos mecánicos de la estructura según norma AEA
    Incluye asignación de cargas, cálculo de reacciones y tiros en cima
    """
    
    def __init__(self, geometria):
        """
        Inicializa el módulo mecánico con referencia a la geometría
        
        Args:
            geometria (EstructuraAEA_Geometria): Instancia de la clase de geometría
        """
        self.geometria = geometria
        
        # Para almacenar DataFrames de cargas
        self.df_cargas_completo = None
        self.cargas_key = {}
        
        # Para almacenar resultados de reacciones
        self.resultados_reacciones = {}
        self.df_reacciones = None
        
        print(f"✅ ESTRUCTURA_AEA MECÁNICA CREADA")
    
    # ================= MÉTODOS DE CÁLCULO DE CARGAS =================
    
    def _calcular_componentes_tiro(self, tiro, angulo_grados, reduccion=0.0, es_guardia=False):
        """Calcula componentes transversal y longitudinal del tiro"""
        ang_rad = math.radians(angulo_grados / 2)
        
        if reduccion > 0:
            factor_trans = 2.0 * math.sin(ang_rad) * (1 - reduccion/2)
            factor_long = 2.0 * math.cos(ang_rad) * (reduccion/2)
        else:
            factor_trans = 2.0 * math.sin(ang_rad)
            factor_long = 0.0
        
        tiro_trans = factor_trans * tiro
        tiro_long = factor_long * tiro
        
        return tiro_trans, tiro_long
    
    def _calcular_componentes_tiro_unilateral(self, tiro, angulo_grados, factor=1.0):
        """Calcula componentes para tiro unilateral"""
        ang_rad = math.radians(angulo_grados / 2)
        
        factor_trans = factor * math.sin(ang_rad)
        factor_long = factor * math.cos(ang_rad)
        
        tiro_trans = factor_trans * tiro
        tiro_long = factor_long * tiro
        
        return tiro_trans, tiro_long
    
    def _obtener_carga_por_codigo(self, df_cargas_totales, codigo_buscar):
        """Busca carga por código en DataFrame de cargas"""
        try:
            filtro = df_cargas_totales['Código'] == codigo_buscar
            if not df_cargas_totales[filtro].empty:
                return df_cargas_totales[filtro]['Magnitud'].iloc[0]
            else:
                return 0.0
        except Exception as e:
            print(f"   ❌ Error buscando código {codigo_buscar}: {e}")
            return 0.0
    
    def _obtener_tiro_estado(self, resultados_dict, estado, componente="longitudinal"):
        """Obtiene tiro para estado específico"""
        if estado in resultados_dict:
            tiro_total = resultados_dict[estado]["tiro_daN"]
            alpha_rad = math.radians(self.geometria.alpha_quiebre / 2.0)
            if componente == "transversal":
                return round(tiro_total * math.sin(alpha_rad), 2)
            else:
                return round(tiro_total * math.cos(alpha_rad), 2)
        return 0.0
    
    def _aplicar_patron_dos_unilaterales_terminal(self, nodo, config_tiro, tiro_base, es_guardia=False):
        """
        Aplica patrón dos-unilaterales inverso para Terminal: 
        todos menos un conductor y un guardia se cargan con tiro unilateral
        """
        if es_guardia:
            # Para guardias: determinar qué guardia NO se carga (el eliminado)
            nodos_guardia = [n for n in self.geometria.nodes_key.keys() if n.startswith('HG')]
            if len(nodos_guardia) > 1:
                # Eliminar el primer guardia (HG1), cargar los demás con tiro unilateral
                guardia_eliminado = "HG1"
                if nodo == guardia_eliminado:
                    # Este guardia se elimina - no se carga
                    return 0.0, 0.0, 0.0, 0.0  # tiro_trans, tiro_long, factor_peso, factor_viento
                else:
                    # Los demás guardias se cargan con tiro unilateral
                    factor_guardia = config_tiro.get("factor_guardia", 1.0)
                    tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                        tiro_base, self.geometria.alpha_quiebre, factor_guardia
                    )
                    return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
            else:
                # Solo un guardia - se carga con tiro unilateral
                factor_guardia = config_tiro.get("factor_guardia", 1.0)
                tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                    tiro_base, self.geometria.alpha_quiebre, factor_guardia
                )
                return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
        
        else:
            # Para conductores: determinar qué conductor NO se carga (el eliminado)
            nodos_conductor = [n for n in self.geometria.nodes_key.keys() if n.startswith(('C1_', 'C2_', 'C3_'))]
            
            if nodos_conductor:
                # Elegir un conductor a eliminar (por ejemplo, el primero)
                conductor_eliminado = nodos_conductor[0]
                
                if nodo == conductor_eliminado:
                    # Este conductor se elimina - no se carga
                    return 0.0, 0.0, 0.0, 0.0
                else:
                    # Los demás conductores se cargan con tiro unilateral
                    factor_cond = config_tiro.get("factor_cond", 1.0)
                    tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                        tiro_base, self.geometria.alpha_quiebre, factor_cond
                    )
                    return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
            else:
                return 0.0, 0.0, 0.0, 0.0
    
    def _aplicar_patron_doble_terna_a_simple(self, nodo, config_tiro, tiro_base, es_guardia=False):
        """
        Aplica patrón doble-terna-a-simple: 
        - Todos los conductores del lado L (CX_L) se cargan con tiro unilateral
        - Los conductores del lado R se cargan con tiro bilateral
        - Los guardias se cargan con tiro unilateral
        """
        if es_guardia:
            # Para guardias: aplicar tiro unilateral a todos
            factor_guardia = config_tiro.get("factor_guardia", 1.0)
            tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                tiro_base, self.geometria.alpha_quiebre, factor_guardia
            )
            return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
        
        else:
            # Para conductores: determinar si es del lado L o R
            if nodo.endswith('_L'):
                # Conductores del lado L: tiro unilateral
                factor_cond = config_tiro.get("factor_cond", 1.0)
                tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                    tiro_base, self.geometria.alpha_quiebre, factor_cond
                )
                return tiro_trans, tiro_long, 0.5, 0.5  # unilateral: factor 0.5
            else:
                # Conductores del lado R: tiro bilateral (NO eliminados)
                reduccion_cond = config_tiro.get("reduccion_cond", 0.0)
                tiro_trans, tiro_long = self._calcular_componentes_tiro(
                    tiro_base, self.geometria.alpha_quiebre, reduccion_cond, False
                )
                return tiro_trans, tiro_long, 1.0, 1.0  # bilateral: factor 1.0
    
    def asignar_cargas_hipotesis(self, df_cargas_totales, resultados_conductor, 
                                 resultados_guardia1, vano, hipotesis_maestro, 
                                 t_hielo, hipotesis_a_incluir="Todas", resultados_guardia2=None):
        """
        Asigna cargas a todos los nodos según las hipótesis definidas
        
        Args:
            df_cargas_totales (DataFrame): DataFrame con todas las cargas
            resultados_conductor (dict): Resultados del cálculo mecánico del conductor
            resultados_guardia1 (dict): Resultados del cálculo mecánico del guardia 1
            vano (float): Longitud del vano en metros
            hipotesis_maestro (dict): Diccionario con definición de hipótesis
            t_hielo (float): Espesor de hielo en metros
            hipotesis_a_incluir (str/list): Hipótesis a procesar
            resultados_guardia2 (dict, optional): Resultados del cálculo mecánico del guardia 2
        """
        print(f"\n🔄 ASIGNANDO CARGAS SEGÚN HIPÓTESIS...")
        
        # Pesos base
        peso_conductor_base = self.geometria.cable_conductor.peso_unitario_dan_m
        peso_guardia1_base = self.geometria.cable_guardia1.peso_unitario_dan_m
        
        # Pesos con hielo
        peso_hielo_conductor = self.geometria.cable_conductor._calcular_peso_hielo(t_hielo)
        peso_hielo_guardia1 = self.geometria.cable_guardia1._calcular_peso_hielo(t_hielo)
        
        if self.geometria.cable_guardia2:
            peso_guardia2_base = self.geometria.cable_guardia2.peso_unitario_dan_m
            peso_hielo_guardia2 = self.geometria.cable_guardia2._calcular_peso_hielo(t_hielo)
        
        # Nodos especiales
        NODOS_DOS_UNILATERAL = ["C3_L", "HG1"]
        
        # Filtrar hipótesis si se especificó
        if self.geometria.tipo_estructura in hipotesis_maestro:
            hipotesis_dict = hipotesis_maestro[self.geometria.tipo_estructura]
            
            # Determinar qué hipótesis procesar
            if hipotesis_a_incluir == "Todas":
                hipotesis_a_procesar = hipotesis_dict.items()
                print(f"   Procesando TODAS las hipótesis disponibles")
            else:
                hipotesis_a_procesar = []
                for codigo in hipotesis_a_incluir:
                    if codigo in hipotesis_dict:
                        hipotesis_a_procesar.append((codigo, hipotesis_dict[codigo]))
                    else:
                        print(f"   ⚠️ Hipótesis {codigo} no encontrada para {self.geometria.tipo_estructura}")
                print(f"   Procesando hipótesis: {hipotesis_a_incluir}")

            for codigo_hip, config in hipotesis_a_procesar:
                nombre_completo = f"HIP_{self.geometria.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_')}_{codigo_hip}_{config['desc']}"
                
                # Inicializar cargas para esta hipótesis
                cargas_hipotesis = {nombre: [0.00, 0.00, 0.00] for nombre in self.geometria.nodes_key.keys()}
                
                try:
                    # Obtener estados
                    estado_viento_config = config["viento"]["estado"] if config["viento"] else None
                    estado_viento = self.geometria.ESTADOS_MAPEO.get(estado_viento_config, estado_viento_config) if estado_viento_config else None
                    
                    estado_tiro_config = config["tiro"]["estado"] if config["tiro"] else None
                    estado_tiro = self.geometria.ESTADOS_MAPEO.get(estado_tiro_config, estado_tiro_config) if estado_tiro_config else None
                    
                    config_tiro = config["tiro"] if config["tiro"] else None
                    patron_tiro = config_tiro["patron"] if config_tiro else "bilateral"
                    
                    factor_peso = config["peso"]["factor"]
                    
                    # Calcular pesos
                    if config["peso"]["hielo"]:
                        peso_cond = (peso_conductor_base + peso_hielo_conductor) * vano * factor_peso
                        peso_guardia1 = (peso_guardia1_base + peso_hielo_guardia1) * vano * factor_peso
                        if self.geometria.cable_guardia2:
                            peso_guardia2 = (peso_guardia2_base + peso_hielo_guardia2) * vano * factor_peso
                    else:
                        peso_cond = peso_conductor_base * vano * factor_peso
                        peso_guardia1 = peso_guardia1_base * vano * factor_peso
                        if self.geometria.cable_guardia2:
                            peso_guardia2 = peso_guardia2_base * vano * factor_peso
                    
                    # Obtener tiros
                    if estado_tiro == "máximo":
                        tiro_cond_base = max([d["tiro_daN"] for d in resultados_conductor.values()])
                        tiro_guardia1_base = max([d["tiro_daN"] for d in resultados_guardia1.values()])
                        if resultados_guardia2:
                            tiro_guardia2_base = max([d["tiro_daN"] for d in resultados_guardia2.values()])
                    elif estado_tiro in resultados_conductor and estado_tiro in resultados_guardia1:
                        tiro_cond_base = resultados_conductor[estado_tiro]["tiro_daN"]
                        tiro_guardia1_base = resultados_guardia1[estado_tiro]["tiro_daN"]
                        if resultados_guardia2 and estado_tiro in resultados_guardia2:
                            tiro_guardia2_base = resultados_guardia2[estado_tiro]["tiro_daN"]
                    else:
                        tiro_cond_base = 0.0
                        tiro_guardia1_base = 0.0
                        if resultados_guardia2:
                            tiro_guardia2_base = 0.0
                    
                    # VIENTO SOBRE ESTRUCTURA
                    if config["viento"]:
                        direccion_viento = config["viento"]["direccion"]
                        factor_viento = config["viento"]["factor"]
                        estado_v = config["viento"]["estado"]
                        
                        if direccion_viento == "Transversal":
                            if estado_v == "Vmax":
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "VeT")
                            else:
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "Vemedt")
                            cargas_hipotesis['V'] = [viento_estructura * factor_viento, 0.0, 0.0]
                            
                        elif direccion_viento == "Longitudinal":
                            if estado_v == "Vmax":
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "VeL")
                            else:
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "Vemedl")
                            cargas_hipotesis['V'] = [0.0, viento_estructura * factor_viento, 0.0]
                            
                        elif direccion_viento == "Oblicua":
                            if estado_v == "Vmax":
                                viento_estructura_trans = self._obtener_carga_por_codigo(df_cargas_totales, "VeoT")
                                viento_estructura_long = self._obtener_carga_por_codigo(df_cargas_totales, "VeoL")
                            else:
                                viento_estructura_trans = self._obtener_carga_por_codigo(df_cargas_totales, "VemedoT")
                                viento_estructura_long = self._obtener_carga_por_codigo(df_cargas_totales, "VemedoL")
                            cargas_hipotesis['V'] = [
                                viento_estructura_trans * factor_viento,
                                viento_estructura_long * factor_viento,
                                0.0
                            ]
                    
                    # CARGAS EN CONDUCTORES
                    nodos_conductor = [n for n in self.geometria.nodes_key.keys() if n.startswith(('C1_', 'C2_', 'C3_'))]
                    
                    for nodo in nodos_conductor:
                        carga_x, carga_y, carga_z = 0.0, 0.0, 0.0

                        if patron_tiro == "doble-terna-a-simple":
                            # Para conductores: aplicar patrón doble-terna-a-simple
                            tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_doble_terna_a_simple(
                                nodo, config_tiro, tiro_cond_base, es_guardia=False
                            )
                        elif patron_tiro == "unilateral":
                            factor_peso_nodo = 0.5
                            factor_viento_nodo = 0.5
                            factor_cond = config_tiro.get("factor_cond", 1.0)
                            tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                                tiro_cond_base, self.geometria.alpha_quiebre, factor_cond
                            )
                        elif patron_tiro == "dos-unilaterales":
                            if self.geometria.tipo_estructura == "Terminal":
                                # Para Terminal: patrón inverso
                                tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_dos_unilaterales_terminal(
                                    nodo, config_tiro, tiro_cond_base, es_guardia=False
                                )
                            else:
                                # Comportamiento original
                                es_unilateral = (nodo in NODOS_DOS_UNILATERAL)
                                factor_peso_nodo = 0.5 if es_unilateral else 1.0
                                factor_viento_nodo = 0.5 if es_unilateral else 1.0
                                if es_unilateral:
                                    factor_cond = config_tiro.get("factor_cond", 1.0)
                                    tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                                        tiro_cond_base, self.geometria.alpha_quiebre, factor_cond
                                    )
                                else:
                                    reduccion_cond = config_tiro.get("reduccion_cond", 0.0)
                                    tiro_trans, tiro_long = self._calcular_componentes_tiro(
                                        tiro_cond_base, self.geometria.alpha_quiebre, reduccion_cond, False
                                    )
                        else:  # bilateral
                            factor_peso_nodo = 1.0
                            factor_viento_nodo = 1.0
                            reduccion_cond = config_tiro.get("reduccion_cond", 0.0)
                            tiro_trans, tiro_long = self._calcular_componentes_tiro(
                                tiro_cond_base, self.geometria.alpha_quiebre, reduccion_cond, False
                            )
                        
                        carga_x += tiro_trans
                        carga_y += tiro_long
                        carga_z = -peso_cond * factor_peso_nodo
                        
                        # VIENTO EN CABLES
                        if config["viento"]:
                            direccion_viento = config["viento"]["direccion"]
                            estado_v = config["viento"]["estado"]
                            factor_viento = config["viento"]["factor"]
                            
                            if direccion_viento == "Transversal":
                                if estado_v == "Vmax":
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "Vc")
                                else:
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed")
                                carga_x += viento_cond * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Longitudinal":
                                if estado_v == "Vmax":
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "VcL")
                                else:
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "VcmedL")
                                carga_y += viento_cond * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Oblicua":
                                es_unilateral = (patron_tiro == "unilateral") or (patron_tiro == "dos-unilaterales" and nodo in NODOS_DOS_UNILATERAL)
                                if es_unilateral:
                                    lado = 1 if "L" in nodo else 2
                                    if estado_v == "Vmax":
                                        viento_cond_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vc_o_t_{lado}")
                                        viento_cond_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vc_o_l_{lado}")
                                    else:
                                        viento_cond_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcmed_o_t_{lado}")
                                        viento_cond_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcmed_o_l_{lado}")
                                    
                                    carga_x += viento_cond_x * factor_viento * factor_viento_nodo
                                    carga_y += viento_cond_y * factor_viento * factor_viento_nodo
                                else:
                                    if estado_v == "Vmax":
                                        viento_cond_x = (self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_t_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_t_2"))
                                        viento_cond_y = (self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_l_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, "Vc_o_l_2"))
                                    else:
                                        viento_cond_x = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed_o_t_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed_o_t_2"))
                                        viento_cond_y = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed_o_l_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed_o_l_2"))
                                    
                                    carga_x += viento_cond_x * factor_viento * factor_viento_nodo
                                    carga_y += viento_cond_y * factor_viento * factor_viento_nodo
                        
                        # SOBRECARGA ADICIONAL
                        if config["sobrecarga"] and nodo == "C1_L":
                            carga_z -= config["sobrecarga"]
                        
                        cargas_hipotesis[nodo] = [round(carga_x, 2), round(carga_y, 2), round(carga_z, 2)]
                    
                    # CARGAS EN GUARDIA
                    nodos_guardia = [n for n in self.geometria.nodes_key.keys() if n.startswith('HG')]
                    
                    for nodo in nodos_guardia:
                        carga_x, carga_y, carga_z = 0.0, 0.0, 0.0
                        
                        # Determinar qué cable de guardia usar según el nodo
                        if nodo == "HG1" or (nodo.startswith("HG") and self.geometria.nodes_key[nodo][0] > 0):
                            # HG1 o nodos con x > 0 (derecha) usan guardia1
                            tiro_guardia_base = tiro_guardia1_base
                            peso_guardia = peso_guardia1
                            sufijo_viento = "1"
                        else:
                            # HG2 o nodos con x < 0 (izquierda) usan guardia2
                            tiro_guardia_base = tiro_guardia2_base if resultados_guardia2 else tiro_guardia1_base
                            peso_guardia = peso_guardia2 if self.geometria.cable_guardia2 else peso_guardia1
                            sufijo_viento = "2" if self.geometria.cable_guardia2 else "1"

                        if patron_tiro == "doble-terna-a-simple":
                            tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_doble_terna_a_simple(
                                nodo, config_tiro, tiro_guardia_base, es_guardia=True
                            )
                        elif patron_tiro == "unilateral":
                            factor_peso_nodo = 0.5
                            factor_viento_nodo = 0.5
                            factor_guardia = config_tiro.get("factor_guardia", 1.0)
                            tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                                tiro_guardia_base, self.geometria.alpha_quiebre, factor_guardia
                            )
                        elif patron_tiro == "dos-unilaterales":
                            if self.geometria.tipo_estructura == "Terminal":
                                tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_dos_unilaterales_terminal(
                                    nodo, config_tiro, tiro_guardia_base, es_guardia=True
                                )
                            else:
                                es_unilateral = (nodo in NODOS_DOS_UNILATERAL)
                                factor_peso_nodo = 0.5 if es_unilateral else 1.0
                                factor_viento_nodo = 0.5 if es_unilateral else 1.0
                                if es_unilateral:
                                    factor_guardia = config_tiro.get("factor_guardia", 1.0)
                                    tiro_trans, tiro_long = self._calcular_componentes_tiro_unilateral(
                                        tiro_guardia_base, self.geometria.alpha_quiebre, factor_guardia
                                    )
                                else:
                                    reduccion_guardia = config_tiro.get("reduccion_guardia", 0.0)
                                    tiro_trans, tiro_long = self._calcular_componentes_tiro(
                                        tiro_guardia_base, self.geometria.alpha_quiebre, reduccion_guardia, True
                                    )
                        else:  # bilateral
                            factor_peso_nodo = 1.0
                            factor_viento_nodo = 1.0
                            reduccion_guardia = config_tiro.get("reduccion_guardia", 0.0)
                            tiro_trans, tiro_long = self._calcular_componentes_tiro(
                                tiro_guardia_base, self.geometria.alpha_quiebre, reduccion_guardia, True
                            )
                        
                        carga_x += tiro_trans
                        carga_y += tiro_long
                        carga_z = -peso_guardia * factor_peso_nodo
                        
                        # VIENTO EN GUARDIA
                        if config["viento"]:
                            direccion_viento = config["viento"]["direccion"]
                            estado_v = config["viento"]["estado"]
                            factor_viento = config["viento"]["factor"]
                            
                            if direccion_viento == "Transversal":
                                if estado_v == "Vmax":
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}")
                                else:
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}med")
                                carga_x += viento_guardia * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Longitudinal":
                                if estado_v == "Vmax":
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}L")
                                else:
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}medL")
                                carga_y += viento_guardia * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Oblicua":
                                es_unilateral = (patron_tiro == "unilateral") or (patron_tiro == "dos-unilaterales" and nodo in NODOS_DOS_UNILATERAL)
                                if es_unilateral:
                                    lado = 1
                                    if estado_v == "Vmax":
                                        viento_guardia_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}_o_t_{lado}")
                                        viento_guardia_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}_o_l_{lado}")
                                    else:
                                        viento_guardia_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}med_o_t_{lado}")
                                        viento_guardia_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}med_o_l_{lado}")
                                    
                                    carga_x += viento_guardia_x * factor_viento * factor_viento_nodo
                                    carga_y += viento_guardia_y * factor_viento * factor_viento_nodo
                                else:
                                    if estado_v == "Vmax":
                                        viento_guardia_x = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg1_o_t_1") + 
                                                          self._obtener_carga_por_codigo(df_cargas_totales, "Vcg1_o_t_2"))
                                        viento_guardia_y = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg1_o_l_1") + 
                                                          self._obtener_carga_por_codigo(df_cargas_totales, "Vcg1_o_l_2"))
                                        if self.geometria.cable_guardia2:
                                            viento_guardia_x += (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg2_o_t_1") + 
                                                              self._obtener_carga_por_codigo(df_cargas_totales, "Vcg2_o_t_2"))
                                            viento_guardia_y += (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg2_o_l_1") + 
                                                              self._obtener_carga_por_codigo(df_cargas_totales, "Vcg2_o_l_2"))
                                    else:
                                        viento_guardia_x = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg1med_o_t_1") + 
                                                          self._obtener_carga_por_codigo(df_cargas_totales, "Vcg1med_o_t_2"))
                                        viento_guardia_y = (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg1med_o_l_1") + 
                                                          self._obtener_carga_por_codigo(df_cargas_totales, "Vcg1med_o_l_2"))
                                        if self.geometria.cable_guardia2:
                                            viento_guardia_x += (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg2med_o_t_1") + 
                                                              self._obtener_carga_por_codigo(df_cargas_totales, "Vcg2med_o_t_2"))
                                            viento_guardia_y += (self._obtener_carga_por_codigo(df_cargas_totales, "Vcg2med_o_l_1") + 
                                                              self._obtener_carga_por_codigo(df_cargas_totales, "Vcg2med_o_l_2"))
                                    
                                    carga_x += viento_guardia_x * factor_viento * factor_viento_nodo
                                    carga_y += viento_guardia_y * factor_viento * factor_viento_nodo
                        
                        cargas_hipotesis[nodo] = [round(carga_x, 2), round(carga_y, 2), round(carga_z, 2)]
                    
                    self.cargas_key[nombre_completo] = cargas_hipotesis
                    print(f"✅ Cargas asignadas: {codigo_hip} - {config['desc']}")
                    
                except Exception as e:
                    print(f"❌ Error en hipótesis {codigo_hip}: {e}")
                    self.cargas_key[nombre_completo] = {nombre: [0.00, 0.00, 0.00] for nombre in self.geometria.nodes_key.keys()}
        else:
            print(f"❌ Tipo de estructura '{self.geometria.tipo_estructura}' no encontrado en hipotesis maestro")
        
        print(f"✅ Asignación completada: {len(self.cargas_key)} hipótesis procesadas")
    
    def generar_dataframe_cargas(self):
        """Genera DataFrame completo de cargas por nodo e hipótesis"""
        print(f"\n📊 GENERANDO DATAFRAME DE CARGAS...")
        
        if not self.cargas_key:
            print("❌ No hay cargas asignadas. Ejecutar asignar_cargas_hipotesis primero.")
            return None
        
        todos_nodos = list(self.geometria.nodes_key.keys())
        clave_busqueda = f"HIP_{self.geometria.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_')}_"
        hipotesis_filtradas = sorted([k for k in self.cargas_key.keys() if k.startswith(clave_busqueda)])
        
        # Crear multi-index
        nivel_superior = [''] * 2
        nivel_inferior = ['Nodo', 'Unidad']
        
        codigos_hipotesis = []
        for hip_larga in hipotesis_filtradas:
            partes = hip_larga.split('_')
            codigo_corto = partes[-3] if len(partes) > 3 else hip_larga
            codigos_hipotesis.append(codigo_corto)
            nivel_superior.extend([codigo_corto] * 3)
            nivel_inferior.extend(['x', 'y', 'z'])
        
        multi_index = pd.MultiIndex.from_arrays([nivel_superior, nivel_inferior])
        
        # Crear filas
        filas = []
        for nodo in todos_nodos:
            fila = [nodo, 'daN']
            
            for hip_larga in hipotesis_filtradas:
                cargas_nodo = self.cargas_key[hip_larga].get(nodo, [0.00, 0.00, 0.00])
                fila.extend(cargas_nodo)
            
            filas.append(fila)
        
        self.df_cargas_completo = pd.DataFrame(filas, columns=multi_index)
        
        print(f"✅ DataFrame creado: {len(self.df_cargas_completo)} nodos × {len(self.df_cargas_completo.columns)} columnas")
        return self.df_cargas_completo
    
    # ================= MÉTODOS DE CÁLCULO DE REACCIONES =================
    
    def calcular_reacciones_tiros_cima(self, nodo_apoyo="BASE", nodo_cima=None):
        """
        Calcula reacciones en el nodo de apoyo y tiros equivalentes en la cima
        
        Args:
            nodo_apoyo (str): Nodo considerado como apoyo (por defecto "BASE")
            nodo_cima (str): Nodo considerado como cima (por defecto se autodetecta)
            
        Returns:
            DataFrame: Resultados de reacciones para todas las hipótesis
        """
        print(f"\n🔧 CÁLCULO DE REACCIONES Y TIROS EN CIMA")
        print(f"   Apoyo: {nodo_apoyo}, Cima: {nodo_cima if nodo_cima else 'Auto-detectar'}")
        
        # 1. DETECTAR NODO CIMA SI NO SE ESPECIFICA
        if nodo_cima is None:
            if "TOP" in self.geometria.nodes_key:
                nodo_cima = "TOP"
            elif "HG1" in self.geometria.nodes_key:
                nodo_cima = "HG1"
            else:
                # Buscar el nodo más alto
                nodo_cima = max(self.geometria.nodes_key.items(), key=lambda x: x[1][2])[0]
        
        # 2. VERIFICAR QUE EXISTEN LOS NODOS
        if nodo_apoyo not in self.geometria.nodes_key:
            raise ValueError(f"Nodo de apoyo '{nodo_apoyo}' no encontrado")
        if nodo_cima not in self.geometria.nodes_key:
            raise ValueError(f"Nodo cima '{nodo_cima}' no encontrado")
        
        # 3. OBTENER COORDENADAS
        x_apoyo, y_apoyo, z_apoyo = self.geometria.nodes_key[nodo_apoyo]
        x_cima, y_cima, z_cima = self.geometria.nodes_key[nodo_cima]
        
        altura_efectiva = z_cima - z_apoyo
        print(f"   Altura efectiva: {altura_efectiva:.2f} m")
        
        # 4. CALCULAR REACCIONES PARA CADA HIPÓTESIS
        self.resultados_reacciones = {}
        
        for nombre_hipotesis, cargas_nodo in self.cargas_key.items():
            # Inicializar reacciones
            Fx, Fy, Fz = 0.0, 0.0, 0.0
            Mx, My, Mz = 0.0, 0.0, 0.0
            
            for nodo, carga in cargas_nodo.items():
                if nodo != nodo_apoyo:  # No considerar el propio nodo de apoyo
                    x, y, z = self.geometria.nodes_key[nodo]
                    Fx_n, Fy_n, Fz_n = carga
                    
                    # Sumatoria de fuerzas
                    Fx += Fx_n
                    Fy += Fy_n
                    Fz += Fz_n
                    
                    # Vector posición relativa
                    rx, ry, rz = x - x_apoyo, y - y_apoyo, z - z_apoyo
                    
                    # Cálculo de momentos - producto vectorial r × F
                    Mx += (ry * Fz_n) - (rz * Fy_n)
                    My += (rz * Fx_n) - (rx * Fz_n)
                    Mz += (rx * Fy_n) - (ry * Fx_n)
            
            # 5. REDUCIR MOMENTOS A TIROS EN CIMA
            Tiro_X = My / altura_efectiva if altura_efectiva > 0 else 0.0
            Tiro_Y = -Mx / altura_efectiva if altura_efectiva > 0 else 0.0
            Tiro_resultante = math.sqrt(Tiro_X**2 + Tiro_Y**2)
            
            # Cálculo del ángulo
            if Tiro_resultante > 0:
                angulo_rad = math.atan2(Tiro_Y, Tiro_X)
                angulo_grados = math.degrees(angulo_rad)
                if angulo_grados < 0:
                    angulo_grados += 360
            else:
                angulo_grados = 0.0
            
            # Almacenar resultados
            self.resultados_reacciones[nombre_hipotesis] = {
                'Reaccion_Fx_daN': round(Fx, 1),
                'Reaccion_Fy_daN': round(Fy, 1),
                'Reaccion_Fz_daN': round(Fz, 1),
                'Reaccion_Mx_daN_m': round(Mx, 1),
                'Reaccion_My_daN_m': round(My, 1),
                'Reaccion_Mz_daN_m': round(Mz, 1),
                'Tiro_X_daN': round(Tiro_X, 1),
                'Tiro_Y_daN': round(Tiro_Y, 1),
                'Tiro_resultante_daN': round(Tiro_resultante, 1),
                'Angulo_grados': round(angulo_grados, 1),
                'Nodo_apoyo': nodo_apoyo,
                'Nodo_cima': nodo_cima,
                'Altura_efectiva_m': round(altura_efectiva, 2)
            }
        
        # 6. CREAR DATAFRAME CON RESULTADOS
        self.df_reacciones = pd.DataFrame.from_dict(self.resultados_reacciones, orient='index')
        
        print(f"✅ Cálculo completado: {len(self.resultados_reacciones)} hipótesis procesadas")
        return self.df_reacciones
    
    def imprimir_reacciones_tiros(self, mostrar_c2=True):
        """
        Imprime tabla resumen de reacciones y tiros en cima
        """
        if self.df_reacciones is None:
            print("❌ No hay datos de reacciones. Ejecutar calcular_reacciones_tiros_cima primero.")
            return
        
        print(f"\n{'='*120}")
        print("TABLA RESUMEN - REACCIONES Y TIROS EQUIVALENTES EN LA CIMA")
        print(f"{'='*120}")
        
        # Filtrar hipótesis C2 si corresponde
        df_mostrar = self.df_reacciones.copy()
        if not mostrar_c2:
            df_mostrar = df_mostrar[~df_mostrar.index.str.contains('_C2_')]
        
        # Crear tabla formateada
        tabla_resumen = []
        for hipotesis, datos in df_mostrar.iterrows():
            # Extraer código corto de hipótesis
            codigo = hipotesis.split('_')[-2] if len(hipotesis.split('_')) >= 2 else hipotesis
            
            fila = [
                codigo,
                f"{datos['Reaccion_Fx_daN']:7.1f}",
                f"{datos['Reaccion_Fy_daN']:7.1f}",
                f"{datos['Reaccion_Fz_daN']:7.1f}",
                f"{datos['Reaccion_Mx_daN_m']:7.1f}",
                f"{datos['Reaccion_My_daN_m']:7.1f}",
                f"{datos['Reaccion_Mz_daN_m']:7.1f}",
                f"{datos['Tiro_X_daN']:6.1f}",
                f"{datos['Tiro_Y_daN']:6.1f}",
                f"{datos['Tiro_resultante_daN']:6.1f}",
                f"{datos['Angulo_grados']:5.1f}"
            ]
            tabla_resumen.append(fila)
        
        # Encabezados
        headers = ["Hipótesis", "Fx [daN]", "Fy [daN]", "Fz [daN]", "Mx [daN·m]", "My [daN·m]", "Mz [daN·m]", 
                  "Tiro_X [daN]", "Tiro_Y [daN]", "Tiro_Res [daN]", "Ángulo [°]"]
        
        # Mostrar tabla
        try:
            from tabulate import tabulate
            print(tabulate(tabla_resumen, headers=headers, tablefmt='grid'))
        except ImportError:
            # Tabla básica
            print(" | ".join(headers))
            print("-" * len(" | ".join(headers)))
            for fila in tabla_resumen:
                print(" | ".join(fila))
        
        # RESUMEN EJECUTIVO
        print(f"\n{'='*80}")
        print("RESUMEN EJECUTIVO")
        print(f"{'='*80}")
        
        max_tiro = df_mostrar['Tiro_resultante_daN'].max()
        max_fz = df_mostrar['Reaccion_Fz_daN'].max()
        hip_max_tiro = df_mostrar['Tiro_resultante_daN'].idxmax()
        hip_max_fz = df_mostrar['Reaccion_Fz_daN'].idxmax()
        
        print(f"Estructura: {self.geometria.tension_nominal}kV - {self.geometria.tipo_estructura}")
        print(f"Altura efectiva: {df_mostrar['Altura_efectiva_m'].iloc[0]:.2f} m")
        print(f"Nodo apoyo: {df_mostrar['Nodo_apoyo'].iloc[0]}, Nodo cima: {df_mostrar['Nodo_cima'].iloc[0]}")
        print(f"\n🔴 Hipótesis más desfavorable por tiro en cima:")
        print(f"   {hip_max_tiro}: {max_tiro:.1f} daN")
        print(f"\n🔴 Hipótesis más desfavorable por carga vertical:")
        print(f"   {hip_max_fz}: {max_fz:.1f} daN")
    
    def guardar_resultados_mecanica(self, folder):
        """Guarda los resultados mecánicos en archivos CSV"""
        import os
        
        print(f"\n💾 GUARDANDO RESULTADOS MECÁNICOS...")
        os.makedirs(folder, exist_ok=True)
        
        # 1. Guardar cargas si existen
        if self.df_cargas_completo is not None:
            ruta_cargas = f"{folder}/8_{self.geometria.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_').lower()}_CARGAS_POO.csv"
            self.df_cargas_completo.to_csv(ruta_cargas, index=False, encoding='utf-8')
            print(f"✅ Cargas guardadas: {ruta_cargas}")
        
        # 2. Guardar resultados de reacciones si existen
        if self.df_reacciones is not None:
            ruta_reacciones = f"{folder}/10_{self.geometria.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_').lower()}_REACCIONES_POO.csv"
            self.df_reacciones.to_csv(ruta_reacciones, encoding='utf-8')
            print(f"✅ Reacciones guardadas: {ruta_reacciones}")
        
        print(f"✅ Resultados mecánicos guardados en: {folder}")