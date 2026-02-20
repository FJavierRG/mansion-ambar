"""
Gestor de sprites para el juego roguelike.
Carga y maneja sprites PNG para criaturas e items.
"""
from __future__ import annotations
import os
from typing import Dict, Generator, Optional, Tuple
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
        "stranger_dead": "stranger_dead.png",  # Cadáver del Stranger
        "nieta": "nieta.png",  # Nieta del Stranger
        "nieta_dead": "nieta_dead.png",  # Cadáver de la Nieta
        "alquimista": "alchemist.png",  # Alquimista
        "comerciante": "merchant.png",  # Comerciante (32x32, no escalar)
        "comerciante errante": "merchant_wanderer.png",  # Comerciante Errante (lobby)
    }
    
    # Sprites de decoración del suelo (sangre, etc.)
    DECORATION_SPRITES: Dict[str, str] = {
        "blood": "blood.png",
    }
    
    # Sprites que NO deben escalarse a TILE_SIZE (mantienen su tamaño original)
    NO_SCALE_CREATURES: set = {
        "comerciante",
    }
    
    # Mapeo de terreno especial (escaleras, puertas)
    TERRAIN_SPRITES: Dict[str, str] = {
        "stairs_down": "Escaleras abajo.png",
        "stairs_up": "Escaleras arriba.png",
        "door_open": "door_open.png",
        "door_closed": "door_close.png",
    }
    
    # Mapeo de tipos de item a nombres de archivo
    ITEM_SPRITES: Dict[str, str] = {
        "potion": "pocion.png",
        "poison_potion": "pocion_veneno.png",
        "scroll": "pergamino.png",
        "weapon": "arma.png",       # Fallback genérico para armas sin sprite
        "armor": "armadura.png",
        "gold": "oro.png",
        "amulet": "amuleto.png",
        "ring": "anilo.png",        # El archivo tiene este nombre
        # Sprites específicos por tipo de arma
        "dagger": "dagger.png",
        "sword": "sword.png",
        "axe": "axe.png",           # También cubre martillos
        "spear": "spear.png",
    }
    
    def __init__(self) -> None:
        """Inicializa el gestor de sprites."""
        self._creature_cache: Dict[str, pygame.Surface] = {}
        self._item_cache: Dict[str, pygame.Surface] = {}
        self._terrain_cache: Dict[str, pygame.Surface] = {}
        self._decoration_cache: Dict[str, pygame.Surface] = {}
        self._loaded = False
        
        # Ruta base a los sprites
        self._base_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "sprites"
        )
        self._creatures_path = os.path.join(self._base_path, "criaturas")
        self._items_path = os.path.join(self._base_path, "objetos")
    
    def load_sprites(self) -> None:
        """Carga todos los sprites en memoria (sin feedback de progreso)."""
        if self._loaded:
            return
        # Consumir el generador de carga completo
        for _ in self.load_sprites_iter():
            pass
    
    def load_sprites_iter(self) -> Generator[Tuple[int, int, str], None, None]:
        """
        Carga todos los sprites emitiendo progreso.
        
        Yields:
            (loaded, total, asset_name) — cantidad cargada, total, nombre del asset actual
        """
        if self._loaded:
            return
        
        # Calcular total de assets
        all_assets: list[Tuple[str, str, str, bool]] = []  # (category, key, filename, scale)
        
        for creature_type, filename in self.CREATURE_SPRITES.items():
            scale = creature_type not in self.NO_SCALE_CREATURES
            all_assets.append(("creature", creature_type, filename, scale))
        
        for item_type, filename in self.ITEM_SPRITES.items():
            all_assets.append(("item", item_type, filename, True))
        
        for terrain_type, filename in self.TERRAIN_SPRITES.items():
            all_assets.append(("terrain", terrain_type, filename, True))
        
        for deco_type, filename in self.DECORATION_SPRITES.items():
            all_assets.append(("decoration", deco_type, filename, True))
        
        total = len(all_assets)
        
        for i, (category, key, filename, scale) in enumerate(all_assets):
            folder = self._creatures_path if category in ("creature", "terrain", "decoration") else self._items_path
            sprite = self._load_sprite(folder, filename, scale=scale)
            
            if sprite:
                if category == "creature":
                    self._creature_cache[key] = sprite
                elif category == "item":
                    self._item_cache[key] = sprite
                elif category == "decoration":
                    self._decoration_cache[key] = sprite
                else:
                    self._terrain_cache[key] = sprite
            
            yield (i + 1, total, key)
        
        self._loaded = True
        print(f"[SpriteManager] Cargados {len(self._creature_cache)} sprites de criaturas")
        print(f"[SpriteManager] Cargados {len(self._item_cache)} sprites de items")
        print(f"[SpriteManager] Cargados {len(self._terrain_cache)} sprites de terreno")
        print(f"[SpriteManager] Cargados {len(self._decoration_cache)} sprites de decoración")
    
    def _load_sprite(self, folder: str, filename: str, scale: bool = True) -> Optional[pygame.Surface]:
        """
        Carga un sprite desde archivo.
        
        Args:
            folder: Carpeta donde está el sprite
            filename: Nombre del archivo
            scale: Si True, escala al tamaño de tile. Si False, mantiene tamaño original.
            
        Returns:
            Surface de pygame o None si no se pudo cargar
        """
        filepath = os.path.join(folder, filename)
        
        try:
            if os.path.exists(filepath):
                # Cargar con soporte de transparencia
                sprite = pygame.image.load(filepath).convert_alpha()
                
                # Escalar al tamaño de tile si es necesario (y si se permite)
                if scale and (sprite.get_width() != TILE_SIZE or sprite.get_height() != TILE_SIZE):
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
    
    def get_decoration_sprite(self, deco_type: str) -> Optional[pygame.Surface]:
        """
        Obtiene el sprite de una decoración de suelo.
        
        Args:
            deco_type: Tipo de decoración (ej: "blood")
            
        Returns:
            Surface del sprite o None si no existe
        """
        if not self._loaded:
            self.load_sprites()
        return self._decoration_cache.get(deco_type)


# Instancia global del gestor de sprites
sprite_manager = SpriteManager()
