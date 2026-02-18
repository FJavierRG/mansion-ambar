"""
Items especiales: Amuleto de Yendor y Oro.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Tuple

from .item import Item
from ..config import SYMBOLS

if TYPE_CHECKING:
    from ..entities.player import Player


class Amulet(Item):
    """
    El Amuleto de Yendor - Objetivo del juego.
    """
    
    def __init__(self, x: int = 0, y: int = 0) -> None:
        """
        Inicializa el amuleto.
        
        Args:
            x: Posición X
            y: Posición Y
        """
        super().__init__(
            x=x,
            y=y,
            char=SYMBOLS["amulet"],
            name="Amuleto de Yendor",
            color="amulet",
            item_type="amulet",
            identified=True,
            usable=False,
            slot=None
        )
    
    def get_description(self) -> str:
        """Retorna la descripción del amuleto."""
        return "El legendario Amuleto de Yendor. ¡Escapa con él!"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el amuleto."""
        data = super().to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Amulet:
        """Crea un amuleto desde un diccionario."""
        return cls(x=data["x"], y=data["y"])


class Gold(Item):
    """
    Monedas de oro.
    """
    
    def __init__(self, x: int = 0, y: int = 0, amount: int = 1) -> None:
        """
        Inicializa el oro.
        
        Args:
            x: Posición X
            y: Posición Y
            amount: Cantidad de oro (siempre 1)
        """
        super().__init__(
            x=x,
            y=y,
            char=SYMBOLS["gold"],
            name="moneda de oro",
            color="gold",
            item_type="gold",
            identified=True,
            usable=False,
            slot=None
        )
        
        self.value = 1
    
    def get_description(self) -> str:
        """Retorna la descripción del oro."""
        return "Una moneda de oro."
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el oro."""
        data = super().to_dict()
        data["value"] = self.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Gold:
        """Crea oro desde un diccionario."""
        return cls(x=data["x"], y=data["y"], amount=data.get("value", 1))
