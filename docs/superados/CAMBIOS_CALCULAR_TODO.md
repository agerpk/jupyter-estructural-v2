# Cambios en "Calcular Todo"

## Resumen de Mejoras Implementadas

### 1. ✅ Persistencia Completa
- **Implementación**: Los resultados se guardan en `{nombre_estructura}.calculoTODO.json`
- **Navegación**: Al reiniciar la app y volver a "Calcular Todo", se cargan automáticamente los resultados guardados
- **Vigencia**: Se verifica el hash de parámetros para determinar si los resultados siguen vigentes
- **Última vista**: La app recuerda que estabas en "Calcular Todo" y vuelve a esa vista al reiniciar

**Archivos modificados**:
- `utils/calculo_cache.py`: Agregados métodos `guardar_calculo_todo()` y `cargar_calculo_todo()`
- `controllers/navigation_controller.py`: Agregada lógica para cargar resultados guardados al navegar a "calcular-todo"
- `components/vista_calcular_todo.py`: Actualizada para mostrar resultados guardados si existen

### 2. ✅ Outputs Detallados de Todas las Vistas
"Calcular Todo" es una **interfaz** que ejecuta las rutinas existentes de cada vista y muestra sus outputs en secuencia:

- **CMC**: Ejecuta `ejecutar_calculo_cmc_automatico()` y muestra los 3 gráficos (Combinado, Conductor, Guardia)
- **DGE**: Ejecuta `calcular_diseno_geometrico()` y muestra todo su output (nodos, dimensiones, gráficos)
- **DME**: Ejecuta `calcular_diseno_mecanico()` y muestra todo su output (reacciones, gráficos polar y barras)
- **Árboles**: Ejecuta `generar_arboles_carga()` y muestra las primeras 6 hipótesis con sus diagramas
- **SPH**: Ejecuta `calcular_seleccion_postes()` y muestra información de postes seleccionados

**Archivos modificados**:
- `controllers/calcular_todo_controller.py`: Completamente reescrito para llamar a las funciones existentes de cada vista

### 3. ✅ Ejecución Automática de Todos los Pasos
- Todos los 5 pasos se ejecutan automáticamente en secuencia:
  1. CMC → 2. DGE → 3. DME → 4. **Árboles** → 5. **SPH**
- Cada paso usa los resultados del anterior (encadenamiento automático)
- Si CMC falla, se detiene (es crítico)
- Si Árboles o SPH fallan, se muestra advertencia pero no detiene el proceso

### 4. ✅ Descarga HTML
- Botón "Descargar HTML" convierte todos los outputs a un archivo HTML standalone
- Mantiene formato, imágenes (base64 embebidas) y estilos
- Incluye Bootstrap para mantener el diseño responsive

## Arquitectura de la Solución

### Principio de Diseño
"Calcular Todo" **NO duplica código**. Es una interfaz que:
1. Llama a las funciones existentes de cada vista
2. Concatena sus outputs en secuencia
3. Guarda el resultado completo en cache

### Flujo de Ejecución

```
Usuario hace clic en "Ejecutar Cálculo Completo"
    ↓
1. CMC → ejecutar_calculo_cmc_automatico() → Carga imágenes desde cache → Muestra
    ↓
2. DGE → calcular_diseno_geometrico() → Retorna html.Div completo → Muestra
    ↓
3. DME → calcular_diseno_mecanico() → Retorna html.Div completo → Muestra
    ↓
4. Árboles → generar_arboles_carga() → Genera diagramas → Muestra primeros 6
    ↓
5. SPH → calcular_seleccion_postes() → Calcula postes → Muestra selección
    ↓
Guarda TODO en {nombre}.calculoTODO.json
    ↓
Usuario reinicia app → Navega a "Calcular Todo" → Se cargan resultados automáticamente
```

### Carga Parcial de Resultados
Si al abrir la vista existen resultados parciales en cache:
- CMC: Se carga si existe y es vigente
- DGE: Se carga si existe y es vigente
- DME: Se carga si existe y es vigente
- Árboles: Se carga si existe y es vigente
- SPH: Se carga si existe y es vigente

Cada vista maneja su propia persistencia usando el sistema de cache existente.

## Estructura de Archivos Modificados

```
jupyter_estructural_v2/
├── utils/
│   └── calculo_cache.py                    [MODIFICADO] +2 métodos
├── controllers/
│   ├── navigation_controller.py            [MODIFICADO] +persistencia calcular-todo
│   └── calcular_todo_controller.py         [REESCRITO] +llamadas a vistas existentes
└── components/
    └── vista_calcular_todo.py              [MODIFICADO] +carga resultados guardados
```

## Funciones Reutilizadas

### De `geometria_controller.py`:
- `ejecutar_calculo_cmc_automatico(estructura_actual, state)` → Ejecuta CMC
- `calcular_diseno_geometrico(callback_context, n_clicks, estructura_actual)` → Ejecuta DGE

### De `mecanica_controller.py`:
- `calcular_diseno_mecanico(n_clicks, mostrar_sismo, estructura_actual)` → Ejecuta DME

### De `arboles_carga.py`:
- `generar_arboles_carga(estructura_mecanica, estructura_actual, ...)` → Genera árboles

### De `PostesHormigon.py`:
- `calcular_seleccion_postes(geometria, mecanica, ...)` → Calcula SPH

## Persistencia de Navegación

La app recuerda la última vista visitada:
- Se guarda en `data/navegacion_state.json`
- Al reiniciar, vuelve a la última vista
- Si era "Calcular Todo", carga los resultados guardados automáticamente

## Verificación de Vigencia

Cada vez que se cargan resultados guardados:
1. Se calcula hash MD5 de los parámetros actuales
2. Se compara con el hash guardado
3. Si coinciden → Resultados vigentes ✅
4. Si no coinciden → Se debe recalcular ⚠️

## Beneficios

1. **Sin Duplicación**: Reutiliza código existente de cada vista
2. **Mantenibilidad**: Si se mejora una vista, "Calcular Todo" se beneficia automáticamente
3. **Persistencia**: No se pierden cálculos largos al reiniciar
4. **Transparencia**: Se ven todos los outputs, no solo mensajes
5. **Automatización**: Un solo clic ejecuta todo el flujo
6. **Exportación**: Descarga HTML con todo el contenido formateado
