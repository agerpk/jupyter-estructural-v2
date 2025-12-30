# Guía de Despliegue en Render

## Configuración para Render

### Archivos de Configuración

1. **Procfile**: Define el comando para ejecutar la aplicación
   ```
   web: gunicorn app:server --bind 0.0.0.0:$PORT --timeout 120 --workers 2
   ```

2. **requirements.txt**: Dependencias de Python
   ```
   dash>=2.14.0
   dash-bootstrap-components>=1.5.0
   pandas>=2.0.0
   numpy>=1.24.0
   matplotlib>=3.7.0
   plotly>=5.15.0
   kaleido>=0.2.1
   openpyxl>=3.1.0
   gunicorn>=21.2.0
   ```

3. **runtime.txt**: Versión de Python
   ```
   python-3.11.0
   ```

### Variables de Entorno en Render

- `PORT`: Automáticamente configurado por Render
- `DEBUG`: Establecer como `false` para producción
- Otras variables se configuran automáticamente desde `app_config.py`

### Configuración de la Aplicación

La aplicación está configurada para:
- Usar el puerto proporcionado por Render (`$PORT`)
- Ejecutarse en modo producción (debug=False)
- Servir archivos estáticos correctamente
- Manejar timeouts largos para cálculos complejos

### Pasos para Desplegar

1. **Conectar Repositorio**:
   - Crear cuenta en Render.com
   - Conectar repositorio de GitHub
   - Seleccionar "Web Service"

2. **Configuración del Servicio**:
   - **Name**: `agp-postaciones`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: Se usa automáticamente desde Procfile

3. **Variables de Entorno**:
   - `DEBUG`: `false`
   - Otras variables se configuran automáticamente

4. **Configuración Avanzada**:
   - **Instance Type**: Starter (gratuito) o Professional según necesidades
   - **Auto-Deploy**: Habilitado para despliegues automáticos

### Estructura de Archivos para Producción

```
/
├── app.py                 # Aplicación principal
├── Procfile              # Comando de inicio
├── requirements.txt      # Dependencias
├── runtime.txt          # Versión Python
├── config/              # Configuración
├── components/          # Componentes UI
├── controllers/         # Lógica de negocio
├── models/             # Modelos de datos
├── utils/              # Utilidades
├── views/              # Vistas
└── data/               # Datos (cache se ignora)
```

### Consideraciones de Rendimiento

1. **Timeout**: Configurado a 120 segundos para cálculos largos
2. **Workers**: 2 workers para manejar múltiples requests
3. **Cache**: Los archivos de cache se generan dinámicamente
4. **Memoria**: Los cálculos complejos pueden requerir más memoria

### Monitoreo y Logs

- Los logs se pueden ver en el dashboard de Render
- La consola de la aplicación captura output para debugging
- Errores se registran automáticamente

### Actualizaciones

- Los despliegues se activan automáticamente con push a main/master
- La aplicación se reinicia automáticamente tras el despliegue
- Los datos persistentes se mantienen entre despliegues

## Versión Actual: 1.0

### Características de la Versión 1.0

- Cálculo mecánico de cables (CMC)
- Diseño geométrico de estructuras (DGE)
- Diseño mecánico de estructuras (DME)
- Árboles de carga 3D interactivos (ADC)
- Selección de postes de hormigón (SPH)
- Cálculos de fundaciones
- Comparativa de cables
- Sistema de cache inteligente
- Interfaz web responsive
- Exportación de resultados

### Próximas Versiones

- Optimizaciones de rendimiento
- Nuevos tipos de estructuras
- Análisis económico de vanos
- Integración con bases de datos externas