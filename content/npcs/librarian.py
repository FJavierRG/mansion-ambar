"""
Diálogos y configuración del NPC Bibliotecario y su perro Hermes.

DESBLOQUEO: El jugador compra su primera poción al mercader.
UBICACIÓN INICIAL: Plantas impares de la mazmorra, 50% de probabilidad (una vez por run).

LORE:
  El Bibliotecario es un anciano aventurero que ha perdido la noción del tiempo
  en los túneles. Su bien más preciado es Hermes, su perro, cuyo pelaje está
  compuesto por hilos metálicos afilados. Ambos recorren y trazan un mapa del
  laberinto infinito. Provienen de la mansión que se levanta sobre la entrada.

ESTADOS:
  dungeon_encounter → Dungeon (plantas impares, 50%, limitado a 1 por run)
      Primera conversación. Al completar el diálogo, desaparece y pasa al lobby.
  lobby_rest → Lobby (cerca de la hoguera)
      Segunda conversación. Habla sobre la mansión y los túneles.
      A partir de aquí, cada run completada desbloqueará un diálogo nuevo (futuro).

NOTAS:
  - Hermes (el perro) se registra como NPC independiente con spawn_near_npc.
  - Ambos sprites ya existen: librarian.png y dog.png.
  - El sistema de spawn pareado (spawn_near_npc) garantiza que Hermes
    aparezca siempre junto al Bibliotecario.
"""
import random
from roguelike.systems.text import DialogTree, DialogNode, DialogOption, InteractiveText
from roguelike.systems.music import music_manager


def _play_hermes_bark() -> None:
    """Reproduce el sonido de ladrido de Hermes."""
    music_manager.play_sound("Hermes_bark.mp3", volume=0.5)


# ============================================================================
# ESTADO: "dungeon_encounter" (Dungeon - Plantas impares, 50%, 1 por run)
# ============================================================================

def create_librarian_dungeon_dialog() -> DialogTree:
    """
    Crea el diálogo del Bibliotecario en su primer encuentro en la mazmorra.

    Returns:
        DialogTree con el diálogo completo del primer encuentro
    """
    tree = DialogTree(start_node="greeting")

    greeting_node = DialogNode(
        node_id="greeting",
        speaker="Bibliotecario",
        text="¿Qué has olido Hermes? ¿Un viajero?---"
             "Vaya, ¿quién eres tú? ¿Vienes... en son de paz?---"
             "Yo soy, o solía ser, el bibliotecario. Ahora soy solo un vagabundo, un aventurero.\n"
             "Este es Hermes, mi perro. Te aconsejo que no lo toques",
        options=[
            DialogOption("Continuar", next_node="hermes_bark")
        ]
    )
    tree.add_node(greeting_node)

    hermes_bark_node = DialogNode(
        node_id="hermes_bark",
        speaker="Hermes",
        text="*wof wof*",
        options=[
            DialogOption("Continuar", next_node="explanation")
        ],
        on_enter=_play_hermes_bark
    )
    tree.add_node(hermes_bark_node)

    explanation_node = DialogNode(
        node_id="explanation",
        speaker="Bibliotecario",
        text="Su pelaje está compuesto por cientos de hilos metálicos, "
             "afilados como obsidiana.\n"
             "Solo yo puedo acariciarlo sin cortarme. "
             "Y a ti ¿Qué te trae por aquí?---"
             "hmmm, ya veo. No me sorprende. Estos túneles son un enigma.\n"
             "Muchos han aparecido como tú en el pasado sin recordar nada, "
             "ni comprender.",
        options=[
            DialogOption("Continuar", next_node="farewell")
        ]
    )
    tree.add_node(explanation_node)

    def on_dungeon_encounter_complete(player, zone):
        """Activa el evento cuando se completa el primer encuentro."""
        from roguelike.systems.events import event_manager
        if not event_manager.is_event_triggered("librarian_dungeon_met"):
            event_manager.trigger_event(
                "librarian_dungeon_met", player, zone, skip_conditions=True
            )

    farewell_node = DialogNode(
        node_id="farewell",
        speaker="Bibliotecario",
        text="¿Sabes qué? Llevo mucho tiempo andando, estoy cansado.\n"
             "Creo que puede que suba a la entrada y descanse allí un poco. "
             "Podremos hablar",
        options=[
            DialogOption("Continuar", next_node="farewell_bark")
        ]
    )
    tree.add_node(farewell_node)

    farewell_bark_node = DialogNode(
        node_id="farewell_bark",
        speaker="Bibliotecario",
        text="¿Vamos chico?",
        options=[
            DialogOption("Continuar", next_node="farewell_end")
        ]
    )
    tree.add_node(farewell_bark_node)

    farewell_end_node = DialogNode(
        node_id="farewell_end",
        speaker="Hermes",
        text="*wof wof*",
        options=[
            DialogOption("Continuar", next_node=None, action=on_dungeon_encounter_complete)
        ],
        on_enter=_play_hermes_bark
    )
    tree.add_node(farewell_end_node)

    return tree


# ============================================================================
# ESTADO: "lobby_rest" (Lobby - Cerca de la hoguera)
# ============================================================================

def create_librarian_lobby_dialog() -> DialogTree:
    """
    Crea el diálogo del Bibliotecario en el lobby (segunda conversación).

    Returns:
        DialogTree con el diálogo completo del lobby
    """
    tree = DialogTree(start_node="greeting")

    greeting_node = DialogNode(
        node_id="greeting",
        speaker="Bibliotecario",
        text="Hola aventurero",
        options=[
            DialogOption("Continuar", next_node="hermes_bark")
        ]
    )
    tree.add_node(greeting_node)

    hermes_bark_node = DialogNode(
        node_id="hermes_bark",
        speaker="Hermes",
        text="*wof wof*",
        options=[
            DialogOption("Continuar", next_node="nostalgia")
        ],
        on_enter=_play_hermes_bark
    )
    tree.add_node(hermes_bark_node)

    nostalgia_node = DialogNode(
        node_id="nostalgia",
        speaker="Bibliotecario",
        text="Hacía mucho que Hermes y yo no pasábamos por aquí. "
             "Apenas descansamos ya fuera de los túneles.\n"
             "Nos hemos acostumbrado a la humedad y la oscuridad de esos pasillos.---"
             "Comencé mi viaje con la intención de trazar un mapa y comprender "
             "qué es este lugar.\n"
             "Allí arriba la mayoría lo desconocen, ignoran las pesadillas que "
             "se ocultan bajo el suelo",
        options=[
            DialogOption("Continuar", next_node="mansion")
        ]
    )
    tree.add_node(nostalgia_node)

    def on_lobby_dialog_complete(player, zone):
        """Activa el evento cuando se completa el diálogo del lobby."""
        from roguelike.systems.events import event_manager
        if not event_manager.is_event_triggered("librarian_lobby_dialog_completed"):
            event_manager.trigger_event(
                "librarian_lobby_dialog_completed", player, zone, skip_conditions=True
            )

    mansion_node = DialogNode(
        node_id="mansion",
        speaker="Bibliotecario",
        text="Oh, disculpa, claro. No sabes nada de la mansión. Verás yo vengo de arriba. "
             "Sobre esta sala se levanta un edificio colosal, infinito, habitado por "
             "artistas, científicos y pensadores.",
        options=[
            DialogOption("Continuar", next_node="farewell")
        ]
    )
    tree.add_node(mansion_node)

    farewell_bark_node = DialogNode(
        node_id="farewell",
        speaker="Hermes",
        text="*wof wof*",
        options=[
            DialogOption("Continuar", next_node="farewell_end")
        ],
        on_enter=_play_hermes_bark
    )
    tree.add_node(farewell_bark_node)

    farewell_end_node = DialogNode(
        node_id="farewell_end",
        speaker="Bibliotecario",
        text="Si, estamos cansados amigo. Vamos a necesitar descansar un poco. "
             "La próxima vez que te pases por aquí hablaremos un poco más",
        options=[
            DialogOption("Hasta luego", next_node=None, action=on_lobby_dialog_complete)
        ]
    )
    tree.add_node(farewell_end_node)

    return tree


def create_librarian_lobby_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'lobby_rest' ya fue completado."""
    return InteractiveText.create_simple_text(
        "Estamos descansando un poco. La próxima vez que te pases hablaremos un poco más.",
        title="Bibliotecario",
        auto_close=False
    )


# ============================================================================
# DIÁLOGO DEL PERRO HERMES
# ============================================================================

def create_hermes_dialog() -> DialogTree:
    """Diálogo simple de Hermes cuando lo tocas."""
    tree = DialogTree(start_node="bark")

    bark_node = DialogNode(
        node_id="bark",
        speaker="Hermes",
        text="*wof wof*",
        options=[
            DialogOption("Buen chico", next_node=None)
        ],
        on_enter=_play_hermes_bark
    )
    tree.add_node(bark_node)

    return tree


def create_hermes_completed() -> DialogTree:
    """Diálogo corto de Hermes (con sonido de ladrido)."""
    tree = DialogTree(start_node="bark")

    bark_node = DialogNode(
        node_id="bark",
        speaker="Hermes",
        text="*wof wof*",
        options=[
            DialogOption("Buen chico", next_node=None)
        ],
        on_enter=_play_hermes_bark
    )
    tree.add_node(bark_node)

    return tree


# ============================================================================
# CONDICIONES DE SPAWN
# ============================================================================

# Flag de desarrollo: forzar spawn al 100% (se activa con comando dev "librarian")
_dev_force_spawn = False

def _librarian_dungeon_spawn_condition(floor, event_manager) -> bool:
    """
    Determina si el Bibliotecario debe aparecer en esta planta.

    Condiciones (TODAS deben cumplirse):
      1. El jugador compró la primera poción al mercader
      2. No ha sido encontrado aún (librarian_dungeon_met no triggered)
      3. La planta es impar (1, 3, 5, 7, 9)
      4. 50% de probabilidad (o 100% si _dev_force_spawn está activo)

    Args:
        floor: Número de planta actual
        event_manager: Gestor de eventos

    Returns:
        True si el Bibliotecario debe spawnear
    """
    # 1. Requiere haber comprado la primera poción
    if not event_manager.is_event_triggered("merchant_first_potion_bought"):
        return False

    # 2. No debe haber sido encontrado ya
    if event_manager.is_event_triggered("librarian_dungeon_met"):
        return False

    # 3. Solo en plantas impares
    if floor is None or floor % 2 == 0:
        return False

    # 4. 50% de probabilidad (100% si dev force activo)
    if _dev_force_spawn:
        return True
    return random.random() < 0.5


def _hermes_dungeon_spawn_condition(floor, event_manager) -> bool:
    """
    Condición de spawn de Hermes en dungeon.
    
    NO incluye la tirada de probabilidad (random). La decisión aleatoria
    la toma solo el Bibliotecario. Hermes depende de spawn_near_npc para
    aparecer junto a él; si el Bibliotecario no spawneó, Hermes tampoco.
    """
    # 1. Requiere haber comprado la primera poción
    if not event_manager.is_event_triggered("merchant_first_potion_bought"):
        return False

    # 2. No debe haber sido encontrado ya
    if event_manager.is_event_triggered("librarian_dungeon_met"):
        return False

    # 3. Solo en plantas impares
    if floor is None or floor % 2 == 0:
        return False

    # Sin tirada de probabilidad: Hermes depende del spawn del Bibliotecario
    return True


# ============================================================================
# REGISTRO DE ESTADOS DEL NPC
# ============================================================================

def register_npc_states(manager) -> None:
    """
    Registra todos los estados del Bibliotecario y Hermes en el sistema FSM.

    Esta función es llamada automáticamente por el sistema de auto-discovery.

    NPCs registrados:
      - Bibliotecario: NPC principal con diálogos de lore
      - Hermes: perro compañero, siempre junto al Bibliotecario

    Args:
        manager: Instancia de NPCStateManager
    """
    from roguelike.systems.npc_states import NPCStateConfig, StateTransition
    from roguelike.systems.events import event_manager

    # ──────────────────────────────────────────────────────────────
    # BIBLIOTECARIO
    # ──────────────────────────────────────────────────────────────

    # Estado "dungeon_encounter" - Dungeon, plantas impares, 50%, primera vez
    manager.register_npc_state("Bibliotecario", NPCStateConfig(
        state_id="dungeon_encounter",
        zone_type="dungeon",
        floor=None,  # Cualquier planta impar (filtrado por spawn_condition)
        position=None,  # Posición aleatoria
        char="B",
        color="white",
        blocks=True,
        dialog_tree_func=create_librarian_dungeon_dialog,
        completion_condition=lambda p, z: event_manager.is_event_triggered("librarian_dungeon_met"),
        spawn_condition=_librarian_dungeon_spawn_condition,
        transitions=[
            StateTransition(
                target_state="lobby_rest",
                condition=lambda p, z: event_manager.is_event_triggered("librarian_dungeon_met"),
                description="Después de hablar con el Bibliotecario en la mazmorra"
            )
        ]
    ))

    # Estado "lobby_rest" - Lobby, cerca de la hoguera
    manager.register_npc_state("Bibliotecario", NPCStateConfig(
        state_id="lobby_rest",
        zone_type="lobby",
        position=(32, 14),  # Cerca de la hoguera (Comerciante Errante en 36,12; hoguera en 34,12)
        char="B",
        color="white",
        blocks=True,
        dialog_tree_func=create_librarian_lobby_dialog,
        completed_dialog_func=create_librarian_lobby_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("librarian_lobby_dialog_completed"),
        # Futuro: transiciones a nuevos diálogos por run completada
    ))

    # ──────────────────────────────────────────────────────────────
    # HERMES (perro del Bibliotecario)
    # ──────────────────────────────────────────────────────────────

    # Estado "with_librarian_dungeon" - Dungeon, junto al Bibliotecario
    manager.register_npc_state("Hermes", NPCStateConfig(
        state_id="with_librarian_dungeon",
        zone_type="dungeon",
        floor=None,  # Misma planta que el Bibliotecario
        position=None,  # Se calcula con spawn_near_npc
        char="d",
        color="white",
        blocks=False,  # El perro no bloquea el paso
        spawn_near_npc="Bibliotecario",  # Siempre junto al Bibliotecario
        dialog_tree_func=create_hermes_dialog,
        completed_dialog_func=create_hermes_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("librarian_dungeon_met"),
        spawn_condition=_hermes_dungeon_spawn_condition,
        transitions=[
            StateTransition(
                target_state="with_librarian_lobby",
                condition=lambda p, z: event_manager.is_event_triggered("librarian_dungeon_met"),
                description="Sigue al Bibliotecario al lobby"
            )
        ]
    ))

    # Estado "with_librarian_lobby" - Lobby, junto al Bibliotecario
    manager.register_npc_state("Hermes", NPCStateConfig(
        state_id="with_librarian_lobby",
        zone_type="lobby",
        position=None,  # Se calcula con spawn_near_npc
        char="d",
        color="white",
        blocks=False,
        spawn_near_npc="Bibliotecario",  # Siempre junto al Bibliotecario
        dialog_tree_func=create_hermes_dialog,
        completed_dialog_func=create_hermes_completed,
        completion_condition=None,  # Siempre interactivo
    ))
