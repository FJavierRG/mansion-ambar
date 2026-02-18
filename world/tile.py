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


# Propiedades por tipo de tile
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
        walkable=True,
        transparent=True,
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
    
    @property
    def properties(self) -> TileProperties:
        """Retorna las propiedades del tile."""
        return TILE_PROPERTIES[self.tile_type]
    
    @property
    def walkable(self) -> bool:
        """Si se puede caminar sobre el tile."""
        return self.properties.walkable
    
    @property
    def transparent(self) -> bool:
        """Si el tile permite ver a través."""
        return self.properties.transparent
    
    @property
    def char(self) -> str:
        """Caracter ASCII del tile."""
        return self.properties.char
    
    @property
    def color(self) -> str:
        """Color del tile (clave en COLORS)."""
        if self.visible:
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
        return {
            "type": self.tile_type.name,
            "explored": self.explored,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Tile:
        """Crea un tile desde un diccionario."""
        tile = cls(TileType[data["type"]])
        tile.explored = data["explored"]
        return tile
    
    def __repr__(self) -> str:
        return f"Tile({self.tile_type.name}, explored={self.explored})"
