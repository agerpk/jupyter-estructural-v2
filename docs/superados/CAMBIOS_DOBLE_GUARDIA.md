# Cambios para Soportar 2 Cables de Guardia Diferentes

## Resumen
Se ha rediseñado la aplicación para soportar 2 cables de guardia diferentes, uno en los nodos de la derecha (coord. x positiva) y otro en los nodos de la izquierda (coord. x negativa), para casos donde CANT_HG = 2.

## Estructura Creada
**Archivo:** `KACHI-1x220-Sst-0a1500.estructura.json`

**Configuración:**
- TERNA: Simple
- DISPOSICION: horizontal
- TENSION: 220 kV
- CANT_HG: 2
- Cable conductor: AlAc 435/55
- Cable guardia 1 (derecha): Ac 70
- Cable guardia 2 (izquierda): OPGW 44F70s 24FO 120mm2

## Archivos Modificados

### 1. `data/KACHI-1x220-Sst-0a1500.estructura.json`
- ✅ Agregado campo `cable_guardia2_id` con valor "OPGW 44F70s 24FO 120mm2"
- ✅ Configurado `cable_guardia_id` con valor "Ac 70"

### 2. `data/plantilla.estructura.json`
- ✅ Agregado campo `cable_guardia2_id` con valor `null` por defecto
- Este campo será opcional y solo se usará cuando CANT_HG = 2

### 3. `utils/calculo_objetos.py`
**Cambios en la clase CalculoObjetosAEA:**

- ✅ Agregado atributo `self.cable_guardia2 = None` en `__init__`
- ✅ Modificado método `crear_objetos_cable()`:
  - Lee el campo `cable_guardia2_id` de la configuración
  - Valida que el cable exista en la base de datos
  - Si CANT_HG = 2 y existe cable_guardia2_id, crea el segundo objeto Cable_AEA
  - Agrega el segundo cable a la librería de cables
  - Retorna información de ambos cables de guardia

- ✅ Modificado método `crear_todos_objetos()`:
  - Incluye el nombre del segundo cable de guardia en el mensaje de éxito

### 4. `components/vista_ajuste_parametros.py`
**Cambios en la vista de parámetros:**

- ✅ Agregado selector para `cable_guardia2_id` en el bloque "CABLES Y CONDUCTORES"
- ✅ Agregadas descripciones claras:
  - `cable_guardia_id`: "Cable guardia 1 (derecha, x+)"
  - `cable_guardia2_id`: "Cable guardia 2 (izquierda, x-)"
- ✅ Agregado `cable_guardia2_id` a las opciones disponibles

## Lógica de Funcionamiento

### Cuando CANT_HG = 1
- Solo se usa `cable_guardia_id`
- `cable_guardia2_id` se ignora (puede ser null)
- Comportamiento idéntico al anterior

### Cuando CANT_HG = 2
- Se usa `cable_guardia_id` para el cable de la derecha (x+)
- Se usa `cable_guardia2_id` para el cable de la izquierda (x-)
- Si `cable_guardia2_id` es null, se usa el mismo cable para ambos lados
- Si `cable_guardia2_id` está definido, se crean 2 objetos Cable_AEA diferentes

## Compatibilidad hacia atrás
✅ **Totalmente compatible**
- Estructuras existentes sin `cable_guardia2_id` seguirán funcionando
- El campo es opcional y se maneja con valor null por defecto
- La lógica verifica la existencia del campo antes de usarlo

## Archivos Modificados (Continuación)

### 5. `utils/calculo_mecanico_cables.py` ✅
**Cambios realizados:**
- ✅ Renombrado `self.df_guardia` → `self.df_guardia1`
- ✅ Agregado `self.df_guardia2` y `self.resultados_guardia2`
- ✅ Calcula guardia 2 si `cable_guardia2` existe
- ✅ Pasa ambos resultados de guardia a `ListadorCargas`
- ✅ Retorna `df_guardia1` y `df_guardia2` en resultados

### 6. `ListarCargas.py` ✅
**Cambios realizados:**
- ✅ Parámetro `cable_guardia` → `cable_guardia1` y `cable_guardia2`
- ✅ Sufijos actualizados: `Pcg` → `Pcg1`, `Pcg2`
- ✅ Sufijos actualizados: `Vcg` → `Vcg1`, `Vcg2`
- ✅ Sufijos actualizados: `cg` → `cg1`, `cg2` en tiros
- ✅ Genera cargas para ambos cables de guardia
- ✅ Método `generar_lista_cargas()` acepta `resultados_guardia2` opcional

### 7. `EstructuraAEA_Mecanica.py` ✅
**Cambios realizados:**
- ✅ Parámetro `resultados_guardia` → `resultados_guardia1` + `resultados_guardia2` (opcional)
- ✅ Variables `peso_guardia_base` → `peso_guardia1_base`, `peso_guardia2_base`
- ✅ Variables `tiro_guardia_base` → `tiro_guardia1_base`, `tiro_guardia2_base`
- ✅ Lógica para asignar cable correcto según posición del nodo:
  - HG1 o x > 0 (derecha) → usa guardia1
  - HG2 o x < 0 (izquierda) → usa guardia2
- ✅ Sufijos de viento dinámicos: `Vcg1`, `Vcg2`, `Vcg1med`, `Vcg2med`
- ✅ Viento oblicuo suma ambos guardias cuando es bilateral

## Próximos Pasos Pendientes

### Archivos que aún necesitan actualización:
1. **EstructuraAEA_Geometria.py** - Asignar cable_guardia1 y cable_guardia2 desde geometría
2. **plot_flechas.py** - Graficar ambos cables de guardia con colores diferentes
3. **arboles_carga.py** - Considerar cargas de ambos cables de guardia
4. **memoria_calculo_dge.py** - Incluir información de ambos cables en la memoria
5. **Controllers** - Actualizar callbacks para manejar df_guardia1 y df_guardia2
6. **EstructuraAEA_Graficos.py** - Graficar ambos cables de guardia

### Validaciones recomendadas:
- Verificar que cuando CANT_HG = 2, ambos cables estén definidos
- Alertar al usuario si cable_guardia2_id es null cuando CANT_HG = 2
- Validar compatibilidad mecánica entre ambos cables de guardia

## Resumen de Cambios en Sufijos

### Antes (1 cable de guardia):
- `cable_guardia` → Cable de guardia único
- `df_guardia` → DataFrame de resultados
- `resultados_guardia` → Dict de resultados
- Sufijos: `g`, `cg`, `Pcg`, `Vcg`

### Después (2 cables de guardia):
- `cable_guardia` → `cable_guardia1` (derecha, x+)
- `cable_guardia2` → Cable de guardia 2 (izquierda, x-)
- `df_guardia1`, `df_guardia2` → DataFrames separados
- `resultados_guardia1`, `resultados_guardia2` → Dicts separados
- Sufijos: `g1`, `g2`, `cg1`, `cg2`, `Pcg1`, `Pcg2`, `Vcg1`, `Vcg2`

## Testing
Para probar la nueva funcionalidad:
1. Cargar la estructura `KACHI-1x220-Sst-0a1500.estructura.json`
2. Verificar que en "Ajustar Parámetros" aparezcan ambos selectores de cables de guardia
3. Ejecutar "Calcular Todo" y verificar que se creen 3 objetos Cable_AEA
4. Revisar los logs para confirmar que ambos cables de guardia se procesan correctamente
5. Verificar que ListarCargas genere cargas con sufijos g1 y g2

## Notas Técnicas
- Los cables de guardia comparten los mismos parámetros de viento (Vmax, Zcg, Cf_guardia)
- Cada cable tiene sus propias propiedades mecánicas (peso, diámetro, módulo de elasticidad)
- La asignación de cables a nodos específicos debe implementarse en EstructuraAEA_Geometria.py
- Los sufijos "g" se reemplazaron por "g1" y "g2" en todo el código
- La compatibilidad hacia atrás se mantiene: si cable_guardia2 es None, solo se usa guardia1
