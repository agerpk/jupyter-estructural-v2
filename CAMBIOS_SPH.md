# Cambios Implementados - Selección de Postes de Hormigón (SPH)

## Resumen
Se implementó la funcionalidad completa de Selección de Postes de Hormigón (SPH) según AEA-95301-2007, siguiendo la arquitectura MVC de la aplicación.

## Cambios Realizados

### 1. Barra de Menú Fija (Sticky)
**Archivo:** `views/main_layout.py`
- Se agregó `sticky="top"` y `style={"zIndex": 1000}` al componente `dbc.Navbar`
- La barra de menú ahora permanece fija en la parte superior al hacer scroll

### 2. Nuevo Botón en Menú CALCULAR
**Archivo:** `components/menu.py`
- Se agregó el ítem "Selección Poste Hormigón (SPH)" con id `menu-seleccion-poste`
- Ubicado en el menú desplegable CALCULAR, después de un divisor

### 3. Nueva Vista de Selección de Postes
**Archivo:** `components/vista_seleccion_poste.py` (NUEVO)
- Vista completa con parámetros editables:
  - `FORZAR_N_POSTES`: Slider de 0 (Auto) a 3
  - `FORZAR_ORIENTACION`: Select con opciones No/Longitudinal/Transversal
  - `PRIORIDAD_DIMENSIONADO`: Select con altura_libre/longitud_total
  - `ANCHO_CRUCETA`: Input numérico en metros
- Botones:
  - "Guardar Parámetros": Guarda en el JSON de estructura
  - "Calcular": Ejecuta el cálculo SPH
- Área de resultados que muestra:
  - Resumen ejecutivo con configuración seleccionada
  - Desarrollo completo del cálculo (texto capturado de `imprimir_desarrollo_seleccion_postes`)

### 4. Controlador de Selección de Postes
**Archivo:** `controllers/seleccion_poste_controller.py` (NUEVO)
- Callback `guardar_parametros_sph`: Guarda parámetros en estructura.json
- Callback `calcular_seleccion_poste`:
  - Verifica que exista cálculo DME vigente
  - Recupera objetos de geometría y mecánica del AppState
  - Ejecuta `PostesHormigon.calcular_seleccion_postes()`
  - Captura salida de `imprimir_desarrollo_seleccion_postes()`
  - Calcula hash de parámetros para verificación de vigencia
  - Guarda resultado en `{nombre}.calculoSPH.json`
  - Muestra resultados en la vista

### 5. Persistencia de Cálculos SPH
**Archivo:** `utils/calculo_cache.py`
- Se agregaron métodos:
  - `guardar_calculo_sph()`: Guarda cálculo en JSON
  - `cargar_calculo_sph()`: Carga cálculo desde JSON
- Formato del archivo: `{nombre_estructura}.calculoSPH.json`
- Incluye:
  - `parametros`: Parámetros usados en el cálculo
  - `hash_parametros`: Hash MD5 para verificar vigencia
  - `resultados`: Diccionario con resultados del cálculo
  - `desarrollo_texto`: Texto completo del desarrollo

### 6. Navegación
**Archivo:** `controllers/navigation_controller.py`
- Se agregó Input para `menu-seleccion-poste`
- Se agregó parámetro `n_clicks_sph` en función `navegar_vistas`
- Se agregó caso `elif trigger_id == "menu-seleccion-poste"`:
  - Guarda estado de navegación como "seleccion-poste"
  - Carga cálculo guardado si existe
  - Verifica vigencia del cálculo
  - Retorna vista de selección de postes
- Se agregó caso en carga inicial para restaurar vista SPH

### 7. Registro del Controlador
**Archivo:** `app.py`
- Se importó `seleccion_poste_controller`
- Se registró con `seleccion_poste_controller.register_callbacks(app)`

## Flujo de Uso

1. Usuario navega a CALCULAR → Selección Poste Hormigón (SPH)
2. Vista muestra parámetros de configuración actuales
3. Usuario puede:
   - Ajustar parámetros con sliders/selects
   - Guardar parámetros (actualiza estructura.json)
   - Calcular (ejecuta cálculo SPH)
4. Al calcular:
   - Verifica que exista DME vigente
   - Ejecuta cálculo usando objetos de geometría/mecánica
   - Guarda resultado en `{nombre}.calculoSPH.json`
   - Muestra resultados en pantalla
5. Al volver a entrar:
   - Si existe cálculo guardado y hash coincide → muestra resultados
   - Si hash no coincide → muestra vista vacía (debe recalcular)

## Verificación de Vigencia

El sistema verifica automáticamente si el cálculo guardado sigue vigente:
- Calcula hash MD5 de los parámetros actuales
- Compara con hash guardado en el JSON
- Si coinciden → cálculo vigente (muestra resultados)
- Si no coinciden → cálculo obsoleto (debe recalcular)

## Integración con Código Existente

La implementación utiliza directamente:
- `PostesHormigon.calcular_seleccion_postes()`: Método existente en celda 006
- `PostesHormigon.imprimir_desarrollo_seleccion_postes()`: Captura salida para mostrar
- Objetos `EstructuraAEA_Geometria` y `EstructuraAEA_Mecanica` del AppState
- Sistema de persistencia existente (CalculoCache)

## Archivos Modificados

1. `views/main_layout.py` - Barra sticky
2. `components/menu.py` - Nuevo botón SPH
3. `controllers/navigation_controller.py` - Navegación a SPH
4. `utils/calculo_cache.py` - Persistencia SPH
5. `app.py` - Registro de controlador

## Archivos Nuevos

1. `components/vista_seleccion_poste.py` - Vista SPH
2. `controllers/seleccion_poste_controller.py` - Lógica SPH

## Notas Técnicas

- La vista sigue el mismo patrón que las vistas de CMC, DGE y DME
- Los parámetros editables corresponden a la sección "CONFIGURACIÓN SELECCIÓN DE POSTES" de la celda 000
- El cálculo requiere que DME esté ejecutado previamente (necesita objetos de geometría y mecánica)
- La persistencia usa el mismo sistema de hash que los otros cálculos
- El desarrollo completo se captura redirigiendo stdout temporalmente
