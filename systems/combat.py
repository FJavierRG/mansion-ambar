"""
Sistema de combate del juego.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple
import random

if TYPE_CHECKING:
    from ..entities.entity import Entity
    from ..entities.player import Player
    from ..entities.monster import Monster


class Combat:
    """
    Sistema de combate por turnos.
    
    Implementa las mecánicas de ataque, defensa y daño.
    """
    
    @staticmethod
    def attack(attacker: Entity, defender: Entity, animation_manager=None) -> List[str]:
        """
        Resuelve un ataque entre dos entidades.
        
        Args:
            attacker: Entidad atacante
            defender: Entidad defensora
            
        Returns:
            Lista de mensajes describiendo el combate
        """
        messages = []
        
        # Obtener stats
        attack_power = Combat._get_attack(attacker)
        defense_power = Combat._get_defense(defender)
        
        # Calcular daño base
        base_damage = attack_power - defense_power // 2
        
        # Añadir variación aleatoria (±20%)
        variance = max(1, int(base_damage * 0.2))
        damage = base_damage + random.randint(-variance, variance)
        
        # Mínimo 1 de daño si el ataque conecta
        damage = max(1, damage)
        
        # Probabilidad de crítico (10%)
        is_critical = random.random() < 0.1
        if is_critical:
            damage = int(damage * 1.5)
        
        # Probabilidad de fallo (5%)
        is_miss = random.random() < 0.05
        
        if is_miss:
            messages.append(f"{attacker.name} falla el ataque contra {defender.name}.")
        else:
            # Aplicar daño
            defender.fighter.take_damage(damage)
            
            # Añadir número de daño flotante si hay animation_manager
            if animation_manager:
                # Determinar si el atacante es el jugador
                from ..entities.player import Player
                is_player_attack = isinstance(attacker, Player)
                
                animation_manager.add_damage_number(
                    x=defender.x,
                    y=defender.y,
                    damage=damage,
                    is_critical=is_critical,
                    is_player_attack=is_player_attack
                )
            
            # Generar mensaje
            if is_critical:
                messages.append(
                    f"¡CRÍTICO! {attacker.name} golpea a {defender.name} "
                    f"por {damage} de daño."
                )
            else:
                messages.append(
                    f"{attacker.name} golpea a {defender.name} "
                    f"por {damage} de daño."
                )
            
            # Aplicar desgaste de equipo
            messages.extend(Combat._apply_equipment_wear(attacker, defender, damage))
            
            # Verificar muerte
            if defender.fighter.is_dead:
                messages.extend(Combat._handle_death(attacker, defender))
        
        return messages
    
    @staticmethod
    def _get_attack(entity: Entity) -> int:
        """Obtiene el poder de ataque de una entidad."""
        # Para el jugador, usa la propiedad attack que incluye equipo
        if hasattr(entity, 'attack') and callable(getattr(type(entity), 'attack', None).__get__):
            return entity.attack
        # Para monstruos, usa el fighter directamente
        if hasattr(entity, 'fighter'):
            return entity.fighter.attack
        return 1
    
    @staticmethod
    def _get_defense(entity: Entity) -> int:
        """Obtiene el poder de defensa de una entidad."""
        if hasattr(entity, 'defense') and callable(getattr(type(entity), 'defense', None).__get__):
            return entity.defense
        if hasattr(entity, 'fighter'):
            return entity.fighter.defense
        return 0
    
    @staticmethod
    def _handle_death(killer: Entity, victim: Entity) -> List[str]:
        """
        Maneja la muerte de una entidad.
        
        Args:
            killer: Quien mató
            victim: Quien murió
            
        Returns:
            Lista de mensajes
        """
        messages = []
        
        # Si el jugador mata a un monstruo
        from ..entities.player import Player
        from ..entities.monster import Monster
        
        if isinstance(killer, Player) and isinstance(victim, Monster):
            # Dar experiencia
            xp = victim.fighter.xp
            xp_messages = killer.gain_xp(xp)
            messages.extend(xp_messages)
            
            # Procesar muerte del monstruo
            death_messages = victim.die()
            messages.extend(death_messages)
            
            # Drop de oro
            gold_drop = random.randint(1, 5) * (victim.dungeon.floor if victim.dungeon else 1)
            killer.gold += gold_drop
            messages.append(f"Encuentras {gold_drop} monedas de oro.")
        
        elif isinstance(victim, Player):
            messages.append("¡Has muerto!")
        
        return messages
    
    @staticmethod
    def _apply_equipment_wear(attacker: Entity, defender: Entity, damage: int) -> List[str]:
        """
        Aplica desgaste al equipo del atacante (arma) y defensor (armadura).
        
        Args:
            attacker: Entidad atacante
            defender: Entidad defensora
            damage: Daño causado
            
        Returns:
            Lista de mensajes sobre el desgaste
        """
        messages = []
        from ..entities.player import Player
        
        # Desgaste del arma del atacante (si es jugador)
        if isinstance(attacker, Player) and attacker.equipped.get("weapon"):
            weapon = attacker.equipped["weapon"]
            weapon.use_weapon()
            
            if weapon.is_broken():
                messages.append(f"¡Tu {weapon.name} se ha roto!")
                attacker.equipped["weapon"] = None
                # Eliminar del inventario si está ahí
                if weapon in attacker.inventory:
                    attacker.inventory.remove(weapon)
            elif weapon.durability <= 20:
                messages.append(f"Tu {weapon.name} está muy dañada ({weapon.durability}%).")
        
        # Desgaste de la armadura del defensor (si es jugador)
        if isinstance(defender, Player) and defender.equipped.get("armor"):
            armor = defender.equipped["armor"]
            armor.take_damage(damage)
            
            if armor.is_broken():
                messages.append(f"¡Tu {armor.name} se ha destrozado!")
                defender.equipped["armor"] = None
                # Eliminar del inventario si está ahí
                if armor in defender.inventory:
                    defender.inventory.remove(armor)
            elif armor.durability <= 20:
                messages.append(f"Tu {armor.name} está muy dañada ({armor.durability}%).")
        
        return messages
    
    @staticmethod
    def calculate_damage_preview(attacker: Entity, defender: Entity) -> Tuple[int, int]:
        """
        Calcula el rango de daño esperado.
        
        Args:
            attacker: Entidad atacante
            defender: Entidad defensora
            
        Returns:
            Tupla (daño_mínimo, daño_máximo)
        """
        attack_power = Combat._get_attack(attacker)
        defense_power = Combat._get_defense(defender)
        
        base_damage = max(1, attack_power - defense_power // 2)
        variance = max(1, int(base_damage * 0.2))
        
        min_damage = max(1, base_damage - variance)
        max_damage = int((base_damage + variance) * 1.5)  # Con crítico
        
        return (min_damage, max_damage)
