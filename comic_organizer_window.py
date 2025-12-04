#!/usr/bin/env python3
"""
Ventana de reorganización de cómics
Muestra preview de cómo quedarán organizados los cómics y permite ejecutar el proceso
"""

import gi
import threading
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio, Pango

from helpers.comic_organizer import ComicOrganizer, ComicOrganizationPlan


class ComicOrganizerWindow(Adw.Window):
    """Ventana para reorganizar y renombrar cómics físicos de volumen(es)"""

    def __init__(self, parent_window, session, config, volume_id=None, volume_ids=None):
        super().__init__()

        print(f"\n🔧 DEBUG: Inicializando ComicOrganizerWindow")
        print(f"  - volume_id: {volume_id}")
        print(f"  - volume_ids: {volume_ids}")

        self.session = session
        self.config = config
        self.volume_id = volume_id
        self.volume_ids = volume_ids or []
        self.volumes = {}  # Dict volume_id -> Volume object
        self.publishers = {}  # Dict publisher_id -> Publisher object
        self.plans = []
        self.selected_plans = set()  # IDs de planes seleccionados

        # Cargar información de volumen(es)
        print(f"🔧 DEBUG: Cargando info de volúmenes...")
        self.load_volumes_info()
        print(f"🔧 DEBUG: Volúmenes cargados: {len(self.volumes)}")

        # Configurar ventana
        if len(self.volumes) == 1:
            volume = list(self.volumes.values())[0]
            volume_title = volume.nombre
        else:
            volume_title = f"{len(self.volumes)} Volúmenes"

        self.set_title(f"Reorganizar Cómics - {volume_title}")
        self.set_default_size(1200, 700)
        self.set_modal(True)

        if parent_window:
            self.set_transient_for(parent_window)

        # Crear UI
        self.setup_ui()

        # Iniciar generación de planes
        self.generate_plans()

    def load_volumes_info(self):
        """Cargar información de volúmenes y editoriales"""
        from entidades.volume_model import Volume
        from entidades.publisher_model import Publisher

        # Construir lista de IDs de volúmenes
        target_volume_ids = []
        if self.volume_id:
            target_volume_ids.append(self.volume_id)
        if self.volume_ids:
            target_volume_ids.extend(self.volume_ids)

        # Cargar volúmenes
        volumes_list = self.session.query(Volume).filter(
            Volume.id_volume.in_(target_volume_ids)
        ).all()

        for volume in volumes_list:
            self.volumes[volume.id_volume] = volume

            # Cargar publisher si no está cargado ya
            if volume.id_publisher and volume.id_publisher not in self.publishers:
                publisher = self.session.query(Publisher).filter_by(
                    id_publisher=volume.id_publisher
                ).first()
                if publisher:
                    self.publishers[volume.id_publisher] = publisher

    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Box principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Banner informativo del volumen
        info_banner = self.create_volume_info_banner()
        if info_banner:
            main_box.append(info_banner)

        # Toolbar con controles
        toolbar = self.create_toolbar()
        main_box.append(toolbar)

        # Área de contenido con scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        # Lista de planes
        self.plans_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.plans_list_box.set_margin_start(12)
        self.plans_list_box.set_margin_end(12)
        self.plans_list_box.set_margin_top(12)
        self.plans_list_box.set_margin_bottom(12)

        scrolled.set_child(self.plans_list_box)
        main_box.append(scrolled)

        # Status bar
        self.status_label = Gtk.Label()
        self.status_label.set_margin_start(12)
        self.status_label.set_margin_end(12)
        self.status_label.set_margin_top(6)
        self.status_label.set_margin_bottom(6)
        self.status_label.add_css_class("dim-label")
        main_box.append(self.status_label)

        # Barra de progreso (oculta inicialmente)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_margin_start(12)
        self.progress_bar.set_margin_end(12)
        self.progress_bar.set_margin_bottom(12)
        self.progress_bar.set_visible(False)
        main_box.append(self.progress_bar)

        # Botones de acción
        action_box = self.create_action_buttons()
        main_box.append(action_box)

        self.set_content(main_box)

    def create_volume_info_banner(self):
        """Crear banner con información de los volúmenes"""
        if not self.volumes:
            return None

        banner = Adw.Banner()

        # Crear box con información
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_margin_start(12)
        info_box.set_margin_end(12)
        info_box.set_margin_top(6)
        info_box.set_margin_bottom(6)

        if len(self.volumes) == 1:
            # Un solo volumen
            volume = list(self.volumes.values())[0]
            publisher = self.publishers.get(volume.id_publisher) if volume.id_publisher else None
            publisher_name = publisher.nombre if publisher else "Sin Editorial"
            volume_year = volume.anio_inicio if volume.anio_inicio > 0 else ""
            volume_folder = f"{volume.nombre}-{volume_year}" if volume_year else volume.nombre

            banner.set_title(f"Volumen: {volume.nombre} ({volume_year})")
            banner.set_button_label("")
            banner.set_revealed(True)

            # Editorial
            publisher_label = Gtk.Label()
            publisher_label.set_markup(f"<b>Editorial:</b> {publisher_name}")
            publisher_label.set_halign(Gtk.Align.START)
            info_box.append(publisher_label)

            # Path de destino
            destination_path = f"{self.config.carpeta_organizacion}/{publisher_name}/{volume_folder}/"
            dest_label = Gtk.Label()
            dest_label.set_markup(f"<b>Carpeta de destino:</b> {destination_path}")
            dest_label.set_halign(Gtk.Align.START)
            dest_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
            info_box.append(dest_label)
        else:
            # Múltiples volúmenes
            banner.set_title(f"Reorganizando {len(self.volumes)} volúmenes")
            banner.set_button_label("")
            banner.set_revealed(True)

            # Carpeta base
            base_label = Gtk.Label()
            base_label.set_markup(f"<b>Carpeta base:</b> {self.config.carpeta_organizacion}/")
            base_label.set_halign(Gtk.Align.START)
            base_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
            info_box.append(base_label)

            # Lista de volúmenes (máximo 5)
            volumes_label = Gtk.Label()
            volume_names = [v.nombre for v in list(self.volumes.values())[:5]]
            if len(self.volumes) > 5:
                volume_names.append(f"... y {len(self.volumes) - 5} más")
            volumes_text = ", ".join(volume_names)
            volumes_label.set_markup(f"<b>Volúmenes:</b> {volumes_text}")
            volumes_label.set_halign(Gtk.Align.START)
            volumes_label.set_wrap(True)
            info_box.append(volumes_label)

        # Crear un box contenedor para banner + info
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        container.append(banner)
        container.append(info_box)

        return container

    def create_toolbar(self):
        """Crear toolbar con controles"""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)

        # Botón seleccionar todos
        select_all_btn = Gtk.Button(label="Seleccionar Todos")
        select_all_btn.connect("clicked", self.on_select_all)
        toolbar.append(select_all_btn)

        # Botón deseleccionar todos
        deselect_all_btn = Gtk.Button(label="Deseleccionar Todos")
        deselect_all_btn.connect("clicked", self.on_deselect_all)
        toolbar.append(deselect_all_btn)

        # Separador
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.append(separator)

        # Filtro por estado
        self.filter_combo = Gtk.ComboBoxText()
        self.filter_combo.append("all", "Todos")
        self.filter_combo.append("ok", "Listos para mover")
        self.filter_combo.append("duplicate", "Duplicados")
        self.filter_combo.append("already_in_place", "Ya en lugar correcto")
        self.filter_combo.append("no_info", "Sin catalogar")
        self.filter_combo.set_active(0)
        self.filter_combo.connect("changed", self.on_filter_changed)
        toolbar.append(self.filter_combo)

        return toolbar

    def create_action_buttons(self):
        """Crear botones de acción"""
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_box.set_margin_start(12)
        action_box.set_margin_end(12)
        action_box.set_margin_bottom(12)
        action_box.set_halign(Gtk.Align.END)

        # Botón cancelar
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda b: self.close())
        action_box.append(cancel_btn)

        # Botón ejecutar
        self.execute_btn = Gtk.Button(label="Reorganizar Cómics")
        self.execute_btn.add_css_class("suggested-action")
        self.execute_btn.connect("clicked", self.on_execute_reorganization)
        self.execute_btn.set_sensitive(False)  # Deshabilitado hasta que se generen planes
        action_box.append(self.execute_btn)

        return action_box

    def generate_plans(self):
        """Generar planes de reorganización en hilo separado"""
        print(f"🔧 DEBUG: generate_plans() llamado")

        # Verificar que hay carpeta configurada
        if not self.config.carpeta_organizacion:
            print(f"❌ ERROR: No hay carpeta de organización configurada")
            self.show_error("No hay carpeta de organización configurada.\n\nVe a Configuración → ComicVine y configura la carpeta de organización.")
            return

        print(f"🔧 DEBUG: Carpeta de organización: {self.config.carpeta_organizacion}")
        self.status_label.set_text("Generando planes de reorganización...")

        def worker():
            try:
                print(f"🔧 DEBUG: Worker thread iniciado")
                organizer = ComicOrganizer(
                    base_folder=self.config.carpeta_organizacion,
                    session=self.session
                )

                print(f"🔧 DEBUG: Llamando create_organization_plan...")
                print(f"  - volume_id: {self.volume_id}")
                print(f"  - volume_ids: {self.volume_ids if self.volume_ids else None}")

                # Generar planes para el/los volumen(es)
                plans = organizer.create_organization_plan(
                    volume_id=self.volume_id,
                    volume_ids=self.volume_ids if self.volume_ids else None
                )

                print(f"🔧 DEBUG: Planes generados: {len(plans)} total")
                for i, plan in enumerate(plans):
                    print(f"  Plan {i+1}: status={plan.status}, current={plan.current_path}")
                    if plan.status == 'ERROR':
                        print(f"    ❌ ERROR: {plan.message}")

                # Actualizar UI en hilo principal
                GLib.idle_add(lambda: self.on_plans_generated(plans))

            except Exception as e:
                print(f"❌ ERROR FATAL generando planes: {e}")
                import traceback
                traceback.print_exc()
                GLib.idle_add(lambda: self.show_error(f"Error generando planes:\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def on_plans_generated(self, plans):
        """Callback cuando se generan los planes"""
        print(f"🔧 DEBUG: on_plans_generated llamado con {len(plans)} planes")
        self.plans = plans

        # Mostrar estadísticas
        stats = self.calculate_stats()
        print(f"🔧 DEBUG: Estadísticas: {stats}")
        self.update_status(stats)

        # Renderizar lista
        print(f"🔧 DEBUG: Llamando render_plans_list...")
        self.render_plans_list()
        print(f"🔧 DEBUG: render_plans_list completado")

        # Habilitar botón de ejecución
        self.execute_btn.set_sensitive(True)

    def calculate_stats(self):
        """Calcular estadísticas de los planes"""
        stats = {
            'total': len(self.plans),
            'ok': 0,
            'duplicate': 0,
            'already_in_place': 0,
            'no_info': 0,
            'error': 0
        }

        for plan in self.plans:
            if plan.status == 'OK':
                stats['ok'] += 1
            elif plan.status == 'DUPLICATE':
                stats['duplicate'] += 1
            elif plan.status == 'ALREADY_IN_PLACE':
                stats['already_in_place'] += 1
            elif plan.status == 'NO_INFO':
                stats['no_info'] += 1
            elif plan.status == 'ERROR':
                stats['error'] += 1

        return stats

    def update_status(self, stats):
        """Actualizar label de estado con estadísticas"""
        text = (
            f"Total: {stats['total']} | "
            f"Para mover: {stats['ok']} | "
            f"Duplicados: {stats['duplicate']} | "
            f"Ya en lugar: {stats['already_in_place']} | "
            f"Sin catalogar: {stats['no_info']}"
        )

        if stats['error'] > 0:
            text += f" | Errores: {stats['error']}"

        self.status_label.set_text(text)

    def render_plans_list(self):
        """Renderizar lista de planes agrupados por volumen"""
        from collections import defaultdict

        # Limpiar lista actual
        while self.plans_list_box.get_first_child():
            self.plans_list_box.remove(self.plans_list_box.get_first_child())

        # Obtener filtro actual
        filter_id = self.filter_combo.get_active_id()

        # Agrupar planes por volumen
        plans_by_volume = defaultdict(list)
        for plan in self.plans:
            # Aplicar filtro
            if not self.should_show_plan(plan, filter_id):
                continue
            plans_by_volume[plan.volume_id].append(plan)

        # Si hay un solo volumen o no hay agrupación, mostrar plano
        if len(plans_by_volume) <= 1:
            # Renderizar cada plan directamente
            for plan in self.plans:
                if not self.should_show_plan(plan, filter_id):
                    continue
                plan_row = self.create_plan_row(plan)
                self.plans_list_box.append(plan_row)
        else:
            # Múltiples volúmenes: agrupar con headers
            for volume_id, volume_plans in sorted(plans_by_volume.items()):
                # Crear header del volumen
                volume_header = self.create_volume_header(volume_id, len(volume_plans))
                self.plans_list_box.append(volume_header)

                # Renderizar planes del volumen
                for plan in volume_plans:
                    plan_row = self.create_plan_row(plan)
                    self.plans_list_box.append(plan_row)

                # Separador
                separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                separator.set_margin_top(12)
                separator.set_margin_bottom(12)
                self.plans_list_box.append(separator)

    def create_volume_header(self, volume_id, plan_count):
        """Crear header para un grupo de volumen"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header_box.set_margin_top(12)
        header_box.set_margin_bottom(6)

        # Obtener información del volumen
        volume = self.volumes.get(volume_id)
        if not volume:
            return header_box

        publisher = self.publishers.get(volume.id_publisher) if volume.id_publisher else None
        publisher_name = publisher.nombre if publisher else "Sin Editorial"
        volume_year = volume.anio_inicio if volume.anio_inicio > 0 else ""

        # Título del volumen
        title_label = Gtk.Label()
        title_text = f"{volume.nombre}"
        if volume_year:
            title_text += f" ({volume_year})"
        title_label.set_markup(f"<b>{title_text}</b>")
        title_label.set_halign(Gtk.Align.START)
        header_box.append(title_label)

        # Subtitle con editorial y cantidad
        subtitle_label = Gtk.Label()
        subtitle_label.set_markup(f"<small>{publisher_name} • {plan_count} cómic(s)</small>")
        subtitle_label.set_halign(Gtk.Align.START)
        subtitle_label.add_css_class("dim-label")
        header_box.append(subtitle_label)

        return header_box

    def should_show_plan(self, plan, filter_id):
        """Determina si un plan debe mostrarse según el filtro"""
        if filter_id == "all":
            return True
        elif filter_id == "ok":
            return plan.status == "OK"
        elif filter_id == "duplicate":
            return plan.status == "DUPLICATE"
        elif filter_id == "already_in_place":
            return plan.status == "ALREADY_IN_PLACE"
        elif filter_id == "no_info":
            return plan.status == "NO_INFO"
        elif filter_id == "error":
            return plan.status == "ERROR"

        return True

    def create_plan_row(self, plan: ComicOrganizationPlan):
        """Crear widget de fila para un plan"""
        row = Adw.ActionRow()

        # Título: nombre de archivo actual
        current_filename = Path(plan.current_path).name
        row.set_title(current_filename)

        # Subtítulo: path nuevo o mensaje
        if plan.status in ['OK', 'DUPLICATE']:
            row.set_subtitle(f"→ {plan.new_path_relative}")
        else:
            row.set_subtitle(plan.message)

        # Badge de estado
        status_label = Gtk.Label()
        status_label.set_valign(Gtk.Align.CENTER)

        if plan.status == 'OK':
            status_label.set_markup('<span color="green">✓ Listo</span>')
        elif plan.status == 'DUPLICATE':
            status_label.set_markup(f'<span color="orange">⚠ Duplicado (ver{plan.version:02d})</span>')
        elif plan.status == 'ALREADY_IN_PLACE':
            status_label.set_markup('<span color="blue">✓ En lugar</span>')
        elif plan.status == 'NO_INFO':
            status_label.set_markup('<span color="gray">⊘ Sin info</span>')
        elif plan.status == 'ERROR':
            status_label.set_markup('<span color="red">✗ Error</span>')

        row.add_suffix(status_label)

        # Checkbox para seleccionar
        # Solo para planes que se pueden ejecutar
        if plan.status in ['OK', 'DUPLICATE']:
            checkbox = Gtk.CheckButton()
            checkbox.set_valign(Gtk.Align.CENTER)
            checkbox.set_active(plan.comicbook_id in self.selected_plans)
            checkbox.connect(
                "toggled",
                lambda cb, plan_id=plan.comicbook_id: self.on_plan_toggled(cb, plan_id)
            )
            row.add_prefix(checkbox)

        return row

    def on_plan_toggled(self, checkbox, plan_id):
        """Callback cuando se toggle un checkbox"""
        if checkbox.get_active():
            self.selected_plans.add(plan_id)
        else:
            self.selected_plans.discard(plan_id)

    def on_select_all(self, button):
        """Seleccionar todos los planes ejecutables"""
        for plan in self.plans:
            if plan.status in ['OK', 'DUPLICATE']:
                self.selected_plans.add(plan.comicbook_id)

        # Re-renderizar
        self.render_plans_list()

    def on_deselect_all(self, button):
        """Deseleccionar todos los planes"""
        self.selected_plans.clear()

        # Re-renderizar
        self.render_plans_list()

    def on_filter_changed(self, combo):
        """Callback cuando cambia el filtro"""
        self.render_plans_list()

    def on_execute_reorganization(self, button):
        """Ejecutar reorganización de cómics seleccionados"""
        # Filtrar planes seleccionados
        selected_plans = [
            p for p in self.plans
            if p.comicbook_id in self.selected_plans
        ]

        if not selected_plans:
            self.show_error("No hay cómics seleccionados para reorganizar.")
            return

        # Mostrar confirmación
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Confirmar Reorganización")
        dialog.set_body(
            f"¿Estás seguro de que quieres reorganizar {len(selected_plans)} cómic(s)?\n\n"
            f"Los archivos se moverán a:\n{self.config.carpeta_organizacion}\n\n"
            f"Esta operación no se puede deshacer fácilmente."
        )
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("execute", "Reorganizar")
        dialog.set_response_appearance("execute", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("cancel")
        dialog.connect(
            "response",
            lambda d, r, plans=selected_plans: self.on_confirm_reorganization(d, r, plans)
        )
        dialog.present()

    def on_confirm_reorganization(self, dialog, response, plans):
        """Confirmar y ejecutar reorganización"""
        if response == "execute":
            self.execute_reorganization(plans)

    def execute_reorganization(self, plans):
        """Ejecutar reorganización en hilo separado"""
        # Deshabilitar controles
        self.execute_btn.set_sensitive(False)
        self.progress_bar.set_visible(True)
        self.status_label.set_text("Reorganizando cómics...")

        def worker():
            try:
                organizer = ComicOrganizer(
                    base_folder=self.config.carpeta_organizacion,
                    session=self.session
                )

                # Ejecutar con callback de progreso
                stats = organizer.execute_plans(
                    plans=plans,
                    dry_run=False,
                    progress_callback=self.on_progress
                )

                # Mostrar resultado
                GLib.idle_add(lambda: self.on_reorganization_complete(stats))

            except Exception as e:
                print(f"Error ejecutando reorganización: {e}")
                import traceback
                traceback.print_exc()
                GLib.idle_add(lambda: self.show_error(f"Error ejecutando reorganización:\n{e}"))
                GLib.idle_add(self.restore_ui_after_execution)

        threading.Thread(target=worker, daemon=True).start()

    def on_progress(self, index, total, plan, success, message):
        """Callback de progreso"""
        progress = (index + 1) / total
        GLib.idle_add(lambda: self.progress_bar.set_fraction(progress))
        GLib.idle_add(
            lambda: self.status_label.set_text(
                f"Procesando {index + 1}/{total}: {Path(plan.current_path).name}"
            )
        )

    def on_reorganization_complete(self, stats):
        """Callback cuando completa la reorganización"""
        # Restaurar UI
        self.restore_ui_after_execution()

        # Mostrar resultado
        message = (
            f"Reorganización completada.\n\n"
            f"✓ Exitosos: {stats['success']}\n"
            f"✗ Fallidos: {stats['failed']}\n"
            f"⊘ Omitidos: {stats['skipped']}"
        )

        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Reorganización Completada")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.connect("response", lambda d, r: self.close())
        dialog.present()

    def restore_ui_after_execution(self):
        """Restaurar UI después de ejecutar"""
        self.execute_btn.set_sensitive(True)
        self.progress_bar.set_visible(False)
        self.progress_bar.set_fraction(0)

    def show_error(self, message):
        """Mostrar mensaje de error"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.present()


def show_organizer_window(parent_window, session, config, volume_id=None, volume_ids=None):
    """Helper para mostrar la ventana de reorganización"""
    window = ComicOrganizerWindow(parent_window, session, config, volume_id, volume_ids)
    window.present()
    return window
