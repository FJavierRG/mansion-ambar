"""
Configuración global del juego roguelike.
Contiene todas las constantes y parámetros configurables.
"""
from typing import Dict, Tuple

# ============================================================================
# CONFIGURACIÓN DE VENTANA
# ============================================================================
WINDOW_WIDTH: int = 1280
WINDOW_HEIGHT: int = 800
GAME_TITLE: str = "Roguelike - En Busca del Amuleto de Yendor"
FPS: int = 60

# ============================================================================
# CONFIGURACIÓN DE TILES ASCII
# ============================================================================
TILE_SIZE: int = 16  # Píxeles por caracter
FONT_NAME: str = "Courier New"
FONT_SIZE: int = 16

# ============================================================================
# DIMENSIONES DEL MAPA
# ============================================================================
MAP_WIDTH: int = 80   # Caracteres
MAP_HEIGHT: int = 38  # Caracteres (reducido para dar espacio al HUD y log)
VIEWPORT_WIDTH: int = 60
VIEWPORT_HEIGHT: int = 35

# ============================================================================
# DIMENSIONES DEL HUD
# ============================================================================
HUD_HEIGHT: int = 3
MESSAGE_LOG_HEIGHT: int = 5
MESSAGE_LOG_MAX_MESSAGES: int = 100

# ============================================================================
# GENERACIÓN DE MAZMORRAS
# ============================================================================
ROOM_MIN_SIZE: int = 6
ROOM_MAX_SIZE: int = 12
MAX_ROOMS: int = 15
MAX_ROOM_MONSTERS: int = 4
MAX_ROOM_ITEMS: int = 1  # Máximo 1 item por habitación para menor abundancia
MAX_DUNGEON_LEVEL: int = 10

# ============================================================================
# FIELD OF VIEW
# ============================================================================
FOV_RADIUS: int = 10
FOV_LIGHT_WALLS: bool = True

# ============================================================================
# STATS DEL JUGADOR
# ============================================================================
PLAYER_BASE_HP: int = 37
PLAYER_BASE_ATTACK: int = 5
PLAYER_BASE_DEFENSE: int = 2
PLAYER_HP_PER_LEVEL: int = 5
PLAYER_ATTACK_PER_LEVEL: int = 2
PLAYER_DEFENSE_PER_LEVEL: int = 1

# ============================================================================
# EXPERIENCIA Y NIVELES
# ============================================================================
XP_BASE: int = 20
XP_FACTOR: float = 1.5

# ============================================================================
# INVENTARIO
# ============================================================================
INVENTORY_CAPACITY: int = 26  # a-z

# ============================================================================
# SÍMBOLOS ASCII
# ============================================================================
SYMBOLS: Dict[str, str] = {
    "player": "@",
    "wall": "#",
    "floor": ".",
    "door": "+",
    "stairs_down": ">",
    "stairs_up": "<",
    "potion": "!",
    "scroll": "?",
    "weapon": "/",
    "armor": "[",
    "gold": "$",
    "amulet": '"',
    "ring": "=",
}

# ============================================================================
# SÍMBOLOS DE MONSTRUOS
# ============================================================================
MONSTER_SYMBOLS: Dict[str, str] = {
    "goblin": "g",
    "orc": "o",
    "troll": "T",
    "dragon": "D",
    "snake": "S",
    "zombie": "Z",
    "rat": "r",
    "bat": "B",
    "skeleton": "s",
    "wraith": "W",
    "ancient_dragon": "D",
}

# ============================================================================
# COLORES (RGB)
# ============================================================================
COLORS: Dict[str, Tuple[int, int, int]] = {
    # UI
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "dark_gray": (64, 64, 64),
    "darker_gray": (32, 32, 32),
    
    # Jugador
    "player": (255, 255, 255),
    
    # Terreno
    "wall": (130, 110, 90),
    "wall_dark": (50, 50, 60),
    "floor": (50, 50, 50),
    "floor_dark": (25, 25, 30),
    "door": (139, 69, 19),
    "stairs": (255, 215, 0),
    
    # Monstruos
    "goblin": (0, 200, 0),
    "orc": (0, 128, 0),
    "troll": (0, 100, 0),
    "dragon": (255, 0, 0),
    "snake": (0, 255, 0),
    "zombie": (100, 150, 100),
    "rat": (139, 90, 43),
    "bat": (100, 100, 100),
    "skeleton": (200, 200, 200),
    "wraith": (150, 0, 200),
    "ancient_dragon": (255, 50, 50),
    
    # Items
    "potion": (0, 255, 255),
    "scroll": (255, 255, 0),
    "weapon": (192, 192, 192),
    "armor": (139, 69, 19),
    "gold": (255, 215, 0),
    "amulet": (255, 0, 255),
    "ring": (255, 165, 0),
    
    # UI
    "hp_bar": (200, 0, 0),
    "hp_bar_bg": (50, 0, 0),
    "xp_bar": (0, 200, 0),
    "xp_bar_bg": (0, 50, 0),
    "message": (200, 200, 200),
    "message_important": (255, 255, 0),
    "message_damage": (255, 100, 100),
    "message_heal": (100, 255, 100),
    "message_death": (255, 0, 0),
}

# ============================================================================
# DATOS DE MONSTRUOS
# ============================================================================
# Progresión de enemigos por piso:
# Piso 1: Solo Ratas (introducción suave)
# Piso 2: Ratas + Murciélagos
# Piso 3: Ratas + Murciélagos + Goblins
# Piso 4: Murciélagos + Goblins + Serpientes
# Piso 5: Goblins + Serpientes + Esqueletos
# Piso 6: Serpientes + Esqueletos + Orcos + Zombies
# Piso 7: Esqueletos + Orcos + Zombies + Espectros
# Piso 8: Orcos + Zombies + Espectros + Trolls
# Piso 9: Espectros + Trolls + Dragones
# Piso 10: Trolls + Dragones + Dragón Anciano (BOSS)

MONSTER_DATA: Dict[str, Dict] = {
    "rat": {
        "name": "Rata",
        "symbol": "r",
        "color": "rat",
        "hp": 7,
        "attack": 2,
        "defense": 0,
        "xp": 5,
        "min_level": 1,  # Piso 1-3: enemigo inicial
        "max_level": 3,
    },
    "bat": {
        "name": "Murciélago",
        "symbol": "B",
        "color": "bat",
        "hp": 10,
        "attack": 5,
        "defense": 0,
        "xp": 8,
        "min_level": 2,  # Aparece desde piso 2
        "max_level": 4,
    },
    "goblin": {
        "name": "Goblin",
        "symbol": "g",
        "color": "goblin",
        "hp": 17,
        "attack": 8,
        "defense": 1,
        "xp": 15,
        "min_level": 3,  # Aparece desde piso 3
        "max_level": 5,
    },
    "snake": {
        "name": "Serpiente",
        "symbol": "S",
        "color": "snake",
        "hp": 15,
        "attack": 10,
        "defense": 0,
        "xp": 12,
        "min_level": 4,  # Aparece desde piso 4
        "max_level": 6,
    },
    "skeleton": {
        "name": "Esqueleto",
        "symbol": "s",
        "color": "skeleton",
        "hp": 20,
        "attack": 13,
        "defense": 2,
        "xp": 20,
        "min_level": 5,  # Aparece desde piso 5
        "max_level": 7,
    },
    "orc": {
        "name": "Orco",
        "symbol": "o",
        "color": "orc",
        "hp": 25,
        "attack": 17,
        "defense": 3,
        "xp": 30,
        "min_level": 6,  # Aparece desde piso 6
        "max_level": 8,
    },
    "zombie": {
        "name": "Zombie",
        "symbol": "Z",
        "color": "zombie",
        "hp": 30,
        "attack": 13,
        "defense": 4,
        "xp": 35,
        "min_level": 6,  # Aparece desde piso 6
        "max_level": 9,
    },
    "wraith": {
        "name": "Espectro",
        "symbol": "W",
        "color": "wraith",
        "hp": 25,
        "attack": 18,
        "defense": 3,
        "xp": 50,
        "min_level": 7,  # Aparece desde piso 7
        "max_level": 10,
    },
    "troll": {
        "name": "Troll",
        "symbol": "T",
        "color": "troll",
        "hp": 45,
        "attack": 20,
        "defense": 5,
        "xp": 60,
        "min_level": 8,  # Aparece desde piso 8
        "max_level": 10,
    },
    "dragon": {
        "name": "Dragón",
        "symbol": "D",
        "color": "dragon",
        "hp": 75,
        "attack": 20,
        "defense": 8,
        "xp": 100,
        "min_level": 9,  # Aparece desde piso 9
        "max_level": 10,
    },
    "ancient_dragon": {
        "name": "Dragón Anciano",
        "symbol": "D",
        "color": "ancient_dragon",
        "hp": 160,
        "attack": 20,
        "defense": 15,
        "xp": 500,
        "min_level": 10,  # Solo en piso 10
        "max_level": 10,
        "is_boss": True,
    },
}

# ============================================================================
# DATOS DE ITEMS
# ============================================================================
POTION_DATA: Dict[str, Dict] = {
    "health_potion": {
        "name": "Poción de Vida",
        "effect": "heal",
        "value": 20,
        "color": "potion",
        "rarity": 1.0,
    },
    "greater_health_potion": {
        "name": "Poción de Vida Mayor",
        "effect": "heal",
        "value": 50,
        "color": "potion",
        "rarity": 0.5,
    },
    "strength_potion": {
        "name": "Poción de Fuerza",
        "effect": "strength",
        "value": 3,
        "duration": 20,
        "color": "potion",
        "rarity": 0.4,
    },
    "poison_potion": {
        "name": "Poción de Veneno",
        "effect": "poison",
        "value": -15,
        "color": "potion",
        "rarity": 0.3,
    },
}

WEAPON_DATA: Dict[str, Dict] = {
    "dagger": {
        "name": "Daga",
        "attack_bonus": 2,
        "color": "weapon",
        "rarity": 1.0,
        "min_level": 1,
    },
    "short_sword": {
        "name": "Espada Corta",
        "attack_bonus": 4,
        "color": "weapon",
        "rarity": 0.8,
        "min_level": 2,
    },
    "long_sword": {
        "name": "Espada Larga",
        "attack_bonus": 6,
        "color": "weapon",
        "rarity": 0.6,
        "min_level": 4,
    },
    "axe": {
        "name": "Hacha de Guerra",
        "attack_bonus": 8,
        "color": "weapon",
        "rarity": 0.4,
        "min_level": 6,
    },
    "great_sword": {
        "name": "Espadón",
        "attack_bonus": 12,
        "color": "weapon",
        "rarity": 0.2,
        "min_level": 8,
    },
}

ARMOR_DATA: Dict[str, Dict] = {
    "leather_armor": {
        "name": "Armadura de Cuero",
        "defense_bonus": 2,
        "color": "armor",
        "rarity": 1.0,
        "min_level": 1,
    },
    "chain_mail": {
        "name": "Cota de Mallas",
        "defense_bonus": 4,
        "color": "armor",
        "rarity": 0.6,
        "min_level": 3,
    },
    "plate_armor": {
        "name": "Armadura de Placas",
        "defense_bonus": 7,
        "color": "armor",
        "rarity": 0.3,
        "min_level": 6,
    },
    "dragon_armor": {
        "name": "Armadura de Dragón",
        "defense_bonus": 12,
        "color": "armor",
        "rarity": 0.1,
        "min_level": 9,
    },
}

# ============================================================================
# CONTROLES
# ============================================================================
MOVEMENT_KEYS: Dict[int, Tuple[int, int]] = {}  # Se llena en runtime con pygame

# Direcciones: (dx, dy)
DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
    "up_left": (-1, -1),
    "up_right": (1, -1),
    "down_left": (-1, 1),
    "down_right": (1, 1),
}

# ============================================================================
# MENSAJES Y DIÁLOGOS
# ============================================================================
# Los diálogos y mensajes narrativos se han movido a roguelike/content/
# - NPCs: roguelike/content/npcs/
# - Textos ambientales: roguelike/content/ambient/

# ============================================================================
# ESTADOS DEL JUEGO
# ============================================================================
class GameState:
    """Enumeración de estados del juego."""
    MAIN_MENU = "main_menu"
    PLAYING = "playing"
    INVENTORY = "inventory"
    DEAD = "dead"
    VICTORY = "victory"
    PAUSED = "paused"
    TARGETING = "targeting"
    DIALOG = "dialog"  # Estado de diálogo/texto interactivo
    CONSOLE = "console"  # Consola de comandos de desarrollo
    SAVE_MENU = "save_menu"  # Menú de selección de guardados
