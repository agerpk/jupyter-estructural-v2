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
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("btn-guardar-familia", "n_clicks"),
        [State("input-nombre-familia", "value"),
         State("tabla-familia", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def guardar_familia(n_clicks, nombre_familia, tabla_data, columnas):
        """Guardar familia en archivo JSON"""
        if not n_clicks or not nombre_familia or not tabla_data:
            return no_update, no_update, no_update, no_update
        
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
            
            return True, "Éxito", f"Familia '{nombre_familia}' guardada en {filename.name}", "success"
            
        except Exception as e:
            return True, "Error", f"Error al guardar familia: {str(e)}", "danger"
    
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
         Output("toast-notificacion", "color", allow_duplicate=True)],
        Input("select-familia-existente", "value"),
        prevent_initial_call=True
    )
    def cargar_familia_seleccionada(archivo_familia):
        """Cargar familia desde archivo seleccionado"""
        if not archivo_familia:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        try:
            from pathlib import Path
            archivo_path = Path("data") / archivo_familia
            
            with open(archivo_path, 'r', encoding='utf-8') as f:
                familia_data = json.load(f)
            
            # Convertir familia a formato tabla
            tabla_data, columnas = familia_a_tabla(familia_data)
            
            return (familia_data["nombre_familia"], tabla_data, columnas, 
                   True, "Éxito", f"Familia '{familia_data['nombre_familia']}' cargada", "success")
            
        except Exception as e:
            return (no_update, no_update, no_update, 
                   True, "Error", f"Error al cargar familia: {str(e)}", "danger")
    
    # Callback para Guardar Como
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
        familia_actual = None  # Por ahora usar valores por defecto
        vista = crear_vista_familia_estructuras(familia_actual)
        return vista
    except Exception as e:
        return html.Div([
            dbc.Alert(f"Error al cargar vista familia: {str(e)}", color="danger")
        ])