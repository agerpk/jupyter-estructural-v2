# Campo Cantidad en Familias de Estructuras

## Resumen
El campo `cantidad` es un campo específico de familias que permite especificar cuántas unidades de cada estructura se incluyen en la familia. Este campo se usa para calcular el costo parcial (costo individual × cantidad) y el costo global de la familia.

## Ubicación del Campo

### 1. En la Tabla de Familia (UI)
- **Archivo**: `components/vista_familia_estructuras.py`
- **Líneas**: 437-447
- **Descripción**: Se genera como segunda fila de la tabla, inmediatamente después de TITULO
- **Valores por defecto**: 1 para cada estructura
- **Tipo**: `int` (entero)

```python
# Agregar fila CANTIDAD como segunda fila
fila_cantidad = {
    "categoria": "General",
    "parametro": "cantidad",
    "simbolo": "CANT",
    "unidad": "unidades",
    "descripcion": "Cantidad de estructuras",
    "tipo": "int"
}
for nombre_estr, datos_estr in estructuras.items():
    fila_cantidad[nombre_estr] = datos_estr.get("cantidad", 1)
tabla_data.append(fila_cantidad)
```

### 2. En el JSON de Familia
- **Archivo**: Guardado en `data/{nombre_familia}.familia.json`
- **Estructura**:
```json
{
  "nombre_familia": "Familia Ejemplo",
  "estructuras": {
    "Estr.1": {
      "TITULO": "Estructura 1",
      "cantidad": 5,
      ...otros parámetros...
    },
    "Estr.2": {
      "TITULO": "Estructura 2", 
      "cantidad": 3,
      ...otros parámetros...
    }
  }
}
```

### 3. En la Creación de Familia Nueva
- **Archivo**: `utils/familia_manager.py`
- **Método**: `crear_familia_nueva()`
- **Línea**: 27
- **Descripción**: Se inicializa con valor 1 al crear una familia nueva

```python
# Agregar campo cantidad
plantilla["cantidad"] = 1
```

### 4. En la Conversión Tabla → Familia
- **Archivo**: `utils/familia_manager.py`
- **Método**: `tabla_a_familia()`
- **Líneas**: 119-177
- **Descripción**: Convierte los valores de la tabla (incluyendo cantidad) al formato JSON de familia

```python
# Convertir tipos para parámetros normales
tipo = fila.get('tipo', 'str')
if tipo == 'int':
    try:
        valor = int(valor)
    except:
        valor = 0
...
estructura_data[parametro] = valor
```

### 5. En el Cálculo de Familia
- **Archivo**: `utils/calcular_familia_logica_encadenada.py`
- **Función**: `ejecutar_calculo_familia_completa()`
- **Líneas**: 48-49, 73-74
- **Descripción**: Extrae cantidad de cada estructura para calcular costos parciales

```python
titulo = datos_estr.get("TITULO", nombre_estr)
cantidad = datos_estr.get("cantidad", 1)
```

### 6. En el Costeo de Familia
- **Archivo**: `utils/calcular_familia_logica_encadenada.py`
- **Función**: `_generar_costeo_familia()`
- **Líneas**: 308-309
- **Descripción**: Calcula costo parcial = costo individual × cantidad

```python
cantidad = datos["cantidad"]
costo_individual = datos["costo_individual"]
costo_parcial = costo_individual * cantidad
```

### 7. En la Vista de Costeo Global
- **Archivo**: `utils/calcular_familia_logica_encadenada.py`
- **Función**: `_crear_contenido_costeo_familia()`
- **Líneas**: 625-650
- **Descripción**: Muestra tabla con cantidad real de cada estructura

```python
# Extraer cantidades desde resultados_estructuras
cantidades_por_titulo = {}
if resultados_estructuras:
    for nombre_estr, datos in resultados_estructuras.items():
        titulo = datos.get("titulo", nombre_estr)
        cantidad = datos.get("cantidad", 1)
        cantidades_por_titulo[titulo] = cantidad

# Tabla de costos
html.Tbody([
    html.Tr([
        html.Td(titulo),
        html.Td(f"{costos_individuales.get(titulo, 0):,.2f}"),
        html.Td(str(cantidades_por_titulo.get(titulo, 1))),  # ✅ Cantidad real
        html.Td(f"{costos_parciales.get(titulo, 0):,.2f}")
    ]) for titulo in costos_individuales.keys()
])
```

## Flujo de Datos

```
1. Usuario edita tabla familia
   ↓
2. Tabla incluye fila "cantidad" con valores editables
   ↓
3. Usuario presiona "Guardar Familia"
   ↓
4. tabla_a_familia() convierte tabla → JSON
   ↓
5. JSON guardado en data/{nombre}.familia.json con campo "cantidad" en cada estructura
   ↓
6. Usuario presiona "Calcular Familia"
   ↓
7. ejecutar_calculo_familia_completa() extrae cantidad de cada estructura
   ↓
8. Se calcula costo individual de cada estructura
   ↓
9. _generar_costeo_familia() calcula:
      - costo_parcial = costo_individual × cantidad
      - costo_global = suma de todos los costos_parciales
   ↓
10. _crear_contenido_costeo_familia() muestra tabla con:
      - Costo Individual
      - Cantidad (valor real desde JSON)
      - Costo Parcial (individual × cantidad)
```

## Validaciones

### Tipo de Dato
- **Tipo esperado**: `int` (entero positivo)
- **Valor por defecto**: 1
- **Conversión**: Se convierte a `int` en `tabla_a_familia()` con manejo de excepciones

### Valores Permitidos
- **Mínimo**: 1 (implícito, no hay validación explícita)
- **Máximo**: Sin límite
- **Valores inválidos**: Se convierten a 0 si falla la conversión a `int`

## Casos de Uso

### Ejemplo 1: Familia con 3 estructuras
```json
{
  "nombre_familia": "Línea Principal",
  "estructuras": {
    "Estr.1": {
      "TITULO": "Suspensión Recta",
      "cantidad": 50,
      "costo_individual": 15000
    },
    "Estr.2": {
      "TITULO": "Angular 30°",
      "cantidad": 10,
      "costo_individual": 22000
    },
    "Estr.3": {
      "TITULO": "Terminal",
      "cantidad": 2,
      "costo_individual": 35000
    }
  }
}
```

**Cálculo de Costeo:**
- Suspensión: 50 × 15,000 = 750,000 UM
- Angular: 10 × 22,000 = 220,000 UM
- Terminal: 2 × 35,000 = 70,000 UM
- **Total Familia**: 1,040,000 UM

## Archivos Modificados (2025-01-XX)

### Corrección de Cantidad en Vista de Costeo
- **Archivo**: `utils/calcular_familia_logica_encadenada.py`
- **Cambio**: Modificada función `_crear_contenido_costeo_familia()` para:
  1. Aceptar parámetro `resultados_estructuras`
  2. Extraer cantidades reales desde `resultados_estructuras`
  3. Mostrar cantidad real en tabla en lugar de valor hardcodeado "1"
- **Líneas modificadas**: 625-650, 706-710

## Notas Importantes

1. **Campo específico de familias**: El campo `cantidad` NO existe en estructuras individuales (`.estructura.json`), solo en familias (`.familia.json`)

2. **Plantilla no incluye cantidad**: El archivo `plantilla.estructura.json` NO tiene el campo `cantidad` porque es específico de familias

3. **Inicialización automática**: Al crear una familia nueva, se agrega automáticamente `cantidad: 1` a cada estructura

4. **Editable en tabla**: El campo cantidad es editable directamente en la tabla de familia (tipo `int`)

5. **Uso en costeo**: El campo cantidad se usa SOLO en el costeo de familia para calcular costos parciales y costo global

## Testing

### Verificar que cantidad se guarda correctamente:
1. Crear familia nueva
2. Editar campo cantidad de cada estructura
3. Guardar familia
4. Verificar archivo JSON en `data/{nombre}.familia.json`
5. Verificar que campo `cantidad` existe en cada estructura con valor correcto

### Verificar que cantidad se usa en costeo:
1. Cargar familia con cantidades diferentes
2. Calcular familia
3. Ir a pestaña "Costeo Familia"
4. Verificar que columna "Cantidad" muestra valores correctos
5. Verificar que "Costo Parcial" = "Costo Individual" × "Cantidad"
6. Verificar que "Costo Global" = suma de todos los costos parciales
