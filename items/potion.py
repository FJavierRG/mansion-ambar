"""
Clase Potion - Pociones consumibles.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Tuple

from .item import Item
from ..config import SYMBOLS

if TYPE_CHECKING:
    from ..entities.player import Player


class Potion(Item):
    """
    Representa una poción consumible.
    
    Attributes:
        potion_type: Tipo de poción
        effect: Efecto de la poción (heal, poison, strength, etc.)
        effect_value: Valor del efecto
        duration: Duración en turnos (para efectos temporales)
    """
    
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        potion_type: str = "health_potion",
        name: str = "Poción",
        effect: str = "heal",
        value: int = 10,
        duration: int = 0
    ) -> None:
        """
        Inicializa una poción.
        
        Args:
            x: Posición X
            y: Posición Y
            potion_type: Tipo de poción
            name: Nombre
            effect: Efecto
            value: Valor del efecto
            duration: Duración (turnos)
        """
        super().__init__(
            x=x,
            y=y,
            char=SYMBOLS["potion"],
            name=name,
            color="potion",
            item_type="potion",
            identified=True,
            usable=True,
            slot=None
        )
        
        self.potion_type = potion_type
        self.effect = effect
        self.effect_value = value
        self.duration = duration
    
    def use(self, player: Player) -> Tuple[List[str], bool]:
        """
        Usa la poción.
        
        Args:
            player: El jugador
            
        Returns:
            Tupla (mensajes, consumido)
        """
        messages = []
        consumed = True
        
        if self.effect == "heal":
            # Poción de curación
            healed = player.fighter.heal(self.effect_value)
            if healed > 0:
                messages.append(f"Bebes {self.name}. Te curas {healed} puntos de vida.")
            else:
                messages.append(f"Bebes {self.name}, pero ya estás a máxima salud.")
        
        elif self.effect == "poison":
            # Poción de veneno
            damage = abs(self.effect_value)
            player.fighter.take_damage(damage)
            messages.append(f"¡La poción está envenenada! Sufres {damage} de daño.")
            # Rastrear causa de muerte si el jugador muere por veneno
            if player.fighter.is_dead:
                player.death_cause = "poison"
        
        elif self.effect == "strength":
            # Poción de fuerza
            player.fighter.attack_bonus += self.effect_value
            player.fighter.bonus_duration = self.duration
            messages.append(
                f"Bebes {self.name}. Tu fuerza aumenta en {self.effect_value} "
                f"por {self.duration} turnos."
            )
        
        else:
            messages.append(f"Bebes {self.name}. No pasa nada.")
            consumed = False
        
        return (messages, consumed)
    
    def get_description(self) -> str:
        """Retorna la descripción de la poción."""
        if self.effect == "heal":
            return f"{self.name} (cura {self.effect_value} HP)"
        elif self.effect == "poison":
            return f"{self.name} (¿?)"  # No revelar que es veneno
        elif self.effect == "strength":
            return f"{self.name} (+{self.effect_value} ATK por {self.duration} turnos)"
        return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la poción."""
        data = super().to_dict()
        data.update({
            "potion_type": self.potion_type,
            "effect": self.effect,
            "effect_value": self.effect_value,
            "duration": self.duration,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Potion:
        """Crea una poción desde un diccionario."""
        potion = cls(
            x=data["x"],
            y=data["y"],
            potion_type=data.get("potion_type", "health_potion"),
            name=data["name"],
            effect=data.get("effect", "heal"),
            value=data.get("effect_value", 10),
            duration=data.get("duration", 0)
        )
        potion.identified = data.get("identified", True)
        potion.persistent = data.get("persistent", False)
        return potion
