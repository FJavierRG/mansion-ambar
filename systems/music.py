"""
Sistema de música para el juego roguelike.
Maneja la reproducción de música de fondo.
"""
from __future__ import annotations
import os
import pygame


class MusicManager:
    """
    Gestor de música del juego.
    
    Carga y reproduce música de fondo usando pygame.mixer.
    """
    
    def __init__(self) -> None:
        """Inicializa el gestor de música."""
        self._music_loaded = False
        self._music_playing = False
        self._volume = 0.5  # Volumen por defecto (0.0 a 1.0)
        self._sound_volume = 0.7  # Volumen para efectos de sonido
        
        # Ruta a la carpeta de música
        self._music_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "sprites",
            "music"
        )
        
        # Inicializar el mixer de pygame
        try:
            pygame.mixer.init()
            self._mixer_available = True
            # Canal para efectos de sonido
            self._sound_channel = pygame.mixer.Channel(0)
        except pygame.error:
            print("[MusicManager] No se pudo inicializar el mixer de audio")
            self._mixer_available = False
            self._sound_channel = None
    
    def load_music(self, filename: str = "dungeonTheme.mp3") -> bool:
        """
        Carga un archivo de música.
        
        Args:
            filename: Nombre del archivo de música
            
        Returns:
            True si se cargó correctamente
        """
        if not self._mixer_available:
            return False
        
        filepath = os.path.join(self._music_path, filename)
        
        try:
            if os.path.exists(filepath):
                pygame.mixer.music.load(filepath)
                self._music_loaded = True
                print(f"[MusicManager] Música cargada: {filename}")
                return True
            else:
                print(f"[MusicManager] Archivo no encontrado: {filepath}")
                return False
        except pygame.error as e:
            print(f"[MusicManager] Error cargando música: {e}")
            return False
    
    def play(self, loops: int = -1, fade_ms: int = 1000) -> None:
        """
        Reproduce la música cargada.
        
        Args:
            loops: Número de repeticiones (-1 = infinito)
            fade_ms: Tiempo de fade in en milisegundos
        """
        if not self._mixer_available or not self._music_loaded:
            return
        
        try:
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
            self._music_playing = True
            print("[MusicManager] Reproduciendo música")
        except pygame.error as e:
            print(f"[MusicManager] Error reproduciendo música: {e}")
    
    def stop(self, fade_ms: int = 500) -> None:
        """
        Detiene la música.
        
        Args:
            fade_ms: Tiempo de fade out en milisegundos
        """
        if not self._mixer_available:
            return
        
        try:
            if fade_ms > 0:
                pygame.mixer.music.fadeout(fade_ms)
            else:
                pygame.mixer.music.stop()
            self._music_playing = False
        except pygame.error:
            pass
    
    def pause(self) -> None:
        """Pausa la música."""
        if not self._mixer_available:
            return
        
        try:
            pygame.mixer.music.pause()
            self._music_playing = False
        except pygame.error:
            pass
    
    def unpause(self) -> None:
        """Reanuda la música pausada."""
        if not self._mixer_available:
            return
        
        try:
            pygame.mixer.music.unpause()
            self._music_playing = True
        except pygame.error:
            pass
    
    def set_volume(self, volume: float) -> None:
        """
        Establece el volumen de la música.
        
        Args:
            volume: Volumen de 0.0 a 1.0
        """
        self._volume = max(0.0, min(1.0, volume))
        
        if self._mixer_available:
            try:
                pygame.mixer.music.set_volume(self._volume)
            except pygame.error:
                pass
    
    def get_volume(self) -> float:
        """Retorna el volumen actual."""
        return self._volume
    
    def is_playing(self) -> bool:
        """Verifica si la música está reproduciéndose."""
        if not self._mixer_available:
            return False
        
        try:
            return pygame.mixer.music.get_busy()
        except pygame.error:
            return False
    
    def toggle_mute(self) -> bool:
        """
        Alterna entre silencio y volumen normal.
        
        Returns:
            True si ahora está silenciado
        """
        if self._volume > 0:
            self._previous_volume = self._volume
            self.set_volume(0.0)
            return True
        else:
            self.set_volume(getattr(self, '_previous_volume', 0.5))
            return False
    
    def stop_aggressive(self, fade_ms: int = 200) -> None:
        """
        Detiene la música con un fadeout agresivo (rápido).
        
        Args:
            fade_ms: Tiempo de fade out en milisegundos (por defecto 200ms)
        """
        if not self._mixer_available:
            return
        
        try:
            pygame.mixer.music.fadeout(fade_ms)
            self._music_playing = False
        except pygame.error:
            pass
    
    def play_sound(self, filename: str, volume: float = None) -> bool:
        """
        Reproduce un efecto de sonido.
        
        Args:
            filename: Nombre del archivo de sonido
            volume: Volumen (0.0 a 1.0), usa self._sound_volume si es None
            
        Returns:
            True si se reprodujo correctamente
        """
        if not self._mixer_available or not self._sound_channel:
            return False
        
        filepath = os.path.join(self._music_path, filename)
        
        try:
            if os.path.exists(filepath):
                sound = pygame.mixer.Sound(filepath)
                play_volume = volume if volume is not None else self._sound_volume
                sound.set_volume(play_volume)
                self._sound_channel.play(sound)
                print(f"[MusicManager] Reproduciendo sonido: {filename}")
                return True
            else:
                print(f"[MusicManager] Archivo de sonido no encontrado: {filepath}")
                return False
        except pygame.error as e:
            print(f"[MusicManager] Error reproduciendo sonido: {e}")
            return False
    
    def stop_all_sounds(self) -> None:
        """Detiene todos los efectos de sonido."""
        if self._sound_channel:
            self._sound_channel.stop()
    
    def stop_all(self) -> None:
        """Detiene música y efectos de sonido."""
        self.stop(fade_ms=0)
        self.stop_all_sounds()


# Instancia global del gestor de música
music_manager = MusicManager()
