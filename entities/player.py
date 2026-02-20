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
from ..systems.inventory import GridInventory

if TYPE_CHECKING:
    from ..world.dungeon import Dungeon
    from ..items.item import Item


class Player(Entity):
    """
    Clase del jugador principal.
    
    Hereda de Entity y añade stats de combate, inventario y progresión.
    
    Attributes:
        fighter: Componente de combate
        grid_inventory: Inventario basado en grid (GridInventory)
        inventory: Propiedad que retorna la lista de items del grid
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
        
        # Inventario grid y equipamiento
        self.grid_inventory: GridInventory = GridInventory()
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
    def inventory(self) -> List[Item]:
        """
        Lista de items en el inventario (vista del grid, ordenados por posición).
        
        Propiedad de solo lectura para compatibilidad con código legacy.
        Para modificar el inventario usar add_to_inventory / remove_from_inventory.
        """
        return self.grid_inventory.get_all_items()
    
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
        Añade un item al inventario (grid).
        
        Busca la primera posición disponible en el grid.
        
        Args:
            item: Item a añadir
            
        Returns:
            True si se pudo añadir, False si no cabe
        """
        return self.grid_inventory.auto_place(item)
    
    def remove_from_inventory(self, item: Item) -> bool:
        """
        Elimina un item del inventario (grid).
        
        Args:
            item: Item a eliminar
            
        Returns:
            True si se eliminó, False si no estaba
        """
        return self.grid_inventory.remove(item)
    
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
        
        # Vaciar el grid y re-colocar solo los persistentes
        self.grid_inventory.clear()
        for item in persistent:
            self.grid_inventory.auto_place(item)
        
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
            index: Índice del item (0-based en la lista ordenada del grid)
            
        Returns:
            El item o None si el índice es inválido
        """
        return self.grid_inventory.get_item_by_index(index)
    
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
            "grid_inventory": self.grid_inventory.to_dict(),
            "equipped": {
                slot: (item.to_dict() if item else None)
                for slot, item in self.equipped.items()
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], dungeon: Optional[Dungeon] = None) -> Player:
        """
        Crea un jugador desde un diccionario.
        
        Soporta saves nuevos (grid_inventory) y legacy (inventory como lista).
        
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
        
        # Restaurar inventario — nuevo formato (grid) o legacy (lista)
        if "grid_inventory" in data:
            player.grid_inventory = GridInventory.from_dict(data["grid_inventory"])
        elif "inventory" in data:
            # Legacy: convertir lista a grid
            legacy_items = [Item.from_dict(item_data) for item_data in data["inventory"]]
            player.grid_inventory = GridInventory.from_item_list(legacy_items)
        
        # Restaurar equipo
        # En el grid, los items equipados siguen estando en el grid.
        # Solo necesitamos vincular las referencias del equipo a los items del grid.
        for slot, item_data in data["equipped"].items():
            if item_data:
                equipped_item = Item.from_dict(item_data)
                # Buscar si el item ya existe en el grid (por nombre y tipo)
                # Si no, añadirlo al grid
                matched = False
                for grid_item in player.grid_inventory.get_all_items():
                    if (grid_item.name == equipped_item.name and 
                            grid_item.item_type == equipped_item.item_type and
                            grid_item not in [v for v in player.equipped.values() if v]):
                        player.equipped[slot] = grid_item
                        matched = True
                        break
                
                if not matched:
                    # El item equipado no está en el grid — añadirlo
                    if player.grid_inventory.auto_place(equipped_item):
                        player.equipped[slot] = equipped_item
                    else:
                        # No cabe en el grid; equipar sin grid (edge case)
                        player.equipped[slot] = equipped_item
        
        return player
