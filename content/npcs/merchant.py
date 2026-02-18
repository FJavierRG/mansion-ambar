"""
Diálogos del NPC Merchant (Comerciante).
Este es un ejemplo completo de cómo crear un nuevo NPC con múltiples estados.

ESTADO INICIAL: greeting (Lobby)
ESTADO FINAL: trading (Lobby, después de la primera compra)
"""
from roguelike.systems.text import DialogTree, DialogNode, DialogOption, InteractiveText


# ============================================================================
# ESTADO: "greeting" (Lobby - Primera vez que lo encuentras)
# ============================================================================

def create_merchant_greeting_dialog() -> DialogTree:
    """
    Crea el diálogo del Merchant cuando lo encuentras por primera vez.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="greeting")
    
    # Nodo inicial: saludo
    greeting_node = DialogNode(
        node_id="greeting",
        speaker="Merchant",
        text="¡Bienvenido, viajero! Soy un comerciante ambulante.\n---Tengo algunos objetos útiles que podrían interesarte.\n---¿Quieres ver mi mercancía?",
        options=[
            DialogOption("Ver inventario", next_node="inventory"),
            DialogOption("¿Quién eres?", next_node="who_are_you"),
            DialogOption("Adiós", next_node=None)  # Cierra el diálogo
        ]
    )
    tree.add_node(greeting_node)
    
    # Nodo de inventario
    inventory_node = DialogNode(
        node_id="inventory",
        speaker="Merchant",
        text="Aquí tienes mi mercancía:\n---[Por ahora solo tengo pociones de vida básicas]\n---¿Te interesa algo?",
        options=[
            DialogOption("Comprar poción de vida (50 oro)", next_node="buy_potion"),
            DialogOption("No, gracias", next_node="greeting")
        ]
    )
    tree.add_node(inventory_node)
    
    # Nodo de compra de poción
    def on_buy_potion(player, zone):
        """Acción cuando el jugador compra una poción."""
        from roguelike.systems.events import event_manager
        
        # Verificar que el jugador tenga suficiente oro
        # (Aquí asumimos que el jugador tiene un atributo gold)
        if hasattr(player, 'gold') and player.gold >= 50:
            player.gold -= 50
            # Añadir poción al inventario del jugador
            from roguelike.items.potion import Potion
            from roguelike.config import POTION_DATA
            potion = Potion.from_data(POTION_DATA["health_potion"])
            player.inventory.append(potion)
            
            # Activar evento de primera compra
            event_manager.trigger_event("merchant_first_sale", player, zone, skip_conditions=True)
            
            return True
        return False
    
    buy_potion_node = DialogNode(
        node_id="buy_potion",
        speaker="Merchant",
        text="¡Excelente elección! Una poción de vida te será muy útil.\n---Gracias por tu compra. ¡Vuelve cuando quieras!",
        options=[
            DialogOption(
                "Gracias", 
                next_node=None,
                action=lambda p, z: on_buy_potion(p, z) or None  # Ejecuta acción al seleccionar
            )
        ]
    )
    tree.add_node(buy_potion_node)
    
    # Nodo de "¿Quién eres?"
    who_node = DialogNode(
        node_id="who_are_you",
        speaker="Merchant",
        text="Soy un comerciante que viaja entre las mazmorras.\n---He visto muchas cosas en mis viajes...\n---Pero eso es otra historia. ¿Quieres ver mi mercancía?",
        options=[
            DialogOption("Sí, ver inventario", next_node="inventory"),
            DialogOption("No, gracias", next_node="greeting")
        ]
    )
    tree.add_node(who_node)
    
    return tree


def create_merchant_greeting_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'greeting' está completado."""
    return InteractiveText.create_simple_text(
        "¡Bienvenido de nuevo! ¿Necesitas algo más?",
        title="Merchant",
        auto_close=False
    )


# ============================================================================
# ESTADO: "trading" (Lobby - Después de la primera compra)
# ============================================================================

def create_merchant_trading_dialog() -> DialogTree:
    """
    Crea el diálogo del Merchant después de la primera compra.
    En este estado, el comerciante tiene más opciones disponibles.
    
    Returns:
        DialogTree con el diálogo completo
    """
    tree = DialogTree(start_node="welcome_back")
    
    # Nodo de bienvenida
    welcome_node = DialogNode(
        node_id="welcome_back",
        speaker="Merchant",
        text="¡Ah, eres tú! Me alegra verte de nuevo.\n---Ahora que eres un cliente regular, puedo ofrecerte mejores productos.\n---¿Qué te interesa?",
        options=[
            DialogOption("Ver inventario mejorado", next_node="better_inventory"),
            DialogOption("¿Tienes algo especial?", next_node="special_items"),
            DialogOption("Adiós", next_node=None)
        ]
    )
    tree.add_node(welcome_node)
    
    # Nodo de inventario mejorado
    better_inventory_node = DialogNode(
        node_id="better_inventory",
        speaker="Merchant",
        text="Aquí tienes mi mejor mercancía:\n---• Poción de vida mayor (100 oro)\n---• Poción de fuerza (150 oro)\n---• Espada corta (200 oro)",
        options=[
            DialogOption("Comprar poción de vida mayor", next_node="buy_greater_potion"),
            DialogOption("Comprar poción de fuerza", next_node="buy_strength_potion"),
            DialogOption("Comprar espada corta", next_node="buy_sword"),
            DialogOption("Volver", next_node="welcome_back")
        ]
    )
    tree.add_node(better_inventory_node)
    
    # Nodo de compra de poción mayor
    def on_buy_greater_potion(player, zone):
        """Acción cuando el jugador compra una poción mayor."""
        if hasattr(player, 'gold') and player.gold >= 100:
            player.gold -= 100
            from roguelike.items.potion import Potion
            from roguelike.config import POTION_DATA
            potion = Potion.from_data(POTION_DATA["greater_health_potion"])
            player.inventory.append(potion)
            return True
        return False
    
    buy_greater_potion_node = DialogNode(
        node_id="buy_greater_potion",
        speaker="Merchant",
        text="¡Excelente! Esta poción te curará mucho más que la básica.\n---Gracias por tu compra.",
        options=[
            DialogOption(
                "Gracias",
                next_node=None,
                action=lambda p, z: on_buy_greater_potion(p, z) or None
            )
        ]
    )
    tree.add_node(buy_greater_potion_node)
    
    # Nodo de compra de poción de fuerza
    def on_buy_strength_potion(player, zone):
        """Acción cuando el jugador compra una poción de fuerza."""
        if hasattr(player, 'gold') and player.gold >= 150:
            player.gold -= 150
            from roguelike.items.potion import Potion
            from roguelike.config import POTION_DATA
            potion = Potion.from_data(POTION_DATA["strength_potion"])
            player.inventory.append(potion)
            return True
        return False
    
    buy_strength_potion_node = DialogNode(
        node_id="buy_strength_potion",
        speaker="Merchant",
        text="¡Buena elección! Esta poción aumentará tu fuerza temporalmente.\n---Úsala con sabiduría.",
        options=[
            DialogOption(
                "Entendido",
                next_node=None,
                action=lambda p, z: on_buy_strength_potion(p, z) or None
            )
        ]
    )
    tree.add_node(buy_strength_potion_node)
    
    # Nodo de compra de espada
    def on_buy_sword(player, zone):
        """Acción cuando el jugador compra una espada."""
        if hasattr(player, 'gold') and player.gold >= 200:
            player.gold -= 200
            from roguelike.items.weapon import Weapon
            from roguelike.config import WEAPON_DATA
            sword = Weapon.from_data(WEAPON_DATA["short_sword"])
            player.inventory.append(sword)
            return True
        return False
    
    buy_sword_node = DialogNode(
        node_id="buy_sword",
        speaker="Merchant",
        text="¡Una espada excelente! Esta te ayudará mucho en combate.\n---Que te sirva bien.",
        options=[
            DialogOption(
                "Gracias",
                next_node=None,
                action=lambda p, z: on_buy_sword(p, z) or None
            )
        ]
    )
    tree.add_node(buy_sword_node)
    
    # Nodo de items especiales
    special_items_node = DialogNode(
        node_id="special_items",
        speaker="Merchant",
        text="Hmm... items especiales...\n---Por ahora no tengo nada realmente especial.\n---Pero si sigues explorando las mazmorras, tal vez encuentres algo interesante.\n---O tal vez yo encuentre algo en mis viajes...",
        options=[
            DialogOption("Entendido", next_node="welcome_back"),
            DialogOption("Ver inventario", next_node="better_inventory")
        ]
    )
    tree.add_node(special_items_node)
    
    return tree


def create_merchant_trading_completed() -> InteractiveText:
    """Diálogo corto cuando el estado 'trading' está completado."""
    return InteractiveText.create_simple_text(
        "¡Bienvenido de nuevo! ¿Necesitas algo más?",
        title="Merchant",
        auto_close=False
    )


# ============================================================================
# REGISTRO DE ESTADOS DEL NPC
# ============================================================================
# NOTA: Este NPC es solo un ejemplo. Para que no se spawnee automáticamente,
# comentamos la función de registro. Si quieres usarlo, descomenta esta función.

# def register_npc_states(manager) -> None:
    """
    Registra todos los estados del Merchant en el sistema FSM.
    
    Esta función es llamada automáticamente por el sistema de auto-discovery.
    
    Args:
        manager: Instancia de NPCStateManager
    """
    from roguelike.systems.npc_states import NPCStateConfig, StateTransition
    from roguelike.systems.events import event_manager
    
    # Estado "greeting" - Lobby, primera vez que lo encuentras
    manager.register_npc_state("Merchant", NPCStateConfig(
        state_id="greeting",
        zone_type="lobby",
        position=(50, 20),  # Posición fija en el lobby
        dialog_tree_func=create_merchant_greeting_dialog,
        completed_dialog_func=create_merchant_greeting_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("merchant_met"),
        transitions=[
            StateTransition(
                target_state="trading",
                condition=lambda p, z: event_manager.is_event_triggered("merchant_first_sale"),
                description="Después de la primera compra"
            )
        ]
    ))
    
    # Estado "trading" - Lobby, después de la primera compra (estado final)
    manager.register_npc_state("Merchant", NPCStateConfig(
        state_id="trading",
        zone_type="lobby",
        position=(50, 20),  # Misma posición
        dialog_tree_func=create_merchant_trading_dialog,
        completed_dialog_func=create_merchant_trading_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("merchant_first_sale"),
        # No tiene transiciones, es el estado final
    ))


# ============================================================================
# NOTAS PARA DESARROLLADORES
# ============================================================================
"""
ESTRUCTURA DEL NPC MERCHANT:

1. ESTADOS:
   - greeting: Primera vez que encuentras al comerciante
   - trading: Después de hacer tu primera compra

2. TRANSICIONES:
   - greeting → trading: Cuando se activa el evento "merchant_first_sale"

3. EVENTOS UTILIZADOS:
   - merchant_met: Se activa cuando hablas con el comerciante por primera vez
   - merchant_first_sale: Se activa cuando compras algo por primera vez

4. POSICIÓN:
   - Lobby en (50, 20)

5. CARACTERÍSTICAS:
   - Tiene múltiples opciones de diálogo
   - Permite comprar items
   - Cambia de estado después de la primera compra
   - Tiene diálogos cortos cuando el estado está completado

EJEMPLO DE USO:
Este NPC es un ejemplo completo que muestra:
- Múltiples estados con transiciones
- Diálogos complejos con múltiples opciones
- Acciones en los diálogos (comprar items)
- Activación de eventos desde los diálogos
- Diálogos cortos para estados completados

Para usar este NPC como plantilla:
1. Copia este archivo
2. Cambia "Merchant" por el nombre de tu NPC
3. Modifica los diálogos según necesites
4. Ajusta los estados y transiciones
5. El sistema lo descubrirá automáticamente
"""
