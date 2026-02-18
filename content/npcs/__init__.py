"""
Sistema de auto-discovery para NPCs.
Cada archivo de NPC debe exportar una función `register_npc_states(manager)`.
"""
from typing import TYPE_CHECKING
import importlib
import pkgutil

if TYPE_CHECKING:
    from ...systems.npc_states import NPCStateManager


def register_all_npcs(manager: 'NPCStateManager') -> None:
    """
    Registra todos los NPCs automáticamente descubriendo módulos en este paquete.
    
    Cada módulo de NPC debe tener una función `register_npc_states(manager)`.
    
    Args:
        manager: El gestor de estados de NPCs
    """
    # Obtener el paquete actual
    package = __package__
    
    # Iterar sobre todos los módulos en este paquete
    for _, module_name, is_pkg in pkgutil.iter_modules(__path__, package + "."):
        if is_pkg or module_name == __name__:
            continue
        
        try:
            # Importar el módulo
            module = importlib.import_module(module_name)
            
            # Buscar la función de registro
            if hasattr(module, 'register_npc_states'):
                register_func = getattr(module, 'register_npc_states')
                if callable(register_func):
                    register_func(manager)
        except Exception as e:
            # Si hay un error al importar o registrar, continuar con el siguiente
            print(f"[WARNING] Error al registrar NPC desde {module_name}: {e}")
            continue
