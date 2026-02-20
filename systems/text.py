"""
Sistema de textos y diálogos del juego.
Permite crear diálogos interactivos, textos ambientales y conversaciones con NPCs.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..world.zone import Zone


class TextType(Enum):
    """Tipos de texto disponibles."""
    DIALOG = "dialog"  # Diálogo con opciones
    SIMPLE = "simple"  # Texto simple (una sola línea o múltiples)
    AMBIENT = "ambient"  # Texto ambiental (se muestra automáticamente)


@dataclass
class DialogOption:
    """
    Opción en un diálogo.
    
    Attributes:
        text: Texto de la opción
        next_node: ID del siguiente nodo de diálogo (None = cerrar diálogo)
        condition: Función que verifica si la opción está disponible (None = siempre disponible)
        action: Función que se ejecuta al seleccionar esta opción (None = sin acción)
    """
    text: str
    next_node: Optional[str] = None
    condition: Optional[Callable[[Player], bool]] = None
    action: Optional[Callable[[Player, Zone], None]] = None


@dataclass
class DialogNode:
    """
    Nodo de un diálogo (una pantalla de conversación).
    
    Attributes:
        node_id: Identificador único del nodo
        speaker: Nombre del hablante (None = narrador/texto ambiental)
        text: Texto del diálogo (puede ser multilínea con \n)
        options: Lista de opciones disponibles
        auto_advance: Si es True, avanza automáticamente sin opciones
        on_enter: Función que se ejecuta al entrar al nodo (None = sin acción)
    """
    node_id: str
    speaker: Optional[str]
    text: str
    options: List[DialogOption]
    auto_advance: bool = False
    on_enter: Optional[Callable[[], None]] = None


class DialogTree:
    """
    Árbol de diálogo completo.
    
    Permite crear conversaciones complejas con múltiples nodos y opciones.
    
    Attributes:
        nodes: Diccionario de nodos por ID
        start_node: ID del nodo inicial
    """
    
    def __init__(self, start_node: str = "start"):
        """
        Inicializa un árbol de diálogo.
        
        Args:
            start_node: ID del nodo inicial
        """
        self.nodes: Dict[str, DialogNode] = {}
        self.start_node = start_node
    
    def add_node(self, node: DialogNode) -> None:
        """
        Añade un nodo al árbol.
        
        Args:
            node: Nodo a añadir
        """
        self.nodes[node.node_id] = node
    
    def get_node(self, node_id: str) -> Optional[DialogNode]:
        """
        Obtiene un nodo por su ID.
        
        Args:
            node_id: ID del nodo
            
        Returns:
            El nodo o None si no existe
        """
        return self.nodes.get(node_id)
    
    def get_start_node(self) -> Optional[DialogNode]:
        """Obtiene el nodo inicial."""
        return self.get_node(self.start_node)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el árbol de diálogo a diccionario."""
        return {
            "start_node": self.start_node,
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "speaker": node.speaker,
                    "text": node.text,
                    "options": [
                        {
                            "text": opt.text,
                            "next_node": opt.next_node
                        }
                        for opt in node.options
                    ],
                    "auto_advance": node.auto_advance
                }
                for node_id, node in self.nodes.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DialogTree:
        """Crea un árbol de diálogo desde un diccionario."""
        tree = cls(start_node=data["start_node"])
        for node_id, node_data in data["nodes"].items():
            node = DialogNode(
                node_id=node_data["node_id"],
                speaker=node_data.get("speaker"),
                text=node_data["text"],
                options=[
                    DialogOption(
                        text=opt_data["text"],
                        next_node=opt_data.get("next_node")
                    )
                    for opt_data in node_data.get("options", [])
                ],
                auto_advance=node_data.get("auto_advance", False)
            )
            tree.add_node(node)
        return tree


class TextContent:
    """
    Contenedor de texto simple (sin opciones).
    
    Útil para carteles, libros, mensajes ambientales, etc.
    
    Attributes:
        title: Título del texto (opcional)
        lines: Lista de líneas de texto
        auto_close: Si es True, se cierra automáticamente después de mostrar
    """
    
    def __init__(
        self,
        lines: List[str],
        title: Optional[str] = None,
        auto_close: bool = False
    ):
        """
        Inicializa contenido de texto.
        
        Args:
            lines: Lista de líneas de texto
            title: Título opcional
            auto_close: Si se cierra automáticamente
        """
        self.title = title
        self.lines = lines
        self.auto_close = auto_close
    
    @classmethod
    def from_string(cls, text: str, title: Optional[str] = None, auto_close: bool = False) -> TextContent:
        """
        Crea contenido de texto desde un string (separa por líneas).
        
        Args:
            text: Texto completo (puede tener \n para múltiples líneas)
            title: Título opcional
            auto_close: Si se cierra automáticamente
        """
        lines = text.split('\n')
        return cls(lines, title, auto_close)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el contenido de texto a diccionario."""
        return {
            "lines": self.lines,
            "title": self.title,
            "auto_close": self.auto_close
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TextContent:
        """Crea contenido de texto desde un diccionario."""
        return cls(
            lines=data.get("lines", []),
            title=data.get("title"),
            auto_close=data.get("auto_close", False)
        )


class InteractiveText:
    """
    Componente que puede añadirse a entidades u objetos para hacerlos interactivos.
    
    Permite que cualquier entidad u objeto muestre diálogos o textos al interactuar.
    
    Attributes:
        text_type: Tipo de texto (DIALOG, SIMPLE, AMBIENT)
        dialog_tree: Árbol de diálogo (si text_type es DIALOG)
        text_content: Contenido de texto simple (si text_type es SIMPLE)
        interaction_key: Tecla para interactuar (por defecto 'e' o ENTER)
        auto_trigger: Si es True, se activa automáticamente al acercarse
    """
    
    def __init__(
        self,
        text_type: TextType,
        dialog_tree: Optional[DialogTree] = None,
        text_content: Optional[TextContent] = None,
        interaction_key: str = "espacio",
        auto_trigger: bool = False
    ):
        """
        Inicializa componente de texto interactivo.
        
        Args:
            text_type: Tipo de texto
            dialog_tree: Árbol de diálogo (requerido si text_type es DIALOG)
            text_content: Contenido de texto (requerido si text_type es SIMPLE)
            interaction_key: Tecla para interactuar
            auto_trigger: Si se activa automáticamente
        """
        self.text_type = text_type
        self.dialog_tree = dialog_tree
        self.text_content = text_content
        self.interaction_key = interaction_key
        self.auto_trigger = auto_trigger
        
        # Validar que los datos requeridos estén presentes
        if text_type == TextType.DIALOG and dialog_tree is None:
            raise ValueError("DialogTree requerido para tipo DIALOG")
        if text_type == TextType.SIMPLE and text_content is None:
            raise ValueError("TextContent requerido para tipo SIMPLE")
    
    @classmethod
    def create_dialog(cls, dialog_tree: DialogTree, interaction_key: str = "e") -> InteractiveText:
        """
        Crea un componente de diálogo.
        
        Args:
            dialog_tree: Árbol de diálogo
            interaction_key: Tecla para interactuar
            
        Returns:
            Componente InteractiveText configurado para diálogo
        """
        return cls(TextType.DIALOG, dialog_tree=dialog_tree, interaction_key=interaction_key)
    
    @classmethod
    def create_simple_text(
        cls,
        text: str,
        title: Optional[str] = None,
        interaction_key: str = "espacio",
        auto_close: bool = False
    ) -> InteractiveText:
        """
        Crea un componente de texto simple.
        
        Args:
            text: Texto a mostrar (puede tener \n para múltiples líneas)
            title: Título opcional
            interaction_key: Tecla para interactuar
            auto_close: Si se cierra automáticamente
            
        Returns:
            Componente InteractiveText configurado para texto simple
        """
        content = TextContent.from_string(text, title, auto_close)
        return cls(TextType.SIMPLE, text_content=content, interaction_key=interaction_key)
    
    @classmethod
    def create_ambient_text(cls, text: str, title: Optional[str] = None) -> InteractiveText:
        """
        Crea un componente de texto ambiental (se muestra automáticamente).
        
        Args:
            text: Texto a mostrar
            title: Título opcional
            
        Returns:
            Componente InteractiveText configurado para texto ambiental
        """
        content = TextContent.from_string(text, title, auto_close=True)
        return cls(TextType.AMBIENT, text_content=content, auto_trigger=True)
