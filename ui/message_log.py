"""
Sistema de log de mensajes del juego.
"""
from __future__ import annotations
from typing import List, Tuple
from collections import deque

from ..config import MESSAGE_LOG_MAX_MESSAGES, COLORS


class MessageLog:
    """
    Log de mensajes del juego.
    
    Almacena y gestiona los mensajes mostrados al jugador.
    
    Attributes:
        messages: Cola de mensajes
        max_messages: Número máximo de mensajes a almacenar
    """
    
    def __init__(self, max_messages: int = MESSAGE_LOG_MAX_MESSAGES) -> None:
        """
        Inicializa el log de mensajes.
        
        Args:
            max_messages: Máximo de mensajes a almacenar
        """
        self.messages: deque[Tuple[str, str]] = deque(maxlen=max_messages)
        self.max_messages = max_messages
    
    def add(self, text: str, color: str = "message") -> None:
        """
        Añade un mensaje al log.
        
        Args:
            text: Texto del mensaje
            color: Color del mensaje (clave en COLORS)
        """
        self.messages.append((text, color))
    
    def add_multiple(self, texts: List[str], color: str = "message") -> None:
        """
        Añade múltiples mensajes al log.
        
        Args:
            texts: Lista de textos
            color: Color para todos los mensajes
        """
        for text in texts:
            self.add(text, color)
    
    def get_recent(self, count: int = 5) -> List[Tuple[str, str]]:
        """
        Obtiene los mensajes más recientes.
        
        Args:
            count: Número de mensajes a obtener
            
        Returns:
            Lista de tuplas (texto, color)
        """
        return list(self.messages)[-count:]
    
    def clear(self) -> None:
        """Limpia todos los mensajes."""
        self.messages.clear()
    
    def get_color_rgb(self, color_key: str) -> Tuple[int, int, int]:
        """
        Obtiene el color RGB para una clave de color.
        
        Args:
            color_key: Clave del color
            
        Returns:
            Tupla RGB
        """
        return COLORS.get(color_key, COLORS["message"])
