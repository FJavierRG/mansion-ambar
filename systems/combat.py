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
            
            # Colocar sangre en el suelo (si no hay ya)
            if defender.dungeon and hasattr(defender.dungeon, 'decorations'):
                pos = (defender.x, defender.y)
                if pos not in defender.dungeon.decorations:
                    angle = random.choice([0, 90, 180, 270])
                    defender.dungeon.decorations[pos] = ("blood", angle)
            
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
            
            # Aplicar desgaste de equipo (solo en ataques confirmados)
            messages.extend(Combat._apply_equipment_wear(attacker, defender, animation_manager))
            
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
        
        elif isinstance(victim, Player):
            messages.append("¡Has muerto!")
        
        return messages
    
    @staticmethod
    def _apply_equipment_wear(attacker: Entity, defender: Entity, animation_manager=None) -> List[str]:
        """
        Aplica desgaste al equipo tras un ataque confirmado (no fallo).
        
        - Arma del atacante: pierde 1 de vida por ataque confirmado.
        - Armadura del defensor: pierde 1 de vida por golpe recibido confirmado.
        
        Args:
            attacker: Entidad atacante
            defender: Entidad defensora
            animation_manager: Gestor de animaciones (para texto flotante)
            
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
                # Texto flotante tachado sobre el jugador
                if animation_manager:
                    animation_manager.add_floating_text(
                        x=attacker.x,
                        y=attacker.y,
                        text=weapon.name,
                        text_style="strikethrough"
                    )
                # Sonido de equipo roto
                from ..systems.music import music_manager
                music_manager.play_sound("broken_equip.mp3")
                attacker.equipped["weapon"] = None
                attacker.remove_from_inventory(weapon)
            elif weapon.durability == 1:
                messages.append(
                    f"Tu {weapon.name} está a punto de romperse "
                    f"({weapon.durability}/{weapon.max_durability})."
                )
        
        # Desgaste de la armadura del defensor (si es jugador)
        if isinstance(defender, Player) and defender.equipped.get("armor"):
            armor = defender.equipped["armor"]
            armor.take_hit()
            
            if armor.is_broken():
                messages.append(f"¡Tu {armor.name} se ha destrozado!")
                # Texto flotante tachado sobre el jugador
                if animation_manager:
                    animation_manager.add_floating_text(
                        x=defender.x,
                        y=defender.y,
                        text=armor.name,
                        text_style="strikethrough"
                    )
                # Sonido de equipo roto
                from ..systems.music import music_manager
                music_manager.play_sound("broken_equip.mp3")
                defender.equipped["armor"] = None
                defender.remove_from_inventory(armor)
            elif armor.durability == 1:
                messages.append(
                    f"Tu {armor.name} está a punto de romperse "
                    f"({armor.durability}/{armor.max_durability})."
                )
        
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
