# Plan de acción: Mover Tabla de Familia a Modal 🔧

## Resumen ejecutivo ✅
- Problema: la tabla de `Familia de Estructuras` está paginada (`page_size=60`) y con más de 60 filas la paginación/UX se rompe. Los filtros/buscador y el botón para modificar **Estados Climáticos** están en la vista principal y esto complica la interacción con tablas grandes.
- Solución propuesta: mover la **tabla completa**, los **filtros/buscador** y el **botón de edición de estados climáticos** a un **modal persistente** (ej: `modal-tabla-familia`) que mantenga los mismos `id`s que hoy usa la app. Esto permite mantener la lógica de callbacks existente y, simultáneamente, mostrar la tabla sin paginación (usar `page_action='none'`) con virtualización y scroll interno para rendimiento.

---

## Alcance y restricciones 🔍
- Mantener los `id` actuales (`tabla-familia`, `filtro-categoria-familia`, `buscar-parametro-familia`, `btn-buscar-familia`, `btn-borrar-filtros-familia`, `btn-abrir-estados-familia`, `tabla-familia-original`, etc.) para no romper callbacks existentes.
- El modal debe estar siempre presente en el layout (is_open=False por defecto) para que los callbacks puedan registrarse en bootstrapping de Dash.
- Considerar rendimiento: para tablas grandes usar `virtualization=True` y `style_table={'maxHeight': '70vh', 'overflowY': 'auto', 'overflowX': 'auto'}`. Ver compatibilidad entre `virtualization` y `fixed_rows` (puede que sea necesario eliminar `fixed_rows` o probar alternativas para header "pegajoso").

---

## Cambios propuestos (alto nivel) 🛠️
1. Components (UI)
   - Añadir `crear_modal_tabla_familia()` en `components/vista_familia_estructuras.py` que devuelva `dbc.Modal` con:
     - Filtros: `filtro-categoria-familia`, `buscar-parametro-familia`, botones `btn-buscar-familia` y `btn-borrar-filtros-familia`.
     - Botón para editar estados climáticos `btn-abrir-estados-familia` (o mantener el existente dentro del modal).
     - `DataTable` con id `tabla-familia` configurada con **sin paginación** ( `page_action='none'` ), **virtualización** y `style_table` con altura máxima y scroll.
     - Mantener `dcc.Store` (ej. `tabla-familia-original`) y modales auxiliares existentes.
   - En la vista principal (card): reemplazar la zona de filtros y la tabla por un compact button `btn-abrir-tabla-familia` que abre el modal.

2. Controller (callbacks)
   - Añadir callback toggle para `modal-tabla-familia` (Input `btn-abrir-tabla-familia`, `modal-tabla-familia-cerrar`, Output `modal-tabla-familia.is_open`).
   - No cambiar IDs de los inputs/outputs de lógica existente (la lógica de filtrado que ya está en `familia_controller.py` debería funcionar sin cambios si los componentes mantienen sus IDs y existen en layout).
   - Revisar y ajustar cualquier callback que dependa de propiedades de DataTable relacionadas a la paginación (ej. si hay suposiciones de pagina activa) — actualmente no parece haber tal dependencia.

3. DataTable config (detalles técnicos)
   - Cambios iniciales propuestos: 
     - `page_action='none'` (muestra todas las filas en un scroll interno del modal)
     - `virtualization=True` (render parcial para rendimiento en tablas grandes)
     - `style_table={'maxHeight': '70vh', 'overflowY': 'auto', 'overflowX': 'auto'}`
     - Eliminar o revisar `fixed_rows={'headers': True}` si entra en conflicto con `virtualization` — probar alternativas (CSS sticky) si hace falta.

4. Estilos y UX
   - Asegurar header "sticky" si `fixed_rows` no es compatible con `virtualization` (usar `position: sticky` en `style_header` + wrapper con overflow).
   - Mantener capacidad de edición en celdas (`editable=True`) y sincronización (`tabla-familia-original` store).

5. Tests & Documentación
   - Añadir tests unitarios/funcionales (pytest + Dash testing) que verifiquen:
     - Apertura del modal con `btn-abrir-tabla-familia`.
     - Que `tabla-familia` existe dentro del modal y `page_action` es `none`.
     - Filtrado por categoría y búsqueda (los callbacks `filtrar_tabla_familia` siguen funcionando).
     - Guardado y propagación de `tabla-familia-original` con la tabla dentro del modal.
   - Actualizar `docs/flujo_calcular_familia.md` para reflejar nuevo flujo y documentar el nuevo modal.

---

## Plan de trabajo detallado (pasos numerados) 📋
1. Crear la nueva función `crear_modal_tabla_familia()` en `components/vista_familia_estructuras.py` y añadir template del modal (sin activar aún en UI). (0.5 día)
2. Reemplazar área de filtros/tabla en la vista principal por un botón `btn-abrir-tabla-familia` y añadir llamada para incluir `crear_modal_tabla_familia()` en el layout. (0.25 día)
3. Implementar callback toggle del `modal-tabla-familia` en `controllers/familia_controller.py` (seguir patrón de otros modales). (0.25 día)
4. Ajustar la configuración del `DataTable` (`page_action='none'`, `virtualization=True`, `style_table`) y probar en local con familias grandes. Registrar cualquier incompatibilidad `fixed_rows`/`virtualization` y prototipar alternativa. (0.5–1 día)
5. Añadir tests automatizados y actualizar docs como en sección anterior. (0.5 día)
6. QA manual: crear familia con > 500 filas (simuladas) y validar rendimiento, edición, filtrado, sincronización y guardado. Corregir issues. (1 día)

---

## Riesgos y mitigaciones ⚠️
- Riesgo: `virtualization` puede romper `fixed_rows` → Mitigación: probar `position: sticky` en `style_header` y usar wrapper `style_table` con scroll.
- Riesgo: rendering lento con miles de filas → Mitigación: mantener `virtualization=True`, y si es necesario, ofrecer opción para "cargar completa" o un warning cuando la familia supera umbral (ej 2000 filas).
- Riesgo: callbacks que asumían paginación específica → Mitigación: revisar callbacks y tests mencionados; en el repo actual no se observan dependencias directas de la paginación.

---

## Criterios de aceptación ✅
- La tabla debe abrirse desde un botón y mostrarse dentro de un modal.
- La tabla debe mostrar todas las filas sin paginación y permitir edición y filtrado síncrono con los callbacks actuales.
- Rendimiento aceptable con familias grandes (p. ej. 500 filas): scroll fluido y edición responsiva gracias a virtualización.
- Tests automatizados que verifiquen apertura de modal, existencia de la tabla en modal, comportamiento de filtros y persistencia de `tabla-familia-original`.

---

## Notas finales / Siguientes pasos 💡
- Si estás de acuerdo, puedo preparar un PR con cambios en pequeños commits (UI modal + toggle callback → DataTable adjustments → tests/documentación) y marcar la PR como `🔧 TESTING PENDIENTE` para que la prueben localmente según el protocolo del proyecto.

---

Documento generado el: 2026-01-28
