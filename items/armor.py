"""
Clase Armor - Armaduras equipables con sistema de durabilidad.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List

from .item import Item
from ..config import SYMBOLS

if TYPE_CHECKING:
    from ..entities.player import Player


class Armor(Item):
    """
    Representa una armadura equipable con durabilidad.
    
    Attributes:
        armor_type: Tipo de armadura
        defense_bonus: Bonificación a la defensa
        durability: Durabilidad actual (0-100%)
        max_durability: Durabilidad máxima
    """
    
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        armor_type: str = "leather_armor",
        name: str = "Armadura de Cuero",
        defense_bonus: int = 2,
        durability: int = 100
    ) -> None:
        """
        Inicializa una armadura.
        
        Args:
            x: Posición X
            y: Posición Y
            armor_type: Tipo de armadura
            name: Nombre
            defense_bonus: Bonificación de defensa
            durability: Durabilidad inicial (0-100%)
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
        self.max_durability = 100
    
    def take_damage(self, damage_received: int) -> int:
        """
        Reduce la durabilidad de la armadura al recibir daño.
        
        La durabilidad se reduce proporcionalmente al daño recibido.
        Armaduras más fuertes se gastan más lento.
        
        Args:
            damage_received: Daño que recibió el jugador
            
        Returns:
            Nueva durabilidad
        """
        # Desgaste base: 2-5% por golpe, reducido por calidad de armadura
        # Armaduras con más defensa se gastan más lento
        base_wear = max(2, 6 - self.defense_bonus // 2)
        
        # Añadir algo de variación
        import random
        wear = base_wear + random.randint(-1, 1)
        wear = max(1, wear)
        
        self.durability = max(0, self.durability - wear)
        return self.durability
    
    def is_broken(self) -> bool:
        """Verifica si la armadura está rota."""
        return self.durability <= 0
    
    def get_effective_defense(self) -> int:
        """
        Retorna la defensa efectiva según la durabilidad.
        
        A menor durabilidad, menor defensa efectiva.
        """
        if self.durability <= 0:
            return 0
        # La defensa se reduce proporcionalmente a la durabilidad
        # pero mantiene al menos 1 si no está rota
        effective = int(self.defense_bonus * (self.durability / 100))
        return max(1, effective) if self.durability > 0 else 0
    
    def get_description(self) -> str:
        """Retorna la descripción de la armadura."""
        return f"{self.name} (+{self.defense_bonus} DEF, {self.durability}%)"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la armadura."""
        data = super().to_dict()
        data.update({
            "armor_type": self.armor_type,
            "defense_bonus": self.defense_bonus,
            "durability": self.durability,
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
            durability=data.get("durability", 100)
        )
        armor.persistent = data.get("persistent", False)
        return armor
