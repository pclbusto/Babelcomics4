import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, GObject
from helpers.download_manager import DownloadManager

class DownloadCard(Gtk.Box):
    def __init__(self, volume_cv_id, dl_info):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.volume_cv_id = volume_cv_id
        
        self.add_css_class("card")
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_size_request(300, 150)
        
        # Guardar metadata para filtrado
        self.dl_info = dl_info
        
        self.title_label = Gtk.Label(label=dl_info.get('title', 'Volumen Desconocido'))
        self.title_label.add_css_class("title-4")
        self.title_label.set_halign(Gtk.Align.START)
        self.append(self.title_label)
        
        self.status_label = Gtk.Label(label=dl_info.get('message', 'En cola...'))
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.add_css_class("dim-label")
        self.append(self.status_label)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(dl_info.get('progress', 0.0))
        self.append(self.progress_bar)

        # Botón de reintento (solo visible en error)
        self.retry_button = Gtk.Button(label="Reintentar")
        self.retry_button.add_css_class("suggested-action")
        self.retry_button.set_halign(Gtk.Align.END)
        self.retry_button.set_visible(dl_info.get('status') == 'error')
        self.retry_button.connect("clicked", self.on_retry_clicked)
        self.append(self.retry_button)

    def on_retry_clicked(self, button):
        from helpers.download_manager import DownloadManager
        manager = DownloadManager.get_instance()
        if manager.retry_download(self.volume_cv_id):
            self.retry_button.set_visible(False)
        
    def update_progress(self, fraction, message):
        self.progress_bar.set_fraction(fraction)
        self.status_label.set_text(message)
        self.dl_info['progress'] = fraction
        self.dl_info['message'] = message
        
        # Ocultar botón reintento si ya no es error
        if self.dl_info.get('status') != 'error':
            self.retry_button.set_visible(False)

class DownloadsPage(Adw.NavigationPage):
    def __init__(self):
        super().__init__(title="Descargas Activas")
        
        self.manager = DownloadManager.get_instance()
        self.cards = {} # volume_cv_id -> DownloadCard
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        header = Adw.HeaderBar()
        self.main_box.append(header)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        
        title = Gtk.Label(label="Progreso de Descargas")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        content_box.append(title)
        
        # Barra de filtros
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        filter_box.set_margin_bottom(10)
        
        self.search_entry = Gtk.SearchEntry(placeholder_text="Buscar volumen...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_filter_changed)
        filter_box.append(self.search_entry)
        
        status_model = Gtk.StringList.new(["Todos", "En cola", "Descargando", "Completado", "Error"])
        self.status_dropdown = Gtk.DropDown(model=status_model)
        self.status_dropdown.connect("notify::selected", self.on_filter_changed)
        filter_box.append(self.status_dropdown)
        
        issues_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        issues_label = Gtk.Label(label="Min. Issues:")
        issues_box.append(issues_label)
        
        self.issues_spinner = Gtk.SpinButton.new_with_range(0, 1000, 1)
        self.issues_spinner.set_value(0)
        self.issues_spinner.connect("value-changed", self.on_filter_changed)
        issues_box.append(self.issues_spinner)
        filter_box.append(issues_box)
        
        self.clear_button = Gtk.Button(label="Limpiar Finalizados")
        self.clear_button.add_css_class("destructive-action")
        self.clear_button.connect("clicked", self.on_clear_clicked)
        filter_box.append(self.clear_button)
        
        content_box.append(filter_box)
        
        self.empty_label = Gtk.Label(label="No hay descargas activas en este momento.")
        self.empty_label.add_css_class("dim-label")
        content_box.append(self.empty_label)
        
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(3)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_homogeneous(False)
        self.flowbox.set_column_spacing(15)
        self.flowbox.set_row_spacing(15)
        content_box.append(self.flowbox)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_child(content_box)
        self.main_box.append(scrolled_window)
        
        self.set_child(self.main_box)
        
        # Conectar señales del manager
        self.manager.connect('download-added', self.on_download_added)
        self.manager.connect('download-progress', self.on_download_progress)
        self.manager.connect('download-completed', self.on_download_completed)
        self.manager.connect('download-error', self.on_download_error)
        self.manager.connect('download-removed', self.on_download_removed)
        
        # Cargar inicial
        self.refresh_cards()
        
    def on_filter_changed(self, *args):
        self.apply_filters()
        
    def apply_filters(self):
        search_text = self.search_entry.get_text().lower()
        status_idx = self.status_dropdown.get_selected()
        min_issues = self.issues_spinner.get_value_as_int()
        
        status_map = {
            0: None, # Todos
            1: 'queued',
            2: 'downloading',
            3: 'completed',
            4: 'error'
        }
        selected_status = status_map.get(status_idx)
        
        visible_count = 0
        for card in self.cards.values():
            info = card.dl_info
            
            # Text filter
            matches_text = search_text in info.get('title', '').lower() if search_text else True
            
            # Status filter
            matches_status = info.get('status') == selected_status if selected_status else True
            
            # Issues filter
            matches_issues = info.get('total_items', 0) >= min_issues
            
            is_visible = matches_text and matches_status and matches_issues
            card.set_visible(is_visible)
            if is_visible:
                visible_count += 1
                
        self.empty_label.set_visible(visible_count == 0)
        self.empty_label.set_text("No hay descargas que coincidan con los filtros." if len(self.cards) > 0 else "No hay descargas en este momento.")

    def on_clear_clicked(self, button):
        to_remove = []
        for cv_id, dl_info in self.manager.active_downloads.items():
            if dl_info['status'] in ['completed', 'error']:
                to_remove.append(cv_id)
                
        for cv_id in to_remove:
            self.manager.remove_download(cv_id)
        
    def refresh_cards(self):
        for child in self.flowbox:
            self.flowbox.remove(child)
        self.cards.clear()
        
        has_downloads = False
        for cv_id, dl_info in self.manager.active_downloads.items():
            self._create_card(cv_id, dl_info)
            has_downloads = True
                
        self.apply_filters()
        
    def _create_card(self, volume_cv_id, dl_info):
        card = DownloadCard(volume_cv_id, dl_info)
        self.cards[volume_cv_id] = card
        self.flowbox.append(card)
        
    def on_download_added(self, manager, volume_cv_id):
        dl_info = self.manager.active_downloads.get(volume_cv_id)
        if dl_info and volume_cv_id not in self.cards:
            self._create_card(volume_cv_id, dl_info)
            self.apply_filters()
            
    def on_download_removed(self, manager, volume_cv_id):
        if volume_cv_id in self.cards:
            card = self.cards.pop(volume_cv_id)
            self.flowbox.remove(card)
            self.apply_filters()
            
    def on_download_progress(self, manager, volume_cv_id, fraction, message):
        if volume_cv_id in self.cards:
            self.cards[volume_cv_id].update_progress(fraction, message)
            self.apply_filters() # Re-apply in case status changed
            
    def on_download_completed(self, manager, volume_cv_id):
        if volume_cv_id in self.cards:
            self.cards[volume_cv_id].update_progress(1.0, "¡Completado!")
            self.cards[volume_cv_id].dl_info['status'] = 'completed'
            self.cards[volume_cv_id].status_label.remove_css_class("dim-label")
            self.cards[volume_cv_id].status_label.add_css_class("success")
            self.apply_filters()
            
    def on_download_error(self, manager, volume_cv_id, error_msg):
        if volume_cv_id in self.cards:
            self.cards[volume_cv_id].update_progress(0.0, f"Error: {error_msg}")
            self.cards[volume_cv_id].dl_info['status'] = 'error'
            self.cards[volume_cv_id].status_label.remove_css_class("dim-label")
            self.cards[volume_cv_id].status_label.add_css_class("error")
            self.cards[volume_cv_id].retry_button.set_visible(True)
            self.apply_filters()

def create_downloads_page():
    return DownloadsPage()
