#!/usr/bin/env python3
"""
Diálogos de filtros avanzados para diferentes tipos de contenido
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


class AdvancedFilterDialog(Adw.Window):  # Cambiar a Window en lugar de Dialog
    """Diálogo de filtros avanzados"""
    
    def __init__(self, parent_window, current_view):
        super().__init__()
        self.parent_window = parent_window
        self.current_view = current_view
        
        # Configurar ventana
        self.set_title("Filtros Avanzados")
        self.set_default_size(450, 600)
        self.set_transient_for(parent_window)
        self.set_modal(True)
        
        # Crear contenido
        self.create_content()
        
    def create_content(self):
        """Crear contenido del diálogo"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Filtros Avanzados"))
        
        # Botón cancelar
        cancel_button = Gtk.Button.new_with_label("Cancelar")
        cancel_button.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_button)
        
        # Botón limpiar
        clear_button = Gtk.Button.new_with_label("Limpiar")
        clear_button.connect("clicked", self.on_clear_filters)
        header.pack_start(clear_button)
        
        # Botón aplicar
        apply_button = Gtk.Button.new_with_label("Aplicar")
        apply_button.add_css_class("suggested-action")
        apply_button.connect("clicked", self.on_apply_filters)
        header.pack_end(apply_button)
        
        main_box.append(header)
        
        # Contenido scrollable
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Banner informativo
        info_banner = Adw.Banner()
        info_banner.set_title(f"Configurar filtros para {self.current_view}")
        info_banner.set_revealed(True)
        content_box.append(info_banner)
        
        # Crear filtros según la vista actual
        if self.current_view == "comics":
            self.create_comic_filters(content_box)
        elif self.current_view == "volumes":
            self.create_volume_filters(content_box)
        elif self.current_view == "publishers":
            self.create_publisher_filters(content_box)
        else:
            self.create_generic_filters(content_box)
            
        scrolled.set_child(content_box)
        main_box.append(scrolled)
        self.set_content(main_box)
        
    def create_comic_filters(self, container):
        """Crear filtros para comics"""
        # Estado de clasificación
        status_group = Adw.PreferencesGroup()
        status_group.set_title("Estado de Clasificación")
        status_group.set_description("Filtrar por estado de catalogación")
        
        self.classification_combo = Adw.ComboRow()
        self.classification_combo.set_title("Clasificación")
        self.classification_combo.set_subtitle("Seleccionar estado de clasificación")
        classification_model = Gtk.StringList.new([
            "Todos los comics",
            "Solo clasificados",
            "Solo sin clasificar"
        ])
        self.classification_combo.set_model(classification_model)
        self.classification_combo.set_selected(0)
        status_group.add(self.classification_combo)
        
        # Calidad
        quality_group = Adw.PreferencesGroup()
        quality_group.set_title("Calidad del Archivo")
        quality_group.set_description("Filtrar por calidad (estrellas)")
        
        self.quality_min = Adw.SpinRow()
        self.quality_min.set_title("Calidad mínima")
        self.quality_min.set_subtitle("Valor mínimo de calidad")
        self.quality_min.set_range(0, 5)
        self.quality_min.set_value(0)
        quality_group.add(self.quality_min)
        
        self.quality_max = Adw.SpinRow()
        self.quality_max.set_title("Calidad máxima")
        self.quality_max.set_subtitle("Valor máximo de calidad")
        self.quality_max.set_range(0, 5)
        self.quality_max.set_value(5)
        quality_group.add(self.quality_max)
        
        # Estado de papelera
        trash_group = Adw.PreferencesGroup()
        trash_group.set_title("Estado del Archivo")
        
        self.include_trash = Adw.SwitchRow()
        self.include_trash.set_title("Incluir elementos en papelera")
        self.include_trash.set_subtitle("Mostrar comics marcados como eliminados")
        self.include_trash.set_active(False)
        trash_group.add(self.include_trash)
        
        container.append(status_group)
        container.append(quality_group)
        container.append(trash_group)
        
    def create_volume_filters(self, container):
        """Crear filtros para volúmenes"""
        # Año de publicación
        year_group = Adw.PreferencesGroup()
        year_group.set_title("Año de Publicación")
        year_group.set_description("Filtrar por rango de años")
        
        self.year_min = Adw.SpinRow()
        self.year_min.set_title("Año mínimo")
        self.year_min.set_subtitle("Año de inicio más temprano")
        self.year_min.set_range(1900, 2030)
        self.year_min.set_value(1900)
        year_group.add(self.year_min)
        
        self.year_max = Adw.SpinRow()
        self.year_max.set_title("Año máximo")
        self.year_max.set_subtitle("Año de inicio más reciente")
        self.year_max.set_range(1900, 2030)
        self.year_max.set_value(2030)
        year_group.add(self.year_max)
        
        # Cantidad de números
        count_group = Adw.PreferencesGroup()
        count_group.set_title("Cantidad de Números")
        count_group.set_description("Filtrar por cantidad de números publicados")
        
        self.count_min = Adw.SpinRow()
        self.count_min.set_title("Números mínimos")
        self.count_min.set_subtitle("Cantidad mínima de números")
        self.count_min.set_range(0, 1000)
        self.count_min.set_value(0)
        count_group.add(self.count_min)
        
        self.count_max = Adw.SpinRow()
        self.count_max.set_title("Números máximos")
        self.count_max.set_subtitle("Cantidad máxima de números")
        self.count_max.set_range(0, 1000)
        self.count_max.set_value(1000)
        count_group.add(self.count_max)
        
        # Completitud de la colección
        completion_group = Adw.PreferencesGroup()
        completion_group.set_title("Estado de Colección")
        completion_group.set_description("Filtrar por completitud de la colección")
        
        self.completion_combo = Adw.ComboRow()
        self.completion_combo.set_title("Estado de colección")
        self.completion_combo.set_subtitle("Nivel de completitud")
        completion_model = Gtk.StringList.new([
            "Todos los volúmenes",
            "Colección completa (100%)",
            "Mayoría completa (>75%)",
            "Parcialmente completa (25-75%)",
            "Pocos números (<25%)",
            "Sin comics (0%)"
        ])
        self.completion_combo.set_model(completion_model)
        self.completion_combo.set_selected(0)
        completion_group.add(self.completion_combo)
        
        # Filtro por editorial
        publisher_group = Adw.PreferencesGroup()
        publisher_group.set_title("Editorial")
        
        self.publisher_entry = Adw.EntryRow()
        self.publisher_entry.set_title("Filtrar por editorial")
        self.publisher_entry.set_text("")
        publisher_group.add(self.publisher_entry)
        
        container.append(year_group)
        container.append(count_group)
        container.append(completion_group)
        container.append(publisher_group)
        
    def create_publisher_filters(self, container):
        """Crear filtros para editoriales"""
        # Cantidad de volúmenes
        volume_group = Adw.PreferencesGroup()
        volume_group.set_title("Cantidad de Volúmenes")
        volume_group.set_description("Filtrar por cantidad de volúmenes publicados")
        
        self.volume_min = Adw.SpinRow()
        self.volume_min.set_title("Volúmenes mínimos")
        self.volume_min.set_subtitle("Cantidad mínima de volúmenes")
        self.volume_min.set_range(0, 1000)
        self.volume_min.set_value(0)
        volume_group.add(self.volume_min)
        
        self.volume_max = Adw.SpinRow()
        self.volume_max.set_title("Volúmenes máximos")
        self.volume_max.set_subtitle("Cantidad máxima de volúmenes")
        self.volume_max.set_range(0, 1000)
        self.volume_max.set_value(1000)
        volume_group.add(self.volume_max)
        
        # Información disponible
        info_group = Adw.PreferencesGroup()
        info_group.set_title("Información Disponible")
        
        self.has_description = Adw.SwitchRow()
        self.has_description.set_title("Con descripción")
        self.has_description.set_subtitle("Solo editoriales con descripción")
        self.has_description.set_active(False)
        info_group.add(self.has_description)
        
        self.has_logo = Adw.SwitchRow()
        self.has_logo.set_title("Con logo")
        self.has_logo.set_subtitle("Solo editoriales con logo")
        self.has_logo.set_active(False)
        info_group.add(self.has_logo)
        
        self.has_website = Adw.SwitchRow()
        self.has_website.set_title("Con sitio web")
        self.has_website.set_subtitle("Solo editoriales con sitio web")
        self.has_website.set_active(False)
        info_group.add(self.has_website)
        
        container.append(volume_group)
        container.append(info_group)
        
    def create_generic_filters(self, container):
        """Crear filtros genéricos para otros tipos de contenido"""
        generic_group = Adw.PreferencesGroup()
        generic_group.set_title("Filtros Básicos")
        generic_group.set_description("Filtros disponibles para este tipo de contenido")
        
        info_label = Gtk.Label()
        info_label.set_markup("<i>Los filtros específicos para este tipo de contenido\nse implementarán próximamente.</i>")
        info_label.set_justify(Gtk.Justification.CENTER)
        info_label.add_css_class("dim-label")
        
        generic_group.add(info_label)
        container.append(generic_group)
        
    def on_apply_filters(self, button):
        """Aplicar filtros configurados"""
        filters = {}
        
        try:
            if self.current_view == "comics":
                # Filtros de comics
                classification = self.classification_combo.get_selected()
                if classification == 1:
                    filters['classification'] = True
                elif classification == 2:
                    filters['classification'] = False
                    
                min_quality = int(self.quality_min.get_value())
                max_quality = int(self.quality_max.get_value())
                if min_quality > 0 or max_quality < 5:
                    filters['quality_range'] = (min_quality, max_quality)
                    
                if not self.include_trash.get_active():
                    filters['exclude_trash'] = True
                    
            elif self.current_view == "volumes":
                # Filtros de volúmenes
                min_year = int(self.year_min.get_value())
                max_year = int(self.year_max.get_value())
                if min_year > 1900 or max_year < 2030:
                    filters['year_range'] = (min_year, max_year)
                    
                min_count = int(self.count_min.get_value())
                max_count = int(self.count_max.get_value())
                if min_count > 0 or max_count < 1000:
                    filters['count_range'] = (min_count, max_count)
                    
                completion = self.completion_combo.get_selected()
                if completion > 0:
                    filters['completion'] = completion
                    
                publisher_filter = self.publisher_entry.get_text().strip()
                if publisher_filter:
                    filters['publisher_name'] = publisher_filter
                    
            elif self.current_view == "publishers":
                # Filtros de editoriales
                min_volumes = int(self.volume_min.get_value())
                max_volumes = int(self.volume_max.get_value())
                if min_volumes > 0 or max_volumes < 1000:
                    filters['volume_range'] = (min_volumes, max_volumes)
                    
                if self.has_description.get_active():
                    filters['has_description'] = True
                if self.has_logo.get_active():
                    filters['has_logo'] = True
                if self.has_website.get_active():
                    filters['has_website'] = True
            
            # Aplicar filtros en la ventana principal
            if hasattr(self.parent_window, 'apply_advanced_filters'):
                self.parent_window.apply_advanced_filters(filters)
                print(f"✓ Filtros aplicados para {self.current_view}: {filters}")
            
            self.close()
            
        except Exception as e:
            print(f"Error aplicando filtros: {e}")
            
            # Mostrar mensaje de error
            toast = Adw.Toast()
            toast.set_title(f"Error aplicando filtros: {e}")
            toast.set_timeout(3)
            
            # Si tenemos acceso al toast overlay de la ventana principal
            if hasattr(self.parent_window, 'toast_overlay'):
                self.parent_window.toast_overlay.add_toast(toast)
        
    def on_clear_filters(self, button):
        """Limpiar todos los filtros"""
        try:
            if self.current_view == "comics":
                self.classification_combo.set_selected(0)
                self.quality_min.set_value(0)
                self.quality_max.set_value(5)
                self.include_trash.set_active(False)
                
            elif self.current_view == "volumes":
                self.year_min.set_value(1900)
                self.year_max.set_value(2030)
                self.count_min.set_value(0)
                self.count_max.set_value(1000)
                self.completion_combo.set_selected(0)
                self.publisher_entry.set_text("")
                
            elif self.current_view == "publishers":
                self.volume_min.set_value(0)
                self.volume_max.set_value(1000)
                self.has_description.set_active(False)
                self.has_logo.set_active(False)
                self.has_website.set_active(False)
                
            print("✓ Filtros limpiados")
            
        except Exception as e:
            print(f"Error limpiando filtros: {e}")


class QuickFilterBar(Gtk.Box):
    """Barra de filtros rápidos integrada"""
    
    def __init__(self, on_filter_changed_callback):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.on_filter_changed = on_filter_changed_callback
        
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        
        # Crear filtros rápidos
        self.create_quick_filters()
        
    def create_quick_filters(self):
        """Crear controles de filtros rápidos"""
        # Label
        filter_label = Gtk.Label(label="Filtros rápidos:")
        filter_label.add_css_class("dim-label")
        self.append(filter_label)
        
        # Botón "Solo clasificados" para comics
        self.classified_button = Gtk.ToggleButton()
        self.classified_button.set_label("Clasificados")
        self.classified_button.set_tooltip_text("Mostrar solo comics clasificados")
        self.classified_button.connect("toggled", self.on_quick_filter_toggled, "classified")
        self.append(self.classified_button)
        
        # Botón "Calidad alta" para comics
        self.quality_button = Gtk.ToggleButton()
        self.quality_button.set_label("Alta calidad")
        self.quality_button.set_tooltip_text("Mostrar solo comics con calidad 4-5 estrellas")
        self.quality_button.connect("toggled", self.on_quick_filter_toggled, "quality")
        self.append(self.quality_button)
        
        # Botón "Completos" para volúmenes
        self.complete_button = Gtk.ToggleButton()
        self.complete_button.set_label("Completos")
        self.complete_button.set_tooltip_text("Mostrar solo volúmenes completos")
        self.complete_button.connect("toggled", self.on_quick_filter_toggled, "complete")
        self.append(self.complete_button)
        
        # Separador
        separator = Gtk.Separator()
        separator.set_orientation(Gtk.Orientation.VERTICAL)
        self.append(separator)
        
        # Botón limpiar filtros
        clear_button = Gtk.Button()
        clear_button.set_label("Limpiar")
        clear_button.set_tooltip_text("Limpiar todos los filtros")
        clear_button.connect("clicked", self.on_clear_all_filters)
        self.append(clear_button)
        
    def on_quick_filter_toggled(self, button, filter_type):
        """Manejar toggle de filtros rápidos"""
        is_active = button.get_active()
        self.on_filter_changed(filter_type, is_active)
        
    def on_clear_all_filters(self, button):
        """Limpiar todos los filtros rápidos"""
        self.classified_button.set_active(False)
        self.quality_button.set_active(False)
        self.complete_button.set_active(False)
        
        self.on_filter_changed("clear_all", True)
        
    def update_for_view(self, view_type):
        """Actualizar filtros disponibles según la vista"""
        # Mostrar/ocultar botones según la vista
        if view_type == "comics":
            self.classified_button.set_visible(True)
            self.quality_button.set_visible(True)
            self.complete_button.set_visible(False)
        elif view_type == "volumes":
            self.classified_button.set_visible(False)
            self.quality_button.set_visible(False)
            self.complete_button.set_visible(True)
        else:
            self.classified_button.set_visible(False)
            self.quality_button.set_visible(False)
            self.complete_button.set_visible(False)