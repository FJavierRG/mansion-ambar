"""
Diálogos y configuración del NPC Comerciante (Merchant).

DESBLOQUEO: Tras aceptar ayudar al Stranger (yes_response en mision_nieta).
UBICACIÓN: Plantas pares de la mazmorra (2, 4, 6, 8, 10), 50% de probabilidad.

ESTADOS:
  shop → Dungeon (plantas pares), abre la tienda al interactuar.

NOTAS:
  - El FSM está preparado para añadir más estados en el futuro
    (ej: misiones, desbloqueo de items especiales, etc.)
  - La compra se gestiona en GameState.SHOP, no en el diálogo.
  - El diálogo solo ofrece la opción de abrir la tienda.
  - Sus items se pueden modificar desde cualquier parte del código
    usando get_merchant_shop().add_item() / remove_item() / etc.
"""
import random
from roguelike.systems.text import DialogTree, DialogNode, DialogOption, InteractiveText

# Flag DEV: fuerza aparición 100% en pares (solo memoria, NO se guarda)
_dev_force_spawn: bool = False


# ============================================================================
# ESTADO: "shop" (Dungeon - Plantas pares, 50% probabilidad)
# ============================================================================

def _open_shop_action(player, zone):
    """
    Acción del diálogo que señala al juego que debe abrir la tienda.
    
    Establece un flag temporal en el jugador que game.py detecta
    en _on_dialog_closed para transicionar a GameState.SHOP.
    """
    player._pending_shop = True


def create_merchant_shop_dialog() -> DialogTree:
    """
    Crea el diálogo del Comerciante.
    
    Ofrece la opción de abrir la tienda o despedirse.
    
    Returns:
        DialogTree con el diálogo
    """
    tree = DialogTree(start_node="welcome")
    
    welcome_node = DialogNode(
        node_id="welcome",
        speaker="Comerciante",
        text="¡Bienvenido, viajero! Tengo mercancía que podría interesarte.",
        options=[
            DialogOption(
                "Ver mercancía",
                next_node=None,
                action=_open_shop_action
            ),
            DialogOption("No, gracias", next_node=None),
        ]
    )
    tree.add_node(welcome_node)
    
    return tree


def create_merchant_shop_completed() -> InteractiveText:
    """
    Diálogo corto cuando el estado 'shop' está completado.
    
    En la práctica, este estado nunca se completa (completion_condition=None),
    así que siempre se usa el diálogo completo. Se mantiene por convención FSM.
    """
    return InteractiveText.create_simple_text(
        "¿Necesitas algo?",
        title="Comerciante",
        auto_close=False
    )


# ============================================================================
# CONDICIÓN DE SPAWN
# ============================================================================

def _merchant_spawn_condition(floor, event_manager) -> bool:
    """
    Determina si el comerciante debe aparecer en esta planta.
    
    Condiciones (TODAS deben cumplirse):
      1. El jugador aceptó ayudar al Stranger (yes_response en mision_nieta)
         — o _dev_force_spawn está activo (ignora requisito de evento)
      2. La planta es par (2, 4, 6, 8, 10)
      3. 50% de probabilidad — o 100% si _dev_force_spawn
    
    Args:
        floor: Número de planta actual
        event_manager: Gestor de eventos para verificar condiciones
        
    Returns:
        True si el comerciante debe spawnear
    """
    global _dev_force_spawn
    
    # DEV: forzar aparición (salta requisito de evento y probabilidad)
    if _dev_force_spawn:
        # Solo mantener requisito de planta par
        if floor is None or floor % 2 != 0:
            return False
        return True
    
    # 1. Solo si el jugador aceptó ayudar al Stranger
    if not event_manager.is_event_triggered("stranger_help_accepted"):
        return False
    
    # 2. Solo en plantas pares
    if floor is None or floor % 2 != 0:
        return False
    
    # 3. 50% de probabilidad
    return random.random() < 0.5


# ============================================================================
# REGISTRO DE ESTADOS DEL NPC
# ============================================================================

def register_npc_states(manager) -> None:
    """
    Registra todos los estados del Comerciante en el sistema FSM.
    
    Esta función es llamada automáticamente por el sistema de auto-discovery.
    
    ESTADO ACTUAL:
      - shop: Dungeon, plantas pares, 50% probabilidad.
              Requiere haber aceptado ayudar al Stranger.
    
    PREPARADO PARA FUTURO:
      - Se pueden añadir más estados con transiciones
        (ej: "quest_active", "special_stock", etc.)
    
    Args:
        manager: Instancia de NPCStateManager
    """
    from roguelike.systems.npc_states import NPCStateConfig
    
    # Estado "shop" - Dungeon, plantas pares, 50% probabilidad
    manager.register_npc_state("Comerciante", NPCStateConfig(
        state_id="shop",
        zone_type="dungeon",
        floor=None,  # Cualquier planta (filtrado por spawn_condition)
        position=None,  # Posición aleatoria en la mazmorra
        char="$",
        color="gold",
        dialog_tree_func=create_merchant_shop_dialog,
        completed_dialog_func=create_merchant_shop_completed,
        # Sin completion_condition: el estado nunca se "completa",
        # siempre muestra el diálogo completo con opción de abrir tienda.
        completion_condition=None,
        # Spawn condition: plantas pares + 50% + stranger_help_accepted
        spawn_condition=_merchant_spawn_condition,
    ))
