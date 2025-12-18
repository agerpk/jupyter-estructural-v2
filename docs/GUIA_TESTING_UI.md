# GUÍA DE TESTING MANUAL - UI

## OBJETIVO
Verificar que todas las mejoras aplicadas funcionan correctamente a través de la interfaz de usuario.

---

## FLUJO DE TESTING COMPLETO

### 1. PREPARACIÓN
1. Iniciar aplicación: `python app.py`
2. Abrir navegador en `http://localhost:8050`
3. Cargar o crear estructura de prueba

### 2. TEST: CÁLCULO MECÁNICO DE CABLES (CMC)
**Objetivo**: Verificar que cargas se guardan en nodos

**Pasos**:
1. Ir a "Cálculo Mecánico de Cables"
2. Hacer clic en "Calcular"
3. Verificar que aparecen resultados
4. Verificar que se generan gráficos

**Verificación**:
- ✅ Resultados aparecen sin errores
- ✅ Gráficos se muestran correctamente
- ✅ Cache se guarda (mensaje de éxito)

**Posibles Errores**:
- ❌ Error: "No hay cargas asignadas" → Problema en asignación
- ❌ Gráficos no aparecen → Problema en cache JSON

---

### 3. TEST: DISEÑO GEOMÉTRICO DE ESTRUCTURA (DGE)
**Objetivo**: Verificar que nodos se crean correctamente

**Pasos**:
1. Ir a "Diseño Geométrico de Estructura"
2. Hacer clic en "Calcular"
3. Verificar que aparecen nodos
4. Verificar gráficos de estructura

**Verificación**:
- ✅ Lista de nodos aparece
- ✅ Gráfico de estructura se muestra
- ✅ Gráfico de cabezal se muestra
- ✅ Cache se guarda

**Posibles Errores**:
- ❌ Error: "nodes_key no existe" → Problema con property
- ❌ Nodos no aparecen → Problema en obtener_nodos_dict()

---

### 4. TEST: DISEÑO MECÁNICO DE ESTRUCTURA (DME)
**Objetivo**: Verificar que cargas se leen desde nodos y rotaciones se aplican

**Pasos**:
1. Ir a "Diseño Mecánico de Estructura"
2. Hacer clic en "Calcular"
3. Verificar tabla de reacciones
4. Verificar gráficos polares

**Verificación**:
- ✅ Tabla de reacciones aparece
- ✅ Valores de reacciones son razonables
- ✅ Gráfico polar se muestra
- ✅ Gráfico de barras se muestra

**Posibles Errores**:
- ❌ Error: "cargas_key no existe" → Problema en eliminación
- ❌ Error: "obtener_cargas_hipotesis" → Problema en lectura desde nodos
- ❌ Valores incorrectos → Problema en rotaciones

---

### 5. TEST: ÁRBOLES DE CARGA
**Objetivo**: Verificar que árboles se generan desde nodos

**Pasos**:
1. Ir a "Árboles de Carga"
2. Hacer clic en "Generar Árboles"
3. Verificar que aparecen imágenes
4. Verificar que hay una imagen por hipótesis

**Verificación**:
- ✅ Imágenes de árboles aparecen
- ✅ Flechas de cargas se muestran
- ✅ Panel de reacciones aparece
- ✅ Cache se guarda

**Posibles Errores**:
- ❌ Error: "cargas_key no existe" → Problema en arboles_carga.py
- ❌ Error: "_obtener_lista_hipotesis" → Problema en método
- ❌ Imágenes vacías → Problema en construcción de cargas_hipotesis

---

### 6. TEST: SELECCIÓN DE POSTE (SPH)
**Objetivo**: Verificar que reacciones se usan correctamente

**Pasos**:
1. Ir a "Selección de Poste"
2. Hacer clic en "Calcular"
3. Verificar que aparece configuración seleccionada
4. Verificar desarrollo de cálculo

**Verificación**:
- ✅ Configuración de postes aparece
- ✅ Desarrollo de cálculo se muestra
- ✅ Cache se guarda

**Posibles Errores**:
- ❌ Error en reacciones → Problema en DME
- ❌ Valores incorrectos → Problema en rotaciones

---

### 7. TEST: CALCULAR TODO
**Objetivo**: Verificar flujo completo automático

**Pasos**:
1. Ir a "Calcular Todo"
2. Hacer clic en "Ejecutar Cálculo Completo"
3. Esperar a que termine (puede tardar)
4. Verificar que todas las secciones aparecen

**Verificación**:
- ✅ CMC completo
- ✅ DGE completo
- ✅ DME completo
- ✅ SPH completo
- ✅ Árboles completos

**Posibles Errores**:
- ❌ Falla en algún paso → Revisar ese paso específico
- ❌ Gráficos no aparecen → Problema en cache JSON

---

### 8. TEST: EDITOR DE NODOS
**Objetivo**: Verificar que nodos editados se guardan correctamente

**Pasos**:
1. En DGE, hacer clic en "Editar Nodos"
2. Modificar coordenadas de un nodo
3. Hacer clic en "Guardar Cambios"
4. Recalcular DGE
5. Verificar que cambios se mantienen

**Verificación**:
- ✅ Cambios se guardan
- ✅ Nodos editados se aplican en recálculo
- ✅ Estructura se actualiza

**Posibles Errores**:
- ❌ Cambios no se guardan → Problema en serialización
- ❌ Nodos no se aplican → Problema en importar_nodos_editados()

---

## CHECKLIST DE VERIFICACIÓN

### Funcionalidad Básica
- [ ] CMC calcula sin errores
- [ ] DGE calcula sin errores
- [ ] DME calcula sin errores
- [ ] SPH calcula sin errores
- [ ] Árboles se generan sin errores
- [ ] Calcular Todo funciona completo

### Cargas Separadas por Tipo
- [ ] Cargas se asignan en nodos
- [ ] Peso, Viento, Tiro separados
- [ ] Suma de cargas es correcta

### Rotaciones
- [ ] Nodos con rotación funcionan
- [ ] Rotaciones se aplican en reacciones
- [ ] Valores son correctos

### Cache
- [ ] CMC guarda cache
- [ ] DGE guarda cache
- [ ] DME guarda cache
- [ ] SPH guarda cache
- [ ] Árboles guardan cache
- [ ] Gráficos interactivos aparecen al cargar cache

### Compatibilidad
- [ ] Estructuras antiguas cargan correctamente
- [ ] Cache antiguo funciona
- [ ] No hay errores de compatibilidad

---

## ERRORES COMUNES Y SOLUCIONES

### Error: "cargas_key no existe"
**Causa**: Código antiguo intentando acceder a cargas_key
**Solución**: Buscar y actualizar referencia a usar nodos

### Error: "obtener_cargas_hipotesis no existe"
**Causa**: Nodo no tiene método
**Solución**: Verificar que NodoEstructural está importado correctamente

### Error: "nodes_key no existe"
**Causa**: Property no funciona
**Solución**: Verificar que @property está definido en EstructuraAEA_Geometria

### Gráficos no aparecen al cargar cache
**Causa**: Falta archivo JSON de Plotly
**Solución**: Verificar que se guarda tanto PNG como JSON

### Valores de reacciones incorrectos
**Causa**: Rotaciones no se aplican
**Solución**: Verificar que obtener_cargas_hipotesis_rotadas() se usa en DME

---

## TESTING DE REGRESIÓN

### Estructuras de Prueba
1. **Suspensión Recta Simple** - Caso básico
2. **Terminal Doble Terna** - Caso complejo
3. **Angular con Rotación** - Caso con rotaciones

### Verificar en Cada Estructura
- [ ] CMC genera resultados consistentes
- [ ] DGE genera nodos correctos
- [ ] DME genera reacciones razonables
- [ ] SPH selecciona postes adecuados
- [ ] Árboles muestran cargas correctas

---

## PRÓXIMOS PASOS

1. **Ejecutar testing manual** siguiendo esta guía
2. **Documentar errores** encontrados
3. **Corregir errores** uno por uno
4. **Re-testear** después de cada corrección
5. **Validar** con estructuras reales

---

**Tokens used/total (59% session). Monthly limit: <1%**
