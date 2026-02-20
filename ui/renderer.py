"""
Sistema de renderizado del juego.
Dibuja el mapa, entidades, UI y mensajes usando Pygame.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple, Set, Optional, Any
import pygame
import time
import random

from ..config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE, FONT_NAME, FONT_SIZE,
    COLORS, MAP_WIDTH, MAP_HEIGHT, MESSAGE_LOG_HEIGHT,
    FPS, GameState,
    GRID_INVENTORY_WIDTH, GRID_INVENTORY_HEIGHT
)
from .hud import HUD
from .message_log import MessageLog
from .sprite_manager import sprite_manager
from .dialog import dialog_renderer
from ..systems.dialog_manager import dialog_manager
from ..systems.music import music_manager

if TYPE_CHECKING:
    from ..world.dungeon import Dungeon
    from ..entities.player import Player
    from ..entities.entity import Entity
    from ..systems.animation import AnimationManager


# ============================================================================
# EFECTO RELÁMPAGO EN VENTANA (lobby)
# Fácil de desactivar: pon LIGHTNING_ENABLED = False
# ============================================================================
LIGHTNING_ENABLED: bool = True

class LightningEffect:
    """
    Efecto de relámpago para decoraciones tipo 'ventanas'.
    
    Ciclo: espera aleatoria → flash1 → pausa → flash2 → fade out → repetir.
    Devuelve un alpha (0-255) que el renderer aplica al sprite.
    """
    
    # Tiempos de cada fase (en segundos)
    WAIT_MIN: float = 15.0   # Mínimo entre relámpagos
    WAIT_MAX: float = 35.0   # Máximo entre relámpagos
    FLASH1_ON: float = 0.08  # Primer destello
    FLASH1_OFF: float = 0.10 # Pausa entre destellos
    FLASH2_ON: float = 0.12  # Segundo destello
    FADE_OUT: float = 0.66   # Desvanecimiento lento
    
    def __init__(self) -> None:
        self._phase: str = "idle"       # idle, flash1_on, flash1_off, flash2_on, fade_out
        self._phase_start: float = time.time()
        self._next_strike: float = time.time() + random.uniform(
            self.WAIT_MIN, self.WAIT_MAX
        )
        self._just_triggered: bool = False  # True solo en el frame que arranca el rayo
    
    def did_trigger(self) -> bool:
        """Devuelve True una sola vez cuando arranca un relámpago (para disparar sonido)."""
        if self._just_triggered:
            self._just_triggered = False
            return True
        return False
    
    def _enter_phase(self, phase: str) -> None:
        """Cambia de fase y resetea el cronómetro."""
        self._phase = phase
        self._phase_start = time.time()
    
    def get_alpha(self) -> int:
        """
        Devuelve el alpha actual (0-255) del sprite de la ventana.
        Avanza la máquina de estados internamente.
        """
        now = time.time()
        elapsed = now - self._phase_start
        
        if self._phase == "idle":
            if now >= self._next_strike:
                self._enter_phase("flash1_on")
                self._just_triggered = True
            return 0
        
        elif self._phase == "flash1_on":
            if elapsed >= self.FLASH1_ON:
                self._enter_phase("flash1_off")
            return 255
        
        elif self._phase == "flash1_off":
            if elapsed >= self.FLASH1_OFF:
                self._enter_phase("flash2_on")
            return 0
        
        elif self._phase == "flash2_on":
            if elapsed >= self.FLASH2_ON:
                self._enter_phase("fade_out")
            return 255
        
        elif self._phase == "fade_out":
            if elapsed >= self.FADE_OUT:
                # Volver a idle con nueva espera aleatoria
                self._enter_phase("idle")
                self._next_strike = now + random.uniform(
                    self.WAIT_MIN, self.WAIT_MAX
                )
                return 0
            # Interpolación lineal de 255 → 0
            progress = elapsed / self.FADE_OUT
            return int(255 * (1.0 - progress))
        
        return 0


class Renderer:
    """
    Sistema de renderizado principal.
    
    Maneja todo el dibujo en pantalla usando Pygame.
    """
    
    def __init__(self) -> None:
        """Inicializa el renderizador."""
        pygame.init()
        pygame.display.set_caption("La Mansión de Ámbar")
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Cargar fuente monoespaciada
        try:
            self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
        except:
            self.font = pygame.font.Font(None, FONT_SIZE)
        
        # Calcular dimensiones
        self.map_width = MAP_WIDTH * TILE_SIZE
        self.map_height = MAP_HEIGHT * TILE_SIZE
        
        # Área del HUD (debajo del mapa)
        hud_y = self.map_height
        hud_height = 55
        self.hud = HUD(self.font, 0, hud_y, WINDOW_WIDTH, hud_height)
        
        # Área del log de mensajes (debajo del HUD)
        log_y = hud_y + hud_height
        log_height = WINDOW_HEIGHT - log_y
        # Asegurar que el log tenga espacio suficiente para 5 líneas
        min_log_height = (FONT_SIZE + 4) * MESSAGE_LOG_HEIGHT + 15
        if log_height < min_log_height:
            log_height = min_log_height
        self.log_area = (0, log_y, WINDOW_WIDTH, log_height)
        
        # Cache de superficies de caracteres para rendimiento
        self._char_cache: dict = {}
        
        # Referencia al animation manager (se actualiza en cada render)
        self._current_animation_manager: Optional[Any] = None
        
        # Efecto de relámpago para ventanas del lobby
        self._lightning_effect: Optional[LightningEffect] = (
            LightningEffect() if LIGHTNING_ENABLED else None
        )
    
    def render(
        self,
        dungeon: Dungeon,
        player: Player,
        visible_tiles: Set[Tuple[int, int]],
        message_log: MessageLog,
        game_state: str,
        inventory_mode: str = "normal",
        cursor: int = 0,
        scroll: int = 0,
        animation_manager: Optional[AnimationManager] = None,
        console_input: str = "",
        save_menu_selected: int = 0,
        save_menu_mode: str = "load",
        shop: Optional[Any] = None,
        shop_cursor: int = 0,
        pause_cursor: int = 0,
        options_cursor: int = 0,
        donation_amount: int = 0,
        donation_digit: int = 0,
        inv_drag_item: object = None,
        inv_drag_mouse_pos: tuple = (0, 0),
        inv_context_menu: dict = None,
        inv_hover_item: object = None,
    ) -> None:
        """
        Renderiza todo el juego.
        
        Args:
            dungeon: La mazmorra actual
            player: El jugador
            visible_tiles: Tiles visibles
            message_log: Log de mensajes
            game_state: Estado actual del juego
            inventory_mode: Modo del inventario (normal, use, equip, drop)
            cursor: Índice del item seleccionado en el inventario
            scroll: Offset de scroll del inventario
            animation_manager: Gestor de animaciones
            shop: Instancia de Shop (para estado SHOP)
            shop_cursor: Índice del item seleccionado en la tienda
        """
        # Guardar referencia para métodos internos
        self._current_animation_manager = animation_manager
        # Limpiar pantalla
        self.screen.fill(COLORS["black"])
        
        # Renderizar mapa
        self._render_map(dungeon, visible_tiles)
        
        # Renderizar items
        self._render_items(dungeon, visible_tiles)
        
        # Renderizar decoraciones de suelo (sangre, etc.)
        self._render_decorations(dungeon, visible_tiles)
        
        # Renderizar entidades
        self._render_entities(dungeon, visible_tiles)
        
        # Renderizar jugador
        self._render_player(player)
        
        # Renderizar indicadores de interacción sobre NPCs cercanos
        if game_state == GameState.PLAYING:
            self._render_interaction_prompts(dungeon, player, visible_tiles)
        
        # Renderizar números de daño flotantes
        self._render_damage_numbers()
        
        # Renderizar HUD
        self.hud.render(self.screen, player)
        
        # Renderizar indicador de piso (esquina superior derecha)
        self.hud.render_floor_indicator(self.screen, player)
        
        # Renderizar log de mensajes
        self._render_message_log(message_log)
        
        # Renderizar overlays según estado
        if game_state == GameState.INVENTORY:
            self._render_inventory(
                player, inventory_mode, cursor, scroll,
                drag_item=inv_drag_item,
                drag_mouse_pos=inv_drag_mouse_pos,
                context_menu=inv_context_menu,
                hover_item=inv_hover_item,
            )
        elif game_state == GameState.DEAD:
            self._render_death_screen()
        elif game_state == GameState.VICTORY:
            self._render_victory_screen()
        elif game_state == GameState.PAUSED:
            self._render_pause_menu(pause_cursor)
        elif game_state == GameState.OPTIONS:
            self._render_options_menu(options_cursor)
        elif game_state == GameState.DIALOG:
            self._render_dialog()
        elif game_state == GameState.CONSOLE:
            self._render_console(console_input)
        elif game_state == GameState.SAVE_MENU:
            self._render_save_menu(save_menu_selected, save_menu_mode)
        elif game_state == GameState.SHOP:
            self._render_shop(player, shop, shop_cursor)
        elif game_state == GameState.DONATION:
            self._render_donation(player, donation_amount, donation_digit)
        
        # Actualizar pantalla
        pygame.display.flip()
    
    def _render_map(self, dungeon: Dungeon, visible_tiles: Set[Tuple[int, int]]) -> None:
        """Renderiza el mapa de tiles."""
        from ..world.tile import TileType
        
        for x in range(min(dungeon.width, MAP_WIDTH)):
            for y in range(min(dungeon.height, MAP_HEIGHT)):
                tile = dungeon.tiles[x][y]
                
                if tile.visible or tile.explored:
                    # Verificar si es terreno especial visible (usar sprite)
                    if tile.visible:
                        if tile.tile_type == TileType.STAIRS_DOWN:
                            sprite = sprite_manager.get_terrain_sprite("stairs_down")
                            if sprite:
                                self._draw_sprite(x, y, sprite)
                                continue
                        elif tile.tile_type == TileType.STAIRS_UP:
                            sprite = sprite_manager.get_terrain_sprite("stairs_up")
                            if sprite:
                                self._draw_sprite(x, y, sprite)
                                continue
                        elif tile.tile_type == TileType.DOOR:
                            sprite_key = "door_open" if tile.is_open else "door_closed"
                            sprite = sprite_manager.get_terrain_sprite(sprite_key)
                            if sprite:
                                self._draw_sprite(x, y, sprite)
                                continue
                    elif tile.explored and tile.tile_type == TileType.DOOR:
                        # Puertas exploradas pero no visibles: sprite oscurecido
                        sprite_key = "door_open" if tile.is_open else "door_closed"
                        sprite = sprite_manager.get_terrain_sprite(sprite_key)
                        if sprite:
                            dark_sprite = sprite.copy()
                            dark_sprite.fill((80, 80, 80), special_flags=pygame.BLEND_RGB_MULT)
                            self._draw_sprite(x, y, dark_sprite)
                            continue
                    
                    # Fallback a ASCII para todo lo demás
                    char = tile.char
                    color = tile.get_color_rgb()
                    self._draw_char(x, y, char, color)
    
    def _render_items(self, dungeon: Dungeon, visible_tiles: Set[Tuple[int, int]]) -> None:
        """Renderiza los items en el suelo."""
        for item in dungeon.items:
            if (item.x, item.y) in visible_tiles:
                # Intentar sprite específico del item (ej: "dagger", "sword")
                sprite = None
                if getattr(item, 'sprite', None):
                    sprite = sprite_manager.get_item_sprite(item.sprite)
                # Fallback a sprite genérico por tipo (ej: "weapon", "armor")
                if not sprite:
                    sprite = sprite_manager.get_item_sprite(item.item_type)
                if sprite:
                    self._draw_sprite(item.x, item.y, sprite)
                else:
                    # Fallback a ASCII
                    color = COLORS.get(item.color, COLORS["white"])
                    self._draw_char(item.x, item.y, item.char, color)
    
    def _render_decorations(self, dungeon: Dungeon, visible_tiles: Set[Tuple[int, int]]) -> None:
        """Renderiza las decoraciones del suelo (sangre, hogueras animadas, ventanas con relámpago, etc.)."""
        current_time = time.time()
        
        for (x, y), (deco_type, angle) in dungeon.decorations.items():
            if (x, y) not in visible_tiles:
                continue
            
            # Verificar si es una decoración animada (múltiples frames)
            if sprite_manager.is_animated_decoration(deco_type):
                frames = sprite_manager.get_animated_decoration_frames(deco_type)
                if frames:
                    # Ciclar frames: ~200ms por frame
                    frame_index = int(current_time / 0.2) % len(frames)
                    self._draw_sprite(x, y, frames[frame_index])
                continue
            
            # Efecto relámpago para ventanas
            if deco_type == "ventanas" and self._lightning_effect:
                alpha = self._lightning_effect.get_alpha()
                if self._lightning_effect.did_trigger():
                    music_manager.play_sound("storm_sound.mp3")
                if alpha > 0:
                    sprite = sprite_manager.get_decoration_sprite(deco_type)
                    if sprite:
                        flash_sprite = sprite.copy()
                        flash_sprite.set_alpha(alpha)
                        self._draw_sprite(x, y, flash_sprite)
                continue
            
            # Decoración estática normal
            sprite = sprite_manager.get_decoration_sprite(deco_type)
            if sprite:
                if angle != 0:
                    sprite = pygame.transform.rotate(sprite, angle)
                self._draw_sprite(x, y, sprite)
    
    def _render_entities(self, dungeon: Dungeon, visible_tiles: Set[Tuple[int, int]]) -> None:
        """Renderiza las entidades (monstruos)."""
        for entity in dungeon.entities:
            if (entity.x, entity.y) in visible_tiles:
                # Obtener offset de animación si existe
                offset_x, offset_y = 0.0, 0.0
                if self._current_animation_manager:
                    offset_x, offset_y = self._current_animation_manager.get_offset(id(entity))
                
                # Verificar si el monstruo está muerto (cadáver = ASCII %)
                fighter = getattr(entity, 'fighter', None)
                is_dead = fighter.is_dead if fighter else False
                
                # Solo usar sprite si está vivo
                if not is_dead:
                    # Primero verificar si la entidad tiene un sprite asignado directamente (NPCs como Stranger)
                    sprite = getattr(entity, 'sprite', None)
                    
                    # Si no tiene sprite directo, intentar obtenerlo por monster_type
                    if not sprite:
                        monster_type = getattr(entity, 'monster_type', None)
                        sprite = sprite_manager.get_creature_sprite(monster_type) if monster_type else None
                    
                    if sprite:
                        self._draw_sprite_with_offset(entity.x, entity.y, sprite, offset_x, offset_y)
                        continue
                
                # Fallback a ASCII (también para cadáveres)
                color = COLORS.get(entity.color, COLORS["white"])
                self._draw_char_with_offset(
                    entity.x, entity.y, 
                    entity.char, color,
                    offset_x, offset_y
                )
    
    def _render_player(self, player: Player) -> None:
        """Renderiza al jugador."""
        # Obtener offset de animación si existe
        offset_x, offset_y = 0.0, 0.0
        if self._current_animation_manager:
            offset_x, offset_y = self._current_animation_manager.get_offset(id(player))
        
        # Intentar usar sprite del jugador
        sprite = sprite_manager.get_creature_sprite("player")
        
        if sprite:
            self._draw_sprite_with_offset(player.x, player.y, sprite, offset_x, offset_y)
        else:
            # Fallback a ASCII
            color = COLORS.get(player.color, COLORS["white"])
            self._draw_char_with_offset(
                player.x, player.y,
                player.char, color,
                offset_x, offset_y
            )
    
    def _render_message_log(self, message_log: MessageLog) -> None:
        """Renderiza el log de mensajes con soporte de scroll."""
        x, y, width, height = self.log_area
        
        # Fondo
        pygame.draw.rect(
            self.screen,
            COLORS["darker_gray"],
            (x, y, width, height)
        )
        
        # Borde
        pygame.draw.rect(
            self.screen,
            COLORS["gray"],
            (x, y, width, height),
            1
        )
        
        # Mensajes (get_recent ya tiene en cuenta el scroll_offset)
        messages = message_log.get_recent(MESSAGE_LOG_HEIGHT)
        padding = 5
        line_height = FONT_SIZE + 2
        
        for i, (text, color_key) in enumerate(messages):
            color = message_log.get_color_rgb(color_key)
            text_surface = self.font.render(text, True, color)
            self.screen.blit(
                text_surface,
                (x + padding, y + padding + i * line_height)
            )
        
        # Indicador de scroll (esquina derecha del log)
        indicator_x = x + width - 10
        if message_log.can_scroll_up:
            arrow_up = self.font.render("\u25b2", True, COLORS["gray"])
            self.screen.blit(arrow_up, (indicator_x, y + 2))
        if message_log.can_scroll_down:
            arrow_down = self.font.render("\u25bc", True, COLORS["gray"])
            self.screen.blit(arrow_down, (indicator_x, y + height - FONT_SIZE - 2))
    
    # ── Constantes de grid UI ─────────────────────────────────────
    _GRID_CELL = 48          # Píxeles por celda del grid
    _GRID_PAD = 1            # Espacio entre celdas (1px = línea fina)
    _GRID_BORDER = 1         # Grosor del borde de celda

    # Colores del grid
    _COL_CELL_EMPTY = (20, 20, 28)
    _COL_CELL_BORDER = (40, 40, 48)
    _COL_GRID_BG = (30, 30, 38)       # Fondo del grid (líneas divisorias)
    _COL_CONTEXT_BG = (35, 35, 45)    # Fondo del menú contextual
    _COL_CONTEXT_HOVER = (60, 60, 80) # Hover del menú contextual
    _COL_DROP_ZONE = (80, 30, 30)     # Color de zona de soltar (rojo tenue)
    _COL_ITEM_POTION = (15, 50, 50)
    _COL_ITEM_WEAPON = (40, 40, 50)
    _COL_ITEM_ARMOR = (45, 30, 18)
    _COL_ITEM_SPECIAL = (45, 15, 50)
    _COL_ITEM_DEFAULT = (30, 30, 38)
    _COL_SELECTED = (255, 255, 255)
    _COL_EQUIPPED = (255, 215, 0)         # Gold
    _COL_EQUIPPED_BG = (50, 43, 10)

    def _get_item_bg_color(self, item) -> tuple:
        """Devuelve un color de fondo según el tipo de item."""
        t = getattr(item, 'item_type', '')
        if t == 'potion':
            return self._COL_ITEM_POTION
        elif t == 'weapon':
            return self._COL_ITEM_WEAPON
        elif t == 'armor':
            return self._COL_ITEM_ARMOR
        elif t in ('amulet', 'gold', 'special', 'key'):
            return self._COL_ITEM_SPECIAL
        return self._COL_ITEM_DEFAULT

    def _render_inventory(
        self,
        player: Player,
        mode: str = "normal",
        cursor: int = 0,
        scroll: int = 0,
        drag_item: object = None,
        drag_mouse_pos: tuple = (0, 0),
        context_menu: dict = None,
        hover_item: object = None,
    ) -> None:
        """
        Renderiza la pantalla de inventario grid estilo RE4 / Tarkov.

        Dibuja:
        - Grid 2D con items ocupando celdas según sus dimensiones
        - Panel de equipamiento a la derecha
        - Tooltip/descripción del item bajo el cursor (hover)
        - Item arrastrado (ghost) siguiendo el ratón
        - Menú contextual (click derecho)
        """
        cell = self._GRID_CELL
        pad = self._GRID_PAD
        grid_cols = GRID_INVENTORY_WIDTH   # 10
        grid_rows = GRID_INVENTORY_HEIGHT  # 5

        # ── Dimensiones del panel ────────────────────────────
        grid_pixel_w = grid_cols * (cell + pad) + pad
        grid_pixel_h = grid_rows * (cell + pad) + pad
        equip_panel_w = 210
        tooltip_h = 70
        header_h = 12
        footer_h = 10

        inv_width = grid_pixel_w + 20 + equip_panel_w + 30   # padding
        inv_height = header_h + grid_pixel_h + 12 + tooltip_h + footer_h + 10
        inv_x = (WINDOW_WIDTH - inv_width) // 2
        inv_y = (WINDOW_HEIGHT - inv_height) // 2

        # ── Overlay ──────────────────────────────────────────
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS["black"])
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        # ── Panel de fondo ───────────────────────────────────
        pygame.draw.rect(self.screen, COLORS["darker_gray"],
                         (inv_x, inv_y, inv_width, inv_height))
        pygame.draw.rect(self.screen, COLORS["white"],
                         (inv_x, inv_y, inv_width, inv_height), 2)

        # (Sin título ni instrucciones — la interfaz se explica sola)

        # ── Origen del grid ──────────────────────────────────
        grid_x0 = inv_x + 15
        grid_y0 = inv_y + header_h

        # Referencia al grid del jugador
        grid_inv = player.grid_inventory
        items_list = grid_inv.get_all_items()

        # Item para tooltip: el que está bajo el ratón (hover), o el del cursor
        selected_item = hover_item if hover_item else (
            items_list[cursor] if 0 <= cursor < len(items_list) else None
        )

        # Conjunto de items equipados para marcarlos visualmente
        equipped_items = set()
        for eq in player.equipped.values():
            if eq is not None:
                equipped_items.add(id(eq))

        # ── Dibujar grid (fondo continuo + celdas) ────────────
        # Fondo del grid completo (las líneas finas son el "hueco" entre celdas)
        pygame.draw.rect(self.screen, self._COL_CELL_BORDER,
                         (grid_x0, grid_y0, grid_pixel_w, grid_pixel_h))
        # Dibujar celdas sobre el fondo → las líneas divisorias son los huecos de 1px
        for gx in range(grid_cols):
            for gy in range(grid_rows):
                px = grid_x0 + gx * (cell + pad) + pad
                py = grid_y0 + gy * (cell + pad) + pad
                pygame.draw.rect(self.screen, self._COL_CELL_EMPTY,
                                 (px, py, cell, cell))

        # ── Dibujar items en el grid ─────────────────────────
        drawn_items: set = set()
        for item_id, (gx, gy, item) in grid_inv._items.items():
            if item_id in drawn_items:
                continue
            drawn_items.add(item_id)

            # Si el item está siendo arrastrado, no dibujarlo en el grid
            if drag_item is not None and item is drag_item:
                continue

            w = getattr(item, 'grid_width', 1)
            h = getattr(item, 'grid_height', 1)

            # Posición en píxeles del bloque completo del item
            ipx = grid_x0 + gx * (cell + pad) + pad
            ipy = grid_y0 + gy * (cell + pad) + pad
            ipw = w * (cell + pad) - pad
            iph = h * (cell + pad) - pad

            is_equipped = id(item) in equipped_items
            is_selected = item is selected_item

            # Fondo del item
            bg = self._COL_EQUIPPED_BG if is_equipped else self._get_item_bg_color(item)
            pygame.draw.rect(self.screen, bg, (ipx, ipy, ipw, iph))

            # Borde del item
            if is_selected:
                border_color = self._COL_SELECTED
                border_w = 2
            elif is_equipped:
                border_color = self._COL_EQUIPPED
                border_w = 2
            else:
                border_color = self._COL_CELL_BORDER
                border_w = 1
            pygame.draw.rect(self.screen, border_color,
                             (ipx, ipy, ipw, iph), border_w)

            # ── Sprite del item (centrado, escalado) ─────────
            sprite = None
            sprite_key = getattr(item, 'sprite', None)
            if sprite_key:
                sprite = sprite_manager.get_item_sprite(sprite_key)
            if not sprite:
                sprite = sprite_manager.get_item_sprite(
                    getattr(item, 'item_type', ''))

            if sprite:
                # Escalar sprite para que quepa bien (max 80% del área)
                max_w = int(ipw * 0.8)
                max_h = int(iph * 0.8)
                sw, sh = sprite.get_width(), sprite.get_height()
                scale = min(max_w / sw, max_h / sh, 3.0)  # Máx ×3
                new_w = max(1, int(sw * scale))
                new_h = max(1, int(sh * scale))
                scaled = pygame.transform.scale(sprite, (new_w, new_h))
                sx = ipx + (ipw - new_w) // 2
                sy = ipy + (iph - new_h) // 2 - 4  # Un poco arriba para dejar espacio al nombre
                self.screen.blit(scaled, (sx, sy))
            else:
                # Fallback: dibujar el carácter del item (grande)
                ch = getattr(item, 'char', '?')
                item_color = COLORS.get(getattr(item, 'color', 'white'), COLORS["white"])
                try:
                    big_font = pygame.font.SysFont(FONT_NAME, min(cell - 8, 28), bold=True)
                except Exception:
                    big_font = pygame.font.Font(None, min(cell - 8, 28))
                ch_surface = big_font.render(ch, True, item_color)
                cx = ipx + (ipw - ch_surface.get_width()) // 2
                cy = ipy + (iph - ch_surface.get_height()) // 2 - 4
                self.screen.blit(ch_surface, (cx, cy))

            # ── Nombre del item (abajo del sprite) ───────────
            try:
                name_font = pygame.font.SysFont(FONT_NAME, 10)
            except Exception:
                name_font = pygame.font.Font(None, 10)
            # Truncar nombre si es muy largo
            display_name = item.name
            if name_font.size(display_name)[0] > ipw - 4:
                while len(display_name) > 3 and name_font.size(display_name + "..")[0] > ipw - 4:
                    display_name = display_name[:-1]
                display_name += ".."
            name_surface = name_font.render(display_name, True, COLORS["white"])
            nx = ipx + (ipw - name_surface.get_width()) // 2
            ny = ipy + iph - name_surface.get_height() - 2
            self.screen.blit(name_surface, (nx, ny))

            # Indicador "E" si está equipado (esquina superior-derecha)
            if is_equipped:
                try:
                    eq_font = pygame.font.SysFont(FONT_NAME, 10, bold=True)
                except Exception:
                    eq_font = pygame.font.Font(None, 10)
                eq_surf = eq_font.render("E", True, self._COL_EQUIPPED)
                self.screen.blit(eq_surf, (ipx + ipw - eq_surf.get_width() - 3, ipy + 2))

        # ── Panel de equipamiento (derecha del grid) ─────────
        equip_x = grid_x0 + grid_pixel_w + 12
        equip_y = grid_y0

        # Fondo del panel de equipo
        pygame.draw.rect(self.screen, (25, 25, 32),
                         (equip_x, equip_y, equip_panel_w, grid_pixel_h))
        pygame.draw.rect(self.screen, COLORS["gray"],
                         (equip_x, equip_y, equip_panel_w, grid_pixel_h), 1)

        # Título
        eq_title = "EQUIPADO"
        eq_title_surface = self.font.render(eq_title, True, COLORS["white"])
        self.screen.blit(eq_title_surface,
                         (equip_x + (equip_panel_w - eq_title_surface.get_width()) // 2,
                          equip_y + 8))

        # Slots de equipo
        slot_names = {
            "weapon": "Arma",
            "armor": "Armadura",
            "ring_left": "Anillo Izq.",
            "ring_right": "Anillo Der.",
        }
        line_h = FONT_SIZE + 6
        ey = equip_y + 35
        for slot, item in player.equipped.items():
            label = slot_names.get(slot, slot)
            if item:
                eq_text = f"{label}: {item.name}"
                color = self._COL_EQUIPPED
            else:
                eq_text = f"{label}: ---"
                color = COLORS["gray"]

            # Truncar si es muy largo
            eq_surface = self.font.render(eq_text, True, color)
            if eq_surface.get_width() > equip_panel_w - 16:
                while len(eq_text) > 8 and self.font.size(eq_text + "..")[0] > equip_panel_w - 16:
                    eq_text = eq_text[:-1]
                eq_text += ".."
                eq_surface = self.font.render(eq_text, True, color)
            self.screen.blit(eq_surface, (equip_x + 8, ey))
            ey += line_h

        # ── Tooltip / descripción (debajo del grid) ──────────
        tooltip_x = grid_x0
        tooltip_y = grid_y0 + grid_pixel_h + 8
        tooltip_w = inv_width - 30
        pygame.draw.rect(self.screen, (18, 18, 24),
                         (tooltip_x, tooltip_y, tooltip_w, tooltip_h))
        pygame.draw.rect(self.screen, COLORS["gray"],
                         (tooltip_x, tooltip_y, tooltip_w, tooltip_h), 1)

        if selected_item:
            # Nombre del item seleccionado
            sel_name = selected_item.name
            is_eq = id(selected_item) in equipped_items
            if is_eq:
                sel_name += "  (equipado)"
            name_color = self._COL_EQUIPPED if is_eq else COLORS["white"]
            name_surf = self.font.render(sel_name, True, name_color)
            self.screen.blit(name_surf, (tooltip_x + 10, tooltip_y + 6))

            # Descripción
            desc = getattr(selected_item, 'description', '') or ''
            if not desc:
                desc = getattr(selected_item, '_description', '') or ''

            # Stats extras
            stats_parts = []
            atk = getattr(selected_item, 'attack_bonus', 0)
            dfn = getattr(selected_item, 'defense_bonus', 0)
            if atk:
                stats_parts.append(f"+{atk} ATK")
            if dfn:
                stats_parts.append(f"+{dfn} DEF")
            dur = getattr(selected_item, 'durability', None)
            max_dur = getattr(selected_item, 'max_durability', None)
            if dur is not None and max_dur is not None:
                stats_parts.append(f"Dur: {dur}/{max_dur}")
            heal_val = getattr(selected_item, 'heal_amount', 0)
            if heal_val:
                stats_parts.append(f"Cura {heal_val} HP")

            stats_str = "  |  ".join(stats_parts) if stats_parts else ""

            try:
                desc_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE - 2)
            except Exception:
                desc_font = pygame.font.Font(None, FONT_SIZE - 2)

            if desc:
                desc_surf = desc_font.render(desc, True, COLORS["message"])
                self.screen.blit(desc_surf, (tooltip_x + 10, tooltip_y + 26))
            if stats_str:
                stats_surf = desc_font.render(stats_str, True, COLORS["message_heal"])
                self.screen.blit(stats_surf, (tooltip_x + 10, tooltip_y + 46))
        # (Sin texto cuando no hay item seleccionado — tooltip vacío)

        # ── Ghost del item arrastrado (sigue al ratón) ─────
        if drag_item is not None:
            mx, my = drag_mouse_pos
            dw = getattr(drag_item, 'grid_width', 1)
            dh = getattr(drag_item, 'grid_height', 1)
            ghost_w = dw * (cell + pad) - pad
            ghost_h = dh * (cell + pad) - pad
            ghost_x = mx - ghost_w // 2
            ghost_y = my - ghost_h // 2

            # ¿El ratón está sobre el grid?
            on_grid = (grid_x0 <= mx <= grid_x0 + grid_pixel_w and
                       grid_y0 <= my <= grid_y0 + grid_pixel_h)

            # Superficie semi-transparente
            ghost_surf = pygame.Surface((ghost_w, ghost_h), pygame.SRCALPHA)
            bg_color = self._get_item_bg_color(drag_item)
            ghost_surf.fill((*bg_color, 160))

            # Dibujar sprite sobre el ghost
            sprite = None
            sprite_key = getattr(drag_item, 'sprite', None)
            if sprite_key:
                sprite = sprite_manager.get_item_sprite(sprite_key)
            if not sprite:
                sprite = sprite_manager.get_item_sprite(
                    getattr(drag_item, 'item_type', ''))
            if sprite:
                max_sw = int(ghost_w * 0.8)
                max_sh = int(ghost_h * 0.8)
                sw, sh = sprite.get_width(), sprite.get_height()
                scale = min(max_sw / sw, max_sh / sh, 3.0)
                new_w = max(1, int(sw * scale))
                new_h = max(1, int(sh * scale))
                scaled = pygame.transform.scale(sprite, (new_w, new_h))
                ghost_surf.blit(scaled, ((ghost_w - new_w) // 2,
                                          (ghost_h - new_h) // 2 - 4))
            else:
                ch = getattr(drag_item, 'char', '?')
                item_color = COLORS.get(getattr(drag_item, 'color', 'white'), COLORS["white"])
                try:
                    big_font = pygame.font.SysFont(FONT_NAME, min(cell - 8, 28), bold=True)
                except Exception:
                    big_font = pygame.font.Font(None, min(cell - 8, 28))
                ch_surface = big_font.render(ch, True, item_color)
                ghost_surf.blit(ch_surface, ((ghost_w - ch_surface.get_width()) // 2,
                                              (ghost_h - ch_surface.get_height()) // 2))

            self.screen.blit(ghost_surf, (ghost_x, ghost_y))

            # Borde del ghost
            border_color = COLORS["white"] if on_grid else (200, 60, 60)
            pygame.draw.rect(self.screen, border_color,
                             (ghost_x, ghost_y, ghost_w, ghost_h), 2)

            # Indicador "soltar" si fuera del grid
            if not on_grid:
                try:
                    drop_font = pygame.font.SysFont(FONT_NAME, 12, bold=True)
                except Exception:
                    drop_font = pygame.font.Font(None, 12)
                drop_label = drop_font.render("SOLTAR", True, (255, 80, 80))
                self.screen.blit(drop_label, (ghost_x + (ghost_w - drop_label.get_width()) // 2,
                                               ghost_y + ghost_h + 4))

        # ── Menú contextual (click derecho) ────────────────
        if context_menu is not None:
            cm_x = context_menu.get("pixel_x", 0)
            cm_y = context_menu.get("pixel_y", 0)
            cm_options = context_menu.get("options", [])

            if cm_options:
                cm_w = 140
                cm_line_h = 28
                cm_h = len(cm_options) * cm_line_h + 8

                # Ajustar para no salir de pantalla
                if cm_x + cm_w > WINDOW_WIDTH:
                    cm_x = WINDOW_WIDTH - cm_w - 4
                if cm_y + cm_h > WINDOW_HEIGHT:
                    cm_y = WINDOW_HEIGHT - cm_h - 4

                # Fondo
                pygame.draw.rect(self.screen, self._COL_CONTEXT_BG,
                                 (cm_x, cm_y, cm_w, cm_h))
                pygame.draw.rect(self.screen, COLORS["white"],
                                 (cm_x, cm_y, cm_w, cm_h), 1)

                # Detectar hover del ratón sobre las opciones
                mouse_pos = pygame.mouse.get_pos()
                try:
                    cm_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE, bold=False)
                except Exception:
                    cm_font = pygame.font.Font(None, FONT_SIZE)

                for i, opt in enumerate(cm_options):
                    opt_y = cm_y + 4 + i * cm_line_h
                    opt_rect = pygame.Rect(cm_x + 2, opt_y, cm_w - 4, cm_line_h)

                    # Highlight si el ratón está sobre esta opción
                    if opt_rect.collidepoint(mouse_pos):
                        pygame.draw.rect(self.screen, self._COL_CONTEXT_HOVER, opt_rect)

                    opt_surface = cm_font.render(opt["label"], True, COLORS["white"])
                    self.screen.blit(opt_surface, (cm_x + 10, opt_y + (cm_line_h - opt_surface.get_height()) // 2))

    # ── Helpers del grid (pixel ↔ celda) ──────────────────────────

    def get_grid_layout(self) -> dict:
        """
        Retorna las coordenadas del grid de inventario en pantalla.
        Necesario para que game.py convierta posiciones de ratón a celdas.
        """
        cell = self._GRID_CELL
        pad = self._GRID_PAD
        grid_cols = GRID_INVENTORY_WIDTH
        grid_rows = GRID_INVENTORY_HEIGHT

        grid_pixel_w = grid_cols * (cell + pad) + pad
        grid_pixel_h = grid_rows * (cell + pad) + pad
        equip_panel_w = 210
        tooltip_h = 70
        header_h = 12
        footer_h = 10

        inv_width = grid_pixel_w + 20 + equip_panel_w + 30
        inv_height = header_h + grid_pixel_h + 12 + tooltip_h + footer_h + 10
        inv_x = (WINDOW_WIDTH - inv_width) // 2
        inv_y = (WINDOW_HEIGHT - inv_height) // 2

        grid_x0 = inv_x + 15
        grid_y0 = inv_y + header_h

        return {
            "cell": cell,
            "pad": pad,
            "grid_cols": grid_cols,
            "grid_rows": grid_rows,
            "grid_x0": grid_x0,
            "grid_y0": grid_y0,
            "grid_pixel_w": grid_pixel_w,
            "grid_pixel_h": grid_pixel_h,
            "inv_x": inv_x,
            "inv_y": inv_y,
            "inv_width": inv_width,
            "inv_height": inv_height,
        }

    def pixel_to_grid_cell(self, px: int, py: int) -> Tuple[int, int]:
        """
        Convierte coordenadas de pantalla a celda del grid.
        Retorna (-1, -1) si está fuera del grid.
        """
        layout = self.get_grid_layout()
        cell = layout["cell"]
        pad = layout["pad"]
        gx0 = layout["grid_x0"]
        gy0 = layout["grid_y0"]

        rx = px - gx0
        ry = py - gy0

        if rx < 0 or ry < 0:
            return (-1, -1)

        col = rx // (cell + pad)
        row = ry // (cell + pad)

        if col < 0 or col >= layout["grid_cols"] or row < 0 or row >= layout["grid_rows"]:
            return (-1, -1)

        # Verificar que no estamos en el "padding" entre celdas
        local_x = rx - col * (cell + pad)
        local_y = ry - row * (cell + pad)
        if local_x < pad or local_y < pad:
            # Estamos en la línea divisoria, snap a la celda más cercana
            pass  # Aún así retornamos la celda, es más usable

        return (int(col), int(row))

    def is_pixel_on_grid(self, px: int, py: int) -> bool:
        """Verifica si un pixel está dentro del área del grid."""
        layout = self.get_grid_layout()
        return (layout["grid_x0"] <= px <= layout["grid_x0"] + layout["grid_pixel_w"] and
                layout["grid_y0"] <= py <= layout["grid_y0"] + layout["grid_pixel_h"])

    def is_pixel_on_inventory_window(self, px: int, py: int) -> bool:
        """Verifica si un pixel está dentro de la ventana de inventario."""
        layout = self.get_grid_layout()
        return (layout["inv_x"] <= px <= layout["inv_x"] + layout["inv_width"] and
                layout["inv_y"] <= py <= layout["inv_y"] + layout["inv_height"])

    def _render_shop(
        self,
        player: Player,
        shop: Optional[Any] = None,
        cursor: int = 0
    ) -> None:
        """Renderiza la pantalla de la tienda."""
        # Overlay semi-transparente
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS["black"])
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        # Ventana de la tienda
        shop_width = 550
        shop_height = 400
        shop_x = (WINDOW_WIDTH - shop_width) // 2
        shop_y = (WINDOW_HEIGHT - shop_height) // 2
        
        # Fondo
        pygame.draw.rect(
            self.screen,
            COLORS["darker_gray"],
            (shop_x, shop_y, shop_width, shop_height)
        )
        # Borde
        pygame.draw.rect(
            self.screen,
            COLORS["white"],
            (shop_x, shop_y, shop_width, shop_height),
            2
        )
        
        # Título
        shop_name = shop.name if shop else "Tienda"
        title = f"=== {shop_name.upper()} ==="
        title_surface = self.font.render(title, True, COLORS["white"])
        self.screen.blit(
            title_surface,
            (shop_x + (shop_width - title_surface.get_width()) // 2, shop_y + 10)
        )
        
        # Oro del jugador
        gold_text = f"Tu oro: {player.gold}"
        gold_color = COLORS.get("gold", COLORS["message_important"])
        gold_surface = self.font.render(gold_text, True, gold_color)
        self.screen.blit(gold_surface, (shop_x + shop_width - gold_surface.get_width() - 20, shop_y + 12))
        
        # Instrucciones
        instructions = "↑↓ Navegar    ENTER Comprar    ESC Cerrar"
        instr_surface = self.font.render(instructions, True, COLORS["gray"])
        self.screen.blit(instr_surface, (shop_x + 20, shop_y + 35))
        
        # Línea separadora
        separator_y = shop_y + 55
        pygame.draw.line(
            self.screen,
            COLORS["gray"],
            (shop_x + 10, separator_y),
            (shop_x + shop_width - 10, separator_y),
            1
        )
        
        # Items de la tienda
        line_height = FONT_SIZE + 8
        y_offset = shop_y + 65
        
        if not shop or not shop.items:
            empty_text = "No hay mercancía disponible."
            empty_surface = self.font.render(empty_text, True, COLORS["gray"])
            self.screen.blit(empty_surface, (shop_x + 20, y_offset))
        else:
            for i, shop_item in enumerate(shop.items):
                is_selected = (i == cursor)
                can_afford = player.gold >= shop_item.price
                
                # Fondo de selección
                if is_selected:
                    selection_rect = pygame.Rect(
                        shop_x + 15,
                        y_offset - 2,
                        shop_width - 30,
                        line_height
                    )
                    pygame.draw.rect(self.screen, COLORS["gray"], selection_rect)
                
                # Indicador de selección
                prefix = "► " if is_selected else "  "
                
                # Color del texto
                if is_selected:
                    color = COLORS["black"]
                elif not can_afford:
                    color = COLORS.get("message_death", COLORS["gray"])
                else:
                    color = COLORS["white"]
                
                # Nombre del item + descripción
                item_text = f"{prefix}{shop_item.name}  ({shop_item.description})"
                item_surface = self.font.render(item_text, True, color)
                self.screen.blit(item_surface, (shop_x + 20, y_offset))
                
                # Precio (alineado a la derecha)
                price_text = f"{shop_item.price} oro"
                price_color = color if can_afford else COLORS.get("message_death", COLORS["gray"])
                if is_selected:
                    price_color = COLORS["black"]
                price_surface = self.font.render(price_text, True, price_color)
                self.screen.blit(
                    price_surface,
                    (shop_x + shop_width - price_surface.get_width() - 20, y_offset)
                )
                
                y_offset += line_height
        
        # Mensaje informativo al fondo
        info_y = shop_y + shop_height - 30
        if shop and shop.items and 0 <= cursor < len(shop.items):
            selected_item = shop.items[cursor]
            if player.gold < selected_item.price:
                info_text = f"Necesitas {selected_item.price - player.gold} monedas más."
                info_surface = self.font.render(info_text, True, COLORS.get("message_death", COLORS["gray"]))
            else:
                info_text = "Pulsa ENTER para comprar."
                info_surface = self.font.render(info_text, True, COLORS["white"])
            self.screen.blit(info_surface, (shop_x + 20, info_y))
    
    def _render_donation(
        self,
        player: Player,
        amount: int = 0,
        active_digit: int = 0,
    ) -> None:
        """
        Renderiza el selector de donación de oro.
        
        Muestra dos dígitos (decenas y unidades) con flechitas ↑↓.
        El dígito activo se resalta.
        
        Args:
            player: El jugador (para mostrar oro disponible)
            amount: Cantidad seleccionada actualmente (0-99)
            active_digit: Dígito activo (0=unidades, 1=decenas)
        """
        # Overlay semi-transparente
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS["black"])
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        # Ventana de donación (compacta)
        panel_w = 340
        panel_h = 220
        panel_x = (WINDOW_WIDTH - panel_w) // 2
        panel_y = (WINDOW_HEIGHT - panel_h) // 2
        
        # Fondo
        pygame.draw.rect(
            self.screen, COLORS["darker_gray"],
            (panel_x, panel_y, panel_w, panel_h)
        )
        # Borde
        pygame.draw.rect(
            self.screen, COLORS["white"],
            (panel_x, panel_y, panel_w, panel_h), 2
        )
        
        # Título
        title = "=== DONACIÓN ==="
        title_surface = self.font.render(title, True, COLORS["white"])
        self.screen.blit(
            title_surface,
            (panel_x + (panel_w - title_surface.get_width()) // 2, panel_y + 10)
        )
        
        # Oro del jugador
        gold_text = f"Tu oro: {player.gold}"
        gold_color = COLORS.get("gold", COLORS["message_important"])
        gold_surface = self.font.render(gold_text, True, gold_color)
        self.screen.blit(
            gold_surface,
            (panel_x + (panel_w - gold_surface.get_width()) // 2, panel_y + 35)
        )
        
        # Separar cantidad en decenas y unidades
        tens = amount // 10
        units = amount % 10
        
        # Dimensiones de cada columna de dígito
        digit_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 10, bold=True)
        arrow_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE + 4)
        col_w = 50
        gap = 20
        total_w = col_w * 2 + gap
        start_x = panel_x + (panel_w - total_w) // 2
        center_y = panel_y + 95
        
        digits = [(tens, 1), (units, 0)]  # (valor, digit_id)
        
        for i, (val, digit_id) in enumerate(digits):
            cx = start_x + i * (col_w + gap) + col_w // 2
            is_active = (digit_id == active_digit)
            
            # Color del dígito
            digit_color = COLORS["white"] if is_active else COLORS["gray"]
            arrow_color = COLORS["white"] if is_active else COLORS.get("dark_gray", (60, 60, 60))
            
            # Flecha arriba ▲
            up_surface = arrow_font.render("▲", True, arrow_color)
            self.screen.blit(
                up_surface,
                (cx - up_surface.get_width() // 2, center_y - 35)
            )
            
            # Dígito
            digit_surface = digit_font.render(str(val), True, digit_color)
            self.screen.blit(
                digit_surface,
                (cx - digit_surface.get_width() // 2, center_y - 8)
            )
            
            # Subrayado del dígito activo
            if is_active:
                underline_y = center_y + digit_surface.get_height() - 5
                underline_w = max(digit_surface.get_width(), 16)
                pygame.draw.line(
                    self.screen, COLORS["white"],
                    (cx - underline_w // 2, underline_y),
                    (cx + underline_w // 2, underline_y),
                    2
                )
            
            # Flecha abajo ▼
            down_surface = arrow_font.render("▼", True, arrow_color)
            self.screen.blit(
                down_surface,
                (cx - down_surface.get_width() // 2, center_y + 28)
            )
        
        # Total a donar
        total_text = f"Donar: {amount} oro"
        total_color = COLORS["white"] if amount > 0 else COLORS["gray"]
        total_surface = self.font.render(total_text, True, total_color)
        self.screen.blit(
            total_surface,
            (panel_x + (panel_w - total_surface.get_width()) // 2, panel_y + panel_h - 60)
        )
        
        # Instrucciones
        hint = "←→ Dígito   ↑↓ Valor   ENTER Donar   ESC Cancelar"
        hint_surface = self.font.render(hint, True, COLORS.get("dark_gray", (80, 80, 80)))
        self.screen.blit(
            hint_surface,
            (panel_x + (panel_w - hint_surface.get_width()) // 2, panel_y + panel_h - 30)
        )
    
    def _render_death_screen(self) -> None:
        """Renderiza la pantalla de muerte."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS["black"])
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        # Texto de muerte
        death_text = "HAS MUERTO"
        death_surface = self.font.render(death_text, True, COLORS["message_death"])
        death_surface = pygame.transform.scale(
            death_surface,
            (death_surface.get_width() * 3, death_surface.get_height() * 3)
        )
        self.screen.blit(
            death_surface,
            ((WINDOW_WIDTH - death_surface.get_width()) // 2,
             (WINDOW_HEIGHT - death_surface.get_height()) // 2 - 50)
        )
        
        # Instrucciones
        restart_text = "Presiona [R] para reiniciar o [ESC] para salir"
        restart_surface = self.font.render(restart_text, True, COLORS["white"])
        self.screen.blit(
            restart_surface,
            ((WINDOW_WIDTH - restart_surface.get_width()) // 2,
             (WINDOW_HEIGHT - restart_surface.get_height()) // 2 + 50)
        )
    
    def _render_victory_screen(self) -> None:
        """Renderiza la pantalla de victoria."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS["black"])
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        # Texto de victoria
        victory_text = "¡VICTORIA!"
        victory_surface = self.font.render(victory_text, True, COLORS["gold"])
        victory_surface = pygame.transform.scale(
            victory_surface,
            (victory_surface.get_width() * 3, victory_surface.get_height() * 3)
        )
        self.screen.blit(
            victory_surface,
            ((WINDOW_WIDTH - victory_surface.get_width()) // 2,
             (WINDOW_HEIGHT - victory_surface.get_height()) // 2 - 80)
        )
        
        # Subtexto
        sub_text = "¡Has escapado con el Amuleto de Ámbar!"
        sub_surface = self.font.render(sub_text, True, COLORS["amulet"])
        self.screen.blit(
            sub_surface,
            ((WINDOW_WIDTH - sub_surface.get_width()) // 2,
             (WINDOW_HEIGHT - sub_surface.get_height()) // 2)
        )
        
        # Instrucciones
        restart_text = "Presiona [R] para jugar de nuevo o [ESC] para salir"
        restart_surface = self.font.render(restart_text, True, COLORS["white"])
        self.screen.blit(
            restart_surface,
            ((WINDOW_WIDTH - restart_surface.get_width()) // 2,
             (WINDOW_HEIGHT - restart_surface.get_height()) // 2 + 50)
        )
    
    def _render_pause_menu(self, selected: int = 0) -> None:
        """Renderiza el menú de pausa con navegación por cursor."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS["black"])
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        # Título
        title_text = "PAUSA"
        title_surface = self.font.render(title_text, True, COLORS["white"])
        title_surface = pygame.transform.scale(
            title_surface,
            (title_surface.get_width() * 2, title_surface.get_height() * 2)
        )
        title_y = WINDOW_HEIGHT // 2 - 80
        self.screen.blit(
            title_surface,
            ((WINDOW_WIDTH - title_surface.get_width()) // 2, title_y)
        )
        
        # Línea decorativa
        line_y = title_y + title_surface.get_height() + 10
        line_width = 200
        line_x = (WINDOW_WIDTH - line_width) // 2
        pygame.draw.line(
            self.screen, COLORS["gray"],
            (line_x, line_y), (line_x + line_width, line_y), 1
        )
        
        # Opciones del menú
        options = ["Continuar", "Opciones", "Salir"]
        
        y_offset = line_y + 25
        for i, option in enumerate(options):
            if i == selected:
                # Opción seleccionada: resaltada con indicador
                text = f"> {option} <"
                color = COLORS["white"]
            else:
                text = option
                color = COLORS["gray"]
            
            opt_surface = self.font.render(text, True, color)
            self.screen.blit(
                opt_surface,
                ((WINDOW_WIDTH - opt_surface.get_width()) // 2, y_offset)
            )
            y_offset += FONT_SIZE + 12
        
        # Hint de controles
        hint_y = y_offset + 20
        hint_text = "[↑↓] Navegar   [Enter] Seleccionar   [ESC] Continuar"
        hint_surface = self.font.render(hint_text, True, (100, 100, 100))
        self.screen.blit(
            hint_surface,
            ((WINDOW_WIDTH - hint_surface.get_width()) // 2, hint_y)
        )
    
    def _render_options_menu(self, selected: int = 0) -> None:
        """Renderiza el menú de opciones centralizado."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS["black"])
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        # Panel central
        panel_w, panel_h = 400, 250
        panel_x = (WINDOW_WIDTH - panel_w) // 2
        panel_y = (WINDOW_HEIGHT - panel_h) // 2
        
        # Fondo del panel
        panel_surface = pygame.Surface((panel_w, panel_h))
        panel_surface.fill((20, 20, 30))
        panel_surface.set_alpha(240)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Borde del panel
        pygame.draw.rect(
            self.screen, COLORS["gray"],
            (panel_x, panel_y, panel_w, panel_h), 1
        )
        
        # Título
        title_text = "OPCIONES"
        title_surface = self.font.render(title_text, True, COLORS["white"])
        title_scaled = pygame.transform.scale(
            title_surface,
            (title_surface.get_width() * 2, title_surface.get_height() * 2)
        )
        self.screen.blit(
            title_scaled,
            ((WINDOW_WIDTH - title_scaled.get_width()) // 2, panel_y + 15)
        )
        
        # Línea decorativa
        line_y = panel_y + 15 + title_scaled.get_height() + 8
        pygame.draw.line(
            self.screen, COLORS["gray"],
            (panel_x + 20, line_y), (panel_x + panel_w - 20, line_y), 1
        )
        
        # === Opción 0: Volumen ===
        vol_y = line_y + 20
        current_vol = music_manager.get_volume()
        vol_percent = int(current_vol * 100)
        
        if selected == 0:
            vol_label = f"> Volumen: {vol_percent}%"
            vol_color = COLORS["white"]
        else:
            vol_label = f"  Volumen: {vol_percent}%"
            vol_color = COLORS["gray"]
        
        vol_surface = self.font.render(vol_label, True, vol_color)
        self.screen.blit(vol_surface, (panel_x + 30, vol_y))
        
        # Barra de volumen
        bar_y = vol_y + FONT_SIZE + 8
        bar_x = panel_x + 50
        bar_width = panel_w - 100
        bar_height = 12
        
        # Fondo de la barra
        pygame.draw.rect(
            self.screen, (40, 40, 50),
            (bar_x, bar_y, bar_width, bar_height)
        )
        # Borde de la barra
        pygame.draw.rect(
            self.screen, COLORS["gray"],
            (bar_x, bar_y, bar_width, bar_height), 1
        )
        # Relleno de la barra
        fill_width = int(bar_width * current_vol)
        if fill_width > 0:
            bar_color = COLORS["white"] if selected == 0 else COLORS["gray"]
            pygame.draw.rect(
                self.screen, bar_color,
                (bar_x + 1, bar_y + 1, fill_width - 2, bar_height - 2)
            )
        
        # Hint de ajuste si está seleccionado
        if selected == 0:
            adj_text = "[← →] Ajustar volumen"
            adj_surface = self.font.render(adj_text, True, (120, 120, 140))
            self.screen.blit(adj_surface, (panel_x + 50, bar_y + bar_height + 5))
        
        # === Opción 1: Volver ===
        back_y = bar_y + bar_height + 35
        if selected == 1:
            back_text = "> Volver <"
            back_color = COLORS["white"]
        else:
            back_text = "  Volver"
            back_color = COLORS["gray"]
        
        back_surface = self.font.render(back_text, True, back_color)
        self.screen.blit(
            back_surface,
            ((WINDOW_WIDTH - back_surface.get_width()) // 2, back_y)
        )
        
        # Hint de controles al fondo del panel
        hint_y = panel_y + panel_h - FONT_SIZE - 10
        hint_text = "[↑↓] Navegar   [Enter] Seleccionar   [ESC] Volver"
        hint_surface = self.font.render(hint_text, True, (80, 80, 90))
        self.screen.blit(
            hint_surface,
            ((WINDOW_WIDTH - hint_surface.get_width()) // 2, hint_y)
        )
    
    def _render_dialog(self) -> None:
        """Renderiza el diálogo o texto actual."""
        if dialog_manager.is_dialog():
            node = dialog_manager.get_current_node()
            if node:
                dialog_renderer.render_dialog(
                    self.screen,
                    node,
                    dialog_manager.selected_option
                )
        elif dialog_manager.is_simple_text():
            if dialog_manager.text_content:
                dialog_renderer.render_simple_text(
                    self.screen,
                    dialog_manager.text_content
                )
    
    def _draw_char_with_offset(
        self,
        x: int,
        y: int,
        char: str,
        color: Tuple[int, int, int],
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> None:
        """
        Dibuja un caracter con offset de animación.
        
        Args:
            x: Posición X base (en tiles)
            y: Posición Y base (en tiles)
            char: Caracter a dibujar
            color: Color RGB
            offset_x: Offset X en tiles (puede ser fraccionario)
            offset_y: Offset Y en tiles (puede ser fraccionario)
        """
        # Usar cache para mejor rendimiento
        cache_key = (char, color)
        if cache_key not in self._char_cache:
            self._char_cache[cache_key] = self.font.render(char, True, color)
        
        surface = self._char_cache[cache_key]
        
        # Calcular posición con offset
        pixel_x = int((x + offset_x) * TILE_SIZE)
        pixel_y = int((y + offset_y) * TILE_SIZE)
        
        # Centrar el caracter en el tile
        center_offset_x = (TILE_SIZE - surface.get_width()) // 2
        center_offset_y = (TILE_SIZE - surface.get_height()) // 2
        
        self.screen.blit(surface, (pixel_x + center_offset_x, pixel_y + center_offset_y))
    
    def _draw_char(
        self,
        x: int,
        y: int,
        char: str,
        color: Tuple[int, int, int]
    ) -> None:
        """
        Dibuja un caracter en una posición del mapa.
        
        Args:
            x: Posición X (en tiles)
            y: Posición Y (en tiles)
            char: Caracter a dibujar
            color: Color RGB
        """
        # Usar cache para mejor rendimiento
        cache_key = (char, color)
        if cache_key not in self._char_cache:
            self._char_cache[cache_key] = self.font.render(char, True, color)
        
        surface = self._char_cache[cache_key]
        pixel_x = x * TILE_SIZE
        pixel_y = y * TILE_SIZE
        
        # Centrar el caracter en el tile
        offset_x = (TILE_SIZE - surface.get_width()) // 2
        offset_y = (TILE_SIZE - surface.get_height()) // 2
        
        self.screen.blit(surface, (pixel_x + offset_x, pixel_y + offset_y))
    
    def _draw_sprite(
        self,
        x: int,
        y: int,
        sprite: pygame.Surface
    ) -> None:
        """
        Dibuja un sprite en una posición del mapa.
        
        Args:
            x: Posición X (en tiles)
            y: Posición Y (en tiles)
            sprite: Superficie de pygame con el sprite
        """
        pixel_x = x * TILE_SIZE
        pixel_y = y * TILE_SIZE
        self.screen.blit(sprite, (pixel_x, pixel_y))
    
    def _draw_sprite_with_offset(
        self,
        x: int,
        y: int,
        sprite: pygame.Surface,
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> None:
        """
        Dibuja un sprite con offset de animación.
        
        Soporta sprites más grandes que TILE_SIZE (ej: 32x32 en grid de 16x16).
        Los sprites grandes se centran horizontalmente y se anclan abajo.
        
        Args:
            x: Posición X base (en tiles)
            y: Posición Y base (en tiles)
            sprite: Superficie de pygame con el sprite
            offset_x: Offset X en tiles (puede ser fraccionario)
            offset_y: Offset Y en tiles (puede ser fraccionario)
        """
        sprite_w = sprite.get_width()
        sprite_h = sprite.get_height()
        
        if sprite_w > TILE_SIZE or sprite_h > TILE_SIZE:
            # Sprite más grande que un tile: centrar horizontalmente, anclar abajo
            pixel_x = int((x + offset_x) * TILE_SIZE) + (TILE_SIZE - sprite_w) // 2
            pixel_y = int((y + offset_y) * TILE_SIZE) + (TILE_SIZE - sprite_h)
        else:
            pixel_x = int((x + offset_x) * TILE_SIZE)
            pixel_y = int((y + offset_y) * TILE_SIZE)
        
        self.screen.blit(sprite, (pixel_x, pixel_y))
    
    def _render_interaction_prompts(
        self, dungeon: Dungeon, player: Player, visible_tiles: Set[Tuple[int, int]]
    ) -> None:
        """
        Renderiza el indicador [ESPACIO] sobre NPCs interactivos
        que estén adyacentes al jugador.
        """
        import math
        
        # Posiciones adyacentes al jugador (ortogonales + misma posición)
        adjacent_positions = [
            (player.x, player.y - 1),
            (player.x, player.y + 1),
            (player.x - 1, player.y),
            (player.x + 1, player.y),
            (player.x, player.y),
        ]
        
        # Fuente más pequeña para el indicador
        try:
            prompt_font = pygame.font.SysFont(FONT_NAME, 11, bold=True)
        except Exception:
            prompt_font = pygame.font.Font(None, 11)
        
        # Efecto de "respiración" sutil usando el tiempo
        ticks = pygame.time.get_ticks()
        pulse = int(25 * math.sin(ticks * 0.004))  # oscila ±25
        
        for ax, ay in adjacent_positions:
            if (ax, ay) not in visible_tiles:
                continue
            for entity in dungeon.entities:
                if entity.x == ax and entity.y == ay:
                    if hasattr(entity, 'interactive_text') and entity.interactive_text:
                        # Verificar que el NPC no esté muerto
                        fighter = getattr(entity, 'fighter', None)
                        if fighter and fighter.is_dead:
                            continue
                        
                        # Texto del prompt
                        prompt_text = "ESPACIO"
                        text_surface = prompt_font.render(prompt_text, True, (255, 255, 255))
                        text_w = text_surface.get_width()
                        text_h = text_surface.get_height()
                        
                        # Calcular offset extra para sprites más grandes que TILE_SIZE
                        entity_sprite = getattr(entity, 'sprite', None)
                        sprite_extra_h = 0
                        if entity_sprite and entity_sprite.get_height() > TILE_SIZE:
                            sprite_extra_h = entity_sprite.get_height() - TILE_SIZE
                        
                        # Posición: centrado sobre el sprite del NPC
                        pixel_x = entity.x * TILE_SIZE + TILE_SIZE // 2
                        pixel_y = entity.y * TILE_SIZE - sprite_extra_h - text_h - 4
                        
                        # Fondo con bordes redondeados
                        padding_x = 4
                        padding_y = 2
                        bg_rect = pygame.Rect(
                            pixel_x - text_w // 2 - padding_x,
                            pixel_y - padding_y,
                            text_w + padding_x * 2,
                            text_h + padding_y * 2
                        )
                        
                        # Fondo semi-transparente sin borde
                        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                        bg_color = (30, 30, 30, min(255, 200 + pulse))
                        bg_surface.fill(bg_color)
                        
                        self.screen.blit(bg_surface, bg_rect.topleft)
                        
                        # Texto centrado
                        self.screen.blit(
                            text_surface,
                            (pixel_x - text_w // 2, pixel_y)
                        )

    def _render_damage_numbers(self) -> None:
        """Renderiza los números de daño flotantes y textos flotantes."""
        if not self._current_animation_manager:
            return
        
        from ..systems.animation import DamageNumber
        
        # Crear fuente pequeña para números de daño (similar al tamaño de sprites)
        damage_font_size = TILE_SIZE  # 16 píxeles, igual que los sprites
        try:
            damage_font = pygame.font.SysFont(FONT_NAME, damage_font_size, bold=True)
        except:
            damage_font = pygame.font.Font(None, damage_font_size)
        
        for damage_num in self._current_animation_manager.get_damage_numbers():
            x, y = damage_num.get_position()
            
            # Convertir posición de tiles a píxeles
            pixel_x = int(x * TILE_SIZE)
            pixel_y = int(y * TILE_SIZE)
            
            # Determinar texto y color
            if damage_num.text is not None:
                # Texto flotante personalizado
                display_text = damage_num.text
                color = COLORS["weapon"]  # Gris plateado para armas
            else:
                # Número de daño estándar
                display_text = f"-{damage_num.damage}"
                
                # Color según quién ataca y si es crítico
                if damage_num.is_player_attack:
                    if damage_num.is_critical:
                        color = COLORS["message_important"]
                    else:
                        color = COLORS["white"]
                else:
                    if damage_num.is_critical:
                        color = COLORS["message_death"]
                    else:
                        color = COLORS["message_damage"]
            
            # Usar fuente ligeramente más grande para textos de rotura
            if damage_num.text is not None:
                try:
                    render_font = pygame.font.SysFont(FONT_NAME, damage_font_size + 1, bold=True)
                except:
                    render_font = pygame.font.Font(None, damage_font_size + 1)
            else:
                render_font = damage_font
            
            # Crear superficie con el texto y aplicar alpha
            text_surface = render_font.render(display_text, True, color)
            
            # Dibujar línea de tachado si el estilo lo requiere
            if damage_num.text_style == "strikethrough":
                text_w = text_surface.get_width()
                text_h = text_surface.get_height()
                line_y = text_h // 2
                pygame.draw.line(text_surface, color, (0, line_y), (text_w, line_y), 1)
            
            # Aplicar transparencia según alpha
            if damage_num.alpha < 255:
                text_surface.set_alpha(damage_num.alpha)
            
            # Centrar el texto sobre el sprite
            text_width = text_surface.get_width()
            text_height = text_surface.get_height()
            centered_x = pixel_x + (TILE_SIZE - text_width) // 2
            centered_y = pixel_y - text_height - 2  # Un poco arriba del sprite
            
            self.screen.blit(text_surface, (centered_x, centered_y))
    
    def show_splash_and_load(self) -> None:
        """
        Muestra una pantalla de carga mientras carga los assets del juego.
        
        Flujo:
        1. Carga sprites mostrando barra de progreso
        2. Espera a que el jugador pulse una tecla
        """
        # Dimensiones de la barra de progreso
        bar_width = 360
        bar_height = 12
        bar_x = (WINDOW_WIDTH - bar_width) // 2
        bar_y = WINDOW_HEIGHT // 2
        
        # ---- Fase de carga: iterar sobre sprites con progreso ----
        for loaded, total, asset_name in sprite_manager.load_sprites_iter():
            # Procesar eventos para que la ventana no se congele
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            
            progress = loaded / total if total > 0 else 1.0
            self._draw_loading_frame(
                bar_x, bar_y, bar_width, bar_height,
                progress, f"Cargando: {asset_name}..."
            )
        
        # ---- Fase de espera: mostrar "Pulsa cualquier tecla" ----
        self._draw_loading_frame(
            bar_x, bar_y, bar_width, bar_height,
            1.0, "¡Carga completa!"
        )
        pygame.time.wait(300)
        
        # Animación de parpadeo para "Pulsa cualquier tecla"
        waiting = True
        blink_timer = 0
        blink_visible = True
        
        while waiting:
            dt = self.clock.tick(FPS)
            blink_timer += dt
            if blink_timer >= 500:
                blink_visible = not blink_visible
                blink_timer = 0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                elif event.type == pygame.KEYDOWN:
                    waiting = False
            
            self._draw_loading_frame(
                bar_x, bar_y, bar_width, bar_height,
                1.0, None,
                show_prompt=blink_visible
            )
    
    def _draw_loading_frame(
        self,
        bar_x: int, bar_y: int,
        bar_width: int, bar_height: int,
        progress: float,
        status_text: Optional[str],
        show_prompt: bool = False,
    ) -> None:
        """Dibuja un frame de la pantalla de carga (fondo negro, barra blanca)."""
        self.screen.fill(COLORS["black"])
        
        cx = WINDOW_WIDTH // 2
        
        # --- Barra de progreso (centrada en pantalla) ---
        # Fondo
        pygame.draw.rect(self.screen, COLORS["darker_gray"],
                         (bar_x, bar_y, bar_width, bar_height), border_radius=3)
        # Relleno
        fill_w = int(bar_width * progress)
        if fill_w > 0:
            pygame.draw.rect(self.screen, COLORS["white"],
                             (bar_x, bar_y, fill_w, bar_height), border_radius=3)
        # Borde
        pygame.draw.rect(self.screen, COLORS["gray"],
                         (bar_x, bar_y, bar_width, bar_height), 1, border_radius=3)
        
        # --- Texto de estado debajo de la barra ---
        if status_text:
            st_surf = self.font.render(status_text, True, COLORS["dark_gray"])
            self.screen.blit(st_surf, (cx - st_surf.get_width() // 2, bar_y + bar_height + 10))
        
        # --- Prompt de continuar (parpadeo) ---
        if show_prompt:
            prompt = self.font.render("Pulsa cualquier tecla para continuar", True, COLORS["gray"])
            self.screen.blit(prompt, (cx - prompt.get_width() // 2, bar_y + bar_height + 50))
        
        pygame.display.flip()
    
    def _render_save_menu(self, selected_index: int = 0, mode: str = "select") -> None:
        """Renderiza el menú de selección de guardados."""
        from ..systems.save_manager import save_manager
        
        # Fondo
        self.screen.fill(COLORS["black"])
        
        # Título del juego
        title_lines = [
            "╔═══════════════════════════════════════╗",
            "║                                       ║",
            "║        La Mansión de Ámbar            ║",
            "║                                       ║",
            "╚═══════════════════════════════════════╝"
        ]
        
        y_offset = 80
        for line in title_lines:
            line_surface = self.font.render(line, True, COLORS["white"])
            self.screen.blit(
                line_surface,
                ((WINDOW_WIDTH - line_surface.get_width()) // 2, y_offset)
            )
            y_offset += FONT_SIZE + 2
        
        # Renderizar slots
        y_start = 200
        slot_height = 90
        spacing = 25
        
        for i, slot in enumerate(save_manager.slots):
            y_pos = y_start + i * (slot_height + spacing)
            slot_rect = pygame.Rect(200, y_pos, WINDOW_WIDTH - 400, slot_height)
            
            # Color según si está seleccionado
            if i == selected_index:
                bg_color = COLORS["darker_gray"]
                border_color = COLORS["message_important"]
            else:
                bg_color = COLORS["dark_gray"]
                border_color = COLORS["gray"]
            
            # Fondo del slot
            pygame.draw.rect(self.screen, bg_color, slot_rect)
            pygame.draw.rect(self.screen, border_color, slot_rect, 2)
            
            # Número del slot
            slot_num_text = f"Slot {slot.slot_id}"
            slot_num_surface = self.font.render(slot_num_text, True, COLORS["white"])
            self.screen.blit(slot_num_surface, (slot_rect.x + 15, slot_rect.y + 10))
            
            # Información del save
            if slot.exists:
                info_text = slot.get_display_info()
                info_surface = self.font.render(info_text, True, COLORS["gray"])
                self.screen.blit(info_surface, (slot_rect.x + 15, slot_rect.y + 35))
                
                # Indicador de que es una partida guardada
                saved_text = "Partida guardada"
                saved_surface = self.font.render(saved_text, True, COLORS["message_heal"])
                self.screen.blit(saved_surface, (slot_rect.x + 15, slot_rect.y + 55))
            else:
                # Slot vacío
                empty_text = "Slot vacío - Nueva partida"
                empty_surface = self.font.render(empty_text, True, COLORS["gray"])
                self.screen.blit(empty_surface, (slot_rect.x + 15, slot_rect.y + 35))
        
        # Instrucciones
        instructions = [
            "[↑↓] Navegar entre slots",
            "[ENTER] Seleccionar slot",
            "[DELETE] Eliminar partida guardada",
            "[ESC] Salir del juego"
        ]
        y_inst = WINDOW_HEIGHT - 100
        for inst in instructions:
            inst_surface = self.font.render(inst, True, COLORS["gray"])
            self.screen.blit(inst_surface, (WINDOW_WIDTH // 2 - 200, y_inst))
            y_inst += 22
    
    def render_save_menu_only(self, selected_index: int = 0, mode: str = "load") -> None:
        """Renderiza solo el menú de guardados (sin necesidad de dungeon/player)."""
        self._render_save_menu(selected_index, mode)
        pygame.display.flip()
    
    def tick(self, fps: int) -> float:
        """
        Limita el framerate y retorna delta time.
        
        Args:
            fps: Frames por segundo objetivo
            
        Returns:
            Tiempo transcurrido en milisegundos
        """
        return self.clock.tick(fps)
    
    def _render_console(self, console_input: str) -> None:
        """Renderiza la consola de comandos de desarrollo."""
        # Overlay semitransparente
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS["black"])
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        # Área de la consola (rectángulo en la parte inferior)
        console_height = 80
        console_y = WINDOW_HEIGHT - console_height
        console_rect = pygame.Rect(0, console_y, WINDOW_WIDTH, console_height)
        
        # Fondo de la consola
        pygame.draw.rect(self.screen, COLORS["dark_gray"], console_rect)
        pygame.draw.rect(self.screen, COLORS["white"], console_rect, 2)
        
        # Título de la consola
        title_text = "CONSOLA DE DESARROLLO (F1 para cerrar)"
        title_surface = self.font.render(title_text, True, COLORS["message_important"])
        self.screen.blit(title_surface, (10, console_y + 5))
        
        # Prompt
        prompt_text = "> "
        prompt_surface = self.font.render(prompt_text, True, COLORS["white"])
        self.screen.blit(prompt_surface, (10, console_y + 30))
        
        # Input del usuario
        input_text = console_input + "_"  # Cursor parpadeante (simple)
        input_surface = self.font.render(input_text, True, COLORS["white"])
        self.screen.blit(input_surface, (10 + prompt_surface.get_width(), console_y + 30))
        
        # Instrucciones
        help_text = "Escribe 'help' para ver comandos disponibles | ENTER para ejecutar | ESC para cerrar"
        help_surface = self.font.render(help_text, True, COLORS["gray"])
        self.screen.blit(help_surface, (10, console_y + 55))
    
    def quit(self) -> None:
        """Cierra Pygame."""
        pygame.quit()
