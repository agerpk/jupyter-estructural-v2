import streamlit as st
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# Agregar el directorio actual al path para importar módulos propios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuración de la página
st.set_page_config(
    page_title="Diseño de Estructuras de Líneas de Transmisión",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definir constantes y opciones
TIPOS_ESTRUCTURA = ["Suspensión Recta", "Suspensión Angular", "Retención / Ret. Angular", "Terminal"]
EXPOSICIONES = ["B", "C", "D"]
CLASES_LINEA = ["A", "B", "BB", "C", "D", "E"]
ZONAS_CLIMATICAS = ["A", "B", "C", "D", "E"]
ZONAS_ESTRUCTURA = ["Peatonal", "Rural", "Urbana", "Autopista", "Ferrocarril", "Línea Eléctrica"]
DISPOSICIONES = ["triangular", "horizontal", "vertical"]
TERNAS = ["Simple", "Doble"]
ORIENTACIONES = ["Longitudinal", "Transversal", "No"]
METODOS_ALTURA = ["AEA 3%/300m"]
PRIORIDADES = ["altura_libre", "longitud_total"]
OBJETIVOS = ["FlechaMin", "TiroMin"]
VIENTO_DIRECCIONES = ["transversal", "longitudinal", "oblicuo"]

class EstructuraApp:
    def __init__(self):
        self.estructura_actual = None
        self.plantilla_path = "plantilla.estructura.json"
        self.actual_path = "actual.estructura.json"
        self.cables_path = "cables.json"
        self.cargar_cables()
        self.inicializar_estructura()
        
    def cargar_cables(self):
        """Cargar datos de cables desde JSON"""
        try:
            with open(self.cables_path, 'r', encoding='utf-8') as f:
                self.cables_data = json.load(f)
            self.cables_list = list(self.cables_data.keys())
        except FileNotFoundError:
            st.error(f"Archivo {self.cables_path} no encontrado")
            self.cables_data = {}
            self.cables_list = []
    
    def cargar_plantilla(self):
        """Cargar plantilla por defecto"""
        try:
            with open(self.plantilla_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Crear plantilla básica si no existe
            plantilla = {
                "TIPO_ESTRUCTURA": "Suspensión Recta",
                "Zona_climatica": "D",
                "exposicion": "C",
                "clase": "C",
                "TITULO": "2x220 DTT SAN JORGE PRUEBAS",
                "cable_conductor_id": "AlAc 435/55",
                "cable_guardia_id": "OPGW FiberHome 24FO 58mm2",
                "Vmax": 38.9,
                "Vmed": 15.56,
                "Vtormenta": 20.0,
                "t_hielo": 0.01,
                "Q": 0.0613,
                "Zco": 13.0,
                "Zcg": 13.0,
                "Zca": 13.0,
                "Zes": 10.0,
                "Cf_cable": 1.0,
                "Cf_guardia": 1.0,
                "Cf_cadena": 0.9,
                "Cf_estructura": 0.9,
                "L_vano": 400.0,
                "alpha": 0.0,
                "theta": 45.0,
                "A_cadena": 0.03,
                "PCADENA": 10.5,
                "PESTRUCTURA": 3900.0,
                "A_estr_trans": 2.982,
                "A_estr_long": 4.482,
                "FORZAR_N_POSTES": 1,
                "FORZAR_ORIENTACION": "No",
                "PRIORIDAD_DIMENSIONADO": "altura_libre",
                "TENSION": 220,
                "Zona_estructura": "Rural",
                "Lk": 2.5,
                "ANG_APANTALLAMIENTO": 30.0,
                "AJUSTAR_POR_ALTURA_MSNM": True,
                "METODO_ALTURA_MSNM": "AEA 3%/300m",
                "Altura_MSNM": 3000,
                "DISPOSICION": "triangular",
                "TERNA": "Doble",
                "CANT_HG": 2,
                "HG_CENTRADO": False,
                "ALTURA_MINIMA_CABLE": 6.5,
                "LONGITUD_MENSULA_MINIMA_CONDUCTOR": 1.3,
                "LONGITUD_MENSULA_MINIMA_GUARDIA": 0.2,
                "HADD": 0.4,
                "HADD_ENTRE_AMARRES": 0.2,
                "HADD_HG": 1.5,
                "HADD_LMEN": 0.5,
                "ANCHO_CRUCETA": 0.3,
                "AUTOAJUSTAR_LMENHG": True,
                "DIST_REPOSICIONAR_HG": 0.1,
                "MOSTRAR_C2": False,
                "SALTO_PORCENTUAL": 0.05,
                "PASO_AFINADO": 0.005,
                "OBJ_CONDUCTOR": "FlechaMin",
                "OBJ_GUARDIA": "TiroMin",
                "RELFLECHA_MAX_GUARDIA": 0.95,
                "RELFLECHA_SIN_VIENTO": True,
                "ZOOM_CABEZAL": 0.95,
                "REEMPLAZAR_TITULO_GRAFICO": False,
                "Vn": 220,
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
                "version": "1.0"
            }
            self.guardar_estructura(self.plantilla_path, plantilla)
            return plantilla
    
    def inicializar_estructura(self):
        """Inicializar o cargar estructura actual"""
        if os.path.exists(self.actual_path):
            try:
                with open(self.actual_path, 'r', encoding='utf-8') as f:
                    self.estructura_actual = json.load(f)
            except:
                self.estructura_actual = self.cargar_plantilla()
        else:
            self.estructura_actual = self.cargar_plantilla()
            self.guardar_estructura(self.actual_path, self.estructura_actual)
    
    def guardar_estructura(self, filepath, estructura):
        """Guardar estructura en archivo JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(estructura, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error al guardar: {e}")
            return False
    
    def cargar_desde_archivo(self, uploaded_file):
        """Cargar estructura desde archivo subido"""
        try:
            estructura = json.load(uploaded_file)
            # Validar estructura básica
            required_keys = ["TITULO", "TIPO_ESTRUCTURA", "TENSION"]
            if all(key in estructura for key in required_keys):
                return estructura
            else:
                st.error("Archivo no contiene estructura válida")
                return None
        except Exception as e:
            st.error(f"Error al cargar archivo: {e}")
            return None
    
    def listar_estructuras(self):
        """Listar archivos de estructura en el directorio"""
        estructuras = []
        for file in os.listdir("."):
            if file.endswith(".estructura.json"):
                estructuras.append(file)
        return estructuras
    
    def mostrar_menu_principal(self):
        """Mostrar menú principal en sidebar"""
        st.sidebar.title("🏗️ Diseño de Estructuras")
        st.sidebar.markdown("---")
        
        menu = st.sidebar.radio(
            "Menú Principal",
            [
                "📊 Dashboard",
                "🆕 Nueva Estructura",
                "📂 Cargar Estructura",
                "📋 Cargar como Plantilla",
                "💾 Guardar Estructura",
                "💾 Guardar Como",
                "⚙️ Ajustar Parámetros"
            ]
        )
        
        st.sidebar.markdown("---")
        if self.estructura_actual:
            st.sidebar.info(f"**Estructura Actual:**\n{self.estructura_actual['TITULO']}")
            st.sidebar.caption(f"Tipo: {self.estructura_actual['TIPO_ESTRUCTURA']}")
        
        return menu
    
    def mostrar_dashboard(self):
        """Mostrar dashboard con información de la estructura actual"""
        st.title("📊 Dashboard - Diseño de Estructuras")
        
        if not self.estructura_actual:
            st.warning("No hay estructura cargada")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Título", self.estructura_actual["TITULO"])
            st.metric("Tipo de Estructura", self.estructura_actual["TIPO_ESTRUCTURA"])
            st.metric("Tensión", f"{self.estructura_actual['TENSION']} kV")
        
        with col2:
            st.metric("Vano", f"{self.estructura_actual['L_vano']} m")
            st.metric("Viento Máximo", f"{self.estructura_actual['Vmax']} m/s")
            st.metric("Altura MSNM", f"{self.estructura_actual.get('Altura_MSNM', 0)} m")
        
        with col3:
            st.metric("Conductor", self.estructura_actual["cable_conductor_id"])
            st.metric("Cable Guardia", self.estructura_actual["cable_guardia_id"])
            st.metric("Disposición", self.estructura_actual["DISPOSICION"])
        
        # Mostrar información detallada
        with st.expander("📋 Detalles Completos de la Estructura"):
            st.json(self.estructura_actual, expanded=False)
    
    def mostrar_nueva_estructura(self):
        """Interfaz para crear nueva estructura"""
        st.title("🆕 Nueva Estructura")
        
        with st.form("nueva_estructura_form"):
            titulo = st.text_input("Título de la Estructura", 
                                 value=f"Nueva Estructura {datetime.now().strftime('%Y%m%d_%H%M')}")
            
            col1, col2 = st.columns(2)
            with col1:
                tipo_estructura = st.selectbox("Tipo de Estructura", TIPOS_ESTRUCTURA)
                tension = st.number_input("Tensión (kV)", min_value=1, max_value=500, value=220, step=1)
                zona_climatica = st.selectbox("Zona Climática", ZONAS_CLIMATICAS, index=3)
            
            with col2:
                exposicion = st.selectbox("Exposición", EXPOSICIONES, index=1)
                clase_linea = st.selectbox("Clase de Línea", CLASES_LINEA, index=3)
                zona_estructura = st.selectbox("Zona de Estructura", ZONAS_ESTRUCTURA, index=1)
            
            if st.form_submit_button("🔧 Crear Nueva Estructura"):
                # Crear nueva estructura basada en plantilla
                nueva_estructura = self.cargar_plantilla()
                nueva_estructura["TITULO"] = titulo
                nueva_estructura["TIPO_ESTRUCTURA"] = tipo_estructura
                nueva_estructura["TENSION"] = tension
                nueva_estructura["Zona_climatica"] = zona_climatica
                nueva_estructura["exposicion"] = exposicion
                nueva_estructura["clase"] = clase_linea
                nueva_estructura["Zona_estructura"] = zona_estructura
                nueva_estructura["fecha_creacion"] = datetime.now().strftime("%Y-%m-%d")
                
                self.estructura_actual = nueva_estructura
                self.guardar_estructura(self.actual_path, nueva_estructura)
                st.success(f"✅ Nueva estructura '{titulo}' creada exitosamente!")
                st.rerun()
    
    def mostrar_cargar_estructura(self):
        """Interfaz para cargar estructura existente"""
        st.title("📂 Cargar Estructura")
        
        tab1, tab2 = st.tabs(["📁 Desde Base de Datos", "💻 Desde Computadora"])
        
        with tab1:
            st.subheader("Cargar desde Base de Datos")
            estructuras_disponibles = self.listar_estructuras()
            
            if estructuras_disponibles:
                estructura_seleccionada = st.selectbox(
                    "Seleccionar estructura",
                    estructuras_disponibles,
                    format_func=lambda x: x.replace(".estructura.json", "")
                )
                
                if st.button("📥 Cargar Estructura Seleccionada"):
                    try:
                        with open(estructura_seleccionada, 'r', encoding='utf-8') as f:
                            self.estructura_actual = json.load(f)
                        self.guardar_estructura(self.actual_path, self.estructura_actual)
                        st.success(f"✅ Estructura '{estructura_seleccionada}' cargada exitosamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al cargar: {e}")
            else:
                st.info("No hay estructuras guardadas en la base de datos")
        
        with tab2:
            st.subheader("Cargar desde Archivo")
            uploaded_file = st.file_uploader(
                "Seleccionar archivo .estructura.json",
                type=["json"],
                accept_multiple_files=False
            )
            
            if uploaded_file is not None:
                if uploaded_file.name.endswith(".estructura.json"):
                    if st.button("📥 Cargar Archivo"):
                        estructura = self.cargar_desde_archivo(uploaded_file)
                        if estructura:
                            self.estructura_actual = estructura
                            self.guardar_estructura(self.actual_path, estructura)
                            st.success(f"✅ Estructura cargada exitosamente!")
                            st.rerun()
                else:
                    st.error("❌ Error: El archivo debe tener extensión .estructura.json")
    
    def mostrar_cargar_como_plantilla(self):
        """Interfaz para cargar estructura como plantilla"""
        st.title("📋 Cargar Estructura como Plantilla")
        
        tab1, tab2 = st.tabs(["📁 Desde Base de Datos", "💻 Desde Computadora"])
        
        with tab1:
            estructuras_disponibles = self.listar_estructuras()
            
            if estructuras_disponibles:
                estructura_seleccionada = st.selectbox(
                    "Seleccionar estructura para plantilla",
                    estructuras_disponibles,
                    key="plantilla_db",
                    format_func=lambda x: x.replace(".estructura.json", "")
                )
                
                if st.button("📋 Establecer como Plantilla"):
                    try:
                        with open(estructura_seleccionada, 'r', encoding='utf-8') as f:
                            nueva_plantilla = json.load(f)
                        self.guardar_estructura(self.plantilla_path, nueva_plantilla)
                        st.success(f"✅ Plantilla actualizada exitosamente!")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.info("No hay estructuras guardadas en la base de datos")
        
        with tab2:
            uploaded_file = st.file_uploader(
                "Seleccionar archivo .estructura.json para plantilla",
                type=["json"],
                accept_multiple_files=False,
                key="plantilla_file"
            )
            
            if uploaded_file is not None:
                if uploaded_file.name.endswith(".estructura.json"):
                    if st.button("📋 Establecer Archivo como Plantilla"):
                        estructura = self.cargar_desde_archivo(uploaded_file)
                        if estructura:
                            self.guardar_estructura(self.plantilla_path, estructura)
                            st.success(f"✅ Plantilla actualizada exitosamente!")
                else:
                    st.error("❌ Error: El archivo debe tener extensión .estructura.json")
    
    def mostrar_guardar_estructura(self):
        """Interfaz para guardar estructura"""
        st.title("💾 Guardar Estructura")
        
        if not self.estructura_actual:
            st.warning("No hay estructura cargada para guardar")
            return
        
        tab1, tab2 = st.tabs(["💾 Guardar en Base de Datos", "💻 Guardar en Computadora"])
        
        with tab1:
            st.subheader("Guardar en Base de Datos")
            nombre_archivo = st.text_input(
                "Nombre del archivo",
                value=f"{self.estructura_actual['TITULO'].replace(' ', '_').lower()}.estructura.json"
            )
            
            if not nombre_archivo.endswith(".estructura.json"):
                nombre_archivo += ".estructura.json"
            
            if os.path.exists(nombre_archivo):
                st.warning(f"⚠️ El archivo '{nombre_archivo}' ya existe")
                sobreescribir = st.checkbox("Sobreescribir archivo existente")
            else:
                sobreescribir = True
            
            if st.button("💾 Guardar en Base de Datos") and sobreescribir:
                if self.guardar_estructura(nombre_archivo, self.estructura_actual):
                    st.success(f"✅ Estructura guardada como '{nombre_archivo}'")
        
        with tab2:
            st.subheader("Descargar a Computadora")
            st.info("La descarga se realizará automáticamente al hacer clic")
            
            # Crear JSON para descarga
            json_str = json.dumps(self.estructura_actual, indent=2, ensure_ascii=False)
            nombre_descarga = f"{self.estructura_actual['TITULO'].replace(' ', '_').lower()}.estructura.json"
            
            st.download_button(
                label="📥 Descargar Estructura",
                data=json_str,
                file_name=nombre_descarga,
                mime="application/json"
            )
    
    def mostrar_guardar_como(self):
        """Interfaz para guardar estructura con nuevo nombre"""
        st.title("💾 Guardar Estructura Como")
        
        if not self.estructura_actual:
            st.warning("No hay estructura cargada para guardar")
            return
        
        with st.form("guardar_como_form"):
            nuevo_titulo = st.text_input(
                "Nuevo Título de la Estructura",
                value=self.estructura_actual["TITULO"]
            )
            
            nombre_archivo = st.text_input(
                "Nombre del archivo",
                value=f"{nuevo_titulo.replace(' ', '_').lower()}.estructura.json"
            )
            
            if not nombre_archivo.endswith(".estructura.json"):
                nombre_archivo += ".estructura.json"
            
            col1, col2 = st.columns(2)
            with col1:
                guardar_db = st.checkbox("Guardar en Base de Datos", value=True)
            with col2:
                guardar_actual = st.checkbox("Actualizar estructura actual", value=True)
            
            if st.form_submit_button("💾 Guardar Como"):
                # Crear copia de la estructura con nuevo título
                nueva_estructura = self.estructura_actual.copy()
                nueva_estructura["TITULO"] = nuevo_titulo
                
                if guardar_db:
                    if self.guardar_estructura(nombre_archivo, nueva_estructura):
                        st.success(f"✅ Estructura guardada como '{nombre_archivo}'")
                
                if guardar_actual:
                    self.estructura_actual = nueva_estructura
                    self.guardar_estructura(self.actual_path, nueva_estructura)
                    st.success("✅ Estructura actual actualizada")
    
    def mostrar_ajustar_parametros(self):
        """Interfaz para ajustar parámetros de la estructura actual"""
        st.title("⚙️ Ajustar Parámetros de la Estructura")
        
        if not self.estructura_actual:
            st.warning("No hay estructura cargada para ajustar")
            return
        
        st.info(f"**Estructura Actual:** {self.estructura_actual['TITULO']}")
        
        # Organizar parámetros por bloques
        parametros_por_bloque = self.organizar_parametros_por_bloque()
        
        # Crear formulario con pestañas
        tabs = st.tabs(list(parametros_por_bloque.keys()))
        
        cambios = False
        
        for tab, (bloque_nombre, parametros) in zip(tabs, parametros_por_bloque.items()):
            with tab:
                st.subheader(bloque_nombre)
                
                for param_name, param_info in parametros.items():
                    current_value = self.estructura_actual.get(param_name)
                    
                    if param_info["tipo"] == "string_list":
                        options = param_info["opciones"]
                        index = options.index(current_value) if current_value in options else 0
                        new_value = st.selectbox(
                            param_info["descripcion"],
                            options,
                            index=index,
                            key=f"{param_name}_{bloque_nombre}"
                        )
                    
                    elif param_info["tipo"] == "boolean":
                        new_value = st.toggle(
                            param_info["descripcion"],
                            value=current_value,
                            key=f"{param_name}_{bloque_nombre}"
                        )
                    
                    elif param_info["tipo"] == "int":
                        if "min" in param_info and "max" in param_info:
                            new_value = st.slider(
                                param_info["descripcion"],
                                min_value=param_info["min"],
                                max_value=param_info["max"],
                                value=int(current_value),
                                step=1,
                                key=f"{param_name}_{bloque_nombre}"
                            )
                        else:
                            new_value = st.number_input(
                                param_info["descripcion"],
                                value=int(current_value),
                                step=1,
                                key=f"{param_name}_{bloque_nombre}"
                            )
                    
                    elif param_info["tipo"] == "float":
                        new_value = st.number_input(
                            param_info["descripcion"],
                            value=float(current_value),
                            step=0.01,
                            format="%.3f",
                            key=f"{param_name}_{bloque_nombre}"
                        )
                    
                    elif param_info["tipo"] == "cable_selection":
                        new_value = st.selectbox(
                            param_info["descripcion"],
                            self.cables_list,
                            index=self.cables_list.index(current_value) if current_value in self.cables_list else 0,
                            key=f"{param_name}_{bloque_nombre}"
                        )
                    
                    else:
                        new_value = st.text_input(
                            param_info["descripcion"],
                            value=str(current_value),
                            key=f"{param_name}_{bloque_nombre}"
                        )
                    
                    # Verificar si hubo cambio
                    if new_value != current_value:
                        self.estructura_actual[param_name] = new_value
                        cambios = True
        
        # Botón para guardar cambios
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                if cambios:
                    self.guardar_estructura(self.actual_path, self.estructura_actual)
                    st.success("✅ Cambios guardados exitosamente!")
                    st.rerun()
                else:
                    st.info("ℹ️ No se realizaron cambios")
    
    def organizar_parametros_por_bloque(self):
        """Organizar parámetros por bloques según comentarios en el código original"""
        
        bloques = {
            "📋 CONFIGURACIÓN GENERAL": {
                "TIPO_ESTRUCTURA": {
                    "tipo": "string_list",
                    "descripcion": "Tipo de Estructura",
                    "opciones": TIPOS_ESTRUCTURA
                },
                "exposicion": {
                    "tipo": "string_list",
                    "descripcion": "Exposición",
                    "opciones": EXPOSICIONES
                },
                "clase": {
                    "tipo": "string_list",
                    "descripcion": "Clase de línea",
                    "opciones": CLASES_LINEA
                },
                "TITULO": {
                    "tipo": "string",
                    "descripcion": "Título de la estructura"
                }
            },
            "📏 PARÁMETROS DE DISEÑO DE LÍNEA": {
                "L_vano": {
                    "tipo": "float",
                    "descripcion": "Longitud de vano (m)"
                },
                "alpha": {
                    "tipo": "float",
                    "descripcion": "Ángulo máximo de quiebre (grados)"
                },
                "theta": {
                    "tipo": "float",
                    "descripcion": "Ángulo de viento oblicuo (grados)"
                },
                "cable_conductor_id": {
                    "tipo": "cable_selection",
                    "descripcion": "Cable conductor"
                },
                "cable_guardia_id": {
                    "tipo": "cable_selection",
                    "descripcion": "Cable guardia"
                }
            },
            "🌬️ PARÁMETROS DEL VIENTO Y TEMPERATURA": {
                "Zona_climatica": {
                    "tipo": "string_list",
                    "descripcion": "Zona climática",
                    "opciones": ZONAS_CLIMATICAS
                },
                "Vmax": {
                    "tipo": "float",
                    "descripcion": "Velocidad máxima del viento (m/s)"
                },
                "Vmed": {
                    "tipo": "float",
                    "descripcion": "Velocidad media del viento (m/s)"
                },
                "Vtormenta": {
                    "tipo": "float",
                    "descripcion": "Velocidad de tormenta (m/s)"
                },
                "t_hielo": {
                    "tipo": "float",
                    "descripcion": "Espesor de hielo (m)"
                },
                "Q": {
                    "tipo": "float",
                    "descripcion": "Coeficiente de densidad del aire"
                }
            },
            "🏗️ CONFIGURACIÓN DE POSTES": {
                "FORZAR_N_POSTES": {
                    "tipo": "int",
                    "descripcion": "Forzar número de postes (0=auto)",
                    "min": 0,
                    "max": 3
                },
                "FORZAR_ORIENTACION": {
                    "tipo": "string_list",
                    "descripcion": "Forzar orientación",
                    "opciones": ORIENTACIONES
                },
                "PRIORIDAD_DIMENSIONADO": {
                    "tipo": "string_list",
                    "descripcion": "Prioridad de dimensionado",
                    "opciones": PRIORIDADES
                }
            },
            "🔌 CONFIGURACIÓN DISEÑO DE CABEZAL": {
                "TENSION": {
                    "tipo": "int",
                    "descripcion": "Tensión nominal (kV)",
                    "min": 1,
                    "max": 500
                },
                "Zona_estructura": {
                    "tipo": "string_list",
                    "descripcion": "Zona de estructura",
                    "opciones": ZONAS_ESTRUCTURA
                },
                "Lk": {
                    "tipo": "float",
                    "descripcion": "Longitud adicional de cadena (m)"
                },
                "ANG_APANTALLAMIENTO": {
                    "tipo": "float",
                    "descripcion": "Ángulo de apantallamiento (grados)"
                },
                "AJUSTAR_POR_ALTURA_MSNM": {
                    "tipo": "boolean",
                    "descripcion": "Ajustar por altura MSNM"
                },
                "Altura_MSNM": {
                    "tipo": "int",
                    "descripcion": "Altura sobre nivel del mar (m)"
                }
            },
            "⚡ DISPOSICIÓN DE CONDUCTORES": {
                "DISPOSICION": {
                    "tipo": "string_list",
                    "descripcion": "Disposición de conductores",
                    "opciones": DISPOSICIONES
                },
                "TERNA": {
                    "tipo": "string_list",
                    "descripcion": "Tipo de terna",
                    "opciones": TERNAS
                },
                "CANT_HG": {
                    "tipo": "int",
                    "descripcion": "Cantidad de cables guardia",
                    "min": 0,
                    "max": 2
                },
                "HG_CENTRADO": {
                    "tipo": "boolean",
                    "descripcion": "Cable guardia centrado"
                }
            },
            "📐 DIMENSIONES MÍNIMAS": {
                "ALTURA_MINIMA_CABLE": {
                    "tipo": "float",
                    "descripcion": "Altura mínima del cable (m)"
                },
                "LONGITUD_MENSULA_MINIMA_CONDUCTOR": {
                    "tipo": "float",
                    "descripcion": "Long. mínima ménsula conductor (m)"
                },
                "LONGITUD_MENSULA_MINIMA_GUARDIA": {
                    "tipo": "float",
                    "descripcion": "Long. mínima ménsula guardia (m)"
                },
                "HADD": {
                    "tipo": "float",
                    "descripcion": "Altura adicional base (m)"
                },
                "ANCHO_CRUCETA": {
                    "tipo": "float",
                    "descripcion": "Ancho de cruceta (m)"
                }
            },
            "⚙️ CONFIGURACIÓN DE FLECHADO": {
                "SALTO_PORCENTUAL": {
                    "tipo": "float",
                    "descripcion": "Salto porcentual"
                },
                "PASO_AFINADO": {
                    "tipo": "float",
                    "descripcion": "Paso afinado"
                },
                "OBJ_CONDUCTOR": {
                    "tipo": "string_list",
                    "descripcion": "Objetivo conductor",
                    "opciones": OBJETIVOS
                },
                "OBJ_GUARDIA": {
                    "tipo": "string_list",
                    "descripcion": "Objetivo guardia",
                    "opciones": OBJETIVOS
                },
                "RELFLECHA_MAX_GUARDIA": {
                    "tipo": "float",
                    "descripcion": "Relación flecha máxima guardia"
                },
                "RELFLECHA_SIN_VIENTO": {
                    "tipo": "boolean",
                    "descripcion": "Rel. flecha sin viento"
                }
            },
            "🎨 CONFIGURACIÓN GRÁFICOS": {
                "ZOOM_CABEZAL": {
                    "tipo": "float",
                    "descripcion": "Zoom del cabezal"
                },
                "REEMPLAZAR_TITULO_GRAFICO": {
                    "tipo": "boolean",
                    "descripcion": "Reemplazar título en gráficos"
                }
            }
        }
        
        return bloques

def main():
    # Inicializar aplicación
    app = EstructuraApp()
    
    # Mostrar menú principal
    menu_seleccionado = app.mostrar_menu_principal()
    
    # Navegar a sección seleccionada
    if menu_seleccionado == "📊 Dashboard":
        app.mostrar_dashboard()
    elif menu_seleccionado == "🆕 Nueva Estructura":
        app.mostrar_nueva_estructura()
    elif menu_seleccionado == "📂 Cargar Estructura":
        app.mostrar_cargar_estructura()
    elif menu_seleccionado == "📋 Cargar como Plantilla":
        app.mostrar_cargar_como_plantilla()
    elif menu_seleccionado == "💾 Guardar Estructura":
        app.mostrar_guardar_estructura()
    elif menu_seleccionado == "💾 Guardar Como":
        app.mostrar_guardar_como()
    elif menu_seleccionado == "⚙️ Ajustar Parámetros":
        app.mostrar_ajustar_parametros()
    
    # Mostrar información de pie de página
    st.sidebar.markdown("---")
    st.sidebar.caption(f"© {datetime.now().year} - Diseño de Estructuras v1.0")

if __name__ == "__main__":
    main()