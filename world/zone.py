"""
Clase base Zone - Representa una zona genérica del juego.
Permite crear diferentes tipos de escenarios (lobby, mazmorra, etc.)
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Dict, Any, Tuple, Set
from abc import ABC, abstractmethod

from .tile import Tile, TileType

if TYPE_CHECKING:
    from ..entities.entity import Entity
    from ..items.item import Item


class Zone(ABC):
    """
    Clase base abstracta para todas las zonas del juego.
    
    Una zona puede ser una mazmorra, un lobby, una ciudad, etc.
    Todas comparten funcionalidad básica: tiles, entidades, items, FOV.
    
    Attributes:
        width: Ancho del mapa
        height: Alto del mapa
        zone_id: Identificador único de la zona
        zone_type: Tipo de zona (lobby, dungeon, etc.)
        tiles: Matriz de tiles
        entities: Lista de entidades
        items: Lista de items en el suelo
    """
    
    def __init__(
        self,
        width: int,
        height: int,
        zone_id: str,
        zone_type: str
    ) -> None:
        """
        Inicializa una zona vacía.
        
        Args:
            width: Ancho del mapa
            height: Alto del mapa
            zone_id: Identificador único de la zona
            zone_type: Tipo de zona (lobby, dungeon, etc.)
        """
        self.width = width
        self.height = height
        self.zone_id = zone_id
        self.zone_type = zone_type
        
        # Crear mapa vacío (todo paredes/void)
        self.tiles: List[List[Tile]] = [
            [Tile(TileType.WALL) for _ in range(height)]
            for _ in range(width)
        ]
        
        self.entities: List[Entity] = []
        self.items: List[Item] = []
    
    @abstractmethod
    def generate(self) -> Tuple[int, int]:
        """
        Genera la zona proceduralmente o desde datos.
        
        Returns:
            Posición inicial del jugador (x, y)
        """
        pass
    
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
        """Serializa la zona a diccionario."""
        return {
            "width": self.width,
            "height": self.height,
            "zone_id": self.zone_id,
            "zone_type": self.zone_type,
            "tiles": [
                [tile.to_dict() for tile in col]
                for col in self.tiles
            ],
            "entities": [e.to_dict() for e in self.entities],
            "items": [i.to_dict() for i in self.items],
        }
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> Zone:
        """Crea una zona desde un diccionario."""
        pass
