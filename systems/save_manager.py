"""
Sistema de gestión de guardados múltiples.
Permite tener varios slots de guardado con información detallada.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any, List
import pickle
import os
from datetime import datetime

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..world.zone import Zone


class SaveSlot:
    """
    Información de un slot de guardado.
    
    Attributes:
        slot_id: ID del slot (1, 2, etc.)
        exists: Si el slot tiene un guardado
        player_name: Nombre del jugador (si existe)
        max_floor_reached: Piso más profundo alcanzado
        player_level: Nivel del jugador
        save_date: Fecha y hora del guardado
        play_time: Tiempo de juego (en segundos)
    """
    
    def __init__(self, slot_id: int):
        """Inicializa un slot vacío."""
        self.slot_id = slot_id
        self.exists = False
        self.player_name = "Jugador"
        self.max_floor_reached = 0
        self.player_level = 1
        self.save_date: Optional[datetime] = None
        self.play_time = 0
        self.has_amulet = False
    
    def load_metadata(self, save_file: str) -> bool:
        """
        Carga los metadatos del guardado sin cargar todo el juego.
        
        Args:
            save_file: Ruta del archivo de guardado
            
        Returns:
            True si se cargó correctamente
        """
        if not os.path.exists(save_file):
            self.exists = False
            return False
        
        try:
            with open(save_file, "rb") as f:
                save_data = pickle.load(f)
            
            # Extraer información del jugador
            player_data = save_data.get("player", {})
            self.player_name = player_data.get("name", "Jugador")
            self.player_level = player_data.get("fighter", {}).get("level", 1)
            self.max_floor_reached = save_data.get("max_floor_reached", save_data.get("current_floor", 0))
            self.play_time = save_data.get("play_time", 0)
            self.has_amulet = save_data.get("has_amulet", False)
            
            # Fecha del guardado
            if "save_date" in save_data:
                self.save_date = save_data["save_date"]
            else:
                # Usar fecha de modificación del archivo
                self.save_date = datetime.fromtimestamp(os.path.getmtime(save_file))
            
            self.exists = True
            return True
        except Exception:
            self.exists = False
            return False
    
    def get_display_info(self) -> str:
        """
        Retorna información formateada para mostrar en la UI.
        
        Returns:
            String con la información del slot
        """
        if not self.exists:
            return "Slot vacío"
        
        floor_info = f"Piso {self.max_floor_reached}" if self.max_floor_reached > 0 else "Lobby"
        level_info = f"Nivel {self.player_level}"
        amulet_info = " ✓ Amuleto" if self.has_amulet else ""
        
        date_str = ""
        if self.save_date:
            date_str = self.save_date.strftime("%d/%m/%Y %H:%M")
        
        return f"{floor_info} | {level_info}{amulet_info} | {date_str}"


class SaveManager:
    """
    Gestor de múltiples slots de guardado.
    
    Attributes:
        num_slots: Número de slots disponibles
        slots: Lista de slots
        save_dir: Directorio donde se guardan los archivos
    """
    
    def __init__(self, num_slots: int = 2, save_dir: str = "."):
        """
        Inicializa el gestor de guardados.
        
        Args:
            num_slots: Número de slots disponibles
            save_dir: Directorio donde guardar los archivos
        """
        self.num_slots = num_slots
        self.save_dir = save_dir
        self.slots: List[SaveSlot] = []
        
        # Inicializar slots
        for i in range(1, num_slots + 1):
            slot = SaveSlot(i)
            save_file = self.get_save_file_path(i)
            slot.load_metadata(save_file)
            self.slots.append(slot)
    
    def get_save_file_path(self, slot_id: int) -> str:
        """
        Obtiene la ruta del archivo de guardado para un slot.
        
        Args:
            slot_id: ID del slot
            
        Returns:
            Ruta del archivo
        """
        return os.path.join(self.save_dir, f"roguelike_save_{slot_id}.dat")
    
    def save_game(self, slot_id: int, player: 'Player', dungeon: 'Zone', dungeons: Dict[int, 'Zone'], 
                  play_time: int = 0) -> bool:
        """
        Guarda el juego en un slot específico.
        
        Args:
            slot_id: ID del slot (1-indexed)
            player: El jugador
            dungeon: Zona actual
            dungeons: Diccionario de mazmorras generadas
            play_time: Tiempo de juego en segundos
            
        Returns:
            True si se guardó correctamente
        """
        if slot_id < 1 or slot_id > self.num_slots:
            return False
        
        try:
            from ..world.lobby import Lobby
            from ..world.dungeon import Dungeon
            from ..systems.events import event_manager
            
            save_data = {
                "player": player.to_dict(),
                "dungeons": {
                    floor: d.to_dict()
                    for floor, d in dungeons.items()
                },
                "current_floor": player.current_floor,
                "max_floor_reached": player.max_floor_reached if hasattr(player, 'max_floor_reached') else player.current_floor,
                "play_time": play_time,
                "has_amulet": player.has_amulet if hasattr(player, 'has_amulet') else False,
                "save_date": datetime.now(),
            }
            
            # Guardar lobby si estamos en él o si existe un lobby guardado
            if isinstance(dungeon, Lobby):
                save_data["lobby"] = dungeon.to_dict()
                save_data["in_lobby"] = True
            else:
                save_data["in_lobby"] = False
                # También guardar el lobby si existe (aunque no estemos en él)
                # Esto permite mantener el estado del lobby entre sesiones
                # Nota: Necesitamos acceso al lobby desde game, pero por ahora
                # solo guardamos el lobby cuando estamos en él
            
            # Guardar estado de eventos (cada save tiene su propio estado)
            save_data["events"] = event_manager.to_dict()
            
            # Guardar estados FSM de NPCs (cada save tiene su propio estado de NPCs)
            from ..systems.npc_states import npc_state_manager
            save_data["npc_states"] = {
                "current_states": npc_state_manager.npc_current_states.copy(),
                "state_completion": {
                    npc_name: {
                        state_id: completion.value
                        for state_id, completion in states.items()
                    }
                    for npc_name, states in npc_state_manager.npc_state_completion.items()
                }
            }
            
            save_file = self.get_save_file_path(slot_id)
            with open(save_file, "wb") as f:
                pickle.dump(save_data, f)
            
            # Actualizar metadata del slot
            self.slots[slot_id - 1].load_metadata(save_file)
            
            return True
        except Exception as e:
            print(f"Error al guardar: {e}")
            return False
    
    def load_game(self, slot_id: int) -> Optional[Dict[str, Any]]:
        """
        Carga un juego desde un slot.
        
        Args:
            slot_id: ID del slot (1-indexed)
            
        Returns:
            Datos del guardado o None si falla
        """
        if slot_id < 1 or slot_id > self.num_slots:
            return None
        
        save_file = self.get_save_file_path(slot_id)
        if not os.path.exists(save_file):
            return None
        
        try:
            with open(save_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error al cargar: {e}")
            return None
    
    def delete_save(self, slot_id: int) -> bool:
        """
        Elimina un guardado y resetea los eventos asociados.
        
        Args:
            slot_id: ID del slot (1-indexed)
            
        Returns:
            True si se eliminó correctamente
        """
        if slot_id < 1 or slot_id > self.num_slots:
            return False
        
        save_file = self.get_save_file_path(slot_id)
        if os.path.exists(save_file):
            try:
                os.remove(save_file)
                self.slots[slot_id - 1].exists = False
                
                # Resetear eventos solo si estamos cargando/guardando en este slot
                # (esto se maneja desde game.py cuando se carga un nuevo save)
                return True
            except Exception:
                return False
        return False
    
    def refresh_slots(self) -> None:
        """Actualiza la información de todos los slots."""
        for slot in self.slots:
            save_file = self.get_save_file_path(slot.slot_id)
            slot.load_metadata(save_file)


# Instancia global del gestor de guardados
save_manager = SaveManager(num_slots=2)
