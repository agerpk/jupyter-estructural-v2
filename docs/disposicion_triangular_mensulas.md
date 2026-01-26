# Disposición Triangular-Mensulas

## Descripción

Nueva disposición geométrica para terna simple que combina características de la disposición triangular con reposicionamiento de conductores en ménsulas.

## Características

- **Aplicable solo a**: Terna Simple
- **No funciona con**: Terna Doble
- **Basada en**: Disposición triangular existente

## Proceso de Dimensionamiento

### Etapa 1 (h1a y Lmen1)
- Funciona **exactamente igual** que disposición triangular
- Crea nodos C1_R, C1_L en h1a
- Calcula Lmen1 según lógica estándar

### Etapa 2 (h2a y reposicionamiento)
Después de calcular h2a y crear el nodo conductor en la posición final:

1. **Crear C3** en posición (Lmen2, 0, h2a) - conductor superior
2. **Reposicionar C2** a altura intermedia:
   - Altura intermedia: `h1ab = (h1a + h2a) / 2`
   - Mantiene coordenada X original
   - Nueva posición: (x_original, 0, h1ab)
3. **Crear CROSS_H3** en (0, 0, h1ab) - nodo de cruce intermedio

## Estructura de Nodos Resultante

```
Altura h2a:  C3 (Lmen2, 0, h2a)
             |
Altura h1ab: C2 (x_c2, 0, h1ab) --- CROSS_H3 (0, 0, h1ab)
             |                        |
Altura h1a:  C1_R (Lmen1, 0, h1a) -- CROSS_H2 (0, 0, h1a)
             C1_L (-Lmen1, 0, h1a) --/
             |
BASE:        (0, 0, 0)
```

## Uso

### En archivo .estructura.json
```json
{
  "DISPOSICION": "triangular-mensulas",
  "TERNA": "Simple",
  ...
}
```

### Validación
- Si `TERNA` != "Simple", el sistema usará disposición triangular estándar
- La disposición solo se activa en Etapa2 cuando se detecta la combinación correcta

## Implementación

### Archivo modificado
- `EstructuraAEA_Geometria_Etapa2.py`

### Cambios realizados
1. Agregado bloque condicional para `disposicion == "triangular-mensulas"`
2. Lógica de creación de C3 en lugar de C2_R
3. Reposicionamiento de C2 existente
4. Creación de CROSS_H3 intermedio
5. Guardado de h1ab en dimensiones

## Notas Técnicas

- El nodo C2 debe existir previamente (creado en Etapa1)
- La altura h1ab se calcula como promedio aritmético de h1a y h2a
- CROSS_H3 permite conexiones estructurales en la altura intermedia
- Compatible con sistema de zonas prohibidas y verificaciones de distancias
- Mantiene compatibilidad con defasaje por hielo y otros parámetros

## Fecha de Implementación
2026-01-23
