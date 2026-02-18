"""
Módulo de sistemas del juego.
Contiene lógica de combate, FOV, inventario, animaciones y diálogos.
"""
from .combat import Combat
from .fov import FOV
from .inventory import Inventory
from .animation import AnimationManager
from .text import (
    DialogTree, DialogNode, DialogOption,
    TextContent, InteractiveText, TextType
)
from .dialog_manager import dialog_manager

__all__ = [
    "Combat", "FOV", "Inventory", "AnimationManager",
    "DialogTree", "DialogNode", "DialogOption",
    "TextContent", "InteractiveText", "TextType",
    "dialog_manager"
]
