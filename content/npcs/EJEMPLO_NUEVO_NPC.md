# Guía: Cómo Añadir un Nuevo NPC

Este documento explica cómo añadir un nuevo NPC al sistema FSM de forma modular.

## 📋 Pasos

### 1. Crear el archivo del NPC

Crea un nuevo archivo en `roguelike/content/npcs/` con el nombre del NPC (ej: `merchant.py`).

### 2. Definir los diálogos

Crea funciones que retornen `DialogTree` o `InteractiveText`:

```python
"""
Diálogos del NPC Merchant.
"""
from roguelike.systems.text import DialogTree, DialogNode, DialogOption, InteractiveText


def create_merchant_greeting_dialog() -> DialogTree:
    """Diálogo inicial del comerciante."""
    tree = DialogTree(start_node="greeting")
    
    greeting_node = DialogNode(
        node_id="greeting",
        speaker="Merchant",
        text="¡Bienvenido a mi tienda!",
        options=[
            DialogOption("Ver inventario", next_node="inventory"),
            DialogOption("Adiós", next_node=None)
        ]
    )
    tree.add_node(greeting_node)
    
    return tree


def create_merchant_greeting_completed() -> InteractiveText:
    """Diálogo corto cuando ya hablaste con el comerciante."""
    return InteractiveText.create_simple_text(
        "¿Necesitas algo más?",
        title="Merchant",
        auto_close=False
    )
```

### 3. Registrar los estados del NPC

Añade la función `register_npc_states()` al final del archivo:

```python
def register_npc_states(manager) -> None:
    """
    Registra todos los estados del Merchant en el sistema FSM.
    
    Esta función es llamada automáticamente por el sistema de auto-discovery.
    
    Args:
        manager: Instancia de NPCStateManager
    """
    from roguelike.systems.npc_states import NPCStateConfig, StateTransition
    from roguelike.systems.events import event_manager
    
    # Estado "greeting" - Lobby, primera vez
    manager.register_npc_state("Merchant", NPCStateConfig(
        state_id="greeting",
        zone_type="lobby",
        position=(50, 20),  # Posición fija en el lobby
        dialog_tree_func=create_merchant_greeting_dialog,
        completed_dialog_func=create_merchant_greeting_completed,
        completion_condition=lambda p, z: event_manager.is_event_triggered("merchant_met"),
        transitions=[
            StateTransition(
                target_state="selling",
                condition=lambda p, z: event_manager.is_event_triggered("merchant_first_sale"),
                description="Después de la primera venta"
            )
        ]
    ))
    
    # Estado "selling" - Lobby, después de la primera venta
    manager.register_npc_state("Merchant", NPCStateConfig(
        state_id="selling",
        zone_type="lobby",
        position=(50, 20),
        dialog_tree_func=create_merchant_selling_dialog,
        completed_dialog_func=create_merchant_selling_completed,
        # No tiene transiciones, es el estado final
    ))
```

### 4. ¡Listo!

El sistema de auto-discovery encontrará automáticamente tu nuevo NPC y lo registrará. No necesitas modificar ningún otro archivo.

## 🎯 Características del Sistema

- **Auto-discovery**: El sistema encuentra automáticamente todos los NPCs
- **Modular**: Cada NPC está en su propio archivo
- **Escalable**: Puedes añadir 50+ NPCs sin modificar el código del manager
- **Centralizado**: Todo el estado se gestiona desde `NPCStateManager`

## 📝 Notas

- El nombre del NPC debe coincidir exactamente con el usado en `register_npc_state()`
- Los estados se spawnean automáticamente según su `zone_type` y condiciones
- Las transiciones se verifican automáticamente cuando se cumplen las condiciones
- Los eventos se pueden activar desde las acciones de los `DialogNode`
