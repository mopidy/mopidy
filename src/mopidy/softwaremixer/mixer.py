import logging
import pykka  # Librería para actores concurrentes
from pykka.typing import proxy_method
from mopidy import mixer  # Importar el módulo de mezclador de Mopidy

logger = logging.getLogger(__name__)  # Configurar el logger

class SoftwareMixer(pykka.ThreadingActor, mixer.Mixer):
    name = "software"  # Nombre del mezclador

    def __init__(self, config):
        super().__init__(config)

        # Variables para almacenar el estado inicial del volumen y el mute
        self._audio_mixer = None
        self._initial_volume = None
        self._initial_mute = None

    def setup(self, mixer_ref):
        # Configuración inicial del mezclador
        self._audio_mixer = mixer_ref

        # Restaurar el volumen inicial si está definido
        if self._initial_volume is not None:
            self.set_volume(self._initial_volume)
        # Restaurar el mute inicial si está definido
        if self._initial_mute is not None:
            self.set_mute(self._initial_mute)

    def teardown(self):
        # Eliminar la referencia al mezclador al finalizar
        self._audio_mixer = None

    def get_volume(self):
        # Obtener el volumen del mezclador si está disponible
        if self._audio_mixer is None:
            return None
        return self._audio_mixer.get_volume().get()

    def set_volume(self, volume):
        # Establecer el volumen en el mezclador si está disponible
        if self._audio_mixer is None:
            self._initial_volume = volume  # Almacenar el volumen para configurar después
            return False
        self._audio_mixer.set_volume(volume)
        return True

    def get_mute(self):
        # Obtener el estado de mute si está disponible
        if self._audio_mixer is None:
            return None
        return self._audio_mixer.get_mute().get()

    def set_mute(self, mute):
        # Establecer el estado de mute si está disponible
        if self._audio_mixer is None:
            self._initial_mute = mute  # Almacenar el mute para configurar después
            return False
        self._audio_mixer.set_mute(mute)
        return True


class SoftwareMixerProxy(mixer.MixerProxy):
    setup = proxy_method(SoftwareMixer.setup)  # Método para configurar el proxy
    teardown = proxy_method(SoftwareMixer.teardown)  # Método para desmontar el proxy
