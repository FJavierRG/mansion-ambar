"""
Clase Game - Gestiona el loop principal y el estado del juego.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, Set, Tuple, List
import pygame

from .config import (
    FPS, FOV_RADIUS, GameState,
    MAP_WIDTH, MAP_HEIGHT
)
from .world.dungeon import Dungeon
from .world.lobby import Lobby
from .entities.player import Player
from .ui.renderer import Renderer
from .ui.message_log import MessageLog
from .systems.inventory import Inventory
from .systems.animation import AnimationManager
from .systems.music import music_manager
from .systems.combat import Combat
from .systems.dialog_manager import dialog_manager
from .systems.text import TextContent
from .systems.events import event_manager
from .systems.dev_commands import dev_command_manager
from .systems.save_manager import save_manager
from .systems.shop import Shop, get_merchant_shop, reset_merchant_shop


class Game:
    """
    Clase principal del juego.
    
    Gestiona el loop de juego, estados, entrada y lógica principal.
    
    Attributes:
        renderer: Sistema de renderizado
        message_log: Log de mensajes
        player: El jugador
        dungeon: Mazmorra actual
        dungeons: Diccionario de mazmorras generadas
        state: Estado actual del juego
        running: Si el juego está corriendo
        visible_tiles: Tiles actualmente visibles
    """
    
    SAVE_FILE = "roguelike_save.dat"
    
    def __init__(self) -> None:
        """Inicializa el juego."""
        self.renderer = Renderer()
        self.message_log = MessageLog()
        self.animation_manager = AnimationManager()
        
        self.player: Optional[Player] = None
        # `self.dungeon` actúa como zona actual (Lobby o Dungeon)
        self.dungeon: Optional[Dungeon] = None  # type: ignore[assignment]
        # Solo mazmorras por piso
        self.dungeons: Dict[int, Dungeon] = {}
        
        self.state = GameState.MAIN_MENU
        self.running = True
        self.visible_tiles: Set[Tuple[int, int]] = set()
        
        # Modos de inventario
        self.inventory_mode = "normal"  # normal, drop
        self.inventory_cursor = 0  # Índice del item seleccionado
        self.inventory_scroll = 0  # Offset de scroll
        self.inventory_max_visible = 12  # Items visibles a la vez
        
        # Estado de ratón para inventario grid
        self._inv_dragging = False                # ¿Arrastrando un item?
        self._inv_drag_item: Optional[Any] = None # Item siendo arrastrado
        self._inv_drag_origin_gx = 0              # Columna original en grid
        self._inv_drag_origin_gy = 0              # Fila original en grid
        self._inv_drag_mouse_pos = (0, 0)         # Posición actual del ratón
        self._inv_context_menu: Optional[dict] = None  # Menú contextual {item, pixel_x, pixel_y, options}
        self._inv_hover_item: Optional[Any] = None     # Item bajo el cursor (para tooltip)
        
        # Entidad con la que se interactuó por última vez (para eventos)
        self._last_interacted_entity: Optional[Any] = None
        # Estado FSM del NPC al inicio de la interacción (para no completar estados cambiados por acciones)
        self._last_interacted_state: Optional[str] = None
        
        # Consola de comandos de desarrollo
        self.console_input = ""  # Texto actual en la consola
        self.console_history: List[str] = []  # Historial de comandos
        self.console_history_index = -1  # Índice del historial
        
        # Menú de guardados
        self.save_menu_selected = 0  # Slot seleccionado (0-indexed)
        self.save_menu_mode = "load"  # "load" o "delete"
        self.current_save_slot: Optional[int] = None  # Slot actual de la partida (None si no hay save)
        
        # Tiempo de juego
        self.play_time_start: Optional[float] = None
        self.total_play_time = 0  # Tiempo acumulado de sesiones anteriores
        
        # Lobby persistente (se guarda entre sesiones)
        self._lobby: Optional[Lobby] = None
        
        # Tienda
        self.current_shop: Optional[Shop] = None
        self.shop_cursor: int = 0
        
        # Donación (selector numérico del Comerciante Errante)
        self.donation_amount: int = 0       # Cantidad seleccionada (0-99)
        self.donation_digit: int = 0        # 0 = unidades, 1 = decenas
        
        # Menú de pausa (cursor de navegación)
        self.pause_menu_cursor: int = 0  # 0=Continuar, 1=Opciones, 2=Salir
        
        # Menú de opciones (centralizado)
        self.options_menu_cursor: int = 0  # 0=Volumen, 1=Volver
        self.options_return_state: str = GameState.PAUSED  # Estado al que volver
        
        # Configurar controles
        self._setup_controls()
        
        # Registrar eventos del juego
        self._register_game_events()
    
    def _setup_controls(self) -> None:
        """Configura los mapeos de teclas."""
        # Movimiento con flechas
        self.move_keys = {
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
        }
        
        # Movimiento con numpad
        self.numpad_keys = {
            pygame.K_KP7: (-1, -1),
            pygame.K_KP8: (0, -1),
            pygame.K_KP9: (1, -1),
            pygame.K_KP4: (-1, 0),
            pygame.K_KP6: (1, 0),
            pygame.K_KP1: (-1, 1),
            pygame.K_KP2: (0, 1),
            pygame.K_KP3: (1, 1),
        }
        
        # Movimiento con vi-keys
        self.vi_keys = {
            pygame.K_h: (-1, 0),
            pygame.K_j: (0, 1),
            pygame.K_k: (0, -1),
            pygame.K_l: (1, 0),
            pygame.K_y: (-1, -1),
            pygame.K_u: (1, -1),
            pygame.K_b: (-1, 1),
            pygame.K_n: (1, 1),
        }
    
    def run(self) -> None:
        """Loop principal del juego."""
        # Pantalla de splash: carga assets y espera input del jugador
        self.renderer.show_splash_and_load()
        
        while self.running:
            if self.state == GameState.MAIN_MENU:
                self._handle_main_menu()
            else:
                self._handle_game_loop()
        
        # Detener todos los sonidos antes de cerrar
        music_manager.stop_all()
        self.renderer.quit()
    
    def _handle_main_menu(self) -> None:
        """Maneja el menú principal (ahora muestra directamente los slots de guardado)."""
        # Actualizar información de slots
        save_manager.refresh_slots()
        
        # Renderizar menú de slots
        self.renderer.render_save_menu_only(self.save_menu_selected, "select")
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_save_menu_input(event.key)
        
        self.renderer.tick(FPS)
    
    def _handle_game_loop(self) -> None:
        """Loop principal cuando se está jugando."""
        # Actualizar animaciones
        self.animation_manager.update()
        
        # Procesar eventos (pero no durante animaciones para que se vean)
        if not self.animation_manager.has_active_animations():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.player and self.dungeon and self.current_save_slot:
                        self._save_game(self.current_save_slot, silent=True)
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_input(event.key)
                elif event.type == pygame.TEXTINPUT and self.state == GameState.CONSOLE:
                    self.console_input += event.text
                elif event.type == pygame.MOUSEWHEEL:
                    self._handle_mousewheel(event.y)
                # ── Eventos de ratón para inventario grid ──
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == GameState.INVENTORY:
                    self._handle_inventory_mouse_down(event.button, event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and self.state == GameState.INVENTORY:
                    self._handle_inventory_mouse_up(event.button, event.pos)
                elif event.type == pygame.MOUSEMOTION and self.state == GameState.INVENTORY:
                    self._handle_inventory_mouse_motion(event.pos)
        else:
            # Durante animaciones, solo procesar quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.player and self.dungeon and self.current_save_slot:
                        self._save_game(self.current_save_slot, silent=True)
                    self.running = False
        
        # Renderizar
        if self.dungeon and self.player:
            self.renderer.render(
                self.dungeon,
                self.player,
                self.visible_tiles,
                self.message_log,
                self.state,
                self.inventory_mode,
                self.inventory_cursor,
                self.inventory_scroll,
                self.animation_manager,
                self.console_input,
                shop=self.current_shop,
                shop_cursor=self.shop_cursor,
                pause_cursor=self.pause_menu_cursor,
                options_cursor=self.options_menu_cursor,
                donation_amount=self.donation_amount,
                donation_digit=self.donation_digit,
                inv_drag_item=self._inv_drag_item if self._inv_dragging else None,
                inv_drag_mouse_pos=self._inv_drag_mouse_pos,
                inv_context_menu=self._inv_context_menu,
                inv_hover_item=self._inv_hover_item,
            )
        
        self.renderer.tick(FPS)
    
    def _handle_input(self, key: int) -> None:
        """
        Procesa la entrada del teclado.
        
        Args:
            key: Código de tecla de Pygame
        """
        if self.state == GameState.PLAYING:
            self._handle_playing_input(key)
        elif self.state == GameState.INVENTORY:
            self._handle_inventory_input(key)
        elif self.state == GameState.DEAD:
            self._handle_dead_input(key)
        elif self.state == GameState.VICTORY:
            self._handle_victory_input(key)
        elif self.state == GameState.PAUSED:
            self._handle_pause_input(key)
        elif self.state == GameState.DIALOG:
            self._handle_dialog_input(key)
        elif self.state == GameState.CONSOLE:
            self._handle_console_input(key)
        elif self.state == GameState.SAVE_MENU:
            self._handle_save_menu_input(key)
        elif self.state == GameState.SHOP:
            self._handle_shop_input(key)
        elif self.state == GameState.DONATION:
            self._handle_donation_input(key)
        elif self.state == GameState.OPTIONS:
            self._handle_options_input(key)
    
    def _handle_mousewheel(self, y: int) -> None:
        """
        Maneja el scroll de la rueda del ratón para el log de mensajes.
        
        Args:
            y: Dirección del scroll (positivo = arriba, negativo = abajo)
        """
        if y > 0:
            self.message_log.scroll_up(2)
        elif y < 0:
            self.message_log.scroll_down(2)
    
    def _handle_playing_input(self, key: int) -> None:
        """Maneja la entrada durante el juego."""
        player_acted = False
        
        # Movimiento
        direction = None
        if key in self.move_keys:
            direction = self.move_keys[key]
        elif key in self.numpad_keys:
            direction = self.numpad_keys[key]
        elif key in self.vi_keys:
            direction = self.vi_keys[key]
        
        if direction:
            player_acted = self._player_move_or_attack(*direction)
        
        # Esperar turno
        elif key == pygame.K_PERIOD or key == pygame.K_KP5:
            player_acted = True
            self.message_log.add("Esperas un turno.")
        
        # Abrir inventario
        elif key == pygame.K_i:
            self.state = GameState.INVENTORY
        
        # ESPACIO: Interacción universal (recoger, hablar, escaleras)
        elif key == pygame.K_SPACE:
            player_acted = self._handle_space_interact()
        
        # Abrir consola de comandos (F1)
        elif key == pygame.K_F1:
            self.state = GameState.CONSOLE
            self.console_input = ""
        
        # Pausa
        elif key == pygame.K_ESCAPE:
            self.state = GameState.PAUSED
        
        # Scroll del log de mensajes con PageUp/PageDown
        if key == pygame.K_PAGEUP:
            self.message_log.scroll_up(3)
        elif key == pygame.K_PAGEDOWN:
            self.message_log.scroll_down(3)
        
        # Si el jugador actuó, ejecutar turno de enemigos
        if player_acted:
            self._enemy_turn()
            self._update_fov()
            self.player.update()
            
            # Verificar eventos automáticos después de acciones del jugador
            triggered = event_manager.check_and_trigger_events(self.player, self.dungeon)
            if triggered:
                # Si algún evento se activó, mostrar mensaje
                for event_id in triggered:
                    event = event_manager.events.get(event_id)
                    if event:
                        self.message_log.add(f"Evento: {event.name}", "message_important")
    
    def _handle_inventory_input(self, key: int) -> None:
        """Maneja la entrada de teclado en el inventario (solo ESC/I para cerrar)."""
        # Cerrar inventario
        if key in (pygame.K_ESCAPE, pygame.K_i):
            self._close_inventory()
            return

    def _close_inventory(self) -> None:
        """Cierra el inventario y limpia todo el estado de ratón."""
        # Si estamos arrastrando un item, devolverlo al grid
        if self._inv_dragging and self._inv_drag_item is not None:
            grid_inv = self.player.grid_inventory
            if not grid_inv.place(self._inv_drag_item, self._inv_drag_origin_gx, self._inv_drag_origin_gy):
                grid_inv.auto_place(self._inv_drag_item)
        
        self.inventory_mode = "normal"
        self.inventory_cursor = 0
        self.inventory_scroll = 0
        self._inv_dragging = False
        self._inv_drag_item = None
        self._inv_context_menu = None
        self._inv_hover_item = None
        self.state = GameState.PLAYING

    # ── Manejo de ratón para inventario grid ──────────────────────

    def _handle_inventory_mouse_down(self, button: int, pos: tuple) -> None:
        """
        Maneja click del ratón en el inventario.
        
        button=1: Click izquierdo → iniciar drag / cerrar menú contextual
        button=3: Click derecho → abrir menú contextual
        """
        mx, my = pos

        # Click izquierdo
        if button == 1:
            # Si hay menú contextual abierto, comprobar si hacemos click en una opción
            if self._inv_context_menu is not None:
                option_clicked = self._get_context_menu_option_at(mx, my)
                if option_clicked is not None:
                    self._execute_context_action(option_clicked)
                # Siempre cerrar el menú contextual con click izquierdo
                self._inv_context_menu = None
                return

            # Identificar item bajo el cursor
            grid_inv = self.player.grid_inventory
            gx, gy = self.renderer.pixel_to_grid_cell(mx, my)
            if gx >= 0 and gy >= 0:
                item = grid_inv.get_item_at(gx, gy)
                if item is not None:
                    # Iniciar drag
                    self._inv_dragging = True
                    self._inv_drag_item = item
                    pos_info = grid_inv.get_item_position(item)
                    if pos_info:
                        self._inv_drag_origin_gx, self._inv_drag_origin_gy = pos_info
                    self._inv_drag_mouse_pos = pos
                    # Sacar el item del grid temporalmente para que pueda recolocarse
                    grid_inv.remove(item)
                    return

        # Click derecho
        elif button == 3:
            # Cerrar menú existente si hay uno
            self._inv_context_menu = None

            grid_inv = self.player.grid_inventory
            gx, gy = self.renderer.pixel_to_grid_cell(mx, my)
            if gx >= 0 and gy >= 0:
                item = grid_inv.get_item_at(gx, gy)
                if item is not None:
                    self._open_context_menu(item, mx, my)

    def _handle_inventory_mouse_up(self, button: int, pos: tuple) -> None:
        """
        Maneja soltar el ratón en el inventario.
        
        button=1: Fin de drag → colocar item o soltarlo
        """
        if button != 1 or not self._inv_dragging:
            return

        mx, my = pos
        item = self._inv_drag_item
        if item is None:
            self._inv_dragging = False
            return

        grid_inv = self.player.grid_inventory

        # ¿Soltamos dentro del grid?
        on_grid = self.renderer.is_pixel_on_grid(mx, my)

        if on_grid:
            # Calcular celda destino (centrada en el item)
            gx, gy = self.renderer.pixel_to_grid_cell(mx, my)
            # Ajustar para que la esquina superior izq del item quede bien
            w = getattr(item, 'grid_width', 1)
            h = getattr(item, 'grid_height', 1)
            target_gx = max(0, min(gx - w // 2, grid_inv.width - w))
            target_gy = max(0, min(gy - h // 2, grid_inv.height - h))

            if grid_inv.can_place(item, target_gx, target_gy):
                grid_inv.place(item, target_gx, target_gy)
            else:
                # Intentar posición exacta donde soltamos
                if gx >= 0 and gy >= 0 and grid_inv.can_place(item, gx, gy):
                    grid_inv.place(item, gx, gy)
                else:
                    # No cabe → devolver a posición original
                    if not grid_inv.place(item, self._inv_drag_origin_gx, self._inv_drag_origin_gy):
                        # Último recurso: auto-place
                        if not grid_inv.auto_place(item):
                            # Imposible colocar → soltar al suelo
                            from roguelike.systems.inventory import Inventory
                            msgs = Inventory.drop_item_direct(self.player, self.dungeon, item)
                            self.message_log.add_multiple(msgs)
        else:
            # Soltamos fuera del grid → TIRAR el item
            on_window = self.renderer.is_pixel_on_inventory_window(mx, my)
            if not on_window:
                # Fuera de la ventana de inventario = tirar item
                # Verificar si está equipado
                is_equipped = any(eq is item for eq in self.player.equipped.values() if eq is not None)
                if is_equipped:
                    self.message_log.add(f"Primero debes desequipar {item.name}.")
                    # Devolver al grid
                    if not grid_inv.place(item, self._inv_drag_origin_gx, self._inv_drag_origin_gy):
                        grid_inv.auto_place(item)
                else:
                    # Tirar al suelo
                    self.dungeon.add_item(item, self.player.x, self.player.y)
                    self.message_log.add(f"Sueltas {item.name}.")
            else:
                # Dentro de la ventana pero fuera del grid → devolver
                if not grid_inv.place(item, self._inv_drag_origin_gx, self._inv_drag_origin_gy):
                    grid_inv.auto_place(item)

        # Limpiar estado de drag
        self._inv_dragging = False
        self._inv_drag_item = None

    def _handle_inventory_mouse_motion(self, pos: tuple) -> None:
        """
        Maneja el movimiento del ratón en el inventario.
        Actualiza posición del drag y tooltip hover.
        """
        mx, my = pos
        self._inv_drag_mouse_pos = pos

        # Si no estamos arrastrando, actualizar hover
        if not self._inv_dragging:
            grid_inv = self.player.grid_inventory
            gx, gy = self.renderer.pixel_to_grid_cell(mx, my)
            if gx >= 0 and gy >= 0:
                self._inv_hover_item = grid_inv.get_item_at(gx, gy)
            else:
                self._inv_hover_item = None

    # ── Menú contextual ──────────────────────────────────────────

    def _open_context_menu(self, item, px: int, py: int) -> None:
        """Abre el menú contextual para un item."""
        options = []

        # Verificar si está equipado
        is_equipped = any(eq is item for eq in self.player.equipped.values() if eq is not None)

        if is_equipped:
            slot = getattr(item, 'slot', None)
            if slot:
                options.append({"label": "Desequipar", "action": "unequip", "slot": slot})
        else:
            # Equipable
            if hasattr(item, 'slot') and item.slot:
                options.append({"label": "Equipar", "action": "equip"})
            # Usable
            if hasattr(item, 'usable') and item.usable:
                options.append({"label": "Usar", "action": "use"})

        # Siempre se puede soltar (si no equipado)
        if not is_equipped:
            options.append({"label": "Soltar", "action": "drop"})

        if options:
            self._inv_context_menu = {
                "item": item,
                "pixel_x": px,
                "pixel_y": py,
                "options": options,
            }

    def _get_context_menu_option_at(self, mx: int, my: int):
        """Retorna la opción del menú contextual bajo el ratón, o None."""
        if self._inv_context_menu is None:
            return None

        cm_x = self._inv_context_menu.get("pixel_x", 0)
        cm_y = self._inv_context_menu.get("pixel_y", 0)
        options = self._inv_context_menu.get("options", [])
        cm_w = 140
        cm_line_h = 28

        # Ajustar posición (misma lógica que el renderer)
        from roguelike.config import WINDOW_WIDTH, WINDOW_HEIGHT
        cm_h = len(options) * cm_line_h + 8
        if cm_x + cm_w > WINDOW_WIDTH:
            cm_x = WINDOW_WIDTH - cm_w - 4
        if cm_y + cm_h > WINDOW_HEIGHT:
            cm_y = WINDOW_HEIGHT - cm_h - 4

        for i, opt in enumerate(options):
            opt_y = cm_y + 4 + i * cm_line_h
            if cm_x <= mx <= cm_x + cm_w and opt_y <= my <= opt_y + cm_line_h:
                return opt
        return None

    def _execute_context_action(self, option: dict) -> None:
        """Ejecuta una acción del menú contextual."""
        if self._inv_context_menu is None:
            return

        item = self._inv_context_menu.get("item")
        if item is None:
            return

        action = option.get("action")
        messages = []
        close_inventory = False
        consume_turn = False

        if action == "unequip":
            slot = option.get("slot")
            if slot:
                from roguelike.systems.inventory import Inventory
                messages = Inventory.unequip_item(self.player, slot)

        elif action == "equip":
            # Necesitamos el índice del item
            items = self.player.grid_inventory.get_all_items()
            try:
                idx = items.index(item)
            except ValueError:
                idx = -1
            if idx >= 0:
                from roguelike.systems.inventory import Inventory
                messages = Inventory.equip_item(self.player, idx)

        elif action == "use":
            items = self.player.grid_inventory.get_all_items()
            try:
                idx = items.index(item)
            except ValueError:
                idx = -1
            if idx >= 0:
                from roguelike.systems.inventory import Inventory
                messages = Inventory.use_item(self.player, idx)
                close_inventory = True
                consume_turn = True

        elif action == "drop":
            from roguelike.systems.inventory import Inventory
            messages = Inventory.drop_item_direct(self.player, self.dungeon, item)

        self.message_log.add_multiple(messages)

        # Verificar si el jugador murió (p.ej. poción de veneno)
        if self.player.fighter.is_dead:
            self._handle_player_death()
        elif close_inventory:
            self.state = GameState.PLAYING
            if consume_turn:
                self._enemy_turn()
                self._update_fov()

    def _find_grid_neighbor(self, dx: int, dy: int) -> int:
        """
        Encuentra el índice del item vecino más cercano en la dirección (dx, dy)
        dentro del grid de inventario.
        
        Usa las posiciones reales del grid para navegación espacial 2D.
        Si no hay vecino en esa dirección, cicla al siguiente/anterior item.
        
        Returns:
            Nuevo índice del cursor
        """
        grid_inv = self.player.grid_inventory
        items = grid_inv.get_all_items()
        if not items:
            return 0
        
        n = len(items)
        cur = max(0, min(self.inventory_cursor, n - 1))
        current_item = items[cur]
        
        # Obtener posición del item actual en el grid
        cur_pos = grid_inv.get_item_position(current_item)
        if cur_pos is None:
            # Fallback: simple ciclo
            return (cur + (1 if dy > 0 or dx > 0 else -1)) % n
        
        cur_gx, cur_gy = cur_pos
        # Centro del item actual
        cur_w = getattr(current_item, 'grid_width', 1)
        cur_h = getattr(current_item, 'grid_height', 1)
        cur_cx = cur_gx + cur_w / 2.0
        cur_cy = cur_gy + cur_h / 2.0
        
        best_idx = None
        best_dist = float('inf')
        
        for i, item in enumerate(items):
            if i == cur:
                continue
            pos = grid_inv.get_item_position(item)
            if pos is None:
                continue
            igx, igy = pos
            iw = getattr(item, 'grid_width', 1)
            ih = getattr(item, 'grid_height', 1)
            icx = igx + iw / 2.0
            icy = igy + ih / 2.0
            
            # Verificar que el item está en la dirección correcta
            diff_x = icx - cur_cx
            diff_y = icy - cur_cy
            
            # Producto escalar con la dirección
            dot = diff_x * dx + diff_y * dy
            if dot <= 0:
                continue  # Item no está en la dirección deseada
            
            # Distancia ponderada: penalizar desviación perpendicular
            if dx != 0:  # Movimiento horizontal
                dist = abs(diff_x) + abs(diff_y) * 2.0
            else:  # Movimiento vertical
                dist = abs(diff_y) + abs(diff_x) * 2.0
            
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        
        if best_idx is not None:
            return best_idx
        
        # Si no hay vecino en esa dirección, ciclar simple
        if dy > 0 or dx > 0:
            return (cur + 1) % n
        else:
            return (cur - 1) % n
    
    def _execute_inventory_action(self, index: int) -> None:
        """Ejecuta la acción del inventario sobre el item seleccionado.
        
        En modo 'drop' suelta el item. En modo 'normal' activa
        inteligentemente según el tipo:
          - Item equipado → lo desequipa
          - Item equipable (arma/armadura) → lo equipa
          - Item usable (pociones) → lo usa
        """
        item = self.player.get_inventory_item(index)
        
        if not item:
            self.message_log.add("No hay item en esa posición.")
            return
        
        messages = []
        close_inventory = False  # Solo cerrar en ciertos casos
        consume_turn = False  # Solo consumir turno en ciertos casos
        
        if self.inventory_mode == "drop":
            messages = Inventory.drop_item(self.player, self.dungeon, index)
            # Soltar NO cierra inventario
            close_inventory = False
            consume_turn = False
            
        else:
            # Activación inteligente: detectar qué hacer con el item
            is_equipped = any(
                equipped is item
                for equipped in self.player.equipped.values()
                if equipped is not None
            )
            
            if is_equipped:
                # Ya equipado → desequipar
                slot = item.slot if hasattr(item, 'slot') else None
                if slot:
                    messages = Inventory.unequip_item(self.player, slot)
                else:
                    messages = ["No puedes desequipar ese item."]
                close_inventory = False
                consume_turn = False
                
            elif hasattr(item, 'slot') and item.slot:
                # Equipable → equipar
                messages = Inventory.equip_item(self.player, index)
                close_inventory = False
                consume_turn = False
                
            elif hasattr(item, 'usable') and item.usable:
                # Usable (pociones, etc.) → usar
                messages = Inventory.use_item(self.player, index)
                close_inventory = True
                consume_turn = True
                
            else:
                messages = [f"No puedes activar {item.name}."]
        
        self.message_log.add_multiple(messages)
        self.inventory_mode = "normal"
        
        # Ajustar cursor si se eliminó un item
        inventory_size = len(self.player.inventory)
        if self.inventory_cursor >= inventory_size and inventory_size > 0:
            self.inventory_cursor = inventory_size - 1
        if inventory_size == 0:
            self.inventory_cursor = 0
        
        # Ajustar scroll si es necesario
        if self.inventory_cursor < self.inventory_scroll:
            self.inventory_scroll = self.inventory_cursor
        
        # Verificar si el jugador murió
        if self.player.fighter.is_dead:
            self._handle_player_death()
        elif close_inventory:
            self.state = GameState.PLAYING
            if consume_turn:
                self._enemy_turn()
                self._update_fov()
    
    def _handle_player_death(self) -> None:
        """
        Maneja la muerte del jugador.
        
        Enfoque: en el instante de morir se aplican TODAS las consecuencias
        (desbloqueos, respawn lógico en lobby, auto-save). Así el save en
        disco SIEMPRE refleja el estado post-muerte. La pantalla de muerte
        es puramente visual; si el jugador cierra el juego en cualquier
        momento, al reabrir estará en el lobby con el progreso correcto.
        """
        self.state = GameState.DEAD
        
        # Fadeout agresivo del tema de la mazmorra
        music_manager.stop_aggressive(fade_ms=200)
        
        # Reproducir sonido de muerte
        music_manager.play_sound("sound-dead.mp3", volume=0.8)
        
        # === Aplicar consecuencias de muerte inmediatamente ===
        
        # Desbloqueos por causa de muerte (ej: morir por veneno → alquimista)
        death_cause = getattr(self.player, 'death_cause', None)
        if death_cause == "poison":
            alchemist_was_unlocked = event_manager.is_event_triggered("alchemist_unlocked")
            event_manager.triggered_events.add("alchemist_unlocked")
            if alchemist_was_unlocked:
                event_manager.triggered_events.add("alchemist_second_poison")
                event_manager.triggered_events.add("alchemist_greeting_done")
        
        # Respawn lógico en el lobby (crea jugador nuevo, preserva meta-progreso)
        # La pantalla de muerte sigue mostrándose, pero el estado real ya es lobby
        self._respawn_in_lobby()
        
        # Forzar estado DEAD de nuevo (el respawn lo cambia a PLAYING)
        # La pantalla de muerte es solo visual; el save ya está correcto
        self.state = GameState.DEAD
        
        # _start_in_lobby arrancó la música del lobby y paró los sonidos.
        # En la pantalla de muerte no queremos música de lobby, solo el efecto.
        music_manager.stop_all()
        music_manager.play_sound("sound-dead.mp3", volume=0.8)
    
    def _handle_dead_input(self, key: int) -> None:
        """
        Maneja la entrada cuando el jugador está muerto.
        
        La pantalla de muerte es puramente visual. Todo el trabajo real
        (desbloqueos, respawn, auto-save) ya se hizo en _handle_player_death.
        Aquí solo transicionamos al estado PLAYING que ya está preparado.
        """
        if key == pygame.K_r:
            # Detener sonido de muerte y transicionar al lobby (ya preparado)
            music_manager.stop_all_sounds()
            
            # Arrancar música del lobby (no se inició antes para no sonar en la pantalla de muerte)
            if music_manager.load_music("lobby-music.mp3"):
                music_manager.set_volume(0.4)
                music_manager.play(loops=-1, fade_ms=1500)
            
            self.state = GameState.PLAYING
        elif key == pygame.K_ESCAPE:
            # Cerrar juego — el save ya está correcto (se guardó al morir)
            music_manager.stop_all()
            self.running = False
    
    def _handle_victory_input(self, key: int) -> None:
        """Maneja la entrada en la victoria."""
        # NOTA: Esta función ya no se usa porque eliminamos la lógica de VICTORY del colgante
        # Pero la mantenemos por si acaso hay otros casos de victoria en el futuro
        if key == pygame.K_r:
            # Obtener el slot actual
            current_slot = self.current_save_slot or 1
            if save_manager.delete_save(current_slot):
                event_manager.clear_all()  # Resetear eventos al borrar el save
                self.current_save_slot = None
            self._new_game()
        elif key == pygame.K_ESCAPE:
            # No borramos el save al salir, solo cerramos
            self.running = False
    
    def _handle_pause_input(self, key: int) -> None:
        """Maneja la entrada en el menú de pausa."""
        pause_options_count = 3  # Continuar, Opciones, Salir
        
        if key == pygame.K_ESCAPE:
            # ESC siempre vuelve a jugar
            self.pause_menu_cursor = 0
            self.state = GameState.PLAYING
        elif key == pygame.K_UP or key == pygame.K_k:
            self.pause_menu_cursor = (self.pause_menu_cursor - 1) % pause_options_count
            music_manager.play_sound("UI-move.mp3", volume=0.2)
        elif key == pygame.K_DOWN or key == pygame.K_j:
            self.pause_menu_cursor = (self.pause_menu_cursor + 1) % pause_options_count
            music_manager.play_sound("UI-move.mp3", volume=0.2)
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER or key == pygame.K_SPACE:
            music_manager.play_sound("UI-select.mp3", volume=0.3)
            if self.pause_menu_cursor == 0:
                # Continuar
                self.pause_menu_cursor = 0
                self.state = GameState.PLAYING
            elif self.pause_menu_cursor == 1:
                # Opciones
                self.options_menu_cursor = 0
                self.options_return_state = GameState.PAUSED
                self.state = GameState.OPTIONS
            elif self.pause_menu_cursor == 2:
                # Salir
                self.running = False
    
    def _handle_options_input(self, key: int) -> None:
        """Maneja la entrada en el menú de opciones (centralizado)."""
        options_count = 2  # Volumen, Volver
        
        if key == pygame.K_ESCAPE:
            # Volver al menú anterior
            self.options_menu_cursor = 0
            self.state = self.options_return_state
        elif key == pygame.K_UP or key == pygame.K_k:
            self.options_menu_cursor = (self.options_menu_cursor - 1) % options_count
            music_manager.play_sound("UI-move.mp3", volume=0.2)
        elif key == pygame.K_DOWN or key == pygame.K_j:
            self.options_menu_cursor = (self.options_menu_cursor + 1) % options_count
            music_manager.play_sound("UI-move.mp3", volume=0.2)
        elif key == pygame.K_LEFT or key == pygame.K_h:
            if self.options_menu_cursor == 0:
                # Bajar volumen
                new_vol = max(0.0, music_manager.get_volume() - 0.05)
                music_manager.set_volume(new_vol)
        elif key == pygame.K_RIGHT or key == pygame.K_l:
            if self.options_menu_cursor == 0:
                # Subir volumen
                new_vol = min(1.0, music_manager.get_volume() + 0.05)
                music_manager.set_volume(new_vol)
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER or key == pygame.K_SPACE:
            if self.options_menu_cursor == 1:
                # Volver
                music_manager.play_sound("UI-select.mp3", volume=0.3)
                self.options_menu_cursor = 0
                self.state = self.options_return_state
    
    def _handle_dialog_input(self, key: int) -> None:
        """Maneja la entrada durante diálogos/textos."""
        if dialog_manager.is_dialog():
            # Navegación en diálogo
            if key == pygame.K_UP or key == pygame.K_k:
                dialog_manager.select_previous_option()
            elif key == pygame.K_DOWN or key == pygame.K_j:
                dialog_manager.select_next_option()
            elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER or key == pygame.K_SPACE:
                # Seleccionar opción
                print("[DEBUG] Enter/Espacio presionado en diálogo")
                dialog_continues = dialog_manager.select_option(self.player, self.dungeon)
                print(f"[DEBUG] dialog_continues = {dialog_continues}")
                if not dialog_continues:
                    # El diálogo se cerró (select_option ya llamó a close() internamente)
                    print("[DEBUG] Diálogo cerrado, llamando _on_dialog_closed()")
                    self._on_dialog_closed()
                    print("[DEBUG] _on_dialog_closed() completado")
                    # Verificar si hay más mensajes activos DESPUÉS de procesar la cola
                    is_active = dialog_manager.is_active()
                    print(f"[DEBUG] dialog_manager.is_active() = {is_active}")
                    if is_active:
                        # Hay algo activo (de la cola), asegurar que el estado sea DIALOG
                        print("[DEBUG] Hay mensajes activos, manteniendo estado DIALOG")
                        self.state = GameState.DIALOG
                    elif getattr(self.player, '_pending_shop', False):
                        # El diálogo del comerciante señaló abrir la tienda
                        self.player._pending_shop = False
                        self._open_shop()
                    elif getattr(self.player, '_pending_donation', False):
                        # El diálogo del errante señaló abrir el selector de donación
                        self.player._pending_donation = False
                        self._open_donation()
                    else:
                        # No hay más mensajes, volver al juego inmediatamente
                        print("[DEBUG] No hay mensajes, cambiando a estado PLAYING")
                        self.state = GameState.PLAYING
                        # Asegurar que el dialog_manager esté completamente cerrado
                        if dialog_manager.is_active():
                            print("[DEBUG] Dialog aún activo, forzando cierre")
                            dialog_manager.close()
                            self.state = GameState.PLAYING
                    print(f"[DEBUG] Estado final del juego: {self.state}")
                # Si el diálogo continúa, no hacer nada (ya está en modo DIALOG)
            elif key == pygame.K_ESCAPE:
                # Cerrar diálogo
                self._on_dialog_closed()
                # Cerrar el diálogo y procesar cola
                dialog_manager.close()
                # Verificar si hay más mensajes activos DESPUÉS de procesar la cola
                if dialog_manager.is_active():
                    # Hay algo activo (de la cola), asegurar que el estado sea DIALOG
                    self.state = GameState.DIALOG
                else:
                    # No hay más mensajes, volver al juego inmediatamente
                    self.state = GameState.PLAYING
        
        elif dialog_manager.is_simple_text():
            # Cerrar texto simple y avanzar a siguiente si existe
            if key == pygame.K_ESCAPE or key == pygame.K_RETURN or key == pygame.K_KP_ENTER or key == pygame.K_SPACE:
                self._on_dialog_closed()
                dialog_manager.close()
                # Verificar si hay más mensajes activos DESPUÉS de procesar la cola
                if dialog_manager.is_active():
                    # Hay algo activo (de la cola), asegurar que el estado sea DIALOG
                    self.state = GameState.DIALOG
                else:
                    # No hay más mensajes, volver al juego inmediatamente
                    self.state = GameState.PLAYING
    
    def _open_shop(self) -> None:
        """
        Abre la tienda del comerciante.
        
        Configura el estado SHOP y carga la tienda correspondiente.
        """
        self.current_shop = get_merchant_shop()
        self.shop_cursor = 0
        self.state = GameState.SHOP
        music_manager.play_sound("UI-select.mp3", volume=0.3)
    
    def _handle_shop_input(self, key: int) -> None:
        """
        Maneja la entrada durante la tienda.
        
        Controles:
            ↑/↓: Navegar items
            ENTER: Comprar item seleccionado
            ESC: Cerrar tienda
        """
        if not self.current_shop:
            self.state = GameState.PLAYING
            return
        
        item_count = self.current_shop.get_item_count()
        
        if key == pygame.K_UP or key == pygame.K_k:
            if item_count > 0:
                self.shop_cursor = (self.shop_cursor - 1) % item_count
                music_manager.play_sound("UI-move.mp3", volume=0.2)
        
        elif key == pygame.K_DOWN or key == pygame.K_j:
            if item_count > 0:
                self.shop_cursor = (self.shop_cursor + 1) % item_count
                music_manager.play_sound("UI-move.mp3", volume=0.2)
        
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if item_count > 0:
                success, message = self.current_shop.buy_item(self.player, self.shop_cursor)
                self.message_log.add(
                    message,
                    "message_important" if success else "message_death"
                )
                if success:
                    music_manager.play_sound("UI-select.mp3", volume=0.4)
                    # Ajustar cursor si se eliminó un item agotado
                    new_count = self.current_shop.get_item_count()
                    if new_count == 0:
                        # Tienda vacía: cerrar automáticamente
                        self.current_shop = None
                        self.shop_cursor = 0
                        self.state = GameState.PLAYING
                        return
                    elif self.shop_cursor >= new_count:
                        self.shop_cursor = new_count - 1
        
        elif key == pygame.K_ESCAPE:
            self.current_shop = None
            self.shop_cursor = 0
            self.state = GameState.PLAYING
    
    def _open_donation(self) -> None:
        """Abre el selector de donación de oro."""
        self.donation_amount = 0
        self.donation_digit = 0  # Empezar en unidades
        self.state = GameState.DONATION
        music_manager.play_sound("UI-select.mp3", volume=0.3)
    
    def _handle_donation_input(self, key: int) -> None:
        """
        Maneja la entrada durante el selector de donación.
        
        Controles:
            ←/→: Cambiar entre dígito de decenas y unidades
            ↑/↓: Incrementar/decrementar el dígito seleccionado
            ENTER: Confirmar donación
            ESC: Cancelar
        """
        max_donation = min(99, self.player.gold)
        
        if key == pygame.K_LEFT:
            self.donation_digit = 1  # Decenas
            music_manager.play_sound("UI-move.mp3", volume=0.2)
        
        elif key == pygame.K_RIGHT:
            self.donation_digit = 0  # Unidades
            music_manager.play_sound("UI-move.mp3", volume=0.2)
        
        elif key == pygame.K_UP:
            step = 10 if self.donation_digit == 1 else 1
            self.donation_amount = min(max_donation, self.donation_amount + step)
            music_manager.play_sound("UI-move.mp3", volume=0.2)
        
        elif key == pygame.K_DOWN:
            step = 10 if self.donation_digit == 1 else 1
            self.donation_amount = max(0, self.donation_amount - step)
            music_manager.play_sound("UI-move.mp3", volume=0.2)
        
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if self.donation_amount > 0:
                # Ejecutar la donación
                from .systems.events import event_manager
                from .systems.shop import refresh_merchant_shop, get_unlocked_count
                
                current_total = event_manager.get_data("merchant_donated_total", 0)
                old_unlocked = get_unlocked_count(current_total)
                
                self.player.gold -= self.donation_amount
                new_total = current_total + self.donation_amount
                event_manager.set_data("merchant_donated_total", new_total)
                refresh_merchant_shop()
                
                new_unlocked = get_unlocked_count(new_total)
                
                self.message_log.add(
                    f"Has donado {self.donation_amount} oro al mercader.",
                    "message_important"
                )
                
                # Si se desbloqueó al menos un tier, el wanderer reacciona
                if new_unlocked > old_unlocked:
                    self.message_log.add(
                        "Comerciante Errante: \"Oh, genial! Ya se en qué voy a usar esto.\"",
                        "message_important"
                    )
                
                music_manager.play_sound("UI-select.mp3", volume=0.4)
            
            self.state = GameState.PLAYING
        
        elif key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def _handle_console_input(self, key: int) -> None:
        """Maneja la entrada durante el modo consola."""
        # Cerrar consola con ESC o F1
        if key == pygame.K_ESCAPE or key == pygame.K_F1:
            self.state = GameState.PLAYING
            self.console_input = ""
            self.console_history_index = -1
            return
        
        # Ejecutar comando con ENTER
        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if self.console_input.strip():
                # Añadir al historial
                self.console_history.append(self.console_input)
                if len(self.console_history) > 50:  # Limitar historial
                    self.console_history.pop(0)
                self.console_history_index = -1
                
                # Ejecutar comando
                results = dev_command_manager.execute(self.console_input, self)
                for msg in results:
                    self.message_log.add(msg, "message_important")
                
                self.console_input = ""
                # Cerrar consola después de ejecutar
                self.state = GameState.PLAYING
            return
        
        # Navegar historial con flechas arriba/abajo
        if key == pygame.K_UP:
            if self.console_history:
                if self.console_history_index == -1:
                    self.console_history_index = len(self.console_history) - 1
                else:
                    self.console_history_index = max(0, self.console_history_index - 1)
                self.console_input = self.console_history[self.console_history_index]
            return
        
        if key == pygame.K_DOWN:
            if self.console_history:
                if self.console_history_index >= 0:
                    self.console_history_index += 1
                    if self.console_history_index >= len(self.console_history):
                        self.console_history_index = -1
                        self.console_input = ""
                    else:
                        self.console_input = self.console_history[self.console_history_index]
            return
        
        # Borrar con BACKSPACE
        if key == pygame.K_BACKSPACE:
            self.console_input = self.console_input[:-1]
            return
        
        # La entrada de texto se captura via pygame.TEXTINPUT en el game loop,
        # que respeta el layout de teclado (español, etc.).
    
    def _handle_save_menu_input(self, key: int) -> None:
        """Maneja la entrada en el menú de selección de guardados."""
        # Navegar con flechas arriba/abajo
        if key == pygame.K_UP:
            self.save_menu_selected = max(0, self.save_menu_selected - 1)
            return
        
        if key == pygame.K_DOWN:
            self.save_menu_selected = min(len(save_manager.slots) - 1, self.save_menu_selected + 1)
            return
        
        # Eliminar save con DELETE o SUPR
        if key == pygame.K_DELETE:
            slot_id = self.save_menu_selected + 1
            slot = save_manager.slots[slot_id - 1]
            if slot.exists:
                # Eliminar save y resetear eventos asociados
                if save_manager.delete_save(slot_id):
                    # Si estamos jugando en este slot, resetear eventos
                    if self.current_save_slot == slot_id:
                        event_manager.clear_all()
                        self.current_save_slot = None
                    save_manager.refresh_slots()
            return
        
        # Seleccionar con ENTER
        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            slot_id = self.save_menu_selected + 1
            slot = save_manager.slots[slot_id - 1]
            
            if slot.exists:
                # Cargar partida existente
                if self._load_game_from_slot(slot_id):
                    self.current_save_slot = slot_id  # Recordar el slot actual
                    self.state = GameState.PLAYING
            else:
                # Slot vacío: crear nueva partida (resetea todo)
                self._new_game()
                # Guardar inmediatamente en el slot seleccionado
                if self.player and self.dungeon:
                    self._save_game(slot_id, silent=True)
                    self.current_save_slot = slot_id
            return
        
        # Salir del juego con ESC
        if key == pygame.K_ESCAPE:
            self.running = False
            return
    
    def _handle_space_interact(self) -> bool:
        """
        Maneja la interacción universal con ESPACIO.
        
        Prioridad:
        1. Abrir/cerrar puertas adyacentes (máxima prioridad)
        2. Hablar con NPCs/entidades adyacentes (interactive_text)
        3. Recoger items del suelo
        4. Usar escaleras
        
        Returns:
            True si el jugador consumió un turno
        """
        # Posiciones adyacentes (cardinales) para puertas y NPCs
        adjacent_positions = [
            (self.player.x, self.player.y - 1),  # Arriba
            (self.player.x, self.player.y + 1),  # Abajo
            (self.player.x - 1, self.player.y),  # Izquierda
            (self.player.x + 1, self.player.y),  # Derecha
        ]
        
        # 1. Buscar puertas adyacentes (prioridad máxima)
        from .world.tile import TileType
        for x, y in adjacent_positions:
            tile = self.dungeon.get_tile(x, y)
            if tile and tile.tile_type == TileType.DOOR:
                return self._toggle_door(x, y)
        
        # 2. Buscar NPCs/entidades interactivas adyacentes (+ posición actual)
        interact_positions = adjacent_positions + [(self.player.x, self.player.y)]
        for x, y in interact_positions:
            for entity in self.dungeon.entities:
                if entity.x == x and entity.y == y:
                    if hasattr(entity, 'interactive_text') and entity.interactive_text:
                        self._start_interaction(entity.interactive_text)
                        return False  # Hablar no consume turno
            
            # Buscar items con InteractiveText
            items = self.dungeon.get_items_at(x, y)
            for item in items:
                if hasattr(item, 'interactive_text') and item.interactive_text:
                    self._start_interaction(item.interactive_text)
                    return False
        
        # 3. Recoger items del suelo
        items_here = self.dungeon.get_items_at(self.player.x, self.player.y)
        if items_here:
            messages = Inventory.pickup_item(self.player, self.dungeon)
            self.message_log.add_multiple(messages)
            return True
        
        # 4. Usar escaleras
        pos = (self.player.x, self.player.y)
        if self.dungeon.stairs_down and self.dungeon.stairs_down == pos:
            return self._use_stairs_down()
        elif self.dungeon.stairs_up and self.dungeon.stairs_up == pos:
            return self._use_stairs_up()
        
        # Nada con lo que interactuar
        self.message_log.add("No hay nada con lo que interactuar aquí.")
        return False
    
    def _toggle_door(self, x: int, y: int) -> bool:
        """
        Abre o cierra una puerta en la posición dada.
        
        No se puede toggle si hay una entidad (incluido el jugador) en el tile de la puerta.
        
        Args:
            x: Coordenada X de la puerta
            y: Coordenada Y de la puerta
            
        Returns:
            True si se consumió un turno
        """
        tile = self.dungeon.get_tile(x, y)
        if not tile:
            return False
        
        # Verificar si hay alguna entidad en la posición de la puerta
        blocking = self.dungeon.get_blocking_entity_at(x, y)
        if blocking:
            self.message_log.add("No puedes cerrar la puerta, hay algo en el camino.")
            return False
        
        # Verificar si el jugador está en la puerta
        if self.player.x == x and self.player.y == y:
            self.message_log.add("No puedes cerrar la puerta mientras estás en ella.")
            return False
        
        # Toggle
        if tile.is_open:
            tile.is_open = False
            self.message_log.add("Cierras la puerta.")
            music_manager.play_sound("door_effect.mp3", volume=0.4)
        else:
            tile.is_open = True
            self.message_log.add("Abres la puerta.")
            music_manager.play_sound("door_effect.mp3", volume=0.4)
        
        return True  # Consume turno
    
    def _start_interaction(self, interactive_text) -> None:
        """
        Inicia una interacción con texto/diálogo.
        
        Args:
            interactive_text: Componente InteractiveText
        """
        from .systems.text import TextType
        
        if interactive_text.text_type == TextType.DIALOG:
            dialog_manager.set_player(self.player)
            if dialog_manager.start_dialog(interactive_text.dialog_tree):
                self.state = GameState.DIALOG
        elif interactive_text.text_type == TextType.SIMPLE:
            # Si el texto contiene "---", procesarlo como múltiples mensajes
            text_lines = interactive_text.text_content.lines
            full_text = "\n".join(text_lines)
            
            if "---" in full_text:
                # Separar por "---" y crear múltiples mensajes
                messages = [msg.strip() for msg in full_text.split("---") if msg.strip()]
                if len(messages) > 1:
                    dialog_manager.queue_multiple_texts(messages, titles=[interactive_text.text_content.title] * len(messages))
                    if dialog_manager.process_queue():
                        self.state = GameState.DIALOG
                else:
                    # Solo un mensaje después de filtrar
                    dialog_manager.start_text(interactive_text.text_content)
                    self.state = GameState.DIALOG
            else:
                dialog_manager.start_text(interactive_text.text_content)
                self.state = GameState.DIALOG
        elif interactive_text.text_type == TextType.AMBIENT:
            dialog_manager.start_text(interactive_text.text_content)
            self.state = GameState.DIALOG
        
        # Guardar referencia a la entidad con la que interactuamos para activar eventos después
        self._last_interacted_entity = None
        self._last_interacted_state = None  # Estado FSM al inicio de la interacción
        # Buscar la entidad con la que interactuamos (tanto para DIALOG como SIMPLE)
        for entity in self.dungeon.entities:
            if (hasattr(entity, 'interactive_text') and 
                entity.interactive_text == interactive_text):
                self._last_interacted_entity = entity
                
                # Guardar el estado FSM actual ANTES de cualquier acción del diálogo
                # para que _on_dialog_closed solo complete este estado, no uno nuevo
                if hasattr(entity, 'name'):
                    from roguelike.systems.npc_states import npc_state_manager as _fsm
                    _norm = _fsm.normalize_npc_name(entity.name)
                    self._last_interacted_state = _fsm.get_current_state(_norm)
                
                # Si es un NPC con sistema FSM, actualizar el diálogo antes de mostrar
                if hasattr(entity, 'name'):
                    from roguelike.systems.npc_states import npc_state_manager
                    from roguelike.systems.text import InteractiveText
                    normalized_name = npc_state_manager.normalize_npc_name(entity.name)
                    current_state = npc_state_manager.get_current_state(normalized_name)
                    if current_state:
                        # Obtener el diálogo correcto (corto si está completado, completo si no)
                        new_dialog = npc_state_manager.get_dialog_for_state(
                            normalized_name, current_state
                        )
                        if new_dialog:
                            if isinstance(new_dialog, InteractiveText):
                                entity.interactive_text = new_dialog
                                interactive_text = new_dialog  # Actualizar referencia
                            else:
                                # Es un DialogTree
                                dialog_tree = new_dialog
                                entity.interactive_text = InteractiveText.create_dialog(dialog_tree, interaction_key="espacio")
                                interactive_text = entity.interactive_text  # Actualizar referencia
                break
        
        # Verificar eventos automáticos después de interactuar
        triggered = event_manager.check_and_trigger_events(self.player, self.dungeon)
        if triggered:
            for event_id in triggered:
                event = event_manager.events.get(event_id)
                if event:
                    self.message_log.add(f"Evento: {event.name}", "message_important")
    
    def _on_dialog_closed(self) -> None:
        """
        Se llama cuando se cierra un diálogo. Activa eventos y verifica transiciones de estados.
        
        IMPORTANTE: Procesa transiciones FSM incluso si la entidad fue eliminada de la zona
        (por ejemplo, cuando un evento elimina al NPC durante el diálogo). La referencia al
        objeto entity sigue siendo válida para acceder al nombre del NPC.
        """
        from roguelike.systems.npc_states import npc_state_manager, StateCompletion
        
        if not (hasattr(self, '_last_interacted_entity') and self._last_interacted_entity):
            return
        
        entity = self._last_interacted_entity
        npc_name = entity.name
        
        # Verificar si la entidad todavía está en la zona
        entity_in_zone = entity in self.dungeon.entities
        
        # Marcar el estado como completado si tiene estado FSM
        # IMPORTANTE: Usamos el estado que estaba activo al INICIO de la interacción
        # (guardado en _last_interacted_state), NO el estado actual. 
        # Esto evita que si una acción del diálogo cambió el estado (ej: found → obligada),
        # marquemos el nuevo estado como COMPLETED antes de que el jugador lo vea.
        interaction_state = getattr(self, '_last_interacted_state', None)
        current_state = npc_state_manager.get_current_state(npc_name)
        
        if interaction_state:
            # Marcar el estado que estaba activo al inicio como completado
            # PERO solo si tiene completion_condition definida (o si ya se cumple).
            # Si completion_condition=None, el estado NUNCA se completa automáticamente
            # (ej: tienda del comerciante, que siempre muestra el diálogo completo).
            state_cfg = npc_state_manager.get_state_config(npc_name, interaction_state)
            interaction_completion = npc_state_manager.get_state_completion(npc_name, interaction_state)
            if interaction_completion != StateCompletion.COMPLETED:
                if state_cfg and state_cfg.completion_condition is not None:
                    npc_state_manager.set_state_completion(npc_name, interaction_state, StateCompletion.COMPLETED)
        elif current_state:
            # Fallback: si no tenemos estado guardado, usar el actual (comportamiento legacy)
            state_cfg = npc_state_manager.get_state_config(npc_name, current_state)
            current_completion = npc_state_manager.get_state_completion(npc_name, current_state)
            if current_completion != StateCompletion.COMPLETED:
                if state_cfg and state_cfg.completion_condition is not None:
                    npc_state_manager.set_state_completion(npc_name, current_state, StateCompletion.COMPLETED)
        
        # Detectar si una acción del diálogo cambió el estado programáticamente
        # (ej: on_give_poison cambia nieta a "huida" con zone_type=None)
        # Si el nuevo estado está en otra zona (o en ninguna), eliminar la entidad
        if interaction_state and current_state and interaction_state != current_state and entity_in_zone:
            new_state_config = npc_state_manager.get_state_config(npc_name, current_state)
            if new_state_config:
                # zone_type=None → NPC no debe aparecer en ningún sitio
                # zone_type diferente → NPC se fue a otra zona
                current_zone_type = getattr(self.dungeon, 'zone_type', None)
                if new_state_config.zone_type is None or new_state_config.zone_type != current_zone_type:
                    self.dungeon.entities.remove(entity)
                    self.message_log.add(f"{npc_name} se ha ido...", "message_important")
                    entity_in_zone = False
        
        # Actualizar el diálogo del NPC (solo si la entidad sigue en la zona)
        # Usar el estado ACTUAL (puede haber cambiado por la acción del diálogo)
        if current_state and entity_in_zone:
            from roguelike.systems.text import InteractiveText
            state_config = npc_state_manager.get_state_config(npc_name, current_state)
            if state_config:
                new_dialog = npc_state_manager.get_dialog_for_state(npc_name, current_state)
                if new_dialog:
                    if isinstance(new_dialog, InteractiveText):
                        entity.interactive_text = new_dialog
                    else:
                        dialog_tree = new_dialog
                        entity.interactive_text = InteractiveText.create_dialog(dialog_tree, interaction_key="espacio")
        
        # Verificar transiciones automáticas del FSM
        # Solo transiciones CROSS-ZONA (ej: dungeon → lobby = Stranger "se ha ido")
        # Las transiciones MISMA-ZONA se difieren al spawn (próxima visita a la zona)
        # Esto evita que about_weapons → mision_nieta se ejecute inmediatamente
        new_state = npc_state_manager.check_and_transition(npc_name, self.player, self.dungeon, only_cross_zone=True)
        if new_state:
            state_config = npc_state_manager.get_state_config(npc_name, new_state)
            if state_config:
                # Si el nuevo estado es en otra zona, eliminar el NPC de la zona actual
                if state_config.zone_type != self.dungeon.zone_type:
                    if entity_in_zone:
                        self.dungeon.entities.remove(entity)
                        self.message_log.add(f"{npc_name} se ha ido...", "message_important")
                elif entity_in_zone:
                    # Mismo tipo de zona: aplicar nuevo estado al NPC existente
                    from roguelike.systems.dev_commands import dev_command_manager
                    dev_command_manager.apply_npc_state(entity, self.dungeon, npc_name, new_state, state_config, self)
            
            # Verificar eventos automáticos después de la transición
            triggered = event_manager.check_and_trigger_events(self.player, self.dungeon)
            if triggered:
                for event_id in triggered:
                    event = event_manager.events.get(event_id)
                    if event:
                        self.message_log.add(f"Evento: {event.name}", "message_important")
        
        # Limpiar referencias
        self._last_interacted_entity = None
        self._last_interacted_state = None
    
    def _register_game_events(self) -> None:
        """
        Registra todos los eventos del juego.
        Los eventos se definen en game_events.py o aquí mismo.
        """
        # Importar y registrar eventos
        try:
            from .game_events import register_all_game_events
            register_all_game_events()
        except ImportError:
            # Si no existe game_events.py, no pasa nada
            pass
    
    def _player_move_or_attack(self, dx: int, dy: int) -> bool:
        """
        Mueve al jugador o ataca si hay un enemigo.
        
        Args:
            dx: Desplazamiento X
            dy: Desplazamiento Y
            
        Returns:
            True si el jugador actuó
        """
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        # Verificar si hay una entidad bloqueante (blocks=True)
        target = self.dungeon.get_blocking_entity_at(new_x, new_y)
        
        if target:
            # Fighter: atacar si está vivo
            if hasattr(target, 'fighter') and target.fighter is not None and not target.fighter.is_dead:
                # Animación de ataque del jugador
                self.animation_manager.add_attack_animation(
                    attacker_id=id(self.player),
                    attacker_x=self.player.x,
                    attacker_y=self.player.y,
                    target_x=target.x,
                    target_y=target.y
                )
                
                # Atacar (pasando animation_manager para números de daño)
                messages = Combat.attack(self.player, target, self.animation_manager)
                
                # Colorear mensajes según contenido
                for msg in messages:
                    if "muere" in msg.lower():
                        self.message_log.add(msg, "message_death")
                    elif "experiencia" in msg.lower() or "nivel" in msg.lower():
                        self.message_log.add(msg, "message_important")
                    elif "golpea" in msg.lower() or "daño" in msg.lower():
                        self.message_log.add(msg, "message_damage")
                    else:
                        self.message_log.add(msg)
                
                return True
            
            # Entidad bloqueante sin fighter: no se puede pasar ni atacar
            return False
        
        # Intentar moverse (no hay entidad bloqueante)
        if self.dungeon.is_walkable(new_x, new_y):
            self.player.x = new_x
            self.player.y = new_y
            
            # Verificar escaleras
            if self.dungeon.stairs_down and self.dungeon.stairs_down == (new_x, new_y):
                self.message_log.add("Ves escaleras hacia abajo. Presiona ESPACIO para bajar.")
            elif self.dungeon.stairs_up and self.dungeon.stairs_up == (new_x, new_y):
                self.message_log.add("Ves escaleras hacia arriba. Presiona ESPACIO para subir.")
            
            # Verificar items en el suelo
            items = self.dungeon.get_items_at(new_x, new_y)
            if items:
                item_names = [item.name for item in items[:3]]
                if len(items) > 3:
                    item_names.append(f"y {len(items) - 3} más")
                self.message_log.add(f"Ves aquí: {', '.join(item_names)}")
            
            return True
        
        return False
    
    def _use_any_stairs(self) -> bool:
        """Usa cualquier escalera en la posición actual."""
        pos = (self.player.x, self.player.y)
        
        # Verificar escaleras hacia abajo (incluyendo lobby)
        if self.dungeon.stairs_down and self.dungeon.stairs_down == pos:
            return self._use_stairs_down()
        elif self.dungeon.stairs_up and self.dungeon.stairs_up == pos:
            return self._use_stairs_up()
        else:
            self.message_log.add("No hay escaleras aquí.")
            return False
    
    def _use_stairs_down(self) -> bool:
        """Usa las escaleras descendentes."""
        if not self.dungeon:
            self.message_log.add("No hay escaleras para bajar aquí (busca >).")
            return False
        
        player_pos = (self.player.x, self.player.y)
        
        # Para el lobby, verificar tanto stairs_down como dungeon_entrance
        if isinstance(self.dungeon, Lobby):
            # Asegurar que stairs_down esté sincronizado con dungeon_entrance
            if not self.dungeon.stairs_down and self.dungeon.dungeon_entrance:
                self.dungeon.stairs_down = self.dungeon.dungeon_entrance
            
            # Verificar si estamos en las escaleras
            if self.dungeon.stairs_down == player_pos or self.dungeon.dungeon_entrance == player_pos:
                # Si estamos en el lobby, entrar a la mazmorra (piso 1)
                # Crear o cargar la mazmorra del piso 1
                if 1 in self.dungeons:
                    new_dungeon = self.dungeons[1]
                    self.dungeon = new_dungeon
                    # Posicionar al jugador en las escaleras de subida del piso 1
                    if new_dungeon.stairs_up:
                        self.player.x, self.player.y = new_dungeon.stairs_up
                else:
                    new_dungeon = Dungeon(MAP_WIDTH, MAP_HEIGHT, 1)
                    start_pos = new_dungeon.generate()
                    self.dungeons[1] = new_dungeon
                    self.dungeon = new_dungeon
                    self.player.x, self.player.y = start_pos

                # Actualizar datos del jugador
                self.player.current_floor = 1
                self.player.dungeon = self.dungeon

                # Cambiar música a tema de mazmorra
                music_manager.stop(fade_ms=500)
                if music_manager.load_music("dungeonTheme.mp3"):
                    music_manager.set_volume(0.4)
                    music_manager.play(loops=-1, fade_ms=1500)

                self.message_log.add("Desciendes a la mazmorra...", "message_important")
                self._update_fov()
                
                # Auto-guardar al entrar a la mazmorra
                if self.current_save_slot:
                    self._save_game(self.current_save_slot, silent=True)
                
                return True
            else:
                # No estamos en las escaleras del lobby
                self.message_log.add("No hay escaleras para bajar aquí (busca >).")
                return False
        else:
            # No estamos en el lobby, verificar escaleras normales
            if self.dungeon.stairs_down == player_pos:
                # Si ya estamos en una mazmorra, cambiar de piso normalmente
                self._change_floor(self.player.current_floor + 1)
                return True
            else:
                self.message_log.add("No hay escaleras para bajar aquí (busca >).")
                return False
    
    def _use_stairs_up(self) -> bool:
        """Usa las escaleras ascendentes."""
        if self.dungeon.stairs_up == (self.player.x, self.player.y):
            # NOTA: El colgante es placeholder, no termina el juego
            # Si estamos en el piso 1, subir al lobby normalmente
            if self.player.current_floor == 1:
                # Cambiar al lobby (piso 0)
                if isinstance(self.dungeon, Lobby):
                    # Ya estamos en el lobby, no hacer nada
                    self.message_log.add("Ya estás en el lobby.")
                    return False
                else:
                    # Guardar mazmorra actual
                    self.dungeons[self.player.current_floor] = self.dungeon
                    
                    # Cargar o crear lobby
                    # Buscar si ya tenemos un lobby guardado
                    lobby = None
                    if hasattr(self, '_lobby') and self._lobby is not None:
                        lobby = self._lobby
                    else:
                        # Crear nuevo lobby
                        lobby = Lobby(MAP_WIDTH, MAP_HEIGHT)
                        lobby.generate()
                        self._lobby = lobby
                    
                    # Asegurar que los NPCs estén spawneados cada vez que entras al lobby
                    # (por si muriste y volviste, o si el lobby se cargó desde guardado)
                    lobby.spawn_npcs_from_states()
                    
                    self.dungeon = lobby
                    # Posicionar al jugador en las escaleras de subida del lobby
                    if lobby.stairs_up:
                        self.player.x, self.player.y = lobby.stairs_up
                    else:
                        # Si no hay escaleras, usar posición inicial (centro)
                        self.player.x = MAP_WIDTH // 2
                        self.player.y = MAP_HEIGHT // 2
                    
                    self.player.current_floor = 0
                    self.player.dungeon = self.dungeon
                    
                    # Cambiar música a tema de lobby
                    music_manager.stop(fade_ms=500)
                    if music_manager.load_music("lobby-music.mp3"):
                        music_manager.set_volume(0.4)
                        music_manager.play(loops=-1, fade_ms=1500)
                    
                    # Los NPCs se spawnean automáticamente en spawn_npcs_from_states()
                    # que se llama cada vez que entras al lobby
                    
                    self.message_log.add("Has vuelto al lobby.", "message_important")
                    self._update_fov()
                    
                    # Auto-guardar al volver al lobby
                    if self.current_save_slot:
                        self._save_game(self.current_save_slot, silent=True)
                    
                    return True
            else:
                self._change_floor(self.player.current_floor - 1)
                return True
        else:
            self.message_log.add("No hay escaleras para subir aquí (busca <).")
            return False
    
    def _change_floor(self, new_floor: int) -> None:
        """
        Cambia de piso dentro de la mazmorra.
        
        Args:
            new_floor: Nuevo número de piso
        """
        # Guardar mazmorra actual
        if self.dungeon and not isinstance(self.dungeon, Lobby):
            self.dungeons[self.player.current_floor] = self.dungeon
        
        # Cargar o generar nueva mazmorra
        if new_floor in self.dungeons:
            self.dungeon = self.dungeons[new_floor]
            # Posicionar al jugador en las escaleras correctas
            if new_floor > self.player.current_floor:
                # Bajando: aparecer en escaleras arriba
                if self.dungeon.stairs_up:
                    self.player.x, self.player.y = self.dungeon.stairs_up
            else:
                # Subiendo: aparecer en escaleras abajo
                if self.dungeon.stairs_down:
                    self.player.x, self.player.y = self.dungeon.stairs_down
        else:
            new_dungeon = Dungeon(MAP_WIDTH, MAP_HEIGHT, new_floor)
            start_pos = new_dungeon.generate()
            self.player.x, self.player.y = start_pos
            self.dungeons[new_floor] = new_dungeon
            self.dungeon = new_dungeon
        
        self.player.current_floor = new_floor
        self.player.dungeon = self.dungeon
        
        self.message_log.add(f"Entras al piso {new_floor}.", "message_important")
        self._update_fov()
        
        # Auto-guardar al cambiar de piso
        if self.current_save_slot:
            self._save_game(self.current_save_slot, silent=True)
    
    def _enemy_turn(self) -> None:
        """Ejecuta el turno de todos los enemigos."""
        for entity in self.dungeon.entities:
            if hasattr(entity, 'fighter') and entity.fighter is not None and not entity.fighter.is_dead:
                # Guardar posición antes del update para detectar ataques
                was_adjacent = entity.distance_to(self.player) < 1.5
                
                messages = entity.update(self.player, self.visible_tiles, self.animation_manager)
                
                # Si estaba adyacente y hay mensaje de golpe, añadir animación
                attack_happened = any("golpea" in msg.lower() for msg in messages)
                if was_adjacent and attack_happened:
                    self.animation_manager.add_attack_animation(
                        attacker_id=id(entity),
                        attacker_x=entity.x,
                        attacker_y=entity.y,
                        target_x=self.player.x,
                        target_y=self.player.y
                    )
                
                for msg in messages:
                    if "golpea" in msg.lower():
                        self.message_log.add(msg, "message_damage")
                    else:
                        self.message_log.add(msg)
        
        # Verificar si el jugador murió
        if self.player.fighter.is_dead:
            self._handle_player_death()
            self.message_log.add("¡Has muerto!", "message_death")
    
    def _update_fov(self) -> None:
        """Actualiza el campo de visión."""
        self.visible_tiles = self.dungeon.update_fov(
            self.player.x,
            self.player.y,
            FOV_RADIUS
        )
    
    def _start_in_lobby(self) -> None:
        """
        Configura el juego en el lobby con un jugador nuevo.
        
        Crea un lobby nuevo, un jugador fresco, y configura la música y mensajes.
        NO toca los eventos ni los estados FSM de NPCs — eso es progreso meta.
        Se usa tanto para partidas nuevas como para respawn tras muerte.
        """
        # Detener todos los sonidos
        music_manager.stop_all_sounds()
        
        # Resetear las mazmorras (cada run genera nuevas)
        self.dungeons = {}
        self.message_log.clear()

        # Crear lobby inicial
        lobby = Lobby(MAP_WIDTH, MAP_HEIGHT)
        start_pos = lobby.generate()
        self.dungeon = lobby
        self._lobby = lobby

        # Crear jugador nuevo
        self.player = Player(start_pos[0], start_pos[1], self.dungeon)
        self.player.current_floor = 0

        # Actualizar FOV
        self._update_fov()

        # Música de lobby
        music_manager.stop_all()
        if music_manager.load_music("lobby-music.mp3"):
            music_manager.set_volume(0.4)
            music_manager.play(loops=-1, fade_ms=1500)

        # Mensajes iniciales
        self.message_log.add("Bienvenido al lobby.", "message_important")
        self.message_log.add("Desde aquí podrás descender a las mazmorras.")
        self.message_log.add("Colócate sobre las escaleras (>) y presiona ENTER para entrar.")
        
        # Mostrar mensaje de bienvenida del lobby (solo la primera vez por save)
        self._show_lobby_welcome_message()
        
        # Solo establecer PLAYING si no hay un diálogo activo
        if not dialog_manager.is_active():
            self.state = GameState.PLAYING
    
    def _new_game(self) -> None:
        """
        Inicia una partida completamente nueva (slot vacío).
        Resetea TODO: eventos, estados FSM, mazmorras, jugador.
        """
        event_manager.clear_all()
        from roguelike.systems.npc_states import npc_state_manager
        npc_state_manager.npc_current_states.clear()
        npc_state_manager.npc_state_completion.clear()
        
        self._start_in_lobby()
    
    def _respawn_in_lobby(self) -> None:
        """
        Respawnea al jugador en el lobby tras morir.
        
        Preserva el progreso meta (eventos, estados FSM de NPCs).
        Solo resetea la run actual (mazmorras, jugador, inventario no persistente).
        Los items con persistent=True y el oro se transfieren al nuevo jugador.
        Incrementa el contador de runs completadas.
        Guarda automáticamente en el slot actual.
        """
        # Guardar items persistentes y oro del jugador anterior
        persistent_items = []
        preserved_gold = 0
        if self.player:
            persistent_items = self.player.get_persistent_items()
            preserved_gold = self.player.gold
        
        # Incrementar contador de runs completadas
        # Esto permite que las transiciones FSM de NPCs detecten
        # "el jugador ha completado una run desde que hablamos"
        event_manager.complete_run()
        
        # Restockear la tienda del comerciante para la nueva run
        reset_merchant_shop()
        
        # Resetear flag DEV de forzar merchant (solo en memoria, nunca guardado)
        from .content.npcs import merchant as _merchant_module
        _merchant_module._dev_force_spawn = False
        
        self._start_in_lobby()
        
        # Transferir items persistentes y oro al nuevo jugador
        if self.player:
            self.player.gold = preserved_gold
            for item in persistent_items:
                self.player.add_to_inventory(item)
        
        # Auto-guardar para que el progreso no se pierda
        if self.current_save_slot:
            self._save_game(self.current_save_slot, silent=True)
    
    def _save_game(self, slot_id: int = 1, silent: bool = False) -> None:
        """
        Guarda la partida en un slot específico.
        
        Args:
            slot_id: ID del slot (1 o 2), por defecto 1
            silent: Si es True, no muestra mensajes en el log
        """
        if not self.player or not self.dungeon:
            return
        
        # Calcular tiempo de juego
        import time
        current_play_time = 0
        if self.play_time_start:
            current_play_time = int(time.time() - self.play_time_start)
        total_time = self.total_play_time + current_play_time
        
        if save_manager.save_game(slot_id, self.player, self.dungeon, self.dungeons, total_time):
            self.current_save_slot = slot_id  # Recordar el slot actual
            if not silent:
                self.message_log.add(f"Partida guardada en Slot {slot_id}.", "message_important")
        else:
            if not silent:
                self.message_log.add(f"Error al guardar en Slot {slot_id}.", "message_damage")
    
    def _load_game_from_slot(self, slot_id: int) -> bool:
        """
        Carga una partida desde un slot específico.
        
        Args:
            slot_id: ID del slot (1 o 2)
            
        Returns:
            True si se cargó exitosamente
        """
        save_data = save_manager.load_game(slot_id)
        if not save_data:
            return False
        
        try:
            # ============================================================
            # PASO 1: Restaurar eventos y estados FSM PRIMERO
            # Es CRÍTICO que esto se haga ANTES de crear lobbies/dungeons,
            # porque sus from_dict() llaman a spawn_npcs_from_states()
            # que necesita los eventos y estados FSM para funcionar.
            # ============================================================
            
            # Restaurar eventos (cada save tiene su propio estado de eventos)
            if "events" in save_data:
                event_manager.from_dict(save_data["events"])
            else:
                event_manager.clear_all()
            
            # Restaurar estados FSM de NPCs
            from roguelike.systems.npc_states import npc_state_manager, StateCompletion
            if "npc_states" in save_data:
                npc_states_data = save_data["npc_states"]
                npc_state_manager.npc_current_states = npc_states_data.get("current_states", {}).copy()
                completion_data = npc_states_data.get("state_completion", {})
                for npc_name, states in completion_data.items():
                    npc_state_manager.npc_state_completion[npc_name] = {
                        state_id: StateCompletion(completion_value)
                        for state_id, completion_value in states.items()
                    }
            else:
                npc_state_manager.npc_current_states.clear()
                npc_state_manager.npc_state_completion.clear()
            
            # ============================================================
            # PASO 2: Crear zonas (ahora con eventos y FSM correctos)
            # ============================================================
            
            # Restaurar mazmorras
            self.dungeons = {}
            for floor, dungeon_data in save_data.get("dungeons", {}).items():
                self.dungeons[int(floor)] = Dungeon.from_dict(dungeon_data)
            
            # Restaurar zona actual (lobby o mazmorra)
            in_lobby = save_data.get("in_lobby", False)
            current_floor = save_data.get("current_floor", 0)
            
            if in_lobby and "lobby" in save_data:
                self.dungeon = Lobby.from_dict(save_data["lobby"])
                self._lobby = self.dungeon
            elif current_floor in self.dungeons:
                self.dungeon = self.dungeons[current_floor]
                if "lobby" in save_data:
                    self._lobby = Lobby.from_dict(save_data["lobby"])
            else:
                self.dungeon = Lobby(MAP_WIDTH, MAP_HEIGHT)
                self.dungeon.generate()
                self._lobby = self.dungeon
                current_floor = 0
            
            # ============================================================
            # PASO 3: Restaurar jugador y tiempo
            # ============================================================
            
            self.player = Player.from_dict(save_data["player"], self.dungeon)
            self.player.current_floor = current_floor
            
            self.total_play_time = save_data.get("play_time", 0)
            import time
            self.play_time_start = time.time()
            
            # Actualizar FOV
            self._update_fov()
            
            # Restaurar música según la zona
            if isinstance(self.dungeon, Lobby):
                music_manager.stop_all()
                if music_manager.load_music("lobby-music.mp3"):
                    music_manager.set_volume(0.4)
                    music_manager.play(loops=-1, fade_ms=1500)
            else:
                music_manager.stop_all()
                if music_manager.load_music("dungeonTheme.mp3"):
                    music_manager.set_volume(0.4)
                    music_manager.play(loops=-1, fade_ms=1500)
            
            self.message_log.add(f"Partida cargada desde Slot {slot_id}.", "message_important")
            return True
        except Exception as e:
            self.message_log.add(f"Error al cargar: {e}", "message_damage")
            return False
    
    def _load_game(self) -> bool:
        """
        Carga una partida guardada (método legacy, redirige al nuevo sistema).
        
        Returns:
            True si se cargó exitosamente
        """
        # Por defecto cargar del slot 1
        return self._load_game_from_slot(1)
    
    def _show_lobby_welcome_message(self) -> None:
        """
        Muestra el mensaje de bienvenida del lobby automáticamente.
        El mensaje se puede editar en roguelike/content/ambient/lobby.py (LOBBY_WELCOME_MESSAGE).
        
        Solo se muestra la primera vez en un save nuevo. Usa el sistema de eventos
        para persistir que ya se mostró.
        
        Si LOBBY_WELCOME_MESSAGE contiene múltiples mensajes separados por "---",
        se mostrarán secuencialmente como bocadillos.
        """
        from .systems.events import event_manager
        
        # Solo mostrar una vez por save
        if event_manager.is_event_triggered("lobby_welcome_shown"):
            return
        
        from .content.ambient.lobby import LOBBY_WELCOME_MESSAGE
        
        # Limpiar espacios
        message_text = LOBBY_WELCOME_MESSAGE.strip()
        if not message_text:
            return
        
        # Marcar como mostrado (se persiste con el save)
        event_manager.triggered_events.add("lobby_welcome_shown")
        
        # Verificar si hay múltiples mensajes separados por "---"
        messages = [msg.strip() for msg in message_text.split("---") if msg.strip()]
        
        if len(messages) > 1:
            # Múltiples mensajes: usar cola para mostrarlos secuencialmente
            titles = [""] * len(messages)  # Todos con el mismo título, o puedes personalizar
            dialog_manager.queue_multiple_texts(messages, titles=titles)
            # Mostrar el primer mensaje
            if dialog_manager.process_queue():
                self.state = GameState.DIALOG
        else:
            # Un solo mensaje: mostrar directamente
            text_content = TextContent.from_string(
                message_text,
                title="",
                auto_close=False  # El jugador debe cerrarlo manualmente
            )
            dialog_manager.start_text(text_content)
            self.state = GameState.DIALOG
