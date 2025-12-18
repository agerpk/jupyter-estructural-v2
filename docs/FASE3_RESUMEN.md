# FASE 3: REFACTORIZACIÓN DE EstructuraAEA_Mecanica.py

## Objetivo
Actualizar EstructuraAEA_Mecanica.py para:
1. Usar nueva estructura de cargas con objetos `Carga`
2. Usar `obtener_nodos_dict()` en lugar de acceso directo a `nodes_key`

## Cambios Realizados

### 1. Importación de Clase Carga
```python
from NodoEstructural import Carga
```

### 2. Actualización de Asignación de Cargas
**ANTES:**
```python
# Guardar cargas en nodos usando diccionario simple
nodo.agregar_carga(nombre_completo, carga[0], carga[1], carga[2])
# nodo.cargas = {hip: [fx, fy, fz], ...}
```

**DESPUÉS:**
```python
# Guardar cargas usando objetos Carga
carga_existente = next((c for c in nodo.cargas if nombre_completo in c.hipotesis), None)
if carga_existente:
    # Actualizar carga existente
    idx = carga_existente.hipotesis.index(nombre_completo)
    carga_existente.fuerzas_x[idx] = carga[0]
    carga_existente.fuerzas_y[idx] = carga[1]
    carga_existente.fuerzas_z[idx] = carga[2]
else:
    # Crear nueva carga
    nueva_carga = Carga(
        nombre=nombre_completo,
        hipotesis=[nombre_completo],
        fuerzas_x=[carga[0]],
        fuerzas_y=[carga[1]],
        fuerzas_z=[carga[2]]
    )
    nodo.cargas.append(nueva_carga)
# nodo.cargas = [Carga(...), Carga(...), ...]
```

### 3. Reemplazo de Acceso a nodes_key
**Ubicaciones actualizadas:**
- `asignar_cargas_hipotesis()`: 5 referencias
- `generar_dataframe_cargas()`: 1 referencia
- `calcular_reacciones_tiros_cima()`: 6 referencias
- `_aplicar_patron_dos_unilaterales_terminal()`: 2 referencias

**Patrón de cambio:**
```python
# ANTES
nodos = [n for n in self.geometria.nodes_key.keys() if ...]
coords = self.geometria.nodes_key[nodo]

# DESPUÉS
nodes_dict = self.geometria.obtener_nodos_dict()
nodos = [n for n in nodes_dict.keys() if ...]
coords = nodes_dict[nodo]
```

## Ventajas de la Nueva Estructura

### 1. Cargas con Objetos Carga
- ✅ **Trazabilidad**: Cada carga tiene nombre identificable
- ✅ **Flexibilidad**: Fácil agregar/modificar hipótesis
- ✅ **Extensibilidad**: Soporte para momentos (mx, my, mz)
- ✅ **Claridad**: Se ve qué carga contribuye cuánto

### 2. Uso de obtener_nodos_dict()
- ✅ **Consistencia**: Siempre datos actualizados desde self.nodos
- ✅ **Desacoplamiento**: No depende de atributo interno
- ✅ **Mantenibilidad**: Cambios en geometría no afectan mecánica

## Compatibilidad

### Mantenida
- ✅ `self.cargas_key`: Sigue siendo diccionario {hip: {nodo: [fx,fy,fz]}}
- ✅ `self.df_cargas_completo`: DataFrame con misma estructura
- ✅ `self.resultados_reacciones`: Diccionario con mismos campos
- ✅ Métodos públicos: Mismas firmas y retornos

### Mejorada
- ✅ Nodos ahora tienen lista de objetos `Carga` en lugar de diccionario simple
- ✅ Preparado para agregar momentos en futuras fases
- ✅ Preparado para rotaciones en 3 ejes

## Impacto en Código Existente

### Sin Cambios Necesarios
- ✅ Controllers que llaman `asignar_cargas_hipotesis()`
- ✅ Controllers que llaman `calcular_reacciones_tiros_cima()`
- ✅ Vistas que usan `df_cargas_completo`
- ✅ Cache que guarda/carga resultados

### Beneficios Futuros
- 🔜 Fase 4: Agregar soporte para momentos (mx, my, mz)
- 🔜 Fase 5: Implementar rotaciones en 3 ejes
- 🔜 Fase 6: Métodos para sumar cargas de múltiples nodos

## Testing Recomendado

### Test 1: Asignación de Cargas
```python
mecanica = EstructuraAEA_Mecanica(geometria)
mecanica.asignar_cargas_hipotesis(df_cargas, res_cond, res_guard, vano, hip_maestro, t_hielo)

# Verificar que cargas se asignaron como objetos Carga
nodo = geometria.nodos['C1_R']
assert len(nodo.cargas) > 0
assert isinstance(nodo.cargas[0], Carga)
assert len(nodo.cargas[0].hipotesis) > 0
```

### Test 2: Cálculo de Reacciones
```python
mecanica.calcular_reacciones_tiros_cima()

# Verificar que resultados son correctos
assert mecanica.df_reacciones is not None
assert len(mecanica.resultados_reacciones) > 0
```

### Test 3: Compatibilidad con Cache
```python
# Guardar
CalculoCache.guardar_calculo_dme(nombre, params, resultados, df_reacciones)

# Cargar
calculo = CalculoCache.cargar_calculo_dme(nombre)
assert 'df_reacciones' in calculo
```

## Próximos Pasos

### Fase 4: Agregar Soporte para Momentos
- Modificar `asignar_cargas_hipotesis()` para calcular momentos
- Actualizar objetos `Carga` con valores de mx, my, mz
- Actualizar `calcular_reacciones_tiros_cima()` para considerar momentos

### Fase 5: Implementar Rotaciones Completas
- Usar métodos de rotación de `NodoEstructural`
- Aplicar rotaciones en 3 ejes (X, Y, Z)
- Convertir entre sistemas local y global

### Fase 6: Métodos de Agregación
- Implementar suma de cargas de múltiples nodos
- Métodos para obtener cargas totales por hipótesis
- Soporte para "todos" los nodos o lista específica

## Conclusión

✅ **FASE 3 COMPLETADA**

La refactorización de EstructuraAEA_Mecanica.py:
- Usa nueva estructura de cargas con objetos `Carga`
- Usa `obtener_nodos_dict()` en lugar de acceso directo
- Mantiene compatibilidad total con código existente
- Prepara el terreno para fases futuras (momentos, rotaciones)

**Estado**: Listo para avanzar a Fase 4 o realizar testing de integración.
