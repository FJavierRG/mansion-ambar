"""
Diálogos y configuración del NPC Comerciante Errante (Merchant Wanderer).

DESBLOQUEO: El jugador recoge su primera moneda de oro del suelo.
UBICACIÓN: Lobby, a la izquierda de las escaleras (misma Y).

FUNCIÓN:
  El Comerciante Errante es el intermediario entre el jugador y el
  Comerciante de la mazmorra (merchant.py). Acepta donaciones de oro
  para dos fines:
    1. RESTOCK (por run): Reabastecer los suministros del mercader.
       Sin pagar, la tienda en dungeon está vacía.
    2. MEJORA (permanente): Donar oro libremente para desbloquear
       nuevos items en la pool de la tienda. El jugador no conoce
       los umbrales; simplemente dona lo que quiera.

ESTADOS:
  greeting → Lobby, tras recoger la primera moneda de oro.

NOTAS:
  - Este NPC es INDEPENDIENTE del Comerciante de la mazmorra (merchant.py).
  - Las donaciones y el restock se almacenan en event_data (persistentes).
  - La tienda del mercader en dungeon lee estos datos dinámicamente
    (ver shop.py: _get_unlocked_merchant_items, _create_merchant_shop_from_state).
"""
from roguelike.systems.text import DialogTree, DialogNode, DialogOption, InteractiveText


# ============================================================================
# COSTES
# ============================================================================

# Coste fijo para reabastecer la tienda del mercader (por run)
RESTOCK_COST: int = 5


# ============================================================================
# CONDICIONES DE DIÁLOGO
# ============================================================================

def _can_donate(player) -> bool:
    """
    Condición: tiene al menos 1 oro para donar.
    """
    return player.gold >= 1


# ============================================================================
# ACCIONES DE DIÁLOGO
# ============================================================================

def _restock_action(player, zone):
    """
    Acción: cobra el coste de restock y marca la tienda para reabastecer.
    """
    from roguelike.systems.events import event_manager
    from roguelike.systems.shop import refresh_merchant_shop

    player.gold -= RESTOCK_COST
    event_manager.set_data("merchant_restock_paid", True)
    refresh_merchant_shop()


def _open_donation_action(player, zone):
    """
    Acción: señala al juego que debe abrir el selector de donación.
    
    Similar al patrón de _pending_shop del comerciante de dungeon.
    game.py detecta este flag en _on_dialog_closed y abre GameState.DONATION.
    """
    player._pending_donation = True


# ============================================================================
# DIÁLOGOS
# ============================================================================

def create_wanderer_greeting_dialog() -> DialogTree:
    """
    Crea el diálogo del Comerciante Errante con opciones de donación.
    
    Se recrea cada vez que se interactúa con el NPC, así que los textos
    reflejan el estado actual de restock/donaciones.
    
    Opciones:
      - Reabastecer suministros (coste fijo, por run)
      - Donar oro para mejorar mercancía (abre selector numérico)
      - Despedirse
    """
    from roguelike.systems.events import event_manager
    
    tree = DialogTree(start_node="welcome")
    already_restocked = event_manager.get_data("merchant_restock_paid", False)

    options = []
    
    # Opción de restock: siempre visible si no se ha pagado esta run.
    # Si no tiene oro suficiente, la acción redirige al nodo de rechazo.
    if not already_restocked:
        restock_option = DialogOption(
            f"Ofrecer algo de ayuda: ({RESTOCK_COST} oro)",
            next_node="thanks_restock",
            action=None,  # Se asigna abajo via closure
        )

        def _try_restock(player, zone, _opt=restock_option):
            """Intenta el restock: si hay oro suficiente cobra y reabastece,
            si no redirige al nodo de 'no tienes suficiente'."""
            if player.gold >= RESTOCK_COST:
                _restock_action(player, zone)
                _opt.next_node = "thanks_restock"
            else:
                _opt.next_node = "not_enough_gold"

        restock_option.action = _try_restock
        options.append(restock_option)
    
    options.append(DialogOption(
        "Aportar dinero para mejorar el negocio del mercader",
        next_node=None,
        condition=_can_donate,
        action=_open_donation_action,
    ))
    options.append(DialogOption("No, gracias", next_node=None))

    welcome_node = DialogNode(
        node_id="welcome",
        speaker="Comerciante Errante",
        text="¿Quién anda ahí? ¿Que son esos pasos?"
             "---Oh, un viajero. Yo he subido aquí a descansar un poco.\n"
             "¿Por casualidad no querrías echarme una mano aportando algo "
             "de dinero a mi tienda?",
        options=options,
    )
    tree.add_node(welcome_node)

    # Confirmación de restock
    thanks_restock_node = DialogNode(
        node_id="thanks_restock",
        speaker="Comerciante Errante",
        text="Gracias por tu ayuda. Esto servirá.",
        options=[DialogOption("Continuar", next_node=None)],
    )
    tree.add_node(thanks_restock_node)

    # Rechazo por falta de oro
    not_enough_node = DialogNode(
        node_id="not_enough_gold",
        speaker="Comerciante Errante",
        text="Parece que no tienes suficiente.",
        options=[DialogOption("Continuar", next_node=None)],
    )
    tree.add_node(not_enough_node)

    return tree


def create_wanderer_greeting_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'greeting' está completado."""
    return InteractiveText.create_simple_text(
        "¿Otra vez por aquí? Ya sabes, si necesitas algo... siempre estoy rondando.",
        title="Comerciante Errante",
        auto_close=False
    )


# ============================================================================
# CONDICIÓN DE SPAWN
# ============================================================================

def _wanderer_spawn_condition(floor, event_manager) -> bool:
    """
    Determina si el Comerciante Errante debe aparecer en el lobby.
    
    Condición: El jugador recogió su primera moneda de oro del suelo.
    """
    return event_manager.is_event_triggered("first_gold_pickup")


# ============================================================================
# REGISTRO DE ESTADOS DEL NPC
# ============================================================================

def register_npc_states(manager) -> None:
    """
    Registra todos los estados del Comerciante Errante en el sistema FSM.
    
    Esta función es llamada automáticamente por el sistema de auto-discovery.
    """
    from roguelike.systems.npc_states import NPCStateConfig

    manager.register_npc_state("Comerciante Errante", NPCStateConfig(
        state_id="greeting",
        zone_type="lobby",
        position=(36, 12),
        char="$",
        color="gold",
        dialog_tree_func=create_wanderer_greeting_dialog,
        completed_dialog_func=create_wanderer_greeting_completed,
        completion_condition=None,
        spawn_condition=_wanderer_spawn_condition,
    ))
