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
    Soporta scroll para revisar mensajes antiguos.
    
    Attributes:
        messages: Cola de mensajes
        max_messages: Número máximo de mensajes a almacenar
        scroll_offset: Desplazamiento actual del scroll (0 = más recientes)
    """
    
    def __init__(self, max_messages: int = MESSAGE_LOG_MAX_MESSAGES) -> None:
        """
        Inicializa el log de mensajes.
        
        Args:
            max_messages: Máximo de mensajes a almacenar
        """
        self.messages: deque[Tuple[str, str]] = deque(maxlen=max_messages)
        self.max_messages = max_messages
        self.scroll_offset: int = 0
    
    def add(self, text: str, color: str = "message") -> None:
        """
        Añade un mensaje al log.
        Al añadir un mensaje nuevo, el scroll vuelve al final (más recientes).
        
        Args:
            text: Texto del mensaje
            color: Color del mensaje (clave en COLORS)
        """
        self.messages.append((text, color))
        self.scroll_offset = 0
    
    def add_multiple(self, texts: List[str], color: str = "message") -> None:
        """
        Añade múltiples mensajes al log.
        
        Args:
            texts: Lista de textos
            color: Color para todos los mensajes
        """
        for text in texts:
            self.messages.append((text, color))
        self.scroll_offset = 0
    
    def get_recent(self, count: int = 5) -> List[Tuple[str, str]]:
        """
        Obtiene los mensajes visibles teniendo en cuenta el scroll.
        
        Args:
            count: Número de mensajes a mostrar
            
        Returns:
            Lista de tuplas (texto, color)
        """
        all_msgs = list(self.messages)
        total = len(all_msgs)
        
        if total == 0:
            return []
        
        # end apunta al último mensaje visible (exclusivo)
        end = total - self.scroll_offset
        start = max(0, end - count)
        
        return all_msgs[start:end]
    
    @property
    def can_scroll_up(self) -> bool:
        """Indica si se puede hacer scroll hacia arriba (hay mensajes más antiguos)."""
        from ..config import MESSAGE_LOG_HEIGHT
        return self.scroll_offset < len(self.messages) - MESSAGE_LOG_HEIGHT
    
    @property
    def can_scroll_down(self) -> bool:
        """Indica si se puede hacer scroll hacia abajo (hay mensajes más recientes)."""
        return self.scroll_offset > 0
    
    def scroll_up(self, amount: int = 1) -> None:
        """Hace scroll hacia arriba (mensajes más antiguos)."""
        from ..config import MESSAGE_LOG_HEIGHT
        max_offset = max(0, len(self.messages) - MESSAGE_LOG_HEIGHT)
        self.scroll_offset = min(self.scroll_offset + amount, max_offset)
    
    def scroll_down(self, amount: int = 1) -> None:
        """Hace scroll hacia abajo (mensajes más recientes)."""
        self.scroll_offset = max(0, self.scroll_offset - amount)
    
    def scroll_reset(self) -> None:
        """Resetea el scroll al final (mensajes más recientes)."""
        self.scroll_offset = 0
    
    def clear(self) -> None:
        """Limpia todos los mensajes."""
        self.messages.clear()
        self.scroll_offset = 0
    
    def get_color_rgb(self, color_key: str) -> Tuple[int, int, int]:
        """
        Obtiene el color RGB para una clave de color.
        
        Args:
            color_key: Clave del color
            
        Returns:
            Tupla RGB
        """
        return COLORS.get(color_key, COLORS["message"])
