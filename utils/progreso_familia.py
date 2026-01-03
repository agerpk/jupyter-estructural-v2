"""
Sistema de control de progreso para cálculo de familia
"""

class ProgresoFamilia:
    """Control de progreso y cancelación para cálculo de familia"""
    
    def __init__(self):
        self.cancelado = False
        self.progreso = 0
        self.estructura_actual = ""
        self.paso_actual = ""
        self.total_pasos = 0
        self.pasos_completados = 0
        self.archivos_temporales = []
    
    def reset(self):
        """Reiniciar estado"""
        self.cancelado = False
        self.progreso = 0
        self.estructura_actual = ""
        self.paso_actual = ""
        self.total_pasos = 0
        self.pasos_completados = 0
        self.archivos_temporales = []
    
    def cancelar(self):
        """Marcar como cancelado"""
        self.cancelado = True
    
    def actualizar(self, estructura, paso, pasos_completados, total_pasos):
        """Actualizar progreso"""
        self.estructura_actual = estructura
        self.paso_actual = paso
        self.pasos_completados = pasos_completados
        self.total_pasos = total_pasos
        self.progreso = int((pasos_completados / total_pasos) * 100) if total_pasos > 0 else 0
    
    def agregar_archivo_temporal(self, archivo):
        """Agregar archivo temporal para limpieza"""
        if archivo not in self.archivos_temporales:
            self.archivos_temporales.append(archivo)
    
    def limpiar_archivos_temporales(self):
        """Eliminar archivos temporales"""
        from pathlib import Path
        for archivo in self.archivos_temporales:
            try:
                archivo_path = Path(archivo)
                if archivo_path.exists():
                    archivo_path.unlink()
                    print(f"🧹 Archivo temporal eliminado: {archivo}")
            except Exception as e:
                print(f"⚠️ Error eliminando {archivo}: {e}")
        self.archivos_temporales = []
    
    def obtener_estado(self):
        """Obtener estado actual como dict"""
        return {
            "cancelado": self.cancelado,
            "progreso": self.progreso,
            "estructura_actual": self.estructura_actual,
            "paso_actual": self.paso_actual,
            "pasos_completados": self.pasos_completados,
            "total_pasos": self.total_pasos
        }

# Instancia global
_progreso_global = ProgresoFamilia()

def obtener_progreso():
    """Obtener instancia global de progreso"""
    return _progreso_global
