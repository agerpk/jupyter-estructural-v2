"""
Controlador para gestión de Familias de Estructuras
"""

from dash import callback, Input, Output, State, ctx, no_update, ALL
import dash_bootstrap_components as dbc
from dash import html
import json
import re
import threading
from pathlib import Path
from datetime import datetime

def sanitizar_nombre_archivo(nombre):
    """Sanitizar nombre de archivo removiendo caracteres peligrosos"""
    if not nombre:
        return "familia"
    # Remover caracteres peligrosos y path traversal
    nombre_limpio = re.sub(r'[^\w\s-]', '_', nombre)
    nombre_limpio = nombre_limpio.replace('..', '').replace('/', '_').replace('\\', '_')
    return nombre_limpio.replace(' ', '_')

def ejecutar_calculo_tipo(tipo_calculo, funcion_ejecutar, funcion_cargar, estructura_actual, state, titulo_unico):
    """Ejecutar cálculo y cargar desde cache - patrón unificado"""
    print(f"Ejecutando {tipo_calculo}...")
    resultado = funcion_ejecutar(estructura_actual, state)
    if resultado.get('exito'):
        print(f"{tipo_calculo} exitoso, cargando desde cache...")
        calculo_cache = funcion_cargar(titulo_unico)
        if calculo_cache:
            print(f"{tipo_calculo}: Cache cargado para {titulo_unico}")
            return {'exito': True, 'cache': calculo_cache}
        else:
            print(f"{tipo_calculo}: No se pudo cargar desde cache para {titulo_unico}")
            return {'exito': False, 'mensaje': f'No se pudo cargar cache {tipo_calculo}'}
    else:
        print(f"{tipo_calculo} fallo: {resultado.get('mensaje')}")
        return {'exito': False, 'mensaje': resultado.get('mensaje')}

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

    # Callback único centralizado para manejar TODAS las acciones de familia
    @app.callback(
        [Output("toast-notificacion", "is_open"),
         Output("toast-notificacion", "header"),
         Output("toast-notificacion", "children"),
         Output("toast-notificacion", "color"),
         Output("familia-activa-state", "data"),
         Output("input-nombre-familia", "value"),
         Output("tabla-familia", "data"),
         Output("tabla-familia", "columns"),
         Output("resultados-familia", "children"),
         Output("modal-eliminar-familia", "is_open")],
        [Input("btn-guardar-familia", "n_clicks"),
         Input("btn-guardar-como-familia", "n_clicks"),
         Input("select-familia-existente", "value"),
         Input("btn-eliminar-familia", "n_clicks"),
         Input("modal-eliminar-confirmar", "n_clicks"),
         Input("btn-calcular-familia", "n_clicks"),
         Input("btn-cargar-cache-familia", "n_clicks")],
        [State("input-nombre-familia", "value"),
         State("tabla-familia", "data"),
         State("tabla-familia", "columns")],
        prevent_initial_call=True
    )
    def manejar_acciones_familia_centralizado(n_guardar, n_guardar_como, familia_seleccionada, n_eliminar, n_eliminar_confirmar, n_calcular, n_cargar_cache, nombre_familia, tabla_data, columnas):
        """Callback centralizado que maneja TODAS las acciones de familia"""
        from dash import callback_context
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        print(f"DEBUG: Callback centralizado ejecutado - trigger: {trigger_id}")
        print(f"DEBUG: n_guardar: {n_guardar}, n_guardar_como: {n_guardar_como}, familia_seleccionada: {familia_seleccionada}")
        print(f"DEBUG: n_eliminar: {n_eliminar}, n_eliminar_confirmar: {n_eliminar_confirmar}, n_calcular: {n_calcular}, n_cargar_cache: {n_cargar_cache}")
        
        # Guardar Familia
        if trigger_id == "btn-guardar-familia":
            print(f"DEBUG: Procesando guardar familia - nombre: {nombre_familia}")
            if not nombre_familia or not tabla_data:
                print("DEBUG: Faltan datos para guardar")
                return True, "Error", "Faltan datos para guardar familia", "danger", no_update, no_update, no_update, no_update, no_update, no_update
            
            try:
                familia_data = tabla_a_familia(tabla_data, columnas, nombre_familia)
                nombre_sanitizado = sanitizar_nombre_archivo(nombre_familia)
                
                data_dir = Path("data")
                data_dir.mkdir(exist_ok=True)
                filename = data_dir / f"{nombre_sanitizado}.familia.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(familia_data, f, indent=2, ensure_ascii=False)
                
                from models.app_state import AppState
                state = AppState()
                state.set_familia_activa(nombre_sanitizado)
                guardar_familia_activa_state(familia_data)
                
                return True, "Éxito", f"Familia '{nombre_familia}' guardada", "success", familia_data, no_update, no_update, no_update, no_update, no_update
                
            except Exception as e:
                return True, "Error", f"Error al guardar: {str(e)}", "danger", no_update, no_update, no_update, no_update, no_update, no_update
        
        # Guardar Como Familia
        elif trigger_id == "btn-guardar-como-familia":
            print(f"DEBUG: Procesando guardar como familia - nombre: {nombre_familia}")
            if not nombre_familia or not tabla_data:
                print("DEBUG: Faltan datos para guardar como")
                return True, "Error", "Faltan datos para guardar como familia", "danger", no_update, no_update, no_update, no_update, no_update, no_update
            
            try:
                familia_data = tabla_a_familia(tabla_data, columnas, nombre_familia)
                nombre_sanitizado = sanitizar_nombre_archivo(nombre_familia)
                
                data_dir = Path("data")
                data_dir.mkdir(exist_ok=True)
                filename = data_dir / f"{nombre_sanitizado}.familia.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(familia_data, f, indent=2, ensure_ascii=False)
                
                from models.app_state import AppState
                state = AppState()
                state.set_familia_activa(nombre_sanitizado)
                guardar_familia_activa_state(familia_data)
                
                return True, "Éxito", f"Familia guardada como '{nombre_familia}'", "success", familia_data, nombre_familia, no_update, no_update, no_update, no_update
                
            except Exception as e:
                return True, "Error", f"Error al guardar como: {str(e)}", "danger", no_update, no_update, no_update, no_update, no_update, no_update
        
        # Cargar Familia Seleccionada
        elif trigger_id == "select-familia-existente":
            print(f"DEBUG: Procesando cargar familia - seleccionada: {familia_seleccionada}")
            if not familia_seleccionada:
                print("DEBUG: No hay familia seleccionada")
                return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
            
            try:
                archivo_path = Path("data") / familia_seleccionada
                
                with open(archivo_path, 'r', encoding='utf-8') as f:
                    familia_data = json.load(f)
                
                tabla_data_nueva, columnas_nuevas = familia_a_tabla(familia_data)
                
                nombre_sanitizado = familia_seleccionada.replace('.familia.json', '')
                from models.app_state import AppState
                state = AppState()
                state.set_familia_activa(nombre_sanitizado)
                
                return True, "Éxito", f"Familia '{familia_data['nombre_familia']}' cargada", "success", familia_data, familia_data["nombre_familia"], tabla_data_nueva, columnas_nuevas, no_update, no_update
                
            except Exception as e:
                return True, "Error", f"Error al cargar familia: {str(e)}", "danger", no_update, no_update, no_update, no_update, no_update, no_update
        
        # Abrir Modal Eliminar Familia
        elif trigger_id == "btn-eliminar-familia":
            print(f"DEBUG: Procesando abrir modal eliminar - nombre: {nombre_familia}")
            if not nombre_familia:
                return True, "Advertencia", "Debe especificar un nombre de familia para eliminar", "warning", no_update, no_update, no_update, no_update, no_update, no_update
            
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, True
        
        # Eliminar Familia Confirmado
        elif trigger_id == "modal-eliminar-confirmar":
            print(f"DEBUG: Procesando eliminar familia confirmado - nombre: {nombre_familia}")
            if not nombre_familia:
                return True, "Error", "No hay familia para eliminar", "danger", no_update, no_update, no_update, no_update, no_update, False
            
            try:
                data_dir = Path("data")
                filename = data_dir / f"{nombre_familia.replace(' ', '_')}.familia.json"
                
                if filename.exists():
                    filename.unlink()  # Eliminar archivo
                    
                    # Resetear vista a familia vacía
                    familia_vacia = {
                        "nombre_familia": "",
                        "estructuras": {"Estr.1": {"TITULO": "", "cantidad": 1}}
                    }
                    tabla_data_nueva, columnas_nuevas = familia_a_tabla(familia_vacia)
                    
                    # Limpiar estado de familia actual
                    from models.app_state import AppState
                    state = AppState()
                    state.set_familia_activa(None)
                    guardar_familia_activa_state(None)
                    
                    return (True, "Éxito", f"Familia '{nombre_familia}' eliminada", "success",
                           None, "", tabla_data_nueva, columnas_nuevas, no_update, False)
                else:
                    return (True, "Advertencia", f"Archivo de familia '{nombre_familia}' no encontrado", "warning",
                           no_update, no_update, no_update, no_update, no_update, False)
                    
            except Exception as e:
                return (True, "Error", f"Error al eliminar familia: {str(e)}", "danger",
                       no_update, no_update, no_update, no_update, no_update, False)
        
        # Calcular Familia
        elif trigger_id == "btn-calcular-familia":
            print(f"DEBUG: Procesando calcular familia - nombre: {nombre_familia}")
            if not tabla_data or not nombre_familia:
                return True, "Error", "Faltan datos para calcular familia", "danger", no_update, no_update, no_update, no_update, no_update, no_update
            
            try:
                # Convertir tabla a formato familia
                familia_data = tabla_a_familia(tabla_data, columnas, nombre_familia)
                estructuras = familia_data.get("estructuras", {})
                
                if not estructuras:
                    return True, "Error", "No hay estructuras para calcular", "danger", no_update, no_update, no_update, no_update, no_update, no_update
                
                # Iniciar cálculo asíncrono
                def calcular_async():
                    try:
                        resultados_familia = {}
                        for nombre_estr, datos_estr in estructuras.items():
                            print(f"Calculando {nombre_estr}: {datos_estr.get('TITULO', 'Sin título')}")
                            resultado_estructura = ejecutar_calculo_estructura_familia(
                                datos_estr, nombre_familia, nombre_estr
                            )
                            resultados_familia[nombre_estr] = resultado_estructura
                        print(f"CALCULO FAMILIA COMPLETADO: {len(resultados_familia)} estructuras")
                    except Exception as e:
                        print(f"ERROR CALCULO FAMILIA ASYNC: {str(e)}")
                
                # Ejecutar en hilo separado
                thread = threading.Thread(target=calcular_async, daemon=True)
                thread.start()
                
                resultados_html = html.Div([
                    html.H4("Calculando familia..."),
                    html.P(f"Procesando {len(estructuras)} estructuras en segundo plano."),
                    html.P("Los resultados aparecerán en el cache cuando termine.")
                ])
                
                return True, "Info", f"Cálculo de familia '{nombre_familia}' iniciado", "info", no_update, no_update, no_update, no_update, resultados_html, no_update
                
            except Exception as e:
                return True, "Error", f"Error calculando familia: {str(e)}", "danger", no_update, no_update, no_update, no_update, no_update, no_update
        
        # Cargar Cache Familia
        elif trigger_id == "btn-cargar-cache-familia":
            print(f"DEBUG: Procesando cargar cache familia - nombre: {nombre_familia}")
            if not nombre_familia:
                return True, "Advertencia", "Debe especificar un nombre de familia para cargar cache", "warning", no_update, no_update, no_update, no_update, no_update, no_update
            
            try:
                # TODO: Implementar carga de cache de familia
                # Por ahora mostrar mensaje de no implementado
                return True, "Info", "Función de cargar cache familia no implementada aún", "info", no_update, no_update, no_update, no_update, no_update, no_update
                
            except Exception as e:
                return True, "Error", f"Error cargando cache: {str(e)}", "danger", no_update, no_update, no_update, no_update, no_update, no_update
        
        print(f"DEBUG: Trigger no reconocido o sin acción: {trigger_id}")
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    # Callback para cargar opciones de familias existentes
    @app.callback(
        Output("select-familia-existente", "options"),
        Input("select-familia-existente", "id"),
        prevent_initial_call=False
    )
    def cargar_opciones_familias(_):
        """Cargar lista de familias existentes"""
        print("DEBUG: Callback cargar_opciones_familias ejecutado")
        try:
            from pathlib import Path
            data_dir = Path("data")
            familias = []
            
            if data_dir.exists():
                for archivo in data_dir.glob("*.familia.json"):
                    nombre = archivo.stem.replace("_", " ")
                    familias.append({"label": nombre, "value": archivo.name})
            
            print(f"DEBUG: Familias encontradas: {familias}")
            return familias
        except Exception as e:
            print(f"ERROR: Error cargando familias: {e}")
            return []
    

    
    # Callback separado para cerrar modal eliminar familia
    @app.callback(
        Output("modal-eliminar-familia", "is_open", allow_duplicate=True),
        Input("modal-eliminar-cancelar", "n_clicks"),
        prevent_initial_call=True
    )
    def cerrar_modal_eliminar(n_clicks):
        """Cerrar modal de eliminar familia"""
        if n_clicks:
            return False
        return no_update
    
    # Callback separado para actualizar nombre en modal eliminar
    @app.callback(
        Output("modal-eliminar-familia-nombre", "children"),
        Input("modal-eliminar-familia", "is_open"),
        State("input-nombre-familia", "value"),
        prevent_initial_call=True
    )
    def actualizar_nombre_modal_eliminar(is_open, nombre_familia):
        """Actualizar nombre en modal eliminar"""
        if is_open and nombre_familia:
            return f"Familia: {nombre_familia}"
        return no_update
    # @app.callback(
    #     [Output("modal-eliminar-familia", "is_open"),
    #      Output("modal-eliminar-familia-nombre", "children")],
    #     [Input("btn-eliminar-familia", "n_clicks"),
    #      Input("modal-eliminar-cancelar", "n_clicks")],
    #     [State("input-nombre-familia", "value"),
    #      State("modal-eliminar-familia", "is_open")],
    #     prevent_initial_call=True
    # )
    # def abrir_modal_eliminar(n_clicks_eliminar, n_clicks_cancelar, nombre_familia, is_open):
    #     """Abrir/cerrar modal de confirmación para eliminar familia"""
    #     if not ctx.triggered:
    #         return no_update, no_update
    #     
    #     trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    #     
    #     if trigger_id == "btn-eliminar-familia" and nombre_familia:
    #         return True, f"Familia: {nombre_familia}"
    #     elif trigger_id == "modal-eliminar-cancelar":
    #         return False, no_update
    #     
    #     return no_update, no_update
    
    # Callback para Eliminar Familia (confirmado) - MOVIDO AL CALLBACK CENTRALIZADO
    # @app.callback(
    #     [Output("toast-notificacion", "is_open", allow_duplicate=True),
    #      Output("toast-notificacion", "header", allow_duplicate=True),
    #      Output("toast-notificacion", "children", allow_duplicate=True),
    #      Output("toast-notificacion", "color", allow_duplicate=True),
    #      Output("input-nombre-familia", "value", allow_duplicate=True),
    #      Output("tabla-familia", "data", allow_duplicate=True),
    #      Output("tabla-familia", "columns", allow_duplicate=True),
    #      Output("modal-eliminar-familia", "is_open", allow_duplicate=True),
    #      Output("familia-activa-state", "data", allow_duplicate=True)],
    #     Input("modal-eliminar-confirmar", "n_clicks"),
    #     [State("input-nombre-familia", "value")],
    #     prevent_initial_call=True
    # )
    # def eliminar_familia_confirmado(n_clicks, nombre_familia):
    #     """Eliminar familia tras confirmación"""
    #     if not n_clicks or not nombre_familia:
    #         return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    #     
    #     try:
    #         from pathlib import Path
    #         data_dir = Path("data")
    #         filename = data_dir / f"{nombre_familia.replace(' ', '_')}.familia.json"
    #         
    #         if filename.exists():
    #             filename.unlink()  # Eliminar archivo
    #             
    #             # Resetear vista a familia vacía sin plantilla
    #             familia_vacia = {
    #                 "nombre_familia": "",
    #                 "estructuras": {"Estr.1": {"TITULO": "", "cantidad": 1}}
    #             }
    #             tabla_data, columnas = familia_a_tabla(familia_vacia)
    #             
    #             # Limpiar estado de familia actual en AppState
    #             from models.app_state import AppState
    #             state = AppState()
    #             state.set_familia_activa(None)
    #             
    #             # Limpiar estado de familia actual
    #             guardar_familia_activa_state(None)
    #             
    #             return (True, "Éxito", f"Familia '{nombre_familia}' eliminada", "success",
    #                    "", tabla_data, columnas, False, None)
    #         else:
    #             return (True, "Advertencia", f"Archivo de familia '{nombre_familia}' no encontrado", "warning",
    #                    no_update, no_update, no_update, False, no_update)
    #             
    #     except Exception as e:
    #         return (True, "Error", f"Error al eliminar familia: {str(e)}", "danger",
    #                no_update, no_update, no_update, False, no_update)
    
    # Callback para persistir cambios automáticamente - COMENTADO PARA EVITAR CONFLICTOS
    # @app.callback(
    #     Output("familia-activa-state", "data", allow_duplicate=True),
    #     [Input("tabla-familia", "data"),
    #      Input("input-nombre-familia", "value")],
    #     [State("tabla-familia", "columns"),
    #      State("familia-activa-state", "data")],
    #     prevent_initial_call=True
    # )
    # def persistir_cambios_automaticamente(tabla_data, nombre_familia, columnas, familia_actual):
    #     """Persistir cambios automáticamente cuando se modifica la tabla o nombre"""
    #     if not tabla_data or not nombre_familia:
    #         return no_update
    #     
    #     try:
    #         # Convertir tabla a formato familia
    #         familia_data = tabla_a_familia(tabla_data, columnas, nombre_familia)
    #         
    #         # Solo persistir si hay cambios reales
    #         if familia_actual != familia_data:
    #             guardar_familia_activa_state(familia_data)
    #             return familia_data
    #         
    #         return no_update
    #     except (ValueError, KeyError, TypeError) as e:
    #         print(f"Error persistiendo cambios: {str(e)}")
    #         return no_update
    
    # Callback para persistir estado de familia actual - COMENTADO PARA EVITAR CONFLICTOS
    # @app.callback(
    #     Output("familia-activa-state", "data", allow_duplicate=True),
    #     [Input("btn-guardar-familia", "n_clicks"),
    #      Input("select-familia-existente", "value")],
    #     [State("input-nombre-familia", "value"),
    #      State("tabla-familia", "data"),
    #      State("tabla-familia", "columns")],
    #     prevent_initial_call=True
    # )
    # def actualizar_familia_actual_state(n_guardar, familia_seleccionada, nombre_familia, tabla_data, columnas):
    #     """Actualizar estado de familia actual"""
    #     if not ctx.triggered:
    #         return no_update
    #     
    #     trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    #     
    #     if trigger_id == "btn-guardar-familia" and nombre_familia and tabla_data:
    #         # Guardar estado tras guardar familia
    #         familia_data = tabla_a_familia(tabla_data, columnas, nombre_familia)
    #         guardar_familia_activa_state(familia_data)
    #         return familia_data
    #     elif trigger_id == "select-familia-existente" and familia_seleccionada:
    #         # Cargar estado de familia seleccionada
    #         try:
    #             from pathlib import Path
    #             archivo_path = Path("data") / familia_seleccionada
    #             with open(archivo_path, 'r', encoding='utf-8') as f:
    #                 familia_data = json.load(f)
    #             # Marcar como familia activa
    #             nombre_sanitizado = familia_seleccionada.replace('.familia.json', '')
    #             from models.app_state import AppState
    #             state = AppState()
    #             state.set_familia_activa(nombre_sanitizado)
    #             return familia_data
    #         except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
    #             print(f"Error cargando familia: {str(e)}")
    #             return no_update
    #     
    #     return no_update
    
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
    # Callback para Guardar Como Familia - COMENTADO TEMPORALMENTE PARA EVITAR CONFLICTOS
    # @app.callback(
    #     [Output("toast-notificacion", "is_open", allow_duplicate=True),
    #      Output("toast-notificacion", "header", allow_duplicate=True),
    #      Output("toast-notificacion", "children", allow_duplicate=True),
    #      Output("toast-notificacion", "color", allow_duplicate=True),
    #      Output("input-nombre-familia", "value", allow_duplicate=True),
    #      Output("familia-activa-state", "data", allow_duplicate=True)],
    #     Input("btn-guardar-como-familia", "n_clicks"),
    #     [State("input-nombre-familia", "value"),
    #      State("tabla-familia", "data"),
    #      State("tabla-familia", "columns")],
    #     prevent_initial_call=True
    # )
    def guardar_como_familia(n_clicks, nombre_actual, tabla_data, columnas):
        """Guardar familia con nombre sanitizado"""
        if not n_clicks or not nombre_actual or not tabla_data:
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        try:
            # Convertir tabla a formato familia
            familia_data = tabla_a_familia(tabla_data, columnas, nombre_actual)
            
            # Sanitizar nombre y guardar archivo
            nombre_sanitizado = sanitizar_nombre_archivo(nombre_actual)
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            filename = data_dir / f"{nombre_sanitizado}.familia.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(familia_data, f, indent=2, ensure_ascii=False)
            
            # Marcar como familia activa en AppState
            from models.app_state import AppState
            state = AppState()
            state.set_familia_activa(nombre_sanitizado)
            
            # Persistir estado y cambiar archivo actual
            guardar_familia_activa_state(familia_data)
            
            return (True, "Éxito", f"Familia guardada como '{nombre_actual}'", "success", nombre_actual, familia_data)
            
        except (ValueError, KeyError, TypeError, OSError) as e:
            print(f"Error guardando como familia: {str(e)}")
            return (True, "Error", f"Error al guardar como: {str(e)}", "danger", no_update, no_update)
    
    # Callback para Calcular Familia (Asíncrono) - MOVIDO AL CALLBACK CENTRALIZADO
    # @app.callback(
    #     [Output("resultados-familia", "children"),
    #      Output("toast-notificacion", "is_open", allow_duplicate=True),
    #      Output("toast-notificacion", "header", allow_duplicate=True),
    #      Output("toast-notificacion", "children", allow_duplicate=True),
    #      Output("toast-notificacion", "color", allow_duplicate=True)],
    #     Input("btn-calcular-familia", "n_clicks"),
    #     [State("tabla-familia", "data"),
    #      State("tabla-familia", "columns"),
    #      State("input-nombre-familia", "value")],
    #     prevent_initial_call=True
    # )
    # def calcular_familia(n_clicks, tabla_data, columnas, nombre_familia):
    #     """Ejecutar cálculos para toda la familia de forma asíncrona"""
    #     if not n_clicks or not tabla_data or not nombre_familia:
    #         return no_update, no_update, no_update, no_update, no_update
    #     
    #     print(f"INICIANDO CALCULO FAMILIA: {nombre_familia}")
    #     print(f"DEBUG: Datos de tabla recibidos: {len(tabla_data)} filas")
    #     print(f"DEBUG: Columnas: {[col['id'] for col in columnas if col['id'].startswith('Estr.')]}")
    #     
    #     try:
    #         # Convertir tabla a formato familia
    #         familia_data = tabla_a_familia(tabla_data, columnas, nombre_familia)
    #         estructuras = familia_data.get("estructuras", {})
    #         
    #         print(f"DEBUG: Estructuras convertidas: {list(estructuras.keys())}")
    #         for nombre_estr, datos_estr in estructuras.items():
    #             print(f"DEBUG: {nombre_estr} -> TITULO: {datos_estr.get('TITULO', 'Sin título')}")
    #         
    #         if not estructuras:
    #             return (no_update, True, "Error", "No hay estructuras para calcular", "danger")
    #         
    #         # Iniciar cálculo asíncrono
    #         def calcular_async():
    #             try:
    #                 resultados_familia = {}
    #                 for nombre_estr, datos_estr in estructuras.items():
    #                     print(f"Calculando {nombre_estr}: {datos_estr.get('TITULO', 'Sin título')}")
    #                     resultado_estructura = ejecutar_calculo_estructura_familia(
    #                         datos_estr, nombre_familia, nombre_estr
    #                     )
    #                     resultados_familia[nombre_estr] = resultado_estructura
    #                 print(f"CALCULO FAMILIA COMPLETADO: {len(resultados_familia)} estructuras")
    #             except Exception as e:
    #                 print(f"ERROR CALCULO FAMILIA ASYNC: {str(e)}")
    #         
    #         # Ejecutar en hilo separado
    #         thread = threading.Thread(target=calcular_async, daemon=True)
    #         thread.start()
    #         
    #         return (html.Div([
    #             html.H4("Calculando familia..."),
    #             html.P(f"Procesando {len(estructuras)} estructuras en segundo plano."),
    #             html.P("Los resultados aparecerán en el cache cuando termine.")
    #         ]), True, "Info", f"Cálculo de familia '{nombre_familia}' iniciado", "info")
    #         
    #     except (ValueError, KeyError, TypeError) as e:
    #         print(f"ERROR CALCULO FAMILIA: {str(e)}")
    #         return (no_update, True, "Error", f"Error calculando familia: {str(e)}", "danger")



def guardar_familia_activa_state(familia_data):
    """Guardar estado de familia activa usando AppState"""
    try:
        from pathlib import Path
        from models.app_state import AppState
        
        state = AppState()
        
        if familia_data is None:
            # Limpiar familia activa
            state.set_familia_activa(None)
            return
        
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Guardar archivo de familia con nombre correcto
        nombre_familia = familia_data.get("nombre_familia", "")
        if nombre_familia:
            nombre_sanitizado = sanitizar_nombre_archivo(nombre_familia)
            filename = data_dir / f"{nombre_sanitizado}.familia.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(familia_data, f, indent=2, ensure_ascii=False)
            print(f"Familia guardada en: {filename}")
            
            # Marcar como familia activa en AppState
            state.set_familia_activa(nombre_sanitizado)
    except Exception as e:
        print(f"Error guardando familia: {str(e)}")

def marcar_familia_activa(nombre_sanitizado):
    """Marcar cual es la familia activa actual"""
    try:
        from pathlib import Path
        data_dir = Path("data")
        archivo_activo = data_dir / "familia_activa.txt"
        with open(archivo_activo, 'w', encoding='utf-8') as f:
            f.write(nombre_sanitizado)
    except Exception as e:
        print(f"Error marcando familia activa: {str(e)}")

def obtener_familia_activa():
    """Obtener nombre de la familia activa"""
    try:
        from pathlib import Path
        data_dir = Path("data")
        archivo_activo = data_dir / "familia_activa.txt"
        if archivo_activo.exists():
            with open(archivo_activo, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except:
        pass
    return None
def cargar_familia_activa_state():
    """Cargar familia activa desde AppState"""
    try:
        from models.app_state import AppState
        state = AppState()
        return state.cargar_familia_activa()
    except:
        pass
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
            fila[nombre_estr] = datos_estr.get(parametro, "")
        
        tabla_data.append(fila)
    
    return tabla_data, columnas

def ejecutar_calculo_estructura_familia(estructura_data, nombre_familia="", nombre_estructura_familia=""):
    """Ejecutar cálculos para una estructura de familia usando SOLO datos en memoria"""
    from models.app_state import AppState
    
    titulo_original = estructura_data.get('TITULO', 'estructura')
    print(f"Ejecutando cálculos para: {titulo_original}")
    
    # CREAR TÍTULO ÚNICO para evitar conflictos de cache
    if nombre_familia and nombre_estructura_familia:
        titulo_unico = f"{nombre_familia}_{nombre_estructura_familia}_{titulo_original}"
        print(f"Usando título único para cache: {titulo_unico}")
    else:
        titulo_unico = titulo_original
    
    # Crear AppState y trabajar SOLO en memoria
    state = AppState()
    
    try:
        # VALIDAR parámetros críticos OBLIGATORIOS
        parametros_criticos = [
            'Vmax', 'Vmed', 't_hielo', 'Zco', 'Zcg', 'Cf_cable', 'Cf_guardia',
            'Cf_cadena', 'Cf_estructura', 'Zca', 'Zes', 'exposicion', 'clase',
            'A_cadena', 'PCADENA', 'PESTRUCTURA', 'A_estr_trans', 'A_estr_long',
            'SALTO_PORCENTUAL', 'PASO_AFINADO', 'RELFLECHA_MAX_GUARDIA', 'RELFLECHA_SIN_VIENTO'
        ]
        
        parametros_faltantes = [param for param in parametros_criticos 
                               if param not in estructura_data or estructura_data[param] is None]
        
        if parametros_faltantes:
            error_msg = f"Parámetros críticos faltantes en {titulo_original}: {', '.join(parametros_faltantes)}"
            print(f"ERROR: {error_msg}")
            return {'error': error_msg}
        
        # USAR DATOS DIRECTAMENTE EN MEMORIA - NO archivos
        estructura_actual = estructura_data.copy()
        estructura_actual['TITULO'] = titulo_unico
        print(f"Usando datos de familia con título único: {titulo_unico}")
        
        # Establecer estructura actual SOLO en memoria
        state.set_estructura_actual(estructura_actual)
        
        resultados = {}
        
        # Importar funciones necesarias
        from controllers.geometria_controller import ejecutar_calculo_cmc_automatico, ejecutar_calculo_dge
        from controllers.ejecutar_calculos import ejecutar_calculo_dme, ejecutar_calculo_arboles, ejecutar_calculo_sph, ejecutar_calculo_fundacion, ejecutar_calculo_costeo
        from utils.calculo_cache import CalculoCache
        
        state.cargado_desde_cache = False
        
        # Ejecutar todos los cálculos usando patrón unificado
        calculos = [
            ('cmc', ejecutar_calculo_cmc_automatico, CalculoCache.cargar_calculo_cmc),
            ('dge', ejecutar_calculo_dge, CalculoCache.cargar_calculo_dge),
            ('dme', ejecutar_calculo_dme, CalculoCache.cargar_calculo_dme),
            ('arboles', ejecutar_calculo_arboles, CalculoCache.cargar_calculo_arboles),
            ('sph', ejecutar_calculo_sph, CalculoCache.cargar_calculo_sph),
            ('fundacion', ejecutar_calculo_fundacion, CalculoCache.cargar_calculo_fund),
            ('costeo', ejecutar_calculo_costeo, CalculoCache.cargar_calculo_costeo)
        ]
        
        for tipo, func_ejecutar, func_cargar in calculos:
            resultados[tipo] = ejecutar_calculo_tipo(tipo.upper(), func_ejecutar, func_cargar, estructura_actual, state, titulo_unico)
        
        print(f"Calculos completados para {titulo_unico}")
        
        return resultados
        
    except Exception as e:
        print(f"Error en calculos para {titulo_unico}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
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
    
    # Fundación - EXACTAMENTE como en calcular_todo_controller.py
    if resultados.get('fundacion', {}).get('exito'):
        contenido.append(html.H3("6. FUNDACIÓN", className="mt-4"))
        calculo_fundacion = resultados['fundacion'].get('cache')
        if calculo_fundacion:
            try:
                from components.vista_fundacion import generar_resultados_fundacion
                resultado_fund = generar_resultados_fundacion(calculo_fundacion, estructura_data)
                if isinstance(resultado_fund, list):
                    contenido.extend(resultado_fund)
                else:
                    contenido.append(resultado_fund)
            except Exception as e:
                contenido.append(dbc.Alert(f"Error cargando Fundación: {str(e)}", color="warning"))
    else:
        mensaje_fundacion = resultados.get('fundacion', {}).get('mensaje', 'Fundación no ejecutado exitosamente')
        contenido.append(html.H3("6. FUNDACIÓN", className="mt-4"))
        contenido.append(dbc.Alert(f"Error Fundación: {mensaje_fundacion}", color="danger"))
    
    # Costeo - EXACTAMENTE como en calcular_todo_controller.py
    if resultados.get('costeo', {}).get('exito'):
        contenido.append(html.H3("7. COSTEO", className="mt-4"))
        calculo_costeo = resultados['costeo'].get('cache')
        if calculo_costeo:
            try:
                from components.vista_costeo import generar_resultados_costeo
                resultado_cost = generar_resultados_costeo(calculo_costeo, estructura_data)
                if isinstance(resultado_cost, list):
                    contenido.extend(resultado_cost)
                else:
                    contenido.append(resultado_cost)
            except Exception as e:
                contenido.append(dbc.Alert(f"Error cargando Costeo: {str(e)}", color="warning"))
    else:
        mensaje_costeo = resultados.get('costeo', {}).get('mensaje', 'Costeo no ejecutado exitosamente')
        contenido.append(html.H3("7. COSTEO", className="mt-4"))
        contenido.append(dbc.Alert(f"Error Costeo: {mensaje_costeo}", color="danger"))
    
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


