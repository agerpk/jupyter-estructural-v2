import re

with open('c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2/utils/analisis_estatico.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar comillas escapadas
content = content.replace("\\'logaritmica\\'", '"logaritmica"')
content = content.replace("\\'lineal\\'", '"lineal"')
content = content.replace("'logaritmica'", '"logaritmica"')
content = content.replace("'lineal'", '"lineal"')

with open('c:/Users/gpesoa/MobiDrive/jupyter_estructural_v2/utils/analisis_estatico.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Comillas corregidas")
