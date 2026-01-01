# Implementación Familias de Estructuras

## Estado General: 🔧 INICIANDO IMPLEMENTACIÓN

**Fecha inicio**: 2025.12.31  
**Última actualización**: 2025.12.31

---

## Resumen de la Feature

Sistema completo para manejo de familias de estructuras que permite:
- Crear y editar familias con múltiples estructuras en formato tabla
- Calcular toda la familia de forma automatizada
- Análisis de costeo comparativo
- Análisis de vano económico
- Sistema de cache para familias completas

---

## Plan de Implementación

### FASE 1: Vista Familia de Estructuras ✅ COMPLETADO

#### 1.1 Estructura Base ✅ COMPLETADO
- [x] Crear `components/vista_familia_estructuras.py`
- [x] Crear `controllers/familia_controller.py`
- [x] Crear `utils/familia_manager.py`
- [x] Agregar entrada en menú HERRAMIENTAS > Calcular Familia

#### 1.2 Tabla de Parámetros Multi-Columna ✅ COMPLETADO
- [x] Reutilizar lógica de `vista_ajustar_parametros.py` modo tabla
- [x] Implementar columnas dinámicas (Estr.1, Estr.2, Estr.n...)
- [x] Botones Agregar/Eliminar Estructura
- [x] Campo NOMBRE FAMILIA
- [x] Campo CANTIDAD (entero, default=1)
- [x] Filtros por categoría (General, Cables, Cabezal, etc.)
- [x] Búsqueda de parámetros por nombre/descripción
- [x] Columna Categoría visible en tabla

#### 1.3 Modales y Edición ✅ COMPLETADO
- [x] Reutilizar clase ModalCelda de ajustar parámetros
- [x] Entrada numérica para valores numéricos
- [x] Modales para valores no numéricos (select, bool)
- [x] Validación de datos por columna
- [x] Callbacks para manejo de opciones y booleanos
- [x] IDs únicos para evitar conflictos (familia-modal-*)
- [x] Detección correcta tipos numéricos vs no-numéricos

#### 1.4 Persistencia 🔧 TESTING PENDIENTE
- [x] Formato `nombre_familia.familia.json`
- [x] Botón Guardar Familia (UI creado, callback pendiente)
- [x] Cargar/Guardar Como familia (UI creado, callback pendiente)
- [x] Menu desplegable familias existentes (UI creado, callback pendiente)

#### 1.5 Campos Especiales ✅ COMPLETADO
- [x] Campo TITULO como primera fila de tabla (editable por columna)
- [x] Campo cantidad como segunda fila de tabla (entero, default=1)
- [x] Columna Categoría visible en tabla
- [x] Filtros por categoría y búsqueda implementados

#### 1.6 Botones de Control 🔧 TESTING PENDIENTE
- [x] Botón Agregar Estructura (funcional)
- [x] Botón Eliminar Estructura (funcional)
- [x] Botón Cargar Columna (UI creado, callback pendiente)
- [x] Botón Guardar Familia (UI creado, callback pendiente)
- [x] Botón Cargar Familia (UI creado, callback pendiente)
- [x] Botón Calcular Familia (UI creado, callback pendiente)
- [x] Botón Cargar Cache (UI creado, callback pendiente)

### FASE 2: Cargar Estructura Existente ❌ PENDIENTE

#### 2.1 Modal Cargar Columna ❌ PENDIENTE
- [ ] Reutilizar modal cargar estructura de DB
- [ ] Selector de columna destino (Estr.1, Estr.2, etc)
- [ ] Completar columna con datos de estructura seleccionada

### FASE 3: Calcular Familia ❌ PENDIENTE

#### 3.1 Orquestación de Cálculos ❌ PENDIENTE
- [ ] Reutilizar lógica de `calcular_todo_controller.py`
- [ ] Ejecutar secuencia CMC>DGE>DME>ADC>SPH>FUNDACIONES>COSTEO
- [ ] Una ejecución por cada columna de estructura

#### 3.2 Presentación de Resultados ❌ PENDIENTE
- [ ] Sistema de pestañas por estructura
- [ ] Menu desplegable para selección de pestaña
- [ ] Mostrar nombre estructura (campo TITULO) en pestaña
- [ ] Output completo similar a Calcular Todo por pestaña

#### 3.3 Descarga HTML ❌ PENDIENTE
- [ ] Botón descargar HTML estructura individual
- [ ] Botón descargar HTML familia completa
- [ ] Reutilizar lógica de `descargar_html.py`

### FASE 4: Costeo de Familia ❌ PENDIENTE

#### 4.1 Cálculos de Costeo ❌ PENDIENTE
- [ ] Costo individual por estructura
- [ ] Costo parcial = costo individual × cantidad
- [ ] Costo global = suma de costos parciales

#### 4.2 Gráficos Comparativos ❌ PENDIENTE
- [ ] Gráfico barras: costos individuales (mayor a menor)
- [ ] Gráfico torta: costos parciales (individual × cantidad)
- [ ] Ejes: Estructura (TITULO) vs Costo en UM

#### 4.3 Integración HTML ❌ PENDIENTE
- [ ] Incluir sección costeo en HTML familia
- [ ] NO incluir en HTML individual

### FASE 5: Sistema de Cache ❌ PENDIENTE

#### 5.1 Cache de Familia ❌ PENDIENTE
- [ ] Extender `calculo_cache.py` para familias
- [ ] Archivo único con todos los datos de familia
- [ ] Hash de `familia.json` para validación

#### 5.2 Carga de Cache ❌ PENDIENTE
- [ ] Botón cargar cache familia
- [ ] Verificación hash familia vs cache
- [ ] Toast "cache no disponible" / "Hash no coincide, recalcular"

### FASE 6: Vano Económico ❌ PENDIENTE
**⚠️ SOLO IMPLEMENTAR CUANDO FASE 1-5 ESTÉN COMPLETAS Y FUNCIONALES**

#### 6.1 Vista Vano Económico ❌ PENDIENTE
- [ ] Crear `components/vista_vano_economico.py`
- [ ] Crear `controllers/vano_economico_controller.py`
- [ ] Cargar familia activa automáticamente
- [ ] Botón cargar familia desde DB

#### 6.2 Controles de Vano ❌ PENDIENTE
- [ ] Inputs: vano min, vano max, salto
- [ ] Generación lista vanos (min, min+salto, ..., max)
- [ ] Validación: siempre incluir min y max

#### 6.3 Cálculo Iterativo ❌ PENDIENTE
- [ ] Barra de progreso por vano calculado
- [ ] Ejecutar secuencia familia completa por cada vano
- [ ] Capturar solo resultados de costeo

#### 6.4 Gráficos Vano Económico ❌ PENDIENTE
- [ ] Gráfico curva: X=vano, Y=costo global familia
- [ ] Ajuste polinómico a curva
- [ ] Gráfico barras apiladas: X=vano, Y=costo por estructura

#### 6.5 Cache Vano Económico ❌ PENDIENTE
- [ ] Extender `calculo_cache.py` para Vano Económico
- [ ] Formato: `{nombre_familia}.calculoVE.json`
- [ ] Hash de validación: archivo `.familia.json`
- [ ] Botón cargar cache VE
- [ ] Toast "cache no disponible" / "Hash no coincide, recalcular"

#### 6.6 Descarga HTML Vano Económico ❌ PENDIENTE
- [ ] Incluir todos los resultados y gráficos
- [ ] Incluir tabla familia y ajustes vano

---

## Archivos a Crear/Modificar

### Nuevos Archivos
- `components/vista_familia_estructuras.py`
- `components/vista_vano_economico.py`
- `controllers/familia_controller.py`
- `controllers/vano_economico_controller.py`
- `utils/familia_manager.py`

### Archivos a Modificar
- `components/menu.py` - Agregar entrada HERRAMIENTAS > Calcular Familia
- `controllers/navigation_controller.py` - Routing nuevas vistas
- `utils/calculo_cache.py` - Extender para familias
- `utils/descargar_html.py` - Soporte descarga familia

---

## Patrones a Reutilizar

### De Vista Ajustar Parámetros
- Estructura tabla con columnas Parámetro, Símbolo, Unidad, Descripción
- Modales para valores no numéricos
- Entrada numérica con validación
- Colores y formatos de tabla

### De Vista Calcular Todo
- Secuencia completa CMC>DGE>DME>ADC>SPH>FUNDACIONES>COSTEO
- Orquestación de cálculos
- Manejo de errores en cadena
- Presentación de resultados

### De Sistema Cache
- Patrón hash para validación
- Guardado/carga JSON
- Mensajes toast para estados
- Formato `.calculoVE.json` para Vano Económico

### De Descarga HTML
- Generación HTML completo
- Inclusión de gráficos y tablas
- Formato de exportación

---

## Notas de Implementación

### Estructura Archivo Familia
```json
{
  "nombre_familia": "Familia Ejemplo",
  "fecha_creacion": "2025-12-31T10:00:00",
  "fecha_modificacion": "2025-12-31T10:00:00",
  "estructuras": {
    "Estr.1": {
      "cantidad": 1,
      "TITULO": "Estructura 1",
      // ... resto parámetros plantilla.estructura.json
    },
    "Estr.2": {
      "cantidad": 2,
      "TITULO": "Estructura 2",
      // ... resto parámetros plantilla.estructura.json
    }
  }
}
```

### Consideraciones Técnicas
- Reutilizar máximo código existente
- Mantener consistencia con patrones actuales
- Sistema de cache robusto para familias grandes
- Manejo de memoria para múltiples cálculos
- Validación de datos por columna
- Progreso visual para operaciones largas

---

## Próximos Pasos

1. **INMEDIATO**: Implementar FASE 1.1 - Estructura base
2. Revisar `vista_ajustar_parametros.py` modo tabla para reutilizar
3. Revisar `calcular_todo_controller.py` para reutilizar lógica
4. Crear estructura básica de archivos

---

## Log de Cambios

### 2025.12.31
- ✅ Documento creado
- ✅ Plan completo definido
- ✅ FASE 6 actualizada con cache VE
- ✅ FASE 1.1 y 1.2 implementadas (estructura base y tabla)
- ✅ FASE 1.3 implementada y testeada (modales con IDs únicos)
- ✅ FASE 1.5 implementada (TITULO y cantidad como filas de tabla)
- 🔧 FASE 1.4 y 1.6 UI creada, callbacks pendientes
- ❌ FASE 2-6 pendientes

---

**IMPORTANTE**: Este documento debe actualizarse después de cada cambio en la implementación. Marcar elementos completados con ✅ y pendientes con ❌.