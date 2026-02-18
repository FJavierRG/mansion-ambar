"""
Clase base Item y funciones de creación de items.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Tuple, Optional
import random

from ..config import SYMBOLS, POTION_DATA, WEAPON_DATA, ARMOR_DATA

if TYPE_CHECKING:
    from ..entities.player import Player


class Item:
    """
    Clase base para todos los items del juego.
    
    Attributes:
        x: Posición X en el mapa
        y: Posición Y en el mapa
        char: Caracter ASCII
        name: Nombre del item
        color: Color del item
        item_type: Tipo de item (potion, weapon, armor, etc.)
        identified: Si el item ha sido identificado
        usable: Si el item puede usarse
        slot: Slot de equipamiento (si aplica)
        persistent: Si el item persiste al morir (items especiales de misión)
    """
    
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        name: str = "Item",
        color: str = "white",
        item_type: str = "misc",
        identified: bool = True,
        usable: bool = False,
        slot: Optional[str] = None,
        persistent: bool = False
    ) -> None:
        """
        Inicializa un item.
        
        Args:
            x: Posición X
            y: Posición Y
            char: Caracter ASCII
            name: Nombre
            color: Color
            item_type: Tipo
            identified: Si está identificado
            usable: Si es usable
            slot: Slot de equipamiento
            persistent: Si persiste al morir (default: False)
        """
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.item_type = item_type
        self.identified = identified
        self.usable = usable
        self.slot = slot
        self.persistent = persistent
        
        # Propiedades adicionales que pueden ser sobrescritas
        self.attack_bonus = 0
        self.defense_bonus = 0
        self.value = 0
    
    def use(self, player: Player) -> Tuple[List[str], bool]:
        """
        Usa el item.
        
        Args:
            player: El jugador que usa el item
            
        Returns:
            Tupla (mensajes, consumido)
        """
        return ([f"No puedes usar {self.name}."], False)
    
    def get_description(self) -> str:
        """Retorna la descripción del item."""
        return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el item a diccionario."""
        data = {
            "x": self.x,
            "y": self.y,
            "char": self.char,
            "name": self.name,
            "color": self.color,
            "item_type": self.item_type,
            "identified": self.identified,
            "usable": self.usable,
            "slot": self.slot,
            "attack_bonus": self.attack_bonus,
            "defense_bonus": self.defense_bonus,
            "value": self.value,
        }
        # Solo serializar persistent si es True (para no romper saves existentes)
        if self.persistent:
            data["persistent"] = True
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Item:
        """Crea un item desde un diccionario."""
        # Determinar el tipo correcto de item
        item_type = data.get("item_type", "misc")
        
        if item_type == "potion":
            from .potion import Potion
            return Potion.from_dict(data)
        elif item_type == "weapon":
            from .weapon import Weapon
            return Weapon.from_dict(data)
        elif item_type == "armor":
            from .armor import Armor
            return Armor.from_dict(data)
        elif item_type == "gold":
            from .special import Gold
            return Gold.from_dict(data)
        elif item_type == "amulet":
            from .special import Amulet
            return Amulet.from_dict(data)
        else:
            item = cls(
                x=data["x"],
                y=data["y"],
                char=data["char"],
                name=data["name"],
                color=data["color"],
                item_type=item_type,
                identified=data.get("identified", True),
                usable=data.get("usable", False),
                slot=data.get("slot"),
                persistent=data.get("persistent", False),
            )
            item.attack_bonus = data.get("attack_bonus", 0)
            item.defense_bonus = data.get("defense_bonus", 0)
            item.value = data.get("value", 0)
            return item
    
    def __repr__(self) -> str:
        return f"Item({self.name} at ({self.x}, {self.y}))"


def create_item_for_floor(floor: int, x: int, y: int, allowed_types: Optional[List[str]] = None) -> Item:
    """
    Crea un item aleatorio apropiado para el piso actual.
    
    Distribución de probabilidades (pesos):
    - Oro: 35% (consumible común)
    - Poción: 40% (muy necesarias para sobrevivir)
    - Arma: 15% (más raras)
    - Armadura: 10% (las más raras)
    
    Args:
        floor: Número de piso
        x: Posición X
        y: Posición Y
        allowed_types: Lista de tipos permitidos (None = todos). 
                      Opciones: ["weapon", "armor", "potion", "gold"]
        
    Returns:
        Un item apropiado
    """
    from .potion import Potion
    from .weapon import Weapon
    from .armor import Armor
    from .special import Gold
    
    # Si hay tipos permitidos, filtrar según eso
    if allowed_types is None:
        allowed_types = ["weapon", "armor", "potion", "gold"]
    
    # Sistema de pesos para mejor balance
    # Ajustar pesos según qué tipos están permitidos
    total_weight = 0.0
    weights = {}
    
    if "gold" in allowed_types:
        weights["gold"] = 0.35
        total_weight += 0.35
    if "potion" in allowed_types:
        weights["potion"] = 0.40
        total_weight += 0.40
    if "weapon" in allowed_types:
        weights["weapon"] = 0.15
        total_weight += 0.15
    if "armor" in allowed_types:
        weights["armor"] = 0.10
        total_weight += 0.10
    
    # Normalizar pesos si hay tipos restringidos
    if total_weight > 0:
        for key in weights:
            weights[key] = weights[key] / total_weight
    
    # Generar roll normalizado
    roll = random.random() * total_weight
    
    current = 0.0
    if "gold" in allowed_types:
        current += weights["gold"]
        if roll < current:
            amount = random.randint(5, 15) * floor
            return Gold(x, y, amount)
    
    if "potion" in allowed_types:
        current += weights["potion"]
        if roll < current:
            return _create_random_potion(x, y)
    
    if "weapon" in allowed_types:
        current += weights["weapon"]
        if roll < current:
            return _create_random_weapon(floor, x, y)
    
    if "armor" in allowed_types:
        # Armadura (última opción)
        return _create_random_armor(floor, x, y)
    
    # Fallback: oro si nada más está disponible
    amount = random.randint(5, 15) * floor
    return Gold(x, y, amount)


def _create_random_potion(x: int, y: int) -> Item:
    """Crea una poción aleatoria."""
    from .potion import Potion
    
    # Seleccionar tipo basado en rareza
    potions = list(POTION_DATA.items())
    weights = [data["rarity"] for _, data in potions]
    potion_key, potion_data = random.choices(potions, weights=weights)[0]
    
    return Potion(
        x=x,
        y=y,
        potion_type=potion_key,
        name=potion_data["name"],
        effect=potion_data["effect"],
        value=potion_data["value"],
        duration=potion_data.get("duration", 0)
    )


def _create_random_weapon(floor: int, x: int, y: int) -> Item:
    """Crea un arma aleatoria apropiada para el piso."""
    from .weapon import Weapon
    
    # Filtrar armas por nivel mínimo
    valid_weapons = [
        (key, data) for key, data in WEAPON_DATA.items()
        if data["min_level"] <= floor
    ]
    
    if not valid_weapons:
        valid_weapons = [("dagger", WEAPON_DATA["dagger"])]
    
    # Seleccionar basado en rareza
    weights = [data["rarity"] for _, data in valid_weapons]
    weapon_key, weapon_data = random.choices(valid_weapons, weights=weights)[0]
    
    return Weapon(
        x=x,
        y=y,
        weapon_type=weapon_key,
        name=weapon_data["name"],
        attack_bonus=weapon_data["attack_bonus"]
    )


def _create_random_armor(floor: int, x: int, y: int) -> Item:
    """Crea una armadura aleatoria apropiada para el piso."""
    from .armor import Armor
    
    # Filtrar armaduras por nivel mínimo
    valid_armors = [
        (key, data) for key, data in ARMOR_DATA.items()
        if data["min_level"] <= floor
    ]
    
    if not valid_armors:
        valid_armors = [("leather_armor", ARMOR_DATA["leather_armor"])]
    
    # Seleccionar basado en rareza
    weights = [data["rarity"] for _, data in valid_armors]
    armor_key, armor_data = random.choices(valid_armors, weights=weights)[0]
    
    return Armor(
        x=x,
        y=y,
        armor_type=armor_key,
        name=armor_data["name"],
        defense_bonus=armor_data["defense_bonus"]
    )
