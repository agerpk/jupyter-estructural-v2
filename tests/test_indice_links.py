import re
from utils.descargar_html_familia_completo import generar_html_familia


def test_indice_targets_exist():
    resultados = {
        "resultados_estructuras": {
            "Estr1": {
                "titulo": "Estructura 1",
                "resultados": {
                    "cmc": {"ok": True},
                    "dge": {"dimensiones": True, "hash_parametros": True},
                    "dme": {"ok": True},
                    "arboles": {"ok": True},
                },
                "cantidad": 1,
            }
        },
        "costeo_global": {}
    }

    html = generar_html_familia("FamiliaX", resultados, checklist_activo=None)

    # Extract index HTML block
    index_match = re.search(r'(<div class="indice">.*?</div>)', html, re.S)
    assert index_match, "Index not found in generated HTML"
    index_html = index_match.group(1)

    # Find targets in index (href or data-bs-target)
    targets = re.findall(r'(?:data-bs-target|href)=["\'](#[^"\']+)["\']', index_html)
    assert targets, "No targets found in index"

    # Each target should correspond to an element with that id in the full HTML
    for t in targets:
        id_attr = f'id="{t[1:]}"'
        assert id_attr in html, f"Target {t} does not match any element id in HTML"

    # Label must include the 'Estructura: ' prefix in the index
    assert 'Estructura: Estructura 1' in index_html

    # Check that DME and DGE fine-grained anchors are present in the body
    assert 'id="Estructura_1_dme_tabla_reacciones"' in html
    assert 'id="Estructura_1_dge_graf_estructura"' in html