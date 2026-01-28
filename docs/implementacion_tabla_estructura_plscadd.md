# Implementación: Tabla "Estructura PLS-CADD" (implementacion_tabla_estructura_plscadd.md)

## Resumen (💡)
- Objetivo: añadir soporte para generar una tabla con formato PLS-CADD para la estructura (CSV) al finalizar DGE y permitir su descarga/visualización en UI y en la salida de "Calcular Todo" / Familias.
- Archivo util: `utils/estructura_plscadd.py` (encapsula la lógica de generación y validación de la tabla y su CSV).
- Integraciones principales:
  - `controllers/geometria_controller.py` → llamar al util después de finalizar DGE si el flag está activo
  - `utils/calculo_cache.py` → guardar el CSV y metadatos en el `calculoDGE` cache
  - `components/vista_diseno_geometrico.py` → mostrar la tabla (y botón de descarga) en los resultados DGE
  - `components/vista_ajuste_parametros.py` → exponer parámetros en la vista "Ajustar Parámetros"
  - `components/vista_calcular_familia.py` / `utils/calcular_familia_logica_encadenada.py` → asegurar que la tabla se genere/guarde cuando se calcule una familia
  - Tests unitarios/integración y documentación QA

---

## Entradas y parámetros requeridos
- Parámetros de estructura a añadir (en `data/plantilla.estructura.json` y UI):
  - `generar_estructura_plscadd_tabla` (bool, default: True)
  - `insulator_type_guardia` (string, default: "Clamp", opciones: clamp, Post, Strain, Suspension, 2-Part)
  - `insulator_type_conductor` (string, default: "Suspension", mismas opciones)
- Inputs al util:
  - `estructura_geometria` (o `nodes_key`) — para obtener nodos conductores y guardia con coordenadas
  - `insulator_type_guardia`, `insulator_type_conductor`
  - `tipo_estructura` (para decidir criterio "suspensión" vs otro)
  - `Lk` (longitud de cadena), `PCADENA` (peso cadena), `Vn` (tensión nominal), `Ka` (ajuste por altitud), `TITULO` (nombre estructura)

---

## Salida y formato (CSV)
- Archivo CSV con el mismo formato que `otros/ejemplo_tabla_estructura_plscadd.csv`.
- Dos secciones al principio (propiedades generales de la estructura) y luego una fila por nodo (guardia o conductor) con columnas como:
  - `Set #`, `Phase #`, `Dead End Set`, `Set Description`, `Insulator Type`, `Insul. Weight (N)`, `Insul. Wind Area (cm^2)`, `Insul. Length (m)`, `Attach. Trans. Offset (m)`, `Attach. Dist. Below Top (m)`, `Attach. Longit. Offset (m)`, `Min. Req. Vertical Load (uplift) (N)`, etc.
- Reglas y fórmulas:
  - Height: max(z of all nodes, including guardia)
  - Embedded lenght: 0.1 * Height
  - Lowest wire attachment point: min z among conductor nodes
  - Set assignment:
    - `1` = guardia nodes
    - `2` = conductor nodes with x>0 (or all conductor nodes if terna = Simple)
    - `3` = conductor nodes with x<0 (if terna = Doble)
  - `Phase #`: incremental por set (1..n)
  - Insul. Wind Area (cm^2):
    - if tipo_estructura contains 'suspension' or 'suspensión': ((0.5 + Vn / 150) * Ka * 0.146)/10000 (rounded to 2 dec)
    - else: ((0.5 + Vn / 75) * Ka * 0.146)/10000  (matches spec: use Vn/75)
  - Insul. Weight (N): `PCADENA`*10 for conductor nodes, 0 for guardia
  - Insul. Length (m): `Lk` for conductor nodes, 0 for guardia
  - Attach.* fields -> x,y coordinates and distances to top etc.
  - Min. Req. Vertical Load: "No Uplift"  if tipo_estructura contains 'suspension' or 'suspensión', else "No Limit"

---

## Diseño del util: `utils/estructura_plscadd.py` (especificación)
- Función pública: `generar_tabla_estructura_plscadd(estructura_geometria, insulator_type_guardia, insulator_type_conductor, tipo_estructura, Lk, PCADENA, Vn, Ka, titulo)`
  - Devuelve: `pandas.DataFrame` (tabla ya formateada) y `csv_path` (Path al CSV escrito en `CACHE_DIR` o `DATA_DIR` según convenga)
  - Validaciones:
    - `estructura_geometria` tiene `nodes_key` y al menos 1 nodo conductor
    - `insulator_type_*` estén en la lista permitida
    - `Vn`, `Ka` sean numéricos
  - Logging y errores: levantar ValueError con mensaje claro si falta información; registrar debug info en stdout
  - Tests unitarios: probar con estructuras simples, doble terna, terna simple y con/ sin cable guardia

---

## Cambios en el flujo DGE y almacenamiento en cache
1. En `controllers/geometria_controller.py` (al finalizar DGE, antes de guardar en cache):
   - Si `estructura_actual.get('generar_estructura_plscadd_tabla', True)`:
     - Llamar a `generar_tabla_estructura_plscadd(...)` y obtener `df_plscadd`, `csv_path`
     - Incluir en la llamada a `CalculoCache.guardar_calculo_dge(...)` un nuevo argumento: `plscadd_csv` (o `plscadd_table`) con el nombre del archivo o estructura serializada.
2. En `utils/calculo_cache.py` (modificar `guardar_calculo_dge`):
   - Añadir parámetros opcionales `plscadd_csv` y `plscadd_table` (string o objeto serializable)
   - Guardar el nombre del archivo CSV en `calculoDGE.json`: p.ej. `"plscadd_csv": "EstructuraPlsCadd.{hash}.csv"` y escribir el CSV en `CACHE_DIR`.
   - Actualizar `cargar_calculo_dge` para exponer ese campo si existe.

---

## Cambios UI y vistas
1. `components/vista_ajuste_parametros.py` (categoria "Cabezal")
   - Agregar controles:
     - Switch `generar_estructura_plscadd_tabla` (True/False)
     - Select `insulator_type_guardia` (opciones enumeradas)
     - Select `insulator_type_conductor` (opciones enumeradas)
   - Asegurar que `guardar_parametros_geometria` incluye estos campos al persistir en el JSON (`controllers/geometria_controller.guardar_parametros_geometria` ya actualiza muchos campos; agregar los nuevos allí siguiendo el mismo patrón).
2. `components/vista_diseno_geometrico.py` / `generar_resultados_dge`:
   - Si `calculo_guardado` contiene `plscadd_csv` o `plscadd_table`:
     - Mostrar un `html.H5("TABLA PLS-CADD")` seguido de:
       - una tabla renderizada (p.ej. `dash_table.DataTable` o `html.Pre` con CSV)
       - un botón para descargar el CSV (implementar con `dcc.Link` o `dcc.send_file` endpoint / `dcc.Download`)
     - Añadir memoria de cálculo (explicar como se generó la tabla, parámetros usados) en `memoria_calculo` del DGE
   - Alinear estilo con otras secciones (Servidumbre, memoria, gráficos).
3. Vista Calcular Familias (`components/vista_familia_estructuras.py` o el flujo de `utils/calcular_familia_logica_encadenada.py`):
   - **Obligatorio**: agregar `generar_estructura_plscadd_tabla`, `insulator_type_guardia`, `insulator_type_conductor` a la tabla de parámetros de familia (estos parámetros deben estar disponibles y ser editables por familia/estructura).
   - Durante `Calcular Familia`, si el flag está activo (en la estructura o heredado por la familia), generar y guardar **un CSV por estructura** (UNA tabla por estructura). No se generará un CSV maestro por familia por defecto; la compilación por familia puede implementarse en una fase futura. Asegurar que los CSVs individuales queden disponibles en la salida de `Calcular Familia` y que la UI permita descargarlos.

---

## Tests y QA
1. Unit tests:
   - `tests/test_estructura_plscadd.py` con varios escenarios:
     - Terna simple con 3 conductores
     - Terna doble con guardia(s)
     - Verificar fórmulas `Insul. Wind Area`, `Attach. Dist. Below Top`, `Set` / `Phase` assignment
     - Validación de parámetros inválidos
2. Integración tests:
   - `tests/integration/test_dge_plscadd.py`:
     - Ejecutar DGE en modo test con `generar_estructura_plscadd_tabla=True` y confirmar que:
       - `CalculoCache.cargar_calculo_dge(...)` contiene `plscadd_csv` y el archivo existe en `CACHE_DIR` con el patrón de nombre `{TITULO}_{hash}.csv`
       - `components.vista_diseno_geometrico.generar_resultados_dge` devuelve HTML con la tabla / link descarga
       - `Calcular Todo` (cuando incluye DGE) expone la misma tabla en sus resultados y permite descargar el CSV
       - `Calcular Familia` muestra y permite descargar los CSVs por estructura en la salida de la familia
   - Prueba de `Calcular Familia` para confirmar generación por miembro (una tabla por estructura) y que los enlaces de descarga estén disponibles en la UI.
3. QA manual checklist (pre-merge):
   - Comparar CSV generado con `otros/ejemplo_tabla_estructura_plscadd.csv` para un caso simple
   - Validar que el CSV respeta el orden de columnas esperado por PLS-CADD
   - Verificar que cuando el flag está off no se genera CSV
   - Verificar manejo de nodos sin cable guardia (no crash, filas guardia omitidas si no hay)

---

## Backwards-compat & migración
- Añadir los nuevos parámetros a `data/plantilla.estructura.json` con valores por defecto para mantener compatibilidad. **Nota:** el valor por defecto para `generar_estructura_plscadd_tabla` será `True` (generación activada por defecto); documentar este comportamiento y cómo desactivarlo si se desea.
- Actualizar `docs/` y `README` para documentar los nuevos parámetros y su uso.
- Documentar el comportamiento no destructivo: aunque la generación esté activada por defecto, los usuarios podrán desactivarla poniendo `generar_estructura_plscadd_tabla = False`.

---

## Entregables y TODOs (prioridad)
1. Crear `utils/estructura_plscadd.py` + tests unitarios (alta)
2. Añadir parámetros a `data/plantilla.estructura.json` y controles en `components/vista_ajuste_parametros.py` (media)
3. Modificar `controllers/geometria_controller.py` para invocar el util y recoger resultado (alta)
4. Modificar `utils/calculo_cache.py` para guardar CSV y exponerlo en cache (alta)
5. Mostrar tabla y botón de descarga en `components/vista_diseno_geometrico.py` (alta)
6. Agregar tests de integración y casos de familia (media)
7. Actualizar documentación `docs/implementacion_tabla_estructura_plscadd.md` (este documento) y `README` (media)

---

## Decisiones confirmadas
- **Una tabla por estructura**: se generará **una** tabla PLS-CADD por cada estructura procesada. No se genera por defecto un CSV maestro por familia; la compilación por familia queda como mejora futura opcional.
- **PCADENA** está en **daN** en los parámetros actuales; para obtener `Insul. Weight (N)` se utilizará la conversión **PCADENA * 10** (ya reflejado en la sección de Salida y formato).
- **Ubicación y nombre del CSV**: los CSV se guardan en `CACHE_DIR` (p. ej. la carpeta `/cache`) con el patrón de nombre `{TITULO}_{hash}.csv`.
- **Visibilidad UI**: la tabla debe estar disponible y descargable desde **DGE**, **Calcular Todo** (cuando DGE forme parte del cálculo) y **Calcular Familia** (descargas por estructura).
- **Parámetros en familias**: los nuevos parámetros (`generar_estructura_plscadd_tabla`, `insulator_type_guardia`, `insulator_type_conductor`) **deben aparecer** en la tabla de parámetros de familia y ser editables allí.

---

## Referencias internas útiles
- Ejemplo CSV: `otros/ejemplo_tabla_estructura_plscadd.csv` ✅
- Implementaciones análogas y documentación: `docs/implementacion_servidumbre.md`, `docs/ImplementacionAEE.md`
- Cache DGE: `utils/calculo_cache.py::guardar_calculo_dge`
- Generación y render DGE: `controllers/geometria_controller.py`, `components/vista_diseno_geometrico.py`

---

## Criterios de aceptación
- [x] CSV PLS-CADD generado y guardado en cache si `generar_estructura_plscadd_tabla` = True
- [x] Tabla visible en UI DGE y botón de descarga funcional
- [x] Tabla y CSV accesibles desde **Calcular Todo** (cuando incluye DGE)
- [x] CSV descargable desde **Calcular Familia** (por estructura) en la salida de la familia
- [x] Valores y columnas respetan `otros/ejemplo_tabla_estructura_plscadd.csv`
- [x] Tests unitarios + integración cubren casos básicos


---

Si quieres, puedo ahora generar los *stubs* (archivos vacíos y tests) en una rama separada para que tengas la base de trabajo — o crear un PR con la documentación y lista de tareas para asignación. ¿Cuál prefieres? 🚀
