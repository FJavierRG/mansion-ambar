"""
Módulo de entidades del juego.
Contiene las clases base y específicas para jugador y monstruos.
"""
from .entity import Entity
from .player import Player
from .monster import Monster

__all__ = ["Entity", "Player", "Monster"]
