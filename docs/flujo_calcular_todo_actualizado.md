# Flujo Actualizado del Botón "Calcular Todo"

## Secuencia de Cálculos Ampliada

El botón "Calcular Todo" ahora ejecuta **7 cálculos en secuencia**:

1. **CMC** - Cálculo Mecánico de Cables
2. **DGE** - Diseño Geométrico de Estructura  
3. **DME** - Diseño Mecánico de Estructura
4. **Árboles** - Árboles de Carga
5. **SPH** - Selección de Poste de Hormigón
6. **Fundación** - Cálculo de Fundaciones (NUEVO)
7. **Costeo** - Análisis de Costos (NUEVO)

## Funciones Ejecutables Agregadas

### `ejecutar_calculo_fundacion(estructura_actual, state)`
**Ubicación**: `controllers/ejecutar_calculos.py`

**Funcionalidad**:
- Obtiene parámetros de fundación desde `estructura_actual['fundacion']`
- Ejecuta cadena completa CMC→DGE→DME→SPH si no hay cache válido
- Crea instancia `Sulzberger` con parámetros completos
- Ejecuta `calcular_fundacion_multiples_hipotesis()`
- Genera DataFrame y memoria de cálculo
- Guarda en cache: `{nombre}.calculoFUND.json`

**Dependencias**:
- Requiere parámetros configurados en vista Fundación
- Necesita cache válido de SPH/DME para obtener fuerzas

### `ejecutar_calculo_costeo(estructura_actual, state)`
**Ubicación**: `controllers/ejecutar_calculos.py`

**Funcionalidad**:
- Obtiene parámetros de costeo desde `estructura_actual['costeo']`
- Verifica cadena completa CMC→DGE→DME→SPH→Fundación
- Extrae datos de SPH y Fundaciones para costeo
- Ejecuta `calcular_costeo_completo()` con precios configurados
- Guarda en cache: `{nombre}.calculoCOSTEO.json`

**Dependencias**:
- Requiere parámetros configurados en vista Costeo
- Necesita cache válido de SPH y Fundación

## Captura de Output

### Sistema Global de Captura
- **Archivo**: `utils/console_capture.py`
- **Activación**: Se inicia en `app.py` al arrancar aplicación
- **Funcionamiento**: Redirige `sys.stdout/stderr` a buffer persistente
- **Capacidad**: 10,000 líneas máximo con thread-safety

### Output por Cálculo
Cada cálculo captura su output específico:

```python
# CMC: Captura automática en console_output
# DGE: Memoria de cálculo específica  
# DME: Sin console específico
# Árboles: Sin console específico
# SPH: desarrollo_texto desde buffer
# Fundación: memoria_calculo desde Sulzberger
# Costeo: Sin console específico (usa datos extraídos)
```

## Cache Actualizado

### Archivos de Cache Generados
```
data/cache/
├── {nombre}.calculoCMC.json      # Tablas + gráficos Plotly
├── {nombre}.calculoDGE.json      # Dimensiones + gráfico 3D nodos
├── {nombre}.calculoDME.json      # Reacciones + diagramas
├── {nombre}.calculoARBOLES.json  # Imágenes + DataFrame cargas
├── {nombre}.calculoSPH.json      # Resultados + desarrollo_texto
├── {nombre}.calculoFUND.json     # Resultados + memoria + gráfico 3D (NUEVO)
└── {nombre}.calculoCOSTEO.json   # Costos + parámetros precios (NUEVO)
```

### Carga Modular Actualizada
**Función**: `cargar_resultados_modulares()` en `vista_calcular_todo.py`

Ahora incluye:
- **Sección 6**: Fundación con `generar_resultados_fundacion()`
- **Sección 7**: Costeo con `generar_resultados_costeo()`

## Flujo de Ejecución Completo

```
Usuario presiona "Calcular Todo"
    ↓
Callback ejecuta 7 cálculos secuenciales:
    ↓
1. CMC → Cables y flechas
2. DGE → Geometría y nodos 3D  
3. DME → Reacciones y diagramas
4. Árboles → Load trees 2D/3D
5. SPH → Selección postes
6. Fundación → Dimensionado Sulzberger (NUEVO)
7. Costeo → Análisis económico (NUEVO)
    ↓
Cada cálculo:
  - Ejecuta lógica específica
  - Captura output automáticamente  
  - Guarda resultados + output en JSON
  - Genera gráficos (PNG + JSON para Plotly)
    ↓
Carga resultados desde cache
    ↓
Genera componentes Dash por sección
    ↓
Retorna lista completa de componentes al UI
```

## Manejo de Errores

### Cálculos Independientes
- Cada cálculo puede fallar independientemente
- Error en un cálculo no detiene los siguientes
- Se muestra alerta específica por cálculo fallido

### Dependencias de Cadena
- **Fundación**: Requiere SPH válido (ejecuta cadena si falta)
- **Costeo**: Requiere SPH + Fundación válidos (ejecuta cadena completa si falta)

### Configuración Requerida
- **Fundación**: Parámetros en `estructura_actual['fundacion']`
- **Costeo**: Parámetros en `estructura_actual['costeo']`
- Sin configuración → Error específico, continúa con siguientes cálculos

## Beneficios de la Ampliación

1. **Flujo Completo**: Desde cables hasta costos en una sola ejecución
2. **Reutilización**: Usa mismas funciones que vistas individuales
3. **Cache Inteligente**: Evita recálculos innecesarios
4. **Output Completo**: Captura automática de toda la información
5. **Modularidad**: Cada cálculo es independiente y reutilizable
6. **Consistencia**: Mismos resultados que vistas individuales

## Archivos Modificados

- `controllers/ejecutar_calculos.py` - Funciones ejecutables agregadas
- `controllers/calcular_todo_controller.py` - Secuencia ampliada 
- `components/vista_calcular_todo.py` - Carga modular actualizada
- `docs/flujo_calcular_todo_actualizado.md` - Esta documentación

El sistema mantiene la arquitectura modular existente mientras amplía significativamente las capacidades del flujo "Calcular Todo".