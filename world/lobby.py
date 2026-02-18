"""
Clase Lobby - Zona inicial del juego donde el jugador puede prepararse.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, Tuple, Optional, Set
import random

from .zone import Zone
from .tile import Tile, TileType
from ..config import MAP_WIDTH, MAP_HEIGHT

if TYPE_CHECKING:
    from ..entities.entity import Entity
    from ..items.item import Item


class Lobby(Zone):
    """
    Zona de lobby - área inicial donde el jugador puede prepararse antes de entrar a la mazmorra.
    
    El lobby es una zona segura donde no hay enemigos, pero puede tener NPCs,
    tiendas, o puntos de entrada a diferentes áreas.
    
    Attributes:
        dungeon_entrance: Posición de la entrada a la mazmorra
    """
    
    def __init__(
        self,
        width: int = MAP_WIDTH,
        height: int = MAP_HEIGHT,
        zone_id: str = "lobby_main"
    ) -> None:
        """
        Inicializa el lobby.
        
        Args:
            width: Ancho del mapa
            height: Alto del mapa
            zone_id: Identificador único del lobby
        """
        super().__init__(width, height, zone_id, "lobby")
        self.dungeon_entrance: Optional[Tuple[int, int]] = None

        # Mantener compatibilidad con la interfaz de Dungeon
        self.stairs_down: Optional[Tuple[int, int]] = None
        self.stairs_up: Optional[Tuple[int, int]] = None
    
    def generate(self) -> Tuple[int, int]:
        """
        Genera el lobby con una estructura simple.
        
        El lobby tiene:
        - Una sala central grande
        - Una entrada a la mazmorra (escaleras hacia abajo)
        - Posiblemente NPCs o puntos de interés
        
        Returns:
            Posición inicial del jugador (centro del lobby)
        """
        # Primero, convertir todos los tiles a VOID (negro) en lugar de WALL
        for x in range(self.width):
            for y in range(self.height):
                self.tiles[x][y] = Tile(TileType.VOID)
        
        # Crear una sala grande en el centro
        center_x = self.width // 2
        center_y = self.height // 2
        room_width = min(30, self.width - 10)
        room_height = min(20, self.height - 10)
        
        room_x = center_x - room_width // 2
        room_y = center_y - room_height // 2
        
        # Crear las paredes alrededor de la sala
        # Pared superior e inferior
        for x in range(room_x - 1, room_x + room_width + 1):
            if 0 <= x < self.width:
                # Pared superior
                if 0 <= room_y - 1 < self.height:
                    self.tiles[x][room_y - 1] = Tile(TileType.WALL)
                # Pared inferior
                if 0 <= room_y + room_height < self.height:
                    self.tiles[x][room_y + room_height] = Tile(TileType.WALL)
        
        # Paredes laterales (izquierda y derecha)
        for y in range(room_y - 1, room_y + room_height + 1):
            if 0 <= y < self.height:
                # Pared izquierda
                if 0 <= room_x - 1 < self.width:
                    self.tiles[room_x - 1][y] = Tile(TileType.WALL)
                # Pared derecha
                if 0 <= room_x + room_width < self.width:
                    self.tiles[room_x + room_width][y] = Tile(TileType.WALL)
        
        # Crear el suelo de la sala
        for x in range(room_x, room_x + room_width):
            for y in range(room_y, room_y + room_height):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.tiles[x][y] = Tile(TileType.FLOOR)
        
        # Colocar entrada a la mazmorra (escaleras hacia abajo)
        # Misma X del centro, pero Y arriba pegada al muro superior de la sala
        entrance_x = center_x
        entrance_y = room_y + 1  # Una posición dentro de la sala, cerca del muro superior
        self.tiles[entrance_x][entrance_y] = Tile(TileType.STAIRS_DOWN)
        self.dungeon_entrance = (entrance_x, entrance_y)
        self.stairs_down = self.dungeon_entrance
        
        # Posición inicial del jugador en el lado opuesto (abajo, cerca del muro inferior)
        start_x = center_x
        start_y = room_y + room_height - 2  # Cerca del muro inferior de la sala
        
        # Asegurar que la posición inicial es transitable
        if not self.is_walkable(start_x, start_y):
            start_x = center_x + 1
            start_y = room_y + room_height - 2
        
        # Spawnear NPCs basándose en configuración de estados
        self.spawn_npcs_from_states()
        
        # En el lobby, todos los tiles deben estar visibles desde el inicio
        # (sin niebla de guerra)
        self._reveal_all_tiles()
        
        return (start_x, start_y)
    
    def spawn_npcs_from_states(self) -> None:
        """
        Spawnea NPCs automáticamente usando el sistema centralizado del FSM.
        
        Primero elimina los NPCs gestionados por el FSM que ya existan en la zona,
        para que se re-creen con el estado correcto. Esto es necesario porque el lobby
        se REUTILIZA (no se regenera) cuando el jugador vuelve del dungeon.
        Sin esta limpieza, spawn_npcs_for_zone vería que el NPC ya existe y lo saltaría,
        impidiendo que las transiciones diferidas se ejecuten.
        """
        from ..systems.npc_states import npc_state_manager
        
        # Limpiar NPCs FSM existentes para re-crearlos con el estado actual
        fsm_npc_names = set(npc_state_manager.npc_states.keys())
        self.entities = [e for e in self.entities if e.name not in fsm_npc_names]
        
        # Usar el sistema centralizado de spawn (no requiere player)
        npc_state_manager.spawn_npcs_for_zone(zone=self)
    
    def _reveal_all_tiles(self) -> None:
        """
        Marca todos los tiles del lobby como visibles y explorados.
        Esto elimina el efecto de niebla de guerra en el lobby.
        """
        for col in self.tiles:
            for tile in col:
                tile.visible = True
                tile.explored = True
    
    def update_fov(self, x: int, y: int, radius: int) -> Set[Tuple[int, int]]:
        """
        Actualiza el campo de visión en el lobby.
        
        En el lobby, todos los tiles están siempre visibles (sin niebla de guerra).
        Esto permite que el jugador vea todo el lobby completo.
        
        Args:
            x: Centro X (ignorado en lobby, pero necesario para compatibilidad)
            y: Centro Y (ignorado en lobby, pero necesario para compatibilidad)
            radius: Radio de visión (ignorado en lobby, pero necesario para compatibilidad)
            
        Returns:
            Conjunto de todas las posiciones del lobby (todas visibles)
        """
        # Revelar todos los tiles
        self._reveal_all_tiles()
        
        # Retornar todas las posiciones del lobby como visibles
        all_positions: Set[Tuple[int, int]] = set()
        for x_pos in range(self.width):
            for y_pos in range(self.height):
                all_positions.add((x_pos, y_pos))
        
        return all_positions
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el lobby a diccionario.
        
        NOTA: El lobby es determinista — su estructura (tiles, paredes) se regenera
        siempre igual. Solo se guarda el estado dinámico (items en el suelo).
        Los NPCs se gestionan vía el sistema FSM y no necesitan guardarse aquí.
        """
        return {
            "width": self.width,
            "height": self.height,
            "zone_id": self.zone_id,
            "zone_type": self.zone_type,
            "dungeon_entrance": self.dungeon_entrance,
            # Solo guardamos items (estado dinámico del suelo)
            "items": [i.to_dict() for i in self.items],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Lobby:
        """
        Crea un lobby desde un diccionario de guardado.
        
        El lobby se REGENERA (no se restaura tile a tile) porque su estructura
        es determinista. Solo se restaura el estado dinámico:
        - Items en el suelo (el jugador pudo haber dejado cosas)
        - NPCs vía el sistema FSM (se spawnean automáticamente en generate())
        """
        from ..items.item import Item
        
        lobby = cls(data["width"], data["height"], data.get("zone_id", "lobby_main"))
        
        # Regenerar la estructura del lobby (tiles, paredes, escaleras, NPCs, FOV)
        # Esto es determinista: siempre produce el mismo resultado
        lobby.generate()
        
        # Restaurar solo el estado dinámico: items en el suelo
        for item_data in data.get("items", []):
            item = Item.from_dict(item_data)
            lobby.items.append(item)
        
        return lobby
