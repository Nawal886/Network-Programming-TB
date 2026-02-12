"""
Main Application Window (Jendela Utama) untuk Py-SiteCheck
Mengatur switching antar view dan menghubungkan semua komponen.

File ini adalah "pengontrol utama" (controller) yang:
1. Menginisialisasi semua komponen (monitor, sidebar, views, status bar)
2. Menangani navigasi antar halaman (Dashboard → Sites → Alerts → Settings)
3. Menghubungkan event dari background thread ke GUI (thread-safe update)
4. Mengelola penambahan/penghapusan website
"""

import customtkinter as ctk        # Library GUI modern berbasis Tkinter
from typing import Optional        # Type hint untuk parameter opsional
import threading                    # Untuk operasi multi-threading

# Import komponen dari file-file dalam package gui/
from .theme import COLORS, FONTS, SIZES
from .components import SiteCard, AddURLDialog, Sidebar, StatusBar
from .views import SitesView, AlertsView, SettingsView

# Import dari package core/
from core.monitor import SiteMonitor, SiteStatus, AlertEntry
from core.utils import validate_url, extract_domain


# ══════════════════════════════════════════════════════
# CLASS UTAMA: PySiteCheckApp
# Jendela utama aplikasi yang mengatur semuanya
# ══════════════════════════════════════════════════════

class PySiteCheckApp(ctk.CTk):
    """
    Kelas jendela utama aplikasi Py-SiteCheck.
    Mewarisi ctk.CTk (CustomTkinter root window).

    Arsitektur:
    ┌──────────────────────────────────────────────┐
    │  [Sidebar]  │  [Main Content Area]           │
    │  Dashboard  │  ┌──────────────────────────┐  │
    │  Sites      │  │  View yang aktif:        │  │
    │  Alerts     │  │  - Dashboard (cards)     │  │
    │  Settings   │  │  - Sites (table)         │  │
    │             │  │  - Alerts (log)          │  │
    │             │  │  - Settings (config)     │  │
    │             │  └──────────────────────────┘  │
    │             │  [Status Bar]                   │
    └──────────────────────────────────────────────┘
    """

    def __init__(self):
        super().__init__()  # Inisialisasi window Tkinter

        # ── Konfigurasi Window ──
        self.title("Py-SiteCheck - Web Availability Monitor")
        self.geometry("1100x700")   # Ukuran awal: 1100×700 pixel
        self.minsize(900, 600)      # Ukuran minimum (tidak bisa lebih kecil)

        # ── Pengaturan Tema ──
        ctk.set_appearance_mode("dark")           # Mode gelap
        ctk.set_default_color_theme("dark-blue")  # Tema warna biru gelap (bawaan CTk)

        # Warna background window utama
        self.configure(fg_color=COLORS["bg_dark"])

        # ── Inisialisasi Monitor (Core Logic) ──
        # SiteMonitor adalah kelas yang menjalankan pengecekan website di background
        self.monitor = SiteMonitor(check_interval=30.0, timeout=10.0)

        # Mendaftarkan callback dari monitor ke GUI:
        # Setiap kali monitor selesai mengecek website → panggil _on_status_update
        self.monitor.add_callback(self._on_status_update)
        # Setiap kali ada perubahan status (online↔offline) → panggil _on_alert
        self.monitor.add_alert_callback(self._on_alert)

        # Dictionary untuk menyimpan kartu dashboard: URL → SiteCard widget
        self.site_cards: dict[str, SiteCard] = {}

        # Melacak view/halaman yang sedang aktif
        self.current_view = "dashboard"

        # ── Bangun UI ──
        self._setup_ui()

        # ── Tambah Website Default (untuk demo) ──
        self._add_default_sites()

        # ── Mulai Monitoring ──
        self.monitor.start_monitoring()  # Mulai thread background

        # ── Handle Tombol Close (X) ──
        # Saat user menutup window, kita perlu menghentikan thread monitoring dulu
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ────────────────────────────────────────────────────
    # SETUP UI: Membangun seluruh tampilan aplikasi
    # ────────────────────────────────────────────────────

    def _setup_ui(self):
        """Membangun layout utama UI dengan semua view"""

        # ── Konfigurasi Grid Layout ──
        # Kolom 0 = Sidebar (lebar tetap)
        # Kolom 1 = Main content (mengisi sisa ruang, weight=1)
        self.grid_columnconfigure(1, weight=1)
        # Baris 0 = Konten utama (mengisi sisa ruang vertikal)
        self.grid_rowconfigure(0, weight=1)

        # ── SIDEBAR (Kolom Kiri) ──
        # Navigasi menu: Dashboard, Sites, Alerts, Settings
        self.sidebar = Sidebar(self, on_nav_select=self._on_nav_select)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        # rowspan=2 = sidebar meluas ke 2 baris (konten + status bar)
        # sticky="nsew" = menempel ke semua sisi (north, south, east, west)

        # ── MAIN CONTENT AREA (Kolom Kanan) ──
        # Container untuk semua view (hanya satu yang terlihat pada satu waktu)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # ══ MEMBUAT SEMUA VIEW ══
        # Semua view dibuat sekaligus, tapi hanya satu yang ditampilkan
        # Ini lebih efisien daripada membuat ulang view setiap kali pindah halaman
        self.views: dict[str, ctk.CTkFrame] = {}

        # ── VIEW 1: Dashboard ──
        # Menampilkan kartu status website dalam grid 3 kolom
        self.dashboard_view = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.dashboard_view.grid_columnconfigure(0, weight=1)
        self.dashboard_view.grid_rowconfigure(1, weight=1)
        self._create_header(self.dashboard_view)    # Header: judul + tombol Add URL
        self._create_dashboard(self.dashboard_view) # Area scrollable untuk kartu
        self.views["dashboard"] = self.dashboard_view

        # ── VIEW 2: Sites ──
        # Menampilkan website dalam format tabel detail
        self.sites_view = SitesView(
            self.main_frame,
            on_add_url=self._show_add_dialog,      # Callback saat tombol Add diklik
            on_delete_site=self._remove_site,       # Callback saat tombol Delete diklik
            on_refresh_site=self._refresh_site      # Callback saat tombol Refresh diklik
        )
        self.views["sites"] = self.sites_view

        # ── VIEW 3: Alerts ──
        # Menampilkan log alert perubahan status website
        self.alerts_view = AlertsView(
            self.main_frame,
            on_clear_alerts=self._clear_alerts      # Callback saat Clear All diklik
        )
        self.views["alerts"] = self.alerts_view

        # ── VIEW 4: Settings ──
        # Pengaturan interval, timeout, dan kontrol monitoring
        self.settings_view = SettingsView(
            self.main_frame,
            monitor=self.monitor,                    # Referensi ke SiteMonitor
            on_status_bar_update=self._update_status_bar  # Callback untuk update status bar
        )
        self.views["settings"] = self.settings_view

        # Tampilkan Dashboard sebagai halaman default
        self._show_view("dashboard")

        # ── STATUS BAR (Baris Bawah) ──
        # Menampilkan: "● Monitoring Active" + "3 sites monitored"
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=1, sticky="ew")

    def _create_header(self, parent):
        """Membuat bagian header Dashboard (judul + tombol Add URL)"""

        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))
        header_frame.grid_columnconfigure(0, weight=1)

        # ── Section judul ──
        title_section = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_section.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_section,
            text="Dashboard",
            font=(FONTS["family"], FONTS["title_size"], "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_section,
            text="Monitor your websites in real-time",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(4, 0))

        # ── Tombol Add URL ──
        self.add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add URL",
            font=(FONTS["family"], FONTS["body_size"], "bold"),
            height=40,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_primary"],
            corner_radius=8,
            command=self._show_add_dialog
        )
        self.add_btn.grid(row=0, column=1, sticky="e")  # Ditaruh di kanan

    def _create_dashboard(self, parent):
        """Membuat area konten Dashboard (grid kartu website yang bisa di-scroll)"""

        # Frame scrollable untuk menampung kartu-kartu website
        self.dashboard_frame = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["border_light"]
        )
        self.dashboard_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))

        # Konfigurasi grid 3 kolom (kartu tersusun dalam 3 kolom)
        # uniform="card" memastikan ketiga kolom punya lebar yang sama
        self.dashboard_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="card")

        # ── Pesan kosong (empty state) ──
        # Muncul saat belum ada website yang ditambahkan
        self.empty_label = ctk.CTkLabel(
            self.dashboard_frame,
            text="No websites added yet.\nClick '+ Add URL' to start monitoring.",
            font=(FONTS["family"], FONTS["body_size"]),
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self.empty_label.grid(row=0, column=0, columnspan=3, pady=100)

    # ────────────────────────────────────────────────────
    # VIEW SWITCHING: Pindah antar halaman
    # ────────────────────────────────────────────────────

    def _show_view(self, view_id: str):
        """
        Menampilkan view yang dipilih dan menyembunyikan view lainnya.

        Mekanisme: hanya view aktif yang di-grid() (terlihat),
        view lainnya di-grid_forget() (tersembunyi tapi tetap ada di memori).

        Args:
            view_id: ID view yang akan ditampilkan ("dashboard", "sites", "alerts", "settings")
        """
        for vid, view in self.views.items():
            if vid == view_id:
                view.grid(row=0, column=0, sticky="nsew")  # TAMPILKAN
            else:
                view.grid_forget()                           # SEMBUNYIKAN
        self.current_view = view_id

    def _on_nav_select(self, nav_id: str):
        """
        Handler saat tombol navigasi di sidebar diklik.
        Dipanggil oleh Sidebar._on_nav_click()

        Args:
            nav_id: ID navigasi yang dipilih ("dashboard", "sites", "alerts", "settings")
        """
        self._show_view(nav_id)       # Pindah ke view yang dipilih
        self._update_status_bar()     # Update status bar

    # ────────────────────────────────────────────────────
    # SITE MANAGEMENT: Menambah, menghapus, dan refresh website
    # ────────────────────────────────────────────────────

    def _add_default_sites(self):
        """Menambahkan website default untuk demonstrasi saat aplikasi pertama kali dibuka"""
        default_sites = [
            "https://www.google.com",     # Mesin pencari
            "https://www.github.com",     # Platform kode
            "https://www.ulbi.ac.id",     # Website kampus ULBI
        ]

        for url in default_sites:
            self._add_site(url)

    def _show_add_dialog(self):
        """Menampilkan dialog popup untuk menambahkan URL baru"""
        dialog = AddURLDialog(self, on_submit=self._add_site)
        dialog.wait_window()  # Tunggu sampai dialog ditutup (modal behavior)

    def _add_site(self, url: str):
        """
        Menambahkan website baru ke monitoring.
        Sinkronisasi antara Dashboard (kartu) DAN Sites view (tabel).

        Alur:
        1. Validasi URL
        2. Cek apakah sudah ada (hindari duplikat)
        3. Buat kartu di Dashboard
        4. Tambah baris di Sites view
        5. Daftarkan ke SiteMonitor (mulai pencheckan)
        """
        # LANGKAH 1: Validasi URL menggunakan fungsi dari utils.py
        is_valid, result = validate_url(url)
        if not is_valid:
            return  # URL tidak valid, batalkan

        url = result  # Gunakan URL yang sudah dinormalisasi

        # LANGKAH 2: Cek duplikat
        if url in self.site_cards:
            return  # Sudah ada, tidak perlu ditambahkan lagi

        # LANGKAH 3: Sembunyikan pesan empty state
        self.empty_label.grid_forget()

        # LANGKAH 4: Buat kartu baru di Dashboard
        card = SiteCard(
            self.dashboard_frame,
            url=url,
            on_delete=self._remove_site,   # Callback tombol hapus
            on_refresh=self._refresh_site   # Callback tombol refresh
        )

        # Posisikan kartu dalam grid 3 kolom
        # Kartu ke-0,1,2 → baris 0, kolom 0,1,2
        # Kartu ke-3,4,5 → baris 1, kolom 0,1,2
        # dst...
        num_cards = len(self.site_cards)
        row = num_cards // 3   # Integer division (misal: 5 // 3 = 1)
        col = num_cards % 3    # Modulo/sisa bagi (misal: 5 % 3 = 2)
        card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        # Simpan referensi kartu
        self.site_cards[url] = card

        # LANGKAH 5: Tambah juga ke Sites view (tabel)
        self.sites_view.add_site_row(url)

        # LANGKAH 6: Daftarkan ke monitor untuk mulai dicek
        self.monitor.add_site(url)

        # Update jumlah website di status bar
        self._update_status_bar()

    def _remove_site(self, url: str):
        """
        Menghapus website dari monitoring.
        Sinkronisasi penghapusan di Dashboard + Sites view + Monitor.
        """
        if url in self.site_cards:
            # Hancurkan widget kartu di Dashboard
            self.site_cards[url].destroy()
            del self.site_cards[url]

            # Hapus baris di Sites view
            self.sites_view.remove_site_row(url)

            # Hapus dari monitor (berhenti dicek)
            self.monitor.remove_site(url)

            # Atur ulang posisi kartu yang tersisa di Dashboard
            self._reposition_cards()

            # Tampilkan pesan kosong jika tidak ada website lagi
            if not self.site_cards:
                self.empty_label.grid(row=0, column=0, columnspan=3, pady=100)

            # Update status bar
            self._update_status_bar()

    def _refresh_site(self, url: str):
        """Memaksa pengecekan ulang website tertentu (saat user klik tombol ↻)"""
        self.monitor.force_check(url)  # Jalankan pengecekan di thread baru

    def _reposition_cards(self):
        """
        Mengatur ulang posisi kartu di Dashboard setelah ada penghapusan.
        Kartu yang tersisa diposisikan ulang agar tidak ada celah kosong.
        """
        for i, (url, card) in enumerate(self.site_cards.items()):
            row = i // 3
            col = i % 3
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

    # ════════════════════════════════════════════════════
    # ★ THREAD-SAFE CALLBACKS ★
    # Menjembatani data dari background thread ke GUI thread
    # ════════════════════════════════════════════════════

    def _on_status_update(self, status: SiteStatus):
        """
        Callback saat status website diupdate oleh monitor.
        PENTING: Method ini dipanggil dari BACKGROUND THREAD (monitor thread)!

        GUI Tkinter TIDAK BOLEH diupdate langsung dari thread selain main thread.
        Solusi: gunakan self.after(0, func) untuk menjadwalkan update
        di main thread (event loop Tkinter).
        """
        # self.after(0, func) = "tolong jalankan func ini di main thread secepatnya"
        # lambda digunakan karena after() tidak menerima argumen untuk func
        self.after(0, lambda: self._update_card(status))

    def _update_card(self, status: SiteStatus):
        """
        Memperbarui tampilan kartu Dashboard DAN baris Sites view.
        Method ini berjalan di MAIN THREAD (aman untuk update GUI).
        """
        # Update kartu di Dashboard
        if status.url in self.site_cards:
            self.site_cards[status.url].update_status(
                is_online=status.is_online,
                status_code=status.status_code,
                latency_ms=status.latency_ms,
                port_open=status.port_open,
                port=status.port_checked,
                error_message=status.error_message
            )

        # Update baris di Sites view
        self.sites_view.update_site_row(
            url=status.url,
            is_online=status.is_online,
            status_code=status.status_code,
            latency_ms=status.latency_ms,
            port_open=status.port_open,
            port=status.port_checked,
            error_message=status.error_message
        )

    def _on_alert(self, alert: AlertEntry):
        """
        Callback saat alert baru dihasilkan (website berubah status).
        Sama seperti _on_status_update, dipanggil dari background thread
        dan harus dijadwalkan di main thread.
        """
        self.after(0, lambda: self.alerts_view.add_alert(alert))

    def _clear_alerts(self):
        """Menghapus semua alert dari monitor dan GUI"""
        self.monitor.clear_alerts()

    # ────────────────────────────────────────────────────
    # STATUS BAR
    # ────────────────────────────────────────────────────

    def _update_status_bar(self):
        """Memperbarui informasi di status bar (bawah window)"""
        self.status_bar.update_status(
            is_monitoring=self.monitor.is_running(),  # Apakah monitoring aktif?
            site_count=len(self.site_cards)            # Jumlah website
        )

    # ────────────────────────────────────────────────────
    # WINDOW MANAGEMENT: Pengelolaan jendela
    # ────────────────────────────────────────────────────

    def _on_close(self):
        """
        Handler saat user menutup window (klik tombol X).
        Melakukan graceful shutdown:
        1. Hentikan thread monitoring terlebih dahulu
        2. Baru hancurkan window

        Tanpa ini, thread background bisa terus berjalan
        meskipun window sudah ditutup.
        """
        self.monitor.stop_monitoring()  # Hentikan thread monitoring
        self.destroy()                   # Hancurkan window (tutup aplikasi)


# ══════════════════════════════════════════════════════
# FUNGSI ENTRY POINT
# Dipanggil oleh main.py untuk menjalankan aplikasi
# ══════════════════════════════════════════════════════

def run_app():
    """
    Titik masuk untuk menjalankan aplikasi.
    Membuat instance PySiteCheckApp dan memulai event loop GUI.

    Event loop (mainloop) = proses tak terbatas yang:
    1. Mendengarkan event (klik mouse, ketikan keyboard, timer, dll)
    2. Memanggil handler yang sesuai
    3. Merender ulang GUI jika ada perubahan
    4. Berhenti saat window ditutup
    """
    app = PySiteCheckApp()
    app.mainloop()  # Mulai event loop Tkinter (program berjalan di sini sampai ditutup)
