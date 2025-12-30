# Regla: Ejecutar Scripts Python

## COMANDO OBLIGATORIO PARA SCRIPTS

Para ejecutar cualquier script Python (.py) en este proyecto, usar SIEMPRE:

```bash
cd C:\Users\gpesoa\Downloads\portablepy\venvo\Scripts && python.exe [RUTA_COMPLETA_AL_SCRIPT]
```

## EJEMPLOS CORRECTOS

### Ejecutar script de verificación:
```bash
cd C:\Users\gpesoa\Downloads\portablepy\venvo\Scripts && python.exe C:\Users\gpesoa\MobiDrive\jupyter_estructural_v2\verify_deploy.py
```

### Ejecutar app principal:
```bash
cd C:\Users\gpesoa\Downloads\portablepy\venvo\Scripts && python.exe C:\Users\gpesoa\MobiDrive\jupyter_estructural_v2\app.py
```

### Ejecutar cualquier script:
```bash
cd C:\Users\gpesoa\Downloads\portablepy\venvo\Scripts && python.exe C:\Users\gpesoa\MobiDrive\jupyter_estructural_v2\[NOMBRE_SCRIPT].py
```

## ESTRUCTURA DEL COMANDO

1. **cd C:\Users\gpesoa\Downloads\portablepy\venvo\Scripts** - Cambiar al directorio del Python del venv
2. **&&** - Ejecutar siguiente comando solo si el anterior fue exitoso
3. **python.exe** - Ejecutable Python del entorno virtual
4. **[RUTA_COMPLETA_AL_SCRIPT]** - Ruta absoluta al script a ejecutar

## PROHIBIDO

❌ `python script.py`
❌ `C:\Users\gpesoa\Downloads\portablepy\venvo\Scripts\python.exe script.py`
❌ `"C:\Users\gpesoa\Downloads\portablepy\venvo\Scripts\python.exe" script.py`

## OBLIGATORIO

✅ `cd C:\Users\gpesoa\Downloads\portablepy\venvo\Scripts && python.exe [RUTA_COMPLETA]`

## NOTAS IMPORTANTES

- Siempre usar ruta completa al script
- El comando cd && python.exe funciona correctamente
- No usar comillas en la ruta del python.exe
- Verificar que el script exista antes de ejecutar