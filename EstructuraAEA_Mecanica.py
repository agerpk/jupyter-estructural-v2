# EstructuraAEA_Mecanica.py
import pandas as pd
import math
import logging
from NodoEstructural import Carga

logger = logging.getLogger(__name__)

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
        
        # Para almacenar resultados de reacciones
        self.resultados_reacciones = {}
        self.df_reacciones = None

        # Registrar hipótesis A5 que aplicaron reducción 15% para trazabilidad
        self.hipotesis_a5_aplico_15pc = []
        
        print(f"✅ ESTRUCTURA_AEA MECÁNICA CREADA")
    
    # ================= MÉTODOS DE CÁLCULO DE CARGAS =================
    
    def _rotar_carga_eje_z(self, fx, fy, fz, angulo_grados):
        """
        Rota un vector de carga en el eje Z (plano XY)
        
        Args:
            fx (float): Componente X de la carga
            fy (float): Componente Y de la carga
            fz (float): Componente Z de la carga (no se modifica)
            angulo_grados (float): Ángulo de rotación en grados (antihorario positivo)
        
        Returns:
            tuple: (fx_rot, fy_rot, fz)
        """
        ang_rad = math.radians(angulo_grados)
        fx_rot = fx * math.cos(ang_rad) - fy * math.sin(ang_rad)
        fy_rot = fx * math.sin(ang_rad) + fy * math.cos(ang_rad)
        return fx_rot, fy_rot, fz
    
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
                valor = df_cargas_totales[filtro]['Magnitud'].iloc[0]
                return valor
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
            nodes_dict = self.geometria.obtener_nodos_dict()
            nodos_guardia = [n for n in nodes_dict.keys() if n.startswith('HG')]
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
            nodes_dict = self.geometria.obtener_nodos_dict()
            nodos_conductor = [n for n in nodes_dict.keys() if n.startswith(('C1_', 'C2_', 'C3_'))]
            
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
                                 t_hielo, hipotesis_a_incluir="Todas", resultados_guardia2=None, 
                                 estados_climaticos=None):
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
        print(f"   🔍 cable_guardia1: {self.geometria.cable_guardia1.nombre if self.geometria.cable_guardia1 else 'None'}")
        print(f"   🔍 cable_guardia2: {self.geometria.cable_guardia2.nombre if self.geometria.cable_guardia2 else 'None'}")
        print(f"   🔍 resultados_guardia2: {'SÍ' if resultados_guardia2 else 'NO'}")
        
        # DEBUG: Imprimir df_cargas_totales COMPLETO para ver todos los valores
        print(f"\n🔍 DEBUG df_cargas_totales recibido en asignar_cargas_hipotesis:")
        if df_cargas_totales is not None:
            print(f"\n{df_cargas_totales.to_string()}")
            print(f"\n   Total filas: {len(df_cargas_totales)}")
            # Filtrar solo las filas de viento en conductor
            filas_vc = df_cargas_totales[df_cargas_totales['Código'].str.contains('Vc', na=False)]
            print(f"\n   Filas con 'Vc' en código ({len(filas_vc)} filas):")
            for idx, row in filas_vc.iterrows():
                print(f"      {row['Código']}: {row['Magnitud']:.2f} daN - {row['Carga']}")
        else:
            print("   ❌ df_cargas_totales es None")
        # Verificar si se debe anular cargas de una terna
        anular_terna_negativa_x = False
        if (hasattr(self.geometria, 'doble_terna_una_terna_activa') and 
            self.geometria.doble_terna_una_terna_activa):
            anular_terna_negativa_x = True
            print("⚠️  Doble terna con una terna activa: anulando cargas de la terna del lado negativo X")
        
        # Pesos base globales (fallback)
        peso_conductor_base_global = self.geometria.cable_conductor.peso_unitario_dan_m
        peso_guardia1_base_global = self.geometria.cable_guardia1.peso_unitario_dan_m
        
        # Pesos con hielo globales (fallback)
        peso_hielo_conductor_global = self.geometria.cable_conductor._calcular_peso_hielo(t_hielo)
        peso_hielo_guardia1_global = self.geometria.cable_guardia1._calcular_peso_hielo(t_hielo)
        
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
                nodes_dict = self.geometria.obtener_nodos_dict()
                cargas_hipotesis = {nombre: [0.00, 0.00, 0.00] for nombre in nodes_dict.keys()}
                
                try:
                    # Inicializar cargas por tipo en cada nodo
                    for nodo_nombre in nodes_dict.keys():
                        if nodo_nombre in self.geometria.nodos:
                            nodo = self.geometria.nodos[nodo_nombre]
                            # Crear cargas por tipo si no existen
                            if not nodo.obtener_carga("Peso"):
                                nodo.agregar_carga(Carga(nombre="Peso"))
                            if not nodo.obtener_carga("Viento"):
                                nodo.agregar_carga(Carga(nombre="Viento"))
                            if not nodo.obtener_carga("Tiro"):
                                nodo.agregar_carga(Carga(nombre="Tiro"))
                    
                    # Obtener estados usando SelectorEstados
                    from utils.selector_estados import SelectorEstados
                    
                    # Mapeo de nombres legacy a funciones selectoras
                    MAPEO_FUNCIONES = {
                        "TMA": "buscar_tma_equivalente",
                        "Tmin": "buscar_tmin_equivalente",
                        "Vmax": "buscar_vmax_equivalente",
                        "Vmed": "buscar_hielo_max",
                        "maximo": "buscar_max_tiro"
                    }
                    
                    estado_viento = None
                    if config["viento"]:
                        estado_viento_config = config["viento"]["estado"]
                        # Traducir nombre legacy a función
                        nombre_funcion = MAPEO_FUNCIONES.get(estado_viento_config, estado_viento_config)
                        if not hasattr(SelectorEstados, nombre_funcion):
                            raise ValueError(f"Función '{nombre_funcion}' no existe en SelectorEstados")
                        funcion_viento = getattr(SelectorEstados, nombre_funcion)
                        estado_viento = funcion_viento(estados_climaticos if estados_climaticos else self.geometria.estados_climaticos)
                    
                    estado_tiro = None
                    if config["tiro"]:
                        estado_tiro_config = config["tiro"]["estado"]
                        # Traducir nombre legacy a función
                        nombre_funcion = MAPEO_FUNCIONES.get(estado_tiro_config, estado_tiro_config)
                        if not hasattr(SelectorEstados, nombre_funcion):
                            raise ValueError(f"Función '{nombre_funcion}' no existe en SelectorEstados")
                        funcion_tiro = getattr(SelectorEstados, nombre_funcion)
                        
                        # buscar_max_tiro requiere resultados CMC
                        if nombre_funcion == "buscar_max_tiro":
                            estado_tiro = funcion_tiro(resultados_conductor)
                        else:
                            estado_tiro = funcion_tiro(estados_climaticos if estados_climaticos else self.geometria.estados_climaticos)
                    
                    config_tiro = config["tiro"] if config["tiro"] else None
                    patron_tiro = config_tiro["patron"] if config_tiro else "bilateral"
                    
                    # Ajuste por HIPÓTESIS A5: si corresponde y Lk>2.5 y parámetro activo -> reduccion_cond = 0.15
                    if config_tiro and ((codigo_hip == "A5") or (config.get("desc", "").lower().startswith("tiro unilateral"))):
                        if getattr(self.geometria, "hipotesis_a5_dme_15pc_si_lk_mayor_2_5", True) and getattr(self.geometria, "lk", 0) > 2.5:
                            prev_val = config_tiro.get("reduccion_cond", None)
                            config_tiro["reduccion_cond"] = 0.15
                            logger.info(f"HIPÓTESIS A5: Lk={self.geometria.lk} > 2.5 -> reduccion_cond {prev_val} -> 0.15")
                            # Registrar para memoria/trazabilidad
                            try:
                                # Usar nombre legible de hipótesis
                                self.hipotesis_a5_aplico_15pc.append(nombre_completo)
                            except Exception:
                                # No causar fallo si por alguna razón no existe la lista
                                pass

                    factor_peso = config["peso"]["factor"]
                    
                    # Calcular pesos globales (solo para guardias, conductores se calculan por nodo)
                    if config["peso"]["hielo"]:
                        peso_guardia1 = (peso_guardia1_base_global + peso_hielo_guardia1_global) * vano * factor_peso
                        if self.geometria.cable_guardia2:
                            peso_guardia2 = (peso_guardia2_base + peso_hielo_guardia2) * vano * factor_peso
                    else:
                        peso_guardia1 = peso_guardia1_base_global * vano * factor_peso
                        if self.geometria.cable_guardia2:
                            peso_guardia2 = peso_guardia2_base * vano * factor_peso
                    
                    # Obtener tiros usando estado resuelto
                    tiro_guardia2_base = None
                    
                    if estado_tiro:
                        if estado_tiro not in resultados_conductor:
                            raise ValueError(f"Estado {estado_tiro} no encontrado en resultados de conductor")
                        if estado_tiro not in resultados_guardia1:
                            raise ValueError(f"Estado {estado_tiro} no encontrado en resultados de guardia1")
                        
                        tiro_cond_base = resultados_conductor[estado_tiro]["tiro_daN"]
                        tiro_guardia1_base = resultados_guardia1[estado_tiro]["tiro_daN"]
                        
                        if resultados_guardia2:
                            if estado_tiro not in resultados_guardia2:
                                raise ValueError(f"Estado {estado_tiro} no encontrado en resultados de guardia2")
                            tiro_guardia2_base = resultados_guardia2[estado_tiro]["tiro_daN"]
                    else:
                        logger.warning(f"HIPÓTESIS {nombre_completo} NO TIENE TIROS")
                        tiro_cond_base = 0.0
                        tiro_guardia1_base = 0.0
                        if resultados_guardia2:
                            tiro_guardia2_base = 0.0
                    
                    # VIENTO SOBRE ESTRUCTURA (solo nodo V)
                    if config["viento"]:
                        direccion_viento = config["viento"]["direccion"]
                        factor_viento = config["viento"]["factor"]
                        
                        # Determinar si es Vmax o Vmed basado en estado_viento resuelto
                        es_vmax = (estado_viento and estado_viento in ['III', '3']) if estado_viento else False
                        
                        if direccion_viento == "Transversal":
                            if es_vmax:
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "VeT")
                            else:
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "Vemedt")
                            cargas_hipotesis['V'] = [viento_estructura * factor_viento, 0.0, 0.0]
                            
                        elif direccion_viento == "Longitudinal":
                            if es_vmax:
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "VeL")
                            else:
                                viento_estructura = self._obtener_carga_por_codigo(df_cargas_totales, "Vemedl")
                            cargas_hipotesis['V'] = [0.0, viento_estructura * factor_viento, 0.0]
                            
                        elif direccion_viento == "Oblicua":
                            if es_vmax:
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
                        
                        # Aplicar al nodo V o Viento
                        nodo_viento = 'V' if 'V' in self.geometria.nodos else ('Viento' if 'Viento' in self.geometria.nodos else None)
                        if nodo_viento:
                            nodo_v = self.geometria.nodos[nodo_viento]
                            nodo_v.obtener_carga("Viento").agregar_hipotesis(nombre_completo, cargas_hipotesis['V'][0], cargas_hipotesis['V'][1], cargas_hipotesis['V'][2])
                            if not hasattr(nodo_v, 'cargas_dict'):
                                nodo_v.cargas_dict = {}
                            nodo_v.cargas_dict[nombre_completo] = cargas_hipotesis['V']
                    
                    # CARGAS EN CONDUCTORES
                    nodos_conductor = [n for n in nodes_dict.keys() if n.startswith(('C1', 'C2', 'C3')) and not n.startswith('CROSS')]
                    
                    for nodo_nombre in nodos_conductor:
                        # ANULAR CARGAS SI NODO EN LADO X- Y PARÁMETRO ACTIVO
                        nodo_obj = self.geometria.nodos.get(nodo_nombre)
                        if anular_terna_negativa_x and nodo_obj and nodo_obj.x < 0:
                            # Nodo en lado X negativo - anular todas las cargas
                            nodo_obj.obtener_carga("Peso").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
                            nodo_obj.obtener_carga("Viento").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
                            nodo_obj.obtener_carga("Tiro").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
                            
                            if not hasattr(nodo_obj, 'cargas_dict'):
                                nodo_obj.cargas_dict = {}
                            nodo_obj.cargas_dict[nombre_completo] = [0.0, 0.0, 0.0]
                            cargas_hipotesis[nodo_nombre] = [0.0, 0.0, 0.0]
                            continue  # Saltar al siguiente nodo
                        
                        peso_x, peso_y, peso_z = 0.0, 0.0, 0.0
                        viento_x, viento_y, viento_z = 0.0, 0.0, 0.0
                        tiro_x, tiro_y, tiro_z = 0.0, 0.0, 0.0
                        
                        # Obtener nodo y cable específico
                        nodo_obj = self.geometria.nodos.get(nodo_nombre)
                        if nodo_obj and nodo_obj.cable_asociado:
                            peso_conductor_base = nodo_obj.cable_asociado.peso_unitario_dan_m
                            peso_hielo_conductor = nodo_obj.cable_asociado._calcular_peso_hielo(t_hielo)
                        else:
                            peso_conductor_base = peso_conductor_base_global
                            peso_hielo_conductor = peso_hielo_conductor_global
                        
                        # Calcular peso del conductor para este nodo
                        if config["peso"]["hielo"]:
                            peso_cond = (peso_conductor_base + peso_hielo_conductor) * vano * factor_peso
                        else:
                            peso_cond = peso_conductor_base * vano * factor_peso

                        if patron_tiro == "doble-terna-a-simple":
                            # Para conductores: aplicar patrón doble-terna-a-simple
                            tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_doble_terna_a_simple(
                                nodo_nombre, config_tiro, tiro_cond_base, es_guardia=False
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
                                    nodo_nombre, config_tiro, tiro_cond_base, es_guardia=False
                                )
                            else:
                                # Comportamiento original
                                es_unilateral = (nodo_nombre in NODOS_DOS_UNILATERAL)
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
                        
                        # Separar componentes por tipo
                        tiro_x = tiro_trans
                        tiro_y = tiro_long
                        tiro_z = 0.0
                        
                        # ROTAR TIRO si el cable tiene rotacion_eje_z
                        if nodo_obj and nodo_obj.rotacion_eje_z != 0:
                            rz = math.radians(nodo_obj.rotacion_eje_z)
                            tiro_x_rot = tiro_trans * math.cos(rz) - tiro_long * math.sin(rz)
                            tiro_y_rot = tiro_trans * math.sin(rz) + tiro_long * math.cos(rz)
                            tiro_x, tiro_y = tiro_x_rot, tiro_y_rot
                        
                        peso_x = 0.0
                        peso_y = 0.0
                        peso_z = -peso_cond * factor_peso_nodo
                        
                        # VIENTO EN CABLES
                        if config["viento"]:
                            direccion_viento = config["viento"]["direccion"]
                            factor_viento = config["viento"]["factor"]
                            
                            # Determinar si es Vmax o Vmed basado en el estado climático resuelto
                            es_vmax = (estado_viento and estado_viento in ['III', '3']) if estado_viento else False
                            
                            if direccion_viento == "Transversal":
                                if es_vmax:
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "Vc")
                                else:
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "Vcmed")
                                viento_x += viento_cond * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Longitudinal":
                                if es_vmax:
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "VcL")
                                else:
                                    viento_cond = self._obtener_carga_por_codigo(df_cargas_totales, "VcmedL")
                                viento_y += viento_cond * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Oblicua":
                                lado = 1 if "L" in nodo_nombre else 2
                                if es_vmax:
                                    viento_cond_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vc_o_t_{lado}")
                                    viento_cond_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vc_o_l_{lado}")
                                else:
                                    viento_cond_x = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcmed_o_t_{lado}")
                                    viento_cond_y = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcmed_o_l_{lado}")
                                viento_x += viento_cond_x * factor_viento * factor_viento_nodo
                                viento_y += viento_cond_y * factor_viento * factor_viento_nodo
                            
                            # VIENTO EN CADENA (solo para conductores)
                            if direccion_viento == "Transversal":
                                if es_vmax:
                                    viento_cadena = self._obtener_carga_por_codigo(df_cargas_totales, "VaT")
                                else:
                                    viento_cadena = self._obtener_carga_por_codigo(df_cargas_totales, "VamedT")
                                viento_x += viento_cadena * factor_viento * factor_viento_nodo
                            elif direccion_viento == "Longitudinal":
                                if es_vmax:
                                    viento_cadena = self._obtener_carga_por_codigo(df_cargas_totales, "VaL")
                                else:
                                    viento_cadena = self._obtener_carga_por_codigo(df_cargas_totales, "VamedL")
                                viento_y += viento_cadena * factor_viento * factor_viento_nodo
                            elif direccion_viento == "Oblicua":
                                if es_vmax:
                                    viento_cadena_x = self._obtener_carga_por_codigo(df_cargas_totales, "VaoT")
                                    viento_cadena_y = self._obtener_carga_por_codigo(df_cargas_totales, "VaoL")
                                else:
                                    viento_cadena_x = self._obtener_carga_por_codigo(df_cargas_totales, "VaoTmed")
                                    viento_cadena_y = self._obtener_carga_por_codigo(df_cargas_totales, "VaoLmed")
                                viento_x += viento_cadena_x * factor_viento * factor_viento_nodo
                                viento_y += viento_cadena_y * factor_viento * factor_viento_nodo
                        
                        # SOBRECARGA ADICIONAL
                        if config["sobrecarga"] and nodo_nombre == "C1_L":
                            peso_z -= config["sobrecarga"]
                        
                        # Guardar cargas separadas por tipo en el nodo (nodo_obj ya obtenido arriba)
                        nodo_obj.obtener_carga("Peso").agregar_hipotesis(nombre_completo, peso_x, peso_y, peso_z)
                        nodo_obj.obtener_carga("Viento").agregar_hipotesis(nombre_completo, viento_x, viento_y, viento_z)
                        nodo_obj.obtener_carga("Tiro").agregar_hipotesis(nombre_completo, tiro_x, tiro_y, tiro_z)
                        
                        # Guardar total en cargas_dict (compatibilidad)
                        if not hasattr(nodo_obj, 'cargas_dict'):
                            nodo_obj.cargas_dict = {}
                        carga_total_x = round(peso_x + viento_x + tiro_x, 2)
                        carga_total_y = round(peso_y + viento_y + tiro_y, 2)
                        carga_total_z = round(peso_z + viento_z + tiro_z, 2)
                        nodo_obj.cargas_dict[nombre_completo] = [carga_total_x, carga_total_y, carga_total_z]
                        cargas_hipotesis[nodo_nombre] = [carga_total_x, carga_total_y, carga_total_z]
                    
                    # CARGAS EN GUARDIA
                    nodos_guardia = [n for n in nodes_dict.keys() if n.startswith('HG')]
                    
                    for nodo_nombre in nodos_guardia:
                        # ANULAR CARGAS SI NODO EN LADO X- Y PARÁMETRO ACTIVO
                        nodo_obj = self.geometria.nodos.get(nodo_nombre)
                        if anular_terna_negativa_x and nodo_obj and nodo_obj.x < 0:
                            # Nodo en lado X negativo - anular todas las cargas
                            nodo_obj.obtener_carga("Peso").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
                            nodo_obj.obtener_carga("Viento").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
                            nodo_obj.obtener_carga("Tiro").agregar_hipotesis(nombre_completo, 0.0, 0.0, 0.0)
                            
                            if not hasattr(nodo_obj, 'cargas_dict'):
                                nodo_obj.cargas_dict = {}
                            nodo_obj.cargas_dict[nombre_completo] = [0.0, 0.0, 0.0]
                            cargas_hipotesis[nodo_nombre] = [0.0, 0.0, 0.0]
                            continue  # Saltar al siguiente nodo
                        
                        peso_x, peso_y, peso_z = 0.0, 0.0, 0.0
                        viento_x, viento_y, viento_z = 0.0, 0.0, 0.0
                        tiro_x, tiro_y, tiro_z = 0.0, 0.0, 0.0
                        
                        # Obtener nodo y cable específico
                        nodo_obj = self.geometria.nodos.get(nodo_nombre)
                        if nodo_obj and nodo_obj.cable_asociado:
                            # Usar cable específico del nodo
                            peso_guardia_base_nodo = nodo_obj.cable_asociado.peso_unitario_dan_m
                            peso_hielo_guardia_nodo = nodo_obj.cable_asociado._calcular_peso_hielo(t_hielo)
                            
                            # Determinar si es cable_guardia1 o cable_guardia2
                            if nodo_obj.cable_asociado == self.geometria.cable_guardia2:
                                tiro_guardia_base = tiro_guardia2_base if resultados_guardia2 else tiro_guardia1_base
                                sufijo_viento = "2"
                                print(f"   🔵 {nodo_nombre}: cable={nodo_obj.cable_asociado.nombre}, peso={peso_guardia_base_nodo}, tiro={tiro_guardia_base}, sufijo={sufijo_viento}")
                            else:
                                tiro_guardia_base = tiro_guardia1_base
                                sufijo_viento = "1"
                                print(f"   🔵 {nodo_nombre}: cable={nodo_obj.cable_asociado.nombre}, peso={peso_guardia_base_nodo}, tiro={tiro_guardia_base}, sufijo={sufijo_viento}")
                        else:
                            # Lógica global original
                            if nodo_nombre == "HG1" or (nodo_nombre.startswith("HG") and nodes_dict[nodo_nombre][0] > 0):
                                peso_guardia_base_nodo = peso_guardia1_base_global
                                peso_hielo_guardia_nodo = peso_hielo_guardia1_global
                                tiro_guardia_base = tiro_guardia1_base
                                sufijo_viento = "1"
                            else:
                                peso_guardia_base_nodo = peso_guardia2_base if self.geometria.cable_guardia2 else peso_guardia1_base_global
                                peso_hielo_guardia_nodo = peso_hielo_guardia2 if self.geometria.cable_guardia2 else peso_hielo_guardia1_global
                                tiro_guardia_base = tiro_guardia2_base if resultados_guardia2 else tiro_guardia1_base
                                sufijo_viento = "2" if self.geometria.cable_guardia2 else "1"
                        
                        # Calcular peso del guardia para este nodo
                        if config["peso"]["hielo"]:
                            peso_guardia = (peso_guardia_base_nodo + peso_hielo_guardia_nodo) * vano * factor_peso
                        else:
                            peso_guardia = peso_guardia_base_nodo * vano * factor_peso

                        if patron_tiro == "doble-terna-a-simple":
                            tiro_trans, tiro_long, factor_peso_nodo, factor_viento_nodo = self._aplicar_patron_doble_terna_a_simple(
                                nodo_nombre, config_tiro, tiro_guardia_base, es_guardia=True
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
                                    nodo_nombre, config_tiro, tiro_guardia_base, es_guardia=True
                                )
                            else:
                                es_unilateral = (nodo_nombre in NODOS_DOS_UNILATERAL)
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
                        
                        # Separar componentes por tipo
                        tiro_x = tiro_trans
                        tiro_y = tiro_long
                        tiro_z = 0.0
                        
                        # ROTAR TIRO si el cable tiene rotacion_eje_z
                        if nodo_obj and nodo_obj.rotacion_eje_z != 0:
                            rz = math.radians(nodo_obj.rotacion_eje_z)
                            tiro_x_rot = tiro_trans * math.cos(rz) - tiro_long * math.sin(rz)
                            tiro_y_rot = tiro_trans * math.sin(rz) + tiro_long * math.cos(rz)
                            tiro_x, tiro_y = tiro_x_rot, tiro_y_rot
                        
                        peso_x = 0.0
                        peso_y = 0.0
                        peso_z = -peso_guardia * factor_peso_nodo
                        
                        # VIENTO EN GUARDIA
                        if config["viento"]:
                            direccion_viento = config["viento"]["direccion"]
                            factor_viento = config["viento"]["factor"]
                            
                            # Determinar si es Vmax o Vmed basado en el estado climático resuelto
                            es_vmax = (estado_viento and estado_viento in ['III', '3']) if estado_viento else False
                            
                            if direccion_viento == "Transversal":
                                if es_vmax:
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}")
                                else:
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}med")
                                viento_x += viento_guardia * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Longitudinal":
                                if es_vmax:
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}L")
                                else:
                                    viento_guardia = self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}medL")
                                viento_y += viento_guardia * factor_viento * factor_viento_nodo
                                
                            elif direccion_viento == "Oblicua":
                                if es_vmax:
                                    viento_guardia_x = (self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}_o_t_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}_o_t_2"))
                                    viento_guardia_y = (self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}_o_l_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}_o_l_2"))
                                else:
                                    viento_guardia_x = (self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}med_o_t_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}med_o_t_2"))
                                    viento_guardia_y = (self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}med_o_l_1") + 
                                                       self._obtener_carga_por_codigo(df_cargas_totales, f"Vcg{sufijo_viento}med_o_l_2"))
                                viento_x += viento_guardia_x * factor_viento * factor_viento_nodo
                                viento_y += viento_guardia_y * factor_viento * factor_viento_nodo
                        
                        # Guardar cargas separadas por tipo en el nodo (nodo_obj ya obtenido arriba)
                        nodo_obj.obtener_carga("Peso").agregar_hipotesis(nombre_completo, peso_x, peso_y, peso_z)
                        nodo_obj.obtener_carga("Viento").agregar_hipotesis(nombre_completo, viento_x, viento_y, viento_z)
                        nodo_obj.obtener_carga("Tiro").agregar_hipotesis(nombre_completo, tiro_x, tiro_y, tiro_z)
                        
                        # Guardar total en cargas_dict (compatibilidad)
                        if not hasattr(nodo_obj, 'cargas_dict'):
                            nodo_obj.cargas_dict = {}
                        carga_total_x = round(peso_x + viento_x + tiro_x, 2)
                        carga_total_y = round(peso_y + viento_y + tiro_y, 2)
                        carga_total_z = round(peso_z + viento_z + tiro_z, 2)
                        nodo_obj.cargas_dict[nombre_completo] = [carga_total_x, carga_total_y, carga_total_z]
                        cargas_hipotesis[nodo_nombre] = [carga_total_x, carga_total_y, carga_total_z]
                    
                    print(f"✅ Cargas asignadas: {codigo_hip} - {config['desc']}")
                    
                except Exception as e:
                    print(f"❌ Error en hipótesis {codigo_hip}: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print(f"❌ Tipo de estructura '{self.geometria.tipo_estructura}' no encontrado en hipotesis maestro")
        
        # Contar hipótesis desde nodos
        hipotesis_count = len(self._obtener_lista_hipotesis())
        print(f"✅ Asignación completada: {hipotesis_count} hipótesis procesadas")
    
    def _obtener_lista_hipotesis(self):
        """Obtiene lista de todas las hipótesis desde los nodos"""
        hipotesis_set = set()
        for nodo in self.geometria.nodos.values():
            hipotesis_set.update(nodo.listar_hipotesis())
        return sorted(list(hipotesis_set))
    
    def generar_dataframe_cargas(self):
        """Genera DataFrame completo de cargas por nodo e hipótesis"""
        print(f"\n📊 GENERANDO DATAFRAME DE CARGAS...")
        
        # Verificar que las cargas estén en los nodos
        nodos_con_cargas = sum(1 for nodo in self.geometria.nodos.values() 
                              if (hasattr(nodo, 'cargas_dict') and nodo.cargas_dict) or nodo.cargas)
        print(f"   🔍 Nodos con cargas: {nodos_con_cargas}/{len(self.geometria.nodos)}")
        
        if nodos_con_cargas == 0:
            print("❌ No hay cargas asignadas. Ejecutar asignar_cargas_hipotesis primero.")
            return None
        
        nodes_dict = self.geometria.obtener_nodos_dict()
        todos_nodos = list(nodes_dict.keys())
        
        # Obtener hipótesis desde nodos
        todas_hipotesis = self._obtener_lista_hipotesis()
        clave_busqueda = f"HIP_{self.geometria.tipo_estructura.replace(' ', '_').replace('ó','o').replace('/','_')}_"
        hipotesis_filtradas = sorted([k for k in todas_hipotesis if k.startswith(clave_busqueda)])
        
        if not hipotesis_filtradas:
            print("❌ No hay hipótesis asignadas")
            return None
        
        # Crear multi-index
        nivel_superior = [''] * 2
        nivel_inferior = ['Nodo', 'Unidad']
        
        codigos_hipotesis = []
        for hip_larga in hipotesis_filtradas:
            # Extraer código corto de hipótesis (penúltimo token) — funciona con tipos que contienen '_' en el nombre
            partes = hip_larga.split('_')
            if len(partes) >= 2:
                codigo_corto = partes[-2]
            else:
                codigo_corto = hip_larga
            codigos_hipotesis.append(codigo_corto)
            nivel_superior.extend([codigo_corto] * 3)
            nivel_inferior.extend(['x', 'y', 'z'])
        
        multi_index = pd.MultiIndex.from_arrays([nivel_superior, nivel_inferior])
        # Nombrar niveles para facilitar visualización (Hipótesis / Componente)
        try:
            multi_index.names = ['Hipótesis', 'Componente']
        except Exception:
            pass
        
        # Crear filas desde nodos
        filas = []
        for nodo_nombre in todos_nodos:
            fila = [nodo_nombre, 'daN']
            nodo = self.geometria.nodos.get(nodo_nombre)
            
            for hip_larga in hipotesis_filtradas:
                if nodo:
                    cargas = nodo.obtener_cargas_hipotesis(hip_larga)
                    fila.extend([cargas["fx"], cargas["fy"], cargas["fz"]])
                else:
                    fila.extend([0.00, 0.00, 0.00])
            
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
        nodes_dict = self.geometria.obtener_nodos_dict()
        if nodo_cima is None:
            if "TOP" in nodes_dict:
                nodo_cima = "TOP"
            elif "HG1" in nodes_dict:
                nodo_cima = "HG1"
            else:
                # Buscar el nodo más alto
                nodo_cima = max(nodes_dict.items(), key=lambda x: x[1][2])[0]
        
        # 2. VERIFICAR QUE EXISTEN LOS NODOS
        if nodo_apoyo not in nodes_dict:
            raise ValueError(f"Nodo de apoyo '{nodo_apoyo}' no encontrado")
        if nodo_cima not in nodes_dict:
            raise ValueError(f"Nodo cima '{nodo_cima}' no encontrado")
        
        # 3. OBTENER COORDENADAS
        x_apoyo, y_apoyo, z_apoyo = nodes_dict[nodo_apoyo]
        x_cima, y_cima, z_cima = nodes_dict[nodo_cima]
        
        altura_efectiva = z_cima - z_apoyo
        print(f"   Altura efectiva: {altura_efectiva:.2f} m")
        
        # 4. CALCULAR REACCIONES PARA CADA HIPÓTESIS
        self.resultados_reacciones = {}
        todas_hipotesis = self._obtener_lista_hipotesis()
        
        for nombre_hipotesis in todas_hipotesis:
            # Inicializar reacciones
            Fx, Fy, Fz = 0.0, 0.0, 0.0
            Mx, My, Mz = 0.0, 0.0, 0.0
            
            # Iterar sobre todos los nodos
            for nodo_nombre in nodes_dict.keys():
                if nodo_nombre != nodo_apoyo:  # No considerar el propio nodo de apoyo
                    x, y, z = nodes_dict[nodo_nombre]
                    
                    # Obtener nodo y sus cargas
                    nodo_obj = self.geometria.nodos.get(nodo_nombre)
                    if not nodo_obj:
                        continue
                    
                    # Obtener cargas (ya rotadas durante asignar_cargas_hipotesis)
                    cargas = nodo_obj.obtener_cargas_hipotesis(nombre_hipotesis)
                    Fx_n = cargas["fx"]
                    Fy_n = cargas["fy"]
                    Fz_n = cargas["fz"]
                    
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
