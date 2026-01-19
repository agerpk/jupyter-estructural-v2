# Plan de Implementación - Memoria de Cálculo CMC

## Análisis de Referencia

### Patrón DGE (memoria_calculo_dge.py)
- **Estructura**: Argumentos → Ecuaciones → Resultados
- **Formato**: Texto plano con secciones numeradas
- **Contenido**: Fórmulas matemáticas con valores sustituidos
- **Organización**: Pasos secuenciales del 0 al N

### Estructura CalculoCables.py
- **Clase Cable_AEA**: Contiene todos los métodos de cálculo mecánico
- **Método principal**: `calculo_mecanico()` - orquesta todo el proceso
- **Métodos internos**: `_optimizar_flecha_min()`, `_optimizar_tiro_min()`, `_calcular_estado()`
- **Datos disponibles**: Propiedades del cable, estados climáticos, restricciones, resultados finales

## Implementación Propuesta

### 1. Archivo: `utils/memoria_calculo_cmc.py`

```python
def gen_memoria_calculo_CMC(cable_aea, vano, estados_climaticos, parametros_viento, 
                           restricciones, objetivo, resultados_finales, t_final, 
                           q0_final, estado_limitante):
    """
    Genera memoria de cálculo del Cálculo Mecánico de Cables
    
    Args:
        cable_aea: Objeto Cable_AEA con propiedades y métodos
        vano: Longitud del vano en metros
        estados_climaticos: Dict con estados climáticos
        parametros_viento: Dict con parámetros de viento
        restricciones: Dict con restricciones aplicadas
        objetivo: 'FlechaMin' o 'TiroMin'
        resultados_finales: Dict con resultados por estado
        t_final: Tensión final optimizada
        q0_final: Temperatura del estado básico
        estado_limitante: Estado que limita la optimización
    
    Returns:
        str: Texto formateado con la memoria de cálculo
    """
```

### 2. Estructura de la Memoria

#### SECCIÓN 1: DATOS DE ENTRADA
- **Identificación del cable**: ID, nombre, tipo
- **Tabla de propiedades**: Formato tabular con parámetro, símbolo, valor, unidad
- **Parámetros de vano**: Longitud, desnivel (si aplica)
- **Estados climáticos**: Temperatura, viento, hielo por estado
- **Parámetros de viento**: Exposición, clase, alturas efectivas, coeficientes
- **Restricciones**: Tensión máxima por estado, relación flecha (si es guardia)
- **Objetivo de optimización**: FlechaMin o TiroMin

#### SECCIÓN 2: ECUACIONES Y MÉTODOS
- **Ecuación de cambio de estado**: Ecuación cúbica t³ + A·t² + B = 0
- **Coeficientes A y B**: Fórmulas con valores sustituidos
- **Método de resolución**: Newton-Raphson para ecuación cúbica
- **Carga de peso**: Peso cable + peso hielo (si aplica)
- **Carga de viento**: Fórmula AEA 95301 con factores Zp, G, Fc
- **Carga vectorial**: G = √(peso² + viento²)
- **Flecha**: f = (G × L²) / (8 × T)

#### SECCIÓN 3: PROCESO DE OPTIMIZACIÓN
- **Estado básico inicial**: Primer estado climático
- **Iteración de estado básico**: Proceso hasta convergencia
- **Búsqueda incremental**: Pasos según objetivo (FlechaMin: ↑tensión, TiroMin: ↓tensión)
- **Verificación de restricciones**: Por cada estado climático
- **Ajuste fino**: Fases de 1%, 0.1%, 0.01%

#### SECCIÓN 4: CÁLCULOS POR ESTADO
Para cada estado climático:
- **Cargas aplicadas**: Peso, hielo, viento
- **Resolución ecuación cúbica**: Valores A, B, solución t
- **Resultados**: Tensión, tiro, flechas, % rotura

#### SECCIÓN 5: RESULTADOS FINALES
- **Tabla resumen**: Todos los estados con valores finales
- **Estado limitante**: Cuál restricción determinó la solución
- **Tensión optimizada**: Valor final y estado básico
- **Verificación restricciones**: Cumplimiento por estado

### 3. Función auxiliar para tabla de propiedades

```python
def _generar_tabla_propiedades_cable(cable_aea):
    """Genera tabla formateada de propiedades del cable"""
    props = cable_aea.propiedades
    
    # Mapeo de propiedades a formato tabla
    propiedades_tabla = [
        ("Sección nominal", "Sn", props.get("seccion_nominal", "-"), "mm²"),
        ("Sección total", "S", f"{cable_aea.seccion_mm2:.1f}", "mm²"),
        ("Diámetro total", "d", f"{cable_aea.diametro_m*1000:.1f}", "mm"),
        ("Peso unitario", "p", f"{cable_aea.peso_unitario_dan_m:.3f}", "daN/m"),
        ("Carga rotura mínima", "Pr", f"{cable_aea.carga_rotura_dan:.1f}", "daN"),
        ("Tensión rotura mínima", "σr", f"{cable_aea.carga_rotura_dan/cable_aea.seccion_mm2:.1f}", "daN/mm²"),
        ("Módulo elasticidad", "E", f"{cable_aea.modulo_elasticidad_dan_mm2:.2f}", "daN/mm²"),
        ("Coeficiente dilatación", "α", f"{cable_aea.coeficiente_dilatacion:.2e}", "1/°C"),
        ("Norma fabricación", "-", props.get("norma_fabricacion", "-"), "-")
    ]
    
    # Formatear tabla
    tabla = []
    tabla.append("Parámetro                    | Símbolo | Valor      | Unidad")
    tabla.append("-" * 60)
    
    for parametro, simbolo, valor, unidad in propiedades_tabla:
        tabla.append(f"{parametro:<28} | {simbolo:<7} | {valor:<10} | {unidad}")
    
    return "\n".join(tabla)
```

### 4. Integración en Cable_AEA

#### Modificar método `calculo_mecanico()`
```python
def calculo_mecanico(self, ...):
    # ... código existente ...
    
    # Al final, generar memoria de cálculo
    from utils.memoria_calculo_cmc import gen_memoria_calculo_CMC
    
    memoria_calculo = gen_memoria_calculo_CMC(
        cable_aea=self,
        vano=vano,
        estados_climaticos=estados_climaticos,
        parametros_viento=parametros_viento,
        restricciones=restricciones,
        objetivo=objetivo,
        resultados_finales=resultados_final,
        t_final=t_final,
        q0_final=q0_final,
        estado_limitante=estado_limitante
    )
    
    # Agregar memoria al resultado
    return df_resultados, resultados_final, estado_limitante, memoria_calculo
```

### 4. Actualizar Callers

#### `utils/calculo_mecanico_cables.py`
- Capturar memoria de cálculo de cada cable
- Almacenar en resultados del cálculo

#### Controllers que usen CMC
- Guardar memoria en cache junto con otros resultados
- Mostrar memoria en vistas de resultados

### 5. Formato de Salida

#### Ejemplo de estructura:
```
CALCULO MECANICO DE CABLES - METODO AEA 95301
================================================================

DATOS DE ENTRADA
----------------------------------------
Cable: OPGW 44F70s 24FO 120mm2
Tipo: OPGW
Material: ACS/A

PROPIEDADES DEL CABLE
----------------------------------------
Parámetro                    | Símbolo | Valor      | Unidad
-----------------------------|---------|------------|--------
Sección nominal              | Sn      | 120        | mm²
Sección total                | S       | 120.0      | mm²
Diámetro total               | d       | 14.4       | mm
Peso unitario                | p       | 0.686      | daN/m
Carga rotura mínima          | Pr      | 11090.6    | daN
Tensión rotura mínima        | σr      | 92.4       | daN/mm²
Carga máxima trabajo         | Pt      | 4436.2     | daN
Tensión máxima trabajo       | σt      | 37.0       | daN/mm²
Módulo elasticidad           | E       | 12845.86   | daN/mm²
Coeficiente dilatación       | α       | 1.4e-05    | 1/°C
Norma fabricación            | -       | IEC/EN 60794| -

PARAMETROS DE CALCULO
----------------------------------------
Vano regulador: 400.0 m
Objetivo optimización: FlechaMin

Estados climáticos:
  I - Tmáx (35°C, sin viento, sin hielo)
  II - Tmín (-20°C, sin viento, sin hielo)
  III - Viento máximo (15°C, 120 km/h, sin hielo)
  IV - Hielo (0°C, sin viento, 6mm hielo)
  V - Hielo + viento (0°C, 60 km/h, 6mm hielo)

ECUACIONES Y METODOS
----------------------------------------
Ecuación de cambio de estado:
  t³ + A·t² + B = 0

Donde:
  A = (L²·E·Go²)/(24·t0²·S²) + α·E·(q-q0) - t0
  B = -(L²·E·G²)/(24·S²)

Valores:
  L = 400.0 m
  E = 6800.0 daN/mm²
  S = 490.0 mm²
  α = 19.3e-6 1/°C

PROCESO DE OPTIMIZACION
----------------------------------------
Objetivo: FlechaMin (minimizar flecha, aumentar tensión)
Tensión inicial: 1.36 daN/mm² (1% de rotura)
Búsqueda incremental: pasos de 1% hasta violación
Estado básico final: Estado II (Tmín)
Tensión optimizada: 5.58 daN/mm²

CALCULOS POR ESTADO CLIMATICO
----------------------------------------
Estado I (Tmáx - 35°C):
  Carga peso: 1.653 daN/m
  Carga viento: 0.000 daN/m
  Carga vectorial: 1.653 daN/m
  Coeficientes: A = -2.847, B = -1247.8
  Tensión: 3.42 daN/mm² 
  Tiro: 1675.8 daN
  Flecha vertical: 15.84 m
  % rotura: 12.3%

[... otros estados ...]

RESULTADOS FINALES
----------------------------------------
Estado limitante: Estado II (restricción tensión máxima 40%)
Tensión final: 5.58 daN/mm²
Estado básico: Estado II (-20°C)

Verificación restricciones:
✓ Estado I: 12.3% < 25% (OK)
✓ Estado II: 40.0% = 40% (LÍMITE)
✓ Estado III: 38.7% < 40% (OK)
✓ Estado IV: 35.2% < 40% (OK)
✓ Estado V: 25.1% < 25% (OK)

================================================================
```

## Cronograma de Implementación

### Fase 1: Estructura básica (1 sesión)
- Crear `utils/memoria_calculo_cmc.py`
- Implementar secciones 1 y 5 (datos entrada y resultados)
- Integrar en `Cable_AEA.calculo_mecanico()`

### Fase 2: Ecuaciones y métodos (1 sesión)
- Implementar sección 2 (ecuaciones)
- Implementar sección 3 (proceso optimización)
- Validar fórmulas con casos conocidos

### Fase 3: Cálculos detallados (1 sesión)
- Implementar sección 4 (cálculos por estado)
- Agregar verificación de restricciones
- Formatear salida completa

### Fase 4: Integración (1 sesión)
- Actualizar `calculo_mecanico_cables.py`
- Modificar controllers para guardar memoria
- Agregar visualización en vistas

## Consideraciones Técnicas

### Acceso a datos internos
- Usar métodos públicos de `Cable_AEA` cuando sea posible
- Acceder a atributos privados solo si es necesario
- Documentar dependencias internas

### Formato matemático
- Usar notación científica para números muy pequeños
- Mostrar 3-4 decimales para valores de ingeniería
- Incluir unidades en todas las fórmulas

### Manejo de casos especiales
- Cable ACSS (usar propiedades de acero)
- Vanos desnivelados
- Estados sin convergencia
- Restricciones no aplicables

### Performance
- Generar memoria solo cuando se solicite explícitamente
- Cachear cálculos intermedios si es necesario
- Limitar longitud de salida para casos complejos