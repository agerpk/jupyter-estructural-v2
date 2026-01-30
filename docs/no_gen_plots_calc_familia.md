# Plan: Opción "No generar plots" en Vista "Calcular Familia" ✅

## Objetivo
Agregar un control (checkbox / switch) en la vista de **Calcular Familia** que permita desactivar la generación de plots (gráficos 2D/3D) durante el cálculo de la familia, para acelerar la ejecución cuando el usuario solo necesite tablas/valores y no imágenes. El control debe comportarse de forma similar al `vano-economico` (switch `vano-economico-switch-generar-plots`).

---

## Resumen de la solución propuesta 💡
- Añadir un **Switch** en `components/vista_familia_estructuras.py` (id sugerido: `familia-switch-generar-plots`).
- Pasar el valor del switch como `State` al callback `calcular_familia_completa` en `controllers/familia_controller.py` y a `cargar_cache_familia`.
- Reutilizar el parámetro `generar_plots` que ya existe en `utils/calcular_familia_logica_encadenada.py` (ya soporta `generar_plots: bool = True`).
- Hacer que `generar_vista_resultados_familia(...)` acepte un parámetro opcional `generar_plots` y, cuando sea `False`, omita o reemplace los componentes pesados de imágenes por placeholders (por ejemplo, texto: "Gráficos omitidos (generar_plots=False)").
- (Opcional pero recomendado) Persistir la preferencia en `AppState` (ej. `set_generar_plots_familia` / `get_generar_plots_familia`) y/o en un archivo temporal para volver a usar la misma preferencia en nuevas sesiones/view reload.

---

## Cambios concretos (paso a paso) 🔧

1) UI: añadir switch en `components/vista_familia_estructuras.py`

- Insertar el switch junto a los controles de cálculo (por ejemplo debajo de `crear_checklist_calculos_familia()` o dentro de `crear_botones_control_familia()`):

```python
# Ejemplo (sugerencia): en crear_botones_control_familia() debajo de los botones
dbc.Row([
    dbc.Col([
        dbc.Label("Generar Gráficos:", className="fw-bold"),
        dbc.Switch(
            id="familia-switch-generar-plots",
            value=True,  # RECOMENDADO: default True para mantener comportamiento actual
            label="Activar graficos 2D/3D (más lento)"
        ),
        html.Small("Desactivado: cálculo rápido (solo datos)", className="text-muted")
    ], width=12)
])
```

- **Decisión de valor por defecto:** Recomiendo `value=True` para no romper comportamiento actual; si se prefiere comportamiento "rápido por defecto" (como en vano), usar `value=False`.


2) Controller: recibir el valor y pasarlo al motor de cálculo (`familia_controller.py`)

- Modificar la firma internamente del callback `calcular_familia_completa(...)` para incluir la nueva `State("familia-switch-generar-plots", "value")` y aceptar `generar_plots` (booleano) dentro del cuerpo.

- Pasar `generar_plots` a `ejecutar_calculo_familia_completa(...)`:

```python
# ANTES
resultados_familia = ejecutar_calculo_familia_completa(familia_data, calculos_activos=calculos_activos)

# DESPUÉS
resultados_familia = ejecutar_calculo_familia_completa(
    familia_data,
    generar_plots=generar_plots,
    calculos_activos=calculos_activos
)
```

- También añadir `State("familia-switch-generar-plots", "value")` en `cargar_cache_familia(...)` y pasar ese valor a `generar_vista_resultados_familia(..., generar_plots=generar_plots)` (ver punto 3).

- (Opcional) Guardar la preferencia en `AppState` y en un archivo temporal para que persista entre acciones, similar a `vano_economico_ajustes`. Añadir un pequeño callback que guarde `familia-switch-generar-plots` en `AppState` cuando cambie.


3) Vista/Renderizado: adaptar `generar_vista_resultados_familia(...)` para respetar `generar_plots`

- Cambiar la firma:

```python
# ANTES
def generar_vista_resultados_familia(resultados_familia: Dict, calculos_activos: List[str] = None) -> List:

# DESPUÉS
def generar_vista_resultados_familia(resultados_familia: Dict, calculos_activos: List[str] = None, generar_plots: bool = True) -> List:
```

- Donde se agregan componentes que contienen gráficos (p. ej. `generar_resultados_cmc`, `generar_resultados_dge`, dcc.Graph, etc.), envolver o condicionar la inclusión de esos componentes con `if generar_plots:`.

- Si `generar_plots` es `False`, sustituir componentes pesados por una alerta/label informando "Gráficos omitidos (generar_plots=False)" o por tablas resumidas.

- Asegurar que funciones auxiliares `generar_resultados_*` que cargan y muestran figuras toleren inputs con `None` (ya debe estar contemplado en otras partes). Si no, adaptar para que no fallen cuando faltan figuras.


4) Lógica de cálculo: verificación de propagación (`calcular_familia_logica_encadenada.py`)

- La función `ejecutar_calculo_familia_completa(..., generar_plots: bool = True, ...)` ya existe y propaga `generar_plots` a `_ejecutar_secuencia_estructura(...)`, que a su vez pasa `generar_plots` a las funciones específicas (`ejecutar_calculo_cmc_automatico`, `ejecutar_calculo_dge`, etc.).

- Revisar que todas las funciones llamadas aceptan `generar_plots` y respetan la bandera; ya existe el soporte en los módulos principales (ver `docs/implementacion_generar_plots.md`). Hacer ajustes menores si alguna función no soporta la bandera.


5) Persistencia / Cache

- `CalculoCache` ya debe manejar casos donde las figuras no existen (por ejemplo guardando `fig=None` o sin archivos). Asegurarse de que cuando `generar_plots=False`, el cache se guarda correctamente y `generar_vista_resultados_familia` sepa interpretar resultados con ausencia de imágenes.

- En `cargar_cache_familia(...)` pasar el `generar_plots` actual para que la vista que se arma para el usuario respete la preferencia (ej. ocultar imágenes aunque existan en cache si el user optó por no generar ploteos ahora).


6) AppState (recomendado)

- Añadir métodos en `models/app_state.py`:

```python
def set_generar_plots_familia(self, valor: bool):
    state_data = self._read_state()
    state_data['generar_plots_familia'] = valor
    self._write_state(state_data)

def get_generar_plots_familia(self):
    state_data = self._read_state()
    return state_data.get('generar_plots_familia', True)
```

- Usar estos métodos para inicializar el switch al crear la vista de familia y guardar la preferencia cuando el usuario la cambia (a través de un callback simple `Input("familia-switch-generar-plots","value") -> Output(store?, ...)`).


7) Tests / QA ✅

- Unit tests sugeridos (en `tests/`):
  1. `test_ejecutar_calculo_familia_generar_plots_flag()` → ejecutar `ejecutar_calculo_familia_completa(..., generar_plots=False)` y verificar que:
     - No se generan figuras (figuras almacenadas en cache son None o listas vacías).
     - La función retorna `exito=True` y resultados numéricos válidos.
  2. `test_controller_calcular_familia_switch()` → simular callback `calcular_familia_completa` con `familia-switch-generar-plots` en `True/False` y verificar que `ejecutar_calculo_familia_completa` es llamado con el flag correcto (se puede usar monkeypatch o spies).
  3. `test_generar_vista_resultados_sin_plots()` → comprobar que `generar_vista_resultados_familia(..., generar_plots=False)` no incluye `dcc.Graph` ni componentes pesados.

- Manual QA:
  - Caso A: Switch ON → ejecutar "Calcular Familia" → verificar que se muestran plots y que tiempo es mayor.
  - Caso B: Switch OFF → ejecutar "Calcular Familia" → verificar que NO se generan plots y que tiempo es menor; verificar que no hay errores al renderizar la vista.
  - Probar `Cargar Cache` con switch ON y OFF y verificar comportamiento coherente (mostrar/ocultar gráficos según switch actual).


8) Documentación

- Añadir una breve nota en `docs/flujo_calcular_familia.md` y en `docs/implementacion_generar_plots.md` mencionando la nueva bandera UI `familia-switch-generar-plots` y cómo afecta la vista/cache.


## Archivos que se modificarían (lista corta) 📁
- components/vista_familia_estructuras.py  ← **añadir switch UI**
- controllers/familia_controller.py      ← **recibir State del switch** y **pasar valor** a utils
- utils/calcular_familia_logica_encadenada.py ← (opcional) aceptar pasar el flag hacia la generación de vista (ya soportado) y/o propagarlo a `generar_vista_resultados_familia`
- utils/calcular_familia_logica_encadenada.py ← **modificar firma** de `generar_vista_resultados_familia` para aceptar `generar_plots` y ajustar su comportamiento
- models/app_state.py (recomendado)   ← **set/get** para persistir la preferencia
- tests/test_familia_generar_plots.py  ← **nuevos tests**
- docs/* (flujo_calcular_familia.md, implementacion_generar_plots.md, y agregar este archivo)


---

## Consideraciones y notas finales ⚠️
- Mantén la **compatibilidad hacia atrás**: default `value=True` evita romper flujos existentes. Si se decide `False` por defecto, documentar y avisar al equipo.
- Asegurar que el front-end no intente renderizar imágenes `None` (proteger con condicionales en `generar_vista_resultados_familia` y en los `generar_resultados_*`).
- Verificar la **consistencia en cache**: cuando `generar_plots=False`, puede que exista cache con imágenes de ejecuciones previas (con plot). Decidir si `Cargar Cache` debe respetar la preferencia de visualización (recomiendo que sí: mostrar/ocultar según switch actual) y documentarlo.

---

Si quieres, puedo preparar un PR con cambios mínimos (UI + controller + tests básicos) para que lo revises y luego lo integramos (no implementaré sin tu OK). ✅
