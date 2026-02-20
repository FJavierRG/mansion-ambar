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


def create_nieta_descubierta_dialog() -> DialogTree:
    """
    Crea el diálogo de la nieta cuando ha sido descubierta (Stranger entró en estado indignado).
    Al completar este diálogo, Stranger pasa al estado contratado_mercenario.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="descubierta")
    
    def on_descubierta_complete(player, zone):
        """Acción al completar el diálogo de descubierta: Stranger → contratado_mercenario."""
        from roguelike.systems.events import event_manager
        from roguelike.systems.npc_states import npc_state_manager, StateCompletion
        
        # Activar evento
        if not event_manager.is_event_triggered("nieta_descubierta"):
            event_manager.trigger_event("nieta_descubierta", player, zone, skip_conditions=True)
        
        # Cambiar estado del Stranger: indignado → contratado_mercenario
        npc_state_manager.set_current_state("Stranger", "contratado_mercenario")
        npc_state_manager.set_state_completion("Stranger", "indignado", StateCompletion.COMPLETED)
        npc_state_manager.set_state_completion("Stranger", "contratado_mercenario", StateCompletion.IN_PROGRESS)
        
        # Guardar en qué run se entró para calcular timeout de la ruta sin veneno
        event_manager.set_data("contratado_mercenario_entered_at_run", event_manager.run_count)
    
    descubierta_node = DialogNode(
        node_id="descubierta",
        speaker="nieta",
        text="Le he visto por los pasillos. Se ha artado y me está buscando él mismo ¿O tal vez ha enviado a alguien a darme caza?---Sea lo que sea me persigue ¿Qué puedo hacer? No sé utilizar armas, no tengo con qué defenderme...",
        options=[
            DialogOption("Continuar", next_node=None, action=on_descubierta_complete)
        ]
    )
    tree.add_node(descubierta_node)
    
    return tree


def create_nieta_descubierta_completed():
    """
    Diálogo corto cuando el estado 'descubierta' está completado.
    
    Incluye opción condicional: si el jugador tiene una poción de veneno,
    puede dársela a la nieta para defenderse. Al darle el veneno, continúa
    el diálogo inmediatamente y al terminar ambos NPCs desaparecen.
    
    Returns:
        InteractiveText con diálogo y opción condicional
    """
    tree = DialogTree(start_node="descubierta_short")
    
    def has_poison_potion(player) -> bool:
        """Verifica si el jugador tiene una poción de veneno en el inventario."""
        from roguelike.items.potion import Potion
        for item in player.inventory:
            if isinstance(item, Potion) and item.potion_type == "poison_potion":
                return True
        return False
    
    def on_give_poison(player, zone):
        """Acción al dar la poción de veneno a la nieta: ambos NPCs desaparecen."""
        from roguelike.systems.events import event_manager
        from roguelike.systems.npc_states import npc_state_manager, StateCompletion
        from roguelike.items.potion import Potion
        
        # Buscar y consumir la poción de veneno del inventario
        for item in player.inventory:
            if isinstance(item, Potion) and item.potion_type == "poison_potion":
                player.inventory.remove(item)
                break
        
        # Activar evento
        event_manager.trigger_event("nieta_veneno_entregado", player, zone, skip_conditions=True)
        
        # Guardar en qué run se dio el veneno (para calcular cuándo aparece el cadáver)
        event_manager.set_data("stranger_desaparecido_at_run", event_manager.run_count)
        
        # Cambiar estado de nieta: descubierta → huida
        npc_state_manager.set_current_state("nieta", "huida")
        npc_state_manager.set_state_completion("nieta", "descubierta", StateCompletion.COMPLETED)
        npc_state_manager.set_state_completion("nieta", "huida", StateCompletion.IN_PROGRESS)
        
        # Cambiar estado de Stranger: contratado_mercenario → desaparecido
        npc_state_manager.set_current_state("Stranger", "desaparecido")
        npc_state_manager.set_state_completion("Stranger", "contratado_mercenario", StateCompletion.COMPLETED)
        npc_state_manager.set_state_completion("Stranger", "desaparecido", StateCompletion.IN_PROGRESS)
    
    descubierta_short_node = DialogNode(
        node_id="descubierta_short",
        speaker="nieta",
        text="Estoy perdida, hay alguien buscándome por estos pasillos...",
        options=[
            DialogOption(
                "Tengo este veneno, úsalo para defenderte",
                next_node="veneno_response",
                condition=has_poison_potion,
            ),
            DialogOption("Cerrar", next_node=None)
        ]
    )
    tree.add_node(descubierta_short_node)
    
    # Nodo de respuesta al dar el veneno (continúa inmediatamente)
    veneno_response_node = DialogNode(
        node_id="veneno_response",
        speaker="nieta",
        text="Vaya, esto puede serme muy útil... Si consiguiera escabullirme...---Tal vez al anochecer...---Te estoy muy agradecida, el veneno me servirá.",
        options=[
            DialogOption("Continuar", next_node=None, action=on_give_poison)
        ]
    )
    tree.add_node(veneno_response_node)
    
    return InteractiveText.create_dialog(tree, interaction_key="espacio")


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
# ESTADO: "cadaver_juntos_nieta" (Dungeon - Cadáver de la Nieta, ruta sin veneno)
# ============================================================================

def create_nieta_cadaver_juntos_dialog() -> DialogTree:
    """
    Crea el diálogo al encontrar el cadáver de la nieta junto al del Stranger.
    
    Ruta: Ayudar a la nieta → NO dar veneno → El mercenario los alcanza.
    Entre los ropajes de la niña el jugador encuentra la llave con forma de corazón.
    
    Returns:
        DialogTree con el diálogo del cadáver
    """
    tree = DialogTree(start_node="discover")
    
    discover_node = DialogNode(
        node_id="discover",
        speaker="",
        text="El cuerpo sin vida de la niña yace junto al del viejo.\nSea lo que fuese lo que pasó aquí, parece que ninguno de los dos salió con vida.\n---Entre sus ropajes brilla algo con una forma peculiar.",
        options=[
            DialogOption("Recoger el objeto", next_node=None, action=lambda p, z: _on_loot_cadaver_nieta(p, z))
        ]
    )
    tree.add_node(discover_node)
    
    return tree


def _on_loot_cadaver_nieta(player, zone):
    """Acción al saquear el cadáver de la nieta. Entrega la Llave con forma de corazón."""
    from roguelike.systems.events import event_manager
    from roguelike.items.item import create_item
    
    # Marcar como saqueado
    event_manager.triggered_events.add("nieta_cadaver_looted")
    
    # Guardar en qué run se saqueó para que ambos cadáveres desaparezcan en la siguiente
    event_manager.set_data("cadaver_juntos_looted_at_run", event_manager.run_count)
    
    # Entregar: Llave con forma de corazón
    key = create_item("heart_key", x=player.x, y=player.y)
    if key:
        player.add_to_inventory(key)


def create_nieta_cadaver_juntos_completed() -> InteractiveText:
    """Diálogo corto cuando el cadáver de la nieta ya fue saqueado."""
    return InteractiveText.create_simple_text(
        "Los restos de la niña. Ya no queda nada entre sus pertenencias.",
        title="",
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
        completion_condition=lambda p, z: True,
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
    
    def check_descubierta_transition(player, zone):
        """Verifica si la nieta debe pasar a 'descubierta' (Stranger entró en indignado)."""
        return event_manager.is_event_triggered("stranger_indignado")
    
    manager.register_npc_state("nieta", NPCStateConfig(
        state_id="ayudando",
        zone_type="dungeon",
        floor=1,  # Solo en el piso 1
        position=None,  # Posición aleatoria en el piso 1
        dialog_tree_func=None,  # Usa el diálogo corto directamente
        completed_dialog_func=create_nieta_completed,
        completion_condition=lambda p, z: True,  # Se completa tras agotar el diálogo
        spawn_condition=nieta_ayudando_spawn_condition,
        transitions=[
            StateTransition(
                target_state="descubierta",
                condition=check_descubierta_transition,
                description="Cuando Stranger entra en estado indignado"
            )
        ]
    ))
    
    # Estado "descubierta" - Dungeon Piso 1, Stranger la ha descubierto
    # Se llega por transición desde ayudando cuando stranger_indignado.
    # Al completar el diálogo principal, Stranger pasa a contratado_mercenario.
    # En el diálogo completado, si el jugador tiene veneno puede dárselo.
    def nieta_descubierta_spawn_condition(floor: int, evt_mgr) -> bool:
        """Condición de spawn para nieta descubierta: evento activado."""
        return evt_mgr.is_event_triggered("stranger_indignado")
    
    def check_huida_transition(player, zone):
        """Verifica si la nieta debe pasar a 'huida' (jugador le dio el veneno)."""
        return event_manager.is_event_triggered("nieta_veneno_entregado")
    
    def check_cadaver_juntos_nieta_transition(player, zone):
        """
        Verifica si la nieta muere junto al Stranger (ruta sin veneno).
        
        Requiere:
        - La nieta NO recibió el veneno
        - Han pasado 4+ runs desde que Stranger entró en contratado_mercenario
        """
        if event_manager.is_event_triggered("nieta_veneno_entregado"):
            return False
        entered_at = event_manager.get_data("contratado_mercenario_entered_at_run", -1)
        if entered_at < 0:
            return False
        return event_manager.run_count >= entered_at + 4
    
    manager.register_npc_state("nieta", NPCStateConfig(
        state_id="descubierta",
        zone_type="dungeon",
        floor=1,  # Solo en el piso 1
        position=None,  # Posición aleatoria en el piso 1
        dialog_tree_func=create_nieta_descubierta_dialog,
        completed_dialog_func=create_nieta_descubierta_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("nieta_descubierta"),
        spawn_condition=nieta_descubierta_spawn_condition,
        transitions=[
            # Orden importante: primero la ruta del veneno, luego la timeout
            StateTransition(
                target_state="huida",
                condition=check_huida_transition,
                description="Cuando el jugador da el veneno a la nieta"
            ),
            StateTransition(
                target_state="cadaver_juntos_nieta",
                condition=check_cadaver_juntos_nieta_transition,
                description="Ambos mueren tras 4 runs sin que el jugador dé el veneno"
            )
        ]
    ))
    
    # Estado "huida" - Nieta se escabulle con el veneno y desaparece
    # zone_type=None hace que no spawnee en ninguna zona.
    # Se llega por acción del diálogo de descubierta (dar veneno).
    # Al mismo tiempo, Stranger pasa a estado 'desaparecido'.
    manager.register_npc_state("nieta", NPCStateConfig(
        state_id="huida",
        zone_type=None,  # No aparece en ninguna zona
    ))
    
    # Estado "cadaver_juntos_nieta" - Dungeon, cadáver de la nieta (ruta sin veneno)
    # Se llega por transición desde 'descubierta' tras 4 runs sin veneno.
    # El mercenario les alcanzó. El jugador encuentra la Llave con forma de corazón.
    # spawn_near_npc="Stranger" asegura que spawnee adyacente al cadáver del Stranger.
    manager.register_npc_state("nieta", NPCStateConfig(
        state_id="cadaver_juntos_nieta",
        zone_type="dungeon",
        floor=2,
        position=None,
        char="%",
        color="dark_red",
        blocks=False,
        sprite_override="nieta_dead",
        spawn_near_npc="Stranger",
        dialog_tree_func=create_nieta_cadaver_juntos_dialog,
        completed_dialog_func=create_nieta_cadaver_juntos_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("nieta_cadaver_looted"),
        spawn_condition=lambda floor, evt_mgr: not evt_mgr.is_event_triggered("nieta_veneno_entregado") and evt_mgr.is_event_triggered("nieta_descubierta"),
        transitions=[
            StateTransition(
                target_state="cadaver_juntos_nieta_done",
                condition=lambda p, z: (
                    event_manager.get_data("cadaver_juntos_looted_at_run", -1) >= 0
                    and event_manager.run_count > event_manager.get_data("cadaver_juntos_looted_at_run", -1)
                ),
                description="Quest completada: llave recogida en run anterior"
            )
        ]
    ))
    
    # Estado "cadaver_juntos_nieta_done" - Quest completada, nieta ya no aparece
    manager.register_npc_state("nieta", NPCStateConfig(
        state_id="cadaver_juntos_nieta_done",
        zone_type=None,  # No aparece en ninguna zona
    ))
