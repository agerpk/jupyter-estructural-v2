# Implementación Familias de Estructuras

## Estado General: ✅ FASE 1-3 COMPLETADAS - 🔧 TESTING PENDIENTE FASE 4

**Fecha inicio**: 2025.12.31  
**Última actualización**: 2026.01.01

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

#### 1.4 Persistencia ✅ COMPLETADO
- [x] Formato `nombre_familia.familia.json`
- [x] Botón Guardar Familia (funcional)
- [x] Cargar/Guardar Como familia (funcional)
- [x] Menu desplegable familias existentes (funcional)
- [x] Conversión bidireccional tabla ↔ JSON
- [x] Validación y creación directorio /data
- [x] Toast notifications para operaciones CRUD
- [x] Persistencia de familia activa en estado ✅ NUEVO
- [x] Archivo `familia_actual.json` para estado ✅ NUEVO

#### 1.5 Campos Especiales ✅ COMPLETADO
- [x] Campo TITULO como primera fila de tabla (editable por columna)
- [x] Campo cantidad como segunda fila de tabla (entero, default=1)
- [x] Columna Categoría visible en tabla
- [x] Filtros por categoría y búsqueda implementados

#### 1.6 Botones de Control ✅ COMPLETADO
- [x] Botón Agregar Estructura (funcional)
- [x] Botón Eliminar Estructura (funcional)
- [x] Botón Cargar Columna (funcional) ✅ NUEVO
- [x] Botón Guardar Familia (funcional)
- [x] Botón Guardar Como (funcional)
- [x] Botón Eliminar Familia (funcional con modal confirmación) ✅ NUEVO
- [x] Botón Calcular Familia (🔧 UI creado, callback pendiente)
- [x] Botón Cargar Cache (🔧 UI creado, callback pendiente)
- [x] Separación de controles: Tabla vs Familia ✅ NUEVO
- [x] Modal de confirmación para eliminar familia ✅ NUEVO

### FASE 2: Cargar Estructura Existente ✅ COMPLETADO

#### 2.1 Modal Cargar Columna ✅ COMPLETADO
- [x] Modal con selección de estructura desde DB
- [x] Selector de columna destino (Estr.1, Estr.2, etc)
- [x] Carga de estructuras disponibles desde /data
- [x] Completar columna con datos de estructura seleccionada
- [x] Toast notifications para éxito/error
- [x] Validación de selección requerida

### FASE 3: Calcular Familia ✅ COMPLETADO

#### 3.1 Orquestación de Cálculos ✅ COMPLETADO
- [x] Reutilizar lógica de `calcular_todo_controller.py`
- [x] Ejecutar secuencia CMC>DGE>DME>ADC>SPH>FUNDACIONES>COSTEO
- [x] Una ejecución por cada columna de estructura
- [x] Callback `calcular_familia()` implementado
- [x] Función `ejecutar_calculo_estructura_completa()` implementada
- [x] Manejo de archivos temporales para cada estructura

#### 3.2 Presentación de Resultados ✅ COMPLETADO
- [x] Sistema de pestañas por estructura
- [x] Mostrar nombre estructura (campo TITULO) en pestaña
- [x] Output completo similar a Calcular Todo por pestaña
- [x] Función `crear_vista_resultados_familia()` implementada
- [x] Función `crear_contenido_estructura()` implementada
- [x] Callback para manejo de pestañas activas
- [x] Área de resultados `resultados-familia` en vista

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

1. **INMEDIATO**: Implementar FASE 4 - Costeo de Familia (gráficos comparativos)
2. **SIGUIENTE**: Implementar FASE 5 - Sistema de Cache
3. **LUEGO**: Completar FASE 3.3 - Descarga HTML
4. **FINAL**: Implementar FASE 6 - Vano Económico (solo cuando FASE 1-5 estén OK)

---

## Log de Cambios

### 2026.01.01
- ✅ Documento creado
- ✅ Plan completo definido
- ✅ FASE 6 actualizada con cache VE
- ✅ FASE 1.1 y 1.2 implementadas (estructura base y tabla)
- ✅ FASE 1.3 implementada y testeada (modales con IDs únicos)
- ✅ FASE 1.4 completada (CRUD + persistencia estado familia actual)
- ✅ FASE 1.5 implementada (TITULO y cantidad como filas de tabla)
- ✅ FASE 1.6 completada (CRUD + Eliminar con modal + separación controles)
- ✅ Menú HERRAMIENTAS > Calcular Familia agregado
- ✅ Navegación y badge familia implementados
- ✅ Archivo familia de prueba creado: PSJ_Prueba1.familia.json
- ✅ Cache deletion protege archivos .familia.json
- ✅ Botón Eliminar Familia con modal de confirmación
- ✅ Persistencia de familia activa en `familia_actual.json`
- ✅ Estado sincronizado entre navegación y operaciones CRUD
- ✅ Controles separados: Tabla (Agregar/Eliminar/Cargar Columna) vs Familia (Guardar/Eliminar/Calcular/Cache)
- ✅ FASE 2.1 implementada (Modal Cargar Columna funcional)
- ✅ Botón Cargar Columna con modal de selección estructura/columna
- ✅ Carga de datos de estructura existente en columna seleccionada
- ✅ FASE 3.1 y 3.2 implementadas (Calcular Familia con pestañas)
- ✅ Callback `calcular_familia()` con orquestación completa
- ✅ Sistema de pestañas con resultados por estructura
- ✅ Reutilización EXACTA de lógica de `calcular_todo_controller.py`
- ✅ Área de resultados integrada en vista familia
- ✅ Manejo correcto de AppState singleton y estructura activa
- ✅ Creación de archivos `.estructura.json` y `.hipotesismaestro.json` reales
- ✅ Secuencia completa: CMC>DGE>DME>Árboles>SPH>Fundación>Costeo
- ✅ Gestión de cache y archivos intermedios idéntica a Calcular Todo
- ✅ Display correcto de primera pestaña por defecto
- ✅ Mensajes de error reales sin placeholders ni datos inventados
- 🔧 Fix aplicado: Corrección de callback de pestañas para evitar error 'dict' object has no attribute 'style'
- 🔧 Fix aplicado: Agregados parámetros de viento faltantes (Vmax, Vmed, t_hielo, temp_max_zona) para evitar errores CMC
- 🔧 Fix aplicado: Agregados parámetros adicionales de cálculo (Zco, Zcg, Zca, Zes, Cf_*, PCADENA, etc.) requeridos por Cable_AEA
- 🔧 Fix aplicado: Reutilización exacta de lógica calcular_todo_controller.py sin imports innecesarios
- 🔧 Fix aplicado: Corrección crítica en `ejecutar_calculo_como_calcular_todo()` - usar datos directos de familia en lugar de cargar desde archivo
- 🔧 TESTING PENDIENTE: Usuario debe verificar que cálculos se ejecuten sin errores
- ❌ FASE 3.3, 4-6 pendientes

---

**IMPORTANTE**: Este documento debe actualizarse después de cada cambio en la implementación. Marcar elementos completados con ✅ y pendientes con ❌.