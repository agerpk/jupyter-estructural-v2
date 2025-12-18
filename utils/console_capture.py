"""Captura global de output de consola"""
import sys
from io import StringIO
from threading import Lock

class ConsoleCapture:
    """Captura persistente de stdout/stderr desde inicio de app"""
    
    def __init__(self):
        self.buffer = []
        self.lock = Lock()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.max_lines = 10000
        
    def start(self):
        """Iniciar captura de consola"""
        sys.stdout = self
        sys.stderr = self
        print("🟢 Captura de consola iniciada")
        
    def write(self, text):
        """Capturar texto (llamado por print())"""
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
        with self.lock:
            self.buffer.append(text)
            if len(self.buffer) > self.max_lines:
                self.buffer = self.buffer[-self.max_lines:]
    
    def flush(self):
        """Flush (requerido por interfaz de file)"""
        self.original_stdout.flush()
    
    def isatty(self):
        """Requerido por Click/Flask"""
        return self.original_stdout.isatty()
    
    def fileno(self):
        """Requerido por algunos módulos"""
        return self.original_stdout.fileno()
    
    def __getattr__(self, name):
        """Delegar atributos no implementados al stdout original"""
        return getattr(self.original_stdout, name)
    
    def get_text(self):
        """Obtener todo el texto capturado"""
        with self.lock:
            return "".join(self.buffer)
    
    def clear(self):
        """Limpiar buffer"""
        with self.lock:
            self.buffer = []
            print("🗑️  Buffer de consola limpiado")

# Instancia global única
_console_capture = ConsoleCapture()

def get_console_capture():
    """Obtener instancia global de captura"""
    return _console_capture
