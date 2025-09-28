#!/usr/bin/env python3
"""
selectable_card.py - Wrapper para cards con capacidad de selección múltiple
"""

import gi
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, GObject, Gdk


class SelectableCard(Gtk.Box):
    """
    Wrapper que añade capacidad de selección múltiple a cualquier card.
    
    Envuelve una card existente y añade:
    - Checkbox de selección (mostrable/ocultable)
    - Eventos de click izquierdo/derecho
    - Estados visuales de selección
    - Señales para comunicar cambios
    """
    
    __gsignals__ = {
        'selection-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        'item-activated': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, original_card, item_id, item_type):
        """
        Args:
            original_card: Card original (ComicCard, VolumeCard, etc.)
            item_id: ID único del item
            item_type: Tipo de item ("comics", "volumes", "publishers")
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.original_card = original_card
        self.item_id = item_id
        self.item_type = item_type
        self._selected = False
        self._selection_mode = False
        
        # Crear overlay para superponer controles
        self.overlay = Gtk.Overlay()
        
        # Agregar la card original como base
        self.overlay.set_child(original_card)
        
        # Crear checkbox de selección
        self._create_selection_checkbox()
        
        # Configurar eventos de mouse
        self._setup_mouse_events()
        
        # Agregar overlay al contenedor principal
        self.append(self.overlay)
        
    def _create_selection_checkbox(self):
        """Crear checkbox de selección en la esquina superior derecha"""
        self.selection_check = Gtk.CheckButton()
        self.selection_check.set_halign(Gtk.Align.END)
        self.selection_check.set_valign(Gtk.Align.START)
        self.selection_check.set_margin_top(8)
        self.selection_check.set_margin_end(8)
        self.selection_check.add_css_class("selection-checkbox")
        
        # Conectar evento de cambio
        self.selection_check.connect("toggled", self._on_selection_toggled)
        
        # Inicialmente oculto
        self.selection_check.set_visible(False)
        
        # Añadir como overlay
        self.overlay.add_overlay(self.selection_check)
        
    def _setup_mouse_events(self):
        """Configurar eventos de mouse para la card"""
        # Gesture para click derecho (menú contextual)
        right_click = Gtk.GestureClick()
        right_click.set_button(Gdk.BUTTON_SECONDARY)
        right_click.connect("pressed", self._on_right_click)
        self.overlay.add_controller(right_click)
        
        # Gesture para click izquierdo (selección)
        left_click = Gtk.GestureClick()
        left_click.set_button(Gdk.BUTTON_PRIMARY)
        left_click.connect("pressed", self._on_left_click)
        self.overlay.add_controller(left_click)
        
    @property
    def selected(self):
        """Estado de selección actual"""
        return self._selected
        
    def set_selected(self, selected):
        """
        Cambiar estado de selección
        
        Args:
            selected (bool): Nuevo estado de selección
        """
        if self._selected != selected:
            self._selected = selected
            self.selection_check.set_active(selected)
            self._update_visual_state()
            self.emit('selection-changed', selected)
    
    def set_selection_mode(self, enabled):
        """
        Activar/desactivar modo de selección
        
        Args:
            enabled (bool): Si True, muestra controles de selección
        """
        self._selection_mode = enabled
        self.selection_check.set_visible(enabled)
        
        # Si se desactiva el modo, deseleccionar
        if not enabled:
            self.set_selected(False)
            
    def _on_selection_toggled(self, checkbox):
        """Manejar cambio en checkbox de selección"""
        self.set_selected(checkbox.get_active())
        
    def _on_left_click(self, gesture, n_press, x, y):
        """Manejar click izquierdo"""
        # Doble click - abrir detalle
        if n_press == 2 and not self._selection_mode:
            self.emit('item-activated')
            return True  # Consumir el evento

        # Solo procesar si estamos en modo selección
        if self._selection_mode:
            self.set_selected(not self.selected)
            return True  # Consumir el evento

        # Si no estamos en modo selección, dejar que la card original lo maneje
        return False
        
    def _on_right_click(self, gesture, n_press, x, y):
        """Manejar click derecho - mostrar menú contextual"""
        # Buscar la ventana principal para mostrar el popover
        parent_window = self.get_root()
        if hasattr(parent_window, 'show_item_popover'):
            parent_window.show_item_popover(self, self.item_id, self.item_type, x, y)
            return True
            
        return False
            
    def _update_visual_state(self):
        """Actualizar apariencia visual según estado de selección"""
        if self._selected:
            self.add_css_class("selected-item")
        else:
            self.remove_css_class("selected-item")
            
    def get_original_card(self):
        """Obtener referencia a la card original"""
        return self.original_card
        
    def get_item_data(self):
        """Obtener datos del item (ID y tipo)"""
        return {
            'id': self.item_id,
            'type': self.item_type,
            'item': getattr(self.original_card, 'item', None)
        }


class SelectionManager:
    """
    Gestor centralizado para el modo de selección múltiple.
    
    Maneja el estado global de selección y coordina múltiples SelectableCards.
    """
    
    def __init__(self):
        self.selection_mode = False
        self.selected_items = set()
        self.selectable_cards = []
        self.callbacks = {
            'selection_changed': [],
            'mode_changed': []
        }
        
    def add_card(self, selectable_card):
        """Agregar una card al gestor"""
        if selectable_card not in self.selectable_cards:
            self.selectable_cards.append(selectable_card)
            selectable_card.connect('selection-changed', self._on_card_selection_changed)
            selectable_card.set_selection_mode(self.selection_mode)
            
    def remove_card(self, selectable_card):
        """Quitar una card del gestor"""
        if selectable_card in self.selectable_cards:
            self.selectable_cards.remove(selectable_card)
            self.selected_items.discard(selectable_card.item_id)
            
    def clear_cards(self):
        """Limpiar todas las cards"""
        self.selectable_cards.clear()
        self.selected_items.clear()
        
    def set_selection_mode(self, enabled):
        """Cambiar modo de selección global"""
        if self.selection_mode != enabled:
            self.selection_mode = enabled
            
            # Actualizar todas las cards
            for card in self.selectable_cards:
                card.set_selection_mode(enabled)
                
            # Si se desactiva, limpiar selección
            if not enabled:
                self.clear_selection()
                
            # Notificar cambio de modo
            self._notify_callbacks('mode_changed', enabled)
            
    def clear_selection(self):
        """Limpiar toda la selección"""
        for card in self.selectable_cards:
            card.set_selected(False)
        self.selected_items.clear()
        self._notify_callbacks('selection_changed', set())
        
    def select_all(self, visible_only=True):
        """Seleccionar todas las cards"""
        for card in self.selectable_cards:
            if not visible_only or card.get_visible():
                card.set_selected(True)
                
    def get_selected_items(self):
        """Obtener set de IDs seleccionados"""
        return self.selected_items.copy()
        
    def get_selected_cards(self):
        """Obtener lista de cards seleccionadas"""
        return [card for card in self.selectable_cards if card.selected]
        
    def get_selection_count(self):
        """Obtener cantidad de items seleccionados"""
        return len(self.selected_items)
        
    def add_callback(self, event_type, callback):
        """
        Agregar callback para eventos
        
        Args:
            event_type: 'selection_changed' o 'mode_changed'
            callback: Función a llamar
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            
    def remove_callback(self, event_type, callback):
        """Quitar callback"""
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
            
    def _on_card_selection_changed(self, card, selected):
        """Manejar cambio de selección en una card"""
        if selected:
            self.selected_items.add(card.item_id)
        else:
            self.selected_items.discard(card.item_id)
            
        # Notificar cambio
        self._notify_callbacks('selection_changed', self.selected_items.copy())
        
    def _notify_callbacks(self, event_type, data):
        """Notificar a callbacks registrados"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error en callback {event_type}: {e}")
                    
    def get_stats(self):
        """Obtener estadísticas de selección"""
        return {
            'total_cards': len(self.selectable_cards),
            'selected_count': len(self.selected_items),
            'selection_mode': self.selection_mode,
            'visible_cards': len([c for c in self.selectable_cards if c.get_visible()])
        }


# Funciones de utilidad
def create_selectable_card(original_card, item_id, item_type):
    """
    Factory function para crear SelectableCard
    
    Args:
        original_card: Card base a envolver
        item_id: ID del item
        item_type: Tipo de item
        
    Returns:
        SelectableCard configurada
    """
    return SelectableCard(original_card, item_id, item_type)


def batch_create_selectable_cards(cards_data, card_factory):
    """
    Crear múltiples SelectableCards en lote
    
    Args:
        cards_data: Lista de (item, item_id, item_type)
        card_factory: Función para crear card original
        
    Returns:
        Lista de SelectableCards
    """
    selectable_cards = []
    
    for item, item_id, item_type in cards_data:
        try:
            original_card = card_factory(item)
            selectable_card = SelectableCard(original_card, item_id, item_type)
            selectable_cards.append(selectable_card)
        except Exception as e:
            print(f"Error creando card seleccionable para {item_id}: {e}")
            
    return selectable_cards


if __name__ == "__main__":
    # Test básico del módulo
    print("Probando SelectableCard y SelectionManager...")
    
    # Crear un manager
    manager = SelectionManager()
    
    # Simular algunas cards (normalmente vendrían de comic_cards.py)
    class MockCard(Gtk.Box):
        def __init__(self, name):
            super().__init__()
            self.name = name
            
    # Crear cards seleccionables
    for i in range(3):
        mock_card = MockCard(f"Card {i}")
        selectable_card = SelectableCard(mock_card, i, "comics")
        manager.add_card(selectable_card)
        
    print(f"Stats iniciales: {manager.get_stats()}")
    
    # Activar modo selección
    manager.set_selection_mode(True)
    print(f"Modo selección activado")
    
    # Simular selecciones
    manager.selectable_cards[0].set_selected(True)
    manager.selectable_cards[2].set_selected(True)
    
    print(f"Items seleccionados: {manager.get_selected_items()}")
    print(f"Stats finales: {manager.get_stats()}")