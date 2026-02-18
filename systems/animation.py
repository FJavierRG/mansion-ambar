"""
Sistema de animaciones del juego.
Maneja animaciones visuales como ataques, daño, etc.
"""
from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
import time
import random


@dataclass
class Animation:
    """
    Representa una animación en progreso.
    
    Attributes:
        entity_id: ID único de la entidad animada
        start_x: Posición X inicial (en tiles)
        start_y: Posición Y inicial
        target_x: Posición X objetivo
        target_y: Posición Y objetivo
        duration: Duración total en segundos
        elapsed: Tiempo transcurrido
        animation_type: Tipo de animación (lunge, shake, etc.)
        phase: Fase actual (forward, backward)
    """
    entity_id: int
    start_x: float
    start_y: float
    target_x: float
    target_y: float
    duration: float = 0.15  # 150ms por fase
    elapsed: float = 0.0
    animation_type: str = "lunge"
    phase: str = "forward"  # forward, backward
    
    @property
    def progress(self) -> float:
        """Progreso de la fase actual (0.0 a 1.0)."""
        return min(1.0, self.elapsed / self.duration)
    
    @property
    def is_complete(self) -> bool:
        """Si la animación ha terminado completamente."""
        return self.phase == "backward" and self.progress >= 1.0
    
    def get_current_offset(self) -> Tuple[float, float]:
        """
        Calcula el offset actual de la animación.
        
        Returns:
            Tupla (offset_x, offset_y) en tiles
        """
        # Calcular dirección
        dx = self.target_x - self.start_x
        dy = self.target_y - self.start_y
        
        # Normalizar (solo queremos la dirección, no la distancia completa)
        # El lunge solo avanza 0.4 tiles hacia el objetivo
        lunge_distance = 0.4
        
        if self.animation_type == "lunge":
            if self.phase == "forward":
                # Avanzar hacia el objetivo con easing
                t = self._ease_out_quad(self.progress)
                return (dx * lunge_distance * t, dy * lunge_distance * t)
            else:  # backward
                # Retroceder a la posición original
                t = self._ease_in_quad(self.progress)
                return (dx * lunge_distance * (1 - t), dy * lunge_distance * (1 - t))
        
        return (0.0, 0.0)
    
    def _ease_out_quad(self, t: float) -> float:
        """Easing cuadrático de salida (desacelera)."""
        return 1 - (1 - t) ** 2
    
    def _ease_in_quad(self, t: float) -> float:
        """Easing cuadrático de entrada (acelera)."""
        return t ** 2
    
    def update(self, delta_time: float) -> None:
        """
        Actualiza la animación.
        
        Args:
            delta_time: Tiempo transcurrido desde el último frame
        """
        self.elapsed += delta_time
        
        # Cambiar de fase cuando termina forward
        if self.phase == "forward" and self.progress >= 1.0:
            self.phase = "backward"
            self.elapsed = 0.0


class AnimationManager:
    """
    Gestor de animaciones del juego.
    
    Mantiene una lista de animaciones activas y las actualiza.
    También gestiona números de daño flotantes.
    """
    
    def __init__(self) -> None:
        """Inicializa el gestor de animaciones."""
        self.animations: Dict[int, Animation] = {}
        self.damage_numbers: List[DamageNumber] = []
        self.last_update: float = time.time()
    
    def add_attack_animation(
        self, 
        attacker_id: int, 
        attacker_x: int, 
        attacker_y: int,
        target_x: int, 
        target_y: int
    ) -> None:
        """
        Añade una animación de ataque (lunge).
        
        Args:
            attacker_id: ID de la entidad atacante
            attacker_x: Posición X del atacante
            attacker_y: Posición Y del atacante
            target_x: Posición X del objetivo
            target_y: Posición Y del objetivo
        """
        self.animations[attacker_id] = Animation(
            entity_id=attacker_id,
            start_x=attacker_x,
            start_y=attacker_y,
            target_x=target_x,
            target_y=target_y,
            animation_type="lunge"
        )
    
    def add_damage_number(
        self,
        x: int,
        y: int,
        damage: int,
        is_critical: bool = False,
        is_player_attack: bool = False
    ) -> None:
        """
        Añade un número de daño flotante.
        
        Args:
            x: Posición X (en tiles)
            y: Posición Y (en tiles)
            damage: Cantidad de daño
            is_critical: Si es un golpe crítico
            is_player_attack: Si el atacante es el jugador (True = blanco, False = rojo)
        """
        # Añadir pequeña variación aleatoria en X para evitar superposiciones
        offset_x = random.uniform(-0.15, 0.15)
        
        self.damage_numbers.append(
            DamageNumber(
                x=x + offset_x,
                y=y - 0.3,  # Empezar un poco arriba del sprite
                damage=damage,
                is_critical=is_critical,
                is_player_attack=is_player_attack
            )
        )
    
    def update(self) -> None:
        """Actualiza todas las animaciones activas y números de daño."""
        current_time = time.time()
        delta_time = current_time - self.last_update
        self.last_update = current_time
        
        # Actualizar animaciones y eliminar las completadas
        completed = []
        for entity_id, animation in self.animations.items():
            animation.update(delta_time)
            if animation.is_complete:
                completed.append(entity_id)
        
        for entity_id in completed:
            del self.animations[entity_id]
        
        # Actualizar números de daño y eliminar los completados
        self.damage_numbers = [
            dn for dn in self.damage_numbers
            if not dn.is_complete
        ]
        
        for damage_num in self.damage_numbers:
            damage_num.update(delta_time)
    
    def get_offset(self, entity_id: int) -> Tuple[float, float]:
        """
        Obtiene el offset de animación para una entidad.
        
        Args:
            entity_id: ID de la entidad
            
        Returns:
            Tupla (offset_x, offset_y) o (0, 0) si no hay animación
        """
        if entity_id in self.animations:
            return self.animations[entity_id].get_current_offset()
        return (0.0, 0.0)
    
    def has_active_animations(self) -> bool:
        """Retorna True si hay animaciones en progreso."""
        return len(self.animations) > 0 or len(self.damage_numbers) > 0
    
    def get_damage_numbers(self) -> List[DamageNumber]:
        """Retorna la lista de números de daño activos."""
        return self.damage_numbers
    
    def clear(self) -> None:
        """Limpia todas las animaciones y números de daño."""
        self.animations.clear()
        self.damage_numbers.clear()


@dataclass
class DamageNumber:
    """
    Representa un número de daño flotante.
    
    Attributes:
        x: Posición X inicial (en tiles)
        y: Posición Y inicial (en tiles)
        damage: Cantidad de daño a mostrar
        is_critical: Si es un golpe crítico
        is_player_attack: Si el atacante es el jugador (blanco) o enemigo (rojo)
        duration: Duración total en segundos
        elapsed: Tiempo transcurrido
        offset_y: Offset vertical acumulado (se mueve hacia arriba)
        alpha: Opacidad actual (255 = opaco, 0 = transparente)
    """
    x: float
    y: float
    damage: int
    is_critical: bool = False
    is_player_attack: bool = False
    duration: float = 1.0  # Duración total de 1 segundo
    elapsed: float = 0.0
    offset_y: float = 0.0
    alpha: int = 255
    
    def update(self, delta_time: float) -> None:
        """
        Actualiza el número de daño.
        
        Args:
            delta_time: Tiempo transcurrido desde el último frame
        """
        self.elapsed += delta_time
        
        # Moverse hacia arriba
        self.offset_y -= 0.3 * delta_time  # Se mueve 0.3 tiles por segundo hacia arriba
        
        # Calcular fadeout (desaparece en los últimos 0.3 segundos)
        fade_start = self.duration - 0.3
        if self.elapsed >= fade_start:
            fade_progress = (self.elapsed - fade_start) / 0.3
            self.alpha = int(255 * (1 - fade_progress))
        else:
            self.alpha = 255
    
    @property
    def is_complete(self) -> bool:
        """Si la animación ha terminado."""
        return self.elapsed >= self.duration
    
    def get_position(self) -> Tuple[float, float]:
        """
        Retorna la posición actual del número.
        
        Returns:
            Tupla (x, y) en tiles
        """
        # Añadir pequeña variación horizontal aleatoria para que no se superpongan
        return (self.x, self.y + self.offset_y)
