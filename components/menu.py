"""
Componentes de menú para la aplicación
"""

from dash import html
import dash_bootstrap_components as dbc

def crear_menu_archivo():
    """Crear menú ARCHIVO"""
    return dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem("Nueva Estructura", id="menu-nueva-estructura"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Cargar Estructura desde DB", id="menu-cargar-estructura"),
            dbc.DropdownMenuItem("Cargar desde Computadora", id="menu-cargar-desde-pc"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Guardar Estructura", id="menu-guardar-estructura"),
            dbc.DropdownMenuItem("Descargar Estructura", id="menu-descargar-estructura"),
            dbc.DropdownMenuItem("Guardar Estructura Como...", id="menu-guardar-como"),
            dbc.DropdownMenuItem("Guardar como Plantilla", id="menu-guardar-plantilla"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Consola", id="menu-consola"),
        ],
        nav=True,
        in_navbar=True,
        label="ARCHIVO",
        className="ms-2",
        direction="down",
    )

def crear_modal_nueva_estructura():
    """Crear modal para nueva estructura"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Nueva Estructura")),
        dbc.ModalBody([
            dbc.Label("Nombre de la estructura:"),
            dbc.Input(
                id="input-nombre-nueva-estructura",
                type="text",
                placeholder="Ingrese nombre de la estructura..."
            ),
            html.Small("El archivo se guardará como: [nombre].estructura.json", 
                      className="text-muted mt-2 d-block")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-nueva", color="secondary", className="me-2"),
            dbc.Button("Crear", id="btn-crear-nueva-confirmar", color="primary")
        ])
    ], id="modal-nueva-estructura", is_open=False)

def crear_menu_editar():
    """Crear menú EDITAR"""
    return dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem("Ajustar Parámetros", id="menu-ajustar-parametros"),
            dbc.DropdownMenuItem("Eliminar Estructura de DB", id="menu-eliminar-estructura"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Agregar Cable", id="menu-agregar-cable"),
            dbc.DropdownMenuItem("Modificar Cable", id="menu-modificar-cable"),
            dbc.DropdownMenuItem("Eliminar Cable", id="menu-eliminar-cable"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Borrar Cache", id="menu-borrar-cache"),
        ],
        nav=True,
        in_navbar=True,
        label="EDITAR",
        className="ms-2",
        direction="down",
    )

def crear_menu_calcular():
    """Crear menú CALCULAR"""
    return dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem("Cálculo Mecánico de Cables", id="menu-calculo-mecanico"),
            dbc.DropdownMenuItem("Diseño Geométrico de Estructura", id="menu-diseno-geometrico"),
            dbc.DropdownMenuItem("Diseño Mecánico de Estructura", id="menu-diseno-mecanico"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("ADC - Árboles de Carga", id="menu-arboles-carga"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Selección Poste Hormigón (SPH)", id="menu-seleccion-poste"),
            dbc.DropdownMenuItem("Fundación", id="menu-fundacion"),
            dbc.DropdownMenuItem("Costeo", id="menu-costeo"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Calcular Todo", id="menu-calcular-todo", style={"fontWeight": "bold"}),
        ],
        nav=True,
        in_navbar=True,
        label="CALCULAR",
        className="ms-2",
        direction="down",
    )

def crear_modal_cargar_db(estructuras_disponibles):
    """Crear modal para cargar estructura desde DB"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Cargar Estructura desde Base de Datos")),
        dbc.ModalBody([
            dbc.Label("Seleccionar estructura:"),
            dbc.Select(
                id="select-estructura-db",
                options=[{"label": e, "value": e} for e in estructuras_disponibles],
                placeholder="Seleccione una estructura..."
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-db", color="secondary", className="me-2"),
            dbc.Button("Cargar", id="btn-cargar-db", color="primary")
        ])
    ], id="modal-cargar-db", is_open=False)

def crear_modal_guardar_como(titulo_actual):
    """Crear modal para guardar como"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Guardar Estructura Como")),
        dbc.ModalBody([
            dbc.Label("Nuevo nombre para la estructura:"),
            dbc.Input(
                id="input-titulo-nuevo",
                value=titulo_actual,
                type="text",
                placeholder="Ingrese nuevo título..."
            ),
            html.Small("El archivo se guardará como: [título].estructura.json", 
                      className="text-muted mt-2 d-block")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-como", color="secondary", className="me-2"),
            dbc.Button("Guardar", id="btn-guardar-como-confirmar", color="primary")
        ])
    ], id="modal-guardar-como", is_open=False)

def crear_modal_guardar_plantilla():
    """Crear modal para confirmar guardar como plantilla"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Guardar como Plantilla")),
        dbc.ModalBody([
            html.P("¿Está seguro que desea reemplazar la plantilla actual?"),
            html.P("Esta acción no se puede deshacer.", className="text-danger")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-plantilla", color="secondary", className="me-2"),
            dbc.Button("Confirmar", id="btn-guardar-plantilla-confirmar", color="danger")
        ])
    ], id="modal-guardar-plantilla", is_open=False)

def crear_menu_herramientas():
    """Crear menú HERRAMIENTAS"""
    return dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem("Comparativa CMC", id="menu-comparativa-cmc"),
        ],
        nav=True,
        in_navbar=True,
        label="HERRAMIENTAS",
        className="ms-2",
        direction="down",
    )

def crear_menu_info():
    """Crear menú INFO"""
    return dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem("Acerca de AGP", id="menu-acerca-de"),
        ],
        nav=True,
        in_navbar=True,
        label="INFO",
        className="ms-2",
        direction="down",
    )

def crear_modal_acerca_de():
    """Crear modal Acerca de AGP"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Acerca de AGP")),
        dbc.ModalBody([
            html.Div([
                html.H5("AGP - Análisis General de Postaciones", className="text-center mb-4"),
                html.P("Versión 1.0", className="text-center"),
                html.P("Programado por AGPK", className="text-center"),
                html.P(["Tg: ", html.A("@alegerpk", href="https://t.me/alegerpk", target="_blank")], className="text-center"),
                html.P("Año 2025", className="text-center")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cerrar", id="btn-cerrar-acerca-de", color="primary")
        ])
    ], id="modal-acerca-de", is_open=False)

def crear_modal_borrar_cache():
    """Crear modal para confirmar borrar cache"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Borrar Cache")),
        dbc.ModalBody([
            html.P("¿Está seguro que desea borrar todos los archivos de cache?"),
            html.P("Se eliminarán todos los cálculos guardados e imágenes generadas.", className="text-warning"),
            html.P("Las estructuras guardadas NO se eliminarán.", className="text-muted")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancelar-borrar-cache", color="secondary", className="me-2"),
            dbc.Button("Borrar Cache", id="btn-confirmar-borrar-cache", color="danger")
        ])
    ], id="modal-borrar-cache", is_open=False)