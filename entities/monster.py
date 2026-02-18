"""
Clase Monster - Enemigos del juego.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple
import random

from .entity import Entity, Fighter
from ..config import MONSTER_DATA, COLORS

if TYPE_CHECKING:
    from ..world.dungeon import Dungeon
    from .player import Player


class Monster(Entity):
    """
    Clase para los monstruos enemigos.
    
    Attributes:
        fighter: Componente de combate
        monster_type: Tipo de monstruo (clave en MONSTER_DATA)
        ai_state: Estado actual de la IA
        target: Objetivo actual (normalmente el jugador)
        is_boss: Si es un jefe
    """
    
    def __init__(
        self,
        x: int,
        y: int,
        monster_type: str,
        dungeon: Optional[Dungeon] = None
    ) -> None:
        """
        Inicializa un monstruo.
        
        Args:
            x: Posición X
            y: Posición Y
            monster_type: Tipo de monstruo
            dungeon: Referencia a la mazmorra
        """
        data = MONSTER_DATA.get(monster_type, MONSTER_DATA["rat"])
        
        super().__init__(
            x=x,
            y=y,
            char=data["symbol"],
            name=data["name"],
            color=data["color"],
            blocks=True,
            dungeon=dungeon
        )
        
        self.monster_type = monster_type
        self.is_boss = data.get("is_boss", False)
        
        # Componente de combate
        self.fighter = Fighter(
            max_hp=data["hp"],
            attack=data["attack"],
            defense=data["defense"],
            xp=data["xp"]
        )
        
        # IA
        self.ai_state = "idle"  # idle, hunting, fleeing
        self.target: Optional[Player] = None
        self.last_known_player_pos: Optional[Tuple[int, int]] = None
    
    def update(self, player: Player, fov_map: set, animation_manager=None) -> List[str]:
        """
        Actualiza el monstruo (IA y acciones).
        
        Args:
            player: Referencia al jugador
            fov_map: Conjunto de tiles visibles por el jugador
            animation_manager: Gestor de animaciones (opcional)
            
        Returns:
            Lista de mensajes generados
        """
        messages = []
        
        if self.fighter.is_dead:
            return messages
        
        # Verificar si el monstruo puede ver al jugador
        can_see_player = self._can_see_player(player)
        
        if can_see_player:
            self.ai_state = "hunting"
            self.target = player
            self.last_known_player_pos = (player.x, player.y)
        elif self.ai_state == "hunting" and self.last_known_player_pos:
            # Ir a la última posición conocida
            if (self.x, self.y) == self.last_known_player_pos:
                self.ai_state = "idle"
                self.last_known_player_pos = None
        
        # Ejecutar acción según estado
        if self.ai_state == "hunting" and self.target:
            messages.extend(self._hunt_player(player, animation_manager))
        elif self.ai_state == "idle":
            self._wander()
        
        return messages
    
    def _can_see_player(self, player: Player) -> bool:
        """
        Verifica si el monstruo puede ver al jugador.
        
        Args:
            player: El jugador
            
        Returns:
            True si puede ver al jugador
        """
        from ..systems.fov import FOV
        
        distance = self.distance_to(player)
        if distance > 8:  # Rango de visión del monstruo
            return False
        
        # Verificar línea de visión
        if self.dungeon:
            return FOV.has_line_of_sight(
                self.dungeon, self.x, self.y, player.x, player.y
            )
        return False
    
    def _hunt_player(self, player: Player, animation_manager=None) -> List[str]:
        """
        Persigue y ataca al jugador.
        
        Args:
            player: El jugador
            animation_manager: Gestor de animaciones (opcional)
            
        Returns:
            Lista de mensajes
        """
        messages = []
        
        # Si está adyacente, atacar
        if self.distance_to(player) < 1.5:
            messages.extend(self._attack_player(player, animation_manager))
        else:
            # Moverse hacia el jugador
            self._move_towards(player.x, player.y)
        
        return messages
    
    def _attack_player(self, player: Player, animation_manager=None) -> List[str]:
        """
        Ataca al jugador.
        
        Args:
            player: El jugador
            animation_manager: Gestor de animaciones (opcional)
            
        Returns:
            Lista de mensajes de combate
        """
        from ..systems.combat import Combat
        return Combat.attack(self, player, animation_manager)
    
    def _move_towards(self, target_x: int, target_y: int) -> bool:
        """
        Mueve el monstruo hacia una posición objetivo.
        
        Args:
            target_x: X objetivo
            target_y: Y objetivo
            
        Returns:
            True si se movió
        """
        dx = target_x - self.x
        dy = target_y - self.y
        
        # Normalizar dirección
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)
        
        # Intentar moverse en diagonal primero
        if dx != 0 and dy != 0:
            if self._try_move(dx, dy):
                return True
        
        # Intentar moverse en una dirección
        if dx != 0:
            if self._try_move(dx, 0):
                return True
        if dy != 0:
            if self._try_move(0, dy):
                return True
        
        # Intentar la otra dirección diagonal
        if dx != 0 and dy != 0:
            if self._try_move(dx, 0):
                return True
            if self._try_move(0, dy):
                return True
        
        return False
    
    def _try_move(self, dx: int, dy: int) -> bool:
        """
        Intenta moverse en una dirección.
        
        Args:
            dx: Desplazamiento X
            dy: Desplazamiento Y
            
        Returns:
            True si el movimiento fue exitoso
        """
        new_x = self.x + dx
        new_y = self.y + dy
        
        if self.dungeon:
            # Verificar que sea caminable y no haya otra entidad
            if self.dungeon.is_walkable(new_x, new_y):
                # Verificar que no haya otro monstruo
                for entity in self.dungeon.entities:
                    if entity.x == new_x and entity.y == new_y and entity.blocks:
                        return False
                
                self.x = new_x
                self.y = new_y
                return True
        return False
    
    def _wander(self) -> None:
        """Movimiento aleatorio cuando está idle."""
        if random.random() < 0.3:  # 30% de probabilidad de moverse
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            if dx != 0 or dy != 0:
                self._try_move(dx, dy)
    
    def die(self) -> List[str]:
        """
        Procesa la muerte del monstruo.
        
        Returns:
            Lista de mensajes
        """
        messages = []
        messages.append(f"¡El {self.name} muere!")
        
        # Cambiar apariencia a cadáver
        self.char = "%"
        self.color = "dark_gray"
        self.blocks = False
        self.name = f"restos de {self.name}"
        
        return messages
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el monstruo a un diccionario.
        
        Returns:
            Diccionario con los datos
        """
        return {
            "x": self.x,
            "y": self.y,
            "monster_type": self.monster_type,
            "hp": self.fighter.hp,
            "ai_state": self.ai_state,
            "is_dead": self.fighter.is_dead,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], dungeon: Optional[Dungeon] = None) -> Monster:
        """
        Crea un monstruo desde un diccionario.
        
        Args:
            data: Diccionario con los datos
            dungeon: Referencia a la mazmorra
            
        Returns:
            Nueva instancia de Monster
        """
        monster = cls(
            x=data["x"],
            y=data["y"],
            monster_type=data["monster_type"],
            dungeon=dungeon
        )
        monster.fighter.hp = data["hp"]
        monster.ai_state = data["ai_state"]
        
        if data.get("is_dead", False):
            monster.char = "%"
            monster.color = "dark_gray"
            monster.blocks = False
        
        # Restaurar interactive_text si existe (para NPCs que son monstruos)
        # Entity.from_dict() ya maneja esto, pero Monster tiene su propia implementación
        # así que necesitamos hacerlo manualmente aquí
        if "interactive_text" in data and data["interactive_text"]:
            from ..systems.text import InteractiveText, TextType, TextContent, DialogTree
            it_data = data["interactive_text"]
            text_type = it_data["text_type"]
            
            if text_type == "DIALOG":
                dialog_tree = DialogTree.from_dict(it_data["dialog_tree"])
                # IMPORTANTE: Restaurar el start_node guardado para preservar el estado del diálogo
                if "dialog_start_node" in it_data and it_data["dialog_start_node"] in dialog_tree.nodes:
                    dialog_tree.start_node = it_data["dialog_start_node"]
                monster.interactive_text = InteractiveText.create_dialog(
                    dialog_tree, 
                    it_data.get("interaction_key", "espacio")
                )
            elif text_type in ("SIMPLE", "AMBIENT"):
                text_content = TextContent.from_dict(it_data["text_content"])
                monster.interactive_text = InteractiveText.create_simple_text(
                    "\n".join(text_content.lines),
                    title=text_content.title,
                    interaction_key=it_data.get("interaction_key", "espacio"),
                    auto_close=text_content.auto_close
                )
        
        return monster


def create_monster_for_floor(floor: int, x: int, y: int, dungeon: Optional[Dungeon] = None) -> Monster:
    """
    Crea un monstruo apropiado para el piso actual.
    
    Args:
        floor: Número de piso
        x: Posición X
        y: Posición Y
        dungeon: Referencia a la mazmorra
        
    Returns:
        Un monstruo apropiado para el nivel
    """
    # Filtrar monstruos válidos para este piso
    valid_monsters = []
    for monster_type, data in MONSTER_DATA.items():
        if data["min_level"] <= floor <= data["max_level"]:
            if not data.get("is_boss", False):  # No incluir jefes normalmente
                valid_monsters.append(monster_type)
    
    if not valid_monsters:
        valid_monsters = ["rat"]  # Fallback
    
    # Elegir uno aleatorio con peso hacia los más débiles
    weights = [1.0 / (i + 1) for i in range(len(valid_monsters))]
    monster_type = random.choices(valid_monsters, weights=weights)[0]
    
    return Monster(x, y, monster_type, dungeon)
