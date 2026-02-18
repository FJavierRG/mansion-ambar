"""
Sistema de estados de NPCs - Máquina de Estados Finitos (FSM).
Sistema profesional para gestionar estados de NPCs con transiciones, condiciones y diálogos condicionales.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional, Tuple, Callable, Any, List
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..world.zone import Zone
    from ..entities.entity import Entity
    from ..entities.player import Player


class StateCompletion(Enum):
    """Estado de completitud de un estado de NPC."""
    NOT_STARTED = "not_started"  # Estado no iniciado
    IN_PROGRESS = "in_progress"   # Estado en progreso (diálogo activo)
    COMPLETED = "completed"       # Estado completado (muestra diálogo corto)
    LOCKED = "locked"             # Estado bloqueado (no disponible)


@dataclass
class StateTransition:
    """
    Transición entre estados.
    
    Define cuándo y cómo un NPC cambia de un estado a otro.
    
    Attributes:
        target_state: ID del estado destino
        condition: Función que verifica si se puede transicionar (player, zone) -> bool
        description: Descripción de la condición (para debug)
    """
    target_state: str
    condition: Callable[[Player, Zone], bool]
    description: str = ""


@dataclass
class NPCStateConfig:
    """
    Configuración completa de un estado de NPC.
    
    Define todo lo necesario para que un NPC esté en un estado específico.
    
    Attributes:
        state_id: ID único del estado
        zone_type: Tipo de zona ("lobby", "dungeon", None = cualquier)
        floor: Piso específico si es mazmorra (None = cualquier, requiere spawn_condition)
        position: Posición (x, y) donde debe estar
        dialog_tree_func: Función que retorna el DialogTree completo para este estado
        completed_dialog_func: Función que retorna diálogo corto cuando el estado está completado (None = usar el mismo)
        transitions: Lista de transiciones posibles desde este estado
        completion_condition: Función que verifica si el estado está completado (player, zone) -> bool
        spawn_condition: Función que verifica si el estado debe spawnearse (floor, event_manager) -> bool
                         Solo necesario si floor=None. Si no se proporciona y floor=None, no se spawnea.
    """
    state_id: str
    zone_type: Optional[str] = None
    floor: Optional[int] = None
    position: Optional[Tuple[int, int]] = None
    char: str = "?"  # Carácter ASCII del NPC (fallback si no hay sprite)
    color: str = "white"  # Color del NPC (fallback si no hay sprite)
    dialog_tree_func: Optional[Callable[[], Any]] = None
    completed_dialog_func: Optional[Callable[[], Any]] = None
    transitions: List[StateTransition] = field(default_factory=list)
    completion_condition: Optional[Callable[[Player, Zone], bool]] = None
    spawn_condition: Optional[Callable[[int, Any], bool]] = None  # (floor, event_manager) -> bool


class NPCStateManager:
    """
    Gestor de estados de NPCs con sistema FSM completo.
    
    Maneja estados, transiciones, completitud y diálogos condicionales.
    """
    
    def __init__(self):
        """Inicializa el gestor de estados."""
        # npc_name -> Dict[state_id -> NPCStateConfig]
        self.npc_states: Dict[str, Dict[str, NPCStateConfig]] = {}
        # npc_name -> state_id actual
        self.npc_current_states: Dict[str, str] = {}
        # npc_name -> Dict[state_id -> StateCompletion]
        self.npc_state_completion: Dict[str, Dict[str, StateCompletion]] = {}
        self._register_default_states()
    
    def register_npc_state(self, npc_name: str, state_config: NPCStateConfig) -> None:
        """
        Registra un estado para un NPC.
        
        Args:
            npc_name: Nombre del NPC
            state_config: Configuración del estado
        """
        if npc_name not in self.npc_states:
            self.npc_states[npc_name] = {}
            self.npc_state_completion[npc_name] = {}
        self.npc_states[npc_name][state_config.state_id] = state_config
        self.npc_state_completion[npc_name][state_config.state_id] = StateCompletion.NOT_STARTED
    
    def normalize_npc_name(self, npc_name: str) -> str:
        """Normaliza el nombre del NPC para búsqueda case-insensitive."""
        # Buscar el nombre exacto primero
        if npc_name in self.npc_states:
            return npc_name
        # Buscar case-insensitive
        for key in self.npc_states.keys():
            if key.lower() == npc_name.lower():
                return key
        # Si no se encuentra, retornar el original
        return npc_name
    
    def get_state_config(self, npc_name: str, state_id: str) -> Optional[NPCStateConfig]:
        """Obtiene la configuración de un estado."""
        normalized_name = self.normalize_npc_name(npc_name)
        if normalized_name not in self.npc_states:
            return None
        return self.npc_states[normalized_name].get(state_id)
    
    def get_npc_states(self, npc_name: str) -> Dict[str, NPCStateConfig]:
        """
        Obtiene todos los estados de un NPC.
        
        Args:
            npc_name: Nombre del NPC
            
        Returns:
            Diccionario de estados (state_id -> NPCStateConfig)
        """
        normalized_name = self.normalize_npc_name(npc_name)
        return self.npc_states.get(normalized_name, {})
    
    def get_all_npc_states(self, npc_name: str) -> Dict[str, NPCStateConfig]:
        """
        Obtiene todos los estados de un NPC (alias de get_npc_states para compatibilidad).
        
        Args:
            npc_name: Nombre del NPC
            
        Returns:
            Diccionario de estados (state_id -> NPCStateConfig)
        """
        return self.get_npc_states(npc_name)
    
    def get_current_state(self, npc_name: str) -> Optional[str]:
        """Obtiene el estado actual de un NPC."""
        normalized_name = self.normalize_npc_name(npc_name)
        return self.npc_current_states.get(normalized_name)
    
    def set_current_state(self, npc_name: str, state_id: str) -> None:
        """Establece el estado actual de un NPC."""
        normalized_name = self.normalize_npc_name(npc_name)
        self.npc_current_states[normalized_name] = state_id
        if normalized_name not in self.npc_state_completion:
            self.npc_state_completion[normalized_name] = {}
        if state_id not in self.npc_state_completion[normalized_name]:
            self.npc_state_completion[normalized_name][state_id] = StateCompletion.NOT_STARTED
    
    def get_state_completion(self, npc_name: str, state_id: str) -> StateCompletion:
        """Obtiene el estado de completitud de un estado."""
        normalized_name = self.normalize_npc_name(npc_name)
        if normalized_name not in self.npc_state_completion:
            return StateCompletion.NOT_STARTED
        return self.npc_state_completion[normalized_name].get(state_id, StateCompletion.NOT_STARTED)
    
    def set_state_completion(self, npc_name: str, state_id: str, completion: StateCompletion) -> None:
        """Establece el estado de completitud de un estado."""
        normalized_name = self.normalize_npc_name(npc_name)
        if normalized_name not in self.npc_state_completion:
            self.npc_state_completion[normalized_name] = {}
        self.npc_state_completion[normalized_name][state_id] = completion
    
    def check_and_transition(self, npc_name: str, player: Player, zone: Zone, only_cross_zone: bool = False) -> Optional[str]:
        """
        Verifica transiciones y cambia de estado si es necesario.
        
        Args:
            npc_name: Nombre del NPC
            player: Jugador
            zone: Zona actual
            only_cross_zone: Si True, solo procesa transiciones donde el estado destino
                             está en una zona DIFERENTE al estado actual. Esto permite que
                             las transiciones de misma zona se difieran al momento de spawn
                             (próxima visita a la zona).
        
        Returns:
            ID del nuevo estado si hubo transición, None si no
        """
        normalized_name = self.normalize_npc_name(npc_name)
        current_state_id = self.get_current_state(normalized_name)
        if not current_state_id:
            return None
        
        state_config = self.get_state_config(normalized_name, current_state_id)
        if not state_config:
            return None
        
        # Verificar cada transición posible
        for transition in state_config.transitions:
            if transition.condition(player, zone):
                # Si only_cross_zone, saltar transiciones donde el destino está en la misma zona
                if only_cross_zone:
                    target_config = self.get_state_config(normalized_name, transition.target_state)
                    if target_config and target_config.zone_type == state_config.zone_type:
                        continue  # Misma zona → diferir al spawn
                
                # Transicionar al nuevo estado
                self.set_current_state(normalized_name, transition.target_state)
                # Marcar el estado anterior como completado
                self.set_state_completion(normalized_name, current_state_id, StateCompletion.COMPLETED)
                # Marcar el nuevo estado como en progreso
                self.set_state_completion(normalized_name, transition.target_state, StateCompletion.IN_PROGRESS)
                return transition.target_state
        
        return None
    
    def get_dialog_for_state(self, npc_name: str, state_id: str, player: Optional[Player] = None, zone: Optional[Zone] = None) -> Optional[Any]:  # noqa: ARG002
        """
        Obtiene el diálogo apropiado para un estado.
        
        Si el estado está completado, retorna el diálogo corto.
        Si no, retorna el diálogo completo.
        
        Args:
            npc_name: Nombre del NPC
            state_id: ID del estado
            player: (No usado, mantenido por compatibilidad)
            zone: (No usado, mantenido por compatibilidad)
        
        Returns:
            DialogTree o TextContent según corresponda
        """
        normalized_name = self.normalize_npc_name(npc_name)
        state_config = self.get_state_config(normalized_name, state_id)
        if not state_config:
            return None
        
        completion = self.get_state_completion(normalized_name, state_id)
        
        # Si está completado y hay diálogo corto, usarlo
        if completion == StateCompletion.COMPLETED and state_config.completed_dialog_func:
            return state_config.completed_dialog_func()
        
        # Si no, usar diálogo completo
        if state_config.dialog_tree_func:
            return state_config.dialog_tree_func()
        
        # Fallback: si solo hay completed_dialog_func (ej: estado que solo tiene diálogo corto)
        if state_config.completed_dialog_func:
            return state_config.completed_dialog_func()
        
        return None
    
    def determine_target_state(self, npc_name: str, zone_type: str, player: Optional[Player] = None, zone: Optional[Zone] = None) -> Optional[str]:  # noqa: ARG002
        """
        Determina qué estado debe tener un NPC según el FSM.
        
        Delegación directa a _get_spawn_state. Mantenido por compatibilidad.
        
        Args:
            npc_name: Nombre del NPC
            zone_type: Tipo de zona ("lobby" o "dungeon")
            player: (No usado, mantenido por compatibilidad)
            zone: (No usado, mantenido por compatibilidad)
            
        Returns:
            ID del estado objetivo o None si no hay estado válido
        """
        return self._get_spawn_state(npc_name, zone_type)
    
    def create_npc_entity(
        self,
        npc_name: str,
        state_id: str,
        x: int,
        y: int,
        zone: Zone
    ) -> Optional[Entity]:
        """
        Crea una entidad NPC usando el sistema FSM.
        
        Esta es la función centralizada para crear NPCs. Todas las zonas
        (lobby, dungeon) deben usar esta función para crear NPCs.
        
        Args:
            npc_name: Nombre del NPC (debe estar registrado en el FSM)
            state_id: ID del estado en el que debe estar el NPC
            x: Posición X
            y: Posición Y
            zone: Zona donde se crea el NPC
            
        Returns:
            La entidad creada o None si hay error
        """
        from ..entities.entity import Entity
        from ..systems.text import InteractiveText
        from ..ui.sprite_manager import sprite_manager
        
        # Verificar que el NPC está registrado
        normalized_name = self.normalize_npc_name(npc_name)
        if normalized_name not in self.npc_states:
            print(f"[WARNING] NPC '{npc_name}' no está registrado en el FSM")
            return None
        
        # Verificar que el estado existe
        state_config = self.get_state_config(normalized_name, state_id)
        if not state_config:
            print(f"[WARNING] Estado '{state_id}' no existe para NPC '{npc_name}'")
            return None
        
        # Crear la entidad (usar char y color del estado si están definidos)
        npc = Entity(
            x=x,
            y=y,
            char=state_config.char,
            name=npc_name,
            color=state_config.color,
            blocks=True,
            dungeon=zone
        )
        
        # Asignar sprite si existe
        sprite = sprite_manager.get_creature_sprite(normalized_name.lower())
        if sprite:
            npc.sprite = sprite
        
        # Establecer estado en el FSM
        self.set_current_state(normalized_name, state_id)
        
        # Verificar completitud del estado
        completion = self.get_state_completion(normalized_name, state_id)
        if completion == StateCompletion.NOT_STARTED:
            self.set_state_completion(normalized_name, state_id, StateCompletion.IN_PROGRESS)
        
        # Obtener diálogo del estado (no requiere player/zone)
        dialog = self.get_dialog_for_state(normalized_name, state_id)
        if dialog:
            if isinstance(dialog, InteractiveText):
                npc.interactive_text = dialog
            else:
                # Es un DialogTree
                dialog_tree = dialog
                npc.interactive_text = InteractiveText.create_dialog(dialog_tree, interaction_key="espacio")
        else:
            # Fallback: usar diálogo simple
            npc.interactive_text = InteractiveText.create_simple_text(
                f"[{npc_name}]",
                title=npc_name,
                auto_close=False
            )
        
        # El NPC no tiene componente de combate
        npc.fighter = None  # type: ignore
        
        return npc
    
    def _get_random_spawn_position(self, zone: Zone, state_config: NPCStateConfig) -> Optional[Tuple[int, int]]:  # noqa: ARG002
        """
        Obtiene una posición aleatoria válida para spawnear un NPC en una zona.
        
        Args:
            zone: Zona donde spawnear
            state_config: Configuración del estado
            
        Returns:
            Tupla (x, y) con la posición o None si no se encuentra
        """
        import random
        
        # Para dungeon: usar habitaciones
        if zone.zone_type == "dungeon" and hasattr(zone, 'rooms') and zone.rooms:
            # Elegir habitación (preferir no la primera si hay varias)
            if len(zone.rooms) > 1:
                spawn_room = random.choice(zone.rooms[1:])
            else:
                spawn_room = zone.rooms[0]
            
            # Obtener posición aleatoria en la habitación
            if hasattr(zone, '_get_random_room_position'):
                return zone._get_random_room_position(spawn_room)
            else:
                # Fallback: posición aleatoria en la habitación
                room = spawn_room
                x = random.randint(room.x1 + 1, room.x2 - 1)
                y = random.randint(room.y1 + 1, room.y2 - 1)
                return (x, y)
        
        # Para lobby u otras zonas: buscar posiciones walkable
        walkable_positions = []
        for tx in range(zone.width):
            for ty in range(zone.height):
                if zone.is_walkable(tx, ty):
                    walkable_positions.append((tx, ty))
        
        if not walkable_positions:
            return None
        
        return random.choice(walkable_positions)
    
    def spawn_npcs_for_zone(
        self,
        zone: Zone
    ) -> List[Entity]:
        """
        Spawnea NPCs automáticamente para una zona basándose en el FSM.
        
        Este es el ÚNICO método que debe usarse para spawnear NPCs.
        No requiere player — el spawn es completamente independiente del jugador.
        
        Algoritmo simplificado:
        1. Si el NPC ya existe en la zona → skip
        2. Determinar qué estado mostrar (_get_spawn_state)
        3. Determinar posición y crear la entidad
        
        La lógica de transiciones NO se evalúa aquí — solo al interactuar.
        La completion_condition NO se evalúa aquí — solo para elegir diálogo.
        
        Args:
            zone: Zona donde spawnear (Lobby o Dungeon)
            
        Returns:
            Lista de entidades NPCs spawneadas
        """
        spawned_npcs = []
        
        zone_type = zone.zone_type  # "lobby" o "dungeon"
        floor = getattr(zone, 'floor', None) if zone_type == "dungeon" else None
        
        for npc_name in self.npc_states:
            # 1. Skip si el NPC ya existe en esta zona
            if any(e.name == npc_name for e in zone.entities):
                continue
            
            # 2. Determinar qué estado spawnear
            target_state = self._get_spawn_state(npc_name, zone_type, floor)
            if not target_state:
                continue
            
            state_config = self.get_state_config(npc_name, target_state)
            if not state_config:
                continue
            
            # 3. Determinar posición
            if state_config.position:
                pos = state_config.position
            else:
                pos = self._get_random_spawn_position(zone, state_config)
                if not pos:
                    continue
            
            # 4. Verificar que no haya nada bloqueando
            if zone.get_blocking_entity_at(pos[0], pos[1]):
                found_position = False
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        test_x, test_y = pos[0] + dx, pos[1] + dy
                        if (zone.is_walkable(test_x, test_y) and 
                            not zone.get_blocking_entity_at(test_x, test_y)):
                            pos = (test_x, test_y)
                            found_position = True
                            break
                    if found_position:
                        break
                if not found_position:
                    continue
            
            # 5. Crear NPC
            npc = self.create_npc_entity(
                npc_name=npc_name,
                state_id=target_state,
                x=pos[0],
                y=pos[1],
                zone=zone
            )
            
            if npc:
                spawned_npcs.append(npc)
                zone.entities.append(npc)
        
        return spawned_npcs
    
    def _get_spawn_state(self, npc_name: str, zone_type: str, floor: Optional[int] = None) -> Optional[str]:
        """
        Determina qué estado debe tener un NPC al spawnearse en una zona.
        
        Reglas:
        1. Si hay current_state y está COMPLETED → intentar avanzar via transiciones
           (esto maneja tanto transiciones misma-zona diferidas como cross-zona)
        2. Si hay current_state y es para esta zona → usarlo (incluso si COMPLETED sin transición)
        3. Si hay current_state pero es para otra zona → no spawnear
        4. Si no hay current_state → buscar estado inicial válido para esta zona
        
        IMPORTANTE: Este método puede modificar el estado actual del NPC si detecta
        que una transición diferida debe ejecutarse (side effect intencional).
        
        Args:
            npc_name: Nombre del NPC
            zone_type: Tipo de zona ("lobby" o "dungeon")
            floor: Piso actual (solo para dungeon)
            
        Returns:
            state_id del estado a spawnear, o None
        """
        from ..systems.events import event_manager
        
        normalized_name = self.normalize_npc_name(npc_name)
        states_dict = self.npc_states.get(normalized_name, {})
        if not states_dict:
            return None
        
        current_state = self.get_current_state(normalized_name)
        
        # CASO 1: Hay un estado actual
        if current_state:
            current_config = self.get_state_config(normalized_name, current_state)
            if current_config:
                completion = self.get_state_completion(normalized_name, current_state)
                
                # Si el estado está COMPLETED, intentar avanzar via transiciones
                # Esto maneja transiciones diferidas (misma zona) y cross-zona
                if completion == StateCompletion.COMPLETED and current_config.transitions:
                    for transition in current_config.transitions:
                        target_config = self.get_state_config(normalized_name, transition.target_state)
                        if not target_config or target_config.zone_type != zone_type:
                            continue
                        
                        # Para dungeon, verificar piso del estado destino
                        if zone_type == "dungeon":
                            if not self._floor_matches_for_spawn(target_config, floor, event_manager):
                                continue
                        
                        # Evaluar condición de transición (sin player/zone, usa event_manager)
                        try:
                            if transition.condition(None, None):  # type: ignore
                                # Transición diferida: ejecutar ahora
                                self.set_current_state(normalized_name, transition.target_state)
                                self.set_state_completion(normalized_name, transition.target_state, StateCompletion.IN_PROGRESS)
                                return transition.target_state
                        except (TypeError, AttributeError):
                            pass
                
                # Sin transición válida: usar el estado actual si es para esta zona
                if current_config.zone_type == zone_type:
                    # Para dungeon, verificar piso
                    if zone_type == "dungeon":
                        if not self._floor_matches_for_spawn(current_config, floor, event_manager):
                            return None
                    return current_state
                else:
                    # Estado actual es para otra zona → no spawnear aquí
                    return None
        
        # CASO 2: No hay estado actual → buscar estado inicial para esta zona
        return self._find_initial_state_for_zone(normalized_name, zone_type, floor)
    
    def _floor_matches_for_spawn(self, config: NPCStateConfig, floor: Optional[int], evt_mgr: Any) -> bool:
        """
        Verifica si el piso coincide para spawn en dungeon.
        
        Args:
            config: Configuración del estado
            floor: Piso actual de la dungeon
            evt_mgr: Event manager para verificar spawn_condition
            
        Returns:
            True si el piso es válido para spawn
        """
        if config.floor is not None:
            # Piso específico: debe coincidir exactamente
            if config.floor != floor:
                return False
            # Si tiene spawn_condition adicional, verificarla
            if config.spawn_condition:
                return config.spawn_condition(floor, evt_mgr)
            return True
        else:
            # floor=None: requiere spawn_condition obligatoriamente
            if not config.spawn_condition:
                return False
            return config.spawn_condition(floor, evt_mgr)
    
    def _find_initial_state_for_zone(self, npc_name: str, zone_type: str, floor: Optional[int] = None) -> Optional[str]:
        """
        Busca el estado inicial válido para un NPC en una zona cuando no hay current_state.
        
        Un estado es "inicial" para una zona si:
        - Es de ese zone_type (y piso correcto para dungeon)
        - No tiene transiciones entrantes desde estados DE LA MISMA ZONA
        - Si tiene transiciones entrantes cross-zona, al menos una de esas 
          condiciones de transición se cumple (verificado via event_manager)
        - No está LOCKED
        
        Args:
            npc_name: Nombre del NPC
            zone_type: Tipo de zona
            floor: Piso actual (solo para dungeon)
            
        Returns:
            state_id del estado inicial, o None
        """
        from ..systems.events import event_manager
        
        states_dict = self.npc_states.get(npc_name, {})
        
        # Filtrar estados por zona
        zone_states = [
            (sid, cfg) for sid, cfg in states_dict.items()
            if cfg.zone_type == zone_type
        ]
        
        if not zone_states:
            return None
        
        for state_id, state_config in zone_states:
            # Para dungeon, verificar piso (incluye spawn_condition)
            if zone_type == "dungeon":
                if not self._floor_matches_for_spawn(state_config, floor, event_manager):
                    continue
            
            # Para zonas no-dungeon, verificar spawn_condition si existe
            # (esto permite filtrar estados que solo deben activarse programáticamente)
            if zone_type != "dungeon" and state_config.spawn_condition:
                if not state_config.spawn_condition(None, event_manager):
                    continue
            
            # Verificar si está LOCKED
            completion = self.get_state_completion(npc_name, state_id)
            if completion == StateCompletion.LOCKED:
                continue
            
            # Clasificar transiciones entrantes
            same_zone_incoming = []
            cross_zone_incoming = []
            
            for other_id, other_config in states_dict.items():
                for t in other_config.transitions:
                    if t.target_state == state_id:
                        if other_config.zone_type == zone_type:
                            same_zone_incoming.append((other_id, other_config, t))
                        else:
                            cross_zone_incoming.append((other_id, other_config, t))
            
            # Si tiene transiciones entrantes de la misma zona → no es estado inicial
            # (a menos que un predecesor de la misma zona esté COMPLETED)
            if same_zone_incoming:
                has_completed_same_zone_pred = any(
                    self.get_state_completion(npc_name, pred_id) == StateCompletion.COMPLETED
                    for pred_id, _, _ in same_zone_incoming
                )
                if not has_completed_same_zone_pred:
                    continue
            
            # Si tiene transiciones entrantes cross-zona, verificar condiciones
            # Las condiciones de transición solo usan event_manager, así que 
            # podemos evaluarlas con None como player/zone
            if cross_zone_incoming:
                cross_zone_valid = False
                for _pred_id, _pred_config, transition in cross_zone_incoming:
                    try:
                        if transition.condition(None, None):  # type: ignore
                            cross_zone_valid = True
                            break
                    except (TypeError, AttributeError):
                        # Si la condición necesita player/zone, no podemos evaluarla
                        pass
                
                if not cross_zone_valid:
                    continue
            
            # Este estado es válido como estado inicial
            return state_id
        
        return None
    
    def _register_default_states(self) -> None:
        """
        Registra los estados de todos los NPCs usando auto-discovery.
        
        El sistema busca automáticamente módulos en roguelike/content/npcs/
        que exporten una función register_npc_states(manager).
        """
        from ..content.npcs import register_all_npcs
        register_all_npcs(self)


# Instancia global del gestor de estados
npc_state_manager = NPCStateManager()
