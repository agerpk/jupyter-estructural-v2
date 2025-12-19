# No Hot Reload

El usuario recarga la aplicación manualmente entre cambios de código, ejecutando `python app.py` desde el comando inicial cada vez.

**NO se usa hot reload** en esta aplicación porque:
- Causa reinicios automáticos de vistas que pierden resultados de cálculos
- Interfiere con callbacks y estado de la aplicación
- El usuario prefiere control manual sobre cuándo recargar

## Configuración

La aplicación debe ejecutarse con:
```python
app.run(debug=False, port=APP_PORT)
```

NO usar:
- `debug=True`
- `dev_tools_hot_reload=True`
- `dev_tools_ui=True`

## Workflow de Desarrollo

1. Hacer cambios en código
2. Detener app (Ctrl+C)
3. Ejecutar `python app.py`
4. Probar cambios en navegador
