"""
Clase Dungeon - Generación y gestión de mazmorras.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Dict, Any, Tuple, Set
import random

from .tile import Tile, TileType
from .room import Room
from ..config import (
    MAP_WIDTH, MAP_HEIGHT, ROOM_MIN_SIZE, ROOM_MAX_SIZE,
    MAX_ROOMS, MAX_ROOM_MONSTERS, MAX_ROOM_ITEMS, MAX_DUNGEON_LEVEL,
    SYMBOLS
)

if TYPE_CHECKING:
    from ..entities.entity import Entity
    from ..entities.player import Player
    from ..entities.monster import Monster
    from ..items.item import Item


class Dungeon:
    """
    Representa un nivel de la mazmorra.
    
    Attributes:
        width: Ancho del mapa
        height: Alto del mapa
        floor: Número de piso
        tiles: Matriz de tiles
        rooms: Lista de habitaciones
        entities: Lista de entidades (monstruos, NPCs)
        items: Lista de items en el suelo
        stairs_down: Posición de escaleras descendentes
        stairs_up: Posición de escaleras ascendentes
    """
    
    def __init__(
        self,
        width: int = MAP_WIDTH,
        height: int = MAP_HEIGHT,
        floor: int = 1
    ) -> None:
        """
        Inicializa una mazmorra vacía.
        
        Args:
            width: Ancho del mapa
            height: Alto del mapa
            floor: Número de piso
        """
        self.width = width
        self.height = height
        self.floor = floor
        
        # Crear mapa vacío (todo paredes/void)
        self.tiles: List[List[Tile]] = [
            [Tile(TileType.WALL) for _ in range(height)]
            for _ in range(width)
        ]
        
        self.rooms: List[Room] = []
        self.entities: List[Entity] = []
        self.items: List[Item] = []
        
        self.stairs_down: Optional[Tuple[int, int]] = None
        self.stairs_up: Optional[Tuple[int, int]] = None
        
        # Tipo de zona (para compatibilidad con Zone)
        self.zone_type = "dungeon"
        
        # Para el jefe final
        self.boss_spawned: bool = False
    
    def generate(self) -> Tuple[int, int]:
        """
        Genera la mazmorra proceduralmente.
        
        Returns:
            Posición inicial del jugador (centro de la primera habitación)
        """
        # Generar habitaciones
        for _ in range(MAX_ROOMS * 2):  # Intentar más veces
            if len(self.rooms) >= MAX_ROOMS:
                break
            
            # Tamaño aleatorio
            w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            
            # Posición aleatoria
            x = random.randint(1, self.width - w - 2)
            y = random.randint(1, self.height - h - 2)
            
            new_room = Room(x, y, w, h)
            
            # Verificar superposición
            if not any(new_room.intersects(room) for room in self.rooms):
                self._create_room(new_room)
                
                if self.rooms:
                    # Conectar con la habitación anterior
                    self._create_tunnel(self.rooms[-1].center, new_room.center)
                
                self.rooms.append(new_room)
        
        # Colocar escaleras
        if self.rooms:
            # Escaleras hacia arriba en la primera habitación (si no es piso 1)
            if self.floor > 1:
                up_x, up_y = self.rooms[0].center
                self.tiles[up_x][up_y] = Tile(TileType.STAIRS_UP)
                self.stairs_up = (up_x, up_y)
            
            # Escaleras hacia abajo en la última habitación (si no es el último piso)
            if self.floor < MAX_DUNGEON_LEVEL:
                down_x, down_y = self.rooms[-1].center
                self.tiles[down_x][down_y] = Tile(TileType.STAIRS_DOWN)
                self.stairs_down = (down_x, down_y)
        
        # Poblar con monstruos e items
        self._populate()
        
        # Retornar posición inicial (cerca de escaleras arriba o centro de primera habitación)
        if self.stairs_up:
            # Buscar posición adyacente a las escaleras
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = self.stairs_up[0] + dx, self.stairs_up[1] + dy
                if self.is_walkable(nx, ny):
                    return (nx, ny)
        
        return self.rooms[0].center if self.rooms else (self.width // 2, self.height // 2)
    
    def _create_room(self, room: Room) -> None:
        """
        Cava una habitación en el mapa.
        
        Args:
            room: La habitación a crear
        """
        for x in range(room.x + 1, room.x2):
            for y in range(room.y + 1, room.y2):
                if 0 < x < self.width - 1 and 0 < y < self.height - 1:
                    self.tiles[x][y] = Tile(TileType.FLOOR)
    
    def _create_tunnel(self, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """
        Crea un túnel entre dos puntos.
        
        Args:
            start: Punto inicial (x, y)
            end: Punto final (x, y)
        """
        x1, y1 = start
        x2, y2 = end
        
        # Decidir aleatoriamente si ir horizontal o vertical primero
        if random.random() < 0.5:
            # Horizontal primero
            self._create_h_tunnel(x1, x2, y1)
            self._create_v_tunnel(y1, y2, x2)
        else:
            # Vertical primero
            self._create_v_tunnel(y1, y2, x1)
            self._create_h_tunnel(x1, x2, y2)
    
    def _create_h_tunnel(self, x1: int, x2: int, y: int) -> None:
        """Crea un túnel horizontal."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 < x < self.width - 1 and 0 < y < self.height - 1:
                self.tiles[x][y] = Tile(TileType.FLOOR)
    
    def _create_v_tunnel(self, y1: int, y2: int, x: int) -> None:
        """Crea un túnel vertical."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 < x < self.width - 1 and 0 < y < self.height - 1:
                self.tiles[x][y] = Tile(TileType.FLOOR)
    
    def _populate(self) -> None:
        """Puebla la mazmorra con monstruos e items."""
        from ..entities.monster import Monster, create_monster_for_floor
        from ..items.item import create_item_for_floor
        
        for i, room in enumerate(self.rooms):
            # No poblar la primera habitación (spawn del jugador)
            if i == 0:
                continue
            
            # Monstruos
            num_monsters = random.randint(0, min(MAX_ROOM_MONSTERS, 1 + self.floor // 2))
            for _ in range(num_monsters):
                x, y = self._get_random_room_position(room)
                if not self.get_blocking_entity_at(x, y):
                    monster = create_monster_for_floor(self.floor, x, y, self)
                    self.entities.append(monster)
            
            # Items - Sistema de desbloqueo progresivo
            # Fase 1: Sin items (primera run, va a puños)
            # Fase 2: Solo armas y armaduras (después de primera charla con Stranger en lobby)
            # Fase 3: Todos los items incluyendo pociones (después de segunda charla)
            from ..systems.events import event_manager
            
            # Verificar qué items están desbloqueados
            weapons_unlocked = event_manager.is_event_triggered("stranger_lobby_weapons_unlocked")
            potions_unlocked = event_manager.is_event_triggered("stranger_lobby_potions_unlocked")
            
            # Si no hay nada desbloqueado, no spawneear items
            if not weapons_unlocked:
                continue  # Saltar el spawneo de items (el jugador va a puños)
            
            # Determinar qué tipos de items pueden spawnear
            if weapons_unlocked and not potions_unlocked:
                # Fase 2: Solo armas y armaduras (después de primera charla con Stranger)
                allowed_types = ["weapon", "armor"]
            elif potions_unlocked:
                # Fase 3: Todos los items incluyendo pociones (después de segunda charla)
                allowed_types = ["weapon", "armor", "potion", "gold"]
            else:
                # No debería llegar aquí si weapons_unlocked es True
                allowed_types = []
            
            # Probabilidad de que la habitación tenga items (decrece con el piso)
            # Piso 1: 50% de chance, Piso 10: 14% de chance
            item_room_chance = 0.50 - (self.floor - 1) * 0.04
            
            if random.random() < item_room_chance:
                # Máximo 1 item por habitación
                num_items = random.randint(0, MAX_ROOM_ITEMS)
                
                for _ in range(num_items):
                    x, y = self._get_random_room_position(room)
                    if not self.get_item_at(x, y):
                        item = create_item_for_floor(self.floor, x, y, allowed_types=allowed_types)
                        self.items.append(item)
        
        # Spawn del jefe en el último piso
        if self.floor == MAX_DUNGEON_LEVEL and not self.boss_spawned:
            self._spawn_boss()
        
        # Spawn automático de NPCs basado en configuración de estados
        self.spawn_npcs_from_states()
    
    def _spawn_boss(self) -> None:
        """Spawnea el jefe final y el amuleto."""
        from ..entities.monster import Monster
        from ..items.item import Item
        from ..items.special import Amulet
        
        if len(self.rooms) < 2:
            return
        
        # El jefe en la última habitación
        boss_room = self.rooms[-1]
        bx, by = boss_room.center
        
        # Mover el jefe un poco si las escaleras están ahí
        if self.stairs_down and (bx, by) == self.stairs_down:
            bx += 1
        
        boss = Monster(bx, by, "ancient_dragon", self)
        self.entities.append(boss)
        self.boss_spawned = True
        
        # El amuleto cerca del jefe
        ax, ay = bx + 1, by
        if not self.is_walkable(ax, ay):
            ax, ay = bx - 1, by
        
        amulet = Amulet(ax, ay)
        self.items.append(amulet)
    
    def spawn_npcs_from_states(self) -> None:
        """
        Spawnea NPCs automáticamente usando el sistema centralizado del FSM.
        
        Delega completamente al sistema FSM que verifica todas las condiciones.
        """
        from ..systems.npc_states import npc_state_manager
        
        # Usar el sistema centralizado de spawn (no requiere player)
        npc_state_manager.spawn_npcs_for_zone(zone=self)
    
    def _get_random_room_position(self, room: Room) -> Tuple[int, int]:
        """
        Obtiene una posición aleatoria dentro de una habitación.
        
        Args:
            room: La habitación
            
        Returns:
            Posición (x, y)
        """
        x = random.randint(room.x + 1, room.x2 - 1)
        y = random.randint(room.y + 1, room.y2 - 1)
        return (x, y)
    
    def is_walkable(self, x: int, y: int) -> bool:
        """
        Verifica si una posición es transitable.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            True si se puede caminar ahí
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[x][y].walkable
    
    def is_transparent(self, x: int, y: int) -> bool:
        """
        Verifica si una posición es transparente (permite ver a través).
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            True si es transparente
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[x][y].transparent
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """
        Obtiene el tile en una posición.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            El tile o None si está fuera de límites
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x][y]
        return None
    
    def get_blocking_entity_at(self, x: int, y: int) -> Optional[Entity]:
        """
        Obtiene una entidad que bloquea en una posición.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            La entidad o None
        """
        for entity in self.entities:
            if entity.x == x and entity.y == y and entity.blocks:
                return entity
        return None
    
    def get_item_at(self, x: int, y: int) -> Optional[Item]:
        """
        Obtiene un item en una posición.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            El item o None
        """
        for item in self.items:
            if item.x == x and item.y == y:
                return item
        return None
    
    def get_items_at(self, x: int, y: int) -> List[Item]:
        """
        Obtiene todos los items en una posición.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            Lista de items
        """
        return [item for item in self.items if item.x == x and item.y == y]
    
    def remove_item(self, item: Item) -> bool:
        """
        Elimina un item del suelo.
        
        Args:
            item: Item a eliminar
            
        Returns:
            True si se eliminó
        """
        if item in self.items:
            self.items.remove(item)
            return True
        return False
    
    def add_item(self, item: Item, x: int, y: int) -> None:
        """
        Añade un item al suelo.
        
        Args:
            item: Item a añadir
            x: Coordenada X
            y: Coordenada Y
        """
        item.x = x
        item.y = y
        self.items.append(item)
    
    def update_fov(self, x: int, y: int, radius: int) -> Set[Tuple[int, int]]:
        """
        Actualiza el campo de visión desde una posición.
        
        Args:
            x: Centro X
            y: Centro Y
            radius: Radio de visión
            
        Returns:
            Conjunto de posiciones visibles
        """
        from ..systems.fov import FOV
        
        # Resetear visibilidad
        for col in self.tiles:
            for tile in col:
                tile.visible = False
        
        # Calcular nuevo FOV
        visible = FOV.compute(self, x, y, radius)
        
        # Marcar tiles visibles y explorados
        for vx, vy in visible:
            if 0 <= vx < self.width and 0 <= vy < self.height:
                self.tiles[vx][vy].visible = True
                self.tiles[vx][vy].explored = True
        
        return visible
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la mazmorra a diccionario."""
        return {
            "width": self.width,
            "height": self.height,
            "floor": self.floor,
            "tiles": [
                [tile.to_dict() for tile in col]
                for col in self.tiles
            ],
            "rooms": [
                {"x": r.x, "y": r.y, "width": r.width, "height": r.height}
                for r in self.rooms
            ],
            "entities": [e.to_dict() for e in self.entities],
            "items": [i.to_dict() for i in self.items],
            "stairs_down": self.stairs_down,
            "stairs_up": self.stairs_up,
            "boss_spawned": self.boss_spawned,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Dungeon:
        """Crea una mazmorra desde un diccionario."""
        from ..entities.monster import Monster
        from ..items.item import Item
        
        dungeon = cls(data["width"], data["height"], data["floor"])
        
        # Restaurar tiles
        for x, col in enumerate(data["tiles"]):
            for y, tile_data in enumerate(col):
                dungeon.tiles[x][y] = Tile.from_dict(tile_data)
        
        # Restaurar habitaciones
        dungeon.rooms = [
            Room(r["x"], r["y"], r["width"], r["height"])
            for r in data["rooms"]
        ]
        
        # Restaurar entidades (monstruos y NPCs)
        from ..entities.entity import Entity
        from ..ui.sprite_manager import sprite_manager
        
        for entity_data in data["entities"]:
            # Determinar si es un monstruo o un NPC genérico (Entity)
            if entity_data.get("monster_type"):
                # Es un monstruo
                entity = Monster.from_dict(entity_data, dungeon)
            else:
                # Es un NPC genérico - usar sistema FSM para restaurar sprite
                entity = Entity.from_dict(entity_data, dungeon)
                
                # Restaurar sprite usando el sistema genérico del FSM
                sprite = sprite_manager.get_creature_sprite(entity.name.lower())
                if sprite:
                    entity.sprite = sprite
            
            dungeon.entities.append(entity)
        
        # Restaurar items
        for item_data in data["items"]:
            item = Item.from_dict(item_data)
            dungeon.items.append(item)
        
        dungeon.stairs_down = tuple(data["stairs_down"]) if data["stairs_down"] else None
        dungeon.stairs_up = tuple(data["stairs_up"]) if data["stairs_up"] else None
        dungeon.boss_spawned = data.get("boss_spawned", False)
        
        # Asegurar que los NPCs estén en el estado correcto usando el sistema FSM
        # Esto reemplaza cualquier NPC cargado con uno creado usando el FSM
        dungeon.spawn_npcs_from_states()
        
        return dungeon
