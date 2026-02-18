"""
Registro de eventos del juego.
Aquí se definen todos los eventos persistentes del juego.
"""
from roguelike.systems.events import GameEvent, event_manager
from roguelike.systems.event_helpers import (
    condition_event_triggered,
    action_remove_entity_from_zone,
    action_add_entity_to_zone,
    EventCondition
)
from roguelike.world.lobby import Lobby
from roguelike.systems.npc_states import StateCompletion


def register_all_game_events() -> None:
    """
    Registra todos los eventos del juego.
    Esta función debe llamarse al iniciar el juego.
    """
    # Registrar evento del Stranger
    register_stranger_event()
    
    # Aquí puedes añadir más eventos
    pass


def register_stranger_event() -> None:
    """
    Registra el evento del Stranger que aparece en el nivel 5 y se mueve al lobby.
    """
    # Evento 1: Hablar con el Stranger en el piso 5
    event_stranger_met = GameEvent(
        event_id="stranger_floor5_met",
        name="Conociste al Stranger",
        description="Hablaste con el Stranger en el piso 5",
        persistent=True,
        auto_trigger=False  # Se activa manualmente al hablar
    )
    
    # No necesitamos condición porque se activa manualmente cuando hablamos con él
    # El evento se activa directamente desde _on_dialog_closed cuando el jugador habla con el Stranger
    
    # Acción: eliminar Stranger del piso 5
    event_stranger_met.actions.append(
        action_remove_entity_from_zone("Stranger", zone_type="dungeon")
    )
    
    # Evento 2: Primera conversación en el lobby (desbloquea armas y armaduras)
    event_stranger_lobby_weapons = GameEvent(
        event_id="stranger_lobby_weapons_unlocked",
        name="Stranger desbloquea armas y armaduras",
        description="El jugador habló con Stranger en el lobby por primera vez",
        persistent=True,
        auto_trigger=False  # Se activa manualmente al hablar
    )
    
    # Condición: El evento del piso 5 debe estar activado
    event_stranger_lobby_weapons.conditions.append(
        condition_event_triggered("stranger_floor5_met")
    )
    
    # Evento 4: Segunda conversación en el lobby (desbloquea pociones)
    event_stranger_lobby_potions = GameEvent(
        event_id="stranger_lobby_potions_unlocked",
        name="Stranger desbloquea pociones",
        description="El jugador habló con Stranger en el lobby por segunda vez",
        persistent=True,
        auto_trigger=False  # Se activa manualmente al hablar
    )
    
    # Condición: El evento de armas/armaduras debe estar activado
    event_stranger_lobby_potions.conditions.append(
        condition_event_triggered("stranger_lobby_weapons_unlocked")
    )
    
    # Evento 5: Jugador acepta ayudar al Stranger
    event_stranger_help_accepted = GameEvent(
        event_id="stranger_help_accepted",
        name="Stranger - Ayuda aceptada",
        description="El jugador aceptó ayudar al Stranger a encontrar a su nieta",
        persistent=True,
        auto_trigger=False  # Se activa manualmente desde el diálogo
    )
    
    # Evento 6: Habilitar spawneo de la nieta
    event_granddaughter_spawn = GameEvent(
        event_id="granddaughter_spawn_enabled",
        name="Spawneo de la nieta habilitado",
        description="La nieta del Stranger puede spawnear en las mazmorras",
        persistent=True,
        auto_trigger=False  # Se activa cuando acepta ayudar
    )
    
    # Evento 7: Encontrar a la nieta
    event_granddaughter_found = GameEvent(
        event_id="granddaughter_found",
        name="Nieta encontrada",
        description="El jugador encontró a la nieta del Stranger",
        persistent=True,
        auto_trigger=False  # Se activa manualmente al hablar con ella
    )
    
    # Evento 8: Misión capturar nieta iniciada (Opción 1)
    event_mision_capturar_nieta = GameEvent(
        event_id="mision_capturar_nieta_started",
        name="Misión: Capturar a la nieta",
        description="El jugador obligó a la nieta a subir al lobby",
        persistent=True,
        auto_trigger=False  # Se activa desde el diálogo
    )
    
    # Acción: Mover la niña al lobby cuando está obligada
    def create_lobby_nieta(x, y, zone):
        """Crea la niña en el lobby cuando está obligada."""
        from roguelike.entities.entity import Entity
        from roguelike.systems.text import InteractiveText
        from roguelike.systems.npc_states import npc_state_manager
        from roguelike.ui.sprite_manager import sprite_manager
        
        nieta = Entity(
            x=x,
            y=y,
            char="@",
            name="nieta",
            color="yellow",
            blocks=True,
            dungeon=zone
        )
        
        nieta.sprite = sprite_manager.get_creature_sprite("nieta")
        nieta.fighter = None  # type: ignore
        
        # Establecer estado
        npc_state_manager.set_current_state("nieta", "obligada")
        npc_state_manager.set_state_completion("nieta", "obligada", StateCompletion.IN_PROGRESS)
        
        # Obtener diálogo del estado
        dialog = npc_state_manager.get_dialog_for_state("nieta", "obligada")
        if dialog:
            if isinstance(dialog, InteractiveText):
                nieta.interactive_text = dialog
            else:
                dialog_tree = dialog
                nieta.interactive_text = InteractiveText.create_dialog(dialog_tree, interaction_key="espacio")
        
        return nieta
    
    event_nieta_obligada = GameEvent(
        event_id="nieta_obligada",
        name="Nieta obligada",
        description="La nieta fue obligada a subir al lobby",
        persistent=True,
        auto_trigger=False
    )
    
    # Acción: Eliminar niña de dungeon y crear en lobby
    event_nieta_obligada.actions.append(
        action_remove_entity_from_zone("nieta", zone_type="dungeon")
    )
    event_nieta_obligada.actions.append(
        action_add_entity_to_zone(
            create_lobby_nieta,
            zone_type="lobby",
            x=45,  # Cerca del Stranger pero separada
            y=20
        )
    )
    
    # Evento 9: Misión ayudar nieta iniciada (Opción 2)
    event_mision_nieta_ayudar = GameEvent(
        event_id="mision_nieta_ayudar_started",
        name="Misión: Ayudar a la nieta",
        description="El jugador decidió ayudar a la nieta a investigar al Stranger",
        persistent=True,
        auto_trigger=False  # Se activa desde el diálogo
    )
    
    # Evento 11: Nieta ayudando (estado)
    event_nieta_ayudando = GameEvent(
        event_id="nieta_ayudando",
        name="Nieta ayudando",
        description="La nieta está en modo ayuda, esperando en el piso 1",
        persistent=True,
        auto_trigger=False
    )
    
    # Acción: Eliminar niña de dungeon actual (se creará en piso 1 al generar)
    event_nieta_ayudando.actions.append(
        action_remove_entity_from_zone("nieta", zone_type="dungeon")
    )
    
    # Registrar eventos
    event_manager.register_event(event_stranger_met)
    event_manager.register_event(event_stranger_lobby_weapons)
    event_manager.register_event(event_stranger_lobby_potions)
    event_manager.register_event(event_stranger_help_accepted)
    event_manager.register_event(event_granddaughter_spawn)
    event_manager.register_event(event_granddaughter_found)
    event_manager.register_event(event_mision_capturar_nieta)
    event_manager.register_event(event_mision_nieta_ayudar)
    event_manager.register_event(event_nieta_obligada)
    event_manager.register_event(event_nieta_ayudando)


def register_npc_floor5_event() -> None:
    """
    Ejemplo: Registra el evento del NPC que se mueve del piso 5 al lobby.
    Este es solo un ejemplo de cómo crear eventos.
    """
    # Evento 1: Hablar con NPC en piso 5
    event_npc_met = GameEvent(
        event_id="npc_floor5_met",
        name="Conociste al Forastero",
        description="Hablaste con el misterioso forastero en el piso 5",
        persistent=True,
        auto_trigger=False  # Se activa manualmente
    )
    
    # Condición: estar en el piso 5 y tener el NPC ahí
    def check_npc_exists(player, zone):
        return (player.current_floor == 5 and 
                any(e.name == "Misterioso Forastero" for e in zone.entities))
    
    event_npc_met.conditions.append(
        EventCondition(check_npc_exists, "NPC existe en piso 5")
    )
    
    # Acción: eliminar NPC del piso 5
    event_npc_met.actions.append(
        action_remove_entity_from_zone("Misterioso Forastero", zone_type="dungeon")
    )
    
    # Evento 2: NPC aparece en el lobby
    event_npc_lobby = GameEvent(
        event_id="npc_lobby_appears",
        name="Forastero en el Lobby",
        description="El forastero aparece en el lobby",
        persistent=True,
        auto_trigger=True  # Se activa automáticamente
    )
    
    # Condición: evento anterior activado Y estar en el lobby
    event_npc_lobby.conditions.append(
        condition_event_triggered("npc_floor5_met")
    )
    
    def check_in_lobby(player, zone):
        return isinstance(zone, Lobby)
    
    event_npc_lobby.conditions.append(
        EventCondition(check_in_lobby, "Estar en el lobby")
    )
    
    # Condición: NPC no existe ya en el lobby
    def check_npc_not_in_lobby(player, zone):
        return not any(e.name == "Misterioso Forastero" for e in zone.entities)
    
    event_npc_lobby.conditions.append(
        EventCondition(check_npc_not_in_lobby, "NPC no está en lobby")
    )
    
    # Acción: añadir NPC al lobby (necesitarías crear la función create_lobby_npc)
    # event_npc_lobby.actions.append(
    #     action_add_entity_to_zone(create_lobby_npc, "lobby", x=40, y=20)
    # )
    
    # Registrar eventos
    event_manager.register_event(event_npc_met)
    event_manager.register_event(event_npc_lobby)
