"""
Clase Tile - Representa un tile individual del mapa.
"""
from __future__ import annotations
from enum import Enum, auto
from typing import Dict, Any
from dataclasses import dataclass

from ..config import SYMBOLS, COLORS


class TileType(Enum):
    """Tipos de tiles disponibles."""
    WALL = auto()
    FLOOR = auto()
    DOOR = auto()
    STAIRS_DOWN = auto()
    STAIRS_UP = auto()
    VOID = auto()


@dataclass
class TileProperties:
    """Propiedades de un tipo de tile."""
    walkable: bool
    transparent: bool
    char: str
    color: str
    dark_color: str


# Propiedades por tipo de tile (para DOOR, estos son los defaults — el Tile
# los sobreescribe dinámicamente según is_open)
TILE_PROPERTIES: Dict[TileType, TileProperties] = {
    TileType.VOID: TileProperties(
        walkable=False,
        transparent=False,
        char=" ",
        color="black",
        dark_color="black"
    ),
    TileType.WALL: TileProperties(
        walkable=False,
        transparent=False,
        char=SYMBOLS["wall"],
        color="wall",
        dark_color="wall_dark"
    ),
    TileType.FLOOR: TileProperties(
        walkable=True,
        transparent=True,
        char=SYMBOLS["floor"],
        color="floor",
        dark_color="floor_dark"
    ),
    TileType.DOOR: TileProperties(
        walkable=False,       # Default: cerrada → no walkable
        transparent=False,    # Default: cerrada → no transparente
        char=SYMBOLS["door"],
        color="door",
        dark_color="wall_dark"
    ),
    TileType.STAIRS_DOWN: TileProperties(
        walkable=True,
        transparent=True,
        char=SYMBOLS["stairs_down"],
        color="stairs",
        dark_color="floor_dark"
    ),
    TileType.STAIRS_UP: TileProperties(
        walkable=True,
        transparent=True,
        char=SYMBOLS["stairs_up"],
        color="stairs",
        dark_color="floor_dark"
    ),
}


class Tile:
    """
    Representa un tile individual en el mapa.
    
    Attributes:
        tile_type: Tipo del tile
        explored: Si el tile ha sido explorado
        visible: Si el tile está actualmente visible
        _is_open: Si la puerta está abierta (solo para DOOR)
        _orientation: Orientación de la puerta: "horizontal" o "vertical" (solo para DOOR)
    """
    
    def __init__(self, tile_type: TileType = TileType.VOID) -> None:
        """
        Inicializa un tile.
        
        Args:
            tile_type: Tipo del tile
        """
        self.tile_type = tile_type
        self.explored: bool = False
        self.visible: bool = False
        
        # Estado específico de puertas
        self._is_open: bool = False
        self._orientation: str = "horizontal"
    
    @property
    def is_open(self) -> bool:
        """Si la puerta está abierta (solo relevante para DOOR)."""
        return self._is_open
    
    @is_open.setter
    def is_open(self, value: bool) -> None:
        self._is_open = value
    
    @property
    def orientation(self) -> str:
        """Orientación de la puerta: 'horizontal' o 'vertical'."""
        return self._orientation
    
    @orientation.setter
    def orientation(self, value: str) -> None:
        self._orientation = value
    
    @property
    def properties(self) -> TileProperties:
        """Retorna las propiedades del tile."""
        return TILE_PROPERTIES[self.tile_type]
    
    @property
    def walkable(self) -> bool:
        """Si se puede caminar sobre el tile."""
        if self.tile_type == TileType.DOOR:
            return self._is_open
        return self.properties.walkable
    
    @property
    def transparent(self) -> bool:
        """Si el tile permite ver a través."""
        if self.tile_type == TileType.DOOR:
            return self._is_open
        return self.properties.transparent
    
    @property
    def char(self) -> str:
        """Caracter ASCII del tile (dinámico para puertas)."""
        if self.tile_type == TileType.DOOR:
            return SYMBOLS["door_open"] if self._is_open else SYMBOLS["door_closed"]
        return self.properties.char
    
    @property
    def color(self) -> str:
        """Color del tile (clave en COLORS)."""
        if self.visible:
            if self.tile_type == TileType.DOOR:
                return "door_open" if self._is_open else "door"
            return self.properties.color
        elif self.explored:
            return self.properties.dark_color
        else:
            return "black"
    
    def get_color_rgb(self) -> tuple:
        """Retorna el color RGB del tile."""
        return COLORS.get(self.color, COLORS["black"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el tile a diccionario."""
        data: Dict[str, Any] = {
            "type": self.tile_type.name,
            "explored": self.explored,
        }
        # Guardar estado de puerta si es DOOR
        if self.tile_type == TileType.DOOR:
            data["is_open"] = self._is_open
            data["orientation"] = self._orientation
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Tile:
        """Crea un tile desde un diccionario."""
        tile = cls(TileType[data["type"]])
        tile.explored = data["explored"]
        # Restaurar estado de puerta si existe
        if tile.tile_type == TileType.DOOR:
            tile._is_open = data.get("is_open", False)
            tile._orientation = data.get("orientation", "horizontal")
        return tile
    
    def __repr__(self) -> str:
        if self.tile_type == TileType.DOOR:
            state = "open" if self._is_open else "closed"
            return f"Tile(DOOR, {state}, {self._orientation}, explored={self.explored})"
        return f"Tile({self.tile_type.name}, explored={self.explored})"
