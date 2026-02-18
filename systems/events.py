"""
Sistema de eventos persistentes y logros del juego.
Permite crear eventos que afectan el estado del juego entre partidas.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..world.zone import Zone


class EventStatus(Enum):
    """Estado de un evento."""
    LOCKED = "locked"      # Evento bloqueado (no se puede activar)
    AVAILABLE = "available"  # Evento disponible (condiciones cumplidas)
    TRIGGERED = "triggered"  # Evento activado
    COMPLETED = "completed"  # Evento completado


@dataclass
class EventCondition:
    """
    Condición para activar un evento.
    
    Attributes:
        check_func: Función que verifica si la condición se cumple
        description: Descripción de la condición (para debug)
    """
    check_func: Callable[[Player, Zone], bool]
    description: str = ""


@dataclass
class EventAction:
    """
    Acción que se ejecuta cuando un evento se activa.
    
    Attributes:
        action_func: Función que ejecuta la acción
        description: Descripción de la acción (para debug)
    """
    action_func: Callable[[Player, Zone], None]
    description: str = ""


@dataclass
class GameEvent:
    """
    Evento del juego que puede afectar el estado persistente.
    
    Attributes:
        event_id: Identificador único del evento
        name: Nombre del evento
        description: Descripción del evento
        status: Estado actual del evento
        conditions: Lista de condiciones que deben cumplirse
        actions: Lista de acciones a ejecutar cuando se activa
        persistent: Si el evento persiste entre partidas
        auto_trigger: Si se activa automáticamente cuando se cumplen condiciones
    """
    event_id: str
    name: str
    description: str = ""
    status: EventStatus = EventStatus.LOCKED
    conditions: List[EventCondition] = field(default_factory=list)
    actions: List[EventAction] = field(default_factory=list)
    persistent: bool = True
    auto_trigger: bool = False
    
    def check_conditions(self, player: Player, zone: Zone) -> bool:
        """
        Verifica si todas las condiciones se cumplen.
        
        Args:
            player: El jugador
            zone: La zona actual
            
        Returns:
            True si todas las condiciones se cumplen
        """
        return all(condition.check_func(player, zone) for condition in self.conditions)
    
    def execute_actions(self, player: Player, zone: Zone) -> None:
        """
        Ejecuta todas las acciones del evento.
        
        Args:
            player: El jugador
            zone: La zona actual
        """
        for action in self.actions:
            action.action_func(player, zone)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el evento a diccionario."""
        return {
            "event_id": self.event_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "persistent": self.persistent,
            "auto_trigger": self.auto_trigger,
            # Nota: conditions y actions no se serializan (son funciones)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GameEvent:
        """Crea un evento desde un diccionario."""
        event = cls(
            event_id=data["event_id"],
            name=data["name"],
            description=data.get("description", ""),
            status=EventStatus(data["status"]),
            persistent=data.get("persistent", True),
            auto_trigger=data.get("auto_trigger", False)
        )
        return event


class EventManager:
    """
    Gestor de eventos del juego.
    
    Maneja todos los eventos persistentes, verifica condiciones y ejecuta acciones.
    Los eventos ahora se guardan en el save, no en archivos globales.
    
    Attributes:
        events: Diccionario de eventos por ID
        triggered_events: Conjunto de IDs de eventos activados
    """
    
    def __init__(self):
        """
        Inicializa el gestor de eventos.
        Los eventos se cargan desde el save, no desde archivos globales.
        """
        self.events: Dict[str, GameEvent] = {}
        self.triggered_events: Set[str] = set()
        # Contador de runs completadas (muerte, escapar, etc.)
        self.run_count: int = 0
        # Almacén de datos clave-valor persistente (para guardar datos
        # numéricos o strings asociados a eventos, como el run_count
        # en el que se completó un estado)
        self.event_data: Dict[str, Any] = {}
    
    def register_event(self, event: GameEvent) -> None:
        """
        Registra un evento en el sistema.
        
        Args:
            event: Evento a registrar
        """
        self.events[event.event_id] = event
        
        # Si el evento ya fue activado antes, restaurar su estado
        if event.event_id in self.triggered_events:
            event.status = EventStatus.TRIGGERED
    
    def trigger_event(self, event_id: str, player: Player, zone: Zone, skip_conditions: bool = False) -> bool:
        """
        Activa un evento manualmente.
        
        Args:
            event_id: ID del evento a activar
            player: El jugador
            zone: La zona actual
            skip_conditions: Si es True, salta la verificación de condiciones
            
        Returns:
            True si el evento se activó correctamente
        """
        if event_id not in self.events:
            return False
        
        event = self.events[event_id]
        
        # Verificar condiciones (a menos que se indique lo contrario)
        if not skip_conditions and not event.check_conditions(player, zone):
            return False
        
        # Ejecutar acciones
        event.execute_actions(player, zone)
        
        # Marcar como activado
        event.status = EventStatus.TRIGGERED
        self.triggered_events.add(event_id)
        
        # Nota: El guardado de eventos ahora se hace desde save_manager
        # No guardamos automáticamente aquí para evitar archivos globales
        
        return True
    
    def check_and_trigger_events(self, player: Player, zone: Zone) -> List[str]:
        """
        Verifica condiciones y activa eventos automáticamente si corresponde.
        
        Args:
            player: El jugador
            zone: La zona actual
            
        Returns:
            Lista de IDs de eventos activados
        """
        triggered = []
        
        for event in self.events.values():
            # Solo verificar eventos disponibles o bloqueados (no los ya activados)
            if event.status in [EventStatus.TRIGGERED, EventStatus.COMPLETED]:
                continue
            
            # Verificar condiciones
            if event.check_conditions(player, zone):
                if event.status == EventStatus.LOCKED:
                    event.status = EventStatus.AVAILABLE
                
                # Activar automáticamente si corresponde
                if event.auto_trigger and event.status == EventStatus.AVAILABLE:
                    if self.trigger_event(event.event_id, player, zone):
                        triggered.append(event.event_id)
        
        return triggered
    
    def complete_run(self) -> None:
        """
        Marca una run como completada. Incrementa el contador de runs.
        
        Llamar cuando el jugador muere y respawnea, escapa de la mazmorra,
        o cualquier otra forma de terminar una run.
        """
        self.run_count += 1
    
    def get_run_count(self) -> int:
        """Retorna el número de runs completadas."""
        return self.run_count
    
    def set_data(self, key: str, value: Any) -> None:
        """
        Guarda un dato arbitrario persistente.
        
        Útil para almacenar información asociada a eventos, como
        el run_count en el que se completó un estado de NPC.
        
        Args:
            key: Clave del dato
            value: Valor a guardar (debe ser serializable)
        """
        self.event_data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un dato arbitrario persistente.
        
        Args:
            key: Clave del dato
            default: Valor por defecto si no existe
            
        Returns:
            El valor almacenado o el default
        """
        return self.event_data.get(key, default)
    
    def is_event_triggered(self, event_id: str) -> bool:
        """
        Verifica si un evento ha sido activado.
        
        Args:
            event_id: ID del evento
            
        Returns:
            True si el evento está activado
        """
        return event_id in self.triggered_events
    
    def get_event_status(self, event_id: str) -> Optional[EventStatus]:
        """
        Obtiene el estado de un evento.
        
        Args:
            event_id: ID del evento
            
        Returns:
            Estado del evento o None si no existe
        """
        if event_id not in self.events:
            return None
        return self.events[event_id].status
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el estado de los eventos a diccionario.
        Se guarda en el save, no en archivos globales.
        
        Returns:
            Diccionario con el estado de los eventos
        """
        return {
                "triggered_events": list(self.triggered_events),
                "events_status": {
                    event_id: event.status.value
                    for event_id, event in self.events.items()
                    if event.persistent
                },
                "run_count": self.run_count,
                "event_data": self.event_data,
            }
            
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Carga el estado de los eventos desde un diccionario.
        Se carga desde el save, no desde archivos globales.
        
        Args:
            data: Diccionario con el estado de los eventos
        """
        if not data:
            return
        
        self.triggered_events = set(data.get("triggered_events", []))
        self.run_count = data.get("run_count", 0)
        self.event_data = data.get("event_data", {})
        
        # Restaurar estados de eventos persistentes
        events_status = data.get("events_status", {})
        for event_id, status_value in events_status.items():
            if event_id in self.events:
                self.events[event_id].status = EventStatus(status_value)
    
    def clear_all(self) -> None:
        """
        Limpia todos los eventos.
        Útil cuando se borra un save o se inicia una nueva partida.
        """
        self.triggered_events.clear()
        self.run_count = 0
        self.event_data.clear()
        for event in self.events.values():
            event.status = EventStatus.LOCKED


# Instancia global del gestor de eventos
event_manager = EventManager()
