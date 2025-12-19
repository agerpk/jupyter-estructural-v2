# Implementación del Sistema de Morfologías

## Objetivo
Unificar los parámetros TERNA, DISPOSICION, CANT_HG, HG_CENTRADO en un único parámetro MORFOLOGIA para simplificar la configuración y gestión de estructuras eléctricas.

## Reglas de Morfologías Definidas

### Reglas Específicas por Tipo:
1. **Simple Vertical**: Puede llevar 0 o 1 HG, debe tener nodo TOP y lmenhg>0
2. **Simple Horizontal**: Puede tener 0,1,2 HGs
   - 0 HG: No existe TOP ni nodos HG
   - 1 HG: Está centrado (lmenhg=0)
   - 2 HG: Tendrá lmenhg>0, nodo TOP y dos nodos HG (HG1, HG2)
3. **Simple Triangular**: Puede tener 0 o 1 HG
   - 0 HG: No hay nodo TOP ni HG, el más alto será el nodo conductor más alto
   - 1 HG: Puede estar centrado (lmenhg=0) o defasado (lmenhg>0)
4. **Doble Triangular**: Puede haber 0, 1 o 2 HGs
5. **Doble Vertical**: Puede haber 0, 1 o 2 HGs
6. **Doble Horizontal**: No codificar por ahora

### Restricción General:
- **Solo las estructuras horizontales simples pueden tener 2 HG**

## Tabla de Morfologías Válidas

| MORFOLOGIA | CANT_HG | TERNA | DISPOSICION | HG_CENTRADO | CODIFICADA ACTUAL |
|------------|---------|-------|-------------|-------------|-------------------|
| SIMPLE-VERTICAL-NOHG | 0 | Simple | vertical | N/A | ❌ No |
| SIMPLE-VERTICAL-1HG | 1 | Simple | vertical | No | ✅ Sí |
| SIMPLE-TRIANGULAR-NOHG | 0 | Simple | triangular | N/A | ✅ Sí |
| SIMPLE-TRIANGULAR-1HG-CENTRADO | 1 | Simple | triangular | Sí | ❌ No |
| SIMPLE-TRIANGULAR-1HG-DEFASADO | 1 | Simple | triangular | No | ✅ Sí |
| SIMPLE-HORIZONTAL-NOHG | 0 | Simple | horizontal | N/A | ✅ Sí |
| SIMPLE-HORIZONTAL-1HG | 1 | Simple | horizontal | Sí | ✅ Sí |
| SIMPLE-HORIZONTAL-2HG | 2 | Simple | horizontal | No | ✅ Sí |
| DOBLE-VERTICAL-NOHG | 0 | Doble | vertical | N/A | ✅ Sí |
| DOBLE-VERTICAL-1HG | 1 | Doble | vertical | Sí | ✅ Sí |
| DOBLE-VERTICAL-2HG | 2 | Doble | vertical | No | ✅ Sí |
| DOBLE-TRIANGULAR-NOHG | 0 | Doble | triangular | N/A | ✅ Sí |
| DOBLE-TRIANGULAR-1HG | 1 | Doble | triangular | No | ✅ Sí |
| DOBLE-TRIANGULAR-2HG | 2 | Doble | triangular | No | ✅ Sí |

**Total morfologías válidas: 14**
**Actualmente codificadas: 12**
**Por implementar: 2** (SIMPLE-VERTICAL-NOHG, SIMPLE-TRIANGULAR-1HG-CENTRADO)

## Plan de Implementación

### Archivos a Crear:
1. **`EstructuraAEA_Geometria_Morfologias.py`** - Definiciones de nodos, conexiones y coordenadas por morfología

### Archivos a Modificar:
1. **`EstructuraAEA_Geometria.py`** - Agregar parámetro morfología, simplificar creación de nodos
2. **`EstructuraAEA_Graficos.py`** - Usar conexiones de morfología
3. **`utils/arboles_carga.py`** - Usar conexiones de morfología
4. **`data/plantilla.estructura.json`** - Agregar campo MORFOLOGIA

### Arquitectura del Sistema

#### Flujo de Datos:
```
Usuario → MORFOLOGIA → EstructuraAEA_Geometria → Parámetros calculados (D_fases, s_estructura, etc.)
    ↓
EstructuraAEA_Geometria_Morfologias → Nodos + Conexiones + Coordenadas
    ↓
EstructuraAEA_Graficos + arboles_carga.py → Usan conexiones unificadas
```

#### Estructura de EstructuraAEA_Geometria_Morfologias.py:
```python
def crear_nodos_morfologia(morfologia: str, parametros: dict):
    """Crea nodos y conexiones según morfología"""
    # Delega a función específica por morfología
    return nodos, conexiones

def _crear_simple_vertical_1hg(params):
    """Crea nodos específicos para simple vertical 1HG"""
    # Define nodos estructura, conductor, guardia
    # Define conexiones naturales
    # Calcula coordenadas usando parámetros
    return nodos, conexiones
```

#### Modificación de EstructuraAEA_Geometria.py:
```python
# Constructor modificado
def __init__(self, ..., morfologia=None, terna=None, disposicion=None, cant_hg=None, hg_centrado=None):
    if morfologia:
        # Extraer parámetros de morfología para compatibilidad
        params = self._extraer_parametros_morfologia(morfologia)
        self.terna = params["TERNA"]
        self.disposicion = params["DISPOSICION"] 
        self.cant_hg = params["CANT_HG"]
        self.hg_centrado = params["HG_CENTRADO"]
        self.morfologia = morfologia
    else:
        # Compatibilidad: usar parámetros legacy
        self.morfologia = self._inferir_morfologia_desde_parametros()

# Método simplificado
def _crear_nodos_estructurales_nuevo(self, parametros_calculados):
    from EstructuraAEA_Geometria_Morfologias import crear_nodos_morfologia
    self.nodos, self.conexiones = crear_nodos_morfologia(self.morfologia, parametros_calculados)
```

## Definición de Nodos y Conexiones por Morfología

Cada morfología define:
- **Nodos estructura**: BASE, CROSS_H1, Y1, TOP, etc.
- **Nodos conductor**: C1_L, C2_R, etc.
- **Nodos guardia**: HG1, HG2
- **Conexiones naturales**: Lista de tuplas (nodo_origen, nodo_destino, tipo_conexion)

### Tipos de Conexiones:
- `columna`: Conexiones verticales en estructura
- `mensula`: Conexiones horizontales a conductores/guardias
- `cruceta`: Conexiones horizontales entre conductores
- `cadena`: Conexiones editadas por usuario (se agregan después)

### Validación de Conexiones:
- Si nodo1 está conectado a nodo2, automáticamente nodo2 está conectado a nodo1
- Validación de existencia de nodos antes de crear conexiones
- Conexiones recíprocas automáticas

## Compatibilidad y Migración

### Estrategia de Compatibilidad:
1. Mantener campos legacy (TERNA, DISPOSICION, CANT_HG, HG_CENTRADO) durante transición
2. Sincronización bidireccional: cambio en morfología actualiza legacy
3. Constructor acepta tanto morfología como parámetros separados
4. Migración automática al cargar estructuras sin campo MORFOLOGIA

### Migración de Estructuras Existentes:
- Detectar estructuras sin campo MORFOLOGIA
- Inferir morfología desde parámetros legacy
- Agregar campo MORFOLOGIA manteniendo compatibilidad
- Validar consistencia entre morfología y parámetros legacy

## Beneficios del Sistema

1. **Unificación**: Un solo parámetro en lugar de 4 separados
2. **Consistencia**: Una sola fuente de verdad para conexiones entre nodos
3. **Mantenibilidad**: Agregar nueva morfología = agregar definición en un lugar
4. **Eliminación de duplicación**: Lógica de conexiones unificada en todos los archivos
5. **Validación centralizada**: Conexiones y nodos validados automáticamente
6. **Extensibilidad**: Fácil agregar nuevas morfologías sin modificar múltiples archivos

## Implementación por Fases

### Fase 1: Crear EstructuraAEA_Geometria_Morfologias.py
- Definir estructura de datos para morfologías
- Implementar funciones de creación de nodos por morfología
- Implementar cálculo de coordenadas por morfología

### Fase 2: Modificar EstructuraAEA_Geometria.py
- Agregar parámetro morfología al constructor
- Simplificar métodos de creación de nodos
- Mantener compatibilidad con parámetros legacy

### Fase 3: Actualizar archivos dependientes
- Modificar EstructuraAEA_Graficos.py para usar conexiones unificadas
- Modificar utils/arboles_carga.py para usar conexiones unificadas
- Agregar campo MORFOLOGIA a plantilla.estructura.json

### Fase 4: Testing y validación
- Probar todas las morfologías existentes
- Validar que conexiones funcionan correctamente
- Verificar compatibilidad con estructuras existentes

### Fase 5: Implementar morfologías faltantes
- SIMPLE-VERTICAL-NOHG
- SIMPLE-TRIANGULAR-1HG-CENTRADO