#!/usr/bin/env python3
"""
Diálogos de filtros avanzados para diferentes tipos de contenido
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject


class AdvancedFilterDialog(Adw.Window):  # Cambiar a Window en lugar de Dialog
    """Diálogo de filtros avanzados"""

    __gsignals__ = {
        'filters-applied': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    
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

        # Configurar shortcuts de teclado
        self.setup_keyboard_shortcuts()

        # Cargar estado de filtros actual
        self.load_current_filters()
        
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
                    
                if self.include_trash.get_active():
                    filters['include_trash'] = True
                else:
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
            
            # Emitir señal con los filtros
            self.emit('filters-applied', filters)
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

            # Limpiar filtros en la ventana principal también
            if hasattr(self.parent_window, 'apply_advanced_filters'):
                self.parent_window.apply_advanced_filters({})
                print("✓ Filtros limpiados en la ventana principal")

            print("✓ Filtros limpiados")

        except Exception as e:
            print(f"Error limpiando filtros: {e}")

    def load_current_filters(self):
        """Cargar filtros actuales desde la ventana principal"""
        try:
            # Obtener filtros actuales de la ventana principal
            current_filters = getattr(self.parent_window, 'current_filters', {})
            print(f"🔄 Cargando filtros actuales en diálogo: {current_filters}")

            if self.current_view == "comics":
                # Cargar filtros de comics
                if 'classification' in current_filters:
                    classification_value = current_filters['classification']
                    if classification_value is True:
                        self.classification_combo.set_selected(1)  # Solo clasificados
                    elif classification_value is False:
                        self.classification_combo.set_selected(2)  # Solo sin clasificar

                if 'quality_range' in current_filters:
                    min_quality, max_quality = current_filters['quality_range']
                    self.quality_min.set_value(min_quality)
                    self.quality_max.set_value(max_quality)

                if 'include_trash' in current_filters:
                    self.include_trash.set_active(True)
                elif 'exclude_trash' in current_filters:
                    self.include_trash.set_active(False)
                else:
                    # Por defecto, excluir papelera
                    self.include_trash.set_active(False)

            elif self.current_view == "volumes":
                # Cargar filtros de volúmenes
                if 'year_range' in current_filters:
                    min_year, max_year = current_filters['year_range']
                    self.year_min.set_value(min_year)
                    self.year_max.set_value(max_year)

                if 'count_range' in current_filters:
                    min_count, max_count = current_filters['count_range']
                    self.count_min.set_value(min_count)
                    self.count_max.set_value(max_count)

                if 'completion' in current_filters:
                    completion_value = current_filters['completion']
                    self.completion_combo.set_selected(completion_value)

                if 'publisher_name' in current_filters:
                    publisher_filter = current_filters['publisher_name']
                    self.publisher_entry.set_text(publisher_filter)

            elif self.current_view == "publishers":
                # Cargar filtros de editoriales
                if 'volume_range' in current_filters:
                    min_volumes, max_volumes = current_filters['volume_range']
                    self.volume_min.set_value(min_volumes)
                    self.volume_max.set_value(max_volumes)

                if 'has_description' in current_filters:
                    self.has_description.set_active(current_filters['has_description'])
                if 'has_logo' in current_filters:
                    self.has_logo.set_active(current_filters['has_logo'])
                if 'has_website' in current_filters:
                    self.has_website.set_active(current_filters['has_website'])

            print(f"✅ Filtros cargados correctamente en el diálogo")

        except Exception as e:
            print(f"Error cargando filtros actuales: {e}")

    def setup_keyboard_shortcuts(self):
        """Configurar atajos de teclado para la ventana de filtros"""
        # Ctrl+Enter para aplicar filtros
        apply_shortcut = Gtk.Shortcut()
        apply_shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string("<Control>Return"))
        apply_shortcut.set_action(Gtk.CallbackAction.new(self.on_apply_filters_shortcut))

        # Shift+Ctrl+R para limpiar filtros
        clear_shortcut = Gtk.Shortcut()
        clear_shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string("<Shift><Control>r"))
        clear_shortcut.set_action(Gtk.CallbackAction.new(self.on_clear_filters_shortcut))

        # Escape para cerrar
        escape_shortcut = Gtk.Shortcut()
        escape_shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string("Escape"))
        escape_shortcut.set_action(Gtk.CallbackAction.new(self.on_escape_shortcut))

        controller = Gtk.ShortcutController()
        controller.add_shortcut(apply_shortcut)
        controller.add_shortcut(clear_shortcut)
        controller.add_shortcut(escape_shortcut)

        self.add_controller(controller)

    def on_apply_filters_shortcut(self, widget, args):
        """Aplicar filtros con Ctrl+Enter"""
        self.on_apply_filters(None)
        return True

    def on_clear_filters_shortcut(self, widget, args):
        """Limpiar filtros con Ctrl+Shift+R"""
        self.on_clear_filters(None)
        return True

    def on_escape_shortcut(self, widget, args):
        """Cerrar ventana con Escape"""
        self.close()
        return True


# Nota: QuickFilterBar removida - ya no se usa en la aplicación principal