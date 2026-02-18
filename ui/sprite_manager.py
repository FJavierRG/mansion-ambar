"""
Gestor de sprites para el juego roguelike.
Carga y maneja sprites PNG para criaturas e items.
"""
from __future__ import annotations
import os
from typing import Dict, Optional, Tuple
import pygame

from ..config import TILE_SIZE


class SpriteManager:
    """
    Gestor de sprites del juego.
    
    Carga sprites PNG desde carpetas y los escala al tamaño de tile.
    Mantiene cache de sprites para mejor rendimiento.
    """
    
    # Mapeo de tipos de monstruo a nombres de archivo
    CREATURE_SPRITES: Dict[str, str] = {
        # Jugador
        "player": "pj.png",
        
        # Monstruos
        "rat": "rat.png",
        "bat": "murcielago.png",
        "goblin": "goblin.png",
        "snake": "serpiente.png",
        "skeleton": "esqueleto.png",
        "orc": "orco.png",
        "zombie": "zombie.png",
        "wraith": "espectro.png",
        "troll": "troll.png",
        "dragon": "dragon.png",
        "ancient_dragon": "dragon anciano.png",
        "stranger": "stranger.png",  # NPC especial
        "nieta": "nieta.png",  # Nieta del Stranger
        "alquimista": "alchemist.png",  # Alquimista
    }
    
    # Mapeo de terreno especial (escaleras)
    TERRAIN_SPRITES: Dict[str, str] = {
        "stairs_down": "Escaleras abajo.png",
        "stairs_up": "Escaleras arriba.png",
    }
    
    # Mapeo de tipos de item a nombres de archivo
    ITEM_SPRITES: Dict[str, str] = {
        "potion": "pocion.png",
        "scroll": "pergamino.png",
        "weapon": "arma.png",
        "armor": "armadura.png",
        "gold": "oro.png",
        "amulet": "amuleto.png",
        "ring": "anilo.png",  # El archivo tiene este nombre
    }
    
    def __init__(self) -> None:
        """Inicializa el gestor de sprites."""
        self._creature_cache: Dict[str, pygame.Surface] = {}
        self._item_cache: Dict[str, pygame.Surface] = {}
        self._terrain_cache: Dict[str, pygame.Surface] = {}
        self._loaded = False
        
        # Ruta base a los sprites
        self._base_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "sprites"
        )
        self._creatures_path = os.path.join(self._base_path, "criaturas")
        self._items_path = os.path.join(self._base_path, "objetos")
    
    def load_sprites(self) -> None:
        """Carga todos los sprites en memoria."""
        if self._loaded:
            return
        
        # Cargar sprites de criaturas
        for creature_type, filename in self.CREATURE_SPRITES.items():
            sprite = self._load_sprite(self._creatures_path, filename)
            if sprite:
                self._creature_cache[creature_type] = sprite
        
        # Cargar sprites de items
        for item_type, filename in self.ITEM_SPRITES.items():
            sprite = self._load_sprite(self._items_path, filename)
            if sprite:
                self._item_cache[item_type] = sprite
        
        # Cargar sprites de terreno (escaleras están en carpeta criaturas)
        for terrain_type, filename in self.TERRAIN_SPRITES.items():
            sprite = self._load_sprite(self._creatures_path, filename)
            if sprite:
                self._terrain_cache[terrain_type] = sprite
        
        self._loaded = True
        print(f"[SpriteManager] Cargados {len(self._creature_cache)} sprites de criaturas")
        print(f"[SpriteManager] Cargados {len(self._item_cache)} sprites de items")
        print(f"[SpriteManager] Cargados {len(self._terrain_cache)} sprites de terreno")
    
    def _load_sprite(self, folder: str, filename: str) -> Optional[pygame.Surface]:
        """
        Carga un sprite desde archivo.
        
        Args:
            folder: Carpeta donde está el sprite
            filename: Nombre del archivo
            
        Returns:
            Surface de pygame o None si no se pudo cargar
        """
        filepath = os.path.join(folder, filename)
        
        try:
            if os.path.exists(filepath):
                # Cargar con soporte de transparencia
                sprite = pygame.image.load(filepath).convert_alpha()
                
                # Escalar al tamaño de tile si es necesario
                if sprite.get_width() != TILE_SIZE or sprite.get_height() != TILE_SIZE:
                    sprite = pygame.transform.scale(sprite, (TILE_SIZE, TILE_SIZE))
                
                return sprite
            else:
                print(f"[SpriteManager] Archivo no encontrado: {filepath}")
                return None
        except pygame.error as e:
            print(f"[SpriteManager] Error cargando {filepath}: {e}")
            return None
    
    def get_creature_sprite(self, creature_type: str) -> Optional[pygame.Surface]:
        """
        Obtiene el sprite de una criatura.
        
        Args:
            creature_type: Tipo de criatura (ej: "goblin", "player")
            
        Returns:
            Surface del sprite o None si no existe
        """
        if not self._loaded:
            self.load_sprites()
        return self._creature_cache.get(creature_type)
    
    def get_item_sprite(self, item_type: str) -> Optional[pygame.Surface]:
        """
        Obtiene el sprite de un item.
        
        Args:
            item_type: Tipo de item (ej: "potion", "weapon")
            
        Returns:
            Surface del sprite o None si no existe
        """
        if not self._loaded:
            self.load_sprites()
        return self._item_cache.get(item_type)
    
    def has_creature_sprite(self, creature_type: str) -> bool:
        """Verifica si existe sprite para una criatura."""
        if not self._loaded:
            self.load_sprites()
        return creature_type in self._creature_cache
    
    def has_item_sprite(self, item_type: str) -> bool:
        """Verifica si existe sprite para un item."""
        if not self._loaded:
            self.load_sprites()
        return item_type in self._item_cache
    
    def get_terrain_sprite(self, terrain_type: str) -> Optional[pygame.Surface]:
        """
        Obtiene el sprite de un elemento de terreno.
        
        Args:
            terrain_type: Tipo de terreno (ej: "stairs_down", "stairs_up")
            
        Returns:
            Surface del sprite o None si no existe
        """
        if not self._loaded:
            self.load_sprites()
        return self._terrain_cache.get(terrain_type)
    
    def has_terrain_sprite(self, terrain_type: str) -> bool:
        """Verifica si existe sprite para un terreno."""
        if not self._loaded:
            self.load_sprites()
        return terrain_type in self._terrain_cache


# Instancia global del gestor de sprites
sprite_manager = SpriteManager()
