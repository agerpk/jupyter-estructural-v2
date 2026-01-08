from utils.calculo_cache import CalculoCache
from pathlib import Path
import json

nombre='PSJ-2X220-DTV-S_BASE_vano350m'
archivo = Path('data/cache')/f'{nombre}.calculoAEE.json'
print('Archivo existe?', archivo.exists())
if archivo.exists():
    data=json.loads(archivo.read_text(encoding='utf-8'))
    resultados=data.get('resultados', {})
    CalculoCache.guardar_calculo_aee(nombre, {}, resultados)
    print('Reescritura realizada')
else:
    print('Archivo no existe')
