"""
Clase base Entity para todas las entidades del juego.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple, Dict, Any

if TYPE_CHECKING:
    from ..world.dungeon import Dungeon


class Entity:
    """
    Clase base para todas las entidades del juego (jugador, monstruos, items).
    
    Attributes:
        x: Posición X en el mapa
        y: Posición Y en el mapa
        char: Caracter ASCII que representa la entidad
        name: Nombre de la entidad
        color: Color para renderizar
        blocks: Si la entidad bloquea el movimiento
        dungeon: Referencia a la mazmorra actual
    """
    
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        name: str = "Entidad",
        color: str = "white",
        blocks: bool = True,
        dungeon: Optional[Dungeon] = None
    ) -> None:
        """
        Inicializa una nueva entidad.
        
        Args:
            x: Posición X inicial
            y: Posición Y inicial
            char: Caracter ASCII
            name: Nombre de la entidad
            color: Color (clave del diccionario COLORS)
            blocks: Si bloquea movimiento
            dungeon: Referencia a la mazmorra
        """
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        self.dungeon = dungeon
    
    @property
    def position(self) -> Tuple[int, int]:
        """Retorna la posición como tupla."""
        return (self.x, self.y)
    
    @position.setter
    def position(self, value: Tuple[int, int]) -> None:
        """Establece la posición desde una tupla."""
        self.x, self.y = value
    
    def move(self, dx: int, dy: int) -> bool:
        """
        Mueve la entidad en la dirección especificada.
        
        Args:
            dx: Desplazamiento en X
            dy: Desplazamiento en Y
            
        Returns:
            True si el movimiento fue exitoso, False si no
        """
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Verificar si el movimiento es válido
        if self.dungeon and self.dungeon.is_walkable(new_x, new_y):
            self.x = new_x
            self.y = new_y
            return True
        return False
    
    def distance_to(self, other: Entity) -> float:
        """
        Calcula la distancia euclidiana a otra entidad.
        
        Args:
            other: Otra entidad
            
        Returns:
            Distancia como float
        """
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def distance_to_point(self, x: int, y: int) -> float:
        """
        Calcula la distancia euclidiana a un punto.
        
        Args:
            x: Coordenada X del punto
            y: Coordenada Y del punto
            
        Returns:
            Distancia como float
        """
        return ((self.x - x) ** 2 + (self.y - y) ** 2) ** 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa la entidad a diccionario.
        
        Returns:
            Diccionario con los datos de la entidad
        """
        data: Dict[str, Any] = {
            "x": self.x,
            "y": self.y,
            "char": self.char,
            "name": self.name,
            "color": self.color,
            "blocks": self.blocks,
        }
        
        # Guardar sprite si existe (solo el nombre, no el objeto)
        if hasattr(self, 'sprite') and self.sprite is not None:
            # No guardamos el sprite directamente, solo marcamos que tiene uno
            # El sprite se restaurará basándose en el nombre de la entidad
            pass
        
        # Guardar interactive_text si existe
        if hasattr(self, 'interactive_text') and self.interactive_text:
            from ..systems.text import TextType
            it = self.interactive_text
            # Obtener el valor del enum TextType
            text_type_value = it.text_type.value if hasattr(it.text_type, 'value') else str(it.text_type)
            it_data: Dict[str, Any] = {
                "text_type": text_type_value,
                "interaction_key": it.interaction_key,
            }
            
            if it.text_type == TextType.DIALOG and it.dialog_tree:
                # Guardar el árbol de diálogo completo
                it_data["dialog_tree"] = it.dialog_tree.to_dict()
                # IMPORTANTE: Guardar el start_node actual para preservar el estado del diálogo
                # Esto permite que el NPC recuerde en qué punto del diálogo estaba
                it_data["dialog_start_node"] = it.dialog_tree.start_node
            elif it.text_type in (TextType.SIMPLE, TextType.AMBIENT) and it.text_content:
                it_data["text_content"] = it.text_content.to_dict()
            
            data["interactive_text"] = it_data
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], dungeon: Optional[Dungeon] = None) -> 'Entity':
        """
        Crea una entidad desde un diccionario.
        
        Args:
            data: Diccionario con los datos
            dungeon: Referencia a la mazmorra
            
        Returns:
            Nueva instancia de Entity
        """
        entity = cls(
            x=data["x"],
            y=data["y"],
            char=data.get("char", "?"),
            name=data.get("name", "Entidad"),
            color=data.get("color", "white"),
            blocks=data.get("blocks", True),
            dungeon=dungeon
        )
        
        # Restaurar interactive_text si existe
        if "interactive_text" in data and data["interactive_text"]:
            from ..systems.text import InteractiveText, TextContent, DialogTree
            it_data = data["interactive_text"]
            text_type = it_data["text_type"]
            
            if text_type == "DIALOG":
                dialog_tree = DialogTree.from_dict(it_data["dialog_tree"])
                # IMPORTANTE: Restaurar el start_node guardado para preservar el estado del diálogo
                if "dialog_start_node" in it_data and it_data["dialog_start_node"] in dialog_tree.nodes:
                    dialog_tree.start_node = it_data["dialog_start_node"]
                entity.interactive_text = InteractiveText.create_dialog(
                    dialog_tree, 
                    it_data.get("interaction_key", "espacio")
                )
            elif text_type in ("SIMPLE", "AMBIENT"):
                text_content = TextContent.from_dict(it_data["text_content"])
                entity.interactive_text = InteractiveText.create_simple_text(
                    "\n".join(text_content.lines),
                    title=text_content.title,
                    interaction_key=it_data.get("interaction_key", "espacio"),
                    auto_close=text_content.auto_close
        )
        
        return entity
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name} at ({self.x}, {self.y}))"


class Fighter:
    """
    Componente de combate para entidades que pueden pelear.
    
    Attributes:
        max_hp: Puntos de vida máximos
        hp: Puntos de vida actuales
        base_attack: Ataque base
        base_defense: Defensa base
        xp: Experiencia (para monstruos, lo que dan al morir)
        level: Nivel actual
    """
    
    def __init__(
        self,
        max_hp: int,
        attack: int,
        defense: int,
        xp: int = 0,
        level: int = 1
    ) -> None:
        """
        Inicializa el componente de combate.
        
        Args:
            max_hp: HP máximo
            attack: Ataque base
            defense: Defensa base
            xp: Experiencia que otorga
            level: Nivel inicial
        """
        self.max_hp = max_hp
        self._hp = max_hp
        self.base_attack = attack
        self.base_defense = defense
        self.xp = xp
        self.level = level
        
        # Bonificadores temporales
        self.attack_bonus = 0
        self.defense_bonus = 0
        self.bonus_duration = 0
    
    @property
    def hp(self) -> int:
        """Retorna HP actual."""
        return self._hp
    
    @hp.setter
    def hp(self, value: int) -> None:
        """Establece HP, limitado entre 0 y max_hp."""
        self._hp = max(0, min(value, self.max_hp))
    
    @property
    def attack(self) -> int:
        """Retorna ataque total (base + bonificadores)."""
        return self.base_attack + self.attack_bonus
    
    @property
    def defense(self) -> int:
        """Retorna defensa total (base + bonificadores)."""
        return self.base_defense + self.defense_bonus
    
    @property
    def is_dead(self) -> bool:
        """Verifica si la entidad está muerta."""
        return self._hp <= 0
    
    def take_damage(self, amount: int) -> int:
        """
        Aplica daño a la entidad.
        
        Args:
            amount: Cantidad de daño
            
        Returns:
            Daño real aplicado
        """
        actual_damage = max(0, amount)
        self.hp -= actual_damage
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Cura a la entidad.
        
        Args:
            amount: Cantidad a curar
            
        Returns:
            Cantidad real curada
        """
        old_hp = self.hp
        self.hp += amount
        return self.hp - old_hp
    
    def update_bonuses(self) -> None:
        """Actualiza los bonificadores temporales."""
        if self.bonus_duration > 0:
            self.bonus_duration -= 1
            if self.bonus_duration <= 0:
                self.attack_bonus = 0
                self.defense_bonus = 0
