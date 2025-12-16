# Despliegue en Render

## Archivos de configuración creados

1. **Procfile** - Define cómo ejecutar la app con Gunicorn
2. **runtime.txt** - Especifica la versión de Python
3. **requirements.txt** - Actualizado con gunicorn
4. **app.py** - Modificado para exponer el servidor Flask

## Pasos para desplegar en Render

### 1. Preparar el repositorio Git

```bash
git init
git add .
git commit -m "Preparar app para deploy en Render"
```

Subir a GitHub/GitLab/Bitbucket

### 2. Crear Web Service en Render

1. Ir a https://render.com y crear cuenta
2. Click en "New +" → "Web Service"
3. Conectar tu repositorio
4. Configurar:
   - **Name**: agp-estructural (o el nombre que prefieras)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: Se detecta automáticamente del Procfile
   - **Instance Type**: Free (o el que necesites)

### 3. Variables de entorno (opcional)

En la sección "Environment" de Render, agregar:
- `DEBUG=false` (para producción)
- `PORT` (se configura automáticamente por Render)

### 4. Deploy

Click en "Create Web Service" y esperar a que se despliegue.

## Configuración de Gunicorn

El Procfile usa:
- **workers**: 2 (ajustar según recursos)
- **timeout**: 120 segundos (para cálculos largos)
- **bind**: 0.0.0.0:$PORT (puerto dinámico de Render)

## Consideraciones importantes

### Persistencia de datos
- Los archivos en `/data/` se perderán en cada redeploy
- Considerar usar:
  - Base de datos (PostgreSQL en Render)
  - Almacenamiento externo (S3, Cloudinary)
  - Render Disks (persistencia de archivos)

### Memoria y CPU
- Free tier: 512MB RAM, puede ser insuficiente para cálculos grandes
- Considerar upgrade a plan pagado si es necesario

### Timeouts
- Render Free tier: 30 segundos de inactividad
- Configurado 120 segundos en Gunicorn para cálculos largos
- Considerar plan pagado para timeouts mayores

## Alternativas de configuración

### Más workers (para más tráfico)
```
web: gunicorn app:server --bind 0.0.0.0:$PORT --timeout 120 --workers 4
```

### Con threads (mejor para I/O)
```
web: gunicorn app:server --bind 0.0.0.0:$PORT --timeout 120 --workers 2 --threads 2
```

### Con worker class gevent (asíncrono)
```
web: gunicorn app:server --bind 0.0.0.0:$PORT --timeout 120 --workers 2 --worker-class gevent
```
(Requiere agregar `gevent` a requirements.txt)

## Testing local con Gunicorn

```bash
pip install -r requirements.txt
gunicorn app:server --bind 0.0.0.0:8050 --timeout 120 --workers 2
```

Abrir http://localhost:8050

## Troubleshooting

### Error: "Failed to bind to 0.0.0.0:$PORT"
- Verificar que `server = app.server` esté en app.py
- Verificar que PORT esté configurado en variables de entorno

### Error: "Worker timeout"
- Aumentar timeout en Procfile
- Optimizar cálculos largos
- Considerar procesamiento asíncrono

### Error: "Out of memory"
- Reducir workers en Procfile
- Upgrade a plan con más RAM
- Optimizar uso de memoria en cálculos
