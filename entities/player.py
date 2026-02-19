"""
Clase Player - El jugador controlado por el usuario.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any, List
import random

from .entity import Entity, Fighter
from ..config import (
    PLAYER_BASE_HP, PLAYER_BASE_ATTACK, PLAYER_BASE_DEFENSE,
    PLAYER_HP_PER_LEVEL, PLAYER_ATTACK_PER_LEVEL, PLAYER_DEFENSE_PER_LEVEL,
    XP_BASE, XP_FACTOR, SYMBOLS, INVENTORY_CAPACITY
)

if TYPE_CHECKING:
    from ..world.dungeon import Dungeon
    from ..items.item import Item


class Player(Entity):
    """
    Clase del jugador principal.
    
    Hereda de Entity y añade stats de combate, inventario y progresión.
    
    Attributes:
        fighter: Componente de combate
        inventory: Lista de items
        equipped: Diccionario de items equipados
        gold: Oro acumulado
        current_floor: Piso actual de la mazmorra
        total_xp: Experiencia total ganada
        has_amulet: Si tiene el Amuleto de Ámbar
    """
    
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        dungeon: Optional[Dungeon] = None
    ) -> None:
        """
        Inicializa al jugador.
        
        Args:
            x: Posición X inicial
            y: Posición Y inicial
            dungeon: Referencia a la mazmorra
        """
        super().__init__(
            x=x,
            y=y,
            char=SYMBOLS["player"],
            name="Héroe",
            color="player",
            blocks=True,
            dungeon=dungeon
        )
        
        # Componente de combate
        self.fighter = Fighter(
            max_hp=PLAYER_BASE_HP,
            attack=PLAYER_BASE_ATTACK,
            defense=PLAYER_BASE_DEFENSE,
            xp=0,
            level=1
        )
        
        # Inventario y equipamiento
        self.inventory: List[Item] = []
        self.equipped: Dict[str, Optional[Item]] = {
            "weapon": None,
            "armor": None,
            "ring_left": None,
            "ring_right": None,
        }
        
        # Progresión
        self.gold: int = 0
        self.current_floor: int = 1
        self.total_xp: int = 0
        self.has_amulet: bool = False
    
    @property
    def attack(self) -> int:
        """Calcula el ataque total incluyendo equipo (con durabilidad)."""
        total = self.fighter.attack
        if self.equipped["weapon"]:
            # Usar ataque efectivo según durabilidad
            total += self.equipped["weapon"].get_effective_attack()
        return total
    
    @property
    def base_attack(self) -> int:
        """Retorna el ataque base del jugador (sin equipo)."""
        return self.fighter.attack
    
    @property
    def defense(self) -> int:
        """Calcula la defensa total incluyendo equipo (con durabilidad)."""
        total = self.fighter.defense
        if self.equipped["armor"]:
            # Usar defensa efectiva según durabilidad
            total += self.equipped["armor"].get_effective_defense()
        return total
    
    @property
    def base_defense(self) -> int:
        """Retorna la defensa base del jugador (sin equipo)."""
        return self.fighter.defense
    
    @property
    def xp_to_next_level(self) -> int:
        """Calcula la XP necesaria para el siguiente nivel."""
        return int(XP_BASE * (XP_FACTOR ** (self.fighter.level - 1)))
    
    @property
    def current_level_xp(self) -> int:
        """Retorna la XP acumulada hacia el siguiente nivel."""
        return self.total_xp - self._xp_for_level(self.fighter.level)
    
    def _xp_for_level(self, level: int) -> int:
        """Calcula la XP total necesaria para alcanzar un nivel."""
        if level <= 1:
            return 0
        total = 0
        for lvl in range(1, level):
            total += int(XP_BASE * (XP_FACTOR ** (lvl - 1)))
        return total
    
    def gain_xp(self, amount: int) -> List[str]:
        """
        Gana experiencia y sube de nivel si corresponde.
        
        Args:
            amount: Cantidad de XP ganada
            
        Returns:
            Lista de mensajes generados
        """
        messages = []
        self.total_xp += amount
        messages.append(f"Ganas {amount} puntos de experiencia.")
        
        # Verificar level up
        while self.current_level_xp >= self.xp_to_next_level:
            self._level_up()
            messages.append(f"¡Subes al nivel {self.fighter.level}!")
            messages.append(
                f"HP: {self.fighter.max_hp}, ATK: {self.fighter.base_attack}, "
                f"DEF: {self.fighter.base_defense}"
            )
        
        return messages
    
    def _level_up(self) -> None:
        """Sube de nivel al jugador."""
        self.fighter.level += 1
        self.fighter.max_hp += PLAYER_HP_PER_LEVEL
        self.fighter.base_attack += PLAYER_ATTACK_PER_LEVEL
        self.fighter.base_defense += PLAYER_DEFENSE_PER_LEVEL
        # Curar solo la cantidad de HP ganada por nivel (no curación completa)
        self.fighter.heal(PLAYER_HP_PER_LEVEL)
    
    def add_to_inventory(self, item: Item) -> bool:
        """
        Añade un item al inventario.
        
        Args:
            item: Item a añadir
            
        Returns:
            True si se pudo añadir, False si el inventario está lleno
        """
        if len(self.inventory) >= INVENTORY_CAPACITY:
            return False
        self.inventory.append(item)
        return True
    
    def remove_from_inventory(self, item: Item) -> bool:
        """
        Elimina un item del inventario.
        
        Args:
            item: Item a eliminar
            
        Returns:
            True si se eliminó, False si no estaba
        """
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False
    
    def get_persistent_items(self) -> List[Item]:
        """
        Retorna los items persistentes (que sobreviven a la muerte).
        
        Los items con persistent=True no se pierden al morir.
        Útil para items de misión o especiales.
        
        Returns:
            Lista de items persistentes
        """
        return [item for item in self.inventory if getattr(item, 'persistent', False)]
    
    def clear_non_persistent_items(self) -> List[Item]:
        """
        Elimina todos los items no persistentes del inventario y equipo.
        
        Returns:
            Lista de items persistentes que se conservaron
        """
        persistent = self.get_persistent_items()
        self.inventory = persistent.copy()
        # Limpiar equipo (armas y armaduras no son persistentes por defecto)
        for slot in self.equipped:
            item = self.equipped[slot]
            if item and not getattr(item, 'persistent', False):
                self.equipped[slot] = None
        return persistent
    
    def get_inventory_item(self, index: int) -> Optional[Item]:
        """
        Obtiene un item del inventario por índice.
        
        Args:
            index: Índice del item (0-25 para a-z)
            
        Returns:
            El item o None si el índice es inválido
        """
        if 0 <= index < len(self.inventory):
            return self.inventory[index]
        return None
    
    def equip(self, item: Item) -> List[str]:
        """
        Equipa un item.
        
        Args:
            item: Item a equipar
            
        Returns:
            Lista de mensajes generados
        """
        messages = []
        slot = item.slot if hasattr(item, 'slot') else None
        
        if slot and slot in self.equipped:
            # Desequipar item anterior si hay
            if self.equipped[slot]:
                old_item = self.equipped[slot]
                messages.append(f"Te quitas {old_item.name}.")
            
            self.equipped[slot] = item
            messages.append(f"Equipas {item.name}.")
        else:
            messages.append(f"No puedes equipar {item.name}.")
        
        return messages
    
    def unequip(self, slot: str) -> List[str]:
        """
        Desequipa un item de un slot.
        
        Args:
            slot: Slot a desequipar
            
        Returns:
            Lista de mensajes generados
        """
        messages = []
        
        if slot in self.equipped and self.equipped[slot]:
            item = self.equipped[slot]
            self.equipped[slot] = None
            messages.append(f"Te quitas {item.name}.")
        else:
            messages.append("No tienes nada equipado ahí.")
        
        return messages
    
    def attack_entity(self, target: Entity) -> List[str]:
        """
        Ataca a otra entidad.
        
        Args:
            target: Entidad objetivo
            
        Returns:
            Lista de mensajes de combate
        """
        from ..systems.combat import Combat
        return Combat.attack(self, target)
    
    def update(self) -> None:
        """Actualiza el estado del jugador (bonificadores temporales, etc.)."""
        self.fighter.update_bonuses()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el jugador a un diccionario.
        
        Returns:
            Diccionario con los datos del jugador
        """
        return {
            "x": self.x,
            "y": self.y,
            "fighter": {
                "max_hp": self.fighter.max_hp,
                "hp": self.fighter.hp,
                "base_attack": self.fighter.base_attack,
                "base_defense": self.fighter.base_defense,
                "level": self.fighter.level,
            },
            "gold": self.gold,
            "current_floor": self.current_floor,
            "total_xp": self.total_xp,
            "has_amulet": self.has_amulet,
            "inventory": [item.to_dict() for item in self.inventory],
            "equipped": {
                slot: (item.to_dict() if item else None)
                for slot, item in self.equipped.items()
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], dungeon: Optional[Dungeon] = None) -> Player:
        """
        Crea un jugador desde un diccionario.
        
        Args:
            data: Diccionario con los datos
            dungeon: Referencia a la mazmorra
            
        Returns:
            Nueva instancia de Player
        """
        from ..items.item import Item
        
        player = cls(x=data["x"], y=data["y"], dungeon=dungeon)
        
        # Restaurar stats de combate
        fighter_data = data["fighter"]
        player.fighter.max_hp = fighter_data["max_hp"]
        player.fighter.hp = fighter_data["hp"]
        player.fighter.base_attack = fighter_data["base_attack"]
        player.fighter.base_defense = fighter_data["base_defense"]
        player.fighter.level = fighter_data["level"]
        
        # Restaurar progresión
        player.gold = data["gold"]
        player.current_floor = data["current_floor"]
        player.total_xp = data["total_xp"]
        player.has_amulet = data["has_amulet"]
        
        # Restaurar inventario
        for item_data in data["inventory"]:
            item = Item.from_dict(item_data)
            player.inventory.append(item)
        
        # Restaurar equipo
        for slot, item_data in data["equipped"].items():
            if item_data:
                player.equipped[slot] = Item.from_dict(item_data)
        
        return player
