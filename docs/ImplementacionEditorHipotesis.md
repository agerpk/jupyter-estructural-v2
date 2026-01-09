# Implementación: Editor de Hipótesis (Plan de Acción)

## Resumen ejecutivo ✅
La feature "Editor de Hipótesis" permitirá crear, editar, guardar, cargar y aplicar hipótesis estructurales (viento, tiro, peso, sobrecarga, flags especiales) en los cálculos de DME y otras vistas. Las hipótesis se agruparán por `TIPO_ESTRUCTURA` y se almacenarán como archivos JSON en `data/hipotesis/`. Habrá una "hipótesis activa" en la app (fallback a `plantilla.hipotesis.json` si falta).

---

## Objetivos 🎯
- Proveer CRUD completo para archivos de hipótesis (UI + persistencia).
- Mantener compatibilidad con el flujo actual (DME, Arboles, SPH, AEE) y facilitar pruebas con hipótesis personalizadas.
- Asegurar validación de esquema y mensajes de error claros cuando falten parámetros.

---

## Estructura de archivos y convenciones 🔧
- Carpeta: `data/hipotesis/`
- Archivo plantilla: `data/hipotesis/plantilla.hipotesis.json` (basado en `HipotesisMaestro_Especial.py`).
- Nombres: `{TITULO_ESTRUCTURA}.hipotesis.json` o alternativa `{nombre_proyecto}.hipotesis.json` si se desea agrupar por proyecto.
- Formato interno: dict con claves por `TIPO_ESTRUCTURA` (ej. "Suspensión Recta") y dentro códigos `A0`, `A1`, ... con campos:
  - `desc` (string)
  - `viento`: { `estado`, `direccion`, `factor` } | null
  - `tiro`: { `estado`, `patron`, `reduccion_cond`, `reduccion_guardia`, `factor_cond?`, `factor_guardia?` }
  - `peso`: { `factor`, `hielo` }
  - `sobrecarga`: number | null
  - flags especiales (opcional): `{ "doble-terna-una-terna-activa": true }`

---

## Esquema (ejemplo simplificado)
```json
{
  "Suspensión Recta": {
    "A0": { "desc": "EDS (TMA)", "viento": null, "tiro": {"estado":"TMA","patron":"bilateral"}, "peso": {"factor":1.0,"hielo":false}, "sobrecarga": null }
  }
}
```

---

## Flujo de uso en la aplicación 🔁
1. Al cargar la vista DME o cualquier vista que necesite hipótesis, el controlador solicitará la **hipótesis activa** (ver sección Integración).
2. Si no existe archivo de hipótesis activa o no es válido: mostrar mensaje tipo **ARCHIVO DE HIPOTESIS NO ENCONTRADO, USANDO PLANTILLA** y usar `plantilla.hipotesis.json`.
3. Edición: el usuario abre el **Editor de Hipótesis**, modifica y guarda → se escribe a `data/hipotesis/{nombre}.hipotesis.json` y se setea como hipótesis activa.
4. Operaciones disponibles: Guardar (overwrite), Guardar como (nuevo nombre), Cargar desde DB, Importar/Exportar local (descargar/subir JSON), Eliminar.

---

## Integración con DME y `EstructuraAEA_Mecanica` ⚙️
- Antes de `asignar_cargas_hipotesis`, cargar la hipótesis activa:
  - `hipotesis = HipotesisManager.cargar_hipotesis_activa(nombre, path, plantilla)`
- Validar que la hipótesis contenga las claves necesarias para el `TIPO_ESTRUCTURA` actual.
  - Si faltan parámetros requeridos, devolver error visible en UI (toast/modal) y log.
- Implementar soporte para flags especiales (ej.: `doble-terna-una-terna-activa`): `asignar_cargas_hipotesis` debe leer la flag y, cuando esté activa, anular las cargas (o aplicar reducción) en los conductores del lado indicado.

---

## Cambios en `utils/hipotesis_manager.py` 🗃️
- Añadir funciones/operaciones:
  - `listar_hipotesis()` → retorna archivos en `data/hipotesis/`.
  - `cargar_hipotesis_por_nombre(nombre)` → carga y valida esquema.
  - `guardar_hipotesis(nombre, datos, meta)` → guarda con metadata (hash, fecha, autor opcional).
  - `establecer_hipotesis_activa(nombre)` → guarda referencia en `config` (ej.: `DATA_DIR / "hipotesis_activa.json"`) o en `AppState`.
  - `importar_hipotesis_local(filepath)` y `exportar_hipotesis_local(nombre, dest)`.
- Manejar validación de esquema y mensajes de error claros.

---

## UI: componente Editor de Hipótesis 🔨
- Lugar: `components/editor_hipotesis.py` (ampliar) y nueva vista `views/vista_hipotesis.py` o añadir pestaña en Ajustar Parámetros.
- Requisitos de UI:
  - Lista de archivos de hipótesis (select/list) con botón Cargar, Eliminar, Nuevo, Guardar Como, Descargar, Subir.
  - Editor modal para cada `TIPO_ESTRUCTURA` con campos equivalentes a `crear_editor_hipotesis_campo()` ya existente — reutilizar.
  - Validación en cliente (presencia de campos clave) y en servidor (validación final antes de guardar).
  - `dcc.Store(id='hipotesis-actuales', data=hipotesis)` para mantener en memoria la hipótesis activa.

---

## Callbacks / Controllers 🔁
- Nuevo `controllers/hipotesis_controller.py` con:
  - `register_callbacks(app)` que maneje CRUD (guardar, cargar, guardar como, importar/exportar) y actualice `hipotesis-actuales` y `AppState`.
  - Integración con toasts y mensajes de confirmación.
- Ajustes en `navigation_controller.py` y `mecanica_controller.py` para usar `HipotesisManager` cuando corresponda.

---

## Ejemplo: `doble-terna-una-terna-activa` (implementación sugerida)
- Flag en la hipótesis: `"doble-terna-una-terna-activa": { "lado": "L" }` o `{ "lado": "R" }`.
- En `asignar_cargas_hipotesis` antes de aplicar cargas, evaluar flag y si está presente:
  - Para cada `nodo_nombre` que corresponda al lado inactivo: setear `peso_x,y,z = 0` y `viento_x,y,z = 0` (o aplicar factor 0).
  - Registrar en logs la aplicación de la regla.

---

## Criterios de aceptación ✅
- UI permite CRUD completo y operaciones locales (import/export).
- `HipotesisManager` lista y carga archivos desde `data/hipotesis/` y mantiene referencia de la hipótesis activa.
- DME y vistas relacionadas usan la hipótesis activa y responden con mensajes si faltan datos.
- Tests unitarios e integración cubren los casos críticos.

---

## Plan de trabajo sugerido (sprints cortos)
1. Sprint 1 (1-2 días): Documentación + plantilla (`plantilla.hipotesis.json`).
2. Sprint 2 (2-3 días): `HipotesisManager` (listar, cargar, guardar, activar) + tests unitarios básicos.
3. Sprint 3 (3-5 días): UI Editor (lista, modal de edición, guardar/guardar como/importar/exportar) + callbacks.
4. Sprint 4 (2-3 días): Integración con DME y ajustes en `EstructuraAEA_Mecanica` para flags especiales + tests de integración.
5. Sprint 5 (1-2 días): QA, documentación final, PR y revisión.

---

## Observaciones finales 💡
- Mantener compatibilidad hacia atrás (si `hipotesis_maestro` en código existe, usarlo como plantilla inicial).
- Evitar placeholders en producción: validar y rechazar/avisar si faltan datos.
- A futuro: añadir versión en metadata del archivo de hipótesis para migraciones y control de cambios.

### Compatibilidad y reglas adicionales ⚠️
- **Protección de cache:** `utils/borrar_cache.py` **no debe** eliminar la carpeta `data/hipotesis/` ni los archivos de hipótesis (`{nombre_proyecto}.hipotesis.json`). Actualizar `borrar_cache()` para excluir directorios protegidos (p. ej. `hipotesis`) y asegurar que los archivos en `data/hipotesis/` se mantengan intactos.
- **Ubicación y nombre de archivos:** La convención será `data/hipotesis/{nombre_proyecto}.hipotesis.json` (usar este path en `HipotesisManager`). Evitar escribir archivos `.hipotesismaestro.json` en la raíz de `data/` para no mezclarlos con caché.
- **Mensaje de uso:** Al cargar/activar una hipótesis, imprimir/loggear `USANDO HIPÓTESIS {nombre}` y mostrar un toast informativo en la UI. Además, **incluir este mensaje en el encabezado/metadatos de todos los HTML descargables** generados por la app (informes, descargas de resultados, familia, etc.).
- **Eliminar edición duplicada:** Hay ediciones de hipótesis actualmente accesibles desde la vista DME (`components/vista_diseno_mecanico.py` y callbacks en `controllers/mecanica_controller.py`). Estas deben **eliminarse** (botón/funcionalidad de "Modificar Hipótesis" y callbacks de guardado en DME) para evitar duplicidad: toda edición debe centralizarse en la nueva vista/Editor de Hipótesis. En la vista DME solo dejar un botón que *abra* la vista de Editor o navegue a ella.
- **Reemplazo total del sistema:** El sistema antiguo quedará totalmente reemplazado por el nuevo (no coexistirán ambos). Añadir un paso de migración y un mensaje de deprecación en el código para facilitar la transición.
- **Callbacks y allow_duplicate:** Al mover o reubicar callbacks asegúrate de evitar errores `DuplicateCallback`. Revisar todos los callbacks que usan `allow_duplicate=True` y ajustar según sea necesario; añadir tests que detecten errores de registro de callbacks.

---

> Documento generado como plan de acción. Si quieres, puedo: 1) crear `data/hipotesis/plantilla.hipotesis.json` ahora a partir de `HipotesisMaestro_Especial.py`, 2) modificar `utils/borrar_cache.py` para excluir `data/hipotesis/` y añadir tests, o 3) abrir una rama y crear PR con los cambios completos (gestor, UI y tests). Dime qué prefieres y procedo."