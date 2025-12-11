# Resumen de Cambios - Soporte para 2 Cables de Guardia

## ✅ CAMBIOS COMPLETADOS

### 1. Modelo de Datos
- ✅ `data/KACHI-1x220-Sst-0a1500.estructura.json` - Estructura de prueba creada
- ✅ `data/plantilla.estructura.json` - Campo `cable_guardia2_id` agregado
- ✅ Configuración: Ac 70 (derecha) + OPGW 120mm (izquierda)

### 2. Cálculo de Objetos
- ✅ `utils/calculo_objetos.py`
  - Atributo `cable_guardia2` agregado
  - Método `crear_objetos_cable()` crea 2 objetos Cable_AEA cuando CANT_HG=2
  - Validación de existencia de cables en base de datos

### 3. Interfaz de Usuario
- ✅ `components/vista_ajuste_parametros.py`
  - Selector `cable_guardia_id` (derecha, x+)
  - Selector `cable_guardia2_id` (izquierda, x-)
  - Descripciones claras para el usuario

### 4. Cálculo Mecánico de Cables
- ✅ `utils/calculo_mecanico_cables.py`
  - Variables renombradas: `df_guardia` → `df_guardia1`, `df_guardia2`
  - Variables renombradas: `resultados_guardia` → `resultados_guardia1`, `resultados_guardia2`
  - Calcula ambos cables de guardia independientemente
  - Cada guardia tiene su propia restricción de relflecha respecto al conductor

### 5. Listado de Cargas
- ✅ `ListarCargas.py`
  - Parámetros: `cable_guardia` → `cable_guardia1`, `cable_guardia2`
  - Sufijos actualizados en todo el código:
    - `Pcg` → `Pcg1`, `Pcg2` (peso)
    - `Vcg` → `Vcg1`, `Vcg2` (viento)
    - `cg` → `cg1`, `cg2` (tiros)
  - Genera cargas para ambos cables de guardia

### 6. Mecánica de Estructura
- ✅ `EstructuraAEA_Mecanica.py`
  - Parámetros: `resultados_guardia` → `resultados_guardia1` + `resultados_guardia2` (opcional)
  - Lógica de asignación por posición de nodo:
    - **HG1 o x > 0 (derecha)** → usa `cable_guardia1`
    - **HG2 o x < 0 (izquierda)** → usa `cable_guardia2`
  - Sufijos de viento dinámicos según el cable asignado
  - Viento oblicuo bilateral suma ambos guardias

## 🎯 CARACTERÍSTICAS CLAVE

### Restricción de Relflecha
Cada cable de guardia tiene su propia restricción de relflecha respecto al conductor:
- **Guardia 1**: `flecha_g1 ≤ relflecha_max × flecha_conductor`
- **Guardia 2**: `flecha_g2 ≤ relflecha_max × flecha_conductor`

Ambos cables se calculan independientemente con sus propias propiedades mecánicas.

### Asignación Automática por Posición
El sistema asigna automáticamente el cable correcto según la posición del nodo:
```python
if nodo == "HG1" or (nodo.startswith("HG") and x > 0):
    # Usa cable_guardia1 (derecha)
    sufijo = "1"
else:
    # Usa cable_guardia2 (izquierda)
    sufijo = "2"
```

### Compatibilidad hacia Atrás
- Si `cable_guardia2_id` es `null` → solo usa `cable_guardia1`
- Si `CANT_HG = 1` → ignora `cable_guardia2_id`
- Estructuras existentes siguen funcionando sin cambios

## 📊 SUFIJOS ACTUALIZADOS

| Concepto | Antes | Después |
|----------|-------|---------|
| Peso gravivano | `Pcg` | `Pcg1`, `Pcg2` |
| Peso hielo | `Pcgh` | `Pcg1h`, `Pcg2h` |
| Viento máximo transversal | `Vcg` | `Vcg1`, `Vcg2` |
| Viento máximo longitudinal | `VcgL` | `Vcg1L`, `Vcg2L` |
| Viento medio transversal | `Vcgmed` | `Vcg1med`, `Vcg2med` |
| Viento medio longitudinal | `VcgmedL` | `Vcg1medL`, `Vcg2medL` |
| Viento oblicuo | `Vcg_o_t_1` | `Vcg1_o_t_1`, `Vcg2_o_t_1` |
| Tiro estado | `Ttmax_cg_t` | `Ttmax_cg1_t`, `Ttmax_cg2_t` |

## ✅ ACTUALIZACIÓN COMPLETADA

### 7. EstructuraAEA_Geometria.py
- ✅ Atributos: `self.cable_guardia1` y `self.cable_guardia2`
- ✅ Nodo HG1 usa `cable_guardia1` (derecha, x+)
- ✅ Nodo HG2 usa `cable_guardia2` si existe, sino `cable_guardia1` (izquierda, x-)
- ✅ Mantiene `self.cable_guardia` para compatibilidad

### 8. controllers/geometria_controller.py
- ✅ Usa `resultados_guardia1` y `resultados_guardia2`
- ✅ Calcula flechas máximas de ambos guardias
- ✅ Pasa `resultados_guardia2` a `asignar_cargas_hipotesis()`
- ✅ Asigna `cable_guardia2` a geometría si existe
- ✅ Muestra flechas de g1 y g2 en output

### 9. controllers/mecanica_controller.py
- ✅ Reemplazadas todas las referencias a `cable_guardia` → `cable_guardia1`
- ✅ Reemplazadas todas las referencias a `resultados_guardia` → `resultados_guardia1`
- ✅ Calcula flechas máximas de ambos guardias
- ✅ Pasa `resultados_guardia2` a métodos de mecánica

## 📋 PENDIENTES

### Archivos que necesitan actualización:
1. **Controllers** (PRIORIDAD ALTA)
   - arboles_controller.py
   - calcular_todo_controller.py

2. **plot_flechas.py** (PRIORIDAD MEDIA)
   - Graficar 2 cables de guardia con colores diferentes
   - Leyenda que identifique cada cable

3. **EstructuraAEA_Graficos.py** (PRIORIDAD MEDIA)
   - Graficar ambos cables de guardia en diagramas polares
   - Diferenciar visualmente g1 y g2

4. **arboles_carga.py** (PRIORIDAD BAJA)
   - Generar árboles de carga considerando ambos guardias
   - Mostrar cargas de g1 y g2 por separado

5. **memoria_calculo_dge.py** (PRIORIDAD BAJA)
   - Incluir información de ambos cables en la memoria
   - Tablas separadas para g1 y g2

## 🧪 TESTING

### Casos de Prueba:
1. ✅ Estructura con 1 guardia (compatibilidad)
2. ✅ Estructura con 2 guardias iguales
3. ✅ Estructura con 2 guardias diferentes (KACHI)
4. ⏳ Cálculo mecánico de ambos guardias
5. ⏳ Generación de cargas con sufijos g1/g2
6. ⏳ Asignación correcta por posición de nodo
7. ⏳ Restricción de relflecha independiente

## 📝 NOTAS TÉCNICAS

### Convención de Nombres:
- **Guardia 1 (g1)**: Cable de la derecha (x > 0)
- **Guardia 2 (g2)**: Cable de la izquierda (x < 0)

### Parámetros Compartidos:
- Ambos guardias usan los mismos parámetros de viento: `Vmax`, `Zcg`, `Cf_guardia`
- Cada cable tiene sus propias propiedades mecánicas: peso, diámetro, módulo de elasticidad

### Restricciones:
- Ambos guardias deben cumplir: `flecha_g ≤ relflecha_max × flecha_conductor`
- Cada guardia se optimiza independientemente (FlechaMin o TiroMin)
- Los tiros pueden ser diferentes entre g1 y g2

## 🚀 PRÓXIMOS PASOS

1. Actualizar `EstructuraAEA_Geometria.py` para asignar cables
2. Modificar controllers para manejar 2 DataFrames de guardia
3. Actualizar gráficos para mostrar ambos cables
4. Probar con estructura KACHI-1x220-Sst-0a1500
5. Validar cálculos mecánicos independientes
6. Generar documentación de usuario
