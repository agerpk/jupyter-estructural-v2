"""
Vista para gestión de Familias de Estructuras
"""

from dash import html, dcc
from dash.dash_table import DataTable
import dash_bootstrap_components as dbc
from typing import Dict, List, Any
import json
from components.modal_estados_climaticos import crear_modal_estados_climaticos
from components.modal_copiar_estados import crear_modal_copiar_estados

def crear_vista_familia_estructuras(familia_actual=None):
    """Crear vista principal de Familias de Estructuras"""
    
    print("🔵 DEBUG: Iniciando crear_vista_familia_estructuras")
    
    # Intentar cargar familia activa desde AppState si no se proporciona
    if familia_actual is None:
        from models.app_state import AppState
        state = AppState()
        nombre_familia_activa = state.get_familia_activa()
        
        if nombre_familia_activa:
            try:
                from utils.familia_manager import FamiliaManager
                familia_actual = FamiliaManager.cargar_familia(nombre_familia_activa)
                print(f"✅ DEBUG: Familia activa cargada: {nombre_familia_activa}")
            except Exception as e:
                print(f"⚠️ DEBUG: Error cargando familia activa: {e}")
                familia_actual = None
    
    if familia_actual is None:
        familia_actual = {
            "nombre_familia": "",
            "estructuras": {
                "Estr.1": cargar_plantilla_estructura()
            }
        }
        print("🔵 DEBUG: Familia actual creada por defecto")
    else:
        print(f"✅ DEBUG: Familia actual recibida: {familia_actual.get('nombre_familia', 'Sin nombre')}")
    
    # Generar datos de tabla
    tabla_data = generar_datos_tabla_familia(familia_actual)
    print(f"✅ DEBUG: Tabla generada con {len(tabla_data)} filas")
    
    # Configurar columnas dinámicamente
    columnas = [
        {"name": "Categoría", "id": "categoria", "editable": False, "type": "text"},
        {"name": "Parámetro", "id": "parametro", "editable": False, "type": "text"},
        {"name": "Símbolo", "id": "simbolo", "editable": False, "type": "text"},
        {"name": "Unidad", "id": "unidad", "editable": False, "type": "text"},
        {"name": "Descripción", "id": "descripcion", "editable": False, "type": "text"}
    ]
    
    # Agregar columnas de estructuras - TODAS EDITABLES
    estructuras = familia_actual.get("estructuras", {})
    for nombre_estr in sorted(estructuras.keys()):
        columnas.append({
            "name": nombre_estr,
            "id": nombre_estr,
            "editable": True,
            "type": "any"
        })
    
    print(f"✅ DEBUG: Columnas configuradas: {[col['id'] for col in columnas]}")
    print(f"🔍 DEBUG: Retornando vista con DataTable - data={len(tabla_data)} filas, columns={len(columnas)} cols")
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H4("Familia de Estructuras", className="mb-0")),
            dbc.CardBody([
                # Campo nombre familia
                crear_campo_nombre_familia(familia_actual.get("nombre_familia", "")),
                
                # Dropdown para cargar familia existente
                crear_dropdown_cargar_familia(),
                
                # Botones de control
                crear_botones_control_familia(),
                
                # Filtros por categoría
                crear_filtros_familia(),
                html.Hr(),
                
                # Estados Climáticos (compartidos por toda la familia)
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Button("Editar Estados Climaticos y Restricciones", id="btn-abrir-estados-familia", 
                                  color="info", size="sm", className="me-2"),
                        html.H5("Estados Climáticos (Compartidos)", className="d-inline")
                    ])
                ], className="mb-3"),
                
                # Tabla de parámetros multi-columna
                html.Div([
                    DataTable(
                        id="tabla-familia",
                        data=tabla_data,
                        columns=columnas,
                        editable=True,
                        row_deletable=False,
                        page_action='native',
                        page_size=60,
                        sort_action="native",
                        filter_action="native",
                        fixed_rows={'headers': True, 'data': 1},
                        style_cell={'textAlign': 'left', 'padding': '8px', 'color': '#000000', 'fontSize': '14px', 'backgroundColor': '#ffffff'},
                        style_header={'backgroundColor': '#d0e8f2', 'color': '#000000', 'fontWeight': 'bold', 'textAlign': 'center'},
                        style_data={'backgroundColor': '#ffffff', 'color': '#000000'},
                        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa', 'color': '#000000'}],
                        css=[{
                            'selector': '.dash-spreadsheet td.focused',
                            'rule': 'background-color: #e3f2fd !important; color: #000000 !important;'
                        }, {
                            'selector': '.dash-spreadsheet td.active',
                            'rule': 'background-color: #bbdefb !important; color: #000000 !important;'
                        }]
                    )
                ], style={'width': '100%', 'marginTop': '20px'}),
                
                # Modal para edición
                crear_modal_familia(),
                
                # Modal para estados climáticos de familia
                crear_modal_estados_climaticos("modal-estados-familia"),
                crear_modal_copiar_estados("modal-copiar-estados-familia")
            ])
        ])
    ])

def crear_filtros_familia():
    """Crear filtros por categoría para familia"""
    from utils.parametros_manager import ParametrosManager
    
    categorias = ParametrosManager.obtener_parametros_por_categoria()
    opciones_categoria = [{"label": "Todas", "value": "todas"}]
    opciones_categoria.extend([{"label": cat, "value": cat} for cat in sorted(categorias.keys())])
    
    return dbc.Row([
        dbc.Col([
            html.Label("Filtrar por categoría:", className="form-label"),
            dbc.Select(
                id="filtro-categoria-familia",
                options=opciones_categoria,
                value="todas",
                size="sm"
            )
        ], width=3),
        dbc.Col([
            html.Label("Buscar parámetro:", className="form-label"),
            dbc.Input(
                id="buscar-parametro-familia",
                type="text",
                placeholder="Escriba para buscar...",
                size="sm"
            )
        ], width=3),
        dbc.Col([
            html.Label("\u00a0", className="form-label"),
            html.Div([
                dbc.Button("Buscar", id="btn-buscar-familia", color="primary", size="sm", className="me-2"),
                dbc.Button("Borrar Filtros", id="btn-borrar-filtros-familia", color="secondary", size="sm")
            ])
        ], width=3)
    ], className="mb-3")

def crear_dropdown_cargar_familia():
    """Crear dropdown para cargar familia existente"""
    return dbc.Row([
        dbc.Col([
            html.Label("CARGAR FAMILIA EXISTENTE:", className="form-label fw-bold"),
            dbc.Select(
                id="select-familia-existente",
                placeholder="Seleccione familia...",
                size="lg"
            )
        ], width=6)
    ], className="mb-3")

def crear_botones_control_familia():
    """Crear botones de control para familia"""
    return html.Div([
        # Controles de Tabla
        dbc.Row([
            dbc.Col([
                html.H6("Controles de Tabla:", className="text-muted mb-2"),
                dbc.ButtonGroup([
                    dbc.Button(
                        "Agregar Estructura",
                        id="btn-agregar-estructura",
                        color="success",
                        size="sm"
                    ),
                    dbc.Button(
                        "Eliminar Estructura",
                        id="btn-eliminar-estructura",
                        color="danger",
                        size="sm"
                    ),
                    dbc.Button(
                        "Cargar Columna",
                        id="btn-cargar-columna",
                        color="info",
                        size="sm"
                    )
                ])
            ], width=12)
        ], className="mb-3"),
        
        # Controles de Familia
        dbc.Row([
            dbc.Col([
                html.H6("Controles de Familia:", className="text-muted mb-2"),
                dbc.ButtonGroup([
                    dbc.Button(
                        "Guardar Familia",
                        id="btn-guardar-familia",
                        color="primary",
                        size="sm"
                    ),
                    dbc.Button(
                        "Guardar Como",
                        id="btn-guardar-como-familia",
                        color="outline-primary",
                        size="sm"
                    ),
                    dbc.Button(
                        "Eliminar Familia",
                        id="btn-eliminar-familia",
                        color="outline-danger",
                        size="sm"
                    )
                ], className="me-3"),
                
                dbc.ButtonGroup([
                    dbc.Button(
                        "Calcular Familia",
                        id="btn-calcular-familia",
                        color="warning",
                        size="sm"
                    ),
                    dbc.Button(
                        "Cargar Cache",
                        id="btn-cargar-cache-familia",
                        color="dark",
                        size="sm"
                    )
                ])
            ], width=12)
        ])
    ], className="mb-3")

def crear_campo_nombre_familia(nombre_actual):
    """Crear campo para nombre de familia"""
    return dbc.Row([
        dbc.Col([
            html.Label("NOMBRE FAMILIA:", className="form-label fw-bold"),
            dbc.Input(
                id="input-nombre-familia",
                type="text",
                value=nombre_actual,
                placeholder="Ingrese nombre de la familia...",
                size="lg"
            )
        ], width=12)
    ], className="mb-3")

def crear_modal_familia():
    """Crear modal para edición de celda"""
    return html.Div([
        # Modal para editar celda
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Editar Parámetro")),
            dbc.ModalBody(id="modal-familia-body-parametro"),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-familia-cancelar", color="secondary", className="me-2"),
                dbc.Button("Confirmar", id="modal-familia-confirmar", color="primary")
            ])
        ], id="modal-familia-parametro", is_open=False),
        
        # Modal para confirmar eliminar familia
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Eliminar Familia")),
            dbc.ModalBody([
                html.P("¿Está seguro que desea eliminar esta familia?"),
                html.P(id="modal-eliminar-familia-nombre", className="fw-bold text-danger"),
                html.P("Esta acción no se puede deshacer.", className="text-warning")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-eliminar-cancelar", color="secondary", className="me-2"),
                dbc.Button("Eliminar", id="modal-eliminar-confirmar", color="danger")
            ])
        ], id="modal-eliminar-familia", is_open=False),
        
        # Modal para cargar columna con estructura existente
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Cargar Columna con Estructura Existente")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Seleccionar estructura:"),
                        dbc.Select(
                            id="select-estructura-cargar-columna",
                            placeholder="Seleccione estructura..."
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Columna destino:"),
                        dbc.Select(
                            id="select-columna-destino",
                            placeholder="Seleccione columna..."
                        )
                    ], width=6)
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-cargar-columna-cancelar", color="secondary", className="me-2"),
                dbc.Button("Cargar", id="modal-cargar-columna-confirmar", color="primary")
            ])
        ], id="modal-cargar-columna", is_open=False),
        
        # Modal para eliminar estructura
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Eliminar Estructura")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Seleccionar columna a eliminar:"),
                        dbc.Select(
                            id="select-columna-eliminar",
                            placeholder="Seleccione columna..."
                        )
                    ], width=12)
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-eliminar-estructura-cancelar", color="secondary", className="me-2"),
                dbc.Button("Eliminar", id="modal-eliminar-estructura-confirmar", color="danger")
            ])
        ], id="modal-eliminar-estructura", is_open=False),
        
        # Stores para datos
        dcc.Store(id="modal-familia-celda-info", data=None),
        dcc.Store(id="tabla-familia-original", data=None),
        dcc.Store(id="familia-actual-state", data=None),
        
        # Área de resultados
        html.Div(id="resultados-familia", className="mt-4"),
        
        # Botón descargar HTML familia
        html.Div([
            dbc.Button(
                "Descargar HTML Familia Completa",
                id="btn-descargar-html-familia",
                color="success",
                size="lg",
                className="mt-3",
                style={"display": "none"}  # Oculto por defecto
            ),
            dcc.Download(id="download-html-familia")
        ], id="container-descargar-html"),
        
        # Toast para notificaciones
        dbc.Toast(
            id="toast-notificacion",
            header="Notificación",
            is_open=False,
            dismissable=True,
            duration=4000,
            style={"position": "fixed", "top": 80, "right": 20, "width": 300, "z-index": 1050}
        )
    ])

# Los callbacks están ahora en familia_controller.py

def generar_datos_tabla_familia(familia_actual):
    """Generar datos para tabla de familia con TODOS los campos de plantilla"""
    
    print("DEBUG: Iniciando generar_datos_tabla_familia")
    
    # Cargar plantilla para obtener estructura de parámetros
    plantilla = cargar_plantilla_estructura()
    
    if not plantilla:
        print("DEBUG: No se pudo cargar plantilla")
        return []
    
    print(f"DEBUG: Plantilla cargada con {len(plantilla)} campos")
    
    # Obtener estructuras de la familia
    estructuras = familia_actual.get("estructuras", {"Estr.1": plantilla})
    print(f"DEBUG: Estructuras en familia: {list(estructuras.keys())}")
    
    # Usar ParametrosManager para obtener metadata
    from utils.parametros_manager import ParametrosManager
    metadata_dict = ParametrosManager.PARAMETROS_METADATA
    
    # Generar filas de tabla para TODOS los campos de plantilla
    tabla_data = []
    
    # Agregar fila TITULO como primera fila
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
    
    # Agregar fila CANTIDAD como segunda fila
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
    
    # Procesar TODOS los campos de la plantilla
    for parametro, valor_plantilla in plantilla.items():
        # Saltar campos especiales (pero NO costeo - se procesará expandido)
        if parametro in ["TITULO", "cantidad", "fecha_creacion", "fecha_modificacion", "version", "nodos_editados", "estados_climaticos"]:
            continue
        
        # Expandir campos anidados de costeo
        if parametro == "costeo" and isinstance(valor_plantilla, dict):
            for subcampo, subvalor in valor_plantilla.items():
                if isinstance(subvalor, dict):
                    # Expandir un nivel más (ej: fundaciones.precio_m3_hormigon)
                    for subsubcampo, subsubvalor in subvalor.items():
                        param_completo = f"{parametro}.{subcampo}.{subsubcampo}"
                        fila = {
                            "categoria": "Costeo",
                            "parametro": param_completo,
                            "simbolo": subsubcampo[:10],
                            "unidad": "UM" if "precio" in subsubcampo or "costo" in subsubcampo else "-",
                            "descripcion": subsubcampo.replace("_", " ").title(),
                            "tipo": "float" if isinstance(subsubvalor, (int, float)) else "str"
                        }
                        # Agregar valores de cada estructura
                        for nombre_estr, datos_estr in estructuras.items():
                            costeo_estr = datos_estr.get("costeo", {})
                            subcampo_estr = costeo_estr.get(subcampo, {})
                            fila[nombre_estr] = subcampo_estr.get(subsubcampo, subsubvalor)
                        tabla_data.append(fila)
                else:
                    # Campo simple dentro de costeo
                    param_completo = f"{parametro}.{subcampo}"
                    fila = {
                        "categoria": "Costeo",
                        "parametro": param_completo,
                        "simbolo": subcampo[:10],
                        "unidad": "UM" if "precio" in subcampo or "costo" in subcampo else "-",
                        "descripcion": subcampo.replace("_", " ").title(),
                        "tipo": "float" if isinstance(subvalor, (int, float)) else "str"
                    }
                    # Agregar valores de cada estructura
                    for nombre_estr, datos_estr in estructuras.items():
                        costeo_estr = datos_estr.get("costeo", {})
                        fila[nombre_estr] = costeo_estr.get(subcampo, subvalor)
                    tabla_data.append(fila)
            continue
        
        # Obtener metadata si existe, sino usar valores por defecto
        if parametro in metadata_dict:
            metadata = metadata_dict[parametro]
            fila = {
                "categoria": metadata["categoria"],
                "parametro": parametro,
                "simbolo": metadata["simbolo"],
                "unidad": metadata["unidad"],
                "descripcion": metadata["descripcion"],
                "tipo": metadata["tipo"]
            }
        else:
            # Parámetro sin metadata - inferir tipo
            tipo_inferido = "str"
            if isinstance(valor_plantilla, bool):
                tipo_inferido = "bool"
            elif isinstance(valor_plantilla, int):
                tipo_inferido = "int"
            elif isinstance(valor_plantilla, float):
                tipo_inferido = "float"
            
            fila = {
                "categoria": "Otros",
                "parametro": parametro,
                "simbolo": parametro[:10],
                "unidad": "-",
                "descripcion": parametro.replace("_", " ").title(),
                "tipo": tipo_inferido
            }
        
        # Agregar valores de cada estructura
        for nombre_estr, datos_estr in estructuras.items():
            fila[nombre_estr] = datos_estr.get(parametro, valor_plantilla)
        
        tabla_data.append(fila)
    
    print(f"DEBUG: Tabla final generada con {len(tabla_data)} filas (TODOS los campos)")
    if tabla_data:
        print(f"DEBUG: Primera fila: {tabla_data[0]}")
    
    return tabla_data

def cargar_plantilla_estructura():
    """Cargar plantilla de estructura"""
    try:
        with open("data/plantilla.estructura.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def crear_tabla_estados_climaticos_familia(familia_actual):
    """Crear tabla editable de estados climáticos para familia"""
    
    # Cargar estados desde familia_actual si existen
    estados_guardados = familia_actual.get("estados_climaticos", {})
    
    # Valores por defecto
    estados_default = {
        "I": {"temperatura": 35, "descripcion": "Tmáx", "viento_velocidad": 0, "espesor_hielo": 0},
        "II": {"temperatura": -20, "descripcion": "Tmín", "viento_velocidad": 0, "espesor_hielo": 0},
        "III": {"temperatura": 10, "descripcion": "Vmáx", "viento_velocidad": 38.9, "espesor_hielo": 0},
        "IV": {"temperatura": -5, "descripcion": "Vmed", "viento_velocidad": 15.56, "espesor_hielo": 0.01},
        "V": {"temperatura": 8, "descripcion": "TMA", "viento_velocidad": 0, "espesor_hielo": 0}
    }
    
    # Mezclar estados guardados con defaults
    for estado_id in estados_default.keys():
        if estado_id in estados_guardados:
            estados_default[estado_id].update(estados_guardados[estado_id])
    
    # Cargar restricciones desde familia_actual si existen
    restricciones_guardadas = familia_actual.get("restricciones_cables", {})
    restricciones_conductor = restricciones_guardadas.get("conductor", {}).get("tension_max_porcentaje", {})
    restricciones_guardia = restricciones_guardadas.get("guardia", {}).get("tension_max_porcentaje", {})
    
    # Defaults si no existen
    if not restricciones_conductor:
        restricciones_conductor = {"I": 0.25, "II": 0.40, "III": 0.40, "IV": 0.40, "V": 0.25}
    if not restricciones_guardia:
        restricciones_guardia = {"I": 0.7, "II": 0.70, "III": 0.70, "IV": 0.7, "V": 0.7}
    
    # Encabezado
    header = dbc.Row([
        dbc.Col(html.Strong("Estado"), md=1),
        dbc.Col(html.Strong("Temp (°C)"), md=1),
        dbc.Col(html.Strong("Descripción"), md=2),
        dbc.Col(html.Strong("Viento (m/s)"), md=2),
        dbc.Col(html.Strong("Hielo (m)"), md=2),
        dbc.Col(html.Strong("Restricción Conductor (%)"), md=2),
        dbc.Col(html.Strong("Restricción Guardia (%)"), md=2),
    ], className="mb-2 fw-bold")
    
    filas = [header]
    for estado_id in ["I", "II", "III", "IV", "V"]:
        valores = estados_default[estado_id]
        fila = dbc.Row([
            dbc.Col(html.Strong(estado_id), md=1),
            dbc.Col(
                dbc.Input(id={"type": "familia-estado-temp", "index": estado_id}, type="number", 
                         value=valores.get("temperatura"), size="sm"), md=1
            ),
            dbc.Col(
                dbc.Input(id={"type": "familia-estado-desc", "index": estado_id}, type="text",
                         value=valores.get("descripcion"), size="sm"), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "familia-estado-viento", "index": estado_id}, type="number",
                         value=valores.get("viento_velocidad"), size="sm"), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "familia-estado-hielo", "index": estado_id}, type="number",
                         value=valores.get("espesor_hielo"), size="sm"), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "familia-restriccion-conductor", "index": estado_id}, type="number",
                         value=restricciones_conductor.get(estado_id, 0.25), 
                         size="sm", step=0.01, min=0, max=1), md=2
            ),
            dbc.Col(
                dbc.Input(id={"type": "familia-restriccion-guardia", "index": estado_id}, type="number",
                         value=restricciones_guardia.get(estado_id, 0.7), 
                         size="sm", step=0.01, min=0, max=1), md=2
            ),
        ], className="mb-2")
        filas.append(fila)
    
    return html.Div(filas)