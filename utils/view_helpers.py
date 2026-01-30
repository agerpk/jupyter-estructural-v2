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
        print(f"Buscando imagen en cache: {img_path}")
        if img_path.exists():
            try:
                with open(img_path, 'rb') as f:
                    print(f"✅ Imagen cargada desde cache: {nombre_archivo}")
                    return base64.b64encode(f.read()).decode()
            except Exception as e:
                print(f"❌ Error cargando imagen desde cache: {e}")
                # seguir a búsqueda en repo root
        else:
            print(f"🔎 No encontrada en cache: {img_path}")

        # Intentar buscar en carpeta raíz del proyecto (persistente aunque se borre cache)
        repo_root = Path(__file__).resolve().parents[1]
        candidate = repo_root / nombre_archivo
        print(f"Buscando imagen en repo root: {candidate}")
        if candidate.exists():
            try:
                with open(candidate, 'rb') as f:
                    print(f"✅ Imagen cargada desde repo root: {candidate.name}")
                    return base64.b64encode(f.read()).decode()
            except Exception as e:
                print(f"❌ Error cargando imagen desde repo root: {e}")

        # Búsqueda más tolerante (case-insensitive / tokens) en repo root
        lower_target = nombre_archivo.lower()
        for p in repo_root.iterdir():
            try:
                if p.is_file() and p.suffix.lower() in ('.png', '.jpg', '.jpeg'):
                    if p.name.lower() == lower_target or ('logo' in p.name.lower() and 'distrocuyo' in p.name.lower()):
                        try:
                            with open(p, 'rb') as f:
                                print(f"✅ Imagen encontrada por heurística en repo root: {p.name}")
                                return base64.b64encode(f.read()).decode()
                        except Exception as e:
                            print(f"❌ Error cargando imagen heurística: {e}")
            except Exception:
                continue

        print(f"❌ Imagen no encontrada en cache ni en repo root: {nombre_archivo}")
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
        """Crea tabla HTML en iframe con altura dinámica. Si el DataFrame tiene MultiIndex
        en columnas (Hipótesis / Componente x,y,z) se genera una cabecera adicional con
        los códigos de hipótesis (A0, A1, ...).
        
        Args:
            df: DataFrame de pandas
            altura_fila: Altura estimada por fila en pixels
            altura_min: Altura mínima del iframe
            altura_max: Altura máxima del iframe
            
        Returns:
            html.Iframe component
        """
        # Estilos comunes
        style_head = '''<html><head><style>
            body {{ margin: 0; padding: 10px; background: white; font-family: Arial, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; font-size: 13px; background: white !important; }}
            /* Forzar fondo y color aunque haya tema oscuro */
            th, td {{ border: 1px solid #cfcfcf; padding: 8px 10px; text-align: right; background: white !important; color: #000 !important; vertical-align: middle; font-size: 13px; opacity: 1 !important; filter: none !important; -webkit-text-fill-color: #000 !important; text-shadow: none !important; }}
            thead th {{ background: white !important; color: #000 !important; font-weight: 700 !important; }}
            tbody td, tbody tr {{ background: white !important; color: #000 !important; opacity: 1 !important; filter: none !important; }}
            /* Anular cualquier regla de alternado */
            tr:nth-child(even) {{ background-color: white !important; }}
            tr:hover {{ background-color: #f6f7f8 !important; }}
            /* Selección más clara y legible */
            ::selection {{ background: #d9edf7 !important; color: #000 !important; }}
            ::-moz-selection {{ background: #d9edf7 !important; color: #000 !important; }}
        </style></head>'''
        
        df_display = df.copy()
        try:
            df_display = df_display.round(2)
        except Exception:
            pass
        
        # Si tiene MultiIndex en columnas y tiene al menos 3 columnas por hipótesis, construir cabecera personalizada
        if hasattr(df_display.columns, 'levels') and len(df_display.columns) > 2:
            cols = list(df_display.columns)
            # Agrupar columnas por etiqueta del primer nivel para evitar desfaces entre código y sus subcolumnas
            left_n = 2  # asumimos primeras 2 columnas: Nodo y Unidad
            groups = []
            current_label = None
            current_group = []
            for col in cols[left_n:]:
                label = col[0] if isinstance(col, tuple) else col
                if current_label is None:
                    current_label = label
                    current_group = [col]
                elif label == current_label:
                    current_group.append(col)
                else:
                    groups.append((current_label, current_group))
                    current_label = label
                    current_group = [col]
            if current_group:
                groups.append((current_label, current_group))

            # Primera fila: Nodo/Unidad (rowspan=2) + códigos por grupo (colspan=len(grp))
            top_row = '<tr style="background:#ffffff; font-weight:700; text-align:center; color:#000">'
            top_row += '<th rowspan="2" style="text-align:left; vertical-align:middle; padding:6px 8px; color:#000">Nodo</th>'
            top_row += '<th rowspan="2" style="text-align:left; vertical-align:middle; padding:6px 8px; color:#000">Unidad</th>'
            for label, grp in groups:
                try:
                    lstr = str(label)
                    if 'HIP_' in lstr or '_' in lstr:
                        code = lstr.split('_')[-2]
                    else:
                        code = lstr
                except Exception:
                    code = str(label)
                top_row += f'<th colspan="{len(grp)}" style="text-align:center; color:#000; padding:6px 8px">{code}</th>'
            top_row += '</tr>'

            # Segunda fila: subcolumnas (x,y,z,...)
            second_row = '<tr style="font-weight:600; text-align:center; color:#000">'
            for label, grp in groups:
                for col in grp:
                    sub = col[1] if isinstance(col, tuple) and len(col) > 1 else ''
                    second_row += f'<th style="color:#000">{sub}</th>'
            second_row += '</tr>'

            # Cuerpo: iterar por columnas en orden para evitar desfaces
            body_rows = []
            for _, row in df_display.iterrows():
                r = '<tr>'
                r += f'<td style="text-align:left">{row.iloc[0]}</td>'
                r += f'<td style="text-align:left">{row.iloc[1]}</td>'
                for col in cols[left_n:]:
                    v = row[col] if col in row.index else ''
                    r += f'<td>{v}</td>'
                r += '</tr>'
                body_rows.append(r)
            body_html = '\n'.join(body_rows)
            table_html = f'<body><table>\n{top_row}\n{second_row}\n{body_html}\n</table></body>'
            html_table = style_head + table_html
        else:
            # Fallback: usar el método simple de pandas y añadir inline-style a la tabla para evitar que estilos externos la afecten
            pandas_html = df_display.to_html(border=0, index=False)
            # Inserta inline styles en la etiqueta <table>
            if '<table' in pandas_html:
                pandas_html = pandas_html.replace('<table', '<table style="background:white; color:#000"', 1)
            html_table = style_head + f'<body>{pandas_html}</body>'
        
        altura_tabla = min(max(len(df_display) * altura_fila + 80, altura_min), altura_max)
        
        return html.Iframe(
            srcDoc=html_table,
            style={
                'width': '100%',
                'height': f'{altura_tabla}px',
                'border': '1px solid #dee2e6',
                'borderRadius': '4px'
            }
        )

    @staticmethod
    def crear_datatable(df, altura=None, table_id=None):
        """Crea un componente Dash DataTable a partir de un DataFrame.
        Soporta MultiIndex en columnas (los nombres se usan como cabeceras multilínea).
        """
        from dash import dash_table, html
        import pandas as pd

        df2 = df.copy()
        columns = []

        if isinstance(df2.columns, pd.MultiIndex):
            # crear columnas con ids únicos y nombres multilínea
            for col in df2.columns:
                lvl0 = str(col[0])
                lvl1 = str(col[1]) if len(col) > 1 else ''
                col_id = f"{lvl0}__{lvl1}" if lvl1 else lvl0
                # mover la columna a nuevo id
                df2[col_id] = df2[col]
                columns.append({'name': [lvl0, lvl1], 'id': col_id})
            # eliminar columnas originales para evitar duplicados
            # (las nuevas columnas ya contienen los valores)
            # Asegurarse de mantener orden
            cols_order = [c['id'] for c in columns]
            # Prepend index columns si existen (ej. Nodo, Unidad)
            # Detectar si las primeras columnas no pertenecen a hipotesis
            # Si las primeras columnas no tienen formato tuple, las dejamos como están
            # Para simplicidad asumimos que df ya contiene Nodo y Unidad como primeras dos columnas
            data = df2[cols_order].to_dict('records')
        else:
            for col in df2.columns:
                columns.append({'name': str(col), 'id': str(col)})
            data = df2.to_dict('records')

        # DataTable con estilos forzados para fondo blanco y texto negro
        dt = dash_table.DataTable(
            id=table_id or 'datatable-cargas-aplicadas',
            columns=columns,
            data=data,
            fixed_rows={'headers': True},
            page_action='none',
            style_table={'overflowX': 'auto', 'maxHeight': f'{altura}px' if altura else '400px'},
            style_cell={'textAlign': 'right', 'backgroundColor': 'white', 'color': '#000', 'whiteSpace': 'nowrap', 'padding': '6px 8px', 'fontSize': '13px'},
            style_header={'backgroundColor': 'white', 'fontWeight': '700', 'color': '#000', 'textAlign': 'center'},
            style_cell_conditional=[
                {'if': {'column_id': c['id']}, 'textAlign': 'right'} for c in columns
            ],
            style_as_list_view=True,
            tooltip_header={},
            virtualization=False
        )

        return html.Div(dt, style={'border': '1px solid #dee2e6', 'padding': '6px', 'borderRadius': '4px', 'background': 'white'})

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
