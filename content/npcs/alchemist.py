"""
Diálogos del NPC Alquimista.

DESBLOQUEO: Morir bebiendo una poción de veneno en una run.
ESTADO INICIAL: greeting (Lobby)

ESTADOS:
  greeting → Lobby, tras primera muerte por veneno
  cadaver  → Lobby, tras segunda muerte por veneno
"""
from roguelike.systems.text import DialogTree, DialogNode, DialogOption, InteractiveText


# ============================================================================
# ESTADO: "greeting" (Lobby - Primera vez tras desbloqueo)
# ============================================================================

def create_alchemist_greeting_dialog() -> DialogTree:
    """
    Crea el diálogo del Alquimista cuando aparece por primera vez en el lobby.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="greeting")
    
    def on_greeting_complete(player, zone):
        """Marca el greeting como completado."""
        from roguelike.systems.events import event_manager
        if not event_manager.is_event_triggered("alchemist_greeting_done"):
            event_manager.trigger_event("alchemist_greeting_done", player, zone, skip_conditions=True)
    
    greeting_node = DialogNode(
        node_id="greeting",
        speaker="Alquimista",
        text="¿Hay alguien ahí?---¿Así que eres tú? Me habían comentado algún demente andaba por ahí bebiéndose mis pociones de veneno.\nJajajajaja!---Yo soy el alquimista.",
        options=[
            DialogOption("Continuar", next_node="greeting2")
        ]
    )
    tree.add_node(greeting_node)
    
    greeting2_node = DialogNode(
        node_id="greeting2",
        speaker="Alquimista",
        text="¿Cómo que por qué voy dejando venenos por las mazmorras?\n¿Acaso no es evidente?---¡Intento dar caza a algo! Y no pretenderás que un viejo ciego baje armado a por ello.\nHabrás visto que esos pasillos están llenos de criaturas.---Estoy intentando conseguir el cadáver de uno de ellos en concreto.---No te interesa por qué necesito un cadáver, no es asunto tuyo.",
        options=[
            DialogOption("Continuar", next_node=None, action=on_greeting_complete)
        ]
    )
    tree.add_node(greeting2_node)
    
    return tree


def create_alchemist_greeting_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'greeting' está completado."""
    return InteractiveText.create_simple_text(
        "Intenta no seguir bebiéndote mis venenos ¿De acuerdo? Están ahí por algo.",
        title="Alquimista",
        auto_close=False
    )


# ============================================================================
# ESTADO: "cadaver" (Lobby - Tras segunda muerte por veneno)
# ============================================================================

def create_alchemist_cadaver_dialog() -> DialogTree:
    """
    Crea el diálogo del Alquimista tras la segunda muerte por veneno.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="cadaver")
    
    cadaver_node = DialogNode(
        node_id="cadaver",
        speaker="Alquimista",
        text="...¿Otra vez tú?---¿No te quedó claro que NO debías beberte MIS venenos?\n¿Tienes algún tipo de fetiche?---¿Te gusta morir envenenado? ¿Es eso?---Mira, necesito conseguir el cadáver de una criatura especial, y no estoy en condiciones de pelearme con esos bichos allí abajo. Soy ciego, por si no te has percatado.--- Te lo voy a repetir una vez más: NO TE BEBAS MIS VENENOS.",
        options=[
            DialogOption("Continuar", next_node=None)
        ]
    )
    tree.add_node(cadaver_node)
    
    return tree


def create_alchemist_cadaver_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'cadaver' está completado."""
    return InteractiveText.create_simple_text(
        "Te lo voy a repetir una vez más: NO TE BEBAS MIS VENENOS.",
        title="Alquimista",
        auto_close=False
    )


# ============================================================================
# REGISTRO DE ESTADOS DEL NPC
# ============================================================================

def register_npc_states(manager) -> None:
    """
    Registra todos los estados del Alquimista en el sistema FSM.
    
    Esta función es llamada automáticamente por el sistema de auto-discovery.
    
    CONDICIÓN DE DESBLOQUEO:
    El jugador debe morir bebiendo una poción de veneno en una run.
    Esto activa el evento "alchemist_unlocked" que persiste entre partidas.
    
    PROGRESIÓN:
    greeting → cadaver (tras segunda muerte por veneno: evento "alchemist_second_poison")
    
    Args:
        manager: Instancia de NPCStateManager
    """
    from roguelike.systems.npc_states import NPCStateConfig, StateTransition
    from roguelike.systems.events import event_manager
    
    # Estado "greeting" - Lobby, primera vez después de desbloquear
    manager.register_npc_state("Alquimista", NPCStateConfig(
        state_id="greeting",
        zone_type="lobby",
        position=(50, 22),
        char="9",
        color="potion",
        dialog_tree_func=create_alchemist_greeting_dialog,
        completed_dialog_func=create_alchemist_greeting_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("alchemist_greeting_done"),
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("alchemist_unlocked"),
        transitions=[
            StateTransition(
                target_state="cadaver",
                condition=lambda p, z: event_manager.is_event_triggered("alchemist_second_poison"),
                description="Después de la segunda muerte por veneno"
            )
        ]
    ))
    
    # Estado "cadaver" - Lobby, tras segunda muerte por veneno
    manager.register_npc_state("Alquimista", NPCStateConfig(
        state_id="cadaver",
        zone_type="lobby",
        position=(50, 22),
        char="9",
        color="potion",
        dialog_tree_func=create_alchemist_cadaver_dialog,
        completed_dialog_func=create_alchemist_cadaver_completed,
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("alchemist_second_poison"),
    ))
