"""
Sistema de renderizado del juego.
Dibuja el mapa, entidades, UI y mensajes usando Pygame.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple, Set, Optional, Any
import pygame

from ..config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE, FONT_NAME, FONT_SIZE,
    COLORS, MAP_WIDTH, MAP_HEIGHT, MESSAGE_LOG_HEIGHT,
    GameState
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


class Renderer:
    """
    Sistema de renderizado principal.
    
    Maneja todo el dibujo en pantalla usando Pygame.
    """
    
    def __init__(self) -> None:
        """Inicializa el renderizador."""
        pygame.init()
        pygame.display.set_caption("Roguelike - En Busca del Amuleto de Yendor")
        
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
        
        # Cargar sprites
        sprite_manager.load_sprites()
    
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
        
        # Renderizar log de mensajes
        self._render_message_log(message_log)
        
        # Renderizar overlays según estado
        if game_state == GameState.INVENTORY:
            self._render_inventory(player, inventory_mode, cursor, scroll)
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
                # Intentar usar sprite primero
                sprite = sprite_manager.get_item_sprite(item.item_type)
                if sprite:
                    self._draw_sprite(item.x, item.y, sprite)
                else:
                    # Fallback a ASCII
                    color = COLORS.get(item.color, COLORS["white"])
                    self._draw_char(item.x, item.y, item.char, color)
    
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
        """Renderiza el log de mensajes."""
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
        
        # Mensajes
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
    
    def _render_inventory(
        self, 
        player: Player, 
        mode: str = "normal",
        cursor: int = 0,
        scroll: int = 0
    ) -> None:
        """Renderiza la pantalla de inventario con navegación."""
        # Overlay semi-transparente
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS["black"])
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        # Ventana de inventario más grande
        inv_width = 550
        inv_height = 500
        inv_x = (WINDOW_WIDTH - inv_width) // 2
        inv_y = (WINDOW_HEIGHT - inv_height) // 2
        
        pygame.draw.rect(
            self.screen,
            COLORS["darker_gray"],
            (inv_x, inv_y, inv_width, inv_height)
        )
        pygame.draw.rect(
            self.screen,
            COLORS["white"],
            (inv_x, inv_y, inv_width, inv_height),
            2
        )
        
        # Título con modo actual
        mode_text = {
            "normal": "",
            "drop": " [SOLTAR]"
        }
        title = f"=== INVENTARIO{mode_text.get(mode, '')} ==="
        title_color = COLORS["message_important"] if mode != "normal" else COLORS["white"]
        title_surface = self.font.render(title, True, title_color)
        self.screen.blit(
            title_surface,
            (inv_x + (inv_width - title_surface.get_width()) // 2, inv_y + 10)
        )
        
        # Instrucciones simplificadas
        line1 = "↑↓ Navegar    ENTER Activar    [D] Soltar    ESC Cerrar"
        
        line1_surface = self.font.render(line1, True, COLORS["gray"])
        self.screen.blit(line1_surface, (inv_x + 20, inv_y + 35))
        
        # Items del inventario
        from ..systems.inventory import Inventory
        items = Inventory.get_inventory_display(player)
        
        y_offset = inv_y + 58  # Espacio para la línea de instrucciones
        line_height = FONT_SIZE + 6
        max_visible = 12  # Items visibles
        
        if not items:
            empty_text = "El inventario está vacío."
            empty_surface = self.font.render(empty_text, True, COLORS["gray"])
            self.screen.blit(empty_surface, (inv_x + 20, y_offset))
        else:
            # Indicador de scroll arriba
            if scroll > 0:
                scroll_up = "▲ Más items arriba ▲"
                scroll_surface = self.font.render(scroll_up, True, COLORS["gray"])
                self.screen.blit(scroll_surface, (inv_x + 20, y_offset - 2))
            
            y_offset += 5
            
            # Mostrar solo los items visibles según scroll
            visible_items = items[scroll:scroll + max_visible]
            
            for i, (letter, name, equipped) in enumerate(visible_items):
                actual_index = scroll + i
                is_selected = (actual_index == cursor)
                
                # Fondo de selección
                if is_selected:
                    selection_rect = pygame.Rect(
                        inv_x + 15, 
                        y_offset - 2, 
                        inv_width - 30, 
                        line_height
                    )
                    pygame.draw.rect(self.screen, COLORS["gray"], selection_rect)
                
                # Indicador de selección
                prefix = "► " if is_selected else "  "
                
                # Color del texto
                if is_selected:
                    color = COLORS["black"]
                elif equipped:
                    color = COLORS["message_important"]
                else:
                    color = COLORS["white"]
                
                item_text = f"{prefix}{letter}) {name}"
                item_surface = self.font.render(item_text, True, color)
                self.screen.blit(item_surface, (inv_x + 20, y_offset))
                y_offset += line_height
            
            # Indicador de scroll abajo
            if scroll + max_visible < len(items):
                scroll_down = "▼ Más items abajo ▼"
                scroll_surface = self.font.render(scroll_down, True, COLORS["gray"])
                self.screen.blit(scroll_surface, (inv_x + 20, y_offset + 5))
            
            # Mostrar total de items (esquina superior derecha)
            total_text = f"[{len(items)}/26]"
            total_surface = self.font.render(total_text, True, COLORS["gray"])
            self.screen.blit(total_surface, (inv_x + inv_width - 70, inv_y + 12))
        
        # Equipamiento (más abajo)
        y_offset = inv_y + 320
        equip_title = "=== EQUIPADO ==="
        equip_surface = self.font.render(equip_title, True, COLORS["white"])
        self.screen.blit(equip_surface, (inv_x + 20, y_offset))
        
        y_offset += line_height + 5
        equipment = Inventory.get_equipment_display(player)
        
        for slot_name, item_name in equipment:
            equip_text = f"{slot_name}: {item_name}"
            color = COLORS["white"] if item_name != "---" else COLORS["gray"]
            equip_surface = self.font.render(equip_text, True, color)
            self.screen.blit(equip_surface, (inv_x + 20, y_offset))
            y_offset += line_height
    
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
        sub_text = "¡Has escapado con el Amuleto de Yendor!"
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
        """Renderiza los números de daño flotantes."""
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
            
            # Texto del daño
            damage_text = f"-{damage_num.damage}"
            
            # Color según quién ataca y si es crítico
            if damage_num.is_player_attack:
                # Daño del jugador: blanco (o amarillo si es crítico)
                if damage_num.is_critical:
                    color = COLORS["message_important"]  # Amarillo para críticos del jugador
                else:
                    color = COLORS["white"]  # Blanco para daño normal del jugador
            else:
                # Daño recibido por el jugador: rojo
                if damage_num.is_critical:
                    color = COLORS["message_death"]  # Rojo brillante para críticos
                else:
                    color = COLORS["message_damage"]  # Rojo normal
            
            # Crear superficie con el texto y aplicar alpha
            text_surface = damage_font.render(damage_text, True, color)
            
            # Aplicar transparencia según alpha
            if damage_num.alpha < 255:
                text_surface.set_alpha(damage_num.alpha)
            
            # Centrar el texto sobre el sprite
            text_width = text_surface.get_width()
            text_height = text_surface.get_height()
            centered_x = pixel_x + (TILE_SIZE - text_width) // 2
            centered_y = pixel_y - text_height - 2  # Un poco arriba del sprite
            
            self.screen.blit(text_surface, (centered_x, centered_y))
    
    def _render_save_menu(self, selected_index: int = 0, mode: str = "select") -> None:
        """Renderiza el menú de selección de guardados."""
        from ..systems.save_manager import save_manager
        
        # Fondo
        self.screen.fill(COLORS["black"])
        
        # Título del juego
        title_lines = [
            "╔═══════════════════════════════════════╗",
            "║                                       ║",
            "║      ROGUELIKE: EN BUSCA DEL          ║",
            "║       AMULETO DE YENDOR               ║",
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
    
    def render_main_menu(self) -> None:
        """Renderiza el menú principal."""
        self.screen.fill(COLORS["black"])
        
        # Título
        title_lines = [
            "╔═══════════════════════════════════════╗",
            "║                                       ║",
            "║      ROGUELIKE: EN BUSCA DEL          ║",
            "║       AMULETO DE YENDOR               ║",
            "║                                       ║",
            "╚═══════════════════════════════════════╝"
        ]
        
        y_offset = 150
        for line in title_lines:
            title_surface = self.font.render(line, True, COLORS["gold"])
            self.screen.blit(
                title_surface,
                ((WINDOW_WIDTH - title_surface.get_width()) // 2, y_offset)
            )
            y_offset += FONT_SIZE + 2
        
        # Opciones
        options = [
            "",
            "[N] Nueva Partida",
            "[C] Continuar (si hay guardado)",
            "[ESC] Salir",
            "",
            "Controles:",
            "Movimiento: Flechas / Numpad / Vi-keys (hjklyubn)",
            "[ESPACIO] Interactuar  [i] Inventario",
            "[.] Esperar turno"
        ]
        
        y_offset += 50
        for option in options:
            color = COLORS["white"] if option.startswith("[") else COLORS["gray"]
            opt_surface = self.font.render(option, True, color)
            self.screen.blit(
                opt_surface,
                ((WINDOW_WIDTH - opt_surface.get_width()) // 2, y_offset)
            )
            y_offset += FONT_SIZE + 5
        
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
