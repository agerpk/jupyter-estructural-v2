"""Controlador para Editor de Hipótesis: API de alto nivel para listar/cargar/activar"""
from utils.hipotesis_manager import HipotesisManager


def listar_hipotesis():
    """Retorna la lista de archivos de hipótesis disponibles."""
    return HipotesisManager.listar_hipotesis()


def cargar_hipotesis_por_nombre(nombre):
    """Devuelve el contenido del archivo de hipótesis o None si no existe."""
    return HipotesisManager.cargar_hipotesis_por_nombre(nombre)


def establecer_activa(nombre):
    """Establece la hipótesis activa globalmente."""
    return HipotesisManager.establecer_hipotesis_activa(nombre)


def obtener_activa():
    """Retorna el nombre del archivo de hipótesis activa o None."""
    return HipotesisManager.obtener_hipotesis_activa()


def cargar_activa():
    """Carga el contenido de la hipótesis activa y lo retorna o None."""
    return HipotesisManager.cargar_hipotesis_activa()


def validar_hipotesis(hipotesis_maestro):
    """Valida la estructura de un hipotesis_maestro (retorna tuple)."""
    return HipotesisManager.validar_hipotesis(hipotesis_maestro)


def importar_hipotesis(ruta_externa):
    """Importa un JSON de hipótesis desde ruta externa hacia data/hipotesis."""
    return HipotesisManager.importar_hipotesis_desde_archivo(ruta_externa)


