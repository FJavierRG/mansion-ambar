"""
Sistema de Field of View (Campo de Visión).
Implementa el algoritmo de shadowcasting para visibilidad.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Set, Tuple, List
import math

if TYPE_CHECKING:
    from ..world.dungeon import Dungeon


class FOV:
    """
    Sistema de campo de visión usando shadowcasting.
    
    Calcula qué tiles son visibles desde una posición dada.
    """
    
    # Multiplicadores para las 8 octantes
    MULT = [
        [1, 0, 0, -1, -1, 0, 0, 1],
        [0, 1, -1, 0, 0, -1, 1, 0],
        [0, 1, 1, 0, 0, -1, -1, 0],
        [1, 0, 0, 1, -1, 0, 0, -1],
    ]
    
    @classmethod
    def compute(
        cls,
        dungeon: Dungeon,
        x: int,
        y: int,
        radius: int
    ) -> Set[Tuple[int, int]]:
        """
        Calcula el campo de visión desde una posición.
        
        Args:
            dungeon: La mazmorra
            x: Centro X
            y: Centro Y
            radius: Radio de visión
            
        Returns:
            Conjunto de posiciones visibles
        """
        visible: Set[Tuple[int, int]] = set()
        
        # El centro siempre es visible
        visible.add((x, y))
        
        # Calcular para cada octante
        for octant in range(8):
            cls._cast_light(
                dungeon, visible, x, y, radius,
                1, 1.0, 0.0, octant
            )
        
        return visible
    
    @classmethod
    def _cast_light(
        cls,
        dungeon: Dungeon,
        visible: Set[Tuple[int, int]],
        cx: int,
        cy: int,
        radius: int,
        row: int,
        start: float,
        end: float,
        octant: int
    ) -> None:
        """
        Proyecta luz en un octante usando shadowcasting recursivo.
        
        Args:
            dungeon: La mazmorra
            visible: Conjunto de tiles visibles (se modifica)
            cx, cy: Centro de visión
            radius: Radio máximo
            row: Fila actual
            start: Pendiente inicial
            end: Pendiente final
            octant: Índice del octante (0-7)
        """
        if start < end:
            return
        
        radius_sq = radius * radius
        
        for j in range(row, radius + 1):
            dx, dy = -j - 1, -j
            blocked = False
            new_start = start
            
            while dx <= 0:
                dx += 1
                
                # Transformar coordenadas según octante
                mx = cx + dx * cls.MULT[0][octant] + dy * cls.MULT[1][octant]
                my = cy + dx * cls.MULT[2][octant] + dy * cls.MULT[3][octant]
                
                # Calcular pendientes
                l_slope = (dx - 0.5) / (dy + 0.5)
                r_slope = (dx + 0.5) / (dy - 0.5)
                
                if start < r_slope:
                    continue
                elif end > l_slope:
                    break
                
                # Verificar si está dentro del radio
                if dx * dx + dy * dy <= radius_sq:
                    visible.add((mx, my))
                
                # Manejar bloqueo
                if blocked:
                    if not dungeon.is_transparent(mx, my):
                        new_start = r_slope
                        continue
                    else:
                        blocked = False
                        start = new_start
                else:
                    if not dungeon.is_transparent(mx, my) and j < radius:
                        blocked = True
                        cls._cast_light(
                            dungeon, visible, cx, cy, radius,
                            j + 1, start, l_slope, octant
                        )
                        new_start = r_slope
            
            if blocked:
                break
    
    @classmethod
    def has_line_of_sight(
        cls,
        dungeon: Dungeon,
        x1: int,
        y1: int,
        x2: int,
        y2: int
    ) -> bool:
        """
        Verifica si hay línea de visión entre dos puntos.
        
        Args:
            dungeon: La mazmorra
            x1, y1: Punto inicial
            x2, y2: Punto final
            
        Returns:
            True si hay línea de visión
        """
        # Algoritmo de Bresenham para trazar la línea
        points = cls._get_line(x1, y1, x2, y2)
        
        # Verificar cada punto excepto el inicial y final
        for x, y in points[1:-1]:
            if not dungeon.is_transparent(x, y):
                return False
        
        return True
    
    @staticmethod
    def _get_line(x1: int, y1: int, x2: int, y2: int) -> List[Tuple[int, int]]:
        """
        Obtiene los puntos en una línea usando Bresenham.
        
        Args:
            x1, y1: Punto inicial
            x2, y2: Punto final
            
        Returns:
            Lista de puntos (x, y)
        """
        points = []
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        
        err = dx - dy
        
        x, y = x1, y1
        
        while True:
            points.append((x, y))
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            
            if e2 > -dy:
                err -= dy
                x += sx
            
            if e2 < dx:
                err += dx
                y += sy
        
        return points
    
    @classmethod
    def compute_simple(
        cls,
        dungeon: Dungeon,
        x: int,
        y: int,
        radius: int
    ) -> Set[Tuple[int, int]]:
        """
        Versión simplificada del FOV usando raycasting básico.
        Útil como fallback o para debugging.
        
        Args:
            dungeon: La mazmorra
            x: Centro X
            y: Centro Y
            radius: Radio de visión
            
        Returns:
            Conjunto de posiciones visibles
        """
        visible: Set[Tuple[int, int]] = set()
        visible.add((x, y))
        
        # Trazar rayos en todas direcciones
        for angle in range(360):
            rad = math.radians(angle)
            dx = math.cos(rad)
            dy = math.sin(rad)
            
            for dist in range(1, radius + 1):
                tx = int(x + dx * dist + 0.5)
                ty = int(y + dy * dist + 0.5)
                
                if not (0 <= tx < dungeon.width and 0 <= ty < dungeon.height):
                    break
                
                visible.add((tx, ty))
                
                if not dungeon.is_transparent(tx, ty):
                    break
        
        return visible
