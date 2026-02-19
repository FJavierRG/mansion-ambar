"""
Sistema de inventario del juego.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..items.item import Item
    from ..world.dungeon import Dungeon


class Inventory:
    """
    Sistema de gestión de inventario.
    
    Maneja las operaciones de recoger, soltar, usar y equipar items.
    """
    
    @staticmethod
    def pickup_item(player: Player, dungeon: Dungeon) -> List[str]:
        """
        Intenta recoger un item del suelo.
        
        Args:
            player: El jugador
            dungeon: La mazmorra actual
            
        Returns:
            Lista de mensajes
        """
        messages = []
        
        items = dungeon.get_items_at(player.x, player.y)
        
        if not items:
            messages.append("No hay nada aquí para recoger.")
            return messages
        
        # Recoger el primer item
        item = items[0]
        
        # Verificar si es oro
        if item.item_type == "gold":
            player.gold += item.value
            dungeon.remove_item(item)
            messages.append("Recoges una moneda de oro.")
            
            # Disparar evento de primera moneda recogida (desbloquea NPCs)
            from ..systems.events import event_manager
            if not event_manager.is_event_triggered("first_gold_pickup"):
                event_manager.trigger_event(
                    "first_gold_pickup", player, dungeon, skip_conditions=True
                )
            
            return messages
        
        # Verificar si es el amuleto
        if item.item_type == "amulet":
            player.has_amulet = True
            dungeon.remove_item(item)
            messages.append("¡Has encontrado el Amuleto de Ámbar!")
            messages.append("¡Ahora debes escapar ascendiendo a la superficie!")
            return messages
        
        # Intentar añadir al inventario
        if player.add_to_inventory(item):
            dungeon.remove_item(item)
            messages.append(f"Recoges {item.name}.")
        else:
            messages.append("Tu inventario está lleno.")
        
        return messages
    
    @staticmethod
    def drop_item(player: Player, dungeon: Dungeon, index: int) -> List[str]:
        """
        Suelta un item del inventario.
        
        Args:
            player: El jugador
            dungeon: La mazmorra actual
            index: Índice del item en el inventario
            
        Returns:
            Lista de mensajes
        """
        messages = []
        
        item = player.get_inventory_item(index)
        
        if not item:
            messages.append("No tienes ese item.")
            return messages
        
        # Verificar si está equipado
        for slot, equipped in player.equipped.items():
            if equipped == item:
                messages.append(f"Primero debes desequipar {item.name}.")
                return messages
        
        # Soltar el item
        player.remove_from_inventory(item)
        dungeon.add_item(item, player.x, player.y)
        messages.append(f"Sueltas {item.name}.")
        
        return messages
    
    @staticmethod
    def use_item(player: Player, index: int) -> List[str]:
        """
        Usa un item del inventario.
        
        Args:
            player: El jugador
            index: Índice del item
            
        Returns:
            Lista de mensajes
        """
        messages = []
        
        item = player.get_inventory_item(index)
        
        if not item:
            messages.append("No tienes ese item.")
            return messages
        
        # Verificar si el item es usable
        if not hasattr(item, 'use') or not item.usable:
            messages.append(f"No puedes usar {item.name}.")
            return messages
        
        # Usar el item
        use_messages, consumed = item.use(player)
        messages.extend(use_messages)
        
        # Eliminar si se consumió
        if consumed:
            player.remove_from_inventory(item)
        
        return messages
    
    @staticmethod
    def equip_item(player: Player, index: int) -> List[str]:
        """
        Equipa un item del inventario.
        
        Args:
            player: El jugador
            index: Índice del item
            
        Returns:
            Lista de mensajes
        """
        messages = []
        
        item = player.get_inventory_item(index)
        
        if not item:
            messages.append("No tienes ese item.")
            return messages
        
        # Verificar si el item es equipable
        if not hasattr(item, 'slot') or not item.slot:
            messages.append(f"No puedes equipar {item.name}.")
            return messages
        
        # Equipar
        messages.extend(player.equip(item))
        
        return messages
    
    @staticmethod
    def unequip_item(player: Player, slot: str) -> List[str]:
        """
        Desequipa un item de un slot.
        
        Args:
            player: El jugador
            slot: Slot a desequipar
            
        Returns:
            Lista de mensajes
        """
        return player.unequip(slot)
    
    @staticmethod
    def get_inventory_display(player: Player) -> List[Tuple[str, str, bool]]:
        """
        Obtiene la información del inventario para mostrar.
        
        Args:
            player: El jugador
            
        Returns:
            Lista de tuplas (letra, descripción, equipado)
        """
        display = []
        
        for i, item in enumerate(player.inventory):
            letter = chr(ord('a') + i)
            
            # Verificar si está equipado
            is_equipped = any(
                equipped == item
                for equipped in player.equipped.values()
                if equipped is not None
            )
            
            name = item.name
            if is_equipped:
                name += " (equipado)"
            
            display.append((letter, name, is_equipped))
        
        return display
    
    @staticmethod
    def get_equipment_display(player: Player) -> List[Tuple[str, str]]:
        """
        Obtiene la información del equipo para mostrar.
        
        Args:
            player: El jugador
            
        Returns:
            Lista de tuplas (slot, nombre del item)
        """
        slot_names = {
            "weapon": "Arma",
            "armor": "Armadura",
            "ring_left": "Anillo Izq.",
            "ring_right": "Anillo Der.",
        }
        
        display = []
        
        for slot, item in player.equipped.items():
            slot_name = slot_names.get(slot, slot)
            item_name = item.name if item else "---"
            display.append((slot_name, item_name))
        
        return display
