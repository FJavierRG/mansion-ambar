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
        color: Color del item (clave en COLORS, para fallback ASCII)
        item_type: Tipo de item (potion, weapon, armor, etc.)
        identified: Si el item ha sido identificado
        usable: Si el item puede usarse
        slot: Slot de equipamiento (si aplica)
        persistent: Si el item persiste al morir (items especiales de misión)
        sprite: Clave de sprite específico (si aplica, ej: "dagger", "sword")
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
        self.sprite: Optional[str] = None  # Clave de sprite específico
        
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
        if self.sprite:
            data["sprite"] = self.sprite
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
            item.sprite = data.get("sprite")
            return item
    
    def __repr__(self) -> str:
        return f"Item({self.name} at ({self.x}, {self.y}))"


# ============================================================================
# REGISTRO / FACTORÍA DE ITEMS POR ID
# ============================================================================

def get_all_item_ids() -> List[str]:
    """
    Retorna todos los IDs de items registrados en el juego.
    
    Útil para autocompletado, validaciones y listados.
    
    Returns:
        Lista de todos los item_id válidos
    """
    ids: List[str] = []
    ids.extend(POTION_DATA.keys())
    ids.extend(WEAPON_DATA.keys())
    ids.extend(ARMOR_DATA.keys())
    ids.append("gold")
    ids.append("amulet")
    ids.append("heart_key")
    return ids


def create_item(item_id: str, x: int = 0, y: int = 0, **kwargs) -> Optional[Item]:
    """
    Crea cualquier item del juego dado su ID.
    
    Esta es la factoría central. Todos los items deben crearse a través
    de esta función para garantizar una única fuente de verdad (config.py).
    
    IDs válidos:
        Pociones : ver POTION_DATA en config.py
        Armas    : ver WEAPON_DATA en config.py
        Armaduras: ver ARMOR_DATA en config.py
        Especiales: "gold", "amulet", "heart_key"
    
    Args:
        item_id: Identificador único del item (clave en POTION_DATA, WEAPON_DATA, etc.)
        x: Posición X
        y: Posición Y
        **kwargs: Parámetros extra según tipo:
            - gold: siempre vale 1
    
    Returns:
        Instancia del item, o None si el item_id no existe
    """
    from .potion import Potion
    from .weapon import Weapon
    from .armor import Armor
    from .special import Gold, Amulet
    
    # --- Pociones ---
    if item_id in POTION_DATA:
        data = POTION_DATA[item_id]
        return Potion(
            x=x, y=y,
            potion_type=item_id,
            name=data["name"],
            effect=data["effect"],
            value=data["value"],
            duration=data.get("duration", 0)
        )
    
    # --- Armas ---
    if item_id in WEAPON_DATA:
        data = WEAPON_DATA[item_id]
        return Weapon(
            x=x, y=y,
            weapon_type=item_id,
            name=data["name"],
            attack_bonus=data["attack_bonus"],
            durability=data["durability"],
            sprite_key=data.get("sprite")
        )
    
    # --- Armaduras ---
    if item_id in ARMOR_DATA:
        data = ARMOR_DATA[item_id]
        return Armor(
            x=x, y=y,
            armor_type=item_id,
            name=data["name"],
            defense_bonus=data["defense_bonus"],
            durability=data["durability"]
        )
    
    # --- Oro ---
    if item_id == "gold":
        return Gold(x, y, 1)
    
    # --- Amuleto de Ámbar ---
    if item_id == "amulet":
        return Amulet(x, y)
    
    # --- Llave con forma de corazón (item clave de misión) ---
    if item_id == "heart_key":
        return Item(
            x=x, y=y,
            char=SYMBOLS["key"],
            name="Llave con forma de corazón",
            color="amulet",
            item_type="key_item",
            identified=True,
            usable=False,
            persistent=True,
        )
    
    # ID no reconocido
    return None


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
        total_weight += 0.20
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
            return create_item("gold", x, y)
    
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
    return create_item("gold", x, y)


def _create_random_potion(x: int, y: int) -> Item:
    """Crea una poción aleatoria basada en rareza."""
    # Seleccionar tipo basado en rareza
    potions = list(POTION_DATA.items())
    weights = [data["rarity"] for _, data in potions]
    potion_key, _ = random.choices(potions, weights=weights)[0]
    
    return create_item(potion_key, x, y)


def _create_random_weapon(floor: int, x: int, y: int) -> Item:
    """Crea un arma aleatoria apropiada para el piso."""
    # Filtrar armas por nivel mínimo
    valid_weapons = [
        (key, data) for key, data in WEAPON_DATA.items()
        if data["min_level"] <= floor
    ]
    
    if not valid_weapons:
        # Fallback: primera arma del diccionario
        first_key = next(iter(WEAPON_DATA))
        valid_weapons = [(first_key, WEAPON_DATA[first_key])]
    
    # Seleccionar basado en rareza
    weights = [data["rarity"] for _, data in valid_weapons]
    weapon_key, _ = random.choices(valid_weapons, weights=weights)[0]
    
    return create_item(weapon_key, x, y)


def _create_random_armor(floor: int, x: int, y: int) -> Item:
    """Crea una armadura aleatoria apropiada para el piso."""
    # Filtrar armaduras por nivel mínimo
    valid_armors = [
        (key, data) for key, data in ARMOR_DATA.items()
        if data["min_level"] <= floor
    ]
    
    if not valid_armors:
        # Fallback: primera armadura del diccionario
        first_key = next(iter(ARMOR_DATA))
        valid_armors = [(first_key, ARMOR_DATA[first_key])]
    
    # Seleccionar basado en rareza
    weights = [data["rarity"] for _, data in valid_armors]
    armor_key, _ = random.choices(valid_armors, weights=weights)[0]
    
    return create_item(armor_key, x, y)
