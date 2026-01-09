# Guía de Despliegue en Render

## Archivos Preparados ✅

- `requirements.txt` - Actualizado con openseespy>=3.5.0
- `Procfile` - Configuración de gunicorn
- `runtime.txt` - Python 3.11.0
- `render.yaml` - Configuración automática de Render
- `README.md` - Documentación del proyecto
- `.env.example` - Variables de entorno de ejemplo
- `app.py` - Configurado con `host='0.0.0.0'` para producción

## Pasos para Desplegar

### 1. Preparar Repositorio Git

```bash
# Si no tienes git inicializado
git init
git add .
git commit -m "Preparar para despliegue en Render"

# Crear repositorio en GitHub y subir
git remote add origin <tu-repo-url>
git push -u origin main
```

### 2. Crear Cuenta en Render

1. Ir a https://render.com
2. Registrarse con GitHub
3. Autorizar acceso a repositorios

### 3. Crear Web Service

#### Opción A: Despliegue Automático (Recomendado)

1. En Render Dashboard, clic en "New +"
2. Seleccionar "Web Service"
3. Conectar repositorio GitHub
4. Render detectará `render.yaml` automáticamente
5. Clic en "Apply" para usar la configuración
6. Clic en "Create Web Service"

#### Opción B: Configuración Manual

1. En Render Dashboard, clic en "New +"
2. Seleccionar "Web Service"
3. Conectar repositorio GitHub
4. Configurar:
   - **Name**: `agp-estructural`
   - **Region**: Oregon (o más cercana)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. Variables de entorno (opcional):
   - `PYTHON_VERSION`: `3.11.0`
   - `DEBUG_MODE`: `false`
   - `RENDER`: `true`
6. Seleccionar plan:
   - **Free**: Para pruebas (se suspende después de 15 min inactividad)
   - **Starter ($7/mes)**: Para producción (sin suspensión)
7. Clic en "Create Web Service"

### 4. Monitorear Despliegue

1. Render mostrará logs en tiempo real
2. El primer despliegue puede tardar 5-10 minutos
3. Buscar mensaje: `Listening at: http://0.0.0.0:XXXXX`
4. La URL pública será: `https://agp-estructural.onrender.com`

### 5. Verificar Funcionamiento

1. Abrir la URL pública
2. Verificar que la aplicación carga correctamente
3. Probar funcionalidades básicas:
   - Crear nueva estructura
   - Cargar estructura desde DB
   - Ejecutar cálculo CMC
   - Ejecutar cálculo DGE

## Limitaciones del Plan Free

- **RAM**: 512 MB (puede ser insuficiente para cálculos grandes)
- **Suspensión**: Después de 15 minutos de inactividad
- **Primer arranque**: 30-60 segundos después de suspensión
- **Horas mensuales**: 750 horas/mes

## Recomendaciones

### Para Plan Free
- Usar para demos y pruebas
- Advertir a usuarios sobre tiempo de arranque
- Evitar cálculos con muchas hipótesis simultáneas

### Para Plan Starter ($7/mes)
- Usar para producción
- Sin suspensión automática
- Mejor rendimiento
- Métricas y logs avanzados

### Optimizaciones Futuras
- Reducir workers de gunicorn si hay problemas de memoria
- Implementar cache de resultados más agresivo
- Considerar plan con más RAM si hay cálculos pesados

## Actualizar Aplicación

```bash
# Hacer cambios en código
git add .
git commit -m "Descripción de cambios"
git push origin main

# Render detectará el push y redesplegará automáticamente
```

## Variables de Entorno en Render

Si necesitas agregar variables de entorno:

1. En Render Dashboard, ir a tu servicio
2. Clic en "Environment"
3. Agregar variables:
   - `DEBUG_MODE`: `false`
   - `RENDER`: `true`
   - Cualquier otra variable necesaria
4. Guardar cambios (redesplegará automáticamente)

## Troubleshooting

### Error: "Application failed to start"
- Verificar logs en Render Dashboard
- Verificar que `requirements.txt` esté completo
- Verificar que `app.py` expone `server`

### Error: "Out of memory"
- Reducir workers en Procfile: `--workers 1`
- Considerar upgrade a plan con más RAM
- Optimizar código para usar menos memoria

### Error: "Build failed"
- Verificar que `runtime.txt` tenga versión válida de Python
- Verificar que todas las dependencias en `requirements.txt` sean compatibles
- Revisar logs de build para errores específicos

### Aplicación muy lenta
- Verificar que no esté en plan Free suspendido
- Considerar upgrade a Starter
- Optimizar consultas y cálculos pesados

