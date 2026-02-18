"""
Sistema de HUD (Heads-Up Display) del juego.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
import pygame

from ..config import COLORS, TILE_SIZE, FONT_SIZE

if TYPE_CHECKING:
    from ..entities.player import Player


class HUD:
    """
    HUD del juego que muestra información del jugador.
    
    Muestra HP, nivel, piso, oro, ataque y defensa.
    """
    
    def __init__(self, font: pygame.font.Font, x: int, y: int, width: int, height: int) -> None:
        """
        Inicializa el HUD.
        
        Args:
            font: Fuente a usar
            x: Posición X
            y: Posición Y
            width: Ancho en píxeles
            height: Alto en píxeles
        """
        self.font = font
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def render(self, surface: pygame.Surface, player: Player) -> None:
        """
        Renderiza el HUD.
        
        Args:
            surface: Superficie de Pygame
            player: El jugador
        """
        # Fondo del HUD
        pygame.draw.rect(
            surface,
            COLORS["darker_gray"],
            (self.x, self.y, self.width, self.height)
        )
        
        # Borde
        pygame.draw.rect(
            surface,
            COLORS["gray"],
            (self.x, self.y, self.width, self.height),
            1
        )
        
        # Calcular posiciones
        line_height = FONT_SIZE + 4
        padding = 10
        
        # Línea 1: HP y barra de vida
        self._render_hp_bar(surface, player, padding, line_height)
        
        # Línea 2: Stats
        self._render_stats(surface, player, padding, line_height)
    
    def _render_hp_bar(
        self,
        surface: pygame.Surface,
        player: Player,
        padding: int,
        line_height: int
    ) -> None:
        """Renderiza la barra de HP."""
        hp = player.fighter.hp
        max_hp = player.fighter.max_hp
        
        # Texto HP
        hp_text = f"HP: {hp}/{max_hp}"
        text_surface = self.font.render(hp_text, True, COLORS["white"])
        surface.blit(text_surface, (self.x + padding, self.y + padding))
        
        # Barra de HP
        bar_x = self.x + padding + 120
        bar_y = self.y + padding + 2
        bar_width = 150
        bar_height = FONT_SIZE - 4
        
        # Fondo de la barra
        pygame.draw.rect(
            surface,
            COLORS["hp_bar_bg"],
            (bar_x, bar_y, bar_width, bar_height)
        )
        
        # Barra de HP actual
        current_width = int(bar_width * (hp / max_hp))
        if current_width > 0:
            pygame.draw.rect(
                surface,
                COLORS["hp_bar"],
                (bar_x, bar_y, current_width, bar_height)
            )
        
        # Nivel y Piso
        level_text = f"Nivel: {player.fighter.level}"
        text_surface = self.font.render(level_text, True, COLORS["white"])
        surface.blit(text_surface, (bar_x + bar_width + 20, self.y + padding))
        
        floor_text = f"Piso: {player.current_floor}"
        text_surface = self.font.render(floor_text, True, COLORS["stairs"])
        surface.blit(text_surface, (bar_x + bar_width + 140, self.y + padding))
    
    def _render_stats(
        self,
        surface: pygame.Surface,
        player: Player,
        padding: int,
        line_height: int
    ) -> None:
        """Renderiza los stats del jugador con durabilidad del equipo."""
        y_offset = self.y + padding + line_height + 5
        
        # Oro
        gold_text = f"Oro: {player.gold}"
        text_surface = self.font.render(gold_text, True, COLORS["gold"])
        surface.blit(text_surface, (self.x + padding, y_offset))
        
        # Ataque - formato: ATK: base +bonus(durabilidad%)
        atk_text = self._format_attack_text(player)
        text_surface = self.font.render(atk_text, True, COLORS["message_damage"])
        surface.blit(text_surface, (self.x + padding + 100, y_offset))
        
        # Defensa - formato: DEF: base +bonus(durabilidad%)
        def_text = self._format_defense_text(player)
        text_surface = self.font.render(def_text, True, COLORS["message_heal"])
        surface.blit(text_surface, (self.x + padding + 260, y_offset))
        
        # XP
        xp_text = f"XP: {player.current_level_xp}/{player.xp_to_next_level}"
        text_surface = self.font.render(xp_text, True, COLORS["xp_bar"])
        surface.blit(text_surface, (self.x + padding + 420, y_offset))
        
        # Indicador de amuleto
        if player.has_amulet:
            amulet_text = "¡TIENES EL AMULETO!"
            text_surface = self.font.render(amulet_text, True, COLORS["amulet"])
            surface.blit(text_surface, (self.x + padding + 580, y_offset))
    
    def _format_attack_text(self, player: Player) -> str:
        """Formatea el texto de ataque con durabilidad del arma."""
        base_atk = player.base_attack
        
        weapon = player.equipped.get("weapon")
        if weapon:
            bonus = weapon.attack_bonus
            durability = weapon.durability
            return f"ATK: {base_atk} +{bonus}({durability}%)"
        else:
            return f"ATK: {base_atk}"
    
    def _format_defense_text(self, player: Player) -> str:
        """Formatea el texto de defensa con durabilidad de la armadura."""
        base_def = player.base_defense
        
        armor = player.equipped.get("armor")
        if armor:
            bonus = armor.defense_bonus
            durability = armor.durability
            return f"DEF: {base_def} +{bonus}({durability}%)"
        else:
            return f"DEF: {base_def}"
