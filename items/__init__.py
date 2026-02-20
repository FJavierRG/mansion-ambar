"""
Módulo de items del juego.
Contiene clases para diferentes tipos de items.
"""
from .item import Item, create_item, get_all_item_ids
from .potion import Potion
from .weapon import Weapon
from .armor import Armor
from .special import Amulet, Gold

__all__ = [
    "Item", "Potion", "Weapon", "Armor", "Amulet", "Gold",
    "create_item", "get_all_item_ids",
]
