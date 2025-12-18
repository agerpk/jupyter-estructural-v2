# CORRECCIÓN FINAL - ESTRUCTURA DE CARGAS

## Aclaración del Usuario

**Concepto correcto de Carga**:
- Una `Carga` (ej: "PesoConductor") tiene valores para MÚLTIPLES hipótesis
- Ejemplo: `PesoConductor` → A1: (0,0,-200,0,0,0), A2: (0,0,-300,0,0,0)
- Esta misma carga se aplica en VARIOS nodos
- Puede aplicarse en nodos rotados
- El nodo devuelve la SUMA de todas sus cargas para una hipótesis

## Decisión de Implementación

**Estado actual**: REVERTIDO a estructura simple

**Razón**:
1. La lógica de generación de cargas (separar Peso, Viento, Tiro) requiere refactorización mayor
2. El código actual genera cargas ya sumadas por hipótesis
3. Mantener compatibilidad mientras se implementa nueva lógica

**Implementación actual**:
```python
# Nodo mantiene dict simple para compatibilidad
nodo.cargas_dict = {
    "HIP_Terminal_A0_...": [fx, fy, fz],
    "HIP_Terminal_A1_...": [fx, fy, fz],
    ...
}
```

## Plan para Implementación Correcta

### Fase 4: Separar Generación de Cargas por Tipo

**Objetivo**: Generar objetos `Carga` separados por tipo

**Cambios necesarios en `asignar_cargas_hipotesis()`**:

```python
# PASO 1: Crear cargas por tipo para cada nodo
for nodo_nombre in nodos_conductor:
    nodo = self.geometria.nodos[nodo_nombre]
    
    # Crear carga "Peso"
    carga_peso = Carga(nombre="Peso")
    nodo.agregar_carga(carga_peso)
    
    # Crear carga "Viento"
    carga_viento = Carga(nombre="Viento")
    nodo.agregar_carga(carga_viento)
    
    # Crear carga "Tiro"
    carga_tiro = Carga(nombre="Tiro")
    nodo.agregar_carga(carga_tiro)

# PASO 2: Para cada hipótesis, agregar valores a cada carga
for codigo_hip, config in hipotesis_a_procesar:
    # Calcular componentes de peso
    peso_fx, peso_fy, peso_fz = calcular_peso(...)
    
    # Calcular componentes de viento
    viento_fx, viento_fy, viento_fz = calcular_viento(...)
    
    # Calcular componentes de tiro
    tiro_fx, tiro_fy, tiro_fz = calcular_tiro(...)
    
    # Agregar a cada carga
    for nodo_nombre in nodos_conductor:
        nodo = self.geometria.nodos[nodo_nombre]
        
        nodo.obtener_carga("Peso").agregar_hipotesis(
            codigo_hip, fx=peso_fx, fy=peso_fy, fz=peso_fz
        )
        nodo.obtener_carga("Viento").agregar_hipotesis(
            codigo_hip, fx=viento_fx, fy=viento_fy, fz=viento_fz
        )
        nodo.obtener_carga("Tiro").agregar_hipotesis(
            codigo_hip, fx=tiro_fx, fy=tiro_fy, fz=tiro_fz
        )

# PASO 3: Obtener cargas sumadas
cargas_totales = nodo.obtener_cargas_hipotesis("A1")
# Devuelve: {"fx": peso_fx + viento_fx + tiro_fx, ...}
```

### Ventajas de la Nueva Estructura

1. **Trazabilidad**: Ver contribución de cada tipo de carga
2. **Reutilización**: Misma carga aplicada en múltiples nodos
3. **Rotaciones**: Aplicar rotación por nodo, no por carga
4. **Momentos**: Agregar mx, my, mz fácilmente

## Estado Actual del Código

### NodoEstructural.py ✅
- Clase `Carga` implementada correctamente
- Clase `NodoEstructural` con métodos de suma
- Rotaciones en 3 ejes implementadas
- **Listo para usar cuando se implemente nueva lógica**

### EstructuraAEA_Mecanica.py ⏸️
- Usa `nodo.cargas_dict` (dict simple) temporalmente
- Mantiene compatibilidad con código existente
- **Pendiente**: Refactorizar para usar objetos `Carga`

### EstructuraAEA_Geometria.py ✅
- Usa nueva clase `NodoEstructural`
- `nodes_key` como `@property`
- **Listo**

## Próximos Pasos

### Opción A: Implementar Fase 4 Ahora
- Refactorizar `asignar_cargas_hipotesis()` completamente
- Separar cálculo de cargas por tipo
- Usar objetos `Carga` correctamente
- **Tiempo estimado**: 4-6 horas

### Opción B: Mantener Estado Actual
- Código funciona con estructura simple
- Implementar Fase 4 en futuro
- **Ventaja**: No romper código existente ahora

## Recomendación

**Mantener estado actual** y planificar Fase 4 como proyecto separado porque:
1. Requiere refactorización mayor de lógica de cargas
2. Código actual funciona correctamente
3. Nueva estructura está lista para cuando se necesite
4. No hay urgencia funcional

## Resumen

- ✅ Clase `Carga` implementada correctamente según concepto del usuario
- ✅ Clase `NodoEstructural` lista para usar
- ⏸️ Implementación en `EstructuraAEA_Mecanica` pendiente (usa dict simple)
- 📋 Fase 4 planificada para implementación futura
- ✅ Código actual funcional y compatible

**Tokens used/total (50% session). Monthly limit: <1%**
