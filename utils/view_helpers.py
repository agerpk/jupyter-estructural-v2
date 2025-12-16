"""Helpers centralizados para vistas - Carga y guardado de datos de caché"""

import base64
import json
from pathlib import Path
from dash import html, dcc
import dash_bootstrap_components as dbc
from config.app_config import CACHE_DIR


class ViewHelpers:
    """Utilidades para simplificar carga y guardado de datos en vistas"""
    
    # ==================== CARGA DE IMÁGENES ====================
    
    @staticmethod
    def cargar_imagen_base64(nombre_archivo):
        """Carga imagen y retorna string base64
        
        Args:
            nombre_archivo: Nombre del archivo PNG
            
        Returns:
            String base64 o None si no existe
        """
        img_path = CACHE_DIR / nombre_archivo
        print(f"Buscando imagen: {img_path}")
        if not img_path.exists():
            print(f"❌ Imagen no encontrada: {img_path}")
            return None
        
        try:
            with open(img_path, 'rb') as f:
                print(f"✅ Imagen cargada: {nombre_archivo}")
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            print(f"❌ Error cargando imagen: {e}")
            return None
    
    @staticmethod
    def crear_img_component(nombre_archivo, style=None, className=None):
        """Crea componente html.Img desde archivo
        
        Args:
            nombre_archivo: Nombre del archivo PNG
            style: Dict con estilos CSS (opcional)
            className: Clases CSS (opcional)
            
        Returns:
            html.Img o None si no existe imagen
        """
        img_str = ViewHelpers.cargar_imagen_base64(nombre_archivo)
        if not img_str:
            print(f"⚠️ No se pudo crear componente para: {nombre_archivo}")
            return None
        
        default_style = {'width': '100%', 'maxWidth': '1000px'}
        final_style = {**default_style, **(style or {})}
        
        print(f"✅ Componente creado para: {nombre_archivo}")
        return html.Img(
            src=f'data:image/png;base64,{img_str}',
            style=final_style,
            className=className
        )
    
    @staticmethod
    def cargar_imagenes_por_hash(hash_params, patrones_imagenes):
        """Carga múltiples imágenes basadas en hash
        
        Args:
            hash_params: Hash de parámetros
            patrones_imagenes: Lista de tuplas (patron, titulo, style)
                Ejemplo: [("CMC_Combinado.{hash}.png", "Combinado", {})]
        
        Returns:
            Lista de componentes HTML
        """
        if not hash_params:
            return []
        
        componentes = []
        for patron, titulo, style in patrones_imagenes:
            nombre_archivo = patron.format(hash=hash_params)
            img_component = ViewHelpers.crear_img_component(nombre_archivo, style)
            
            if img_component:
                componentes.extend([
                    html.H6(titulo, className="mt-3"),
                    img_component
                ])
        
        return componentes
    
    @staticmethod
    def guardar_imagen_plotly(fig, nombre_archivo, width=1200, height=600):
        """Guarda figura Plotly como PNG
        
        Args:
            fig: Figura Plotly
            nombre_archivo: Nombre del archivo (sin path)
            width: Ancho en pixels
            height: Alto en pixels
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not fig:
            return False
        
        img_path = CACHE_DIR / nombre_archivo
        try:
            fig.write_image(str(img_path), width=width, height=height)
            return True
        except Exception as e:
            print(f"Error guardando imagen Plotly {nombre_archivo}: {e}")
            return False
    
    @staticmethod
    def guardar_figura_plotly_json(fig, nombre_archivo):
        """Guarda figura Plotly como JSON para mantener interactividad
        
        Args:
            fig: Figura Plotly
            nombre_archivo: Nombre del archivo JSON (sin path)
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not fig:
            print(f"Advertencia: Figura vacía para {nombre_archivo}")
            return False
        
        json_path = CACHE_DIR / nombre_archivo
        try:
            # Usar write_json con encoding explícito
            fig.write_json(str(json_path), pretty=False, engine='json')
            print(f"✅ JSON guardado: {nombre_archivo}")
            return True
        except Exception as e:
            print(f"❌ Error guardando JSON Plotly {nombre_archivo}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def cargar_figura_plotly_json(nombre_archivo):
        """Carga figura Plotly desde JSON
        
        Args:
            nombre_archivo: Nombre del archivo JSON
            
        Returns:
            Dict con figura Plotly o None si no existe
        """
        json_path = CACHE_DIR / nombre_archivo
        if not json_path.exists():
            print(f"⚠️ JSON no encontrado: {nombre_archivo}")
            return None
        
        try:
            # Intentar múltiples encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(json_path, 'r', encoding=encoding) as f:
                        fig_dict = json.load(f)
                        print(f"✅ JSON cargado: {nombre_archivo} (encoding: {encoding})")
                        return fig_dict
                except UnicodeDecodeError:
                    continue
            
            # Si ninguno funciona, intentar con errors='ignore'
            with open(json_path, 'r', encoding='utf-8', errors='ignore') as f:
                fig_dict = json.load(f)
                print(f"⚠️ JSON cargado con caracteres ignorados: {nombre_archivo}")
                return fig_dict
        except Exception as e:
            print(f"❌ Error cargando JSON Plotly {nombre_archivo}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def crear_grafico_interactivo(nombre_archivo, config=None, style=None):
        """Crea componente dcc.Graph desde JSON guardado
        
        Args:
            nombre_archivo: Nombre del archivo JSON
            config: Configuración del gráfico (opcional)
            style: Estilos CSS del contenedor (opcional)
            
        Returns:
            dcc.Graph o None si no existe el archivo
        """
        fig_dict = ViewHelpers.cargar_figura_plotly_json(nombre_archivo)
        if not fig_dict:
            return None
        
        # Configuración que preserva ejes y proporciones
        default_config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
        final_config = {**default_config, **(config or {})}
        
        # Estilo que preserva dimensiones - sin responsive para evitar deformación
        default_style = {'width': '100%', 'maxWidth': '1200px', 'height': '600px'}
        final_style = {**default_style, **(style or {})}
        
        return dcc.Graph(
            figure=fig_dict,
            config=final_config,
            style=final_style
        )
    
    @staticmethod
    def guardar_imagen_matplotlib(fig, nombre_archivo, dpi=150, bbox_inches='tight'):
        """Guarda figura Matplotlib como PNG
        
        Args:
            fig: Figura Matplotlib
            nombre_archivo: Nombre del archivo (sin path)
            dpi: Resolución
            bbox_inches: Ajuste de bordes
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not fig:
            return False
        
        img_path = CACHE_DIR / nombre_archivo
        try:
            fig.savefig(str(img_path), format='png', dpi=dpi, bbox_inches=bbox_inches)
            return True
        except Exception as e:
            print(f"Error guardando imagen Matplotlib {nombre_archivo}: {e}")
            return False
    
    # ==================== COMPONENTES DE ALERTA ====================
    
    @staticmethod
    def crear_alerta_cache(mostrar_vigencia=False, vigente=True):
        """Crea alerta estándar de carga desde caché
        
        Args:
            mostrar_vigencia: Si True, muestra estado de vigencia
            vigente: Si los datos son vigentes
            
        Returns:
            dbc.Alert component
        """
        if not mostrar_vigencia:
            return dbc.Alert(
                "Resultados cargados desde cálculo anterior",
                color="info",
                className="mb-3"
            )
        
        if vigente:
            return dbc.Alert(
                "✅ Resultados cargados desde cache (parámetros sin cambios)",
                color="success",
                className="mb-3"
            )
        else:
            return dbc.Alert(
                "⚠️ Resultados cargados desde cache - ATENCIÓN: Los parámetros han cambiado, recalcular para actualizar",
                color="warning",
                className="mb-3"
            )
    
    # ==================== COMPONENTES DE TEXTO ====================
    
    @staticmethod
    def crear_pre_output(texto, titulo=None, max_height='300px', font_size='0.85rem'):
        """Crea componente Pre estilizado para output de consola
        
        Args:
            texto: Texto a mostrar
            titulo: Título opcional
            max_height: Altura máxima del contenedor
            font_size: Tamaño de fuente
            
        Returns:
            Lista de componentes HTML
        """
        componentes = []
        
        if titulo:
            componentes.append(html.H5(titulo, className="mb-2"))
        
        componentes.append(
            html.Pre(
                texto,
                style={
                    'backgroundColor': '#1e1e1e',
                    'color': '#d4d4d4',
                    'padding': '10px',
                    'borderRadius': '5px',
                    'fontSize': font_size,
                    'maxHeight': max_height,
                    'overflowY': 'auto',
                    'whiteSpace': 'pre-wrap',
                    'fontFamily': 'monospace'
                }
            )
        )
        
        return componentes
    
    # ==================== TABLAS ====================
    
    @staticmethod
    def crear_tabla_desde_dataframe(df, titulo=None, responsive=True, **table_kwargs):
        """Crea tabla Bootstrap desde DataFrame
        
        Args:
            df: DataFrame de pandas
            titulo: Título opcional
            responsive: Si True, envuelve en div responsive
            **table_kwargs: Argumentos para dbc.Table.from_dataframe
            
        Returns:
            Lista de componentes HTML
        """
        componentes = []
        
        if titulo:
            componentes.append(html.H5(titulo, className="mt-4 mb-2"))
        
        default_kwargs = {
            'striped': True,
            'bordered': True,
            'hover': True,
            'size': 'sm'
        }
        final_kwargs = {**default_kwargs, **table_kwargs}
        
        tabla = dbc.Table.from_dataframe(df, **final_kwargs)
        
        if responsive:
            componentes.append(
                html.Div(tabla, className="table-responsive")
            )
        else:
            componentes.append(tabla)
        
        return componentes
    
    @staticmethod
    def crear_tabla_html_iframe(df, altura_fila=25, altura_min=150, altura_max=600):
        """Crea tabla HTML en iframe con altura dinámica
        
        Args:
            df: DataFrame de pandas
            altura_fila: Altura estimada por fila en pixels
            altura_min: Altura mínima del iframe
            altura_max: Altura máxima del iframe
            
        Returns:
            html.Iframe component
        """
        html_table = f'''<html><head><style>
            body {{ margin: 0; padding: 10px; background: white; font-family: Arial, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; font-size: 11px; }}
            th, td {{ border: 1px solid #dee2e6; padding: 4px 6px; text-align: right; }}
            th {{ background-color: #f8f9fa; font-weight: 600; position: sticky; top: 0; z-index: 10; }}
            tr:nth-child(even) {{ background-color: #f8f9fa; }}
            tr:hover {{ background-color: #e9ecef; }}
        </style></head><body>{df.to_html(border=0, index=False)}</body></html>'''
        
        altura_tabla = min(max(len(df) * altura_fila + 80, altura_min), altura_max)
        
        return html.Iframe(
            srcDoc=html_table,
            style={
                'width': '100%',
                'height': f'{altura_tabla}px',
                'border': '1px solid #dee2e6',
                'borderRadius': '4px'
            }
        )
    
    # ==================== HELPERS DE GUARDADO ====================
    
    @staticmethod
    def guardar_imagenes_calculo(hash_params, imagenes_config):
        """Guarda múltiples imágenes de un cálculo (PNG + JSON para Plotly)
        
        Args:
            hash_params: Hash de parámetros
            imagenes_config: Lista de tuplas (fig, tipo, nombre_patron, es_plotly, kwargs)
                Ejemplo: [(fig_comb, "plotly", "CMC_Combinado.{hash}.png", True, {})]
        
        Returns:
            Dict con listas de archivos guardados: {'png': [...], 'json': [...]}
        """
        guardados = {'png': [], 'json': []}
        
        for config in imagenes_config:
            fig, tipo, patron, es_plotly, kwargs = config
            if not fig:
                continue
            
            nombre_archivo = patron.format(hash=hash_params)
            
            if es_plotly:
                # Guardar PNG
                exito_png = ViewHelpers.guardar_imagen_plotly(fig, nombre_archivo, **kwargs)
                if exito_png:
                    guardados['png'].append(nombre_archivo)
                
                # Guardar JSON para interactividad
                nombre_json = nombre_archivo.replace('.png', '.json')
                exito_json = ViewHelpers.guardar_figura_plotly_json(fig, nombre_json)
                if exito_json:
                    guardados['json'].append(nombre_json)
            else:
                exito = ViewHelpers.guardar_imagen_matplotlib(fig, nombre_archivo, **kwargs)
                if exito:
                    guardados['png'].append(nombre_archivo)
        
        return guardados
    
    @staticmethod
    def cargar_graficos_interactivos_por_hash(hash_params, patrones_graficos):
        """Carga múltiples gráficos interactivos basados en hash
        
        Args:
            hash_params: Hash de parámetros
            patrones_graficos: Lista de tuplas (patron, titulo, config, style)
                Ejemplo: [("CMC_Combinado.{hash}.json", "Combinado", {}, {})]
        
        Returns:
            Lista de componentes HTML con gráficos interactivos
        """
        if not hash_params:
            return []
        
        componentes = []
        for item in patrones_graficos:
            # Soportar tuplas de 3 o 4 elementos
            if len(item) == 3:
                patron, titulo, config = item
                style = None
            else:
                patron, titulo, config, style = item
            
            nombre_archivo = patron.format(hash=hash_params)
            grafico = ViewHelpers.crear_grafico_interactivo(nombre_archivo, config, style)
            
            if grafico:
                componentes.extend([
                    html.H6(titulo, className="mt-3"),
                    grafico
                ])
        
        return componentes
    
    # ==================== HELPERS DE FORMATO ====================
    
    @staticmethod
    def limpiar_emojis(texto):
        """Elimina emojis de un texto
        
        Args:
            texto: String con posibles emojis
            
        Returns:
            String sin emojis
        """
        import re
        return re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', texto)
    
    @staticmethod
    def formatear_parametros_estructura(estructura_actual, campos):
        """Formatea parámetros de estructura como texto
        
        Args:
            estructura_actual: Dict con datos de estructura
            campos: Lista de tuplas (clave, etiqueta, formato)
                Ejemplo: [("TENSION", "Tensión nominal", "{} kV")]
        
        Returns:
            String formateado
        """
        lineas = []
        for clave, etiqueta, formato in campos:
            valor = estructura_actual.get(clave, 'N/A')
            if formato:
                lineas.append(f"{etiqueta}: {formato.format(valor)}")
            else:
                lineas.append(f"{etiqueta}: {valor}")
        
        return "\n".join(lineas)
