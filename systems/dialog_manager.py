"""
Gestor de diálogos del juego.
Maneja el estado actual de diálogos y textos interactivos.
Soporta cola de mensajes para mostrar textos secuenciales (bocadillos).
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Union
from collections import deque
from ..systems.text import DialogTree, DialogNode, DialogOption, TextContent, TextType

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..world.zone import Zone


class DialogManager:
    """
    Gestor de diálogos activos.
    
    Mantiene el estado del diálogo actual y maneja la navegación.
    Soporta cola de mensajes para mostrar textos secuenciales.
    
    Attributes:
        current_tree: Árbol de diálogo actual (None si no hay diálogo activo)
        current_node_id: ID del nodo actual
        selected_option: Índice de la opción seleccionada
        text_content: Contenido de texto simple actual (None si no hay texto)
        message_queue: Cola de mensajes pendientes (TextContent o DialogTree)
    """
    
    def __init__(self):
        """Inicializa el gestor de diálogos."""
        self.current_tree: Optional[DialogTree] = None
        self.current_node_id: Optional[str] = None
        self.selected_option: int = 0
        self.text_content: Optional[TextContent] = None
        self.text_type: Optional[TextType] = None
        # Cola de mensajes para mostrar secuencialmente
        self.message_queue: deque[Union[TextContent, DialogTree]] = deque()
        # Referencia al player para evaluar condiciones de opciones
        self._player: Optional[Player] = None
    
    def set_player(self, player: Player) -> None:
        """Establece la referencia al player para evaluar condiciones de opciones."""
        self._player = player
    
    def start_dialog(self, dialog_tree: DialogTree) -> bool:
        """
        Inicia un diálogo.
        
        Si el nodo inicial contiene "---", procesa los mensajes secuencialmente.
        
        Args:
            dialog_tree: Árbol de diálogo a iniciar
            
        Returns:
            True si se inició correctamente
        """
        if not dialog_tree or not dialog_tree.get_start_node():
            return False
        
        start_node = dialog_tree.get_start_node()
        if not start_node:
            return False
        
        # Verificar si el texto del nodo contiene "---" para mensajes encadenados
        if "---" in start_node.text:
            # Separar por "---" y crear múltiples mensajes
            messages = [msg.strip() for msg in start_node.text.split("---") if msg.strip()]
            if len(messages) > 1:
                # Crear nodos temporales para cada mensaje (sin opciones excepto el último)
                for i, msg in enumerate(messages[:-1]):
                    # Mensajes intermedios: solo opción "Continuar"
                    temp_node = DialogNode(
                        node_id=f"_temp_{i}",
                        speaker=start_node.speaker,
                        text=msg,
                        options=[DialogOption("Continuar", next_node=f"_temp_{i+1}")]
                    )
                    dialog_tree.add_node(temp_node)
                
                # Último mensaje: usar las opciones originales del nodo
                last_node = DialogNode(
                    node_id=f"_temp_{len(messages)-1}",
                    speaker=start_node.speaker,
                    text=messages[-1],
                    options=start_node.options
                )
                dialog_tree.add_node(last_node)
                
                # Cambiar el nodo inicial al primero temporal
                original_start = dialog_tree.start_node
                dialog_tree.start_node = "_temp_0"
                
                # Actualizar las referencias de next_node en las opciones del último nodo temporal
                for option in last_node.options:
                    if option.next_node == original_start:
                        # Si apuntaba al nodo original, mantener la referencia
                        pass
                    elif option.next_node:
                        # Mantener la referencia original
                        pass
        
        self.current_tree = dialog_tree
        self.current_node_id = dialog_tree.start_node
        self.selected_option = 0
        self.text_content = None
        self.text_type = TextType.DIALOG
        # Asegurar que selected_option apunta a una opción disponible
        self._ensure_selected_option_available()
        # Ejecutar on_enter del nodo inicial
        self._trigger_on_enter()
        return True
    
    def start_text(self, text_content: TextContent) -> None:
        """
        Muestra un texto simple.
        
        Args:
            text_content: Contenido de texto a mostrar
        """
        self.text_content = text_content
        self.current_tree = None
        self.current_node_id = None
        self.selected_option = 0
        self.text_type = TextType.SIMPLE
    
    def queue_text(self, text_content: TextContent) -> None:
        """
        Añade un texto a la cola de mensajes.
        
        Los mensajes en la cola se mostrarán automáticamente uno tras otro
        cuando el jugador cierre el mensaje actual.
        
        Args:
            text_content: Contenido de texto a encolar
        """
        self.message_queue.append(text_content)
    
    def queue_dialog(self, dialog_tree: DialogTree) -> None:
        """
        Añade un diálogo a la cola de mensajes.
        
        Args:
            dialog_tree: Árbol de diálogo a encolar
        """
        self.message_queue.append(dialog_tree)
    
    def queue_multiple_texts(self, texts: List[Union[str, TextContent]], titles: Optional[List[Optional[str]]] = None) -> None:
        """
        Añade múltiples textos a la cola de mensajes.
        
        Útil para crear secuencias de mensajes (bocadillos).
        
        Args:
            texts: Lista de textos (strings o TextContent)
            titles: Lista opcional de títulos (una por cada texto)
        
        Ejemplo:
            queue_multiple_texts([
                "Primer mensaje",
                "Segundo mensaje",
                "Tercer mensaje"
            ], titles=["Mensaje 1", "Mensaje 2", "Mensaje 3"])
        """
        if titles is None:
            titles = [None] * len(texts)
        
        for i, text in enumerate(texts):
            title = titles[i] if i < len(titles) else None
            
            if isinstance(text, TextContent):
                self.message_queue.append(text)
            else:
                content = TextContent.from_string(text, title=title, auto_close=False)
                self.message_queue.append(content)
    
    def process_queue(self) -> bool:
        """
        Procesa el siguiente elemento de la cola.
        
        Returns:
            True si había un mensaje en la cola y se procesó, False si la cola está vacía
        """
        if not self.message_queue:
            return False
        
        next_item = self.message_queue.popleft()
        
        if isinstance(next_item, DialogTree):
            return self.start_dialog(next_item)
        elif isinstance(next_item, TextContent):
            self.start_text(next_item)
            return True
        
        return False
    
    def get_current_node(self) -> Optional[DialogNode]:
        """
        Obtiene el nodo actual del diálogo.
        
        Returns:
            El nodo actual o None
        """
        if not self.current_tree or not self.current_node_id:
            return None
        return self.current_tree.get_node(self.current_node_id)
    
    def get_available_options(self) -> List[tuple]:
        """
        Obtiene las opciones disponibles del nodo actual, filtradas por condition.
        
        Returns:
            Lista de tuplas (índice_original, opción) para opciones disponibles
        """
        node = self.get_current_node()
        if not node or not node.options:
            return []
        result = []
        for i, opt in enumerate(node.options):
            if opt.condition is None or (self._player and opt.condition(self._player)):
                result.append((i, opt))
        return result
    
    def _ensure_selected_option_available(self) -> None:
        """Asegura que selected_option apunte a una opción disponible."""
        available = self.get_available_options()
        if not available:
            return
        # Si la opción actual no está entre las disponibles, seleccionar la primera
        available_indices = [i for i, _ in available]
        if self.selected_option not in available_indices:
            self.selected_option = available_indices[0]
    
    def select_next_option(self) -> None:
        """Selecciona la siguiente opción disponible."""
        available = self.get_available_options()
        if not available:
            return
        available_indices = [i for i, _ in available]
        try:
            current_pos = available_indices.index(self.selected_option)
        except ValueError:
            current_pos = -1
        next_pos = (current_pos + 1) % len(available_indices)
        self.selected_option = available_indices[next_pos]
    
    def select_previous_option(self) -> None:
        """Selecciona la opción anterior disponible."""
        available = self.get_available_options()
        if not available:
            return
        available_indices = [i for i, _ in available]
        try:
            current_pos = available_indices.index(self.selected_option)
        except ValueError:
            current_pos = 0
        prev_pos = (current_pos - 1) % len(available_indices)
        self.selected_option = available_indices[prev_pos]
    
    def select_option(self, player: Player, zone: Zone) -> bool:
        """
        Selecciona la opción actual y avanza el diálogo.
        
        Args:
            player: El jugador
            zone: La zona actual
            
        Returns:
            True si el diálogo continúa, False si se cierra
        """
        node = self.get_current_node()
        if not node or not node.options:
            return False
        
        if self.selected_option >= len(node.options):
            return False
        
        option = node.options[self.selected_option]
        
        # Verificar condición si existe (doble seguridad)
        if option.condition and not option.condition(player):
            return True  # Opción no disponible, no avanzar
        
        # Ejecutar acción si existe
        if option.action:
            option.action(player, zone)
        
        # Avanzar al siguiente nodo o cerrar
        if option.next_node:
            self.current_node_id = option.next_node
            self.selected_option = 0
            # Procesar "---" en el nuevo nodo si existe
            self._process_node_with_separators()
            # Asegurar que selected_option apunta a una opción disponible
            self._ensure_selected_option_available()
            # Ejecutar on_enter del nuevo nodo
            self._trigger_on_enter()
            return True
        else:
            self.close()
            return False
    
    def _process_node_with_separators(self) -> None:
        """
        Procesa el nodo actual si contiene "---" para crear mensajes encadenados.
        """
        if not self.current_tree or not self.current_node_id:
            return
        
        # No procesar nodos temporales (ya procesados)
        if self.current_node_id.startswith("_temp_"):
            return
        
        node = self.get_current_node()
        if not node or "---" not in node.text:
            return
        
        # Separar por "---" y crear múltiples mensajes
        messages = [msg.strip() for msg in node.text.split("---") if msg.strip()]
        if len(messages) <= 1:
            return  # No hay separadores o solo un mensaje
        
        # Crear nodos temporales para cada mensaje (sin opciones excepto el último)
        original_node_id = self.current_node_id
        temp_node_ids = []
        last_temp_id = f"_temp_{original_node_id}_last"
        
        for i, msg in enumerate(messages[:-1]):
            # Mensajes intermedios: solo opción "Continuar"
            temp_id = f"_temp_{original_node_id}_{i}"
            temp_node_ids.append(temp_id)
            
            # Calcular el siguiente nodo
            if i < len(messages) - 2:
                # Hay más mensajes, el siguiente es el siguiente temporal
                next_id = f"_temp_{original_node_id}_{i+1}"
            else:
                # Este es el penúltimo, el siguiente es el último
                next_id = last_temp_id
            
            temp_node = DialogNode(
                node_id=temp_id,
                speaker=node.speaker,
                text=msg,
                options=[DialogOption("Continuar", next_node=next_id)]
            )
            self.current_tree.add_node(temp_node)
        
        # Último mensaje: usar las opciones originales del nodo
        last_node = DialogNode(
            node_id=last_temp_id,
            speaker=node.speaker,
            text=messages[-1],
            options=node.options
        )
        self.current_tree.add_node(last_node)
        
        # Cambiar el nodo actual al primero temporal
        self.current_node_id = temp_node_ids[0] if temp_node_ids else last_temp_id
        self._ensure_selected_option_available()
    
    def close(self) -> bool:
        """
        Cierra el diálogo o texto actual y procesa la cola si hay mensajes pendientes.
        
        Returns:
            True si había un mensaje en la cola y se procesó, False si no hay más mensajes
        """
        self.current_tree = None
        self.current_node_id = None
        self.selected_option = 0
        self.text_content = None
        self.text_type = None
        
        # Procesar siguiente mensaje en la cola si existe
        return self.process_queue()
    
    def clear_queue(self) -> None:
        """Limpia la cola de mensajes pendientes."""
        self.message_queue.clear()
    
    def has_queued_messages(self) -> bool:
        """
        Verifica si hay mensajes en la cola.
        
        Returns:
            True si hay mensajes pendientes
        """
        return len(self.message_queue) > 0
    
    def is_active(self) -> bool:
        """
        Verifica si hay un diálogo o texto activo.
        
        Returns:
            True si hay un diálogo/texto activo
        """
        return self.current_tree is not None or self.text_content is not None
    
    def is_dialog(self) -> bool:
        """
        Verifica si el contenido actual es un diálogo.
        
        Returns:
            True si es un diálogo
        """
        return self.text_type == TextType.DIALOG
    
    def is_simple_text(self) -> bool:
        """
        Verifica si el contenido actual es texto simple.
        
        Returns:
            True si es texto simple
        """
        return self.text_type == TextType.SIMPLE
    
    def _trigger_on_enter(self) -> None:
        """Ejecuta el callback on_enter del nodo actual, si existe."""
        node = self.get_current_node()
        if node and node.on_enter:
            try:
                node.on_enter()
            except Exception as e:
                print(f"[DialogManager] Error en on_enter del nodo '{node.node_id}': {e}")


# Instancia global del gestor
dialog_manager = DialogManager()
