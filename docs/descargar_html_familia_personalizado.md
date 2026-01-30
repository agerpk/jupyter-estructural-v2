# 2026.01.30 — Plan de acción: Descargar HTML Personalizado de Familia ✅

## Resumen
- **Objetivo:** Agregar en la vista *Calcular Familia* un botón y modal para descargar un HTML personalizado que incluya sólo las secciones seleccionadas del output actual (CMC; DGE, DME, árboles de carga, etc.).
- **Lugar de la lógica:** `utils/descargar_html_familia_personalizado.py` (funciones públicas para construir y devolver el HTML listo para descarga).

---

## Alcance
- Mostrar un botón **"Descargar html seleccionando contenido"** junto al output en la vista *Calcular Familia*.
- Abrir un **modal** con una lista dinámica de **checkboxes** que refleje sólo las secciones y subsecciones presentes en el output actual.
- Al presionar **"Descargar HTML"**: generar el HTML con el mismo formato que el HTML actual, pero sólo con las secciones seleccionadas, y descargarlo automáticamente.
- Botón **"Cancelar"** para cerrar el modal sin cambios.

**No implementa** cambios en el formato del HTML, ni en la lógica de cálculo: sólo filtra y compone el HTML existente.

---

## Diseño general (visión rápida) 💡
1. **Detección de secciones disponibles:** obtener la lista de secciones/subsecciones a partir de la misma fuente que genera el output HTML actual (preferible) o, como fallback, parsear el HTML generado.
2. **Interfaz:** añadir botón y modal (componentes Dash) en la UI de *Calcular Familia*.
3. **Callbacks:** 3 callbacks:
   - abrir modal y cargar checkboxes dinámicamente,
   - controlar selección de checkboxes (almacenar selección en `dcc.Store` o estado del modal),
   - generar HTML y devolver el archivo para descarga.
4. **Utilidad:** `utils/descargar_html_familia_personalizado.py` con funciones para construir el HTML final reutilizando las mismas funciones/plantillas que generan el HTML completo.

---

## Tareas detalladas (paso a paso) 🔧

## Detalles técnicos obligatorios 🔩
- **SectionDescriptor (contrato):** definir una estructura que describa cada sección y subsección disponible. Campos sugeridos:
  - `id` (str): identificador único legible
  - `key` (str): clave usada para mapear a funciones generadoras
  - `label` (str): texto a mostrar en el modal
  - `orden` (int): orden de presentación en el HTML
  - `parent_id` (Optional[str]): id del padre si es subsección
  - `generator_func_name` (Optional[str]): nombre de la función/registro que produce la sección
  - `present_flag` (bool): indicador rápido de si la sección existe en el output actual

- **Cómo detectar secciones disponibles (estrategia preferida y fallback):**
  1. Preferir un *generator registry* o las funciones existentes que generan cada sección (reutilizar `generator_func_name` y consultar si produce contenido para la familia dada).
  2. Si no existe registry, añadir metadatos al proceso que crea el `output` (ej. lista de secciones en el `AppState` o en el objeto familia).
  3. Fallback razonable: parsear el HTML actual con `BeautifulSoup` buscando headings con atributos `data-section` o ids convencionales (ej. `id="section-dge"`). Agregar tests que exijan el uso de la estrategia 1/2 cuando sea posible.

- **Manejo de plots y figuras:**
  - Política de caché: exigir que las figuras de Plotly se guarden en cache con **PNG** y **JSON** (seguir convención del repo: `fig.write_image()` y `fig.write_json()`).
  - En `construir_html_personalizado`:
    - Buscar archivos PNG/JSON en cache. Si faltan, intentar regenerar la figura usando el generator correspondiente.
    - Embebedar la imagen en el HTML como `data:image/png;base64,...` para garantizar un único archivo descargable.
    - Para gráficas interactivas: incluir el JSON de Plotly en el HTML y el script para renderizar con Plotly.js; si se prefiere un HTML estático, insertar PNG como fallback.
  - Tests específicos: comprobar que el HTML resultante contiene `<img src="data:image/png;base64,` o incluye el bloque JSON de Plotly.

- **IDs y callbacks recomendados (nombrado consistente):**
  - Botón: `btn-descargar-html-personalizado`
  - Modal: `modal-descargar-html-familia`
  - Checklist: `chk-secciones-html-familia`
  - Store: `store-seleccion-secciones-html`
  - Componente descarga: `download-html-personalizado` (usar `dcc.Download` o endpoint Flask con `send_file`)

- **Callbacks (detalle de comportamiento):**
  1. Click en `btn-descargar-html-personalizado` → abrir `modal-descargar-html-familia` y actualizar `chk-secciones-html-familia` llamando a `listar_secciones_disponibles(familia_id)`.
  2. Cambios en `chk-secciones-html-familia` → opcionalmente actualizar `store-seleccion-secciones-html`.
  3. Click en "Descargar HTML" dentro del modal → validar selección, llamar a `construir_html_personalizado(familia_data, selected_sections)`, y devolver el archivo vía `dcc.send_bytes`/`dcc.send_file` o `dcc.Download`.
  - Manejar errores (generación fallida, plots no regenerables) mostrando alertas/toasts al usuario.

- **Control de tamaño y UX:**
  - Si el HTML resultante supera un umbral (ej. 10 MB), mostrar una advertencia y requerir confirmación.
  - Deshabilitar botón "Descargar" si no hay secciones seleccionadas; mostrar mensaje explicativo.

- **Tests adicionales a incluir:**
  - Unit tests que verifiquen el mapeo `SectionDescriptor.key -> generator` y que `listar_secciones_disponibles` detecte los keys esperados.
  - Unit tests que aseguren que `construir_html_personalizado` embebe correctamente PNG base64 y/o incluye JSON de Plotly según configuración.
  - Integration test que simule el callback de descarga y valide que el archivo devuelto contiene sólo las secciones seleccionadas en el orden correcto.

### 1) Investigación (tarea mínima previa)
- Buscar la implementación actual de "Descargar HTML de familia" y las funciones/plantillas que componen el HTML. Identificar los puntos de reuso (ej. funciones que generan secciones individuales).
- Archivos de interés: buscarlos en `utils/`, `controllers/` y donde se generan los outputs/familia HTML.

### 2) Crear utilitario
- Archivo: `utils/descargar_html_familia_personalizado.py`.
- Exportar funciones principales:
  - `listar_secciones_disponibles(familia_id_or_data) -> List[SectionDescriptor]` — devuelve una lista de secciones y sus subsecciones (id, label, orden, key para reusar generators).
  - `construir_html_personalizado(familia_data, selected_sections) -> bytes` — compone el HTML, reutilizando los generadores por-sección; asegura mismo formato y embebe imágenes/figuras como lo hace la versión actual.
  - posibilidad: `build_and_write_temp_file(...)` si es más sencillo devolver un fichero temporal.
- Reutilizar helpers existentes para los gráficos (asegurar PNG/JSON o inline base64 según convenga) para mantener compatibilidad con el HTML actual.

### 3) UI: botón y modal
- Añadir botón **`Descargar html seleccionando contenido`** en la vista *Calcular Familia* (sugerido: `components/vista_calcular_familia.py` o la vista correspondiente dentro de `views/` o `components/` según patrón del proyecto).
- Nuevo componente: `components/modal_descargar_html_familia.py` (o incluir en la vista si prefieren no fragmentar). Este modal contendrá:
  - título descriptivo,
  - listado de `dcc.Checklist` (o checkboxes individuales) generado dinámicamente a partir de `listar_secciones_disponibles(...)`.
  - botones **"Descargar HTML"** y **"Cancelar"**.
- UX: por defecto seleccionar todas las secciones (opcional) y desactivar el botón de descargar si no hay secciones seleccionadas (o mostrar aviso si está vacío).

### 4) Callbacks y controlador
- Crear callbacks en un controlador nuevo o existente (seguir patrón `register_callbacks(app)` en `controllers/`).
- Callbacks necesarios:
  1. **Abrir modal**: botón -> abre modal y solicita la lista de secciones. Puede obtener la lista desde `AppState()` o solicitando al servidor (callback que llama a `listar_secciones_disponibles`).
  2. **Actualizar selección**: actualizar un `dcc.Store` con las secciones seleccionadas (opcional).
  3. **Generar y descargar**: al pulsar "Descargar HTML" -> llamar a `construir_html_personalizado(...)` y despachar la descarga (usar `dcc.send_bytes` / `dcc.send_file` o un endpoint Flask / `dcc.Download`).
- Manejar errores (secciones no disponibles o fallo en generación) devolviendo mensajes en la UI.

### 5) Tests y QA
- Unit tests para `utils/descargar_html_familia_personalizado.py`:
  - test que `listar_secciones_disponibles` detecte correctamente secciones y subsecciones en diferentes casos (familia con X secciones, familia con menos secciones, etc.).
  - test que `construir_html_personalizado` incluya/excluya secciones según `selected_sections` y conserve el formato esperado (comprobar fragmentos HTML clave de cada sección).
- Test de integración (simulado): prueba que el callback de descarga devuelve un archivo con contenido correcto.
- Manual QA checklist (ver más abajo).

### 6) Documentación y PR
- Añadir este plan a `docs/descargar_html_familia_personalizado.md` (hecho).
- Incluir cambios en el CHANGELOG o `docs/` y en la lista de features.
- Añadir un pequeño tutorial de uso en la doc de la vista *Calcular Familia* (capturas o pasos rápidos).

---

## Casos de borde y consideraciones ⚠️
- Si el usuario NO selecciona ninguna sección, bloquear descarga o mostrar aviso.
- Asegurarse de que la generación de HTML maneja correctamente imágenes/figuras (embebidas o rutas relativas). Si los gráficos se requieren como archivos adicionales, embebedado base64 es preferible para un único HTML descargable.
- Grandes outputs pueden generar archivos pesados: evaluar compresión o advertencia al usuario.
- Mantener la compatibilidad con cualquier caching existente (no romper reglas de `utils/calculo_cache.py`).

---

## QA Manual (pasos rápidos) ✅
1. Abrir la vista *Calcular Familia* para una familia conocida.
2. Ver el nuevo botón junto al output.
3. Abrir modal y verificar que las secciones listadas coinciden con el output actual.
4. Seleccionar una combinación de secciones, pulsar "Descargar HTML" y abrir el archivo descargado.
5. Verificar que el HTML contiene sólo las secciones seleccionadas y mantiene el formato original (gráficos visibles, tablas correctas).
6. Repetir con todas las secciones seleccionadas y con ninguna (ver comportamiento esperado).

---

## Criterios de aceptación (mínimos) 🎯
- El botón y el modal existen y se muestran en la vista *Calcular Familia*.
- El modal lista exactamente las secciones y subsecciones presentes en el output actual.
- La descarga genera un HTML con sólo las secciones seleccionadas y mantiene el mismo formato del HTML existente.
- Tests automáticos cubren la utilidad de generación (unit/integration).

---

## Estimación (vueltas) ⏱️
- Investigación y descubrimiento: 0.5 - 1 día
- Implementación utils + tests unitarios: 1 - 1.5 días
- Implementación UI (modal + callbacks): 0.5 - 1 día
- Integración y tests de integración + QA manual: 0.5 - 1 día
- Total estimado: 2.5 - 4.5 días (dependiendo de caché y reuso de generadores existentes)

---

## Notas finales
- Reusar al máximo el código que ya genera el HTML completo para garantizar compatibilidad del formato.
- Seguir los patrones del repo: `register_callbacks(app)` en `controllers/`, use `AppState()` para data persistente cuando corresponda, y respetar cache y persistencia de `utils/calculo_cache.py` si la generación de gráficos necesita reconstrucción.

> Si quieres, puedo continuar y abrir un PR con la estructura básica (agregar el util, el modal y los callbacks esqueleto), o generar pruebas unitarias iniciales antes de la implementación completa. ✨
