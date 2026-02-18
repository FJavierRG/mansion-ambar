"""
Diálogos del NPC Nieta del Stranger.
"""
from roguelike.systems.text import DialogTree, DialogNode, DialogOption, InteractiveText


def create_nieta_dialog() -> DialogTree:
    """
    Crea el diálogo de la nieta cuando el jugador la encuentra.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="greeting")
    
    # Nodo inicial: diálogo placeholder
    greeting_node = DialogNode(
        node_id="greeting",
        speaker="nieta",
        text="¿Te ha enviado ese viejo baboso?\n Lleva persiguiéndome días, me observa con mirada lasciva.",
        options=[
            DialogOption("Continuar", next_node="options")
        ]
    )
    tree.add_node(greeting_node)
    
    # Nodo con dos opciones
    options_node = DialogNode(
        node_id="options",
        speaker="nieta",
        text="¿Vienes a secuestrarme tú también? ¿Me vas a llevar con él?",
        options=[
            # Opción 1: Lleva al nodo "response_abuelo"
            DialogOption("Tu abuelo te está buscando. Ve con él, ahora.", next_node="response_obligar"),
            # Opción 2: Lleva al nodo "response_baboso"
            DialogOption("¿Ese viejo baboso?", next_node="response_ayudar")
        ]
    )
    tree.add_node(options_node)
    
    # RAMIFICACIÓN 1: Respuesta si elige "Tu abuelo te está buscando"
    def on_obligar_nieta(player, zone):
        """Acción cuando el jugador obliga a la nieta a subir."""
        from roguelike.systems.events import event_manager
        from roguelike.systems.npc_states import npc_state_manager, StateCompletion
        
        # Activar eventos
        event_manager.trigger_event("mision_capturar_nieta_started", player, zone, skip_conditions=True)
        event_manager.trigger_event("nieta_obligada", player, zone, skip_conditions=True)
        event_manager.trigger_event("granddaughter_found", player, zone, skip_conditions=True)
        
        # Cambiar estado del Stranger: mision_nieta → mision_capturar_nieta
        npc_state_manager.set_current_state("Stranger", "mision_capturar_nieta")
        npc_state_manager.set_state_completion("Stranger", "mision_nieta", StateCompletion.COMPLETED)
        npc_state_manager.set_state_completion("Stranger", "mision_capturar_nieta", StateCompletion.IN_PROGRESS)
        
        # Cambiar estado de nieta: found → obligada
        npc_state_manager.set_current_state("nieta", "obligada")
        npc_state_manager.set_state_completion("nieta", "found", StateCompletion.COMPLETED)
        npc_state_manager.set_state_completion("nieta", "obligada", StateCompletion.IN_PROGRESS)
        
        # Mover la niña al lobby (se hará mediante evento)
        # La entidad se eliminará de la dungeon y se creará en el lobby
    
    response_obligar_node = DialogNode(
        node_id="response_obligar",
        speaker="nieta",
        text="...Vaya, así que eres como él ¿Te van estas cosas?---¿Esto te gusta? ¿Las niñas?---...---Subiré a ver que quiere ese viejo baboso.",
        options=[
            DialogOption("Continuar", next_node=None, action=on_obligar_nieta)  # Ejecuta acción al cerrar
        ]
    )
    tree.add_node(response_obligar_node)
    
    # RAMIFICACIÓN 2: Respuesta si elige "¿Ese viejo baboso?"
    def on_ayudar_nieta(player, zone):
        """Acción cuando el jugador decide ayudar a la nieta."""
        from roguelike.systems.events import event_manager
        from roguelike.systems.npc_states import npc_state_manager, StateCompletion
        
        # Activar eventos
        event_manager.trigger_event("mision_nieta_ayudar_started", player, zone, skip_conditions=True)
        event_manager.trigger_event("nieta_ayudando", player, zone, skip_conditions=True)
        event_manager.trigger_event("granddaughter_found", player, zone, skip_conditions=True)
        
        # Cambiar estado del Stranger: mision_nieta → mision_nieta_ayudar
        npc_state_manager.set_current_state("Stranger", "mision_nieta_ayudar")
        npc_state_manager.set_state_completion("Stranger", "mision_nieta_ayudar", StateCompletion.IN_PROGRESS)
        # NOTA: mision_nieta NO se completa, ambas misiones están activas
        
        # Cambiar estado de nieta: found → ayudando
        npc_state_manager.set_current_state("nieta", "ayudando")
        npc_state_manager.set_state_completion("nieta", "found", StateCompletion.COMPLETED)
        npc_state_manager.set_state_completion("nieta", "ayudando", StateCompletion.IN_PROGRESS)
        
        # Mover la niña al piso 1 (se hará mediante evento)
        # La entidad se eliminará de la dungeon actual y se creará en el piso 1
    
    response_ayudar_node = DialogNode(
        node_id="response_ayudar",
        speaker="nieta",
        text="""A tí también te ha mentido diciendo que es mi abuelo, ¿verdad?---No lo es. Me quiere atrapar pero no conozco el motivo.\n¿Me ayudarías a entender qué le pasa al viejo baboso?---
        Ve y pregúntale---Yo me esconderé en la primera planta y te esperaré.""",
        options=[
            DialogOption("Continuar", next_node=None, action=on_ayudar_nieta)  # Ejecuta acción al cerrar
        ]
    )
    tree.add_node(response_ayudar_node)
    
    return tree


def create_nieta_completed() -> InteractiveText:
    """Diálogo corto cuando la nieta ya fue encontrada (estado ayudando)."""
    return InteractiveText.create_simple_text(
        "Vamos, ve y entérate qué le pasa al viejo baboso. Yo esperaré aquí en la primera planta.",
        title="nieta",
        auto_close=False
    )


def create_nieta_obligada_dialog() -> DialogTree:
    """
    Crea el diálogo de la nieta cuando está obligada en el lobby.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="obligada")
    
    obligada_node = DialogNode(
        node_id="obligada",
        speaker="nieta",
        text="Enhorabuena, has secuestrado a una niña pequeña. Espero que te pierdas entre esos pasillos.---¿Qué va a ser ahora de mí? ¿Quién va a ayudar a esta pobre cría?---...---¿Ha colado?",
        options=[
            DialogOption("Continuar", next_node=None)
        ]
    )
    tree.add_node(obligada_node)
    
    return tree


def create_nieta_obligada_completed() -> InteractiveText:
    """Diálogo corto cuando la nieta está obligada (completado)."""
    return InteractiveText.create_simple_text(
        "Ya encontraré una forma de deshacerme del viejo baboso...",
        title="nieta",
        auto_close=False
    )


# ============================================================================
# REGISTRO DE ESTADOS DEL NPC
# ============================================================================

def register_npc_states(manager) -> None:
    """
    Registra todos los estados de la Nieta en el sistema FSM.
    
    Esta función es llamada automáticamente por el sistema de auto-discovery.
    
    Args:
        manager: Instancia de NPCStateManager
    """
    from roguelike.systems.npc_states import NPCStateConfig, StateTransition
    from roguelike.systems.events import event_manager
    import random
    
    # Estado "found" - Dungeon, primera vez que la encuentras
    def nieta_found_spawn_condition(floor: int, evt_mgr) -> bool:  # noqa: ARG001
        """Condición de spawn para nieta found: piso >= 2 y evento activado."""
        if floor < 2:
            return False
        if not evt_mgr.is_event_triggered("stranger_help_accepted"):
            return False
        # 40% de probabilidad
        return random.random() <= 0.4
    
    manager.register_npc_state("nieta", NPCStateConfig(
        state_id="found",
        zone_type="dungeon",
        floor=None,  # Puede aparecer en cualquier piso >= 2 (condición en spawn_condition)
        position=None,  # Posición aleatoria
        dialog_tree_func=create_nieta_dialog,
        completed_dialog_func=create_nieta_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("granddaughter_found"),
        spawn_condition=nieta_found_spawn_condition,
    ))
    
    # Estado "obligada" - Lobby, después de obligarla a subir
    # NOTA: Este estado se alcanza programáticamente desde el diálogo de la nieta.
    # Necesita spawn_condition para evitar ser seleccionado como estado inicial.
    def check_nieta_desaparecen_transition(player, zone):
        """
        Verifica si la nieta debe desaparecer junto con el Stranger.
        Misma condición que el Stranger: 3 runs tras completar mision_capturar_nieta.
        """
        completed_at = event_manager.get_data("mision_capturar_nieta_completed_at_run", -1)
        if completed_at < 0:
            return False
        return event_manager.run_count >= completed_at + 3
    
    manager.register_npc_state("nieta", NPCStateConfig(
        state_id="obligada",
        zone_type="lobby",
        position=(45, 20),  # Cerca del Stranger pero separada
        dialog_tree_func=create_nieta_obligada_dialog,
        completed_dialog_func=create_nieta_obligada_completed,
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("nieta_obligada"),
        transitions=[
            StateTransition(
                target_state="desaparecida",
                condition=check_nieta_desaparecen_transition,
                description="Desaparece junto con el Stranger tras 3 runs"
            )
        ]
    ))
    
    # Estado "desaparecida" - Nieta desaparece junto con el Stranger
    # zone_type=None hace que no spawnee en ninguna zona.
    manager.register_npc_state("nieta", NPCStateConfig(
        state_id="desaparecida",
        zone_type=None,  # No aparece en ninguna zona
    ))
    
    # Estado "ayudando" - Dungeon Piso 1, esperando
    def nieta_ayudando_spawn_condition(floor: int, evt_mgr) -> bool:
        """Condición de spawn para nieta ayudando: evento activado."""
        return evt_mgr.is_event_triggered("nieta_ayudando")
    
    manager.register_npc_state("nieta", NPCStateConfig(
        state_id="ayudando",
        zone_type="dungeon",
        floor=1,  # Solo en el piso 1
        position=None,  # Posición aleatoria en el piso 1
        dialog_tree_func=None,  # Usa el diálogo corto directamente
        completed_dialog_func=create_nieta_completed,
        spawn_condition=nieta_ayudando_spawn_condition,
    ))
