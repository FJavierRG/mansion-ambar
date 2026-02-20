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
    Crea el diálogo del Stranger cuando el jugador obligó a la nieta a subir.
    Stranger agradece y entrega la Llave con forma de corazón.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="start")
    
    start_node = DialogNode(
        node_id="start",
        speaker="Stranger",
        text="Te agradezco enormemente que hayas encontrado a la niña, preciosa, preciosa niña\nNo te preocupes por su enfado, se le pasará enseguida y podremos marcharnos.---Solo espero que no vuelva a escapárseme una vez bajemos a los túneles...",
        options=[
            DialogOption("Continuar", next_node="reward")
        ]
    )
    tree.add_node(start_node)
    
    def on_give_heart_key(player, zone):
        """Da la Llave con forma de corazón al jugador y guarda el run actual."""
        from roguelike.items.item import create_item
        from roguelike.systems.events import event_manager
        key = create_item("heart_key", x=player.x, y=player.y)
        if key:
            player.add_to_inventory(key)
        # Guardar en qué run se completó para contar 3 runs hasta la desaparición
        event_manager.set_data("mision_capturar_nieta_completed_at_run", event_manager.run_count)
    
    reward_node = DialogNode(
        node_id="reward",
        speaker="Stranger",
        text="Por cierto, antes mientras estaba comprobando que no tuviera ninguna herida he encontrado que llevaba esto.\nPuedes quedártelo como muestra de agradecimiento.",
        options=[
            DialogOption("Gracias", next_node=None, action=on_give_heart_key)
        ]
    )
    tree.add_node(reward_node)
    
    return tree


def create_stranger_mision_capturar_nieta_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'mision_capturar_nieta' está completado."""
    return InteractiveText.create_simple_text(
        "Aún sigo pensando cómo podemos salir de aquí...",
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
        """Da una poción de salud al jugador e incrementa el contador.
        Solo da una poción por run (guarda en qué run se dio la última)."""
        from roguelike.systems.events import event_manager
        from roguelike.items.item import create_item
        
        # Guarda: solo dar una poción por run
        last_run = event_manager.get_data("stranger_potion_last_run", -1)
        if last_run == event_manager.run_count:
            return
        
        # Dar poción de salud al jugador
        potion = create_item("health_potion", x=player.x, y=player.y)
        player.add_to_inventory(potion)
        
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
# ESTADO: "contratado_mercenario" (Lobby - Stranger contrata a otro)
# ============================================================================

def create_stranger_contratado_mercenario_dialog() -> DialogTree:
    """
    Crea el diálogo del Stranger cuando ha contratado a un mercenario.
    Se llega aquí cuando la nieta completa su diálogo de 'descubierta'.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="start")
    
    start_node = DialogNode(
        node_id="start",
        speaker="Stranger",
        text="Ya no te necesito. He encontrado a otro que hará mejor el trabajo---Estabas tardando demasiado y no tengo todo el tiempo del mundo.",
        options=[
            DialogOption("Continuar", next_node=None)
        ]
    )
    tree.add_node(start_node)
    
    return tree


def create_stranger_contratado_mercenario_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'contratado_mercenario' está completado."""
    return InteractiveText.create_simple_text(
        "...",
        title="Stranger",
        auto_close=False
    )


# ============================================================================
# ESTADO: "cadaver_envenenado" (Dungeon - Cadáver del Stranger tras el veneno)
# ============================================================================

def create_stranger_cadaver_envenenado_dialog() -> DialogTree:
    """
    Crea el diálogo al encontrar el cadáver del Stranger envenenado por la nieta.
    El jugador recibe la carta de agradecimiento y recompensas.
    
    Ruta: Ayudar a la nieta → Dar veneno → La nieta envenena al Stranger.
    
    Returns:
        DialogTree con el diálogo del cadáver
    """
    tree = DialogTree(start_node="discover")
    
    discover_node = DialogNode(
        node_id="discover",
        speaker="",
        text="Los restos del Extraño yacen en el suelo, su piel amoratada delata el veneno.\n---Entre sus ropas encuentras una nota doblada con esmero y algunos objetos.",
        options=[
            DialogOption("Leer la nota", next_node="carta")
        ]
    )
    tree.add_node(discover_node)
    
    carta_node = DialogNode(
        node_id="carta",
        speaker="Carta de la niña",
        text="«Siento haberte mentido. No soy lo que dije ser, pero tampoco lo era él.\n---Necesitaba deshacerme de él para recuperar algo que me pertenece.\nNo quería involucrarte más de lo necesario.\n---Gracias por el veneno. Me ha sido muy útil.\nEspero que lo que he dejado junto al viejo te sirva de algo.\n---Cuídate entre esos pasillos. Hay cosas peores que un viejo mentiroso.»",
        options=[
            DialogOption("Recoger los objetos", next_node=None, action=lambda p, z: _on_loot_cadaver_envenenado(p, z))
        ]
    )
    tree.add_node(carta_node)
    
    return tree


def _on_loot_cadaver_envenenado(player, zone):
    """Acción al saquear el cadáver envenenado del Stranger. Entrega todas las recompensas."""
    from roguelike.systems.events import event_manager
    from roguelike.items.item import create_item
    
    # Marcar como saqueado
    event_manager.triggered_events.add("stranger_cadaver_looted")
    
    # Entregar: Carta de la niña
    carta = create_item("carta_agradecimiento_nieta", x=player.x, y=player.y)
    if carta:
        player.add_to_inventory(carta)
    
    # Entregar: 50 monedas de oro
    for _ in range(50):
        gold = create_item("gold", x=player.x, y=player.y)
        if gold:
            player.add_to_inventory(gold)
    
    # Entregar: Poción de Vida Mayor
    potion = create_item("greater_health_potion", x=player.x, y=player.y)
    if potion:
        player.add_to_inventory(potion)
    
    # Entregar: Perfume femenino (item clave pendiente de desarrollo)
    perfume = create_item("perfume_femenino", x=player.x, y=player.y)
    if perfume:
        player.add_to_inventory(perfume)


def create_stranger_cadaver_envenenado_completed() -> InteractiveText:
    """Diálogo corto cuando el cadáver ya fue saqueado."""
    return InteractiveText.create_simple_text(
        "Los restos del Extraño yacen inertes. Ya no queda nada de valor entre sus pertenencias.",
        title="",
        auto_close=False
    )


# ============================================================================
# ESTADO: "cadaver_juntos" (Dungeon - Cadáver del Stranger, ruta sin veneno)
# ============================================================================

def create_stranger_cadaver_juntos_dialog() -> DialogTree:
    """
    Crea el diálogo al encontrar el cadáver del Stranger junto al de la nieta.
    
    Ruta: Ayudar a la nieta → NO dar veneno → El mercenario los alcanza a ambos.
    
    Returns:
        DialogTree con el diálogo del cadáver
    """
    tree = DialogTree(start_node="discover")
    
    discover_node = DialogNode(
        node_id="discover",
        speaker="",
        text="Los restos del Extraño yacen en el suelo junto a los de la niña.\nParece que al final se encontraron.\n---No queda nada de valor entre las pertenencias del viejo.",
        options=[
            DialogOption("Cerrar", next_node=None)
        ]
    )
    tree.add_node(discover_node)
    
    return tree


def create_stranger_cadaver_juntos_completed() -> InteractiveText:
    """Diálogo corto para el cadáver del Stranger (ya visto)."""
    return InteractiveText.create_simple_text(
        "Los restos del Extraño. No queda nada de valor.",
        title="",
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
    def check_capturar_nieta_completed(player, zone):
        """Verifica si el diálogo de capturar nieta fue completado."""
        return event_manager.is_event_triggered("mision_capturar_nieta_started")
    
    def check_desaparecen_transition(player, zone):
        """
        Verifica si Stranger y nieta deben desaparecer.
        
        Requiere que se hayan completado 3 runs desde que se completó
        el diálogo de mision_capturar_nieta.
        """
        completed_at = event_manager.get_data("mision_capturar_nieta_completed_at_run", -1)
        if completed_at < 0:
            return False
        return event_manager.run_count >= completed_at + 3
    
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="mision_capturar_nieta",
        zone_type="lobby",
        position=(40, 20),
        dialog_tree_func=create_stranger_mision_capturar_nieta_dialog,
        completed_dialog_func=create_stranger_mision_capturar_nieta_completed,
        completion_condition=check_capturar_nieta_completed,
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("mision_capturar_nieta_started"),
        transitions=[
            StateTransition(
                target_state="stranger_y_nieta_desaparecen",
                condition=check_desaparecen_transition,
                description="Después de 3 runs tras completar mision_capturar_nieta"
            )
        ]
    ))
    
    # Estado "stranger_y_nieta_desaparecen" - Ambos NPCs desaparecen
    # zone_type=None hace que el NPC no spawnee en ninguna zona.
    # Este es un estado "sumidero": una vez aquí, el Stranger no aparece más.
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="stranger_y_nieta_desaparecen",
        zone_type=None,  # No aparece en ninguna zona
    ))
    
    # Estado "mision_nieta_ayudar" - Lobby, el Stranger da pociones al jugador
    # Se alcanza programáticamente desde el diálogo de la nieta.
    # COMPORTAMIENTO: Da una poción por run. Tras 3 runs, transiciona a 'indignado'.
    # completion_condition permite que _on_dialog_closed marque COMPLETED tras hablar,
    # así las interacciones siguientes en la misma visita muestran el diálogo corto.
    def check_indignado_transition(player, zone):
        """
        Verifica si el Stranger debe transicionar a 'indignado'.
        
        Requiere que se hayan dado 3+ pociones (una por run).
        Si aún no se cumple, resetea el estado a IN_PROGRESS solo si estamos
        en una run nueva (para que la próxima visita muestre el diálogo principal).
        """
        from roguelike.systems.npc_states import npc_state_manager, StateCompletion
        
        count = event_manager.get_data("stranger_potions_given", 0)
        if count >= 3:
            return True
        
        # Solo resetear a IN_PROGRESS si estamos en una run nueva
        # (la poción se dio en una run anterior). Esto permite que dentro
        # de la misma visita el estado siga COMPLETED y muestre el diálogo corto.
        last_run = event_manager.get_data("stranger_potion_last_run", -1)
        if last_run != event_manager.run_count:
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
        completion_condition=lambda p, z: True,  # Siempre se completa tras hablar (1 poción por visita)
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
    # Transiciona a contratado_mercenario cuando la nieta completa su diálogo de descubierta.
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="indignado",
        zone_type="lobby",
        position=(40, 20),
        dialog_tree_func=create_stranger_indignado_dialog,
        completed_dialog_func=create_stranger_indignado_completed,
        completion_condition=lambda p, z: True,  # Se completa tras agotar el diálogo principal
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("stranger_indignado") or evt_mgr.get_data("stranger_potions_given", 0) >= 3,
        transitions=[
            StateTransition(
                target_state="contratado_mercenario",
                condition=lambda p, z: event_manager.is_event_triggered("nieta_descubierta"),
                description="Cuando la nieta completa su diálogo de descubierta"
            )
        ]
    ))
    
    # Estado "contratado_mercenario" - Lobby, el Stranger contrata a otro
    # Se alcanza programáticamente desde el diálogo de la nieta (descubierta).
    # Necesita spawn_condition para evitar ser seleccionado como estado inicial.
    def check_desaparecido_transition(player, zone):
        """Verifica si Stranger debe desaparecer (nieta recibió el veneno)."""
        return event_manager.is_event_triggered("nieta_veneno_entregado")
    
    def check_cadaver_juntos_transition(player, zone):
        """
        Verifica si Stranger y nieta mueren juntos (ruta sin veneno).
        
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
    
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="contratado_mercenario",
        zone_type="lobby",
        position=(40, 20),
        dialog_tree_func=create_stranger_contratado_mercenario_dialog,
        completed_dialog_func=create_stranger_contratado_mercenario_completed,
        completion_condition=lambda p, z: True,
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("nieta_descubierta"),
        transitions=[
            # Orden importante: primero la ruta del veneno, luego la timeout
            StateTransition(
                target_state="desaparecido",
                condition=check_desaparecido_transition,
                description="Cuando la nieta recibe el veneno y huye"
            ),
            StateTransition(
                target_state="cadaver_juntos",
                condition=check_cadaver_juntos_transition,
                description="Ambos mueren tras 4 runs sin que el jugador dé el veneno"
            )
        ]
    ))
    
    # Estado "cadaver_juntos" - Dungeon, cadáver del Stranger junto al de la nieta (ruta sin veneno)
    # Se llega por transición desde 'contratado_mercenario' tras 4 runs sin veneno.
    # El mercenario les alcanzó. El loot está en el cadáver de la nieta, no en este.
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="cadaver_juntos",
        zone_type="dungeon",
        floor=2,  # Aparece en el piso 2 (mismo que el cadáver de la nieta)
        position=None,  # Posición aleatoria
        char="%",
        color="dark_red",
        sprite_override="stranger_dead",
        dialog_tree_func=create_stranger_cadaver_juntos_dialog,
        completed_dialog_func=create_stranger_cadaver_juntos_completed,
        completion_condition=lambda p, z: True,
        spawn_condition=lambda floor, evt_mgr: not evt_mgr.is_event_triggered("nieta_veneno_entregado") and evt_mgr.is_event_triggered("nieta_descubierta"),
    ))
    
    # Estado "desaparecido" - Stranger desaparece tras la huida de la nieta
    # zone_type=None hace que no spawnee en ninguna zona.
    # Se llega cuando la nieta recibe el veneno y huye.
    # Ahora tiene transición a cadaver_envenenado (la nieta lo envenena).
    def check_cadaver_envenenado_transition(player, zone):
        """
        Verifica si el cadáver envenenado del Stranger debe aparecer.
        
        Requiere que hayan pasado 2+ runs desde que la nieta recibió el veneno.
        """
        desaparecido_at = event_manager.get_data("stranger_desaparecido_at_run", -1)
        if desaparecido_at < 0:
            return False
        return event_manager.run_count >= desaparecido_at + 2
    
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="desaparecido",
        zone_type=None,  # No aparece en ninguna zona
        transitions=[
            StateTransition(
                target_state="cadaver_envenenado",
                condition=check_cadaver_envenenado_transition,
                description="Cadáver del Stranger aparece 2 runs después de darle el veneno a la nieta"
            )
        ]
    ))
    
    # Estado "cadaver_envenenado" - Dungeon, cadáver del Stranger (ruta veneno)
    # Se llega por transición desde 'desaparecido' tras 2 runs.
    # El jugador encuentra el cadáver con recompensas.
    manager.register_npc_state("Stranger", NPCStateConfig(
        state_id="cadaver_envenenado",
        zone_type="dungeon",
        floor=2,  # Aparece en el piso 2
        position=None,  # Posición aleatoria
        char="%",
        color="dark_red",
        sprite_override="stranger_dead",
        dialog_tree_func=create_stranger_cadaver_envenenado_dialog,
        completed_dialog_func=create_stranger_cadaver_envenenado_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("stranger_cadaver_looted"),
        spawn_condition=lambda floor, evt_mgr: evt_mgr.is_event_triggered("nieta_veneno_entregado"),
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
