import streamlit as st
import json
import os
import sys
from datetime import datetime

st.set_page_config(
    page_title="AGP: Análisis Geométrico de Postes",
    page_icon="🏗️",
    layout="wide"
)

TIPOS_ESTRUCTURA = ["Suspensión Recta", "Suspensión Angular", "Retención / Ret. Angular", "Terminal", "Especial"]
EXPOSICIONES = ["B", "C", "D"]
CLASES_LINEA = ["A", "B", "BB", "C", "D", "E"]
ZONAS_CLIMATICAS = ["A", "B", "C", "D", "E"]
ZONAS_ESTRUCTURA = ["Peatonal", "Rural", "Urbana", "Autopista", "Ferrocarril", "Línea Eléctrica"]
DISPOSICIONES = ["triangular", "horizontal", "vertical"]
TERNAS = ["Simple", "Doble"]
ORIENTACIONES = ["Longitudinal", "Transversal", "No"]
PRIORIDADES = ["altura_libre", "longitud_total"]
OBJETIVOS = ["FlechaMin", "TiroMin"]

st.markdown("""
<style>
.fixed-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: #007bff;
    color: white;
    padding: 10px 20px;
    z-index: 1000;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    height: 120px;
}
.main-content {
    margin-top: 130px;
}
.header-title {
    font-size: 1.2rem;
    font-weight: bold;
    margin: 0;
    padding: 0;
}
.structure-info {
    font-size: 0.9rem;
    margin: 5px 0 10px 0;
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
}
.file-menu {
    position: absolute;
    top: 15px;
    left: 20px;
    z-index: 1001;
}
</style>
""", unsafe_allow_html=True)

class EstructuraApp:
    def __init__(self):
        self.estructura_actual = None
        self.plantilla_path = "plantilla.estructura.json"
        self.actual_path = "actual.estructura.json"
        self.cables_path = "cables.json"
        self.cargar_cables()
        self.inicializar_estructura()
    
    def cargar_cables(self):
        try:
            with open(self.cables_path, 'r', encoding='utf-8') as f:
                self.cables_data = json.load(f)
            self.cables_list = list(self.cables_data.keys())
        except:
            st.error(f"Archivo {self.cables_path} no encontrado")
            self.cables_data = {}
            self.cables_list = []
    
    def cargar_plantilla(self):
        try:
            with open(self.plantilla_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            plantilla = {
                "TIPO_ESTRUCTURA": "Suspensión Recta", "Zona_climatica": "D", "exposicion": "C", "clase": "C",
                "TITULO": "2x220 DTT SAN JORGE PRUEBAS", "cable_conductor_id": "AlAc 435/55",
                "cable_guardia_id": "OPGW FiberHome 24FO 58mm2", "Vmax": 38.9, "Vmed": 15.56, "Vtormenta": 20.0,
                "t_hielo": 0.01, "Q": 0.0613, "Zco": 13.0, "Zcg": 13.0, "Zca": 13.0, "Zes": 10.0,
                "Cf_cable": 1.0, "Cf_guardia": 1.0, "Cf_cadena": 0.9, "Cf_estructura": 0.9, "L_vano": 400.0,
                "alpha": 0.0, "theta": 45.0, "A_cadena": 0.03, "PCADENA": 10.5, "PESTRUCTURA": 3900.0,
                "A_estr_trans": 2.982, "A_estr_long": 4.482, "FORZAR_N_POSTES": 1, "FORZAR_ORIENTACION": "No",
                "PRIORIDAD_DIMENSIONADO": "altura_libre", "TENSION": 220, "Zona_estructura": "Rural", "Lk": 2.5,
                "ANG_APANTALLAMIENTO": 30.0, "AJUSTAR_POR_ALTURA_MSNM": True, "METODO_ALTURA_MSNM": "AEA 3%/300m",
                "Altura_MSNM": 3000, "DISPOSICION": "triangular", "TERNA": "Doble", "CANT_HG": 2,
                "HG_CENTRADO": False, "ALTURA_MINIMA_CABLE": 6.5, "LONGITUD_MENSULA_MINIMA_CONDUCTOR": 1.3,
                "LONGITUD_MENSULA_MINIMA_GUARDIA": 0.2, "HADD": 0.4, "HADD_ENTRE_AMARRES": 0.2, "HADD_HG": 1.5,
                "HADD_LMEN": 0.5, "ANCHO_CRUCETA": 0.3, "AUTOAJUSTAR_LMENHG": True, "DIST_REPOSICIONAR_HG": 0.1,
                "MOSTRAR_C2": False, "SALTO_PORCENTUAL": 0.05, "PASO_AFINADO": 0.005, "OBJ_CONDUCTOR": "FlechaMin",
                "OBJ_GUARDIA": "TiroMin", "RELFLECHA_MAX_GUARDIA": 0.95, "RELFLECHA_SIN_VIENTO": True,
                "ZOOM_CABEZAL": 0.95, "REEMPLAZAR_TITULO_GRAFICO": False, "Vn": 220,
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d"), "version": "1.0"
            }
            self.guardar_estructura(self.plantilla_path, plantilla)
            return plantilla
    
    def inicializar_estructura(self):
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
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(estructura, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error al guardar: {e}")
            return False
    
    def cargar_desde_archivo(self, uploaded_file):
        try:
            estructura = json.load(uploaded_file)
            if all(key in estructura for key in ["TITULO", "TIPO_ESTRUCTURA", "TENSION"]):
                return estructura
            else:
                st.error("Archivo no contiene estructura válida")
                return None
        except Exception as e:
            st.error(f"Error al cargar archivo: {e}")
            return None
    
    def listar_estructuras(self):
        return [f for f in os.listdir(".") if f.endswith(".estructura.json")]
    
    def mostrar_header(self):
        # Panel fijo con HTML/CSS
        html_header = f"""
        <div class="fixed-header">
            <div class="header-title">AGP: ANÁLISIS GEOMÉTRICO DE POSTES</div>
        """
        
        if self.estructura_actual:
            html_header += f"""
                📁 {self.estructura_actual['TITULO']} | {self.estructura_actual['TIPO_ESTRUCTURA']} |⚡{self.estructura_actual['TENSION']} kV | 📏{self.estructura_actual['L_vano']} m
            """      
        
        # Renderizar el panel fijo
        st.markdown(html_header, unsafe_allow_html=True)
        
        # Contenedor para el contenido principal
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        # Menú Archivo en la parte superior izquierda (usando Streamlit)
        with st.container():
            col1, col2, col3 = st.columns([1, 10, 1])
            with col1:
                with st.popover("📁 **Archivo**", use_container_width=True):
                    menu_opcion = st.radio(
                        "Opciones",
                        ["🆕 Nueva Estructura", "📂 Cargar Estructura", "📋 Cargar como Plantilla",
                         "💾 Guardar Estructura", "💾 Guardar Como", "🗑️ Eliminar Estructura",
                         "⚙️ Configurar Estructura"],
                        label_visibility="collapsed"
                    )
        
        return menu_opcion
    
    def mostrar_nueva_estructura(self):
        st.title("🆕 Nueva Estructura")
        with st.form("nueva_estructura_form"):
            titulo = st.text_input("Título de la Nueva Estructura", 
                                  value=f"Nueva Estructura {datetime.now().strftime('%Y%m%d_%H%M')}")
            if st.form_submit_button("🔧 Crear Nueva Estructura", type="primary", use_container_width=True):
                if titulo.strip():
                    nueva_estructura = self.cargar_plantilla()
                    nueva_estructura["TITULO"] = titulo
                    nueva_estructura["fecha_creacion"] = datetime.now().strftime("%Y-%m-%d")
                    self.estructura_actual = nueva_estructura
                    self.guardar_estructura(self.actual_path, nueva_estructura)
                    st.success(f"✅ Nueva estructura '{titulo}' creada!")
                    st.rerun()
    
    def mostrar_cargar_estructura(self):
        st.title("📂 Cargar Estructura")
        tab1, tab2 = st.tabs(["📁 Desde Base de Datos", "💻 Desde Computadora"])
        with tab1:
            estructuras = self.listar_estructuras()
            if estructuras:
                estructura_seleccionada = st.selectbox("Seleccionar estructura", estructuras,
                                                      format_func=lambda x: x.replace(".estructura.json", ""))
                if st.button("📥 Cargar Estructura", type="primary", use_container_width=True):
                    try:
                        with open(estructura_seleccionada, 'r', encoding='utf-8') as f:
                            self.estructura_actual = json.load(f)
                        self.guardar_estructura(self.actual_path, self.estructura_actual)
                        st.success(f"✅ Estructura '{estructura_seleccionada}' cargada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.info("No hay estructuras guardadas")
        with tab2:
            uploaded_file = st.file_uploader("Seleccionar archivo .estructura.json", type=["json"])
            if uploaded_file and uploaded_file.name.endswith(".estructura.json"):
                if st.button("📥 Cargar Archivo", type="primary", use_container_width=True):
                    estructura = self.cargar_desde_archivo(uploaded_file)
                    if estructura:
                        self.estructura_actual = estructura
                        self.guardar_estructura(self.actual_path, estructura)
                        st.success("✅ Estructura cargada!")
                        st.rerun()
    
    def mostrar_cargar_como_plantilla(self):
        st.title("📋 Cargar Estructura como Plantilla")
        tab1, tab2 = st.tabs(["📁 Desde Base de Datos", "💻 Desde Computadora"])
        with tab1:
            estructuras = self.listar_estructuras()
            if estructuras:
                estructura_seleccionada = st.selectbox("Seleccionar estructura", estructuras,
                                                      key="plantilla_db",
                                                      format_func=lambda x: x.replace(".estructura.json", ""))
                if st.button("📋 Establecer como Plantilla", type="primary", use_container_width=True):
                    try:
                        with open(estructura_seleccionada, 'r', encoding='utf-8') as f:
                            nueva_plantilla = json.load(f)
                        self.guardar_estructura(self.plantilla_path, nueva_plantilla)
                        st.success("✅ Plantilla actualizada!")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        with tab2:
            uploaded_file = st.file_uploader("Seleccionar archivo .estructura.json", type=["json"], key="plantilla_file")
            if uploaded_file and uploaded_file.name.endswith(".estructura.json"):
                if st.button("📋 Establecer como Plantilla", type="primary", use_container_width=True):
                    estructura = self.cargar_desde_archivo(uploaded_file)
                    if estructura:
                        self.guardar_estructura(self.plantilla_path, estructura)
                        st.success("✅ Plantilla actualizada!")
    
    def mostrar_guardar_estructura(self):
        st.title("💾 Guardar Estructura")
        if not self.estructura_actual:
            st.warning("No hay estructura cargada")
            return
        tab1, tab2 = st.tabs(["💾 Guardar en Base de Datos", "💻 Guardar en Computadora"])
        with tab1:
            nombre_base = self.estructura_actual['TITULO'].replace(' ', '_').lower()
            col1, col2 = st.columns([4, 1])
            with col1:
                nombre_parte = st.text_input("Nombre del archivo (sin extensión)", value=nombre_base)
            with col2:
                st.text_input("Extensión", value=".estructura.json", disabled=True)
            nombre_archivo = nombre_parte + ".estructura.json"
            if os.path.exists(nombre_archivo):
                st.warning(f"⚠️ El archivo '{nombre_archivo}' ya existe")
                sobreescribir = st.checkbox("Sobreescribir")
            else:
                sobreescribir = True
            if st.button("💾 Guardar en Base de Datos", type="primary", use_container_width=True) and sobreescribir:
                if self.guardar_estructura(nombre_archivo, self.estructura_actual):
                    st.success(f"✅ Guardada como '{nombre_archivo}'")
        with tab2:
            json_str = json.dumps(self.estructura_actual, indent=2, ensure_ascii=False)
            nombre_descarga = f"{self.estructura_actual['TITULO'].replace(' ', '_').lower()}.estructura.json"
            st.download_button("📥 Descargar Estructura", data=json_str, file_name=nombre_descarga,
                             mime="application/json", type="primary", use_container_width=True)
    
    def mostrar_guardar_como(self):
        st.title("💾 Guardar Estructura Como")
        if not self.estructura_actual:
            st.warning("No hay estructura cargada")
            return
        with st.form("guardar_como_form"):
            nuevo_titulo = st.text_input("Nuevo Título", value=self.estructura_actual["TITULO"])
            col1, col2 = st.columns([4, 1])
            with col1:
                nombre_parte = st.text_input("Nombre del archivo (sin extensión)", 
                                           value=nuevo_titulo.replace(' ', '_').lower())
            with col2:
                st.text_input("Extensión", value=".estructura.json", disabled=True)
            nombre_archivo = nombre_parte + ".estructura.json"
            col1, col2 = st.columns(2)
            with col1:
                guardar_db = st.checkbox("Guardar en Base de Datos", value=True)
            with col2:
                guardar_actual = st.checkbox("Actualizar estructura actual", value=True)
            if st.form_submit_button("💾 Guardar Como", type="primary", use_container_width=True):
                nueva_estructura = self.estructura_actual.copy()
                nueva_estructura["TITULO"] = nuevo_titulo
                if guardar_db:
                    if self.guardar_estructura(nombre_archivo, nueva_estructura):
                        st.success(f"✅ Guardada como '{nombre_archivo}'")
                if guardar_actual:
                    self.estructura_actual = nueva_estructura
                    self.guardar_estructura(self.actual_path, nueva_estructura)
                    st.success("✅ Estructura actual actualizada")
    
    def mostrar_eliminar_estructura(self):
        st.title("🗑️ Eliminar Estructura")
        estructuras = self.listar_estructuras()
        estructuras_eliminables = [e for e in estructuras if e not in [self.plantilla_path, self.actual_path]]
        if not estructuras_eliminables:
            st.info("No hay estructuras eliminables")
            st.warning(f"No se pueden eliminar: '{self.plantilla_path}' y '{self.actual_path}'")
            return
        st.warning("⚠️ **ADVERTENCIA:** Esta acción elimina permanentemente el archivo.")
        estructura_seleccionada = st.selectbox("Seleccionar estructura a eliminar", estructuras_eliminables,
                                              format_func=lambda x: x.replace(".estructura.json", ""))
        if estructura_seleccionada:
            try:
                with open(estructura_seleccionada, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Título", info.get("TITULO", "Desconocido"))
                with col2:
                    st.metric("Tipo", info.get("TIPO_ESTRUCTURA", "Desconocido"))
                with col3:
                    st.metric("Fecha", info.get("fecha_creacion", "Desconocido"))
            except:
                st.error(f"No se pudo leer '{estructura_seleccionada}'")
        confirmacion = st.checkbox("Confirmo eliminar permanentemente")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Eliminar", type="secondary", use_container_width=True, disabled=not confirmacion):
                try:
                    os.remove(estructura_seleccionada)
                    st.success(f"✅ '{estructura_seleccionada}' eliminada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        with col2:
            if st.button("🔄 Actualizar Lista", type="primary", use_container_width=True):
                st.rerun()
    
    def mostrar_configurar_estructura(self):
        st.title("⚙️ Configurar Estructura")
        if not self.estructura_actual:
            st.warning("No hay estructura cargada")
            return
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                self.guardar_estructura(self.actual_path, self.estructura_actual)
                st.success("✅ Cambios guardados!")
                st.rerun()
        with col2:
            if st.button("🔄 Revertir a Plantilla", type="secondary", use_container_width=True):
                self.estructura_actual = self.cargar_plantilla()
                self.guardar_estructura(self.actual_path, self.estructura_actual)
                st.success("✅ Revertido a plantilla!")
                st.rerun()
        st.markdown("---")
        bloques = self.organizar_parametros_por_bloque()
        for bloque_nombre, parametros in bloques.items():
            st.markdown(f"### {bloque_nombre}")
            items = list(parametros.items())
            for i in range(0, len(items), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(items):
                        param_name, param_info = items[i + j]
                        with cols[j]:
                            self.mostrar_campo_parametro(param_name, param_info)
            st.markdown("---")
    
    def mostrar_campo_parametro(self, param_name, param_info):
        current_value = self.estructura_actual.get(param_name)
        if param_info["tipo"] == "string_list":
            new_value = st.selectbox(param_info["descripcion"], param_info["opciones"],
                                   index=param_info["opciones"].index(current_value) 
                                   if current_value in param_info["opciones"] else 0, key=param_name)
        elif param_info["tipo"] == "boolean":
            new_value = st.toggle(param_info["descripcion"], value=current_value, key=param_name)
        elif param_info["tipo"] == "int":
            if "min" in param_info and "max" in param_info:
                new_value = st.slider(param_info["descripcion"], param_info["min"], param_info["max"],
                                     int(current_value), step=1, key=param_name)
            else:
                new_value = st.number_input(param_info["descripcion"], value=int(current_value), step=1, key=param_name)
        elif param_info["tipo"] == "float":
            new_value = st.number_input(param_info["descripcion"], value=float(current_value), 
                                       step=0.01, format="%.3f", key=param_name)
        elif param_info["tipo"] == "cable_selection":
            new_value = st.selectbox(param_info["descripcion"], self.cables_list,
                                   index=self.cables_list.index(current_value) 
                                   if current_value in self.cables_list else 0, key=param_name)
        else:
            new_value = st.text_input(param_info["descripcion"], value=str(current_value), key=param_name)
        if new_value != current_value:
            self.estructura_actual[param_name] = new_value
    
    def organizar_parametros_por_bloque(self):
        return {
            "📋 CONFIGURACIÓN GENERAL": {
                "TIPO_ESTRUCTURA": {"tipo": "string_list", "descripcion": "Tipo de Estructura", "opciones": TIPOS_ESTRUCTURA},
                "exposicion": {"tipo": "string_list", "descripcion": "Exposición", "opciones": EXPOSICIONES},
                "clase": {"tipo": "string_list", "descripcion": "Clase de línea", "opciones": CLASES_LINEA},
                "TITULO": {"tipo": "string", "descripcion": "Título de la estructura"}
            },
            "📏 PARÁMETROS DE DISEÑO DE LÍNEA": {
                "L_vano": {"tipo": "float", "descripcion": "Longitud de vano (m)"},
                "alpha": {"tipo": "float", "descripcion": "Ángulo de quiebre (grados)"},
                "theta": {"tipo": "float", "descripcion": "Ángulo viento oblicuo (grados)"},
                "cable_conductor_id": {"tipo": "cable_selection", "descripcion": "Cable conductor"},
                "cable_guardia_id": {"tipo": "cable_selection", "descripcion": "Cable guardia"}
            },
            "🌬️ PARÁMETROS DEL VIENTO Y TEMPERATURA": {
                "Zona_climatica": {"tipo": "string_list", "descripcion": "Zona climática", "opciones": ZONAS_CLIMATICAS},
                "Vmax": {"tipo": "float", "descripcion": "Viento máximo (m/s)"},
                "Vmed": {"tipo": "float", "descripcion": "Viento medio (m/s)"},
                "t_hielo": {"tipo": "float", "descripcion": "Espesor de hielo (m)"},
                "Q": {"tipo": "float", "descripcion": "Coeficiente densidad aire"}
            },
            "🏗️ CONFIGURACIÓN DE POSTES": {
                "FORZAR_N_POSTES": {"tipo": "int", "descripcion": "Forzar nº postes (0=auto)", "min": 0, "max": 3},
                "FORZAR_ORIENTACION": {"tipo": "string_list", "descripcion": "Forzar orientación", "opciones": ORIENTACIONES},
                "PRIORIDAD_DIMENSIONADO": {"tipo": "string_list", "descripcion": "Prioridad", "opciones": PRIORIDADES}
            },
            "🔌 CONFIGURACIÓN DISEÑO DE CABEZAL": {
                "TENSION": {"tipo": "int", "descripcion": "Tensión (kV)", "min": 1, "max": 500},
                "Zona_estructura": {"tipo": "string_list", "descripcion": "Zona de estructura", "opciones": ZONAS_ESTRUCTURA},
                "Lk": {"tipo": "float", "descripcion": "Long. adicional cadena (m)"},
                "ANG_APANTALLAMIENTO": {"tipo": "float", "descripcion": "Ángulo apantallamiento (grados)"},
                "AJUSTAR_POR_ALTURA_MSNM": {"tipo": "boolean", "descripcion": "Ajustar por altura MSNM"},
                "Altura_MSNM": {"tipo": "int", "descripcion": "Altura MSNM (m)"}
            },
            "⚡ DISPOSICIÓN DE CONDUCTORES": {
                "DISPOSICION": {"tipo": "string_list", "descripcion": "Disposición", "opciones": DISPOSICIONES},
                "TERNA": {"tipo": "string_list", "descripcion": "Tipo de terna", "opciones": TERNAS},
                "CANT_HG": {"tipo": "int", "descripcion": "Cant. cables guardia", "min": 0, "max": 2},
                "HG_CENTRADO": {"tipo": "boolean", "descripcion": "Cable guardia centrado"}
            },
            "📐 DIMENSIONES MÍNIMAS": {
                "ALTURA_MINIMA_CABLE": {"tipo": "float", "descripcion": "Altura mínima cable (m)"},
                "LONGITUD_MENSULA_MINIMA_CONDUCTOR": {"tipo": "float", "descripcion": "Long. mínima ménsula conductor (m)"},
                "LONGITUD_MENSULA_MINIMA_GUARDIA": {"tipo": "float", "descripcion": "Long. mínima ménsula guardia (m)"},
                "HADD": {"tipo": "float", "descripcion": "Altura adicional base (m)"},
                "ANCHO_CRUCETA": {"tipo": "float", "descripcion": "Ancho de cruceta (m)"}
            },
            "⚙️ CONFIGURACIÓN DE FLECHADO": {
                "SALTO_PORCENTUAL": {"tipo": "float", "descripcion": "Salto porcentual"},
                "PASO_AFINADO": {"tipo": "float", "descripcion": "Paso afinado"},
                "OBJ_CONDUCTOR": {"tipo": "string_list", "descripcion": "Objetivo conductor", "opciones": OBJETIVOS},
                "OBJ_GUARDIA": {"tipo": "string_list", "descripcion": "Objetivo guardia", "opciones": OBJETIVOS},
                "RELFLECHA_MAX_GUARDIA": {"tipo": "float", "descripcion": "Relación flecha máxima"},
                "RELFLECHA_SIN_VIENTO": {"tipo": "boolean", "descripcion": "Rel. flecha sin viento"}
            },
            "🎨 CONFIGURACIÓN GRÁFICOS": {
                "ZOOM_CABEZAL": {"tipo": "float", "descripcion": "Zoom del cabezal"},
                "REEMPLAZAR_TITULO_GRAFICO": {"tipo": "boolean", "descripcion": "Reemplazar título"}
            }
        }

def main():
    app = EstructuraApp()
    menu_seleccionado = app.mostrar_header()
    
    if menu_seleccionado == "🆕 Nueva Estructura":
        app.mostrar_nueva_estructura()
    elif menu_seleccionado == "📂 Cargar Estructura":
        app.mostrar_cargar_estructura()
    elif menu_seleccionado == "📋 Cargar como Plantilla":
        app.mostrar_cargar_como_plantilla()
    elif menu_seleccionado == "💾 Guardar Estructura":
        app.mostrar_guardar_estructura()
    elif menu_seleccionado == "💾 Guardar Como":
        app.mostrar_guardar_como()
    elif menu_seleccionado == "🗑️ Eliminar Estructura":
        app.mostrar_eliminar_estructura()
    elif menu_seleccionado == "⚙️ Configurar Estructura":
        app.mostrar_configurar_estructura()
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; color: gray;'>© {datetime.now().year} - AGP: Análisis Geométrico de Postes - v15</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()