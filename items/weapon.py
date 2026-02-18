"""
Clase Weapon - Armas equipables con sistema de durabilidad.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List

from .item import Item
from ..config import SYMBOLS

if TYPE_CHECKING:
    from ..entities.player import Player


class Weapon(Item):
    """
    Representa un arma equipable con durabilidad.
    
    Attributes:
        weapon_type: Tipo de arma
        attack_bonus: Bonificación al ataque
        durability: Durabilidad actual (0-100%)
        max_durability: Durabilidad máxima
    """
    
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        weapon_type: str = "dagger",
        name: str = "Daga",
        attack_bonus: int = 2,
        durability: int = 100
    ) -> None:
        """
        Inicializa un arma.
        
        Args:
            x: Posición X
            y: Posición Y
            weapon_type: Tipo de arma
            name: Nombre
            attack_bonus: Bonificación de ataque
            durability: Durabilidad inicial (0-100%)
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
        self.max_durability = 100
    
    def use_weapon(self) -> int:
        """
        Reduce la durabilidad del arma al atacar.
        
        Armas más fuertes se gastan más lento.
        
        Returns:
            Nueva durabilidad
        """
        # Desgaste base: 1-4% por ataque, reducido por calidad del arma
        # Armas con más ataque se gastan más lento
        base_wear = max(1, 5 - self.attack_bonus // 3)
        
        # Añadir algo de variación
        import random
        wear = base_wear + random.randint(-1, 1)
        wear = max(1, wear)
        
        self.durability = max(0, self.durability - wear)
        return self.durability
    
    def is_broken(self) -> bool:
        """Verifica si el arma está rota."""
        return self.durability <= 0
    
    def get_effective_attack(self) -> int:
        """
        Retorna el ataque efectivo según la durabilidad.
        
        A menor durabilidad, menor ataque efectivo.
        """
        if self.durability <= 0:
            return 0
        # El ataque se reduce proporcionalmente a la durabilidad
        # pero mantiene al menos 1 si no está rota
        effective = int(self.attack_bonus * (self.durability / 100))
        return max(1, effective) if self.durability > 0 else 0
    
    def get_description(self) -> str:
        """Retorna la descripción del arma."""
        return f"{self.name} (+{self.attack_bonus} ATK, {self.durability}%)"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el arma."""
        data = super().to_dict()
        data.update({
            "weapon_type": self.weapon_type,
            "attack_bonus": self.attack_bonus,
            "durability": self.durability,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Weapon:
        """Crea un arma desde un diccionario."""
        weapon = cls(
            x=data["x"],
            y=data["y"],
            weapon_type=data.get("weapon_type", "dagger"),
            name=data["name"],
            attack_bonus=data.get("attack_bonus", 2),
            durability=data.get("durability", 100)
        )
        weapon.persistent = data.get("persistent", False)
        return weapon
