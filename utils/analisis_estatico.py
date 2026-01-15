"""
Análisis Estático de Esfuerzos (AEE) usando OpenSeesPy
Calcula esfuerzos en barras de estructura con propiedades E, I, A simuladas
"""

import numpy as np
import openseespy.opensees as ops
import logging
from typing import Dict, List, Tuple, Optional

# Importar funciones de plotting
from utils.analisis_estatico_plots import (
    generar_diagrama_matplotlib_3d,
    generar_diagrama_matplotlib_2d, 
    generar_diagrama_mqnt_matplotlib,
    generar_diagrama_ejes_locales_matplotlib
)

# Logger básico para este módulo
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.WARNING)

logger.info("AnalizadorEstatico inicializado. Nota: OpenSeesPy no impone unidades; use SI (N, m) o convierta cargas si es necesario. NodoEstructural usa daN en documentación interna.")

def calcular_propiedades_barra_circular(diametro=0.10):
    """
    Calcula propiedades de una barra circular de acero.
    
    Args:
        diametro: Diámetro de la barra en metros (default 10 cm)
    
    Returns:
        dict con A, E, G, Ix, Iy, Iz (J)
    """
    E_acero = 200e9
    nu_acero = 0.3
    G_acero = E_acero / (2 * (1 + nu_acero))
    
    A = (np.pi / 4) * diametro**2
    I = (np.pi / 64) * diametro**4
    J = (np.pi / 32) * diametro**4
    
    return {'A': A, 'E': E_acero, 'G': G_acero, 'Ix': I, 'Iy': I, 'Iz': J}

class AnalizadorEstatico:
    """Analizador estático de esfuerzos usando OpenSeesPy"""
    
    def __init__(self, geometria, mecanica, parametros_aee):
        self.geometria = geometria
        self.mecanica = mecanica
        self.parametros = parametros_aee
        self.props_barra = calcular_propiedades_barra_circular(diametro=0.10)
        self.conexiones = self._extraer_conexiones()
        
        logger.info(f"📐 Propiedades de barra circular (D=10cm):")
        logger.debug(f"   A = {self.props_barra['A']:.6f} m²")
        logger.debug(f"   E = {self.props_barra['E']/1e9:.1f} GPa")
        logger.debug(f"   I = {self.props_barra['Ix']:.8f} m⁴")
    
    def _extraer_conexiones(self):
        """Extrae y limpia conexiones desde geometría"""
        conexiones_raw = []
        
        if hasattr(self.geometria, 'conexiones') and self.geometria.conexiones:
            for conn in self.geometria.conexiones:
                if isinstance(conn, (list, tuple)) and len(conn) >= 2:
                    nodo_i, nodo_j = conn[0], conn[1]
                    tipo_conn = conn[2] if len(conn) > 2 else 'barra'
                    conexiones_raw.append((nodo_i, nodo_j, tipo_conn))
            
            if conexiones_raw:
                conexiones_sin_cadena = [(i, j, t) for i, j, t in conexiones_raw if t != 'cadena']
                
                crucetas = [(i, j, t) for i, j, t in conexiones_sin_cadena if t == 'cruceta']
                mensulas = [(i, j, t) for i, j, t in conexiones_sin_cadena if t == 'mensula']
                
                crucetas_redundantes = set()
                for nodo_a, nodo_b, _ in crucetas:
                    for nodo_c1, nodo_d1, _ in mensulas:
                        for nodo_c2, nodo_d2, _ in mensulas:
                            if nodo_c1 == nodo_c2:
                                extremos_mensulas = {nodo_d1, nodo_d2}
                                extremos_cruceta = {nodo_a, nodo_b}
                                if extremos_mensulas == extremos_cruceta:
                                    crucetas_redundantes.add((nodo_a, nodo_b))
                                    crucetas_redundantes.add((nodo_b, nodo_a))
                
                conexiones_limpias = []
                pares_vistos = set()
                
                for nodo_i, nodo_j, tipo_conn in conexiones_sin_cadena:
                    if tipo_conn == 'cruceta' and (nodo_i, nodo_j) in crucetas_redundantes:
                        continue
                    
                    par = tuple(sorted([nodo_i, nodo_j]))
                    if par not in pares_vistos:
                        pares_vistos.add(par)
                        conexiones_limpias.append((nodo_i, nodo_j))
                
                logger.debug(f"📊 Conexiones: {len(conexiones_raw)} raw → {len(conexiones_limpias)} limpias")
                return conexiones_limpias
        
        return []
    
    def resolver_sistema(self, hipotesis_nombre: str) -> Dict:
        """Resuelve sistema usando OpenSeesPy con subdivisión de elementos"""
        
        logger.info(f"🔍 Analizando hipótesis: {hipotesis_nombre}")
        logger.debug(f"   Nodos originales: {len(self.geometria.nodos)}")
        logger.debug(f"   Conexiones: {len(self.conexiones)}")
        
        # Validar parámetros obligatorios
        n_corta = self.parametros.get('n_segmentar_conexion_corta')
        n_larga = self.parametros.get('n_segmentar_conexion_larga')
        percentil = self.parametros.get('percentil_separacion_corta_larga')
        
        if n_corta is None:
            raise ValueError("Parámetro obligatorio 'n_segmentar_conexion_corta' no definido")
        if n_larga is None:
            raise ValueError("Parámetro obligatorio 'n_segmentar_conexion_larga' no definido")
        if percentil is None:
            raise ValueError("Parámetro obligatorio 'percentil_separacion_corta_larga' no definido")
        
        # Calcular longitudes de conexiones para determinar umbral
        eps = 1e-9
        longitudes = []
        conexiones_invalidas = []
        conexiones_validas = []
        for ni, nj in self.conexiones:
            if ni not in self.geometria.nodos:
                conexiones_invalidas.append((ni, nj, f"nodo '{ni}' no existe"))
                logger.error(f"Conexión inválida: nodo '{ni}' no existe en geometría ({ni}, {nj})")
                continue
            if nj not in self.geometria.nodos:
                conexiones_invalidas.append((ni, nj, f"nodo '{nj}' no existe"))
                logger.error(f"Conexión inválida: nodo '{nj}' no existe en geometría ({ni}, {nj})")
                continue
            ci = np.array(self.geometria.nodos[ni].coordenadas)
            cj = np.array(self.geometria.nodos[nj].coordenadas)
            longitud = np.linalg.norm(cj - ci)
            if longitud < eps:
                logger.warning(f"Conexión {ni}-{nj} ignorada: longitud {longitud:.3e} (≈0)")
                continue
            longitudes.append(longitud)
            conexiones_validas.append((ni, nj))
        
        if conexiones_invalidas:
            logger.error(f"Conexiones inválidas detectadas: {conexiones_invalidas}")
            raise ValueError(f"Conexiones inválidas detectadas: {conexiones_invalidas}")
        
        if not longitudes:
            logger.warning("No hay conexiones válidas para analizar")
            raise ValueError("No hay conexiones válidas para analizar")
        
        umbral_longitud = np.percentile(longitudes, percentil)
        
        logger.debug(f"Subdivisiones: corta={n_corta}, larga={n_larga}, percentil={percentil}")
        logger.debug(f"Umbral longitud: {umbral_longitud:.2f} m")
        
        # PASO 1: PREPARAR ESTRUCTURA COMPLETA (ANTES de ops.model)
        nodos_base = [n for n, nodo in self.geometria.nodos.items() 
                     if 'BASE' in n.upper() or getattr(nodo, 'tipo_restriccion', None) == 'FIXED' or getattr(nodo, 'tipo_nodo', '').lower() == 'base']
        
        if not nodos_base:
            logger.error("❌ ERROR CRÍTICO: No se encontraron nodos BASE para empotrar")
            raise ValueError("No se encontraron nodos BASE. La estructura debe tener al menos un nodo marcado como BASE o con tipo_nodo='base' o tipo_restriccion='FIXED'.")
        
        logger.debug(f"Nodos BASE: {nodos_base}")
        
        # 1.1: Preparar diccionario de nodos (originales + intermedios)
        nodos_dict = {}  # {nombre: {'coord': [x,y,z], 'tag': int, 'restriccion': [0/1]*6}}
        tag = 1
        
        # Nodos originales
        for nombre, nodo in self.geometria.nodos.items():
            restriccion = [1,1,1,1,1,1] if nombre in nodos_base else [0,0,0,0,0,0]
            nodos_dict[nombre] = {'coord': nodo.coordenadas, 'tag': tag, 'restriccion': restriccion}
            tag += 1
        
        # Nodos intermedios (con subdivisión variable según longitud)
        for ni, nj in conexiones_validas:
            ci = np.array(self.geometria.nodos[ni].coordenadas)
            cj = np.array(self.geometria.nodos[nj].coordenadas)
            longitud = np.linalg.norm(cj - ci)
            
            # Determinar n_subdiv según longitud
            n_subdiv = n_larga if longitud > umbral_longitud else n_corta
            
            for k in range(1, n_subdiv):
                t = k / n_subdiv
                c_inter = ci + t * (cj - ci)
                nombre_inter = f"{ni}_{nj}_{k}"
                nodos_dict[nombre_inter] = {'coord': c_inter.tolist(), 'tag': tag, 'restriccion': [0,0,0,0,0,0]}
                tag += 1
        
        logger.debug(f"Nodos preparados: {len(nodos_dict)} (originales + intermedios)")
        
        # 1.2: Preparar diccionario de elementos con ejes locales
        elementos_dict = {}  # {elem_id: {..., 'ejes_locales': matriz 3x3}}
        elem_id = 1
        
        for ni, nj in conexiones_validas:
            ci = np.array(self.geometria.nodos[ni].coordenadas)
            cj = np.array(self.geometria.nodos[nj].coordenadas)
            longitud = np.linalg.norm(cj - ci)
            
            # Determinar n_subdiv según longitud
            n_subdiv = n_larga if longitud > umbral_longitud else n_corta
            
            # Calcular ejes locales del elemento
            if longitud < eps:
                logger.warning(f"Elemento {ni}-{nj} con longitud {longitud:.3e} ignorado (≈0)")
                continue
            vec_x_local = (cj - ci) / longitud  # Eje X local = dirección del elemento
            
            # CLASIFICACIÓN DE ELEMENTO: Vertical vs Horizontal-X vs Horizontal-Y (umbral 45°)
            # NOTA: SI SE USAN PIEZAS DIAGONALES (>45°), DEBE CALCULARSE EJE DE ELEMENTO 
            # EN COMPONENTES XYZ Y LUEGO TRANSFORMAR SUS RESULTADOS A EJES GLOBALES
            angulo_con_vertical = np.arccos(np.clip(abs(vec_x_local[2]), 0, 1)) * 180 / np.pi  # Ángulo con eje Z
            
            if angulo_con_vertical < 45:  # ELEMENTO VERTICAL (eje longitudinal ≈ Z global)
                transfTag = 1
                vec_ref = np.array([1., 0., 0.])  # Referencia X global (en plano horizontal)
                tipo_elem = "VERTICAL"
                eje_long_global = "Z"
                logger.debug(f"Elemento {ni}-{nj} VERTICAL: vec_x_local={vec_x_local}, ángulo={angulo_con_vertical:.1f}°")
            else:  # ELEMENTO HORIZONTAL (eje longitudinal en plano XY)
                # Determinar si es predominantemente X o Y comparando componentes del vector
                comp_x = abs(vec_x_local[0])
                comp_y = abs(vec_x_local[1])
                
                if comp_x > comp_y:  # Predomina componente X
                    transfTag = 2
                    vec_ref = np.array([0., 0., 1.])  # Referencia Z global
                    tipo_elem = "HORIZONTAL_X"
                    eje_long_global = "X"
                    logger.debug(f"Elemento {ni}-{nj} HORIZONTAL_X: vec_x_local={vec_x_local}, comp_x={comp_x:.3f} > comp_y={comp_y:.3f}")
                else:  # Predomina componente Y
                    transfTag = 3
                    vec_ref = np.array([0., 0., 1.])  # Referencia Z global
                    tipo_elem = "HORIZONTAL_Y"
                    eje_long_global = "Y"
                    logger.debug(f"Elemento {ni}-{nj} HORIZONTAL_Y: vec_x_local={vec_x_local}, comp_y={comp_y:.3f} > comp_x={comp_x:.3f}")
            
            # Calcular eje Z local (perpendicular a X y referencia)
            vec_z_local = np.cross(vec_x_local, vec_ref)
            norm_z = np.linalg.norm(vec_z_local)
            if norm_z < eps:
                # Intentar referencias alternativas si la referencia inicial falla
                for alt_ref in [np.array([1., 0., 0.]), np.array([0., 1., 0.]), np.array([0., 0., 1.])]:
                    vec_z_local = np.cross(vec_x_local, alt_ref)
                    norm_z = np.linalg.norm(vec_z_local)
                    if norm_z >= eps:
                        vec_ref = alt_ref
                        break
                if norm_z < eps:
                    logger.warning(f"Elemento {ni}-{nj}: no se pudo determinar eje Z local (vector colineal). Se omite elemento.")
                    continue
            vec_z_local = vec_z_local / norm_z
            
            # Calcular eje Y local (perpendicular a X y Z)
            vec_y_local = np.cross(vec_z_local, vec_x_local)
            
            # Matriz de transformación: columnas = ejes locales en coordenadas globales
            ejes_locales = np.column_stack([vec_x_local, vec_y_local, vec_z_local])
            
            logger.debug(f"Elemento {ni}-{nj} {tipo_elem}: ángulo_vert={angulo_con_vertical:.1f}°, transfTag={transfTag}, vec_ref={vec_ref}")
            
            # Secuencia de tags para esta conexión
            tags_secuencia = [nodos_dict[ni]['tag']]
            for k in range(1, n_subdiv):
                nombre_inter = f"{ni}_{nj}_{k}"
                tags_secuencia.append(nodos_dict[nombre_inter]['tag'])
            tags_secuencia.append(nodos_dict[nj]['tag'])
            
            # Crear subelementos
            for idx in range(n_subdiv):
                elementos_dict[elem_id] = {
                    'tag_i': tags_secuencia[idx],
                    'tag_j': tags_secuencia[idx + 1],
                    'transfTag': transfTag,
                    'origen': (ni, nj, idx),
                    'n_subdiv': n_subdiv,
                    'ejes_locales': ejes_locales,
                    'vec_x_local': vec_x_local,
                    'tipo_elemento': tipo_elem,
                    'eje_longitudinal_global': 'Z' if tipo_elem == 'VERTICAL' else 'XY'
                }
                elem_id += 1
        
        logger.debug(f"Elementos preparados: {len(elementos_dict)} subelementos")
        
        # 1.3: Preparar cargas
        cargas_dict = {}  # {tag: [fx, fy, fz, mx, my, mz]}
        for nombre, nodo in self.geometria.nodos.items():
            if nombre not in nodos_base and nombre in nodos_dict:
                cargas = nodo.obtener_cargas_hipotesis(hipotesis_nombre)
                if cargas and any(abs(cargas.get(k, 0)) > 0.01 for k in ['fx', 'fy', 'fz']):
                    tag_nodo = nodos_dict[nombre]['tag']
                    cargas_dict[tag_nodo] = [cargas['fx'], cargas['fy'], cargas['fz'], 0, 0, 0]
                    logger.debug(f"Carga en nodo {nombre} (tag={tag_nodo}): fx={cargas['fx']:.2f}, fy={cargas['fy']:.2f}, fz={cargas['fz']:.2f}")
        
        logger.debug(f"Cargas preparadas: {len(cargas_dict)} nodos con carga")
        
        if len(cargas_dict) == 0:
            logger.warning("No hay cargas para esta hipótesis")
            return {}
        
        # PASO 2: CREAR MODELO OPENSEESPY
        ops.wipe()
        ops.model('basic', '-ndm', 3, '-ndf', 6)
        
        # 2.1: Crear nodos
        for nombre, data in nodos_dict.items():
            c = data['coord']
            ops.node(data['tag'], c[0], c[1], c[2])
        
        # 2.2: Transformaciones
        ops.geomTransf('Linear', 1, 1., 0., 0.)  # VERTICAL: vec_ref = X global
        ops.geomTransf('Linear', 2, 0., 0., 1.)  # HORIZONTAL_X: vec_ref = Z global
        ops.geomTransf('Linear', 3, 0., 0., 1.)  # HORIZONTAL_Y: vec_ref = Z global
        
        # 2.3: Crear elementos
        for eid, data in elementos_dict.items():
            ops.element('elasticBeamColumn', eid, data['tag_i'], data['tag_j'],
                       self.props_barra['A'], self.props_barra['E'], self.props_barra['G'],
                       self.props_barra['Iz'], self.props_barra['Ix'], self.props_barra['Iy'],
                       data['transfTag'])
        
        # 2.4: Aplicar restricciones (DESPUÉS de crear elementos)
        for nombre, data in nodos_dict.items():
            if any(r == 1 for r in data['restriccion']):
                logger.debug(f"🔒 Empotrado nodo {nombre} (tag={data['tag']}): {data['restriccion']}")
                
                # Verificar que el nodo BASE esté conectado a elementos
                elementos_conectados = [eid for eid, edata in elementos_dict.items() 
                                       if edata['tag_i'] == data['tag'] or edata['tag_j'] == data['tag']]
                logger.debug(f"   Elementos conectados a {nombre}: {len(elementos_conectados)}")
                if len(elementos_conectados) == 0:
                    logger.error(f"❌ ERROR: Nodo {nombre} no está conectado a ningún elemento")
            ops.fix(data['tag'], *data['restriccion'])
        
        # 2.4: Aplicar cargas
        ops.timeSeries('Constant', 1)
        ops.pattern('Plain', 1, 1)
        
        for tag_nodo, carga in cargas_dict.items():
            ops.load(tag_nodo, *carga)
        
        # PASO 3: ANÁLISIS
        ops.constraints('Plain')
        ops.numberer('RCM')
        ops.system('BandGeneral')
        ops.test('NormDispIncr', 1.0e-6, 10)
        ops.algorithm('Linear')
        ops.integrator('LoadControl', 1.0)
        ops.analysis('Static')
        
        try:
            resultado = ops.analyze(1)
            if resultado != 0:
                logger.info("🔄 Reintentando con Newton...")
                ops.algorithm('Newton')
                resultado = ops.analyze(1)
            
            if resultado != 0:
                logger.error("Análisis no convergió después de reintentos")
                raise RuntimeError("Análisis no convergió después de reintentos")
            
            logger.info("✅ Análisis convergió")
        except Exception as e:
            logger.error(f"❌ Error en análisis: {e}", exc_info=True)
            raise
        
        # PASO 4: EXTRAER RESULTADOS Y TRANSFORMAR A EJES GLOBALES
        valores_subnodos = {}
        resultados_por_elemento = {}  # {"ni_nj": [{sub_idx, N, Q, M, T, ...}, ...]}
        
        # DEBUG: Verificar fuerzas en primer elemento BASE_V
        logger.debug("=" * 80)
        logger.debug("DEBUG: Verificando fuerzas en elementos BASE_V")
        for eid, data in list(elementos_dict.items())[:3]:
            ni, nj, sub_idx = data['origen']
            if 'BASE' in ni and 'V' in nj:
                fuerzas = ops.eleForce(eid)
                logger.debug(f"Elemento {ni}-{nj} sub={sub_idx}:")
                logger.debug(f"  vec_x_local (eje long): {data['vec_x_local']}")
                logger.debug(f"  tipo: {data['tipo_elemento']}, transfTag: {data['transfTag']}")
                logger.debug(f"  fuerzas_locales: N={fuerzas[0]:.2f}, Qy={fuerzas[1]:.2f}, Qz={fuerzas[2]:.2f}")
                logger.debug(f"  momentos_locales: Mx={fuerzas[3]:.2f}, My={fuerzas[4]:.2f}, Mz={fuerzas[5]:.2f}")
        logger.debug("=" * 80)
        
        for eid, data in elementos_dict.items():
            try:
                fuerzas_locales = ops.eleForce(eid)
            except Exception as e:
                logger.error(f"Error obteniendo fuerzas del elemento {eid}: {e}", exc_info=True)
                continue
            # Validar tamaño del vector de fuerzas (se esperan 12 entradas)
            if not hasattr(fuerzas_locales, '__len__') or len(fuerzas_locales) < 12:
                logger.error(f"Elemento {eid} devolvió fuerzas con longitud inesperada ({getattr(fuerzas_locales, '__len__', None)}). Se omite elemento.")
                continue
            try:
                ni, nj, sub_idx = data['origen']
                ejes_locales = data['ejes_locales']
                
                # OpenSeesPy devuelve fuerzas en convención de equilibrio (reacciones del elemento sobre nodos)
                # Para fuerzas internas del elemento, invertir signos del nodo i
                # IMPORTANTE: Para elementos VERTICALES, verificar que N corresponda a cargas Z globales
                
                # Nodo i: invertir signos (fuerzas internas = -reacciones)
                N_local_i = -fuerzas_locales[0]   # Axial (eje X local)
                Qy_local_i = -fuerzas_locales[1]  # Cortante Y local
                Qz_local_i = -fuerzas_locales[2]  # Cortante Z local
                Mx_local_i = -fuerzas_locales[3]  # Momento X local (torsión en eje elemento)
                My_local_i = -fuerzas_locales[4]  # Momento Y local
                Mz_local_i = -fuerzas_locales[5]  # Momento Z local
                
                # CORRECCIÓN según orientación del elemento:
                # OpenSeesPy usa convención donde eje X local = eje longitudinal del elemento
                # Pero para elementos no alineados con X global, hay que reinterpretar
                tipo_elem = data.get('tipo_elemento', 'DESCONOCIDO')
                
                if tipo_elem == 'VERTICAL':
                    # Elemento vertical: eje longitudinal = Z global
                    # N (axial) viene en Qz, Qz viene en N
                    # T (torsión alrededor Z) viene en Mz, Mz viene en Mx
                    N_local_i, Qz_local_i = Qz_local_i, N_local_i
                    Mx_local_i, Mz_local_i = Mz_local_i, Mx_local_i
                    logger.debug(f"VERTICAL {ni}-{nj}: N<->Qz, Mx<->Mz: N={N_local_i:.2f}, T={Mx_local_i:.2f}")
                
                elif tipo_elem == 'HORIZONTAL_Y':
                    # Elemento horizontal en Y: eje longitudinal = Y global
                    # N (axial) viene en Qy, Qy viene en N
                    # T (torsión alrededor Y) viene en My, My viene en Mx
                    N_local_i, Qy_local_i = Qy_local_i, N_local_i
                    Mx_local_i, My_local_i = My_local_i, Mx_local_i
                    logger.debug(f"HORIZONTAL_Y {ni}-{nj}: N<->Qy, Mx<->My: N={N_local_i:.2f}, T={Mx_local_i:.2f}")
                
                # HORIZONTAL_X no necesita corrección (eje X local = X global)
                
                # Nodo j: mantener signos (ya son fuerzas internas)
                N_local_j = fuerzas_locales[6]
                Qy_local_j = fuerzas_locales[7]
                Qz_local_j = fuerzas_locales[8]
                Mx_local_j = fuerzas_locales[9]
                My_local_j = fuerzas_locales[10]
                Mz_local_j = fuerzas_locales[11]
                
                # CORRECCIÓN para nodo j según orientación
                if tipo_elem == 'VERTICAL':
                    N_local_j, Qz_local_j = Qz_local_j, N_local_j
                    Mx_local_j, Mz_local_j = Mz_local_j, Mx_local_j
                elif tipo_elem == 'HORIZONTAL_Y':
                    N_local_j, Qy_local_j = Qy_local_j, N_local_j
                    Mx_local_j, My_local_j = My_local_j, Mx_local_j
                
                # Calcular magnitudes en ejes locales (DESPUÉS de correcciones)
                # Momento Flector = sqrt(My² + Mz²) en ejes locales
                M_i = np.sqrt(My_local_i**2 + Mz_local_i**2)
                M_j = np.sqrt(My_local_j**2 + Mz_local_j**2)
                
                # Torsión = Mx en ejes locales (ya corregido para verticales)
                T_i = abs(Mx_local_i)
                T_j = abs(Mx_local_j)
                
                # Cortante = sqrt(Qy² + Qz²) en ejes locales
                Q_i = np.sqrt(Qy_local_i**2 + Qz_local_i**2)
                Q_j = np.sqrt(Qy_local_j**2 + Qz_local_j**2)
                
                # Almacenar resultados completos por elemento
                elem_key = f"{ni}_{nj}"
                if elem_key not in resultados_por_elemento:
                    resultados_por_elemento[elem_key] = []
                
                resultados_por_elemento[elem_key].append({
                    'sub_idx': sub_idx,
                    'N': abs(N_local_i),
                    'Qy': Qy_local_i,
                    'Qz': Qz_local_i,
                    'Q': Q_i,
                    'Mx': Mx_local_i,
                    'My': My_local_i,
                    'Mz': Mz_local_i,
                    'M': M_i,
                    'T': T_i,
                    'tipo_elemento': data.get('tipo_elemento', 'DESCONOCIDO'),
                    'eje_longitudinal_global': data.get('eje_longitudinal_global', 'N/A')
                })
                
                # Almacenar: [N, Q, M, T, componentes corregidos...]
                valores_subnodos[f"{ni}_{nj}_{sub_idx}_i"] = np.array([
                    abs(N_local_i), Q_i, M_i, T_i,
                    N_local_i, Qy_local_i, Qz_local_i,
                    Mx_local_i, My_local_i, Mz_local_i
                ])
                valores_subnodos[f"{ni}_{nj}_{sub_idx}_j"] = np.array([
                    abs(N_local_j), Q_j, M_j, T_j,
                    N_local_j, Qy_local_j, Qz_local_j,
                    Mx_local_j, My_local_j, Mz_local_j
                ])
            except Exception as e:
                logger.error(f"Error procesando elemento {eid}: {e}", exc_info=True)
                continue
        
        # Extraer reacciones en BASE
        ops.reactions()
        reacciones_base = {}
        for nombre in nodos_base:
            if nombre in nodos_dict:
                tag = nodos_dict[nombre]['tag']
                try:
                    reaccion = ops.nodeReaction(tag)
                    if not hasattr(reaccion, '__len__') or len(reaccion) < 6:
                        logger.error(f"Reacción en nodo base {nombre} con formato inesperado: {reaccion}")
                        continue
                    reacciones_base[nombre] = {'Fx': reaccion[0], 'Fy': reaccion[1], 'Fz': reaccion[2],
                                               'Mx': reaccion[3], 'My': reaccion[4], 'Mz': reaccion[5]}
                    logger.debug(f"Reacción BASE {nombre}: Fx={reaccion[0]:.2f}, Fy={reaccion[1]:.2f}, Fz={reaccion[2]:.2f}")
                except Exception as e:
                    logger.error(f"Error obteniendo reacciones en nodo {nombre}: {e}", exc_info=True)
                    continue
        
        # Verificar que las reacciones no sean todas cero (indica matriz singular)
        todas_cero = all(
            abs(r['Fx']) < 0.01 and abs(r['Fy']) < 0.01 and abs(r['Fz']) < 0.01
            for r in reacciones_base.values()
        )
        if todas_cero and len(cargas_dict) > 0:
            logger.error("❌ ERROR: Todas las reacciones son cero - matriz singular")
            raise RuntimeError("Análisis falló: matriz singular. Las restricciones no están correctamente aplicadas o la estructura es inestable.")
        
        logger.debug(f"Valores extraídos: {len(valores_subnodos)} subnodos")
        return {'valores': valores_subnodos, 'reacciones': reacciones_base, 'elementos_dict': elementos_dict, 'resultados_por_elemento': resultados_por_elemento}
    
    def generar_dataframe_reacciones(self, hipotesis_nombres: List[str]) -> 'pd.DataFrame':
        """Genera DataFrame con reacciones para múltiples hipótesis"""
        import pandas as pd
        
        datos_reacciones = []
        for hip_nombre in hipotesis_nombres:
            try:
                resultado = self.resolver_sistema(hip_nombre)
                if not resultado:
                    continue
                
                reacciones = resultado.get('reacciones', {})
                if not reacciones:
                    continue
                
                # Sumar reacciones de todos los nodos base
                fx_total = sum(r['Fx'] for r in reacciones.values())
                fy_total = sum(r['Fy'] for r in reacciones.values())
                fz_total = sum(r['Fz'] for r in reacciones.values())
                mx_total = sum(r['Mx'] for r in reacciones.values())
                my_total = sum(r['My'] for r in reacciones.values())
                mz_total = sum(r['Mz'] for r in reacciones.values())
                
                datos_reacciones.append({
                    'Hipótesis': hip_nombre,
                    'Fx [daN]': round(fx_total, 1),
                    'Fy [daN]': round(fy_total, 1),
                    'Fz [daN]': round(fz_total, 1),
                    'Mx [daN·m]': round(mx_total, 1),
                    'My [daN·m]': round(my_total, 1),
                    'Mz [daN·m]': round(mz_total, 1)
                })
            except Exception as e:
                logger.error(f"Error procesando hipótesis {hip_nombre}: {e}")
                continue
        
        if not datos_reacciones:
            return pd.DataFrame()
        
        df = pd.DataFrame(datos_reacciones)
        df = df.set_index('Hipótesis')
        return df
    
    def calcular_momento_resultante_total(self, resultado_analisis: Dict) -> Dict:
        """MRT = sqrt(M^2 + T^2)"""
        if not resultado_analisis:
            raise ValueError("resultado_analisis vacío - análisis no convergió")
        valores_subnodos = resultado_analisis.get('valores', {})
        mrt = {}
        for nodo, vals in valores_subnodos.items():
            if isinstance(vals, np.ndarray) and len(vals) >= 10:
                M, T = vals[2], vals[3]
                mrt[nodo] = float(np.sqrt(M**2 + T**2))
        return {'valores': mrt, 'reacciones': resultado_analisis.get('reacciones', {})}
    
    def calcular_momento_flector_equivalente(self, resultado_analisis: Dict) -> Dict:
        """MFE = M"""
        if not resultado_analisis:
            raise ValueError("resultado_analisis vacío - análisis no convergió")
        valores_subnodos = resultado_analisis.get('valores', {})
        mfe = {}
        for nodo, vals in valores_subnodos.items():
            if isinstance(vals, np.ndarray) and len(vals) >= 10:
                mfe[nodo] = float(vals[2])
        return {'valores': mfe, 'reacciones': resultado_analisis.get('reacciones', {})}
    
    def generar_diagrama_3d_interactivo(self, resultado_analisis: Dict, tipo: str, hipotesis: str, escala: str = "lineal"):
        """Genera diagrama 3D interactivo con Plotly"""
        from utils.analisis_estatico_plots import generar_diagrama_plotly_3d
        
        if not resultado_analisis:
            raise ValueError("resultado_analisis vacío - análisis no convergió")
        
        valores_subnodos = resultado_analisis.get('valores', {})
        reacciones = resultado_analisis.get('reacciones', {})
        
        return generar_diagrama_plotly_3d(
            self.geometria, self.conexiones, valores_subnodos, reacciones,
            self.parametros, tipo, hipotesis, escala
        )
    
    def generar_diagrama_2d_interactivo(self, resultado_analisis: Dict, tipo: str, hipotesis: str, escala: str = "lineal"):
        """Genera diagrama 2D interactivo con Plotly"""
        from utils.analisis_estatico_plots import generar_diagrama_plotly_2d
        
        if not resultado_analisis:
            raise ValueError("resultado_analisis vacío - análisis no convergió")
        
        valores_subnodos = resultado_analisis.get('valores', {})
        reacciones = resultado_analisis.get('reacciones', {})
        
        return generar_diagrama_plotly_2d(
            self.geometria, self.conexiones, valores_subnodos, reacciones,
            self.parametros, tipo, hipotesis, escala
        )
    
    def generar_diagrama_mqnt_interactivo(self, resultado_analisis: Dict, hipotesis: str, graficos_3d: bool = False, escala: str = "lineal"):
        """Genera diagrama combinado MQNT interactivo con Plotly"""
        from utils.analisis_estatico_plots import generar_diagrama_mqnt_plotly
        
        if not resultado_analisis:
            raise ValueError("resultado_analisis vacío - análisis no convergió")
        
        valores_subnodos = resultado_analisis.get('valores', {})
        reacciones = resultado_analisis.get('reacciones', {})
        
        return generar_diagrama_mqnt_plotly(
            self.geometria, self.conexiones, valores_subnodos, reacciones,
            self.parametros, hipotesis, graficos_3d, escala
        )
    
    def generar_diagrama_3d(self, resultado_analisis: Dict, tipo: str, hipotesis: str, escala: str = "lineal"):
        """Genera diagrama 3D con matplotlib"""
        if not resultado_analisis:
            raise ValueError("resultado_analisis vacío - análisis no convergió")
        
        valores_subnodos = resultado_analisis.get('valores', {})
        reacciones = resultado_analisis.get('reacciones', {})
        
        return generar_diagrama_matplotlib_3d(
            self.geometria, self.conexiones, valores_subnodos, reacciones,
            self.parametros, tipo, hipotesis, escala
        )
    
    def generar_diagrama_2d(self, resultado_analisis: Dict, tipo: str, hipotesis: str, escala: str = "lineal"):
        """Genera diagrama 2D con matplotlib"""
        if not resultado_analisis:
            raise ValueError("resultado_analisis vacío - análisis no convergió")
        
        valores_subnodos = resultado_analisis.get('valores', {})
        reacciones = resultado_analisis.get('reacciones', {})
        
        return generar_diagrama_matplotlib_2d(
            self.geometria, self.conexiones, valores_subnodos, reacciones,
            self.parametros, tipo, hipotesis, escala
        )
    
    def generar_diagrama_mqnt(self, resultado_analisis: Dict, hipotesis: str, graficos_3d: bool = False, escala: str = "lineal"):
        """Genera diagrama combinado MQNT con matplotlib"""
        if not resultado_analisis:
            raise ValueError("resultado_analisis vacío - análisis no convergió")
        
        valores_subnodos = resultado_analisis.get('valores', {})
        reacciones = resultado_analisis.get('reacciones', {})
        
        return generar_diagrama_mqnt_matplotlib(
            self.geometria, self.conexiones, valores_subnodos, reacciones,
            self.parametros, hipotesis, graficos_3d, escala
        )

    
    def generar_diagrama_ejes_locales(self, elementos_dict: Dict, hipotesis: str):
        """Genera diagrama 3D mostrando ejes locales de elementos"""
        return generar_diagrama_ejes_locales_matplotlib(
            self.geometria, self.conexiones, elementos_dict, hipotesis
        )
    







