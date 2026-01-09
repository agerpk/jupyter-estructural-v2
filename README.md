# AGP - Análisis General de Postaciones

Aplicación web para diseño y análisis de estructuras de líneas de transmisión eléctrica.

## Características

- Cálculo mecánico de cables (CMC)
- Diseño geométrico de estructuras (DGE)
- Diseño mecánico de estructuras (DME)
- Selección de postes de hormigón (SPH)
- Generación de árboles de carga
- Análisis estático de esfuerzos (AEE) con OpenSeesPy
- Gestión de familias de estructuras
- Análisis de vano económico

## Despliegue en Render

### Opción 1: Despliegue Automático con render.yaml

1. Crear cuenta en [Render](https://render.com)
2. Conectar repositorio de GitHub
3. Render detectará automáticamente `render.yaml` y configurará el servicio
4. El despliegue se iniciará automáticamente

### Opción 2: Despliegue Manual

1. Crear nuevo Web Service en Render
2. Conectar repositorio
3. Configurar:
   - **Name**: agp-estructural
   - **Environment**: Python 3
   - **Region**: Oregon (o la más cercana)
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. Variables de entorno:
   - `PYTHON_VERSION`: 3.11.0
   - `DEBUG_MODE`: false
5. Hacer clic en "Create Web Service"

### Configuración Adicional

#### Plan Free
- 512 MB RAM
- Servicio se suspende después de 15 minutos de inactividad
- Primer arranque puede tardar 30-60 segundos

#### Plan Starter ($7/mes)
- 512 MB RAM
- Sin suspensión automática
- Mejor rendimiento

## Desarrollo Local

### Requisitos
- Python 3.11+
- pip

### Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd jupyter_estructural_v2

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python app.py
```

La aplicación estará disponible en `http://localhost:8050`

## Estructura del Proyecto

```
jupyter_estructural_v2/
├── app.py                 # Aplicación principal
├── requirements.txt       # Dependencias Python
├── Procfile              # Configuración Render/Heroku
├── runtime.txt           # Versión Python
├── render.yaml           # Configuración automática Render
├── config/               # Configuración
├── controllers/          # Lógica de negocio (MVC)
├── models/               # Modelos de datos
├── views/                # Vistas (UI)
├── components/           # Componentes Dash reutilizables
├── utils/                # Utilidades
├── data/                 # Datos y cache
└── docs/                 # Documentación
```

## Tecnologías

- **Framework**: Dash (Plotly)
- **Backend**: Flask + Gunicorn
- **Análisis**: OpenSeesPy, NumPy, SciPy, Pandas
- **Visualización**: Plotly, Matplotlib
- **UI**: Dash Bootstrap Components

