"""Fix para generar HTML de familia - funciones auxiliares"""
import logging
logger = logging.getLogger(__name__)

def _safe_format(value, fmt=None, default="N/A", name=None):
    try:
        if value is None:
            logger.debug(f"Valor None al formatear: {name}")
            return default
        if fmt and isinstance(value, (int, float)):
            try:
                return format(value, fmt)
            except Exception as e:
                logger.debug(f"Error formateando {name} con fmt '{fmt}': {e} - valor={value}")
                return default
        return str(value)
    except Exception as e:
        logger.exception(f"Error en _safe_format {name}: {e}")
        return default


def generar_seccion_costeo_estructura(calculo_costeo):
    """Genera HTML para costeo de estructura individual"""
    if not calculo_costeo:
        return '<p>No hay datos de costeo</p>'
    
    resultados = calculo_costeo.get('resultados', {})
    resumen = resultados.get('resumen_costos', {})
    
    if not resumen:
        return '<p>No hay resumen de costos</p>'
    
    html = ['<h5>Resumen de Costos</h5>', '<table class="table table-bordered">']
    for campo, valor in resumen.items():
        if isinstance(valor, (int, float)):
            valor_str = _safe_format(valor, ",.2f", name=f"costeo_estructura.{campo}")
            html.append(f'<tr><td><strong>{campo}</strong></td><td>{valor_str} UM</td></tr>')
        else:
            html.append(f'<tr><td><strong>{campo}</strong></td><td>{valor}</td></tr>')
    html.append('</table>')
    return '\n'.join(html)
