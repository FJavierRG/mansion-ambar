"""
Clase Room - Representa una habitación en la mazmorra.
"""
from __future__ import annotations
from typing import Tuple
from dataclasses import dataclass


@dataclass
class Room:
    """
    Representa una habitación rectangular en la mazmorra.
    
    Attributes:
        x: Coordenada X de la esquina superior izquierda
        y: Coordenada Y de la esquina superior izquierda
        width: Ancho de la habitación
        height: Alto de la habitación
    """
    x: int
    y: int
    width: int
    height: int
    
    @property
    def x2(self) -> int:
        """Coordenada X de la esquina inferior derecha."""
        return self.x + self.width
    
    @property
    def y2(self) -> int:
        """Coordenada Y de la esquina inferior derecha."""
        return self.y + self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        """Coordenadas del centro de la habitación."""
        center_x = (self.x + self.x2) // 2
        center_y = (self.y + self.y2) // 2
        return (center_x, center_y)
    
    @property
    def inner(self) -> Tuple[slice, slice]:
        """
        Retorna slices para el interior de la habitación (sin paredes).
        
        Returns:
            Tupla de slices (slice_x, slice_y)
        """
        return (slice(self.x + 1, self.x2), slice(self.y + 1, self.y2))
    
    def intersects(self, other: Room) -> bool:
        """
        Verifica si esta habitación se superpone con otra.
        
        Args:
            other: Otra habitación
            
        Returns:
            True si se superponen
        """
        return (
            self.x <= other.x2 and self.x2 >= other.x and
            self.y <= other.y2 and self.y2 >= other.y
        )
    
    def contains(self, x: int, y: int) -> bool:
        """
        Verifica si un punto está dentro de la habitación.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            True si el punto está dentro
        """
        return self.x < x < self.x2 and self.y < y < self.y2
    
    def distance_to(self, other: Room) -> float:
        """
        Calcula la distancia al centro de otra habitación.
        
        Args:
            other: Otra habitación
            
        Returns:
            Distancia euclidiana entre centros
        """
        cx1, cy1 = self.center
        cx2, cy2 = other.center
        return ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
    
    def __repr__(self) -> str:
        return f"Room({self.x}, {self.y}, {self.width}x{self.height})"
