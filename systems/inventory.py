"""
Sistema de inventario del juego.

Incluye:
- GridInventory: inventario tipo grid (RE4 / Tarkov)
- Inventory: operaciones de alto nivel (recoger, soltar, usar, equipar)
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Tuple, Dict, Any

from ..config import GRID_INVENTORY_WIDTH, GRID_INVENTORY_HEIGHT

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..items.item import Item
    from ..world.dungeon import Dungeon


class GridInventory:
    """
    Inventario basado en grid 2D estilo RE4 / Escape from Tarkov.

    Cada item ocupa un rectángulo de grid_width × grid_height celdas.
    Los items se almacenan por su posición superior-izquierda en el grid.

    Attributes:
        width: Número de columnas del grid
        height: Número de filas del grid
        grid: Matriz 2D (col × row) — cada celda apunta al item que la ocupa o None
    """

    def __init__(self, width: int = GRID_INVENTORY_WIDTH, height: int = GRID_INVENTORY_HEIGHT) -> None:
        self.width = width
        self.height = height
        # grid[col][row] → Item | None
        self.grid: List[List[Optional[Item]]] = [
            [None for _ in range(height)] for _ in range(width)
        ]
        # Mapeo rápido: id(item) → (gx, gy, item)
        self._items: Dict[int, Tuple[int, int, Item]] = {}

    # ── Consultas ──────────────────────────────────────────────────

    def __len__(self) -> int:
        """Número de items en el grid."""
        return len(self._items)

    def __iter__(self):
        """Itera sobre los items ordenados por posición (fila, columna)."""
        return iter(self.get_all_items())

    def __contains__(self, item: Item) -> bool:
        return id(item) in self._items

    def get_all_items(self) -> List[Item]:
        """Retorna todos los items como lista, ordenados por posición (y, x)."""
        sorted_entries = sorted(self._items.values(), key=lambda e: (e[1], e[0]))
        return [item for _, _, item in sorted_entries]

    def get_item_at(self, gx: int, gy: int) -> Optional[Item]:
        """Retorna el item que ocupa la celda (gx, gy), o None."""
        if 0 <= gx < self.width and 0 <= gy < self.height:
            return self.grid[gx][gy]
        return None

    def get_item_position(self, item: Item) -> Optional[Tuple[int, int]]:
        """Retorna la posición (gx, gy) del item, o None si no está."""
        entry = self._items.get(id(item))
        if entry:
            return (entry[0], entry[1])
        return None

    def get_item_by_index(self, index: int) -> Optional[Item]:
        """Obtiene un item por índice (compatible con sistema legacy)."""
        items = self.get_all_items()
        if 0 <= index < len(items):
            return items[index]
        return None

    def is_full(self) -> bool:
        """Verifica si no hay espacio ni siquiera para un item 1×1."""
        for gx in range(self.width):
            for gy in range(self.height):
                if self.grid[gx][gy] is None:
                    return False
        return True

    # ── Colocación ─────────────────────────────────────────────────

    def can_place(self, item: Item, gx: int, gy: int) -> bool:
        """
        Verifica si el item puede colocarse en la posición (gx, gy).

        Args:
            item: El item a colocar
            gx: Columna del grid (esquina superior-izquierda)
            gy: Fila del grid (esquina superior-izquierda)
        """
        w = getattr(item, 'grid_width', 1)
        h = getattr(item, 'grid_height', 1)

        if gx < 0 or gy < 0 or gx + w > self.width or gy + h > self.height:
            return False

        for dx in range(w):
            for dy in range(h):
                cell = self.grid[gx + dx][gy + dy]
                if cell is not None:
                    return False
        return True

    def place(self, item: Item, gx: int, gy: int) -> bool:
        """
        Coloca el item en la posición (gx, gy). Retorna True si tuvo éxito.
        """
        if not self.can_place(item, gx, gy):
            return False

        w = getattr(item, 'grid_width', 1)
        h = getattr(item, 'grid_height', 1)

        for dx in range(w):
            for dy in range(h):
                self.grid[gx + dx][gy + dy] = item

        self._items[id(item)] = (gx, gy, item)
        return True

    def auto_place(self, item: Item) -> bool:
        """
        Busca la primera posición disponible y coloca el item.
        Escanea fila por fila (de arriba a abajo, de izquierda a derecha).

        Returns:
            True si se colocó, False si no cabe
        """
        w = getattr(item, 'grid_width', 1)
        h = getattr(item, 'grid_height', 1)

        for gy in range(self.height):
            for gx in range(self.width):
                if self.can_place(item, gx, gy):
                    self.place(item, gx, gy)
                    return True
        return False

    def remove(self, item: Item) -> bool:
        """
        Elimina un item del grid.

        Returns:
            True si se eliminó, False si no estaba
        """
        entry = self._items.get(id(item))
        if entry is None:
            return False

        gx, gy, _ = entry
        w = getattr(item, 'grid_width', 1)
        h = getattr(item, 'grid_height', 1)

        for dx in range(w):
            for dy in range(h):
                if (gx + dx < self.width and gy + dy < self.height and
                        self.grid[gx + dx][gy + dy] is item):
                    self.grid[gx + dx][gy + dy] = None

        del self._items[id(item)]
        return True

    def clear(self) -> None:
        """Vacía el grid completamente."""
        for gx in range(self.width):
            for gy in range(self.height):
                self.grid[gx][gy] = None
        self._items.clear()

    # ── Serialización ──────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el grid a diccionario."""
        items_data = []
        for item_id, (gx, gy, item) in self._items.items():
            items_data.append({
                "item": item.to_dict(),
                "gx": gx,
                "gy": gy,
            })
        return {
            "width": self.width,
            "height": self.height,
            "items": items_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GridInventory:
        """Crea un grid desde un diccionario."""
        from ..items.item import Item

        width = data.get("width", GRID_INVENTORY_WIDTH)
        height = data.get("height", GRID_INVENTORY_HEIGHT)
        grid_inv = cls(width=width, height=height)

        for entry in data.get("items", []):
            item = Item.from_dict(entry["item"])
            gx = entry["gx"]
            gy = entry["gy"]
            if not grid_inv.place(item, gx, gy):
                # Si no cabe en la posición guardada, intentar auto-place
                grid_inv.auto_place(item)

        return grid_inv

    @classmethod
    def from_item_list(cls, items: List[Item],
                       width: int = GRID_INVENTORY_WIDTH,
                       height: int = GRID_INVENTORY_HEIGHT) -> GridInventory:
        """
        Crea un grid desde una lista de items (backward compat con saves viejos).
        Auto-coloca cada item en la primera posición disponible.
        """
        grid_inv = cls(width=width, height=height)
        for item in items:
            grid_inv.auto_place(item)
        return grid_inv


class Inventory:
    """
    Sistema de gestión de inventario.

    Maneja las operaciones de recoger, soltar, usar y equipar items.
    """

    @staticmethod
    def pickup_item(player: Player, dungeon: Dungeon) -> List[str]:
        """
        Intenta recoger un item del suelo.

        Args:
            player: El jugador
            dungeon: La mazmorra actual

        Returns:
            Lista de mensajes
        """
        messages = []

        items = dungeon.get_items_at(player.x, player.y)

        if not items:
            messages.append("No hay nada aquí para recoger.")
            return messages

        # Recoger el primer item
        item = items[0]

        # Verificar si es oro
        if item.item_type == "gold":
            player.gold += item.value
            dungeon.remove_item(item)
            messages.append("Recoges una moneda de oro.")

            # Disparar evento de primera moneda recogida (desbloquea NPCs)
            from ..systems.events import event_manager
            if not event_manager.is_event_triggered("first_gold_pickup"):
                event_manager.trigger_event(
                    "first_gold_pickup", player, dungeon, skip_conditions=True
                )

            return messages

        # Verificar si es el amuleto
        if item.item_type == "amulet":
            player.has_amulet = True
            dungeon.remove_item(item)
            messages.append("¡Has encontrado el Amuleto de Ámbar!")
            messages.append("¡Ahora debes escapar ascendiendo a la superficie!")
            return messages

        # Intentar añadir al inventario
        if player.add_to_inventory(item):
            dungeon.remove_item(item)
            messages.append(f"Recoges {item.name}.")
        else:
            messages.append("Tu inventario está lleno (no cabe en el grid).")

        return messages

    @staticmethod
    def drop_item(player: Player, dungeon: Dungeon, index: int) -> List[str]:
        """
        Suelta un item del inventario.

        Args:
            player: El jugador
            dungeon: La mazmorra actual
            index: Índice del item en el inventario

        Returns:
            Lista de mensajes
        """
        messages = []

        item = player.get_inventory_item(index)

        if not item:
            messages.append("No tienes ese item.")
            return messages

        # Verificar si está equipado
        for slot, equipped in player.equipped.items():
            if equipped is item:
                messages.append(f"Primero debes desequipar {item.name}.")
                return messages

        # Soltar el item
        player.remove_from_inventory(item)
        dungeon.add_item(item, player.x, player.y)
        messages.append(f"Sueltas {item.name}.")

        return messages

    @staticmethod
    def drop_item_direct(player: Player, dungeon: Dungeon, item: Item) -> List[str]:
        """
        Suelta un item del inventario directamente (sin índice).
        Usado por el sistema de drag & drop del grid.

        Args:
            player: El jugador
            dungeon: La mazmorra actual
            item: El item a soltar

        Returns:
            Lista de mensajes
        """
        messages = []

        # Verificar si está equipado
        for slot, equipped in player.equipped.items():
            if equipped is item:
                messages.append(f"Primero debes desequipar {item.name}.")
                return messages

        # Soltar el item
        player.remove_from_inventory(item)
        dungeon.add_item(item, player.x, player.y)
        messages.append(f"Sueltas {item.name}.")
        return messages

    @staticmethod
    def use_item(player: Player, index: int) -> List[str]:
        """
        Usa un item del inventario.

        Args:
            player: El jugador
            index: Índice del item

        Returns:
            Lista de mensajes
        """
        messages = []

        item = player.get_inventory_item(index)

        if not item:
            messages.append("No tienes ese item.")
            return messages

        # Verificar si el item es usable
        if not hasattr(item, 'use') or not item.usable:
            messages.append(f"No puedes usar {item.name}.")
            return messages

        # Usar el item
        use_messages, consumed = item.use(player)
        messages.extend(use_messages)

        # Eliminar si se consumió
        if consumed:
            player.remove_from_inventory(item)

        return messages

    @staticmethod
    def equip_item(player: Player, index: int) -> List[str]:
        """
        Equipa un item del inventario.

        Args:
            player: El jugador
            index: Índice del item

        Returns:
            Lista de mensajes
        """
        messages = []

        item = player.get_inventory_item(index)

        if not item:
            messages.append("No tienes ese item.")
            return messages

        # Verificar si el item es equipable
        if not hasattr(item, 'slot') or not item.slot:
            messages.append(f"No puedes equipar {item.name}.")
            return messages

        # Equipar
        messages.extend(player.equip(item))

        return messages

    @staticmethod
    def unequip_item(player: Player, slot: str) -> List[str]:
        """
        Desequipa un item de un slot.

        Args:
            player: El jugador
            slot: Slot a desequipar

        Returns:
            Lista de mensajes
        """
        return player.unequip(slot)

    @staticmethod
    def get_inventory_display(player: Player) -> List[Tuple[str, str, bool]]:
        """
        Obtiene la información del inventario para mostrar.

        Args:
            player: El jugador

        Returns:
            Lista de tuplas (letra, descripción, equipado)
        """
        display = []

        for i, item in enumerate(player.inventory):
            letter = chr(ord('a') + i)

            # Verificar si está equipado
            is_equipped = any(
                equipped is item
                for equipped in player.equipped.values()
                if equipped is not None
            )

            name = item.name
            if is_equipped:
                name += " (equipado)"

            display.append((letter, name, is_equipped))

        return display

    @staticmethod
    def get_equipment_display(player: Player) -> List[Tuple[str, str]]:
        """
        Obtiene la información del equipo para mostrar.

        Args:
            player: El jugador

        Returns:
            Lista de tuplas (slot, nombre del item)
        """
        slot_names = {
            "weapon": "Arma",
            "armor": "Armadura",
            "ring_left": "Anillo Izq.",
            "ring_right": "Anillo Der.",
        }

        display = []

        for slot, item in player.equipped.items():
            slot_name = slot_names.get(slot, slot)
            item_name = item.name if item else "---"
            display.append((slot_name, item_name))

        return display
