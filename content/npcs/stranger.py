"""
Diálogos del NPC Stranger.
Sistema completo de estados con transiciones y diálogos condicionales.
"""
from roguelike.systems.text import DialogTree, DialogNode, DialogOption, InteractiveText


# ============================================================================
# ESTADO: "start" (Piso 5 - Primera vez)
# ============================================================================

def create_stranger_floor5_dialog() -> DialogTree:
    """
    Crea el diálogo del Stranger en el piso 5 (primera vez que lo encuentras).
    
    Returns:
        DialogTree con el diálogo completo del piso 5
    """
    tree = DialogTree(start_node="greeting")
    
    # Nodo inicial: saludo
    greeting_node = DialogNode(
        node_id="greeting",
        speaker="Stranger",
        text="""¡Oh! Qué susto me has dado.---¿Yo? Estaba buscando a alguien\n
        Pero me he quedado sin pociones y mi arma y armadura están demasiado deterioradas.---
        Así que lo mejor será que me largue de aquí y vuelva más tarde.\n---Nos veremos arriba la próxima vez que... bueno.\nHasta luego.""",
        options=[
            DialogOption("¿Quién eres?", next_node="introduction")
        ]
    )
    tree.add_node(greeting_node)
    
    # Nodo de introducción
    def on_stranger_floor5_complete(player, zone):
        """Activa el evento cuando se completa el diálogo del Stranger en el piso 5."""
        from roguelike.systems.events import event_manager
        if not event_manager.is_event_triggered("stranger_floor5_met"):
            event_manager.trigger_event("stranger_floor5_met", player, zone, skip_conditions=True)
    
    introduction_node = DialogNode(
        node_id="introduction",
        speaker="Stranger",
        text="Solo soy un viajero como tú, perdido en estas mazmorras.\n---Pero ya he hablado demasiado. Debo irme.",
        options=[
            DialogOption("Adiós", next_node=None, action=on_stranger_floor5_complete)  # Activa evento al cerrar
        ]
    )
    tree.add_node(introduction_node)
    
    return tree


# ============================================================================
# ESTADO: "about_weapons" (Lobby - Primera conversación sobre armas)
# ============================================================================

def create_stranger_about_weapons_dialog() -> DialogTree:
    """
    Crea el diálogo del Stranger sobre armas (primera vez en el lobby).
    
    Returns:
        DialogTree con el diálogo completo sobre armas
    """
    tree = DialogTree(start_node="start")
    
    def on_weapons_dialog_complete(player, zone):
        """Activa el evento de desbloqueo de armas cuando se completa el diálogo."""
        from roguelike.systems.events import event_manager
        if not event_manager.is_event_triggered("stranger_lobby_weapons_unlocked"):
            event_manager.trigger_event("stranger_lobby_weapons_unlocked", player, zone, skip_conditions=True)
            # Guardar en qué run se completó este diálogo.
            # La transición al siguiente estado exige que haya pasado
            # al menos una run más (el jugador debe bajar y morir/volver).
            event_manager.set_data("stranger_weapons_completed_at_run", event_manager.run_count)
    
    start_node = DialogNode(
        node_id="start",
        speaker="Stranger",
        text="Ahí estás de nuevo.\n---Si, es un poco desagradable tener que morir para volver aquí arriba.\n¿Qué se le va a hacer?\n---¿Cómo? ¿En la mazmorra?\n---Tienes que fijarte mejor por el suelo, encontrarás objetos que te ayudarán.\nArmas y armaduras principalmente. Eso te dará una ventaja.\n---Vamos, baja y esta vez fíjate, a ver qué encuentras.",
        options=[
            DialogOption("Entendido", next_node=None, action=on_weapons_dialog_complete)
        ]
    )
    tree.add_node(start_node)
    
    return tree


def create_stranger_about_weapons_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'about_weapons' está completado."""
    return InteractiveText.create_simple_text(
        "Vamos, baja y esta vez fíjate, a ver qué encuentras.",
        title="Stranger",
        auto_close=False
    )


# ============================================================================
# ESTADO: "mision_nieta" (Lobby - Misión de la nieta)
# ============================================================================

def create_stranger_mision_nieta_dialog() -> DialogTree:
    """
    Crea el diálogo del Stranger sobre la misión de la nieta.
    
    Returns:
        DialogTree con el diálogo completo sobre la misión
    """
    tree = DialogTree(start_node="start")
    
    def on_potions_dialog_complete(player, zone):
        """Activa el evento de desbloqueo de pociones cuando se completa el diálogo."""
        from roguelike.systems.events import event_manager
        if not event_manager.is_event_triggered("stranger_lobby_potions_unlocked"):
            event_manager.trigger_event("stranger_lobby_potions_unlocked", player, zone, skip_conditions=True)
    
    start_node = DialogNode(
        node_id="start",
        speaker="Stranger",
        text="Ahí estás de nuevo.\nMucho mejor ahora, ¿verdad?\n---¿Cómo? ¿Que no has conseguido curarte ni una sola vez?\nOh diablos, fíjate mejor, también hay unos frascos con un líquido rojo.\n---Te ayudarán a curar tus heridas y resistir más tiempo allí abajo.",
        options=[
            DialogOption("Continuar", next_node="help_request", action=on_potions_dialog_complete)
        ]
    )
    tree.add_node(start_node)
    
    # Nodo con la pregunta de ayuda (aquí están las opciones Sí/No)
    help_node = DialogNode(
        node_id="help_request",
        speaker="Stranger",
        text="Si vas a bajar de nuevo tal vez puedas ayudarme.\nHe perdido a mi nieta ahí abajo. ¿Me ayudarías?",
        options=[
            DialogOption("Sí, te ayudaré", next_node="yes_response"),
            DialogOption("No, no lo haré", next_node=None)  # Cierra el diálogo
        ]
    )
    tree.add_node(help_node)
    
    # Respuesta si dice Sí - Explica en qué consiste la ayuda
    def on_accept_help(player, zone):
        """Acción que se ejecuta cuando el jugador acepta ayudar."""
        from roguelike.systems.events import event_manager
        # Activar evento de que aceptó ayudar
        event_manager.trigger_event("stranger_help_accepted", player, zone, skip_conditions=True)
        # Activar evento para spawneear a la nieta
        event_manager.trigger_event("granddaughter_spawn_enabled", player, zone, skip_conditions=True)
    
    yes_node = DialogNode(
        node_id="yes_response",
        speaker="Stranger",
        text="""jeje.. no esperaba menos.
---
Esta niña, la que se ha perdido es mi nieta.
---
Nos metimos buscando una forma de salir de esta habitación y la perdí.
---
Cuando la encuentres dile que estaré aquí esperándole.""",
        options=[
            DialogOption(
                "Entendido", 
                next_node=None,  # Cierra el diálogo; la transición FSM se maneja en _on_dialog_closed
                action=on_accept_help  # Activar eventos al aceptar
            )
        ]
    )
    tree.add_node(yes_node)
    
    return tree


def create_stranger_mision_nieta_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'mision_nieta' está completado."""
    from roguelike.systems.events import event_manager
    # Si ya aceptó ayudar, mostrar mensaje sobre la nieta
    if event_manager.is_event_triggered("stranger_help_accepted"):
        return InteractiveText.create_simple_text(
            "Gracias por ayudarme. Cuando la encuentres dile que estaré aquí esperándole.",
            title="Stranger",
            auto_close=False
        )
    else:
        # Si no ha aceptado ayudar, preguntarle de nuevo con opciones Sí/No
        # Usar el diálogo completo pero empezando desde help_request
        dialog_tree = create_stranger_mision_nieta_dialog()
        # Cambiar el start_node a help_request para que muestre la pregunta directamente
        dialog_tree.start_node = "help_request"
        return InteractiveText.create_dialog(dialog_tree, interaction_key="espacio")


# ============================================================================
# ESTADO: "waiting" (Lobby - Esperando)
# ============================================================================

def create_stranger_waiting_dialog() -> DialogTree:
    """
    Crea el diálogo del Stranger cuando está esperando (estado final).
    
    Returns:
        DialogTree con el diálogo de espera
    """
    tree = DialogTree(start_node="waiting")
    
    waiting_node = DialogNode(
        node_id="waiting",
        speaker="Stranger",
        text="¿Aún nada? No te preocupes, parece que tenemos todo el tiempo del mundo.",
        options=[
            DialogOption("Adiós", next_node=None)  # None cierra el diálogo
        ]
    )
    tree.add_node(waiting_node)
    
    return tree


# ============================================================================
# ESTADO: "mision_capturar_nieta" (Lobby - Capturar a la nieta)
# ============================================================================

def create_stranger_mision_capturar_nieta_dialog() -> DialogTree:
    """
    Crea el diálogo del Stranger cuando la misión cambia a capturar a la nieta.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="start")
    
    start_node = DialogNode(
        node_id="start",
        speaker="Stranger",
        text="[Diálogo del Stranger sobre capturar a la nieta - placeholder]",
        options=[
            DialogOption("Continuar", next_node=None)
        ]
    )
    tree.add_node(start_node)
    
    return tree


def create_stranger_mision_capturar_nieta_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'mision_capturar_nieta' está completado."""
    return InteractiveText.create_simple_text(
        "[Diálogo corto del Stranger - mision_capturar_nieta - placeholder]",
        title="Stranger",
        auto_close=False
    )


# ============================================================================
# ESTADO: "mision_nieta_ayudar" (Lobby - Investigar al Stranger)
# ============================================================================

def create_stranger_mision_nieta_ayudar_dialog() -> DialogTree:
    """
    Crea el diálogo del Stranger cuando el jugador decide ayudar a la nieta.
    El Stranger le da una poción de salud cada vez que el jugador vuelve al lobby.
    Tras 3 runs dando pociones, transiciona a 'indignado'.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="start")
    
    def on_give_potion(player, zone):
        """Da una poción de salud al jugador e incrementa el contador."""
        from roguelike.systems.events import event_manager
        from roguelike.items.potion import Potion
        
        # Dar poción de salud al jugador
        potion = Potion(
            x=player.x, y=player.y,
            potion_type="health_potion",
            name="Poción de Salud",
            effect="heal",
            value=20
        )
        added = player.add_to_inventory(potion)
        print(f"[DEBUG] on_give_potion: added={added}, inventario={len(player.inventory)} items, id(player)={id(player)}")
        
        # Incrementar contador de pociones dadas
        count = event_manager.get_data("stranger_potions_given", 0)
        event_manager.set_data("stranger_potions_given", count + 1)
        # Guardar en qué run se dio la última poción
        event_manager.set_data("stranger_potion_last_run", event_manager.run_count)
    
    start_node = DialogNode(
        node_id="start",
        speaker="Stranger",
        text="Por favor, tienes que encontrarla.\nEspera esto te ayudará, úsalo en el momento correcto, es una poción de salud.---Verás, ella no es una niña normal ¿Cómo explicarlo? Es complicado.\nAdemás tengo cierta prisa...",
        options=[
            DialogOption("Gracias", next_node=None, action=on_give_potion)
        ]
    )
    tree.add_node(start_node)
    
    return tree


def create_stranger_mision_nieta_ayudar_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'mision_nieta_ayudar' está completado (misma visita)."""
    return InteractiveText.create_simple_text(
        "Intentaré encontrarte más pociones. Necesito que encuentres a la chica, es muy importante.",
        title="Stranger",
        auto_close=False
    )


# ============================================================================
# ESTADO: "indignado" (Lobby - Stranger revela la verdad)
# ============================================================================

def create_stranger_indignado_dialog() -> DialogTree:
    """
    Crea el diálogo del Stranger cuando se indigna tras dar 3 pociones.
    Revela que la niña no es su nieta sino una criatura.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="start")
    
    def on_indignado_complete(player, zone):
        """Acción al completar el diálogo de indignado."""
        from roguelike.systems.events import event_manager
        if not event_manager.is_event_triggered("stranger_indignado"):
            event_manager.trigger_event("stranger_indignado", player, zone, skip_conditions=True)
    
    start_node = DialogNode(
        node_id="start",
        speaker="Stranger",
        text="¿Te estás riendo de mí? ¿Es eso? ¿Te aprovechas de un pobre anciano?---No, no, está bien. Debería habértelo explicado antes\nLa niña no es mi nieta, no exactamente.---De hecho no es una niña, no humana desde luego\nEs una criatura singular que llevo criando desde que salió del huevo---Necesito llevarla de vuelta a casa...",
        options=[
            DialogOption("Continuar", next_node=None, action=on_indignado_complete)
        ]
    )
    tree.add_node(start_node)
    
    return tree


def create_stranger_indignado_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'indignado' está completado."""
    return InteractiveText.create_simple_text(
        "Me costó mucho dinero obtenerla, es aún muy pequeña aunque parezca ya una niña crecidita...\nPor favor, tráemela.",
        title="Stranger",
        auto_close=False
    )


# ============================================================================
# REGISTRO DE ESTADOS DEL NPC
# ============================================================================

def register_npc_states(manager) -> None:
    """
    Registra todos los estados del Stranger en el sistema FSM.
    
    Esta función es llamada automáticamente por el sistema de auto-discovery.
    
    Args:
        manager: Instancia de NPCStateManager
    """
    from roguelike.systems.npc_states import NPCStateConfig, StateTransition
    from roguelike.systems.events import event_manager
    
    # Estado "start" - Piso 4, primera vez que lo encuentras
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="start",
        zone_type="dungeon",
        floor=4,
        position=None,  # Se calcula al spawnear en una habitación aleatoria
        dialog_tree_func=create_stranger_floor5_dialog,
        completion_condition=lambda p, z: event_manager.is_event_triggered("stranger_floor5_met"),
        transitions=[
            StateTransition(
                target_state="about_weapons",
                condition=lambda p, z: event_manager.is_event_triggered("stranger_floor5_met"),
                description="Después de hablar en piso 5"
            )
        ]
    ))
    
    # Estado "about_weapons" - Lobby, primera conversación (sobre armas)
    def check_weapons_completed(player, zone):
        """Verifica si el diálogo de armas fue completado."""
        return event_manager.is_event_triggered("stranger_lobby_weapons_unlocked")
    
    def check_weapons_and_run_completed(player, zone):
        """
        Verifica si se puede transicionar a mision_nieta.
        
        Requiere DOS cosas:
        1. El diálogo de armas fue completado
        2. El jugador ha completado al menos una run desde entonces
           (murió, escapó, etc.)
        
        Esto evita que el Stranger avance de estado solo por guardar/salir/entrar.
        """
        if not event_manager.is_event_triggered("stranger_lobby_weapons_unlocked"):
            return False
        completed_at = event_manager.get_data("stranger_weapons_completed_at_run", -1)
        return event_manager.run_count > completed_at
    
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="about_weapons",
        zone_type="lobby",
        position=(40, 20),
        dialog_tree_func=create_stranger_about_weapons_dialog,
        completed_dialog_func=create_stranger_about_weapons_completed,
        completion_condition=check_weapons_completed,
        transitions=[
            StateTransition(
                target_state="mision_nieta",
                condition=check_weapons_and_run_completed,
                description="Después de desbloquear armas Y completar una run"
            )
        ]
    ))
    
    # Estado "mision_nieta" - Lobby, misión de la nieta
    def check_help_accepted(player, zone):
        return event_manager.is_event_triggered("stranger_help_accepted")
    
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="mision_nieta",
        zone_type="lobby",
        position=(40, 20),
        dialog_tree_func=create_stranger_mision_nieta_dialog,
        completed_dialog_func=create_stranger_mision_nieta_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("stranger_lobby_potions_unlocked"),
        transitions=[
            StateTransition(
                target_state="waiting",
                condition=check_help_accepted,
                description="Después de aceptar ayudar"
            )
        ]
    ))
    
    # Estado "waiting" - Lobby, esperando (estado final)
    # No usa completed_dialog_func: siempre muestra el diálogo principal
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="waiting",
        zone_type="lobby",
        position=(40, 20),
        dialog_tree_func=create_stranger_waiting_dialog,
        # No tiene transiciones, es el estado final
    ))
    
    # Estado "mision_capturar_nieta" - Lobby, capturar a la nieta
    # NOTA: Este estado se alcanza programáticamente desde el diálogo de la nieta.
    # No tiene transiciones entrantes en el grafo FSM, así que necesita spawn_condition
    # para evitar ser seleccionado como estado inicial.
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="mision_capturar_nieta",
        zone_type="lobby",
        position=(40, 20),
        dialog_tree_func=create_stranger_mision_capturar_nieta_dialog,
        completed_dialog_func=create_stranger_mision_capturar_nieta_completed,
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("mision_capturar_nieta_started"),
    ))
    
    # Estado "mision_nieta_ayudar" - Lobby, el Stranger da pociones al jugador
    # Se alcanza programáticamente desde el diálogo de la nieta.
    # COMPORTAMIENTO ESPECIAL: Cada visita al lobby muestra el diálogo principal
    # de nuevo (da una poción). Tras 3 runs dando pociones, transiciona a 'indignado'.
    def check_indignado_transition(player, zone):
        """
        Verifica si el Stranger debe transicionar a 'indignado'.
        
        Requiere que se hayan dado 3+ pociones (una por run).
        Si aún no se cumple, resetea el estado a IN_PROGRESS para que
        la próxima visita al lobby muestre el diálogo principal de nuevo.
        """
        from roguelike.systems.npc_states import npc_state_manager, StateCompletion
        
        count = event_manager.get_data("stranger_potions_given", 0)
        if count >= 3:
            return True
        
        # Aún no suficientes pociones: resetear a IN_PROGRESS
        # para que la próxima visita muestre el diálogo principal (no el completado)
        npc_state_manager.set_state_completion(
            "Stranger", "mision_nieta_ayudar", StateCompletion.IN_PROGRESS
        )
        return False
    
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="mision_nieta_ayudar",
        zone_type="lobby",
        position=(40, 20),
        dialog_tree_func=create_stranger_mision_nieta_ayudar_dialog,
        completed_dialog_func=create_stranger_mision_nieta_ayudar_completed,
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("mision_nieta_ayudar_started"),
        transitions=[
            StateTransition(
                target_state="indignado",
                condition=check_indignado_transition,
                description="Después de dar 3 pociones al jugador"
            )
        ]
    ))
    
    # Estado "indignado" - Lobby, el Stranger revela la verdad sobre la niña
    # Se alcanza por transición desde mision_nieta_ayudar tras 3 runs.
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="indignado",
        zone_type="lobby",
        position=(40, 20),
        dialog_tree_func=create_stranger_indignado_dialog,
        completed_dialog_func=create_stranger_indignado_completed,
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("stranger_indignado") or evt_mgr.get_data("stranger_potions_given", 0) >= 3,
    ))


# ============================================================================
# FUNCIÓN LEGACY (mantener por compatibilidad temporal)
# ============================================================================

def create_stranger_lobby_dialog_2() -> DialogTree:
    """
    Función legacy - usa create_stranger_mision_nieta_dialog() en su lugar.
    Mantener por compatibilidad temporal.
    """
    return create_stranger_mision_nieta_dialog()
