"""
Sistema de tienda del juego.

Gestiona los items en venta, precios, stock y lógica de compra.
La tienda del comerciante es accesible globalmente y modificable
desde cualquier parte del código mediante get_merchant_shop().

Ejemplo de uso externo:
    from roguelike.systems.shop import get_merchant_shop, ShopItem

    shop = get_merchant_shop()
    shop.add_item(ShopItem(
        name="Espada Corta",
        description="+4 ATK",
        price=50,
        create_item=lambda: Weapon(weapon_type="short_sword", name="Espada Corta", attack_bonus=4),
        stock=1
    ))
    shop.remove_item("Poción de Vida")
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..items.item import Item


@dataclass
class ShopItem:
    """
    Representa un item en venta en una tienda.
    
    Attributes:
        name: Nombre del item (para mostrar en la UI)
        description: Descripción corta del item
        price: Precio en monedas de oro
        create_item: Función que crea una nueva instancia del item
        stock: Cantidad disponible (-1 = ilimitado, >0 = limitado)
    """
    name: str
    description: str
    price: int
    create_item: Callable[[], 'Item']
    stock: int = -1  # -1 = ilimitado


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
        
        # Verificar espacio en inventario
        if len(player.inventory) >= 26:
            return False, "Tu inventario está lleno."
        
        # Realizar la compra
        player.gold -= shop_item.price
        item = shop_item.create_item()
        player.inventory.append(item)
        
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
                name=item.name,
                description=item.description,
                price=item.price,
                create_item=item.create_item,
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

def _create_health_potion() -> 'Item':
    """Crea una instancia de Poción de Vida."""
    from ..items.potion import Potion
    return Potion(
        potion_type="health_potion",
        name="Poción de Vida",
        effect="heal",
        value=20
    )


def _get_default_merchant_items() -> List[ShopItem]:
    """
    Retorna la lista por defecto de items del comerciante.
    Modificar esta función para cambiar el inventario base.
    """
    return [
        ShopItem(
            name="Poción de Vida",
            description="Restaura 20 HP",
            price=10,
            create_item=_create_health_potion,
            stock=1
        ),
    ]


def create_merchant_shop() -> Shop:
    """
    Crea una nueva tienda del comerciante con el inventario por defecto.
    
    Returns:
        Instancia de Shop con los items del comerciante
    """
    default_items = _get_default_merchant_items()
    shop = Shop("Comerciante", default_items)
    # Guardar items por defecto para restock
    shop._default_items = _get_default_merchant_items()
    return shop


# Instancia global de la tienda del comerciante (lazy init)
_merchant_shop: Optional[Shop] = None


def get_merchant_shop() -> Shop:
    """
    Obtiene la instancia global de la tienda del comerciante.
    
    Desde código externo se puede modificar el inventario:
        shop = get_merchant_shop()
        shop.add_item(ShopItem(...))
        shop.remove_item("nombre")
    
    Returns:
        Instancia de Shop del comerciante
    """
    global _merchant_shop
    if _merchant_shop is None:
        _merchant_shop = create_merchant_shop()
    return _merchant_shop


def reset_merchant_shop() -> None:
    """
    Resetea la tienda del comerciante a su estado original.
    Llamar al inicio de cada nueva run para restockear items.
    """
    global _merchant_shop
    if _merchant_shop is not None:
        _merchant_shop.restock()
    else:
        _merchant_shop = create_merchant_shop()
