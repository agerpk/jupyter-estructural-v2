# Plan de acción: hipotesis_a5_dme_15pc_si_lk_mayor_2_5 ✅

**Resumen corto** 💡
- Añadir el parámetro **`hipotesis_a5_dme_15pc_si_lk_mayor_2_5`** (default: `true`) al `plantilla.estructura.json` (categoría: DME).
- Si el parámetro está activo, cuando se procese la hipótesis **A5 - "Tiro unilateral reducido"** (Suspensión, Suspensión angular), y la longitud de cadena `Lk > 2.5m`, se debe aplicar **`reduccion_cond = 0.15`** (en lugar de `0.20`) al calcular las componentes de tiro para conductores.

---

## Objetivos del cambio 🎯
1. Implementar el nuevo parámetro en plantilla y UI.
2. Inyectar la lógica condicional en la asignación de cargas (DME / EstructuraAEA_Mecanica) para que A5 use 15% cuando corresponda.
3. Garantizar cobertura en tests, memoria de cálculo y trazabilidad (logs y output DME).
4. Mantener compatibilidad hacia atrás (estructuras sin el parámetro usan default True).

---

## Alcance técnico (archivos a tocar) 🔧
1. data/plantilla.estructura.json
   - Añadir: `"hipotesis_a5_dme_15pc_si_lk_mayor_2_5": true` (top-level, categorizado como DME en docs).

2. EstructuraAEA_Geometria.py
   - Leer/almacenar el parámetro desde `parametros` (o `parametros.get(...)`) en `__init__`:
     - `self.hipotesis_a5_dme_15pc_si_lk_mayor_2_5 = parametros.get('hipotesis_a5_dme_15pc_si_lk_mayor_2_5', True)`
   - Así la lógica de DME puede consultarlo vía `self.geometria.hipotesis_a5_dme_15pc_si_lk_mayor_2_5`.

3. components/vista_diseno_mecanico.py
   - Añadir un `Switch` para el parámetro en la sección "Parámetros de Configuración" (label claro). Mostrar `value=estructura_actual.get('hipotesis_a5_dme_15pc_si_lk_mayor_2_5', True)`.

4. controllers/mecanica_controller.py
   - En el callback `guardar_parametros_mecanica`, añadir `State` y persistir el nuevo parámetro en `estructura_actualizada` y guardar archivo `{TITULO}.estructura.json` (igual que otros parámetros).

5. EstructuraAEA_Mecanica.py
   - En `asignar_cargas_hipotesis()` (donde se procesan las hipótesis): detectar la hipótesis A5 (por ejemplo `if codigo_hip == 'A5' or config.get('desc','').lower().startswith('tiro unilateral'):`) y, si
     - `self.geometria.hipotesis_a5_dme_15pc_si_lk_mayor_2_5 is True` AND
     - `self.geometria.lk > 2.5`
     entonces antes de usar `config_tiro.get('reduccion_cond', ...)` sobrescribir `reduccion_cond = 0.15`.
   - Registrar un `logger.info` / `print` indicando la aplicación: e.g. "Aplicando hipotesis A5: Lk=3.00 > 2.5 => reduccion_cond = 0.15"
   - Aplicar la misma regla donde se obtiene `reduccion_guardia` si aplica (según la especificación, el requisito comenta solo conductores; documentar en la implementación si afecta guardias).

6. utils / memoria DME (utils/descargar_html.py o donde se genera memoria DME)
   - Añadir línea en la memoria de cálculo DME que indique: "A5: reducción conductor aplicada = 15% (Lk > 2.5 m)" si la condición se cumple. Esto aumenta trazabilidad.

7. Tests (tests/)
   - Nuevo test: `tests/test_dme_hipotesis_a5_lk.py` con al menos 3 casos:
     1. Lk = 3.0, parámetro True -> comprobar que `reduccion_cond` usada en cálculo final es 0.15 y que las fuerzas en nodos se corresponden (o que aparece el log/memoria correspondiente).
     2. Lk = 2.5, parámetro True -> comprobar que sigue siendo 0.20.
     3. Lk = 3.0, parámetro False -> comprobar que sigue siendo 0.20.
   - Actualizar tests de integración DME si dependen de valores exactos de A5.

8. Documentación
   - Añadir este doc en `/doc/hipotesis_a5_dme_15pc_si_lk_mayor_2_5.md` (este archivo).
   - Añadir nota breve en `BITÁCORA` y en `docs` (si existe sección DME/Hipótesis) indicando la referencia normativa AEA95301-2007 y la regla aplicada.

---

## Consideraciones de diseño y decisiones 🧭
- Detección de A5: usar `codigo_hip == 'A5'` o `config['desc'].lower().startswith('tiro unilateral')` para no depender exclusivamente del código; documentar la condición en el comentario. Esto evita romperse si el código cambia, pero hace la coincidencia menos estricta.
- Compatibilidad: si el parámetro no está presente en un `*.estructura.json`, default a `True` (tal como pedido). Esto respeta estructuras antiguas.
- Scope: la regla afecta por especificación a **conductores** en la hipótesis A5 (Suspensión, Suspensión desvío). Si en el futuro se decide que también afecta guardias, documentarlo y hacer prueba adicional.
- Logs: añadir un `logger.info` con la condición y el valor aplicado para facilitar debugging y trazabilidad en la salida de DME.

---

## Criterios de aceptación (QA) ✅
1. Unit tests pasan (nuevos + existentes): 100% green en la parte afectada.
2. Pruebas manuales en UI:
   - Con `hipotesis_a5_dme_15pc_si_lk_mayor_2_5 = True` y `Lk = 3.0`, ejecutar DME -> verificar en memoria DME / logs que la reducción aplicada para A5 es 15% y que las reacciones/tiros cambian en consecuencia con respecto a 20%.
   - Cambiar el parámetro a `False` -> ejecutar DME -> verificar que vuelve a 20%.
3. Generación de cache DME incluye el nuevo parámetro en el hash de parámetros (ya contemplado si se guarda `estructura_actual` completo).
4. La entrada aparece en la UI (Switch) en la vista DME y se guarda correctamente en `{TITULO}.estructura.json`.

---

## Notas de implementación (paso a paso) 🧭
1. Añadir campo a `data/plantilla.estructura.json`.
2. Añadir atributo en `EstructuraAEA_Geometria.__init__` (leer desde `parametros`).
3. Añadir `Switch` en `components/vista_diseno_mecanico.py` y `State` + persistencia en `controllers/mecanica_controller.py`.
4. Implementar la condición en `EstructuraAEA_Mecanica.asignar_cargas_hipotesis()` antes de que se utilice `reduccion_cond`.
5. Añadir log y memoria DME message.
6. Añadir/actualizar tests en `tests/`.
7. Ejecutar linters y pruebas locales (unit tests y test_simple.py/test_app.py que no deben romper).
8. Hacer PR con descripción corta y referencia a este doc; pedir revisión de especialista DME.

---

## Riesgos y mitigaciones ⚠️
- Riesgo: cambiar reducción afecta resultados de DME/selección de postes (SPH). Mitigación: validar casos de referencia y comparar antes/después.
- Riesgo: omitir la persistencia del nuevo parámetro en UI; mitigación: cobertura de test que guarde parámetros.

---

## Estimación de tiempo (aprox.) ⏱️
- Implementación de código + UI + tests: 3–5 horas
- Revisión y QA (manual): 1–2 horas

---

Si te parece bien, puedo generar los cambios en ramas separadas y preparar los tests y el PR. ¿Comienzo implementando los cambios propuestos? 🔧