"""
Clase Armor - Armaduras equipables con sistema de durabilidad.

La durabilidad representa la vida de la armadura: un número entero de usos.
Cada ataque recibido confirmado (no fallo) consume exactamente 1 punto de vida.
Cuando la vida llega a 0, la armadura se rompe.
Mientras no esté rota, el bonus de defensa se aplica íntegramente.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List

from .item import Item
from ..config import SYMBOLS

if TYPE_CHECKING:
    from ..entities.player import Player


class Armor(Item):
    """
    Representa una armadura equipable con durabilidad basada en usos.
    
    Attributes:
        armor_type: Tipo de armadura (clave en ARMOR_DATA)
        defense_bonus: Bonificación a la defensa (constante mientras no esté rota)
        durability: Vida actual de la armadura (golpes restantes)
        max_durability: Vida máxima de la armadura
    """
    
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        armor_type: str = "leather_armor",
        name: str = "Armadura de Cuero",
        defense_bonus: int = 2,
        durability: int = 6
    ) -> None:
        """
        Inicializa una armadura.
        
        Args:
            x: Posición X
            y: Posición Y
            armor_type: Tipo de armadura
            name: Nombre
            defense_bonus: Bonificación de defensa
            durability: Vida inicial (número de golpes antes de romperse)
        """
        super().__init__(
            x=x,
            y=y,
            char=SYMBOLS["armor"],
            name=name,
            color="armor",
            item_type="armor",
            identified=True,
            usable=False,
            slot="armor"
        )
        
        self.armor_type = armor_type
        self.defense_bonus = defense_bonus
        self.durability = durability
        self.max_durability = durability
    
    def take_hit(self) -> int:
        """
        Registra un golpe recibido (1 ataque confirmado contra el portador).
        
        Reduce la vida de la armadura en exactamente 1 punto.
        Solo debe llamarse cuando el ataque conecta (no en fallos).
        
        Returns:
            Vida restante de la armadura
        """
        self.durability = max(0, self.durability - 1)
        return self.durability
    
    def is_broken(self) -> bool:
        """Verifica si la armadura está rota (vida = 0)."""
        return self.durability <= 0
    
    def get_effective_defense(self) -> int:
        """
        Retorna la defensa efectiva de la armadura.
        
        Mientras la armadura tenga vida, el bonus es completo.
        Si está rota, el bonus es 0.
        """
        if self.is_broken():
            return 0
        return self.defense_bonus
    
    def get_description(self) -> str:
        """Retorna la descripción de la armadura."""
        return f"{self.name} (+{self.defense_bonus} DEF, {self.durability}/{self.max_durability})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la armadura."""
        data = super().to_dict()
        data.update({
            "armor_type": self.armor_type,
            "defense_bonus": self.defense_bonus,
            "durability": self.durability,
            "max_durability": self.max_durability,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Armor:
        """Crea una armadura desde un diccionario."""
        armor = cls(
            x=data["x"],
            y=data["y"],
            armor_type=data.get("armor_type", "leather_armor"),
            name=data["name"],
            defense_bonus=data.get("defense_bonus", 2),
            durability=data.get("durability", 6)
        )
        # Restaurar max_durability desde el save; fallback a durability actual
        armor.max_durability = data.get("max_durability", armor.durability)
        armor.persistent = data.get("persistent", False)
        return armor
