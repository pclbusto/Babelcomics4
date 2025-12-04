"""
Sistema de notificación para descargas de covers

Este módulo proporciona un mecanismo de señales para notificar cuando se descargan covers
de issues, permitiendo que la UI se actualice en tiempo real.
"""

import gi
gi.require_version('GObject', '2.0')
from gi.repository import GObject


class CoverDownloadNotifier(GObject.Object):
    """Singleton que notifica cuando se descarga un cover de issue"""

    _instance = None

    # Señal que se emite cuando un cover se descarga exitosamente
    # Parámetros: (id_volume, numero_issue, ruta_archivo)
    __gsignals__ = {
        'cover-downloaded': (GObject.SignalFlags.RUN_FIRST, None, (int, str, str,))
    }

    def __new__(cls):
        """Patrón Singleton - solo una instancia"""
        if cls._instance is None:
            cls._instance = super(CoverDownloadNotifier, cls).__new__(cls)
            GObject.Object.__init__(cls._instance)
        return cls._instance

    def notify_cover_downloaded(self, id_volume, numero_issue, file_path):
        """
        Notificar que un cover fue descargado exitosamente

        Args:
            id_volume: ID del volumen
            numero_issue: Número del issue
            file_path: Ruta del archivo descargado
        """
        print(f"📢 CoverDownloadNotifier: Emitiendo señal para issue #{numero_issue} del volumen {id_volume}")
        self.emit('cover-downloaded', id_volume, numero_issue, file_path)


# Instancia global
_notifier = None

def get_notifier():
    """Obtener la instancia singleton del notificador"""
    global _notifier
    if _notifier is None:
        _notifier = CoverDownloadNotifier()
    return _notifier
