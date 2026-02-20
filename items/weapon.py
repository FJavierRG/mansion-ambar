"""
Clase Weapon - Armas equipables con sistema de durabilidad.

La durabilidad representa la vida del arma: un número entero de usos.
Cada ataque confirmado (no fallo) consume exactamente 1 punto de vida.
Cuando la vida llega a 0, el arma se rompe.
Mientras no esté rota, el bonus de ataque se aplica íntegramente.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional

from .item import Item
from ..config import SYMBOLS

if TYPE_CHECKING:
    from ..entities.player import Player


class Weapon(Item):
    """
    Representa un arma equipable con durabilidad basada en usos.
    
    Attributes:
        weapon_type: Tipo de arma (clave en WEAPON_DATA)
        attack_bonus: Bonificación al ataque (constante mientras no esté rota)
        durability: Vida actual del arma (usos restantes)
        max_durability: Vida máxima del arma
    """
    
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        weapon_type: str = "bronze_dagger",
        name: str = "Daga de bronce",
        attack_bonus: int = 1,
        durability: int = 5,
        sprite_key: Optional[str] = None
    ) -> None:
        """
        Inicializa un arma.
        
        Args:
            x: Posición X
            y: Posición Y
            weapon_type: Tipo de arma
            name: Nombre
            attack_bonus: Bonificación de ataque
            durability: Vida inicial (número de usos antes de romperse)
            sprite_key: Clave de sprite visual (ej: "dagger", "sword", "axe", "spear")
        """
        super().__init__(
            x=x,
            y=y,
            char=SYMBOLS["weapon"],
            name=name,
            color="weapon",
            item_type="weapon",
            identified=True,
            usable=False,
            slot="weapon"
        )
        
        self.weapon_type = weapon_type
        self.attack_bonus = attack_bonus
        self.durability = durability
        self.max_durability = durability
        self.sprite = sprite_key
    
    def use_weapon(self) -> int:
        """
        Registra un uso del arma (1 ataque confirmado).
        
        Reduce la vida del arma en exactamente 1 punto.
        Solo debe llamarse cuando el ataque conecta (no en fallos).
        
        Returns:
            Vida restante del arma
        """
        self.durability = max(0, self.durability - 1)
        return self.durability
    
    def is_broken(self) -> bool:
        """Verifica si el arma está rota (vida = 0)."""
        return self.durability <= 0
    
    def get_effective_attack(self) -> int:
        """
        Retorna el ataque efectivo del arma.
        
        Mientras el arma tenga vida, el bonus es completo.
        Si está rota, el bonus es 0.
        """
        if self.is_broken():
            return 0
        return self.attack_bonus
    
    def get_description(self) -> str:
        """Retorna la descripción del arma."""
        return f"{self.name} (+{self.attack_bonus} ATK, {self.durability}/{self.max_durability})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el arma."""
        data = super().to_dict()
        data.update({
            "weapon_type": self.weapon_type,
            "attack_bonus": self.attack_bonus,
            "durability": self.durability,
            "max_durability": self.max_durability,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Weapon:
        """Crea un arma desde un diccionario."""
        weapon = cls(
            x=data["x"],
            y=data["y"],
            weapon_type=data.get("weapon_type", "bronze_dagger"),
            name=data["name"],
            attack_bonus=data.get("attack_bonus", 2),
            durability=data.get("durability", 8),
            sprite_key=data.get("sprite")
        )
        # Restaurar max_durability desde el save; fallback a durability actual
        weapon.max_durability = data.get("max_durability", weapon.durability)
        weapon.persistent = data.get("persistent", False)
        weapon.grid_width = data.get("grid_width", 1)
        weapon.grid_height = data.get("grid_height", 2)
        weapon.description = data.get("description", "")
        return weapon
