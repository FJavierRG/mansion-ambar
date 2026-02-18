#!/usr/bin/env python3
"""
Roguelike: En Busca del Amuleto de Yendor

Un roguelike clásico inspirado en Rogue, desarrollado con Python y Pygame.

Objetivo: Descender hasta el piso 10, derrotar al Dragón Anciano,
obtener el Amuleto de Yendor y escapar a la superficie.

Controles:
- Movimiento: Flechas, Numpad, o Vi-keys (hjklyubn)
- [ESPACIO] Interactuar (recoger, hablar, escaleras)
- [i] Inventario
- [.] Esperar turno
- [ESC] Pausa

Autor: Generado con IA
Versión: 1.0.0
"""

import sys
import os

# Asegurar que el directorio padre está en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roguelike.game import Game


def main() -> None:
    """Punto de entrada principal del juego."""
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\nJuego interrumpido.")
    except Exception as e:
        print(f"Error fatal: {e}")
        raise


if __name__ == "__main__":
    main()
