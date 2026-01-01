"""
Controlador para gestión de Familias de Estructuras
"""

from dash import callback, Input, Output, State, ctx, no_update, ALL
import dash_bootstrap_components as dbc
from dash import html
import json
from pathlib import Path
from datetime import datetime

def register_callbacks(app):
    """Registrar callbacks de familia"""
    
    # Callback para manejar modal
    @app.callback(
        [Output("modal-familia-parametro", "is_open"),
         Output("modal-familia-body-parametro", "children"),
         Output("modal-familia-celda-info", "data")],
        [Input("tabla-familia", "active_cell"),
         Input("modal-familia-confirmar", "n_clicks"),
         Input("modal-familia-cancelar", "n_clicks")],
        [State("modal-familia-parametro", "is_open"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def manejar_modal_parametro(active_cell, n_confirm, n_cancel, is_open, tabla_data):
        """Maneja apertura/cierre del modal"""
        from dash import ctx, no_update, html
        import dash_bootstrap_components as dbc
        
        print(f"DEBUG: Callback modal ejecutado - active_cell: {active_cell}")
        
        if not ctx.triggered:
            print("DEBUG: No hay trigger, retornando no_update")
            return no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        print(f"DEBUG: Trigger ID: {trigger_id}")
        
        # Abrir modal al hacer clic en celda
        if trigger_id == "tabla-familia" and active_cell:
            print(f"DEBUG: Click en tabla detectado - columna: {active_cell.get('column_id')}")
            
            if not active_cell.get("column_id", "").startswith("Estr."):
                print("DEBUG: Columna no es Estr.X, no abrir modal")
                return no_update, no_update, no_update
            
            fila = active_cell["row"]
            columna = active_cell["column_id"]
            
            if not tabla_data or fila >= len(tabla_data):
                print("DEBUG: Datos de tabla inválidos")
                return no_update, no_update, no_update
            
            parametro = tabla_data[fila]["parametro"]
            valor_actual = tabla_data[fila][columna]
            tipo = tabla_data[fila].get("tipo", "str")
            
            print(f"DEBUG: Parámetro: {parametro}, Valor: {valor_actual}, Tipo: {tipo}")
            
            # Solo abrir modal para tipos no numéricos
            if tipo in ["int", "float"]:
                print("DEBUG: Tipo numérico, no abrir modal")
                return no_update, no_update, no_update
            
            # Obtener opciones si es select
            from utils.parametros_manager import ParametrosManager
            opciones = ParametrosManager.obtener_opciones_parametro(parametro)
            print(f"DEBUG: Opciones obtenidas: {opciones}")
            
            if opciones:
                # Modal con botones para opciones
                botones = []
                for opcion in opciones:
                    color = "primary" if opcion == valor_actual else "outline-secondary"
                    botones.append(
                        dbc.Button(
                            opcion,
                            id={"type": "familia-opcion-btn", "value": opcion},
                            color=color,
                            className="me-2 mb-2",
                            size="sm"
                        )
                    )
                contenido = html.Div([
                    html.P(f"Seleccione valor para {parametro}:"),
                    html.Div(botones)
                ])
            elif tipo == "bool":
                # Modal para booleanos
                contenido = html.Div([
                    html.P(f"Seleccione valor para {parametro}:"),
                    dbc.ButtonGroup([
                        dbc.Button(
                            "Verdadero",
                            id={"type": "familia-bool-btn", "value": True},
                            color="success" if valor_actual else "outline-success"
                        ),
                        dbc.Button(
                            "Falso",
                            id={"type": "familia-bool-btn", "value": False},
                            color="danger" if not valor_actual else "outline-danger"
                        )
                    ])
                ])
            else:
                # Modal para texto
                contenido = html.Div([
                    html.P(f"Ingrese valor para {parametro}:"),
                    dbc.Input(
                        id="input-valor",
                        type="text",
                        value=valor_actual
                    )
                ])
            
            celda_info = {"fila": fila, "columna": columna, "parametro": parametro}
            print(f"DEBUG: Abriendo modal con celda_info: {celda_info}")
            return True, contenido, celda_info
        
        # Cerrar modal
        elif trigger_id in ["modal-familia-confirmar", "modal-familia-cancelar"]:
            print("DEBUG: Cerrando modal")
            return False, no_update, no_update
        
        print("DEBUG: Trigger no reconocido")
        return no_update, no_update, no_update
    
    # Callback para selección directa
    @app.callback(
        [Output("tabla-familia", "data", allow_duplicate=True),
         Output("modal-familia-parametro", "is_open", allow_duplicate=True)],
        [Input({"type": "familia-opcion-btn", "value": ALL}, "n_clicks"),
         Input({"type": "familia-bool-btn", "value": ALL}, "n_clicks")],
        [State("modal-familia-celda-info", "data"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def seleccionar_opcion_directa(n_clicks_opciones, n_clicks_bool, celda_info, tabla_data):
        """Actualiza tabla directamente al seleccionar opción y cierra modal"""
        from dash import ctx, no_update
        
        if not ctx.triggered or not celda_info:
            return no_update, no_update
        
        # Obtener el valor seleccionado
        trigger = ctx.triggered[0]
        if trigger["value"] is None:
            return no_update, no_update
        
        # Extraer valor del componente que disparó el callback
        component_id = trigger["prop_id"].split(".")[0]
        import json
        component_data = json.loads(component_id)
        valor_seleccionado = component_data["value"]
        
        # Actualizar tabla
        fila = celda_info["fila"]
        columna = celda_info["columna"]
        tabla_data[fila][columna] = valor_seleccionado
        
        # Cerrar modal y actualizar tabla
        return tabla_data, False
    
    # Callbacks para botones de control
    @app.callback(
        [Output("tabla-familia", "columns", allow_duplicate=True),
         Output("tabla-familia", "data", allow_duplicate=True)],
        Input("btn-agregar-estructura", "n_clicks"),
        [State("tabla-familia", "columns"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def agregar_estructura(n_clicks, columnas_actuales, tabla_data):
        """Agregar nueva columna de estructura"""
        if not n_clicks:
            return no_update, no_update
        
        # Encontrar próximo número de estructura
        nums_existentes = []
        for col in columnas_actuales:
            if col["id"].startswith("Estr."):
                try:
                    num = int(col["id"].split(".")[1])
                    nums_existentes.append(num)
                except:
                    continue
        
        proximo_num = max(nums_existentes) + 1 if nums_existentes else 1
        nueva_columna_id = f"Estr.{proximo_num}"
        
        # Agregar nueva columna
        nueva_columna = {
            "name": nueva_columna_id,
            "id": nueva_columna_id,
            "editable": False,
            "type": "any"
        }
        columnas_actualizadas = columnas_actuales + [nueva_columna]
        
        # Copiar valores de última columna existente
        ultima_columna = None
        for col in reversed(columnas_actuales):
            if col["id"].startswith("Estr."):
                ultima_columna = col["id"]
                break
        
        # Actualizar datos de tabla
        tabla_actualizada = []
        for fila in tabla_data:
            nueva_fila = fila.copy()
            if ultima_columna and ultima_columna in fila:
                nueva_fila[nueva_columna_id] = fila[ultima_columna]
            else:
                nueva_fila[nueva_columna_id] = fila.get("valor", "")
            tabla_actualizada.append(nueva_fila)
        
        return columnas_actualizadas, tabla_actualizada
    
    @app.callback(
        [Output("tabla-familia", "columns", allow_duplicate=True),
         Output("tabla-familia", "data", allow_duplicate=True)],
        Input("btn-eliminar-estructura", "n_clicks"),
        [State("tabla-familia", "columns"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def eliminar_estructura(n_clicks, columnas_actuales, tabla_data):
        """Eliminar última columna de estructura"""
        if not n_clicks:
            return no_update, no_update
        
        # Encontrar columnas de estructura
        cols_estructura = [col for col in columnas_actuales if col["id"].startswith("Estr.")]
        
        if len(cols_estructura) <= 1:
            # No eliminar si solo queda una estructura - mostrar advertencia
            return no_update, no_update
        
        # Encontrar última columna por número
        nums_existentes = []
        for col in cols_estructura:
            try:
                num = int(col["id"].split(".")[1])
                nums_existentes.append((num, col["id"]))
            except:
                continue
        
        if not nums_existentes:
            return no_update, no_update
        
        # Eliminar columna con mayor número
        nums_existentes.sort()
        columna_a_eliminar = nums_existentes[-1][1]
        
        # Filtrar columnas
        columnas_actualizadas = [col for col in columnas_actuales if col["id"] != columna_a_eliminar]
        
        # Actualizar datos de tabla
        tabla_actualizada = []
        for fila in tabla_data:
            nueva_fila = {k: v for k, v in fila.items() if k != columna_a_eliminar}
            tabla_actualizada.append(nueva_fila)
        
        return columnas_actualizadas, tabla_actualizada
    
    # Callback para manejar modal de texto
    @app.callback(
        [Output("tabla-familia", "data", allow_duplicate=True),
         Output("modal-familia-parametro", "is_open", allow_duplicate=True)],
        Input("modal-familia-confirmar", "n_clicks"),
        [State("input-valor", "value"),
         State("modal-familia-celda-info", "data"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def confirmar_modal_texto(n_clicks, valor_texto, celda_info, tabla_data):
        """Confirmar edición de texto en modal"""
        if not n_clicks or not celda_info or valor_texto is None:
            return no_update, no_update
        
        # Actualizar tabla
        fila = celda_info["fila"]
        columna = celda_info["columna"]
        tabla_data[fila][columna] = valor_texto
        
        return tabla_data, False
    
    # Callbacks para filtros
    @app.callback(
        [Output("tabla-familia", "data", allow_duplicate=True),
         Output("tabla-familia-original", "data")],
        [Input("filtro-categoria-familia", "value"),
         Input("buscar-parametro-familia", "value")],
        [State("tabla-familia", "data"),
         State("tabla-familia-original", "data")],
        prevent_initial_call=True
    )
    def filtrar_tabla_familia(categoria_seleccionada, texto_busqueda, tabla_data_actual, tabla_original):
        """Filtrar tabla por categoría y búsqueda"""
        # Si no hay datos originales, usar los actuales como base
        if not tabla_original:
            tabla_original = tabla_data_actual
        
        if not tabla_original:
            return no_update, no_update
        
        # Siempre filtrar desde los datos originales
        tabla_filtrada = tabla_original.copy()
        
        # Aplicar filtro de categoría
        if categoria_seleccionada and categoria_seleccionada != "todas":
            tabla_filtrada = [fila for fila in tabla_filtrada if fila.get("categoria") == categoria_seleccionada]
        
        # Aplicar filtro de búsqueda
        if texto_busqueda:
            texto_lower = texto_busqueda.lower()
            tabla_filtrada = [
                fila for fila in tabla_filtrada
                if (texto_lower in fila["parametro"].lower() or 
                    texto_lower in fila["descripcion"].lower() or
                    texto_lower in fila["simbolo"].lower())
            ]
        
        return tabla_filtrada, tabla_original
    
    # Callback para inicializar datos originales
    @app.callback(
        Output("tabla-familia-original", "data", allow_duplicate=True),
        Input("tabla-familia", "data"),
        State("tabla-familia-original", "data"),
        prevent_initial_call=True
    )
    def inicializar_datos_originales(tabla_data, tabla_original):
        """Inicializar store con datos originales la primera vez"""
        if not tabla_original and tabla_data:
            return tabla_data
        return no_update

    # Callback para Guardar Familia
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True),
         Output("familia-activa-state", "data", allow_duplicate=True)],
        Input("btn-guardar-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("tabla-familia", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def guardar_familia(n_clicks, nombre_familia, tabla_data, columnas):
        """Guardar familia en archivo JSON"""
        if not n_clicks or not nombre_familia or not tabla_data:
            return no_update, no_update, no_update, no_update, no_update
        
        try:
            # Convertir tabla a formato familia
            familia_data = tabla_a_familia(tabla_data, columnas, nombre_familia)
            
            # Guardar archivo
            from pathlib import Path
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            filename = data_dir / f"{nombre_familia.replace(' ', '_')}.familia.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(familia_data, f, indent=2, ensure_ascii=False)
            
            # Persistir estado
            guardar_familia_actual_state(familia_data)
            
            return True, "Éxito", f"Familia '{nombre_familia}' guardada en {filename.name}", "success", familia_data
            
        except Exception as e:
            return True, "Error", f"Error al guardar familia: {str(e)}", "danger", no_update
    
    # Callback para cargar opciones de familias existentes
    @app.callback(
        Output("select-familia-existente", "options"),
        Input("select-familia-existente", "id"),
        prevent_initial_call=False
    )
    def cargar_opciones_familias(_):
        """Cargar lista de familias existentes"""
        try:
            from pathlib import Path
            data_dir = Path("data")
            familias = []
            
            if data_dir.exists():
                for archivo in data_dir.glob("*.familia.json"):
                    nombre = archivo.stem.replace("_", " ")
                    familias.append({"label": nombre, "value": archivo.name})
            
            return familias
        except:
            return []
    
    # Callback para cargar familia seleccionada
    @app.callback(
        [Output("input-nombre-familia", "value"),
         Output("tabla-familia", "data", allow_duplicate=True),
         Output("tabla-familia", "columns", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True),
         Output("familia-activa-state", "data", allow_duplicate=True)],
        Input("select-familia-existente", "value"),
        prevent_initial_call=True
    )
    def cargar_familia_seleccionada(archivo_familia):
        """Cargar familia desde archivo seleccionado"""
        if not archivo_familia:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        try:
            from pathlib import Path
            archivo_path = Path("data") / archivo_familia
            
            with open(archivo_path, 'r', encoding='utf-8') as f:
                familia_data = json.load(f)
            
            # Convertir familia a formato tabla
            tabla_data, columnas = familia_a_tabla(familia_data)
            
            # Persistir estado
            guardar_familia_actual_state(familia_data)
            
            return (familia_data["nombre_familia"], tabla_data, columnas, 
                   True, "Éxito", f"Familia '{familia_data['nombre_familia']}' cargada", "success", familia_data)
            
        except Exception as e:
            return (no_update, no_update, no_update, 
                   True, "Error", f"Error al cargar familia: {str(e)}", "danger", no_update)
    
    # Callback para abrir modal eliminar familia
    @app.callback(
        [Output("modal-eliminar-familia", "is_open"),
         Output("modal-eliminar-familia-nombre", "children")],
        [Input("btn-eliminar-familia", "n_clicks"),
         Input("modal-eliminar-cancelar", "n_clicks")],
        [State("input-nombre-familia", "value"),
         State("modal-eliminar-familia", "is_open")],
        prevent_initial_call=True
    )
    def abrir_modal_eliminar(n_clicks_eliminar, n_clicks_cancelar, nombre_familia, is_open):
        """Abrir/cerrar modal de confirmación para eliminar familia"""
        if not ctx.triggered:
            return no_update, no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-eliminar-familia" and nombre_familia:
            return True, f"Familia: {nombre_familia}"
        elif trigger_id == "modal-eliminar-cancelar":
            return False, no_update
        
        return no_update, no_update
    
    # Callback para Eliminar Familia (confirmado)
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True),
         Output("input-nombre-familia", "value", allow_duplicate=True),
         Output("tabla-familia", "data", allow_duplicate=True),
         Output("tabla-familia", "columns", allow_duplicate=True),
         Output("modal-eliminar-familia", "is_open", allow_duplicate=True),
         Output("familia-activa-state", "data", allow_duplicate=True)],
        Input("modal-eliminar-confirmar", "n_clicks"),
        [State("input-nombre-familia", "value")],
        prevent_initial_call=True
    )
    def eliminar_familia_confirmado(n_clicks, nombre_familia):
        """Eliminar familia tras confirmación"""
        if not n_clicks or not nombre_familia:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        try:
            from pathlib import Path
            data_dir = Path("data")
            filename = data_dir / f"{nombre_familia.replace(' ', '_')}.familia.json"
            
            if filename.exists():
                filename.unlink()  # Eliminar archivo
                
                # Resetear vista a familia vacía
                plantilla = cargar_plantilla_estructura()
                familia_vacia = {
                    "nombre_familia": "",
                    "estructuras": {"Estr.1": plantilla}
                }
                tabla_data, columnas = familia_a_tabla(familia_vacia)
                
                # Limpiar estado de familia actual
                guardar_familia_actual_state(None)
                
                return (True, "Éxito", f"Familia '{nombre_familia}' eliminada", "success",
                       "", tabla_data, columnas, False, None)
            else:
                return (True, "Advertencia", f"Archivo de familia '{nombre_familia}' no encontrado", "warning",
                       no_update, no_update, no_update, False, no_update)
                
        except Exception as e:
            return (True, "Error", f"Error al eliminar familia: {str(e)}", "danger",
                   no_update, no_update, no_update, False, no_update)
    
    # Callback para persistir estado de familia actual
    @app.callback(
        Output("familia-activa-state", "data", allow_duplicate=True),
        [Input("btn-guardar-familia", "n_clicks"),
         Input("select-familia-existente", "value")],
        [State("input-nombre-familia", "value"),
         State("tabla-familia", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def actualizar_familia_actual_state(n_guardar, familia_seleccionada, nombre_familia, tabla_data, columnas):
        """Actualizar estado de familia actual"""
        if not ctx.triggered:
            return no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-guardar-familia" and nombre_familia and tabla_data:
            # Guardar estado tras guardar familia
            familia_data = tabla_a_familia(tabla_data, columnas, nombre_familia)
            guardar_familia_actual_state(familia_data)
            return familia_data
        elif trigger_id == "select-familia-existente" and familia_seleccionada:
            # Cargar estado de familia seleccionada
            try:
                from pathlib import Path
                archivo_path = Path("data") / familia_seleccionada
                with open(archivo_path, 'r', encoding='utf-8') as f:
                    familia_data = json.load(f)
                guardar_familia_actual_state(familia_data)
                return familia_data
            except:
                return no_update
        
        return no_update
    
    # Callback para modal cargar columna
    @app.callback(
        [Output("modal-cargar-columna", "is_open"),
         Output("select-estructura-cargar-columna", "options"),
         Output("select-columna-destino", "options")],
        [Input("btn-cargar-columna", "n_clicks"),
         Input("modal-cargar-columna-cancelar", "n_clicks")],
        [State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def abrir_modal_cargar_columna(n_clicks_abrir, n_clicks_cancelar, columnas):
        """Abrir/cerrar modal cargar columna"""
        if not ctx.triggered:
            return no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-cargar-columna":
            # Cargar estructuras disponibles
            try:
                from pathlib import Path
                data_dir = Path("data")
                estructuras = []
                
                if data_dir.exists():
                    for archivo in data_dir.glob("*.estructura.json"):
                        if archivo.name != "plantilla.estructura.json":
                            try:
                                with open(archivo, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    titulo = data.get("TITULO", archivo.stem)
                                    estructuras.append({"label": titulo, "value": archivo.name})
                            except:
                                continue
                
                # Cargar columnas disponibles
                cols_estructura = [{"label": col["name"], "value": col["id"]} 
                                 for col in columnas if col["id"].startswith("Estr.")]
                
                return True, estructuras, cols_estructura
            except:
                return True, [], []
        
        elif trigger_id == "modal-cargar-columna-cancelar":
            return False, no_update, no_update
        
        return no_update, no_update, no_update
    
    # Callback para cargar estructura en columna
    @app.callback(
        [Output("tabla-familia", "data", allow_duplicate=True),
         Output("modal-cargar-columna", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("modal-cargar-columna-confirmar", "n_clicks"),
        [State("select-estructura-cargar-columna", "value"),
         State("select-columna-destino", "value"),
         State("tabla-familia", "data")],
        prevent_initial_call=True
    )
    def cargar_estructura_en_columna(n_clicks, archivo_estructura, columna_destino, tabla_data):
        """Cargar estructura existente en columna seleccionada"""
        if not n_clicks or not archivo_estructura or not columna_destino:
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        try:
            from pathlib import Path
            archivo_path = Path("data") / archivo_estructura
            
            with open(archivo_path, 'r', encoding='utf-8') as f:
                estructura_data = json.load(f)
            
            # Actualizar tabla con datos de estructura
            tabla_actualizada = []
            for fila in tabla_data:
                nueva_fila = fila.copy()
                parametro = fila["parametro"]
                
                if parametro in estructura_data:
                    nueva_fila[columna_destino] = estructura_data[parametro]
                elif parametro == "cantidad":
                    nueva_fila[columna_destino] = 1  # Valor por defecto
                
                tabla_actualizada.append(nueva_fila)
            
            titulo_estructura = estructura_data.get("TITULO", "Estructura")
            
            return (tabla_actualizada, False, 
                   True, "Éxito", f"Estructura '{titulo_estructura}' cargada en {columna_destino}", "success")
            
        except Exception as e:
            return (no_update, False,
                   True, "Error", f"Error al cargar estructura: {str(e)}", "danger")
    @app.callback(
        [Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True),
         Output("input-nombre-familia", "value", allow_duplicate=True)],
        Input("btn-guardar-como-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("tabla-familia", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def guardar_como_familia(n_clicks, nombre_actual, tabla_data, columnas):
        """Guardar familia con nuevo nombre"""
        if not n_clicks or not nombre_actual or not tabla_data:
            return no_update, no_update, no_update, no_update, no_update
        
        # Generar nuevo nombre
        nuevo_nombre = f"{nombre_actual}_copia"
        
        try:
            # Convertir tabla a formato familia
            familia_data = tabla_a_familia(tabla_data, columnas, nuevo_nombre)
            
            # Guardar archivo
            from pathlib import Path
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            filename = data_dir / f"{nuevo_nombre.replace(' ', '_')}.familia.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(familia_data, f, indent=2, ensure_ascii=False)
            
            return (True, "Éxito", f"Familia guardada como '{nuevo_nombre}'", "success", nuevo_nombre)
            
        except Exception as e:
            return (True, "Error", f"Error al guardar como: {str(e)}", "danger", no_update)
    
    # Callback para Calcular Familia
    @app.callback(
        [Output("resultados-familia", "children"),
         Output("toast-notificacion", "is_open", allow_duplicate=True),
         Output("toast-notificacion", "header", allow_duplicate=True),
         Output("toast-notificacion", "children", allow_duplicate=True),
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-calcular-familia", "n_clicks"),
        [State("tabla-familia", "data"),
         State("tabla-familia", "columns"),
         State("input-nombre-familia", "value")],
        prevent_initial_call=True
    )
    def calcular_familia(n_clicks, tabla_data, columnas, nombre_familia):
        """Ejecutar cálculos para toda la familia"""
        if not n_clicks or not tabla_data or not nombre_familia:
            return no_update, no_update, no_update, no_update, no_update
        
        print(f"🚀 INICIANDO CÁLCULO FAMILIA: {nombre_familia}")
        
        try:
            # Convertir tabla a formato familia
            familia_data = tabla_a_familia(tabla_data, columnas, nombre_familia)
            estructuras = familia_data.get("estructuras", {})
            
            if not estructuras:
                return (no_update, True, "Error", "No hay estructuras para calcular", "danger")
            
            # Ejecutar cálculos para cada estructura
            resultados_familia = {}
            
            for nombre_estr, datos_estr in estructuras.items():
                print(f"🔧 Calculando {nombre_estr}: {datos_estr.get('TITULO', 'Sin título')}")
                
                # Ejecutar secuencia completa para esta estructura
                resultado_estructura = ejecutar_calculo_estructura_familia(datos_estr)
                resultados_familia[nombre_estr] = resultado_estructura
            
            # Crear vista con pestañas
            vista_resultados = crear_vista_resultados_familia(resultados_familia, estructuras)
            
            print(f"✅ CÁLCULO FAMILIA COMPLETADO: {len(resultados_familia)} estructuras")
            return (vista_resultados, True, "Éxito", f"Familia '{nombre_familia}' calculada exitosamente", "success")
            
        except Exception as e:
            import traceback
            error_msg = f"Error calculando familia: {str(e)}"
            print(f"❌ ERROR CÁLCULO FAMILIA: {traceback.format_exc()}")
            return (no_update, True, "Error", error_msg, "danger")

def guardar_familia_activa_state(familia_data):
    """Guardar estado de familia activa en memoria (no archivo)"""
    # Solo mantener en memoria, no persistir en archivo
    pass

def cargar_familia_activa_state():
    """Cargar estado de familia activa desde memoria"""
    # No cargar desde archivo, trabajar solo con estado en memoria
    return None

def cargar_plantilla_estructura():
    """Cargar plantilla de estructura"""
    try:
        with open("data/plantilla.estructura.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def tabla_a_familia(tabla_data, columnas, nombre_familia):
    """Convertir datos de tabla a formato familia"""
    from datetime import datetime
    
    # Obtener columnas de estructura
    cols_estructura = [col["id"] for col in columnas if col["id"].startswith("Estr.")]
    
    # Crear estructura familia
    familia = {
        "nombre_familia": nombre_familia,
        "fecha_creacion": datetime.now().isoformat(),
        "fecha_modificacion": datetime.now().isoformat(),
        "estructuras": {}
    }
    
    # Procesar cada estructura
    for col_estr in cols_estructura:
        estructura = {}
        
        # Extraer valores de cada parámetro
        for fila in tabla_data:
            parametro = fila["parametro"]
            valor = fila.get(col_estr, "")
            estructura[parametro] = valor
        
        familia["estructuras"][col_estr] = estructura
    
    return familia

def familia_a_tabla(familia_data):
    """Convertir formato familia a datos de tabla"""
    estructuras = familia_data.get("estructuras", {})
    
    # Configurar columnas
    columnas = [
        {"name": "Categoría", "id": "categoria", "editable": False, "type": "text"},
        {"name": "Parámetro", "id": "parametro", "editable": False, "type": "text"},
        {"name": "Símbolo", "id": "simbolo", "editable": False, "type": "text"},
        {"name": "Unidad", "id": "unidad", "editable": False, "type": "text"},
        {"name": "Descripción", "id": "descripcion", "editable": False, "type": "text"}
    ]
    
    # Agregar columnas de estructuras
    for nombre_estr in sorted(estructuras.keys()):
        columnas.append({
            "name": nombre_estr,
            "id": nombre_estr,
            "editable": True,
            "type": "any"
        })
    
    # Generar datos de tabla usando ParametrosManager
    from utils.parametros_manager import ParametrosManager
    plantilla = cargar_plantilla_estructura()
    tabla_base = ParametrosManager.estructura_a_tabla(plantilla)
    
    # Agregar filas especiales (TITULO y cantidad)
    tabla_data = []
    
    # Fila TITULO
    fila_titulo = {
        "categoria": "General",
        "parametro": "TITULO",
        "simbolo": "TÍTULO",
        "unidad": "-",
        "descripcion": "Título de la estructura",
        "tipo": "str"
    }
    for nombre_estr, datos_estr in estructuras.items():
        fila_titulo[nombre_estr] = datos_estr.get("TITULO", "")
    tabla_data.append(fila_titulo)
    
    # Fila cantidad
    fila_cantidad = {
        "categoria": "General",
        "parametro": "cantidad",
        "simbolo": "CANT",
        "unidad": "unidades",
        "descripcion": "Cantidad de estructuras",
        "tipo": "int"
    }
    for nombre_estr, datos_estr in estructuras.items():
        fila_cantidad[nombre_estr] = datos_estr.get("cantidad", 1)
    tabla_data.append(fila_cantidad)
    
    # Resto de parámetros
    for fila_base in tabla_base:
        parametro = fila_base["parametro"]
        fila = {
            "categoria": fila_base["categoria"],
            "parametro": parametro,
            "simbolo": fila_base["simbolo"],
            "unidad": fila_base["unidad"],
            "descripcion": fila_base["descripcion"],
            "tipo": fila_base["tipo"]
        }
        
        for nombre_estr, datos_estr in estructuras.items():
            fila[nombre_estr] = datos_estr.get(parametro, fila_base["valor"])
        
        tabla_data.append(fila)
    
    return tabla_data, columnas

def ejecutar_calculo_estructura_familia(estructura_data):
    """Ejecutar cálculos para una estructura de familia"""
    from models.app_state import AppState
    from dash import html
    import dash_bootstrap_components as dbc
    
    titulo = estructura_data.get('TITULO', 'estructura')
    print(f"🔧 Ejecutando cálculos para: {titulo}")
    
    # Crear AppState EXACTAMENTE como en calcular_todo_controller.py
    state = AppState()
    
    try:
        # USAR DIRECTAMENTE los datos de estructura_data, NO cargar desde archivo
        estructura_actual = estructura_data.copy()
        print(f"📂 Usando datos de familia: {estructura_actual.get('TITULO', 'N/A')}")
        
        # COPIAR EXACTAMENTE el código de calcular_todo_controller.py
        resultados = {}
        
        # 1. CMC - CÓDIGO EXACTO de calcular_todo_controller.py
        from controllers.geometria_controller import ejecutar_calculo_cmc_automatico
        from utils.calculo_cache import CalculoCache
        
        state.cargado_desde_cache = False
        
        print("🔧 Ejecutando CMC...")
        # CREAR archivo temporal para que el sistema funcione
        import tempfile
        import json
        from pathlib import Path
        
        # Crear archivo temporal con los datos de la estructura
        with tempfile.NamedTemporaryFile(mode='w', suffix='.estructura.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(estructura_actual, temp_file, indent=2, ensure_ascii=False)
            temp_path = Path(temp_file.name)
        
        # Establecer la ruta temporal en el state
        state.set_estructura_actual(estructura_actual)
        state._estructura_actual_path = temp_path
        
        resultado_cmc = ejecutar_calculo_cmc_automatico(estructura_actual, state)
        if resultado_cmc.get('exito'):
            print("✅ CMC exitoso, cargando desde cache...")
            calculo_cmc = CalculoCache.cargar_calculo_cmc(estructura_actual.get('TITULO', 'estructura'))
            if calculo_cmc:
                resultados['cmc'] = {'exito': True, 'cache': calculo_cmc}
                print(f"✅ CMC: Cache cargado")
            else:
                print("❌ CMC: No se pudo cargar desde cache")
                resultados['cmc'] = {'exito': False, 'mensaje': 'No se pudo cargar cache CMC'}
        else:
            print(f"❌ CMC falló: {resultado_cmc.get('mensaje')}")
            resultados['cmc'] = {'exito': False, 'mensaje': resultado_cmc.get('mensaje')}
        
        # 2. DGE - CÓDIGO EXACTO de calcular_todo_controller.py
        from controllers.geometria_controller import ejecutar_calculo_dge
        
        print("🔧 Ejecutando DGE...")
        resultado_dge = ejecutar_calculo_dge(estructura_actual, state)
        if resultado_dge.get('exito'):
            print("✅ DGE exitoso, cargando desde cache...")
            calculo_dge = CalculoCache.cargar_calculo_dge(estructura_actual.get('TITULO', 'estructura'))
            if calculo_dge:
                resultados['dge'] = {'exito': True, 'cache': calculo_dge}
                print(f"✅ DGE: Cache cargado")
            else:
                print("❌ DGE: No se pudo cargar desde cache")
                resultados['dge'] = {'exito': False, 'mensaje': 'No se pudo cargar cache DGE'}
        else:
            print(f"❌ DGE falló: {resultado_dge.get('mensaje')}")
            resultados['dge'] = {'exito': False, 'mensaje': resultado_dge.get('mensaje')}
        
        # 3. DME - CÓDIGO EXACTO de calcular_todo_controller.py
        from controllers.ejecutar_calculos import ejecutar_calculo_dme
        
        print("🔧 Ejecutando DME...")
        resultado_dme = ejecutar_calculo_dme(estructura_actual, state)
        if resultado_dme.get('exito'):
            print("✅ DME exitoso, cargando desde cache...")
            calculo_dme = CalculoCache.cargar_calculo_dme(estructura_actual.get('TITULO', 'estructura'))
            if calculo_dme:
                resultados['dme'] = {'exito': True, 'cache': calculo_dme}
                print(f"✅ DME: Cache cargado")
            else:
                print("❌ DME: No se pudo cargar desde cache")
                resultados['dme'] = {'exito': False, 'mensaje': 'No se pudo cargar cache DME'}
        else:
            print(f"❌ DME falló: {resultado_dme.get('mensaje')}")
            resultados['dme'] = {'exito': False, 'mensaje': resultado_dme.get('mensaje')}
        
        # 4. Árboles - CÓDIGO EXACTO de calcular_todo_controller.py
        from controllers.ejecutar_calculos import ejecutar_calculo_arboles
        
        print("🔧 Ejecutando Árboles...")
        resultado_arboles = ejecutar_calculo_arboles(estructura_actual, state)
        if resultado_arboles.get('exito'):
            print("✅ Árboles exitoso, cargando desde cache...")
            calculo_arboles = CalculoCache.cargar_calculo_arboles(estructura_actual.get('TITULO', 'estructura'))
            if calculo_arboles:
                resultados['arboles'] = {'exito': True, 'cache': calculo_arboles}
                print(f"✅ Árboles: Cache cargado")
            else:
                print("❌ Árboles: No se pudo cargar desde cache")
                resultados['arboles'] = {'exito': False, 'mensaje': 'No se pudo cargar cache Árboles'}
        else:
            print(f"❌ Árboles falló: {resultado_arboles.get('mensaje')}")
            resultados['arboles'] = {'exito': False, 'mensaje': resultado_arboles.get('mensaje')}
        
        # 5. SPH - CÓDIGO EXACTO de calcular_todo_controller.py
        from controllers.ejecutar_calculos import ejecutar_calculo_sph
        
        print("🔧 Ejecutando SPH...")
        resultado_sph = ejecutar_calculo_sph(estructura_actual, state)
        if resultado_sph.get('exito'):
            print("✅ SPH exitoso, cargando desde cache...")
            calculo_sph = CalculoCache.cargar_calculo_sph(estructura_actual.get('TITULO', 'estructura'))
            if calculo_sph:
                resultados['sph'] = {'exito': True, 'cache': calculo_sph}
                print(f"✅ SPH: Cache cargado")
            else:
                print("❌ SPH: No se pudo cargar desde cache")
                resultados['sph'] = {'exito': False, 'mensaje': 'No se pudo cargar cache SPH'}
        else:
            print(f"❌ SPH falló: {resultado_sph.get('mensaje')}")
            resultados['sph'] = {'exito': False, 'mensaje': resultado_sph.get('mensaje')}
        
        print(f"✅ Cálculos completados para {titulo}")
        
        # Limpiar archivo temporal
        try:
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
        except:
            pass
        
        return resultados
        
    except Exception as e:
        print(f"❌ Error en cálculos para {titulo}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Limpiar archivo temporal en caso de error
        try:
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
        except:
            pass
        
        return {'error': str(e)}

def crear_vista_resultados_familia(resultados_familia, estructuras):
    """Crear vista con pestañas para resultados de familia"""
    from dash import html, dcc
    import dash_bootstrap_components as dbc
    
    if not resultados_familia:
        return html.Div([html.P("No hay resultados para mostrar")])
    
    # Crear pestañas
    tabs = []
    tab_contents = []
    first_tab = True
    
    for nombre_estr, resultados in resultados_familia.items():
        titulo_estructura = estructuras[nombre_estr].get('TITULO', nombre_estr)
        
        # Crear pestaña
        tabs.append(
            dbc.Tab(
                label=titulo_estructura,
                tab_id=f"tab-{nombre_estr}",
                active_tab_style={"textTransform": "none"}
            )
        )
        
        # Crear contenido de pestaña
        contenido_estructura = crear_contenido_estructura(resultados, estructuras[nombre_estr])
        tab_contents.append(
            html.Div(
                contenido_estructura,
                id=f"content-{nombre_estr}",
                style={"display": "block" if first_tab else "none"}
            )
        )
        first_tab = False
    
    return html.Div([
        html.H4("Resultados de Familia", className="mb-3"),
        dbc.Tabs(
            tabs,
            id="tabs-familia",
            active_tab=f"tab-{list(resultados_familia.keys())[0]}" if resultados_familia else None
        ),
        html.Div(tab_contents, id="tab-content-familia", className="mt-3")
    ])

def crear_contenido_estructura(resultados, estructura_data):
    """Crear contenido para una estructura individual usando EXACTAMENTE las mismas funciones que Calcular Todo"""
    from dash import html
    import dash_bootstrap_components as dbc
    
    contenido = []
    titulo = estructura_data.get('TITULO', 'Estructura')
    
    contenido.append(html.H5(f"Resultados para: {titulo}", className="mb-3"))
    
    # Verificar si hay error
    if 'error' in resultados:
        contenido.append(dbc.Alert(f"Error en cálculos: {resultados['error']}", color="danger"))
        return contenido
    
    # CMC - EXACTAMENTE como en calcular_todo_controller.py
    if resultados.get('cmc', {}).get('exito'):
        contenido.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
        calculo_cmc = resultados['cmc'].get('cache')
        if calculo_cmc:
            try:
                from components.vista_calcular_todo import generar_resultados_cmc_lista
                lista_cmc = generar_resultados_cmc_lista(calculo_cmc, estructura_data, mostrar_alerta_cache=False)
                contenido.extend(lista_cmc)
            except Exception as e:
                contenido.append(dbc.Alert(f"Error cargando CMC: {str(e)}", color="warning"))
    else:
        mensaje_cmc = resultados.get('cmc', {}).get('mensaje', 'CMC no ejecutado exitosamente')
        contenido.append(html.H3("1. CÁLCULO MECÁNICO DE CABLES (CMC)", className="mt-4"))
        contenido.append(dbc.Alert(f"Error CMC: {mensaje_cmc}", color="danger"))
    
    # DGE - EXACTAMENTE como en calcular_todo_controller.py
    if resultados.get('dge', {}).get('exito'):
        contenido.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
        calculo_dge = resultados['dge'].get('cache')
        if calculo_dge:
            try:
                from components.vista_diseno_geometrico import generar_resultados_dge
                lista_dge = generar_resultados_dge(calculo_dge, estructura_data, mostrar_alerta_cache=False)
                if isinstance(lista_dge, list):
                    contenido.extend(lista_dge)
                else:
                    contenido.append(lista_dge)
            except Exception as e:
                contenido.append(dbc.Alert(f"Error cargando DGE: {str(e)}", color="warning"))
    else:
        mensaje_dge = resultados.get('dge', {}).get('mensaje', 'DGE no ejecutado exitosamente')
        contenido.append(html.H3("2. DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)", className="mt-4"))
        contenido.append(dbc.Alert(f"Error DGE: {mensaje_dge}", color="danger"))
    
    # DME - EXACTAMENTE como en calcular_todo_controller.py
    if resultados.get('dme', {}).get('exito'):
        contenido.append(html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"))
        calculo_dme = resultados['dme'].get('cache')
        if calculo_dme:
            try:
                from components.vista_diseno_mecanico import generar_resultados_dme
                contenido.append(generar_resultados_dme(calculo_dme, estructura_data, mostrar_alerta_cache=False))
            except Exception as e:
                contenido.append(dbc.Alert(f"Error cargando DME: {str(e)}", color="warning"))
    else:
        mensaje_dme = resultados.get('dme', {}).get('mensaje', 'DME no ejecutado exitosamente')
        contenido.append(html.H3("3. DISEÑO MECÁNICO DE ESTRUCTURA (DME)", className="mt-4"))
        contenido.append(dbc.Alert(f"Error DME: {mensaje_dme}", color="danger"))
    
    # Árboles - EXACTAMENTE como en calcular_todo_controller.py
    if resultados.get('arboles', {}).get('exito'):
        contenido.append(html.H3("4. ÁRBOLES DE CARGA", className="mt-4"))
        calculo_arboles = resultados['arboles'].get('cache')
        if calculo_arboles:
            try:
                from components.vista_arboles_carga import generar_resultados_arboles
                contenido.append(html.Div(generar_resultados_arboles(calculo_arboles, estructura_data, mostrar_alerta_cache=False)))
            except Exception as e:
                contenido.append(dbc.Alert(f"Error cargando Árboles: {str(e)}", color="warning"))
    else:
        mensaje_arboles = resultados.get('arboles', {}).get('mensaje', 'Árboles no ejecutado exitosamente')
        contenido.append(html.H3("4. ÁRBOLES DE CARGA", className="mt-4"))
        contenido.append(dbc.Alert(f"Error Árboles: {mensaje_arboles}", color="danger"))
    
    # SPH - EXACTAMENTE como en calcular_todo_controller.py
    if resultados.get('sph', {}).get('exito'):
        contenido.append(html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"))
        calculo_sph = resultados['sph'].get('cache')
        if calculo_sph:
            try:
                from components.vista_seleccion_poste import _crear_area_resultados
                resultado_sph = _crear_area_resultados(calculo_sph, estructura_data)
                if isinstance(resultado_sph, list):
                    contenido.extend(resultado_sph)
                else:
                    contenido.append(resultado_sph)
            except Exception as e:
                contenido.append(dbc.Alert(f"Error cargando SPH: {str(e)}", color="warning"))
    else:
        mensaje_sph = resultados.get('sph', {}).get('mensaje', 'SPH no ejecutado exitosamente')
        contenido.append(html.H3("5. SELECCIÓN DE POSTE DE HORMIGÓN (SPH)", className="mt-4"))
        contenido.append(dbc.Alert(f"Error SPH: {mensaje_sph}", color="danger"))
    
    return contenido

# Callback para manejar pestañas de resultados
@callback(
    Output("tab-content-familia", "children", allow_duplicate=True),
    Input("tabs-familia", "active_tab"),
    State("tab-content-familia", "children"),
    prevent_initial_call=True
)
def mostrar_contenido_tab(active_tab, current_content):
    """Mostrar contenido de pestaña activa"""
    if not active_tab or not current_content:
        return no_update
    
    # Crear nueva lista con estilos actualizados
    updated_content = []
    tab_id = active_tab.replace("tab-", "content-")
    
    for content in current_content:
        if hasattr(content, 'id') and content.id == tab_id:
            # Mostrar contenido activo - crear nuevo componente con estilo
            from dash import html
            new_content = html.Div(
                content.children if hasattr(content, 'children') else content,
                id=content.id if hasattr(content, 'id') else None,
                style={"display": "block"}
            )
        else:
            # Ocultar otros contenidos - crear nuevo componente con estilo
            from dash import html
            new_content = html.Div(
                content.children if hasattr(content, 'children') else content,
                id=content.id if hasattr(content, 'id') else None,
                style={"display": "none"}
            )
        updated_content.append(new_content)
    
    return updated_content

# Callback único para navegación
@callback(
    Output("contenido-principal", "children", allow_duplicate=True),
    [Input("menu-familia-estructuras", "n_clicks")],
    prevent_initial_call=True
)
def mostrar_vista_familia(n_clicks):
    """Mostrar vista de familia de estructuras"""
    if not n_clicks:
        return no_update
    
    try:
        from components.vista_familia_estructuras import crear_vista_familia_estructuras
        # Cargar familia activa desde estado en memoria
        familia_activa = None  # Solo trabajar con datos en memoria
        vista = crear_vista_familia_estructuras(familia_activa)
        return vista
    except Exception as e:
        return html.Div([
            dbc.Alert(f"Error al cargar vista familia: {str(e)}", color="danger")
        ])
