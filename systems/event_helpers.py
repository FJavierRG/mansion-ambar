"""
Helpers y factories para crear condiciones y acciones de eventos comunes.
Facilita la creación de eventos sin tener que escribir funciones desde cero.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Optional
from .events import EventCondition, EventAction

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..world.zone import Zone
    from ..entities.entity import Entity
    from ..items.item import Item


# ============================================================================
# FACTORIES DE CONDICIONES COMUNES
# ============================================================================

def condition_player_level(min_level: int) -> EventCondition:
    """
    Crea una condición que verifica el nivel del jugador.
    
    Args:
        min_level: Nivel mínimo requerido
        
    Returns:
        EventCondition configurada
    """
    def check(player: Player, _zone: Zone) -> bool:
        return player.fighter.level >= min_level
    
    return EventCondition(check, f"Jugador nivel {min_level}+")


def condition_player_floor(floor: int) -> EventCondition:
    """
    Crea una condición que verifica el piso actual.
    
    Args:
        floor: Piso requerido
        
    Returns:
        EventCondition configurada
    """
    def check(player: Player, _zone: Zone) -> bool:
        return player.current_floor == floor
    
    return EventCondition(check, f"En piso {floor}")


def condition_player_has_item(item_name: str) -> EventCondition:
    """
    Crea una condición que verifica si el jugador tiene un item.
    
    Args:
        item_name: Nombre del item requerido
        
    Returns:
        EventCondition configurada
    """
    def check(player: Player, _zone: Zone) -> bool:
        return any(item.name == item_name for item in player.inventory)
    
    return EventCondition(check, f"Tiene {item_name}")


def condition_player_has_gold(min_gold: int) -> EventCondition:
    """
    Crea una condición que verifica el oro del jugador.
    
    Args:
        min_gold: Oro mínimo requerido
        
    Returns:
        EventCondition configurada
    """
    def check(player: Player, _zone: Zone) -> bool:
        return player.gold >= min_gold
    
    return EventCondition(check, f"Tiene {min_gold}+ de oro")


def condition_entity_exists(entity_name: str, zone_type: Optional[str] = None) -> EventCondition:
    """
    Crea una condición que verifica si existe una entidad en la zona.
    
    Args:
        entity_name: Nombre de la entidad
        zone_type: Tipo de zona (None = cualquier zona)
        
    Returns:
        EventCondition configurada
    """
    def check(_player: Player, zone: Zone) -> bool:
        if zone_type and zone.zone_type != zone_type:
            return False
        return any(entity.name == entity_name for entity in zone.entities)
    
    return EventCondition(check, f"Existe {entity_name}")


def condition_event_triggered(event_id: str) -> EventCondition:
    """
    Crea una condición que verifica si otro evento fue activado.
    
    Args:
        event_id: ID del evento requerido
        
    Returns:
        EventCondition configurada
    """
    from .events import event_manager
    
    def check(_player: Player, _zone: Zone) -> bool:
        return event_manager.is_event_triggered(event_id)
    
    return EventCondition(check, f"Evento {event_id} activado")


def condition_always() -> EventCondition:
    """Crea una condición que siempre es verdadera."""
    def check(_player: Player, _zone: Zone) -> bool:
        return True
    
    return EventCondition(check, "Siempre")


# ============================================================================
# FACTORIES DE ACCIONES COMUNES
# ============================================================================

def action_add_entity_to_zone(
    entity_factory: Callable[[int, int, Zone], Entity],
    zone_type: str,
    x: Optional[int] = None,
    y: Optional[int] = None
) -> EventAction:
    """
    Crea una acción que añade una entidad a una zona específica.
    
    Args:
        entity_factory: Función que crea la entidad (x, y, zone) -> Entity
        zone_type: Tipo de zona donde añadir
        x: Posición X (None = aleatoria)
        y: Posición Y (None = aleatoria)
        
    Returns:
        EventAction configurada
    """
    def action(_player: Player, zone: Zone) -> None:
        # Buscar la zona objetivo
        target_zone = None
        if zone.zone_type == zone_type:
            target_zone = zone
        else:
            # Si no estamos en la zona objetivo, necesitaríamos acceso al Game
            # Por ahora, solo funciona si estamos en la zona correcta
            return
        
        if target_zone:
            # Determinar posición
            if x is not None and y is not None:
                pos_x, pos_y = x, y
            else:
                # Posición aleatoria en el suelo
                import random
                walkable_positions = []
                for tx in range(target_zone.width):
                    for ty in range(target_zone.height):
                        if target_zone.is_walkable(tx, ty):
                            walkable_positions.append((tx, ty))
                
                if walkable_positions:
                    pos_x, pos_y = random.choice(walkable_positions)
                else:
                    return
            
            # Crear y añadir entidad
            entity = entity_factory(pos_x, pos_y, target_zone)
            target_zone.entities.append(entity)
    
    return EventAction(action, f"Añadir entidad a {zone_type}")


def action_remove_entity_from_zone(entity_name: str, zone_type: Optional[str] = None) -> EventAction:
    """
    Crea una acción que elimina una entidad de una zona.
    
    Args:
        entity_name: Nombre de la entidad a eliminar
        zone_type: Tipo de zona (None = zona actual)
        
    Returns:
        EventAction configurada
    """
    def action(_player: Player, zone: Zone) -> None:
        if zone_type and zone.zone_type != zone_type:
            return
        
        # Buscar y eliminar entidad
        for i, entity in enumerate(zone.entities):
            if entity.name == entity_name:
                zone.entities.pop(i)
                break
    
    return EventAction(action, f"Eliminar {entity_name}")


def action_add_item_to_zone(
    item_factory: Callable[[int, int], 'Item'],  # type: ignore
    zone_type: str,
    x: Optional[int] = None,
    y: Optional[int] = None
) -> EventAction:
    """
    Crea una acción que añade un item a una zona.
    
    Args:
        item_factory: Función que crea el item (x, y) -> Item
        zone_type: Tipo de zona donde añadir
        x: Posición X (None = aleatoria)
        y: Posición Y (None = aleatoria)
        
    Returns:
        EventAction configurada
    """
    def action(_player: Player, zone: Zone) -> None:
        if zone.zone_type != zone_type:
            return
        
        if x is not None and y is not None:
            pos_x, pos_y = x, y
        else:
            import random
            walkable_positions = []
            for tx in range(zone.width):
                for ty in range(zone.height):
                    if zone.is_walkable(tx, ty):
                        walkable_positions.append((tx, ty))
            
            if walkable_positions:
                pos_x, pos_y = random.choice(walkable_positions)
            else:
                return
        
        item = item_factory(pos_x, pos_y)
        zone.items.append(item)
    
    return EventAction(action, f"Añadir item a {zone_type}")


def action_give_item_to_player(item_factory: Callable[[], 'Item']) -> EventAction:  # type: ignore
    """
    Crea una acción que da un item al jugador.
    
    Args:
        item_factory: Función que crea el item () -> Item
        
    Returns:
        EventAction configurada
    """
    def action(player: Player, _zone: Zone) -> None:
        item = item_factory()
        if len(player.inventory) < 26:  # Capacidad del inventario
            player.inventory.append(item)
    
    return EventAction(action, "Dar item al jugador")


def action_modify_player_gold(amount: int) -> EventAction:
    """
    Crea una acción que modifica el oro del jugador.
    
    Args:
        amount: Cantidad a añadir (puede ser negativo)
        
    Returns:
        EventAction configurada
    """
    def action(player: Player, _zone: Zone) -> None:
        player.gold = max(0, player.gold + amount)
    
    return EventAction(action, f"Modificar oro: {amount:+d}")


def action_show_message(message: str) -> EventAction:
    """
    Crea una acción que muestra un mensaje al jugador.
    
    Args:
        message: Mensaje a mostrar
        
    Returns:
        EventAction configurada
    """
    def action(_player: Player, _zone: Zone) -> None:
        # Necesitaríamos acceso al message_log, pero por ahora solo imprimimos
        print(f"[Evento] {message}")
    
    return EventAction(action, f"Mostrar mensaje: {message[:30]}...")


def action_custom(custom_func: Callable[[Player, Zone], None], description: str = "") -> EventAction:  # type: ignore
    """
    Crea una acción personalizada.
    
    Args:
        custom_func: Función personalizada (player, zone) -> None
        description: Descripción de la acción
        
    Returns:
        EventAction configurada
    """
    return EventAction(custom_func, description or "Acción personalizada")
