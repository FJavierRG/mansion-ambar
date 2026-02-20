"""
Sistema de tienda del juego.

Gestiona los items en venta, precios, stock y lógica de compra.
La tienda del comerciante es accesible globalmente y modificable
desde cualquier parte del código mediante get_merchant_shop().

Ejemplo de uso externo (usando la factoría de items):
    from roguelike.systems.shop import get_merchant_shop, create_shop_item

    shop = get_merchant_shop()
    shop.add_item(create_shop_item("dagger", stock=1))
    shop.remove_item("Poción de Vida")
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..items.item import Item


@dataclass
class ShopItem:
    """
    Representa un item en venta en una tienda.
    
    Attributes:
        item_id: Identificador de la factoría (clave en POTION_DATA, WEAPON_DATA, etc.)
        name: Nombre del item (para mostrar en la UI)
        description: Descripción corta del item
        price: Precio en monedas de oro
        stock: Cantidad disponible (-1 = ilimitado, >0 = limitado)
    """
    item_id: str
    name: str
    description: str
    price: int
    stock: int = -1  # -1 = ilimitado

    def create_item(self) -> Optional['Item']:
        """
        Crea una nueva instancia del item usando la factoría central.
        
        Returns:
            Instancia del item, o None si el item_id no es válido
        """
        from ..items.item import create_item
        return create_item(self.item_id)


def _auto_description(item_id: str) -> str:
    """
    Genera una descripción corta automática a partir de los datos de config.
    
    Args:
        item_id: Identificador del item en la factoría
        
    Returns:
        Descripción corta del item (ej: "Restaura 20 HP", "+4 ATK")
    """
    from ..config import POTION_DATA, WEAPON_DATA, ARMOR_DATA
    
    if item_id in POTION_DATA:
        data = POTION_DATA[item_id]
        effect = data["effect"]
        value = data["value"]
        if effect == "heal":
            return f"Restaura {value} HP"
        elif effect == "strength":
            duration = data.get("duration", 0)
            return f"+{value} ATK por {duration} turnos"
        elif effect == "poison":
            return "Efecto desconocido"
        return data["name"]
    
    if item_id in WEAPON_DATA:
        data = WEAPON_DATA[item_id]
        return f"+{data['attack_bonus']} ATK, {data['durability']} usos"
    
    if item_id in ARMOR_DATA:
        data = ARMOR_DATA[item_id]
        return f"+{data['defense_bonus']} DEF, {data['durability']} usos"
    
    # Especiales
    if item_id == "gold":
        return "1 moneda de oro"
    if item_id == "amulet":
        return "El legendario amuleto"
    if item_id == "heart_key":
        return "Llave especial"
    
    return item_id


def _auto_name(item_id: str) -> str:
    """
    Obtiene el nombre del item desde los datos de config.
    
    Args:
        item_id: Identificador del item en la factoría
        
    Returns:
        Nombre del item (ej: "Poción de Vida", "Espada Corta")
    """
    from ..config import POTION_DATA, WEAPON_DATA, ARMOR_DATA
    
    if item_id in POTION_DATA:
        return POTION_DATA[item_id]["name"]
    if item_id in WEAPON_DATA:
        return WEAPON_DATA[item_id]["name"]
    if item_id in ARMOR_DATA:
        return ARMOR_DATA[item_id]["name"]
    
    # Especiales
    names = {
        "gold": "Moneda de oro",
        "amulet": "Amuleto de Ámbar",
        "heart_key": "Llave con forma de corazón",
    }
    return names.get(item_id, item_id)


def get_item_price(item_id: str) -> int:
    """
    Obtiene el precio de un item desde sus datos en config.py.
    
    Busca el campo 'price' en POTION_DATA, WEAPON_DATA y ARMOR_DATA.
    
    Args:
        item_id: Identificador del item en la factoría
        
    Returns:
        Precio del item en oro, o 0 si no se encuentra
    """
    from ..config import POTION_DATA, WEAPON_DATA, ARMOR_DATA
    
    for registry in (POTION_DATA, WEAPON_DATA, ARMOR_DATA):
        if item_id in registry:
            return registry[item_id].get("price", 0)
    return 0


def create_shop_item(
    item_id: str,
    price: Optional[int] = None,
    stock: int = -1,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> ShopItem:
    """
    Crea un ShopItem vinculado a la factoría central de items.
    
    El nombre, la descripción y el precio se resuelven automáticamente
    desde config.py a menos que se proporcionen manualmente.
    
    Args:
        item_id: ID del item en la factoría (ej: "health_potion", "dagger")
        price: Precio override (None = automático desde config)
        stock: Cantidad disponible (-1 = ilimitado, >0 = limitado)
        name: Nombre override (None = automático desde config)
        description: Descripción override (None = automática desde config)
        
    Returns:
        ShopItem listo para añadir a una tienda
        
    Ejemplo:
        shop.add_item(create_shop_item("dagger", stock=1))
        shop.add_item(create_shop_item("health_potion"))
    """
    resolved_name = name if name is not None else _auto_name(item_id)
    resolved_desc = description if description is not None else _auto_description(item_id)
    resolved_price = price if price is not None else get_item_price(item_id)
    
    return ShopItem(
        item_id=item_id,
        name=resolved_name,
        description=resolved_desc,
        price=resolved_price,
        stock=stock,
    )


class Shop:
    """
    Tienda que permite al jugador comprar items.
    
    Attributes:
        name: Nombre de la tienda (para el título de la UI)
        items: Lista de items disponibles para comprar
    """
    
    def __init__(self, name: str, items: Optional[List[ShopItem]] = None) -> None:
        """
        Inicializa la tienda.
        
        Args:
            name: Nombre de la tienda
            items: Lista de items en venta (opcional)
        """
        self.name = name
        self.items: List[ShopItem] = list(items) if items else []
        # Guardar los items originales para poder restockear
        self._default_items: List[ShopItem] = []
    
    def buy_item(self, player: 'Player', index: int) -> Tuple[bool, str]:
        """
        Intenta comprar un item de la tienda.
        
        Args:
            player: El jugador que compra
            index: Índice del item en la lista
            
        Returns:
            Tupla (éxito, mensaje)
        """
        if index < 0 or index >= len(self.items):
            return False, "Ítem no válido."
        
        shop_item = self.items[index]
        
        # Verificar stock
        if shop_item.stock == 0:
            return False, f"{shop_item.name} está agotado."
        
        # Verificar oro suficiente
        if player.gold < shop_item.price:
            return False, f"No tienes suficiente oro. Necesitas {shop_item.price} monedas."
        
        # Crear el item usando la factoría
        item = shop_item.create_item()
        
        if item is None:
            return False, f"Error: no se pudo crear {shop_item.name} (item_id={shop_item.item_id!r})."
        
        # Verificar espacio en inventario (grid)
        if not player.add_to_inventory(item):
            return False, "Tu inventario está lleno (no cabe en el grid)."
        
        # Realizar la compra
        player.gold -= shop_item.price
        
        # Gestionar stock
        if shop_item.stock > 0:
            shop_item.stock -= 1
            if shop_item.stock == 0:
                # Eliminar item agotado de la lista
                self.items.pop(index)
        
        return True, f"Has comprado {shop_item.name} por {shop_item.price} monedas de oro."
    
    def get_item_count(self) -> int:
        """Retorna el número de items en la tienda."""
        return len(self.items)
    
    # ── API para modificar items desde código externo ──────────────
    
    def add_item(self, item: ShopItem) -> None:
        """
        Añade un item a la tienda.
        
        Args:
            item: ShopItem a añadir
        """
        self.items.append(item)
    
    def remove_item(self, name: str) -> bool:
        """
        Elimina un item de la tienda por nombre.
        
        Args:
            name: Nombre del item a eliminar
            
        Returns:
            True si se encontró y eliminó, False si no existía
        """
        for i, item in enumerate(self.items):
            if item.name == name:
                self.items.pop(i)
                return True
        return False
    
    def set_items(self, items: List[ShopItem]) -> None:
        """
        Reemplaza todos los items de la tienda.
        
        Args:
            items: Nueva lista de items
        """
        self.items = list(items)
    
    def clear_items(self) -> None:
        """Elimina todos los items de la tienda."""
        self.items.clear()
    
    def restock(self) -> None:
        """
        Restablece el inventario de la tienda a su estado original.
        Útil para resetear entre runs.
        """
        self.items = [
            ShopItem(
                item_id=item.item_id,
                name=item.name,
                description=item.description,
                price=item.price,
                stock=item.stock
            )
            for item in self._default_items
        ]
    
    def get_item_by_name(self, name: str) -> Optional[ShopItem]:
        """
        Busca un item por nombre.
        
        Args:
            name: Nombre del item
            
        Returns:
            ShopItem si se encuentra, None si no
        """
        for item in self.items:
            if item.name == name:
                return item
        return None


# ══════════════════════════════════════════════════════════════════
# TIENDA DEL COMERCIANTE
# ══════════════════════════════════════════════════════════════════
#
# El inventario del comerciante en dungeon es DINÁMICO y se basa en:
#
#   1. DONACIÓN ACUMULADA (persistente): "merchant_donated_total"
#      El jugador dona oro libremente al Comerciante Errante en el lobby.
#      El total donado determina qué items están desbloqueados.
#      Cada tier cuesta exactamente el precio del item que desbloquea.
#      El umbral de desbloqueo del item N es la suma acumulada de los
#      precios de los items 0..N.
#      Si el jugador dona suficiente de golpe, desbloquea varios tiers.
#
#   2. RESTOCK (por run): "merchant_restock_paid"
#      Sin restock pagado la tienda está vacía (0 items).
#      Con restock: todos los items desbloqueados aparecen con stock.
#
# Ambos se gestionan desde el Comerciante Errante (merchant_wanderer.py).
#
# Claves en event_data:
#   "merchant_donated_total" → int, total de oro donado (acumulado)
#   "merchant_restock_paid"  → bool, si el jugador pagó restock esta run
# ══════════════════════════════════════════════════════════════════

# Pool secuencial de items del comerciante.
# Orden = orden de desbloqueo (solo item_ids).
# El coste de cada tier = precio del item (definido en config.py).
# El umbral acumulado para desbloquear el item N es: sum(precio[0..N]).
MERCHANT_ITEM_POOL: list[str] = [
    "health_potion",
    "bronze_dagger",
    "leather_armor",
    "short_sword",
    "chain_mail",
    "greater_health_potion",
    "long_sword",
    "plate_armor",
    "strength_potion",
    "war_axe",
    "commander_sword",
    "dragon_armor",
]


def get_unlock_thresholds() -> list[int]:
    """
    Calcula los umbrales acumulados de desbloqueo para cada item.
    
    Cada tier cuesta el precio del item (leído de config.py).
    El umbral del item N = suma de precios[0..N].
    
    Returns:
        Lista de umbrales acumulados (uno por item en MERCHANT_ITEM_POOL).
        El item i se desbloquea cuando donated_total >= thresholds[i].
    """
    thresholds = []
    cumulative = 0
    for item_id in MERCHANT_ITEM_POOL:
        cumulative += get_item_price(item_id)
        thresholds.append(cumulative)
    return thresholds


def get_unlocked_count(donated_total: int) -> int:
    """
    Calcula cuántos items están desbloqueados dado un total donado.
    
    Cada tier cuesta el precio del item. Si se dona suficiente para
    cubrir varios tiers de golpe, todos se desbloquean.
    
    Args:
        donated_total: Total de oro donado acumulado
        
    Returns:
        Número de items desbloqueados (0 a len(MERCHANT_ITEM_POOL))
    """
    count = 0
    cumulative = 0
    for item_id in MERCHANT_ITEM_POOL:
        cumulative += get_item_price(item_id)
        if donated_total >= cumulative:
            count += 1
        else:
            break
    return count


def _get_unlocked_merchant_items(donated_total: int) -> List[ShopItem]:
    """
    Genera la lista de items desbloqueados según el total donado.
    
    Solo incluye items cuyo umbral acumulado haya sido superado.
    
    Args:
        donated_total: Total de oro donado acumulado
        
    Returns:
        Lista de ShopItems desbloqueados
    """
    items: List[ShopItem] = []
    cumulative = 0
    for item_id in MERCHANT_ITEM_POOL:
        price = get_item_price(item_id)
        cumulative += price
        if donated_total >= cumulative:
            items.append(create_shop_item(item_id, stock=1))
        else:
            break
    return items


def _create_merchant_shop_from_state() -> Shop:
    """
    Crea la tienda del comerciante basándose en el estado actual
    de donaciones y restock (leídos de event_data).
    
    Returns:
        Instancia de Shop con los items correspondientes
    """
    from .events import event_manager
    
    donated_total = event_manager.get_data("merchant_donated_total", 0)
    restock_paid = event_manager.get_data("merchant_restock_paid", False)
    
    if restock_paid:
        items = _get_unlocked_merchant_items(donated_total)
    else:
        items = []
    
    shop = Shop("Comerciante", items)
    shop._default_items = list(items)
    return shop


# Instancia global de la tienda del comerciante (lazy init)
_merchant_shop: Optional[Shop] = None


def get_merchant_shop() -> Shop:
    """
    Obtiene la instancia global de la tienda del comerciante.
    
    La tienda se crea bajo demanda basándose en el estado actual
    de tiers y restock (event_data). Se puede forzar recreación
    con refresh_merchant_shop().
    
    Returns:
        Instancia de Shop del comerciante
    """
    global _merchant_shop
    if _merchant_shop is None:
        _merchant_shop = _create_merchant_shop_from_state()
    return _merchant_shop


def reset_merchant_shop() -> None:
    """
    Resetea la tienda del comerciante para una nueva run.
    
    Marca el restock como NO pagado y fuerza recreación de la tienda.
    Llamar al inicio de cada nueva run (muerte / respawn).
    """
    global _merchant_shop
    from .events import event_manager
    event_manager.set_data("merchant_restock_paid", False)
    _merchant_shop = None  # Se recreará en el próximo get_merchant_shop()


def refresh_merchant_shop() -> None:
    """
    Fuerza la recreación de la tienda del comerciante.
    
    Útil después de que el jugador pague restock o mejore el tier
    en el lobby (vía Comerciante Errante). La próxima llamada a
    get_merchant_shop() creará la tienda con el estado actualizado.
    """
    global _merchant_shop
    _merchant_shop = None
