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
GAME_TITLE: str = "La Mansión de Ámbar"
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
MAX_ROOMS: int = 15  # Tope absoluto (fallback de seguridad)
MAX_ROOM_MONSTERS: int = 4
MAX_DUNGEON_LEVEL: int = 10

# --- Progresión del número de salas por planta (min, max) ---
# Controla cuántas salas genera cada piso para una dificultad progresiva.
# Las plantas no listadas usan FLOOR_ROOM_COUNT_DEFAULT.
# Fácilmente editable para testeo y balance.
FLOOR_ROOM_COUNT: Dict[int, Tuple[int, int]] = {
    1: (4, 5),   # Introducción suave: pocas salas
    2: (5, 6),   # Ligera expansión
    3: (6, 7),   # El jugador ya conoce las mecánicas
    4: (7, 8),   # Dificultad media
    5: (7, 8),
    6: (7, 8),
}
FLOOR_ROOM_COUNT_DEFAULT: Tuple[int, int] = (8, 9)  # Planta 7 en adelante

# --- Margen de colocación de salas por planta (margin_x, margin_y) ---
# Reduce el área efectiva del mapa para concentrar salas en pisos con pocas.
# Área útil real = (MAP_WIDTH - 2*mx) × (MAP_HEIGHT - 2*my).
# Pisos no listados usan FLOOR_MAP_MARGIN_DEFAULT (sin margen extra).
FLOOR_MAP_MARGIN: Dict[int, Tuple[int, int]] = {
    1: (12, 4),  # Área efectiva ~56×30 — salas muy concentradas
    2: (8, 3),   # Área efectiva ~64×32
    3: (4, 2),   # Área efectiva ~72×34
}
FLOOR_MAP_MARGIN_DEFAULT: Tuple[int, int] = (0, 0)  # Sin margen extra

# --- Probabilidad base de spawn por pool ---
# Primer filtro: ¿aparece esta pool en esta planta?
# Valor fijo por ahora. Preparado para extender a per-piso/eventos.
POOL_SPAWN_CHANCE: Dict[str, float] = {
    "equipment": 0.70,  # Armas y armaduras
    "potion":    0.30,  # Pociones
    "gold":      0.80,  # Monedas
}

# --- Rangos de cantidad por pool (si la pool aparece) ---
# min ≥ 1 siempre: el caso "0 items" lo decide POOL_SPAWN_CHANCE.
# Filosofía roguelike: pocos ítems, cada uno es una decisión importante.

# Pool de equipo: armas y armaduras.  Techo: 3.
FLOOR_EQUIPMENT_RANGE: Dict[int, Tuple[int, int]] = {
    1:  (1, 1),   # Un solo hallazgo — cada pieza cuenta
    2:  (1, 1),
    3:  (1, 2),
    4:  (1, 2),
    5:  (1, 2),
    6:  (1, 3),
    7:  (1, 3),
    8:  (2, 3),   # Plantas altas: equipo más generoso
    9:  (2, 3),
    10: (1, 2),   # Planta del boss: reto de recursos
}
FLOOR_EQUIPMENT_RANGE_DEFAULT: Tuple[int, int] = (1, 3)

# Pool de pociones: consumibles curativos/buff.  Techo: 3.
FLOOR_POTION_RANGE: Dict[int, Tuple[int, int]] = {
    1:  (1, 1),
    2:  (1, 1),
    3:  (1, 1),
    4:  (1, 2),
    5:  (1, 2),
    6:  (1, 2),
    7:  (1, 2),
    8:  (1, 3),
    9:  (1, 3),
    10: (1, 1),   # Boss: recursos justos
}
FLOOR_POTION_RANGE_DEFAULT: Tuple[int, int] = (1, 2)

# Pool de oro: monedas (recurso meta-progresión).  Techo: 5.
FLOOR_GOLD_RANGE: Dict[int, Tuple[int, int]] = {
    1:  (1, 2),
    2:  (1, 2),
    3:  (1, 3),
    4:  (1, 3),
    5:  (2, 3),
    6:  (2, 4),
    7:  (2, 4),
    8:  (2, 5),
    9:  (2, 5),
    10: (2, 3),
}
FLOOR_GOLD_RANGE_DEFAULT: Tuple[int, int] = (2, 4)

# Probabilidad de que una habitación tenga puertas en todas sus entradas
DOOR_CHANCE: float = 0.3

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
# INVENTARIO (Grid estilo RE4 / Tarkov)
# ============================================================================
INVENTORY_CAPACITY: int = 26  # Legacy (fallback)
GRID_INVENTORY_WIDTH: int = 4    # Columnas del grid (ancho)
GRID_INVENTORY_HEIGHT: int = 3   # Filas del grid (alto)
GRID_CELL_SIZE: int = 48          # Píxeles por celda en la UI

# ============================================================================
# SÍMBOLOS ASCII
# ============================================================================
SYMBOLS: Dict[str, str] = {
    "player": "@",
    "wall": "#",
    "floor": ".",
    "door": "+",
    "door_closed": "=",     # Puerta cerrada (barrera)
    "door_open": "\u2016",      # Puerta abierta (rotada 90°)
    "stairs_down": ">",
    "stairs_up": "<",
    "potion": "!",
    "scroll": "?",
    "weapon": "/",
    "armor": "[",
    "gold": "$",
    "amulet": '"',
    "ring": "=",
    "key": "♥",
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
    "door_open": (101, 67, 33),
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
        "price": 5,
        "color": "potion",
        "rarity": 0.5,
        "grid_size": (1, 1),
        "description": "Un líquido rojizo con propiedades curativas.",
    },
    "greater_health_potion": {
        "name": "Poción de Vida Mayor",
        "effect": "heal",
        "value": 50,
        "price": 15,
        "color": "potion",
        "rarity": 0.05,
        "grid_size": (1, 1),
        "description": "Una poción potente que restaura gran cantidad de vida.",
    },
    "strength_potion": {
        "name": "Poción de Fuerza",
        "effect": "strength",
        "value": 3,
        "duration": 20,
        "price": 15,
        "color": "potion",
        "rarity": 0.1,
        "grid_size": (1, 1),
        "description": "Un brebaje que otorga fuerza temporal.",
    },
    "poison_potion": {
        "name": "Poción de Veneno",
        "effect": "poison",
        "value": -25,
        "price": 0,
        "color": "potion",
        "rarity": 0.25,
        "grid_size": (1, 1),
        "description": "Un líquido de color sospechoso...",
    },
}

WEAPON_DATA: Dict[str, Dict] = {
    "bronze_dagger": {
        "name": "Daga de bronce",
        "attack_bonus": 1,
        "durability": 5,
        "price": 3,
        "sprite": "dagger",
        "color": "weapon",
        "rarity": 1.0,
        "min_level": 2,
        "grid_size": (1, 2),
        "description": "Una pequeña daga de bronce, modesta pero funcional.",
    },
    "dagger": {
        "name": "Daga",
        "attack_bonus": 2,
        "durability": 5,
        "price": 5,
        "sprite": "dagger",
        "color": "weapon",
        "rarity": 1.0,
        "min_level": 2,
        "grid_size": (1, 2),
        "description": "Una daga afilada, perfecta para ataques rápidos.",
    },
    "holy_dagger": {
        "name": "Daga Sagrada",
        "attack_bonus": 12,
        "durability": 10,
        "price": 25,
        "sprite": "dagger",
        "color": "weapon",
        "rarity": 0.2,
        "min_level": 2,
        "grid_size": (1, 2),
        "description": "Una daga bendecida que emana una tenue luz dorada.",
    },
    "short_sword": {
        "name": "Espada corta",
        "attack_bonus": 3,
        "durability": 8,
        "price": 6,
        "sprite": "sword",
        "color": "weapon",
        "rarity": 0.8,
        "min_level": 3,
        "grid_size": (1, 2),
        "description": "Una espada ligera y versátil.",
    },
    "bronze_hammer": {
        "name": "Martillo de bronce",
        "attack_bonus": 4,
        "durability": 6,
        "price": 6,
        "sprite": "axe",
        "color": "weapon",
        "rarity": 0.8,
        "min_level": 3,
        "grid_size": (1, 2),
        "description": "Un martillo pesado forjado en bronce.",
    },
    "hammer": {
        "name": "Martillo",
        "attack_bonus": 4,
        "durability": 8,
        "price": 8,
        "sprite": "axe",
        "color": "weapon",
        "rarity": 0.8,
        "min_level": 3,
        "grid_size": (1, 2),
        "description": "Un martillo de acero bien equilibrado.",
    },
    "long_sword": {
        "name": "Espada larga",
        "attack_bonus": 5,
        "durability": 10,
        "price": 10,
        "sprite": "sword",
        "color": "weapon",
        "rarity": 0.5,
        "min_level": 4,
        "grid_size": (1, 3),
        "description": "Una espada larga con hoja de acero templado.",
    },
    "war_axe": {
        "name": "Hacha de guerra",
        "attack_bonus": 10,
        "durability": 8,
        "price": 15,
        "sprite": "axe",
        "color": "weapon",
        "rarity": 0.5,
        "min_level": 4,
        "grid_size": (2, 2),
        "description": "Un hacha de guerra devastadora.",
    },
    "lance": {
        "name": "Lanza",
        "attack_bonus": 15,
        "durability": 4,
        "price": 12,
        "sprite": "spear",
        "color": "weapon",
        "rarity": 0.3,
        "min_level": 4,
        "grid_size": (1, 4),
        "description": "Una lanza larga con punta de acero. Frágil pero letal.",
    },
    "dragon_lance": {
        "name": "Lanza Dragontina",
        "attack_bonus": 20,
        "durability": 4,
        "price": 25,
        "sprite": "spear",
        "color": "weapon",
        "rarity": 0.2,
        "min_level": 4,
        "grid_size": (1, 4),
        "description": "Forjada con escamas de dragón. Poderosa pero frágil.",
    },
    "commander_sword": {
        "name": "Espada de comandante",
        "attack_bonus": 10,
        "durability": 10,
        "price": 20,
        "sprite": "sword",
        "color": "weapon",
        "rarity": 0.5,
        "min_level": 4,
        "grid_size": (1, 3),
        "description": "La espada de un comandante caído. Resistente y poderosa.",
    },
}

ARMOR_DATA: Dict[str, Dict] = {
    "leather_armor": {
        "name": "Armadura de Cuero",
        "defense_bonus": 2,
        "durability": 6,
        "price": 3,
        "color": "armor",
        "rarity": 1.0,
        "min_level": 1,
        "grid_size": (2, 2),
        "description": "Armadura ligera de cuero curtido.",
    },
    "chain_mail": {
        "name": "Cota de Mallas",
        "defense_bonus": 4,
        "durability": 10,
        "price": 6,
        "color": "armor",
        "rarity": 0.6,
        "min_level": 3,
        "grid_size": (2, 3),
        "description": "Una cota de mallas que ofrece buena protección.",
    },
    "plate_armor": {
        "name": "Armadura de Placas",
        "defense_bonus": 7,
        "durability": 14,
        "price": 10,
        "color": "armor",
        "rarity": 0.3,
        "min_level": 6,
        "grid_size": (2, 3),
        "description": "Armadura pesada de placas de acero. Gran protección.",
    },
    "dragon_armor": {
        "name": "Armadura de Dragón",
        "defense_bonus": 12,
        "durability": 17,
        "price": 20,
        "color": "armor",
        "rarity": 0.1,
        "min_level": 9,
        "grid_size": (3, 3),
        "description": "Forjada con escamas de dragón. La mejor protección posible.",
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
    SHOP = "shop"  # Tienda del comerciante
    DONATION = "donation"  # Selector de donación de oro
    OPTIONS = "options"  # Menú de opciones (centralizado)