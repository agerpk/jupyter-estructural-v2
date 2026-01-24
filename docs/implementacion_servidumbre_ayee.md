# Implementación: Método de Servidumbre AyEE

## Resumen
Implementación de método alternativo de cálculo de servidumbre según normativa AyEE, con selección de distancia `d` basada en tabla según tensión nominal y zona de estructura.

## Archivos Modificados/Creados

### 1. **utils/servidumbre_ayee.py** (NUEVO) ✅
- Clase `ServidumbreAyEE` con cálculo de distancia `d` por tabla
- Tabla de distancias según tensión (66, 132, 220 kV) y zona (rural/urbana)
- Memoria de cálculo específica AyEE con tabla impresa

### 2. **utils/grafico_servidumbre.py** (RENOMBRADO de grafico_servidumbre_aea.py) ✅
- Renombrado de archivo y función
- Agregado parámetro `metodo` para identificar método usado
- Título del gráfico incluye método (AEA o AyEE)

### 3. **controllers/geometria_controller.py** (MODIFICADO) ✅
- Import renombrado: `from utils.grafico_servidumbre import graficar_servidumbre`
- Lógica de selección de clase según `metodo_servidumbre`
- Pasar `zona_estructura` a constructores
- Actualizado en 2 ubicaciones: `ejecutar_calculo_dge()` y `calcular_diseno_geometrico()`

### 4. **data/plantilla.estructura.json** (MODIFICADO) ✅
- Agregado: `"metodo_servidumbre": "AEA"`

### 5. **docs/implementacion_servidumbre_ayee.md** (NUEVO) ✅
- Documentación completa de la implementación

### 6. **components/vista_diseno_geometrico.py** (PENDIENTE)
- Dropdown para seleccionar método: ["AEA", "AyEE"]
- Callback para guardar `metodo_servidumbre`

### 7. **components/vista_ajustar_parametros.py** (PENDIENTE)
- Fila en tabla para `metodo_servidumbre` (dropdown)

### 8. **components/vista_familia_estructuras.py** (PENDIENTE)
- Columna en tabla para `metodo_servidumbre`

## Tabla de Distancias AyEE

```python
TABLA_DISTANCIAS_AYEE = {
    66: {"rural": 3.0, "urbana": 4.2},
    132: {"rural": 3.15, "urbana": 4.35},
    220: {"rural": 3.75, "urbana": 4.95}
}
```

## Lógica de Selección

### Tensión
- Si Vn ≤ 66 kV → usar 66 kV
- Si 66 < Vn ≤ 132 kV → usar 132 kV
- Si Vn > 132 kV → usar 220 kV

### Zona
- Si `zona_estructura == "urbana"` → usar "urbana"
- Cualquier otro valor → usar "rural"

## Diferencias entre Métodos

### Método AEA (Original)
```
d = 1.5 * dm + 2
donde dm = Vs / 150
donde Vs = μ * 1.2 * 0.82 * Vn
```

### Método AyEE (Nuevo)
```
d = TABLA_DISTANCIAS_AYEE[tension_tabla][zona_tipo]
```

## Memoria de Cálculo AyEE

Incluye:
1. Tabla completa de distancias AyEE
2. Tensión nominal y tensión de tabla seleccionada
3. Zona de estructura y tipo seleccionado (rural/urbana)
4. Distancia `d` resultante de tabla
5. Resto del cálculo igual que AEA (C, A, proyección)

## Visualización

### Título del Gráfico
- AEA: `FRANJA DE SERVIDUMBRE AEA-95301-2007`
- AyEE: `FRANJA DE SERVIDUMBRE AyEE`

### Memoria de Cálculo
- AEA: `MEMORIA DE CÁLCULO: FRANJA DE SERVIDUMBRE AEA-95301-2007 9.2-1`
- AyEE: `MEMORIA DE CÁLCULO: FRANJA DE SERVIDUMBRE AyEE`

## Compatibilidad

- Cache: Método guardado en `servidumbre_data`
- Calcular Todo: Detecta método automáticamente
- Familia: Columna editable para método
- HTML Export: Incluye método en título

## Testing

1. Crear estructura con `metodo_servidumbre: "AEA"` → Verificar cálculo tradicional
2. Cambiar a `metodo_servidumbre: "AyEE"` → Verificar tabla y distancias
3. Probar con diferentes tensiones (66, 132, 220 kV)
4. Probar con diferentes zonas (urbana, rural)
5. Verificar memoria de cálculo incluye tabla AyEE
6. Verificar título de gráfico muestra método correcto
