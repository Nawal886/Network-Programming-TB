"""
Komponen View untuk Py-SiteCheck
Halaman-halaman lengkap untuk navigasi: Sites, Alerts, dan Settings.

Setiap view adalah CTkFrame yang mengisi seluruh area konten utama.
Hanya satu view yang ditampilkan pada satu waktu (diatur oleh app.py).
"""

import customtkinter as ctk      # Library GUI modern berbasis Tkinter
from typing import Callable, Optional  # Type hints
import time                       # Untuk operasi waktu
from datetime import datetime     # Untuk memformat timestamp ke format yang mudah dibaca

# Import konfigurasi tema
from .theme import COLORS, FONTS, SIZES, get_status_code_color


# ══════════════════════════════════════════════════════
# VIEW 1: SitesView
# Halaman manajemen website - menampilkan tabel detail
# ══════════════════════════════════════════════════════

class SitesView(ctk.CTkFrame):
    """
    View manajemen website - menampilkan semua website dalam format tabel.
    Setiap baris menunjukkan: status indicator, URL, HTTP code, latency, port, dan tombol aksi.

    Berbeda dengan Dashboard yang menggunakan kartu (card),
    Sites view menampilkan website dalam format tabel (list/row).
    """

    def __init__(
        self,
        master,
        on_add_url: Callable,                      # Callback saat tombol Add URL diklik
        on_delete_site: Callable[[str], None],     # Callback saat tombol Delete diklik (parameter: URL)
        on_refresh_site: Callable[[str], None],    # Callback saat tombol Refresh diklik (parameter: URL)
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Simpan callback functions
        self.on_add_url = on_add_url
        self.on_delete_site = on_delete_site
        self.on_refresh_site = on_refresh_site

        # Dictionary untuk menyimpan referensi widget setiap baris
        # Key: URL, Value: dict berisi widget-widget (frame, status, code, latency, port)
        self.site_rows: dict[str, dict] = {}

        self._setup_ui()

    def _setup_ui(self):
        """Menyusun tampilan Sites view"""

        # Layout: 3 baris
        # Baris 0: Header (judul + tombol Add)
        # Baris 1: Header tabel (nama kolom)
        # Baris 2: Daftar website (scrollable)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Baris 2 mengisi sisa ruang vertikal

        # ── HEADER ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))
        header.grid_columnconfigure(0, weight=1)

        title_section = ctk.CTkFrame(header, fg_color="transparent")
        title_section.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_section, text="Sites",
            font=(FONTS["family"], FONTS["title_size"], "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        # Subtitle yang menunjukkan jumlah website (akan diupdate dinamis)
        self.subtitle_label = ctk.CTkLabel(
            title_section, text="Manage your monitored websites",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        )
        self.subtitle_label.pack(anchor="w", pady=(4, 0))

        # Tombol Add URL
        add_btn = ctk.CTkButton(
            header, text="+ Add URL",
            font=(FONTS["family"], FONTS["body_size"], "bold"),
            height=40,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_primary"],
            corner_radius=8,
            command=self.on_add_url
        )
        add_btn.grid(row=0, column=1, sticky="e")

        # ── HEADER TABEL (Nama Kolom) ──
        table_header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=8)
        table_header.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 4))
        table_header.grid_columnconfigure(1, weight=1)  # Kolom URL mengisi sisa ruang

        # Definisi kolom tabel: (nama_kolom, indeks_kolom)
        headers = [
            ("Status", 0), ("URL", 1), ("HTTP Code", 2),
            ("Latency", 3), ("Port", 4), ("Actions", 5)
        ]
        # Lebar tetap setiap kolom (0 = otomatis/mengisi sisa)
        widths = [60, 0, 100, 100, 120, 80]

        # Buat label untuk setiap kolom header
        for (name, col), w in zip(headers, widths):
            lbl = ctk.CTkLabel(
                table_header, text=name,
                font=(FONTS["family"], FONTS["small_size"], "bold"),
                text_color=COLORS["text_muted"],
                anchor="w"
            )
            if w > 0:
                lbl.configure(width=w)
            lbl.grid(row=0, column=col, sticky="ew", padx=12, pady=10)
            if col == 1:
                table_header.grid_columnconfigure(col, weight=1)

        # ── DAFTAR WEBSITE (Scrollable) ──
        self.sites_list = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["border_light"]
        )
        self.sites_list.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self.sites_list.grid_columnconfigure(0, weight=1)

        # Pesan empty state (muncul saat belum ada website)
        self.empty_label = ctk.CTkLabel(
            self.sites_list,
            text="🌍 No sites added yet.\nClick '+ Add URL' to start monitoring.",
            font=(FONTS["family"], FONTS["body_size"]),
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self.empty_label.grid(row=0, column=0, pady=80)

    def _update_subtitle(self):
        """Memperbarui subtitle dengan jumlah website yang dimonitor"""
        count = len(self.site_rows)
        if count == 0:
            self.subtitle_label.configure(text="Manage your monitored websites")
        else:
            self.subtitle_label.configure(
                text=f"{count} website{'s' if count != 1 else ''} being monitored"
            )

    def add_site_row(self, url: str):
        """
        Menambahkan baris baru ke tabel website.
        Setiap baris terdiri dari: status indicator, URL, HTTP code, latency, port, dan tombol aksi.

        Args:
            url: URL website yang ditambahkan
        """
        # Cegah duplikat
        if url in self.site_rows:
            return

        # Sembunyikan pesan empty state
        self.empty_label.grid_forget()

        row_idx = len(self.site_rows)  # Posisi baris baru

        # ── Frame baris (satu baris = satu frame) ──
        row_frame = ctk.CTkFrame(
            self.sites_list, fg_color=COLORS["bg_card"],
            corner_radius=8, height=50
        )
        row_frame.grid(row=row_idx, column=0, sticky="ew", pady=3)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_propagate(False)  # Jaga tinggi frame tetap 50px

        # ── Kolom 0: Status Indicator (●) ──
        status_ind = ctk.CTkLabel(
            row_frame, text="●",
            font=(FONTS["family"], 14),
            text_color=COLORS["text_muted"],  # Abu-abu (default)
            width=60, anchor="center"
        )
        status_ind.grid(row=0, column=0, padx=12, pady=8)

        # ── Kolom 1: URL ──
        # Potong URL yang terlalu panjang
        display_url = url if len(url) <= 45 else url[:42] + "..."
        url_lbl = ctk.CTkLabel(
            row_frame, text=display_url,
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        url_lbl.grid(row=0, column=1, sticky="ew", padx=12, pady=8)

        # ── Kolom 2: HTTP Code ──
        code_lbl = ctk.CTkLabel(
            row_frame, text="Checking...",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"],
            width=100, anchor="w"
        )
        code_lbl.grid(row=0, column=2, padx=12, pady=8)

        # ── Kolom 3: Latency ──
        lat_lbl = ctk.CTkLabel(
            row_frame, text="--",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_secondary"],
            width=100, anchor="w"
        )
        lat_lbl.grid(row=0, column=3, padx=12, pady=8)

        # ── Kolom 4: Port Status ──
        port_lbl = ctk.CTkLabel(
            row_frame, text="--",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_secondary"],
            width=120, anchor="w"
        )
        port_lbl.grid(row=0, column=4, padx=12, pady=8)

        # ── Kolom 5: Tombol Aksi (Refresh + Delete) ──
        action_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=80)
        action_frame.grid(row=0, column=5, padx=8, pady=8)

        # Tombol Refresh (↻) - cek ulang website ini
        ctk.CTkButton(
            action_frame, text="↻", width=28, height=28,
            font=(FONTS["family"], 14),
            fg_color="transparent",
            hover_color=COLORS["primary"],    # Ungu saat hover
            text_color=COLORS["text_muted"],
            corner_radius=6,
            # lambda dengan default arg u=url agar menangkap URL yang benar
            command=lambda u=url: self.on_refresh_site(u)
        ).pack(side="left", padx=2)

        # Tombol Delete (×) - hapus website ini
        ctk.CTkButton(
            action_frame, text="×", width=28, height=28,
            font=(FONTS["family"], 14),
            fg_color="transparent",
            hover_color=COLORS["error"],      # Merah saat hover
            text_color=COLORS["text_muted"],
            corner_radius=6,
            command=lambda u=url: self.on_delete_site(u)
        ).pack(side="left", padx=2)

        # Simpan referensi widget untuk update nanti
        self.site_rows[url] = {
            "frame": row_frame,
            "status": status_ind,
            "code": code_lbl,
            "latency": lat_lbl,
            "port": port_lbl,
        }
        self._update_subtitle()

    def remove_site_row(self, url: str):
        """Menghapus baris website dari tabel"""
        if url in self.site_rows:
            # Hancurkan frame baris
            self.site_rows[url]["frame"].destroy()
            del self.site_rows[url]

            # Atur ulang posisi baris yang tersisa (agar tidak ada celah)
            for i, (u, data) in enumerate(self.site_rows.items()):
                data["frame"].grid(row=i, column=0, sticky="ew", pady=3)

            # Tampilkan pesan kosong jika tidak ada website
            if not self.site_rows:
                self.empty_label.grid(row=0, column=0, pady=80)

            self._update_subtitle()

    def update_site_row(
        self, url: str, is_online: bool, status_code: int,
        latency_ms: float, port_open: bool, port: int, error_message: str = ""
    ):
        """
        Memperbarui data di baris tabel dengan status terbaru.

        Args:
            url: URL website
            is_online: Website online?
            status_code: HTTP status code
            latency_ms: Waktu respons (ms)
            port_open: Port TCP terbuka?
            port: Nomor port yang dicek
            error_message: Pesan error jika ada
        """
        if url not in self.site_rows:
            return

        row = self.site_rows[url]

        # ── Update warna status indicator ──
        if status_code < 0:
            color = COLORS["error"]       # Merah (gagal koneksi)
        elif is_online:
            color = COLORS["success"]     # Hijau (online)
        else:
            # Kuning untuk redirect, merah untuk error lainnya
            color = COLORS["warning"] if 300 <= status_code < 400 else COLORS["error"]
        row["status"].configure(text_color=color)

        # ── Update HTTP code ──
        if status_code < 0:
            row["code"].configure(
                text=error_message[:15] if error_message else "Error",
                text_color=COLORS["error"]
            )
        else:
            row["code"].configure(
                text=f"HTTP {status_code}",
                text_color=get_status_code_color(status_code)
            )

        # ── Update latency ──
        if latency_ms >= 0:
            lat = f"{latency_ms:.0f} ms" if latency_ms < 1000 else f"{latency_ms/1000:.2f} s"
        else:
            lat = "Timeout"
        row["latency"].configure(text=lat)

        # ── Update port status ──
        port_text = f"{port} ({'Open' if port_open else 'Closed'})"
        port_color = COLORS["success"] if port_open else COLORS["error"]
        row["port"].configure(text=port_text, text_color=port_color)


# ══════════════════════════════════════════════════════
# VIEW 2: AlertsView
# Halaman log alert - menampilkan riwayat perubahan status
# ══════════════════════════════════════════════════════

class AlertsView(ctk.CTkFrame):
    """
    View log alert - menampilkan riwayat perubahan status website secara kronologis.
    Alert terbaru muncul di paling atas (newest first).

    Alert dihasilkan saat website BERUBAH STATUS:
    - 🔴 DOWN: website yang tadinya online menjadi offline
    - 🟢 RECOVERED: website yang tadinya offline kembali online
    """

    def __init__(self, master, on_clear_alerts: Callable, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_clear_alerts = on_clear_alerts  # Callback saat tombol Clear All diklik
        self.alert_widgets: list[ctk.CTkFrame] = []  # Daftar widget card alert
        self._setup_ui()

    def _setup_ui(self):
        """Menyusun tampilan Alerts view"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))
        header.grid_columnconfigure(0, weight=1)

        title_section = ctk.CTkFrame(header, fg_color="transparent")
        title_section.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_section, text="Alerts",
            font=(FONTS["family"], FONTS["title_size"], "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        # Subtitle menunjukkan jumlah alert
        self.subtitle_label = ctk.CTkLabel(
            title_section, text="No alerts yet",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        )
        self.subtitle_label.pack(anchor="w", pady=(4, 0))

        # Tombol Clear All (hapus semua alert)
        clear_btn = ctk.CTkButton(
            header, text="🗑  Clear All",
            font=(FONTS["family"], FONTS["body_size"]),
            height=36,
            fg_color=COLORS["error"],          # Merah (aksi destruktif)
            hover_color="#DC2626",
            text_color=COLORS["text_primary"],
            corner_radius=8,
            command=self._on_clear
        )
        clear_btn.grid(row=0, column=1, sticky="e")

        # ── Daftar Alert (Scrollable) ──
        self.alerts_list = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["border_light"]
        )
        self.alerts_list.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self.alerts_list.grid_columnconfigure(0, weight=1)

        # Pesan empty state
        self.empty_label = ctk.CTkLabel(
            self.alerts_list,
            text="🔔 No alerts yet\n\nAlerts will appear here when websites\nchange status (online ↔ offline).",
            font=(FONTS["family"], FONTS["body_size"]),
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self.empty_label.grid(row=0, column=0, pady=80)

    def add_alert(self, alert_entry):
        """
        Menambahkan card alert baru ke view (terbaru di paling atas).

        Args:
            alert_entry: Objek AlertEntry dari core/monitor.py yang berisi
                         URL, tipe alert, pesan, timestamp, dan status code
        """
        # Sembunyikan pesan empty state
        self.empty_label.grid_forget()

        # Tentukan apakah ini alert DOWN atau RECOVERED
        is_down = alert_entry.alert_type in ("down", "error")

        # ── Buat Card Alert ──
        card = ctk.CTkFrame(
            self.alerts_list,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            # Border berwarna: merah untuk DOWN, hijau untuk RECOVERED
            border_color=COLORS["error"] if is_down else COLORS["success"]
        )
        card.grid_columnconfigure(1, weight=1)

        # Sisipkan card baru di paling atas (index 0)
        self.alert_widgets.insert(0, card)
        # Atur ulang posisi SEMUA card (yang baru di atas, yang lama ke bawah)
        for i, c in enumerate(self.alert_widgets):
            c.grid(row=i, column=0, sticky="ew", pady=4)

        # ── Kolom 0: Icon Status ──
        icon = "🔴" if is_down else "🟢"  # Merah untuk DOWN, hijau untuk RECOVERED
        ctk.CTkLabel(
            card, text=icon,
            font=(FONTS["family"], 20),
            width=48
        ).grid(row=0, column=0, rowspan=2, padx=(16, 8), pady=14)

        # ── Kolom 1, Baris 0: Badge Tipe + URL ──
        badge_text = "DOWN" if is_down else "RECOVERED"
        badge_color = COLORS["error"] if is_down else COLORS["success"]

        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="ew", padx=8, pady=(14, 0))

        # Badge tipe alert (label kecil dengan background berwarna)
        ctk.CTkLabel(
            title_frame, text=f"  {badge_text}  ",
            font=(FONTS["family"], FONTS["tiny_size"], "bold"),
            fg_color=badge_color,           # Background merah/hijau
            corner_radius=4,
            text_color=COLORS["text_primary"],
        ).pack(side="left", padx=(0, 8))

        # URL website
        ctk.CTkLabel(
            title_frame, text=alert_entry.url,
            font=(FONTS["family"], FONTS["body_size"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        # ── Kolom 1, Baris 1: Pesan Detail ──
        ctk.CTkLabel(
            card, text=alert_entry.message,
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).grid(row=1, column=1, sticky="w", padx=8, pady=(2, 14))

        # ── Kolom 2: Timestamp ──
        # Mengubah Unix timestamp (detik sejak 1970) ke format yang mudah dibaca
        ts = datetime.fromtimestamp(alert_entry.timestamp).strftime("%H:%M:%S  •  %d/%m/%Y")
        ctk.CTkLabel(
            card, text=ts,
            font=(FONTS["family"], FONTS["tiny_size"]),
            text_color=COLORS["text_muted"]
        ).grid(row=0, column=2, rowspan=2, padx=16, pady=14)

        # Update subtitle dengan jumlah alert
        count = len(self.alert_widgets)
        self.subtitle_label.configure(
            text=f"{count} alert{'s' if count != 1 else ''} recorded"
        )

    def _on_clear(self):
        """Handler saat tombol Clear All diklik - menghapus semua alert"""
        # Hancurkan semua widget card alert
        for card in self.alert_widgets:
            card.destroy()
        self.alert_widgets.clear()  # Kosongkan list

        # Tampilkan kembali pesan empty state
        self.empty_label.grid(row=0, column=0, pady=80)
        self.subtitle_label.configure(text="No alerts yet")

        # Beritahu monitor untuk menghapus data alert juga
        self.on_clear_alerts()


# ══════════════════════════════════════════════════════
# VIEW 3: SettingsView
# Halaman pengaturan - konfigurasi parameter monitoring
# ══════════════════════════════════════════════════════

class SettingsView(ctk.CTkFrame):
    """
    View pengaturan - mengatur parameter monitoring.
    Berisi kontrol untuk:
    1. Check Interval (seberapa sering cek website)
    2. Request Timeout (batas waktu tunggu respons)
    3. Start/Stop monitoring
    4. Informasi About
    """

    def __init__(self, master, monitor, on_status_bar_update: Callable, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.monitor = monitor  # Referensi ke objek SiteMonitor
        self.on_status_bar_update = on_status_bar_update  # Callback untuk update status bar
        self._setup_ui()

    def _setup_ui(self):
        """Menyusun tampilan Settings view"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))

        ctk.CTkLabel(
            header, text="Settings",
            font=(FONTS["family"], FONTS["title_size"], "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text="Configure monitoring parameters",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(4, 0))

        # ── Konten Scrollable ──
        content = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["border_light"]
        )
        content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        content.grid_columnconfigure(0, weight=1)

        # ════════════════════════════════════════════
        # CARD 1: Pengaturan Monitoring
        # ════════════════════════════════════════════
        monitor_card = self._create_card(
            content, "⏱  Monitoring", "Configure check intervals and timeouts"
        )
        monitor_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # ── Pengaturan Check Interval ──
        interval_frame = ctk.CTkFrame(monitor_card, fg_color="transparent")
        interval_frame.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            interval_frame, text="Check Interval (seconds)",
            font=(FONTS["family"], FONTS["body_size"]),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            interval_frame, text="How often to check website availability",
            font=(FONTS["family"], FONTS["tiny_size"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(2, 10))

        interval_control = ctk.CTkFrame(interval_frame, fg_color="transparent")
        interval_control.pack(fill="x")

        # Slider untuk mengatur interval (5 sampai 120 detik)
        # number_of_steps=23 → 23 langkah: 5, 10, 15, ..., 115, 120
        self.interval_slider = ctk.CTkSlider(
            interval_control,
            from_=5, to=120, number_of_steps=23,
            command=self._on_interval_change,     # Dipanggil setiap slider bergerak
            fg_color=COLORS["bg_input"],
            progress_color=COLORS["primary"],      # Bar progress berwarna ungu
            button_color=COLORS["primary_light"],
            button_hover_color=COLORS["primary_hover"],
            width=300
        )
        self.interval_slider.set(self.monitor.check_interval)  # Set nilai awal dari monitor
        self.interval_slider.pack(side="left", fill="x", expand=True, padx=(0, 16))

        # Label yang menampilkan nilai interval saat ini
        self.interval_label = ctk.CTkLabel(
            interval_control,
            text=f"{int(self.monitor.check_interval)}s",
            font=(FONTS["family"], FONTS["body_size"], "bold"),
            text_color=COLORS["primary"],
            width=50
        )
        self.interval_label.pack(side="right")

        # ── Pengaturan Request Timeout ──
        timeout_frame = ctk.CTkFrame(monitor_card, fg_color="transparent")
        timeout_frame.pack(fill="x", padx=20, pady=(8, 20))

        ctk.CTkLabel(
            timeout_frame, text="Request Timeout (seconds)",
            font=(FONTS["family"], FONTS["body_size"]),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            timeout_frame, text="Maximum time to wait for a response from each website",
            font=(FONTS["family"], FONTS["tiny_size"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(2, 10))

        timeout_control = ctk.CTkFrame(timeout_frame, fg_color="transparent")
        timeout_control.pack(fill="x")

        # Slider untuk mengatur timeout (3 sampai 30 detik)
        self.timeout_slider = ctk.CTkSlider(
            timeout_control,
            from_=3, to=30, number_of_steps=27,
            command=self._on_timeout_change,
            fg_color=COLORS["bg_input"],
            progress_color=COLORS["secondary"],    # Bar progress berwarna cyan
            button_color=COLORS["secondary"],
            button_hover_color=COLORS["secondary_hover"],
            width=300
        )
        self.timeout_slider.set(self.monitor.timeout)
        self.timeout_slider.pack(side="left", fill="x", expand=True, padx=(0, 16))

        # Label nilai timeout
        self.timeout_label = ctk.CTkLabel(
            timeout_control,
            text=f"{int(self.monitor.timeout)}s",
            font=(FONTS["family"], FONTS["body_size"], "bold"),
            text_color=COLORS["secondary"],
            width=50
        )
        self.timeout_label.pack(side="right")

        # ════════════════════════════════════════════
        # CARD 2: Kontrol Monitoring (Start/Stop)
        # ════════════════════════════════════════════
        control_card = self._create_card(
            content, "🎛  Control", "Start or stop the monitoring service"
        )
        control_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        control_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=(16, 20))
        control_frame.grid_columnconfigure(0, weight=1)

        # Label status monitoring (● aktif / ○ paused)
        self.monitoring_status_label = ctk.CTkLabel(
            control_frame,
            text="● Monitoring Active" if self.monitor.is_running() else "○ Monitoring Paused",
            font=(FONTS["family"], FONTS["body_size"]),
            text_color=COLORS["success"] if self.monitor.is_running() else COLORS["text_muted"]
        )
        self.monitoring_status_label.pack(side="left")

        # Tombol Toggle Start/Stop
        self.toggle_btn = ctk.CTkButton(
            control_frame,
            text="⏹  Stop Monitoring" if self.monitor.is_running() else "▶  Start Monitoring",
            font=(FONTS["family"], FONTS["body_size"], "bold"),
            height=40,
            # Warna disesuaikan: merah saat aktif (untuk stop), hijau saat paused (untuk start)
            fg_color=COLORS["error"] if self.monitor.is_running() else COLORS["success"],
            hover_color="#DC2626" if self.monitor.is_running() else "#059669",
            text_color=COLORS["text_primary"],
            corner_radius=8,
            command=self._toggle_monitoring
        )
        self.toggle_btn.pack(side="right")

        # ════════════════════════════════════════════
        # CARD 3: Informasi About
        # ════════════════════════════════════════════
        about_card = self._create_card(
            content, "ℹ️  About", "Application information"
        )
        about_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        about_frame = ctk.CTkFrame(about_card, fg_color="transparent")
        about_frame.pack(fill="x", padx=20, pady=(16, 20))

        # Daftar informasi aplikasi
        info_lines = [
            ("Application", "Py-SiteCheck v1.0.0"),
            ("Description", "Web Availability Monitor"),
            ("Author", "Nawal Haromaen (714240038)"),
            ("Course", "Network Programming"),
            ("Lecturer", "M. Yusril Helmi Setyawan, S.Kom., M.Kom."),
            ("Institution", "Universitas Logistik Dan Bisnis Internasional (ULBI)"),
            ("Framework", "Python + CustomTkinter"),
            ("Libraries", "requests, socket, threading"),
        ]

        # Tampilkan setiap baris informasi sebagai label: value
        for label, value in info_lines:
            line_frame = ctk.CTkFrame(about_frame, fg_color="transparent")
            line_frame.pack(fill="x", pady=3)

            ctk.CTkLabel(
                line_frame, text=f"{label}:",
                font=(FONTS["family"], FONTS["small_size"]),
                text_color=COLORS["text_muted"],
                width=120, anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                line_frame, text=value,
                font=(FONTS["family"], FONTS["small_size"]),
                text_color=COLORS["text_primary"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

    def _create_card(self, parent, title: str, subtitle: str) -> ctk.CTkFrame:
        """
        Membuat card pengaturan yang bisa dipakai ulang.
        Setiap card punya: header (judul + subjudul) dan garis pemisah.

        Args:
            parent: Widget tempat card ditaruh
            title: Judul card (misal "⏱  Monitoring")
            subtitle: Deskripsi singkat (misal "Configure check intervals...")

        Returns:
            CTkFrame card yang sudah diberi header dan separator
        """
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )

        # Header card
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))

        ctk.CTkLabel(
            header, text=title,
            font=(FONTS["family"], FONTS["heading_size"], "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text=subtitle,
            font=(FONTS["family"], FONTS["tiny_size"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(2, 0))

        # Garis pemisah horizontal
        sep = ctk.CTkFrame(card, fg_color=COLORS["border"], height=1)
        sep.pack(fill="x", padx=20, pady=(12, 0))

        return card

    def _on_interval_change(self, value):
        """
        Handler saat slider interval digeser.
        Langsung mengubah check_interval di monitor.
        """
        val = int(value)
        self.interval_label.configure(text=f"{val}s")    # Update label (misal "30s")
        self.monitor.check_interval = val                 # Update nilai di monitor

    def _on_timeout_change(self, value):
        """
        Handler saat slider timeout digeser.
        Langsung mengubah timeout di monitor.
        """
        val = int(value)
        self.timeout_label.configure(text=f"{val}s")
        self.monitor.timeout = val

    def _toggle_monitoring(self):
        """
        Toggle (saklar) monitoring on/off.
        Jika sedang aktif → stop, jika sedang paused → start.
        Update tampilan tombol dan label sesuai status baru.
        """
        if self.monitor.is_running():
            # ── STOP MONITORING ──
            self.monitor.stop_monitoring()
            self.monitoring_status_label.configure(
                text="○ Monitoring Paused",
                text_color=COLORS["text_muted"]          # Abu-abu
            )
            self.toggle_btn.configure(
                text="▶  Start Monitoring",
                fg_color=COLORS["success"],               # Hijau (ajakan untuk start)
                hover_color="#059669"
            )
        else:
            # ── START MONITORING ──
            self.monitor.start_monitoring()
            self.monitoring_status_label.configure(
                text="● Monitoring Active",
                text_color=COLORS["success"]              # Hijau
            )
            self.toggle_btn.configure(
                text="⏹  Stop Monitoring",
                fg_color=COLORS["error"],                 # Merah (ajakan untuk stop)
                hover_color="#DC2626"
            )

        # Beritahu app.py untuk update status bar
        self.on_status_bar_update()
