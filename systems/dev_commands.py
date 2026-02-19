"""
Sistema de comandos de desarrollo y debug.
Permite comandos rápidos para testear sin tener que jugar todo desde el principio.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..world.zone import Zone
    from ..game import Game


class DevCommand:
    """
    Comando de desarrollo.
    
    Attributes:
        name: Nombre del comando
        description: Descripción de qué hace
        usage: Ejemplo de uso
        handler: Función que ejecuta el comando (game, args) -> List[str]
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        usage: str,
        handler
    ):
        self.name = name
        self.description = description
        self.usage = usage
        self.handler = handler


class DevCommandManager:
    """
    Gestor de comandos de desarrollo.
    
    Permite ejecutar comandos rápidos para testear el juego.
    """
    
    def __init__(self):
        """Inicializa el gestor de comandos."""
        self.commands: dict[str, DevCommand] = {}
        self.enabled = True  # Cambiar a False en release
        self._register_commands()
    
    def _register_commands(self) -> None:
        """Registra todos los comandos disponibles."""
        # Comando: goto <piso>
        self.register_command(
            "goto",
            "Teletransporta al jugador a un piso específico",
            "goto 5",
            self._cmd_goto
        )
        
        # Comando: give <item>
        self.register_command(
            "give",
            "Da un item al jugador",
            "give health_potion",
            self._cmd_give
        )
        
        # Comando: gold <cantidad>
        self.register_command(
            "gold",
            "Modifica el oro del jugador",
            "gold 1000",
            self._cmd_gold
        )
        
        # Comando: heal
        self.register_command(
            "heal",
            "Cura completamente al jugador",
            "heal",
            self._cmd_heal
        )
        
        # Comando: level <nivel>
        self.register_command(
            "level",
            "Establece el nivel del jugador",
            "level 10",
            self._cmd_level
        )
        
        # Comando: xp <cantidad>
        self.register_command(
            "xp",
            "Añade experiencia al jugador",
            "xp 1000",
            self._cmd_xp
        )
        
        # Comando: teleport <x> <y>
        self.register_command(
            "teleport",
            "Teletransporta al jugador a coordenadas específicas",
            "teleport 40 20",
            self._cmd_teleport
        )
        
        # Comando: event <event_id>
        self.register_command(
            "event",
            "Activa un evento manualmente",
            "event stranger_floor5_met",
            self._cmd_event
        )
        
        # Comando: killall
        self.register_command(
            "killall",
            "Mata a todos los enemigos en el piso actual",
            "killall",
            self._cmd_killall
        )
        
        # Comando: amulet
        self.register_command(
            "amulet",
            "Da el Amuleto de Ámbar al jugador",
            "amulet",
            self._cmd_amulet
        )
        
        # Comando: clear
        self.register_command(
            "clear",
            "Limpia el log de mensajes",
            "clear",
            self._cmd_clear
        )
        
        # Comando: npc_state
        self.register_command(
            "npc_state",
            "Muestra o establece el estado de diálogo de un NPC",
            "npc_state <npc_name> [node_id]",
            self._cmd_npc_state
        )
        
        # Comando: merchant
        self.register_command(
            "merchant",
            "Fuerza aparición del comerciante en plantas pares (100%, esta run)",
            "merchant",
            self._cmd_merchant
        )
        
        # Comando: shop_donate
        self.register_command(
            "shop_donate",
            "Muestra estado de donaciones o establece el total donado",
            "shop_donate [cantidad]",
            self._cmd_shop_donate
        )
        
        # Comando: shop_restock
        self.register_command(
            "shop_restock",
            "Activa el restock de la tienda del comerciante (gratis)",
            "shop_restock",
            self._cmd_shop_restock
        )
        
        # Comando: scenario
        self.register_command(
            "scenario",
            "Carga un escenario de test (configura eventos y estados de NPC)",
            "scenario nieta_descubierta",
            self._cmd_scenario
        )
        
        # Comando: help
        self.register_command(
            "help",
            "Muestra la lista de comandos disponibles",
            "help",
            self._cmd_help
        )
    
    def register_command(self, name: str, description: str, usage: str, handler) -> None:
        """
        Registra un nuevo comando.
        
        Args:
            name: Nombre del comando
            description: Descripción
            usage: Ejemplo de uso
            handler: Función que ejecuta el comando
        """
        self.commands[name] = DevCommand(name, description, usage, handler)
    
    def execute(self, command_line: str, game: 'Game') -> List[str]:
        """
        Ejecuta un comando.
        
        Args:
            command_line: Línea de comando completa (ej: "goto 5")
            game: Instancia del juego
            
        Returns:
            Lista de mensajes de resultado
        """
        if not self.enabled:
            return ["Comandos de desarrollo deshabilitados."]
        
        if not command_line.strip():
            return []
        
        # Parsear comando
        parts = command_line.strip().split()
        if not parts:
            return []
        
        cmd_name = parts[0].lower().lstrip("/")  # Permitir /comando o comando
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd_name not in self.commands:
            return [f"Comando desconocido: {cmd_name}. Escribe 'help' para ver comandos disponibles."]
        
        try:
            command = self.commands[cmd_name]
            return command.handler(game, args)
        except Exception as e:
            return [f"Error ejecutando comando: {e}"]
    
    # ============================================================================
    # HANDLERS DE COMANDOS
    # ============================================================================
    
    def _cmd_goto(self, game: 'Game', args: List[str]) -> List[str]:
        """Comando: goto <piso>"""
        if not args:
            return ["Uso: goto <piso> (ej: goto 5)"]
        
        try:
            floor = int(args[0])
            if floor < 1 or floor > 10:
                return ["El piso debe estar entre 1 y 10."]
            
            # Si estamos en el lobby, entrar a la mazmorra primero
            from ..world.lobby import Lobby
            if isinstance(game.dungeon, Lobby):
                # Entrar al piso 1 primero
                game._use_stairs_down()
            
            # Cambiar al piso deseado
            game._change_floor(floor)
            return [f"Teletransportado al piso {floor}."]
        except ValueError:
            return ["El piso debe ser un número."]
    
    def _cmd_give(self, game: 'Game', args: List[str]) -> List[str]:
        """Comando: give <item>"""
        if not args:
            from ..items.item import get_all_item_ids
            available = ", ".join(get_all_item_ids())
            return [
                "Uso: give <item_id> (ej: give health_potion)",
                f"IDs válidos: {available}"
            ]
        
        item_id = args[0].lower()
        
        # Compatibilidad: aliases cortos
        aliases = {
            "potion": "health_potion",
            "greater_potion": "greater_health_potion",
            "poison": "poison_potion",
        }
        item_id = aliases.get(item_id, item_id)
        
        # Compatibilidad: prefijos legacy "weapon_" y "armor_"
        if item_id.startswith("weapon_"):
            item_id = item_id.replace("weapon_", "", 1)
        elif item_id.startswith("armor_"):
            item_id = item_id.replace("armor_", "", 1)
        
        try:
            from ..items.item import create_item
            
            item = create_item(item_id, x=game.player.x, y=game.player.y)
            
            if item is None:
                from ..items.item import get_all_item_ids
                available = ", ".join(get_all_item_ids())
                return [f"Item desconocido: {item_id}", f"IDs válidos: {available}"]
            
            if len(game.player.inventory) < 26:
                game.player.inventory.append(item)
                return [f"Item '{item.name}' añadido al inventario."]
            else:
                return ["Inventario lleno."]
        except Exception as e:
            return [f"Error: {e}"]
    
    def _cmd_gold(self, game: 'Game', args: List[str]) -> List[str]:
        """Comando: gold <cantidad>"""
        if not args:
            return ["Uso: gold <cantidad> (ej: gold 1000)"]
        
        try:
            amount = int(args[0])
            game.player.gold = max(0, game.player.gold + amount)
            return [f"Oro modificado. Total: {game.player.gold}"]
        except ValueError:
            return ["La cantidad debe ser un número."]
    
    def _cmd_heal(self, game: 'Game', _args: List[str]) -> List[str]:
        """Comando: heal"""
        game.player.fighter.hp = game.player.fighter.max_hp
        return ["Jugador curado completamente."]
    
    def _cmd_level(self, game: 'Game', args: List[str]) -> List[str]:
        """Comando: level <nivel>"""
        if not args:
            return ["Uso: level <nivel> (ej: level 10)"]
        
        try:
            target_level = int(args[0])
            if target_level < 1 or target_level > 50:
                return ["El nivel debe estar entre 1 y 50."]
            
            # Calcular XP necesaria para ese nivel
            from ..config import XP_BASE, XP_FACTOR
            total_xp_needed = 0
            for level in range(2, target_level + 1):
                total_xp_needed += int(XP_BASE * (XP_FACTOR ** (level - 2)))
            
            game.player.fighter.level = target_level
            game.player.total_xp = total_xp_needed
            game.player.fighter.xp = 0
            
        except ValueError:
            return ["El nivel debe ser un número."]
        
        return [f"Nivel establecido a {target_level}."]
    
    def _cmd_xp(self, game: 'Game', args: List[str]) -> List[str]:
        """Comando: xp <cantidad>"""
        if not args:
            return ["Uso: xp <cantidad> (ej: xp 1000)"]
        
        try:
            amount = int(args[0])
            game.player.total_xp += amount
            game.player.fighter.xp += amount
            game.player.update()  # Para procesar subida de nivel
            return [f"Experiencia añadida: {amount}. Total: {game.player.total_xp}"]
        except ValueError:
            return ["La cantidad debe ser un número."]
    
    def _cmd_teleport(self, game: 'Game', args: List[str]) -> List[str]:
        """Comando: teleport <x> <y>"""
        if len(args) < 2:
            return ["Uso: teleport <x> <y> (ej: teleport 40 20)"]
        
        try:
            x = int(args[0])
            y = int(args[1])
            
            if game.dungeon.is_walkable(x, y):
                game.player.x = x
                game.player.y = y
                game._update_fov()
                return [f"Teletransportado a ({x}, {y})."]
            else:
                return ["Posición no transitable."]
        except ValueError:
            return ["Las coordenadas deben ser números."]
    
    def _cmd_event(self, game: 'Game', args: List[str]) -> List[str]:
        """Comando: event <event_id>"""
        if not args:
            return ["Uso: event <event_id> (ej: event stranger_floor5_met)"]
        
        event_id = args[0]
        from ..systems.events import event_manager
        
        if event_manager.trigger_event(event_id, game.player, game.dungeon):
            return [f"Evento '{event_id}' activado."]
        else:
            return [f"No se pudo activar el evento '{event_id}' (condiciones no cumplidas o no existe)."]
    
    def _cmd_killall(self, game: 'Game', _args: List[str]) -> List[str]:
        """Comando: killall"""
        killed = 0
        for entity in list(game.dungeon.entities):
            if hasattr(entity, 'fighter') and entity.fighter is not None and entity != game.player:
                entity.fighter.hp = 0
                entity.fighter.is_dead = True
                killed += 1
        
        # Limpiar entidades muertas
        game.dungeon.entities = [
            e for e in game.dungeon.entities
            if not (hasattr(e, 'fighter') and e.fighter is not None and e.fighter.is_dead and e != game.player)
        ]
        
        return [f"{killed} enemigos eliminados."]
    
    def _cmd_amulet(self, game: 'Game', _args: List[str]) -> List[str]:
        """Comando: amulet"""
        from ..items.special import Amulet
        from ..items.item import create_item
        
        # Verificar si ya tiene el amuleto
        has_amulet = any(isinstance(item, Amulet) for item in game.player.inventory)
        if has_amulet:
            return ["Ya tienes el Amuleto de Ámbar."]
        
        amulet = create_item("amulet", x=game.player.x, y=game.player.y)
        if len(game.player.inventory) < 26:
            game.player.inventory.append(amulet)
            game.player.has_amulet = True
            return ["Amuleto de Ámbar añadido al inventario."]
        else:
            return ["Inventario lleno."]
    
    def _cmd_clear(self, game: 'Game', _args: List[str]) -> List[str]:
        """Comando: clear"""
        game.message_log.clear()
        return ["Log de mensajes limpiado."]
    
    def _cmd_npc_state(self, game: 'Game', args: List[str]) -> List[str]:
        """Comando: npc_state <npc_name> [state_id]"""
        if not args:
            return ["Uso: npc_state <npc_name> [state_id]", 
                   "  Sin state_id: muestra el estado actual del NPC",
                   "  Con state_id: establece el estado del NPC (lo crea si no existe)",
                   "Ejemplo: npc_state Stranger",
                   "Ejemplo: npc_state Stranger waiting"]
        
        npc_name = args[0]
        from ..systems.npc_states import npc_state_manager
        
        # Buscar el NPC en TODAS las zonas
        npc = None
        npc_zone = None
        
        # Buscar en zona actual
        if game.dungeon:
            for entity in game.dungeon.entities:
                if entity.name == npc_name:
                    npc = entity
                    npc_zone = game.dungeon
                    break
        
        # Buscar en lobby
        if not npc and hasattr(game, '_lobby') and game._lobby:
            for entity in game._lobby.entities:
                if entity.name == npc_name:
                    npc = entity
                    npc_zone = game._lobby
                    break
        
        # Buscar en todas las mazmorras
        if not npc:
            for dungeon in game.dungeons.values():
                for entity in dungeon.entities:
                    if entity.name == npc_name:
                        npc = entity
                        npc_zone = dungeon
                        break
                if npc:
                    break
        
        # Si no existe, crearlo en la posición del jugador
        if not npc:
            if not game.player or not game.dungeon:
                return [f"NPC '{npc_name}' no encontrado. Necesitas estar en una zona para crearlo."]
            
            npc = self._create_npc_at_player_position(npc_name, game)
            if not npc:
                return [f"NPC '{npc_name}' no encontrado y no se pudo crear."]
            npc_zone = game.dungeon
        
        # Si no se especifica state_id, mostrar estado actual
        if len(args) == 1:
            messages = [f"=== Estado del NPC: {npc_name} ==="]
            messages.append(f"Zona: {type(npc_zone).__name__}")
            messages.append(f"Posición: ({npc.x}, {npc.y})")
            
            # Obtener estado actual del sistema FSM
            current_state_id = npc_state_manager.get_current_state(npc_name)
            if current_state_id:
                state_completion = npc_state_manager.get_state_completion(npc_name, current_state_id)
                messages.append(f"Estado FSM: '{current_state_id}' ({state_completion.value})")
            
            if hasattr(npc, 'interactive_text') and npc.interactive_text:
                from ..systems.text import TextType
                if npc.interactive_text.text_type == TextType.DIALOG and npc.interactive_text.dialog_tree:
                    dialog_tree = npc.interactive_text.dialog_tree
                    messages.append(f"Nodo inicial del diálogo: '{dialog_tree.start_node}'")
                    messages.append("")
                    messages.append("Estados disponibles en FSM:")
                    all_states = npc_state_manager.get_all_npc_states(npc_name)
                    for state_id, state_config in sorted(all_states.items()):
                        completion = npc_state_manager.get_state_completion(npc_name, state_id)
                        is_current = " (ACTUAL)" if state_id == current_state_id else ""
                        messages.append(f"  - {state_id}{is_current} [{completion.value}]")
                        if state_config.zone_type:
                            floor_info = f", piso {state_config.floor}" if state_config.floor else ""
                            messages.append(f"    Zona: {state_config.zone_type}{floor_info}")
                        if state_config.position:
                            messages.append(f"    Posición: {state_config.position}")
                else:
                    messages.append("Tipo: Texto simple (no tiene estados)")
            else:
                messages.append("Sin diálogo configurado")
            
            return messages
        
        # Si se especifica state_id, cambiar el estado
        state_id = args[1]
        
        # Obtener configuración del estado
        state_config = npc_state_manager.get_state_config(npc_name, state_id)
        if not state_config:
            available_states = ", ".join(sorted(npc_state_manager.get_npc_states(npc_name).keys()))
            return [f"Estado '{state_id}' no existe para '{npc_name}'.",
                   f"Estados disponibles: {available_states}",
                   f"Nota: ¿Quisiste decir 'mision_nieta' en lugar de 'nieta_mision'?"]
        
        # Establecer estado en el FSM
        from ..systems.npc_states import StateCompletion
        npc_state_manager.set_current_state(npc_name, state_id)
        npc_state_manager.set_state_completion(npc_name, state_id, StateCompletion.IN_PROGRESS)
        
        # Aplicar el estado (posición, diálogo, etc.)
        success = self.apply_npc_state(npc, npc_zone, npc_name, state_id, state_config, game)
        if success:
            # Verificar que el diálogo se asignó correctamente
            has_dialog = hasattr(npc, 'interactive_text') and npc.interactive_text is not None
            # Obtener información de posición
            from ..world.lobby import Lobby
            zone_name = "lobby" if isinstance(npc.dungeon, Lobby) else f"piso {getattr(npc.dungeon, 'floor', '?')}"
            player_zone = "lobby" if isinstance(game.dungeon, Lobby) else f"piso {getattr(game.dungeon, 'floor', '?')}"
            
            messages = [f"Estado '{npc_name}' -> '{state_id}'"]
            messages.append(f"NPC: ({npc.x}, {npc.y}) en {zone_name}")
            messages.append(f"Jugador: ({game.player.x}, {game.player.y}) en {player_zone}")
            
            # Verificar si están en la misma zona (comparar por tipo, no por instancia)
            from ..world.lobby import Lobby
            npc_is_lobby = isinstance(npc.dungeon, Lobby)
            player_is_lobby = isinstance(game.dungeon, Lobby)
            same_zone_type = npc_is_lobby == player_is_lobby
            
            if not same_zone_type:
                messages.append("ADVERTENCIA: Zonas diferentes!")
            elif npc_is_lobby and player_is_lobby:
                # Ambos en lobby, verificar si es la misma instancia
                if npc.dungeon is not game.dungeon:
                    messages.append("ADVERTENCIA: Instancias diferentes de lobby!")
            
            if has_dialog:
                messages.append("Diálogo: OK")
            else:
                messages.append("ADVERTENCIA: Sin diálogo")
            
            return messages
        else:
            return [f"No se pudo cambiar el estado de '{npc_name}' a '{state_id}'."]
    
    def _create_npc_at_player_position(self, npc_name: str, game: 'Game'):
        """
        Crea un NPC básico en la posición del jugador.
        
        Returns:
            NPC creado o None si falla
        """
        from ..entities.entity import Entity
        from ..ui.sprite_manager import sprite_manager
        
        npc = Entity(
            x=game.player.x,
            y=game.player.y,
            char="?",
            name=npc_name,
            color="white",
            blocks=True,
            dungeon=game.dungeon
        )
        
        # Asignar sprite si existe
        try:
            npc.sprite = sprite_manager.get_creature_sprite(npc_name.lower())
        except Exception:
            pass
        
        game.dungeon.entities.append(npc)
        return npc
    
    def apply_npc_state(self, npc, npc_zone, npc_name: str, state_id: str, 
                         state_config, game: 'Game') -> bool:
        # npc_name se usa para logging/debug si es necesario
        """
        Aplica un estado a un NPC.
        
        Mueve al NPC a su posición según el estado y configura su diálogo.
        
        Returns:
            True si se aplicó correctamente
        """
        from ..systems.text import InteractiveText, TextType
        from ..world.lobby import Lobby
        
        # Si no hay configuración, intentar usar el diálogo existente
        if not state_config:
            if hasattr(npc, 'interactive_text') and npc.interactive_text:
                if npc.interactive_text.text_type == TextType.DIALOG:
                    dialog_tree = npc.interactive_text.dialog_tree
                    if dialog_tree and state_id in dialog_tree.nodes:
                        dialog_tree.start_node = state_id
                        return True
            return False
        
        # Obtener zona destino
        target_zone = None
        if state_config.zone_type == "lobby":
            # Si el jugador ya está en el lobby, usar esa instancia
            if isinstance(game.dungeon, Lobby):
                target_zone = game.dungeon
            elif hasattr(game, '_lobby') and game._lobby:
                target_zone = game._lobby
            else:
                # Crear nuevo lobby si no existe
                game._lobby = Lobby(
                    game.dungeon.width if game.dungeon else 80,
                    game.dungeon.height if game.dungeon else 50
                )
                game._lobby.generate()
                target_zone = game._lobby
        elif state_config.zone_type == "dungeon":
            if state_config.floor is not None:
                if state_config.floor not in game.dungeons:
                    from ..world.dungeon import Dungeon
                    from ..config import MAP_WIDTH, MAP_HEIGHT
                    new_dungeon = Dungeon(MAP_WIDTH, MAP_HEIGHT, state_config.floor)
                    new_dungeon.generate()
                    game.dungeons[state_config.floor] = new_dungeon
                target_zone = game.dungeons[state_config.floor]
            else:
                target_zone = game.dungeon if game.dungeon else None
        else:
            target_zone = npc_zone  # Mantener en zona actual
        
        if not target_zone:
            return False
        
        # Obtener posición destino
        target_pos = state_config.position
        if not target_pos:
            # Usar posición del jugador si está en la zona destino
            if target_zone == game.dungeon and game.player:
                target_pos = (game.player.x, game.player.y)
            else:
                # Posición por defecto (centro)
                target_pos = (target_zone.width // 2, target_zone.height // 2)
        
        # Verificar que la posición sea válida (walkable)
        if hasattr(target_zone, 'is_walkable'):
            if not target_zone.is_walkable(target_pos[0], target_pos[1]):
                # Buscar una posición válida cerca
                found = False
                for dx in range(-5, 6):
                    for dy in range(-5, 6):
                        test_x = target_pos[0] + dx
                        test_y = target_pos[1] + dy
                        if (0 <= test_x < target_zone.width and 
                            0 <= test_y < target_zone.height and
                            target_zone.is_walkable(test_x, test_y) and
                            not target_zone.get_blocking_entity_at(test_x, test_y)):
                            target_pos = (test_x, test_y)
                            found = True
                            break
                    if found:
                        break
                if not found:
                    # Si no se encuentra, usar posición del jugador o centro
                    if game.player and target_zone == game.dungeon:
                        target_pos = (game.player.x, game.player.y)
                    else:
                        target_pos = (target_zone.width // 2, target_zone.height // 2)
        
        # Mover NPC a zona destino si es necesario
        if npc_zone != target_zone:
            if npc in npc_zone.entities:
                npc_zone.entities.remove(npc)
            if npc not in target_zone.entities:
                target_zone.entities.append(npc)
            npc.dungeon = target_zone
        else:
            # Asegurar que el NPC esté en la lista de entidades de la zona
            if npc not in target_zone.entities:
                target_zone.entities.append(npc)
        
        # Mover a posición destino
        npc.x, npc.y = target_pos
        
        # Asegurar que el NPC esté visible (no bloqueado por otra entidad)
        if hasattr(target_zone, 'get_blocking_entity_at'):
            blocking = target_zone.get_blocking_entity_at(npc.x, npc.y)
            if blocking and blocking != npc:
                # Si hay otra entidad bloqueando, buscar posición libre cerca
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        test_x = npc.x + dx
                        test_y = npc.y + dy
                        if (0 <= test_x < target_zone.width and 
                            0 <= test_y < target_zone.height and
                            target_zone.is_walkable(test_x, test_y) and
                            not target_zone.get_blocking_entity_at(test_x, test_y)):
                            npc.x, npc.y = test_x, test_y
                            break
                    else:
                        continue
                    break
        
        # Asignar sprite si no tiene
        if not hasattr(npc, 'sprite') or npc.sprite is None:
            from ..ui.sprite_manager import sprite_manager
            try:
                npc.sprite = sprite_manager.get_creature_sprite(npc_name.lower())
            except Exception:
                pass
        
        # Configurar diálogo según el estado usando el sistema FSM
        from ..systems.npc_states import npc_state_manager as fsm_manager
        dialog = fsm_manager.get_dialog_for_state(npc_name, state_id)
        if dialog:
            if isinstance(dialog, InteractiveText):
                npc.interactive_text = dialog
            else:
                # Es un DialogTree
                dialog_tree = dialog
                # El start_node ya está configurado en el diálogo, no necesitamos cambiarlo
                # a menos que el estado coincida con un nodo específico
                if hasattr(dialog_tree, 'nodes') and state_id in dialog_tree.nodes:
                    # Si el estado coincide con un nodo, usarlo como start_node
                    dialog_tree.start_node = state_id
                # Si no coincide, usar el start_node por defecto del diálogo (ya está configurado)
                npc.interactive_text = InteractiveText.create_dialog(dialog_tree, interaction_key="espacio")
        else:
            # Si no hay diálogo configurado, crear uno básico
            from ..systems.text import TextContent
            npc.interactive_text = InteractiveText.create_simple_text(
                f"Estado: {state_id}",
                title=npc_name,
                auto_close=False
            )
        
        return True
    
    
    def _cmd_merchant(self, _game: 'Game', _args: List[str]) -> List[str]:
        """Comando: merchant — Fuerza aparición del comerciante al 100% en pares (solo esta run, no se guarda)."""
        from ..content.npcs import merchant as merchant_module
        merchant_module._dev_force_spawn = True
        return [
            "[DEV] Comerciante forzado al 100% en plantas pares.",
            "Este cambio NO se guarda. Se resetea al morir o cerrar."
        ]
    
    def _cmd_shop_donate(self, _game: 'Game', args: List[str]) -> List[str]:
        """Comando: shop_donate [cantidad] — Muestra estado o establece total donado."""
        from ..systems.events import event_manager
        from ..systems.shop import (
            refresh_merchant_shop, get_unlocked_count,
            get_unlock_thresholds, MERCHANT_ITEM_POOL,
        )
        
        current_total = event_manager.get_data("merchant_donated_total", 0)
        restock_paid = event_manager.get_data("merchant_restock_paid", False)
        unlocked = get_unlocked_count(current_total)
        thresholds = get_unlock_thresholds()
        max_items = len(MERCHANT_ITEM_POOL)
        
        if not args:
            # Sin argumentos: mostrar estado actual
            messages = [
                f"=== TIENDA DEL COMERCIANTE ===",
                f"Total donado: {current_total} oro",
                f"Items desbloqueados: {unlocked}/{max_items}",
                f"Restock pagado: {'Sí' if restock_paid else 'No'}",
                f"",
            ]
            for i, (item_id, price) in enumerate(MERCHANT_ITEM_POOL):
                status = "✓" if i < unlocked else "✗"
                threshold = thresholds[i]
                messages.append(f"  {status} {item_id} (precio: {price}) — umbral: {threshold}")
            
            if unlocked < max_items:
                next_threshold = thresholds[unlocked]
                messages.append(f"")
                messages.append(f"Siguiente desbloqueo en: {next_threshold - current_total} oro más")
            messages.append(f"Uso: shop_donate <total> para establecer el total donado")
            return messages
        
        try:
            new_total = int(args[0])
            if new_total < 0:
                return ["El total donado no puede ser negativo."]
            
            event_manager.set_data("merchant_donated_total", new_total)
            refresh_merchant_shop()
            
            new_unlocked = get_unlocked_count(new_total)
            messages = [f"[DEV] Total donado: {current_total} → {new_total}"]
            messages.append(f"Items desbloqueados: {new_unlocked}/{max_items}")
            if not restock_paid:
                messages.append("NOTA: El restock no está pagado. La tienda seguirá vacía.")
                messages.append("Usa 'shop_restock' para activar el restock.")
            return messages
        except ValueError:
            return ["Uso: shop_donate <total>  (ej: shop_donate 50)"]
    
    def _cmd_shop_restock(self, _game: 'Game', _args: List[str]) -> List[str]:
        """Comando: shop_restock — Activa el restock de la tienda (gratis, esta run)."""
        from ..systems.events import event_manager
        from ..systems.shop import refresh_merchant_shop, get_unlocked_count
        
        already_paid = event_manager.get_data("merchant_restock_paid", False)
        event_manager.set_data("merchant_restock_paid", True)
        refresh_merchant_shop()
        
        donated_total = event_manager.get_data("merchant_donated_total", 0)
        unlocked = get_unlocked_count(donated_total)
        
        if already_paid:
            return [
                "[DEV] El restock ya estaba activo. Tienda refrescada.",
                f"Items desbloqueados: {unlocked} (donado: {donated_total})",
            ]
        return [
            "[DEV] Restock activado. La tienda tiene stock completo.",
            f"Items desbloqueados: {unlocked} (donado: {donated_total})",
        ]
    
    # ============================================================================
    # SISTEMA DE ESCENARIOS DE TEST
    # ============================================================================
    
    # Cada escenario define:
    #   "events": lista de event_ids a activar
    #   "states": lista de tuplas (npc_name, state_id) para establecer estados FSM
    #   "items":  lista de item_ids a dar al jugador (opcional)
    #   "desc":   descripción corta del escenario
    
    TEST_SCENARIOS = {
        # ── STRANGER ──────────────────────────────────────────────
        "stranger_start": {
            "desc": "Stranger recién encontrado en piso 5",
            "events": ["stranger_floor5_met"],
            "states": [("Stranger", "start")],
        },
        "stranger_mision": {
            "desc": "Stranger en lobby, misión de buscar a la nieta activa",
            "events": [
                "stranger_floor5_met",
                "stranger_lobby_weapons_unlocked",
                "stranger_lobby_potions_unlocked",
                "stranger_help_accepted",
                "granddaughter_spawn_enabled",
            ],
            "states": [("Stranger", "mision_nieta")],
        },
        # ── NIETA: rama obligar ───────────────────────────────────
        "nieta_found": {
            "desc": "Pre-encuentro con nieta (bajar a piso ≥2 para encontrarla)",
            "events": [
                "stranger_floor5_met",
                "stranger_lobby_weapons_unlocked",
                "stranger_lobby_potions_unlocked",
                "stranger_help_accepted",
                "granddaughter_spawn_enabled",
            ],
            "states": [("Stranger", "mision_nieta")],
        },
        "nieta_obligada": {
            "desc": "Nieta obligada en lobby + Stranger en mision_capturar_nieta",
            "events": [
                "stranger_floor5_met",
                "stranger_lobby_weapons_unlocked",
                "stranger_lobby_potions_unlocked",
                "stranger_help_accepted",
                "granddaughter_spawn_enabled",
                "granddaughter_found",
                "mision_capturar_nieta_started",
                "nieta_obligada",
            ],
            "states": [
                ("Stranger", "mision_capturar_nieta"),
                ("nieta", "obligada"),
            ],
        },
        # ── NIETA: rama ayudar ────────────────────────────────────
        "nieta_ayudando": {
            "desc": "Nieta esperando en piso 1 + Stranger dando pociones",
            "events": [
                "stranger_floor5_met",
                "stranger_lobby_weapons_unlocked",
                "stranger_lobby_potions_unlocked",
                "stranger_help_accepted",
                "granddaughter_spawn_enabled",
                "granddaughter_found",
                "mision_nieta_ayudar_started",
                "nieta_ayudando",
            ],
            "states": [
                ("Stranger", "mision_nieta_ayudar"),
                ("nieta", "ayudando"),
            ],
        },
        "stranger_indignado": {
            "desc": "Stranger indignado en lobby (ir al lobby para hablarle)",
            "events": [
                "stranger_floor5_met",
                "stranger_lobby_weapons_unlocked",
                "stranger_lobby_potions_unlocked",
                "stranger_help_accepted",
                "granddaughter_spawn_enabled",
                "granddaughter_found",
                "mision_nieta_ayudar_started",
                "nieta_ayudando",
                "stranger_indignado",
            ],
            "states": [
                ("Stranger", "indignado"),
                ("nieta", "ayudando"),
            ],
        },
        "nieta_descubierta": {
            "desc": "Nieta descubierta en piso 1 (bajar para hablarle)",
            "events": [
                "stranger_floor5_met",
                "stranger_lobby_weapons_unlocked",
                "stranger_lobby_potions_unlocked",
                "stranger_help_accepted",
                "granddaughter_spawn_enabled",
                "granddaughter_found",
                "mision_nieta_ayudar_started",
                "nieta_ayudando",
                "stranger_indignado",
            ],
            "states": [
                ("Stranger", "indignado"),
                ("nieta", "descubierta"),
            ],
        },
        "stranger_contratado": {
            "desc": "Post-descubierta: Stranger con mercenario, nieta con diálogo corto",
            "events": [
                "stranger_floor5_met",
                "stranger_lobby_weapons_unlocked",
                "stranger_lobby_potions_unlocked",
                "stranger_help_accepted",
                "granddaughter_spawn_enabled",
                "granddaughter_found",
                "mision_nieta_ayudar_started",
                "nieta_ayudando",
                "stranger_indignado",
                "nieta_descubierta",
            ],
            "states": [
                ("Stranger", "contratado_mercenario"),
                ("nieta", "descubierta"),
            ],
        },
        "nieta_veneno": {
            "desc": "Igual que stranger_contratado + veneno en inventario",
            "events": [
                "stranger_floor5_met",
                "stranger_lobby_weapons_unlocked",
                "stranger_lobby_potions_unlocked",
                "stranger_help_accepted",
                "granddaughter_spawn_enabled",
                "granddaughter_found",
                "mision_nieta_ayudar_started",
                "nieta_ayudando",
                "stranger_indignado",
                "nieta_descubierta",
            ],
            "states": [
                ("Stranger", "contratado_mercenario"),
                ("nieta", "descubierta"),
            ],
            "items": ["poison_potion"],
        },
        "nieta_huida": {
            "desc": "Post-veneno: nieta huye, Stranger desaparece (ambos en ningún sitio)",
            "events": [
                "stranger_floor5_met",
                "stranger_lobby_weapons_unlocked",
                "stranger_lobby_potions_unlocked",
                "stranger_help_accepted",
                "granddaughter_spawn_enabled",
                "granddaughter_found",
                "mision_nieta_ayudar_started",
                "nieta_ayudando",
                "stranger_indignado",
                "nieta_descubierta",
                "nieta_veneno_entregado",
            ],
            "states": [
                ("Stranger", "desaparecido"),
                ("nieta", "huida"),
            ],
        },
    }
    
    def _cmd_scenario(self, game: 'Game', args: List[str]) -> List[str]:
        """Comando: scenario <nombre>"""
        if not args:
            messages = [
                "=== ESCENARIOS DE TEST ===",
                "Uso: scenario <nombre>",
                "",
            ]
            for name, data in self.TEST_SCENARIOS.items():
                messages.append(f"  {name:25} {data['desc']}")
            messages.append("")
            messages.append("Cada escenario configura eventos + estados de NPC de golpe.")
            return messages
        
        scenario_name = args[0].lower()
        
        if scenario_name not in self.TEST_SCENARIOS:
            return [
                f"Escenario '{scenario_name}' no existe.",
                "Escribe 'scenario' sin argumentos para ver la lista.",
            ]
        
        scenario = self.TEST_SCENARIOS[scenario_name]
        messages = [f"=== Cargando escenario: {scenario_name} ==="]
        messages.append(f"  {scenario['desc']}")
        messages.append("")
        
        from ..systems.events import event_manager
        from ..systems.npc_states import npc_state_manager, StateCompletion
        
        # 1. Activar eventos
        events_triggered = 0
        for event_id in scenario.get("events", []):
            if not event_manager.is_event_triggered(event_id):
                result = event_manager.trigger_event(event_id, game.player, game.dungeon, skip_conditions=True)
                if result:
                    events_triggered += 1
                else:
                    messages.append(f"  ⚠ Evento '{event_id}' no se pudo activar (¿no registrado?)")
        messages.append(f"  ✓ {events_triggered} eventos activados")
        
        # 2. Establecer estados de NPC
        for npc_name, state_id in scenario.get("states", []):
            # Marcar todos los estados previos del NPC como COMPLETED
            all_states = npc_state_manager.get_all_npc_states(npc_name)
            current = npc_state_manager.get_current_state(npc_name)
            if current and current != state_id:
                npc_state_manager.set_state_completion(npc_name, current, StateCompletion.COMPLETED)
            
            # Establecer nuevo estado
            npc_state_manager.set_current_state(npc_name, state_id)
            npc_state_manager.set_state_completion(npc_name, state_id, StateCompletion.IN_PROGRESS)
            messages.append(f"  ✓ {npc_name} → estado '{state_id}'")
        
        # 3. Dar items al jugador
        items_given = 0
        for item_id in scenario.get("items", []):
            try:
                from ..items.item import create_item
                item = create_item(item_id, x=game.player.x, y=game.player.y)
                if item and len(game.player.inventory) < 26:
                    game.player.inventory.append(item)
                    items_given += 1
            except Exception:
                messages.append(f"  ⚠ No se pudo dar item '{item_id}'")
        if items_given > 0:
            messages.append(f"  ✓ {items_given} items añadidos al inventario")
        
        # 4. Eliminar NPCs actuales de la zona para forzar respawn limpio
        npc_names_affected = {name for name, _ in scenario.get("states", [])}
        zone = game.dungeon
        removed = 0
        for entity in list(zone.entities):
            if entity.name in npc_names_affected and entity != game.player:
                zone.entities.remove(entity)
                removed += 1
        # También limpiar del lobby si existe
        if hasattr(game, '_lobby') and game._lobby:
            for entity in list(game._lobby.entities):
                if entity.name in npc_names_affected:
                    game._lobby.entities.remove(entity)
                    removed += 1
        if removed > 0:
            messages.append(f"  ✓ {removed} NPCs eliminados de zona (se respawnearán)")
        
        messages.append("")
        messages.append("Escenario cargado. Cambia de zona para ver los NPCs actualizados.")
        return messages
    
    def _cmd_help(self, _game: 'Game', _args: List[str]) -> List[str]:
        """Comando: help"""
        messages = ["=== COMANDOS DE DESARROLLO ==="]
        for cmd in sorted(self.commands.values(), key=lambda c: c.name):
            messages.append(f"{cmd.name:15} - {cmd.description}")
            messages.append(f"                Uso: {cmd.usage}")
        return messages


# Instancia global del gestor de comandos
dev_command_manager = DevCommandManager()
