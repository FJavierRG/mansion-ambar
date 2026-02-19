"""
Sistema de UI para diálogos y textos.
Muestra diálogos interactivos y textos simples en pantalla.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List
import pygame

from ..config import WINDOW_WIDTH, WINDOW_HEIGHT, COLORS, FONT_NAME, FONT_SIZE
from ..systems.text import DialogNode, TextContent

if TYPE_CHECKING:
    from ..entities.player import Player


class DialogRenderer:
    """
    Renderizador de diálogos y textos.
    
    Muestra diálogos con opciones y textos simples en pantalla.
    """
    
    def __init__(self):
        """Inicializa el renderizador de diálogos."""
        self.font: Optional[pygame.font.Font] = None
        self.font_bold: Optional[pygame.font.Font] = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Asegura que las fuentes estén inicializadas."""
        if self._initialized:
            return
        
        # Asegurar que pygame esté inicializado
        if not pygame.get_init():
            pygame.init()
        
        try:
            self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
            self.font_bold = pygame.font.SysFont(FONT_NAME, FONT_SIZE, bold=True)
        except:
            try:
                self.font = pygame.font.Font(None, FONT_SIZE)
                self.font_bold = pygame.font.Font(None, FONT_SIZE)
            except:
                # Fallback absoluto
                pygame.font.init()
                self.font = pygame.font.Font(None, FONT_SIZE)
                self.font_bold = pygame.font.Font(None, FONT_SIZE)
        
        self._initialized = True
    
    def render_dialog(
        self,
        screen: pygame.Surface,
        node: DialogNode,
        selected_option: int = 0
    ) -> None:
        """
        Renderiza un diálogo con opciones.
        
        Args:
            screen: Superficie de pygame donde renderizar
            node: Nodo del diálogo a mostrar
            selected_option: Índice de la opción seleccionada
        """
        self._ensure_initialized()
        # Dimensiones del cuadro de diálogo (más pequeño, en la parte inferior)
        dialog_width = min(1000, WINDOW_WIDTH - 40)
        dialog_height = min(200, WINDOW_HEIGHT // 3)
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = WINDOW_HEIGHT - dialog_height - 20  # 20 píxeles desde abajo
        
        # Fondo semitransparente oscuro
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(COLORS["black"])
        screen.blit(overlay, (0, 0))
        
        # Cuadro de diálogo
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(screen, COLORS["darker_gray"], dialog_rect)
        pygame.draw.rect(screen, COLORS["white"], dialog_rect, 2)
        
        # Padding interno
        padding = 20
        text_x = dialog_x + padding
        text_y = dialog_y + padding
        max_text_width = dialog_width - (padding * 2)
        
        # Nombre del hablante (si existe)
        if node.speaker:
            speaker_surface = self.font_bold.render(f"{node.speaker}:", True, COLORS["white"])
            screen.blit(speaker_surface, (text_x, text_y))
            text_y += FONT_SIZE + 10
        
        # Texto del diálogo (puede ser multilínea)
        dialog_lines = self._wrap_text(node.text, max_text_width)
        for line in dialog_lines:
            text_surface = self.font.render(line, True, COLORS["message"])
            screen.blit(text_surface, (text_x, text_y))
            text_y += FONT_SIZE + 5
        
        # Opciones (solo las disponibles según sus condiciones)
        if node.options:
            from ..systems.dialog_manager import dialog_manager
            available = dialog_manager.get_available_options()
            
            if available:
                text_y += 10  # Espacio antes de las opciones
                
                for orig_idx, option in available:
                    option_text = option.text
                    option_color = COLORS["white"] if orig_idx == selected_option else COLORS["gray"]
                    
                    # Marcar opción seleccionada
                    prefix = "> " if orig_idx == selected_option else "  "
                    option_line = f"{prefix}{option_text}"
                    
                    option_surface = self.font.render(option_line, True, option_color)
                    screen.blit(option_surface, (text_x + 10, text_y))
                    text_y += FONT_SIZE + 5
        
        # Instrucciones
        if node.options:
            instruction_y = dialog_y + dialog_height - 30
            instruction = "↑↓ para navegar, ESPACIO para seleccionar, ESC para cerrar"
            instruction_surface = self.font.render(instruction, True, COLORS["dark_gray"])
            screen.blit(instruction_surface, (text_x, instruction_y))
    
    def render_simple_text(
        self,
        screen: pygame.Surface,
        content: TextContent
    ) -> None:
        """
        Renderiza un texto simple.
        
        Args:
            screen: Superficie de pygame donde renderizar
            content: Contenido de texto a mostrar
        """
        self._ensure_initialized()
        # Dimensiones del cuadro de texto (más pequeño, en la parte inferior)
        dialog_width = min(1000, WINDOW_WIDTH - 40)
        dialog_height = min(200, WINDOW_HEIGHT // 3)
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = WINDOW_HEIGHT - dialog_height - 20  # 20 píxeles desde abajo
        
        # Fondo semitransparente oscuro
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(COLORS["black"])
        screen.blit(overlay, (0, 0))
        
        # Cuadro de texto
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(screen, COLORS["darker_gray"], dialog_rect)
        pygame.draw.rect(screen, COLORS["white"], dialog_rect, 2)
        
        # Padding interno
        padding = 20
        text_x = dialog_x + padding
        text_y = dialog_y + padding
        max_text_width = dialog_width - (padding * 2)
        
        # Título (si existe)
        if content.title:
            title_surface = self.font_bold.render(content.title, True, COLORS["white"])
            screen.blit(title_surface, (text_x, text_y))
            text_y += FONT_SIZE + 15
        
        # Líneas de texto
        for line in content.lines:
            wrapped_lines = self._wrap_text(line, max_text_width)
            for wrapped_line in wrapped_lines:
                text_surface = self.font.render(wrapped_line, True, COLORS["message"])
                screen.blit(text_surface, (text_x, text_y))
                text_y += FONT_SIZE + 5
        
        # Instrucciones
        instruction_y = dialog_y + dialog_height - 30
        instruction = "Presiona ESPACIO o ESC para continuar"
        instruction_surface = self.font.render(instruction, True, COLORS["dark_gray"])
        screen.blit(instruction_surface, (text_x, instruction_y))
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """
        Envuelve texto en múltiples líneas según el ancho máximo.
        Respeta los saltos de línea explícitos (\n).
        
        Args:
            text: Texto a envolver
            max_width: Ancho máximo en píxeles
            
        Returns:
            Lista de líneas de texto
        """
        self._ensure_initialized()
        # Primero dividir por saltos de línea explícitos
        paragraphs = text.split('\n')
        all_lines = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                # Línea vacía, añadirla
                all_lines.append("")
                continue
            
            # Envolver cada párrafo
            words = paragraph.split(' ')
            current_line = []
            current_width = 0
            
            for word in words:
                word_surface = self.font.render(word, True, COLORS["message"])
                word_width = word_surface.get_width()
                space_width = self.font.size(' ')[0]
                
                if current_width + word_width + (len(current_line) * space_width) <= max_width:
                    current_line.append(word)
                    current_width += word_width
                else:
                    if current_line:
                        all_lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = word_width
            
            if current_line:
                all_lines.append(' '.join(current_line))
        
        return all_lines if all_lines else [text]


# Instancia global del renderizador
dialog_renderer = DialogRenderer()
