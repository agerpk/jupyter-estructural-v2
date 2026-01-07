# Implementación: Defasaje de Ménsula por Hielo

## Objetivo
Defasar horizontalmente nodos conductores en una altura específica (primera, segunda o tercera) cuando hay condiciones de hielo, aplicando un offset desde x=0 hacia afuera.

## Variables Nuevas

### Parámetros de Entrada
- **defasaje_mensula_hielo** (bool): Activa/desactiva el defasaje por hielo
- **lmen_extra_hielo** (float): Valor a agregar a coordenada X de nodos conductores (puede ser positivo o negativo)
- **mensula_defasar** (str): Indica en qué altura aplicar defasaje ("primera", "segunda", "tercera")

### Ubicación
- Sección: **Cabezal**
- Categoría: **Cabezal**

## Lógica de Defasaje

### Identificación de Alturas
1. Buscar todos los nodos tipo "conductor" en la estructura
2. Extraer sus coordenadas Z (altura)
3. Ordenar alturas de menor a mayor (ascendente)
4. Asignar nombres:
   - **primera**: Altura más baja (menor Z)
   - **segunda**: Altura media
   - **tercera**: Altura más alta (mayor Z)

### Aplicación del Defasaje
1. Seleccionar altura según `mensula_defasar` (primera/segunda/tercera)
2. Identificar TODOS los nodos conductores en esa altura (pueden ser 2, 4, etc.)
3. Para cada nodo conductor en esa altura:
   - Si `x > 0`: Sumar `lmen_extra_hielo` (defasar hacia derecha)
   - Si `x < 0`: Restar `lmen_extra_hielo` (defasar hacia izquierda, mantener signo)
   - Si `x = 0`: No defasar (nodo centrado)

### Ejemplos

#### Ejemplo 1: Terna Simple Vertical (2 nodos por altura)
```
Configuración:
- Primera altura (z=12.5m): C1_R (x=2.3m), C1_L (x=-2.3m)
- Segunda altura (z=15.8m): C2_R (x=2.3m), C2_L (x=-2.3m)
- Tercera altura (z=19.1m): C3_R (x=2.3m), C3_L (x=-2.3m)

Defasaje: mensula_defasar="segunda", lmen_extra_hielo=0.5m

Resultado:
- C2_R: x = 2.3 + 0.5 = 2.8m
- C2_L: x = -2.3 - 0.5 = -2.8m
```

#### Ejemplo 2: Doble Terna Triangular (4 nodos en altura superior)
```
Configuración:
- Primera altura (z=12.5m): C1A_R, C1A_L, C1B_R, C1B_L (4 nodos)
- Segunda altura (z=19.1m): C3A_R, C3A_L (2 nodos)

Defasaje: mensula_defasar="primera", lmen_extra_hielo=0.3m

Resultado:
- C1A_R: x aumenta +0.3m
- C1A_L: x disminuye -0.3m
- C1B_R: x aumenta +0.3m
- C1B_L: x disminuye -0.3m
(Los 4 nodos se defasan)
```

#### Ejemplo 3: Horizontal Simple (3 nodos, uno centrado)
```
Configuración:
- Primera altura (z=15.0m): C1 (x=-4.5m), C2 (x=0m), C3 (x=4.5m)

Defasaje: mensula_defasar="primera", lmen_extra_hielo=0.4m

Resultado:
- C1: x = -4.5 - 0.4 = -4.9m
- C2: x = 0m (sin cambio, está centrado)
- C3: x = 4.5 + 0.4 = 4.9m
```

## Implementación Técnica

### Método `_aplicar_defasaje_hielo()` en EstructuraAEA_Geometria

```python
def _aplicar_defasaje_hielo(self):
    """
    Aplica defasaje por hielo a nodos conductores en altura seleccionada.
    
    Identifica nodos conductores por altura, ordena alturas ascendentemente,
    y aplica lmen_extra_hielo a todos los nodos en la altura indicada.
    """
    if not self.defasaje_mensula_hielo:
        return
    
    # 1. Recolectar nodos conductores por altura
    nodos_por_altura = {}  # {z: [nombre_nodo1, nombre_nodo2, ...]}
    
    for nombre, nodo in self.nodos.items():
        if nodo.tipo_nodo == "conductor":
            z = nodo.coordenadas[2]
            if z not in nodos_por_altura:
                nodos_por_altura[z] = []
            nodos_por_altura[z].append(nombre)
    
    if len(nodos_por_altura) <= 1:
        return  # No hay múltiples alturas
    
    # 2. Ordenar alturas ascendentemente
    alturas_ordenadas = sorted(nodos_por_altura.keys())
    
    # 3. Mapear nombres a índices
    nombres_alturas = {0: "primera", 1: "segunda", 2: "tercera"}
    
    # 4. Identificar índice de altura a defasar
    indice_defasar = None
    for i, nombre in nombres_alturas.items():
        if nombre == self.mensula_defasar:
            indice_defasar = i
            break
    
    if indice_defasar is None or indice_defasar >= len(alturas_ordenadas):
        return  # Altura no válida
    
    # 5. Obtener altura y nodos a defasar
    altura_defasar = alturas_ordenadas[indice_defasar]
    nodos_defasar = nodos_por_altura[altura_defasar]
    
    # 6. Aplicar defasaje a cada nodo
    for nombre_nodo in nodos_defasar:
        nodo = self.nodos[nombre_nodo]
        x, y, z = nodo.coordenadas
        
        # Solo defasar si x != 0
        if abs(x) > 0.001:
            # Mantener signo: positivo suma, negativo resta
            signo = 1 if x > 0 else -1
            x_nuevo = x + signo * self.lmen_extra_hielo
            nodo.coordenadas = (x_nuevo, y, z)
    
    # 7. Actualizar nodes_key
    self._actualizar_nodes_key()
```

### Integración en `dimensionar_unifilar()`

```python
def dimensionar_unifilar(self, ...):
    # ... código existente hasta crear nodos ...
    
    # CREAR NODOS SEGÚN CONFIGURACIÓN
    self._crear_nodos_estructurales_nuevo(...)
    
    # APLICAR DEFASAJE POR HIELO
    self._aplicar_defasaje_hielo()
    
    # GUARDAR DIMENSIONES
    self.dimensiones = {
        # ... dimensiones existentes ...
        "defasaje_mensula_hielo": self.defasaje_mensula_hielo,
        "lmen_extra_hielo": self.lmen_extra_hielo,
        "mensula_defasar": self.mensula_defasar
    }
```

## Archivos Modificados

### ✅ Completado

1. **data/plantilla.estructura.json** - Campos agregados
2. **utils/parametros_manager.py** - Metadata agregada
3. **EstructuraAEA_Geometria.py** - Lógica implementada
4. **utils/memoria_calculo_dge.py** - Sección agregada
5. **controllers/geometria_controller.py** - Parámetros pasados
6. **components/vista_diseno_geometrico.py** - Info mostrada

## Validaciones

### Pre-condiciones
- `defasaje_mensula_hielo` debe ser bool
- `lmen_extra_hielo` debe ser float (puede ser negativo)
- `mensula_defasar` debe ser "primera", "segunda" o "tercera"

### Durante Ejecución
- Verificar que existen múltiples alturas de conductores
- Verificar que la altura seleccionada existe
- Solo defasar nodos con x != 0

### Post-condiciones
- Coordenadas X modificadas correctamente
- Signo de X preservado
- `nodes_key` actualizado

## Mensajes de Consola

```
Defasando mensula en altura segunda (z = 15.800); valor defasado 0.500
```

## Casos de Prueba

### Caso 1: Terna Simple Vertical
- 3 alturas, 2 nodos por altura
- Defasar segunda altura
- Verificar que solo 2 nodos cambian

### Caso 2: Doble Terna
- 2 alturas, 4 nodos en primera, 2 en segunda
- Defasar primera altura
- Verificar que 4 nodos cambian

### Caso 3: Horizontal
- 1 altura, 3 nodos (uno centrado)
- Defasar primera altura
- Verificar que solo 2 nodos cambian (el centrado no)

## Notas Importantes

1. **Orden de ejecución**: Defasaje se aplica DESPUÉS de crear nodos
2. **Preservación de signo**: Mantiene dirección izquierda/derecha
3. **Nodos centrados**: No se defasan (x=0)
4. **Múltiples nodos**: Todos los nodos en la altura seleccionada se defasan
5. **Compatibilidad**: Si `defasaje_mensula_hielo=False`, no se ejecuta
