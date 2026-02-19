"""
Sistema de HUD (Heads-Up Display) del juego.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
import pygame

from ..config import COLORS, TILE_SIZE, FONT_SIZE, WINDOW_WIDTH

if TYPE_CHECKING:
    from ..entities.player import Player


class HUD:
    """
    HUD del juego que muestra información del jugador.
    
    Layout (una sola línea con secciones apiladas):
      [HP texto  ] [Nivel texto] [ATK] [DEF] [Oro] [Amuleto]
      [HP barra  ] [XP barra   ]
    
    El indicador de piso se renderiza aparte en la esquina superior derecha.
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
        
        padding = 8
        gap = 24  # Espacio entre secciones
        bar_height = 8
        text_y = self.y + padding
        bar_y = text_y + FONT_SIZE + 2
        
        cursor_x = self.x + padding
        
        # ── Sección HP: texto arriba, barra debajo ──
        cursor_x = self._render_hp_section(
            surface, player, cursor_x, text_y, bar_y, bar_height
        )
        cursor_x += gap
        
        # ── Sección Nivel + XP: texto arriba, barra debajo ──
        cursor_x = self._render_level_section(
            surface, player, cursor_x, text_y, bar_y, bar_height
        )
        cursor_x += gap
        
        # ── Stats en línea (centrados verticalmente): ATK, DEF, Oro, Amuleto ──
        self._render_combat_stats(surface, player, cursor_x, gap)
    
    def _render_hp_section(
        self,
        surface: pygame.Surface,
        player: Player,
        x: int,
        text_y: int,
        bar_y: int,
        bar_height: int
    ) -> int:
        """
        Renderiza la sección de HP (texto + barra apilados).
        
        Returns:
            Posición X tras la sección (para el siguiente elemento).
        """
        hp = player.fighter.hp
        max_hp = player.fighter.max_hp
        
        # Texto HP
        hp_text = f"HP: {hp}/{max_hp}"
        text_surface = self.font.render(hp_text, True, COLORS["white"])
        text_width = text_surface.get_width()
        surface.blit(text_surface, (x, text_y))
        
        # Barra de HP (mismo ancho que el texto, mínimo 80px)
        bar_width = max(80, text_width)
        
        # Fondo de la barra
        pygame.draw.rect(
            surface,
            COLORS["hp_bar_bg"],
            (x, bar_y, bar_width, bar_height)
        )
        
        # Barra de HP actual
        if max_hp > 0:
            current_width = int(bar_width * (hp / max_hp))
            if current_width > 0:
                pygame.draw.rect(
                    surface,
                    COLORS["hp_bar"],
                    (x, bar_y, current_width, bar_height)
                )
        
        return x + bar_width
    
    def _render_level_section(
        self,
        surface: pygame.Surface,
        player: Player,
        x: int,
        text_y: int,
        bar_y: int,
        bar_height: int
    ) -> int:
        """
        Renderiza la sección de Nivel + XP (texto + barra apilados).
        
        Returns:
            Posición X tras la sección.
        """
        # Texto Nivel
        level_text = f"Nivel: {player.fighter.level}"
        text_surface = self.font.render(level_text, True, COLORS["white"])
        text_width = text_surface.get_width()
        surface.blit(text_surface, (x, text_y))
        
        # Barra de XP (mismo ancho que el texto, mínimo 80px)
        bar_width = max(80, text_width)
        xp_current = player.current_level_xp
        xp_needed = player.xp_to_next_level
        
        # Fondo de la barra
        pygame.draw.rect(
            surface,
            COLORS["xp_bar_bg"],
            (x, bar_y, bar_width, bar_height)
        )
        
        # Barra de XP actual
        if xp_needed > 0:
            progress = min(1.0, xp_current / xp_needed)
            current_width = int(bar_width * progress)
            if current_width > 0:
                pygame.draw.rect(
                    surface,
                    COLORS["xp_bar"],
                    (x, bar_y, current_width, bar_height)
                )
        
        return x + bar_width
    
    def _render_combat_stats(
        self,
        surface: pygame.Surface,
        player: Player,
        start_x: int,
        gap: int
    ) -> None:
        """Renderiza ATK, DEF, Oro (y amuleto) centrados verticalmente."""
        center_y = self.y + self.height // 2 - FONT_SIZE // 2
        cursor_x = start_x
        
        # Ataque
        atk_text = self._format_attack_text(player)
        text_surface = self.font.render(atk_text, True, COLORS["message_damage"])
        surface.blit(text_surface, (cursor_x, center_y))
        cursor_x += text_surface.get_width() + gap
        
        # Defensa
        def_text = self._format_defense_text(player)
        text_surface = self.font.render(def_text, True, COLORS["message_heal"])
        surface.blit(text_surface, (cursor_x, center_y))
        cursor_x += text_surface.get_width() + gap
        
        # Oro
        gold_text = f"Oro: {player.gold}"
        text_surface = self.font.render(gold_text, True, COLORS["gold"])
        surface.blit(text_surface, (cursor_x, center_y))
        cursor_x += text_surface.get_width() + gap
        
        # Indicador de amuleto
        if player.has_amulet:
            amulet_text = "¡TIENES EL AMULETO!"
            text_surface = self.font.render(amulet_text, True, COLORS["amulet"])
            surface.blit(text_surface, (cursor_x, center_y))
    
    def render_floor_indicator(self, surface: pygame.Surface, player: Player) -> None:
        """
        Renderiza el indicador de piso en la esquina superior derecha.
        Se posiciona de forma responsive respecto al ancho de la superficie.
        
        Args:
            surface: Superficie de Pygame
            player: El jugador
        """
        floor_text = f"Piso: {player.current_floor}"
        text_surface = self.font.render(floor_text, True, COLORS["stairs"])
        
        text_w = text_surface.get_width()
        text_h = text_surface.get_height()
        
        padding = 6
        screen_w = surface.get_width()
        
        # Fondo semi-transparente
        bg_w = text_w + padding * 2
        bg_h = text_h + padding * 2
        bg_x = screen_w - bg_w - 4
        bg_y = 4
        
        bg_surface = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        bg_surface.fill((20, 20, 20, 180))
        surface.blit(bg_surface, (bg_x, bg_y))
        
        # Texto
        surface.blit(text_surface, (bg_x + padding, bg_y + padding))
    
    def _format_attack_text(self, player: Player) -> str:
        """Formatea el texto de ataque con vida del arma."""
        base_atk = player.base_attack
        
        weapon = player.equipped.get("weapon")
        if weapon:
            bonus = weapon.attack_bonus
            return f"ATK: {base_atk} +{bonus} [{weapon.durability}/{weapon.max_durability}]"
        else:
            return f"ATK: {base_atk}"
    
    def _format_defense_text(self, player: Player) -> str:
        """Formatea el texto de defensa con vida de la armadura."""
        base_def = player.base_defense
        
        armor = player.equipped.get("armor")
        if armor:
            bonus = armor.defense_bonus
            return f"DEF: {base_def} +{bonus} [{armor.durability}/{armor.max_durability}]"
        else:
            return f"DEF: {base_def}"
