"""
Komponen GUI untuk Py-SiteCheck
Widget kustom dengan styling modern menggunakan CustomTkinter.

File ini berisi widget-widget yang digunakan ulang (reusable) di seluruh aplikasi:
- SiteCard: Kartu status website di Dashboard
- AddURLDialog: Dialog popup untuk menambahkan URL baru
- Sidebar: Menu navigasi di sisi kiri
- StatusBar: Bar informasi di bagian bawah window
"""

import customtkinter as ctk      # Library GUI modern berbasis Tkinter
from typing import Callable, Optional  # Type hints untuk dokumentasi tipe parameter
import time                       # Untuk operasi waktu

# Import konfigurasi tema dari file theme.py
from .theme import COLORS, FONTS, SIZES, get_status_code_color


# ══════════════════════════════════════════════════════
# KOMPONEN 1: SiteCard
# Kartu yang menampilkan status website di halaman Dashboard
# Setiap website yang dimonitor punya satu kartu
# ══════════════════════════════════════════════════════

class SiteCard(ctk.CTkFrame):
    """
    Widget kartu yang menampilkan informasi status website.
    Menampilkan: URL, indikator online/offline, response time, port status, dan HTTP status code.

    Mewarisi (inheritance) dari CTkFrame - jadi SiteCard adalah Frame dengan fitur tambahan.
    """

    def __init__(
        self,
        master,                                            # Widget parent (tempat card ini ditaruh)
        url: str,                                          # URL website yang ditampilkan
        on_delete: Optional[Callable[[str], None]] = None, # Fungsi yang dipanggil saat tombol hapus diklik
        on_refresh: Optional[Callable[[str], None]] = None, # Fungsi yang dipanggil saat tombol refresh diklik
        **kwargs                                           # Parameter tambahan untuk CTkFrame
    ):
        # Memanggil constructor parent (CTkFrame) dengan styling card
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],          # Warna background card
            corner_radius=SIZES["card_radius"],   # Sudut card membulat (12px)
            border_width=1,                       # Ketebalan garis tepi
            border_color=COLORS["border"],        # Warna garis tepi
            **kwargs
        )

        # Simpan data ke instance variables
        self.url = url                # URL website
        self.on_delete = on_delete    # Callback fungsi hapus
        self.on_refresh = on_refresh  # Callback fungsi refresh

        self._setup_ui()         # Bangun tampilan UI
        self._set_default_state() # Set kondisi awal (Checking...)

    def _setup_ui(self):
        """Menyusun tampilan layout kartu menggunakan grid"""

        # Kolom 0 (satu-satunya) akan mengisi seluruh lebar
        self.grid_columnconfigure(0, weight=1)

        # ── BARIS 0: Header (Status Indicator + URL + Tombol Hapus) ──
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=SIZES["card_padding"], pady=(SIZES["card_padding"], 8))
        header_frame.grid_columnconfigure(1, weight=1)  # Kolom URL mengisi sisa ruang

        # Indikator status (titik bulat berwarna: hijau=online, merah=offline, abu=checking)
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text="●",                                  # Karakter titik bulat
            font=(FONTS["family"], 16),
            text_color=COLORS["text_muted"],            # Default: abu-abu (belum dicek)
            width=20
        )
        self.status_indicator.grid(row=0, column=0, padx=(0, 8))

        # Label URL (dipotong jika terlalu panjang agar muat di card)
        display_url = self.url
        if len(display_url) > 28:
            display_url = display_url[:25] + "..."  # Potong dan tambahkan "..."

        self.url_label = ctk.CTkLabel(
            header_frame,
            text=display_url,
            font=(FONTS["family"], FONTS["body_size"], "bold"),  # Bold agar menonjol
            text_color=COLORS["text_primary"],
            anchor="w"  # Align ke kiri (west)
        )
        self.url_label.grid(row=0, column=1, sticky="w")

        # Tombol hapus (×) - menghapus website dari monitoring
        self.delete_btn = ctk.CTkButton(
            header_frame,
            text="×",                              # Simbol silang
            width=28, height=28,                   # Ukuran kecil (kotak 28x28)
            font=(FONTS["family"], 16),
            fg_color="transparent",                 # Background transparan (tidak terlihat)
            hover_color=COLORS["error"],            # Merah saat mouse hover
            text_color=COLORS["text_muted"],
            corner_radius=6,
            command=self._on_delete_click           # Panggil fungsi ini saat diklik
        )
        self.delete_btn.grid(row=0, column=2)

        # ── BARIS 1: Response Time / Latency ──
        response_frame = ctk.CTkFrame(self, fg_color="transparent")
        response_frame.grid(row=1, column=0, sticky="ew", padx=SIZES["card_padding"], pady=4)

        ctk.CTkLabel(
            response_frame, text="⏱",              # Emoji stopwatch
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        ctk.CTkLabel(
            response_frame, text=" Response: ",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        # Label yang menampilkan nilai latency (akan diupdate secara dinamis)
        self.latency_label = ctk.CTkLabel(
            response_frame,
            text="-- ms",                           # Default: belum ada data
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_secondary"]
        )
        self.latency_label.pack(side="left")

        # ── BARIS 2: Port Status ──
        port_frame = ctk.CTkFrame(self, fg_color="transparent")
        port_frame.grid(row=2, column=0, sticky="ew", padx=SIZES["card_padding"], pady=4)

        ctk.CTkLabel(
            port_frame, text="🔌",                  # Emoji colokan listrik (representasi port)
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        ctk.CTkLabel(
            port_frame, text=" Port: ",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        # Label port (akan diupdate, misal "443 (Open)" atau "80 (Closed)")
        self.port_label = ctk.CTkLabel(
            port_frame,
            text="--",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_secondary"]
        )
        self.port_label.pack(side="left")

        # ── BARIS 3: HTTP Status Badge + Tombol Refresh ──
        badge_frame = ctk.CTkFrame(self, fg_color="transparent")
        badge_frame.grid(row=3, column=0, sticky="ew", padx=SIZES["card_padding"], pady=(8, SIZES["card_padding"]))

        # Badge status HTTP (label dengan background berwarna)
        # Contoh tampilan: [HTTP 200] berwarna hijau, atau [Connection failed] berwarna merah
        self.status_badge = ctk.CTkLabel(
            badge_frame,
            text="  Checking...  ",                 # Default: sedang mengecek
            font=(FONTS["family"], FONTS["small_size"], "bold"),
            fg_color=COLORS["bg_input"],            # Background abu-abu gelap
            corner_radius=6,
            text_color=COLORS["text_muted"],
            padx=8, pady=4
        )
        self.status_badge.pack(side="left")

        # Tombol refresh (↻) - memaksa pengecekan ulang segera
        self.refresh_btn = ctk.CTkButton(
            badge_frame,
            text="↻",                               # Simbol refresh
            width=28, height=28,
            font=(FONTS["family"], 14),
            fg_color="transparent",
            hover_color=COLORS["primary"],           # Ungu saat hover
            text_color=COLORS["text_muted"],
            corner_radius=6,
            command=self._on_refresh_click
        )
        self.refresh_btn.pack(side="right")

    def _set_default_state(self):
        """Set tampilan ke kondisi default (saat belum ada data / sedang checking)"""
        self.status_indicator.configure(text_color=COLORS["text_muted"])  # Abu-abu
        self.latency_label.configure(text="-- ms")
        self.port_label.configure(text="--")
        self.status_badge.configure(
            text="  Checking...  ",
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_muted"]
        )

    def update_status(
        self,
        is_online: bool,         # Website online?
        status_code: int,        # HTTP status code (200, 404, -1, dll)
        latency_ms: float,       # Waktu respons dalam ms
        port_open: bool,         # Port TCP terbuka?
        port: int,               # Nomor port yang dicek
        error_message: str = ""  # Pesan error jika gagal
    ):
        """
        Memperbarui tampilan kartu dengan data status terbaru.
        Method ini dipanggil setiap kali monitor selesai mengecek website ini.
        """

        # ── Update warna indikator status (●) ──
        if status_code < 0:
            # Status code negatif = gagal total (tidak bisa connect sama sekali)
            indicator_color = COLORS["error"]       # Merah
        elif is_online:
            indicator_color = COLORS["success"]     # Hijau (200-399)
        else:
            # Tidak online tapi ada status code → cek lebih detail
            indicator_color = COLORS["warning"] if 300 <= status_code < 400 else COLORS["error"]

        self.status_indicator.configure(text_color=indicator_color)

        # ── Update teks latency ──
        if latency_ms >= 0:
            if latency_ms < 1000:
                latency_text = f"{latency_ms:.0f} ms"      # Misal: "250 ms"
            else:
                latency_text = f"{latency_ms/1000:.2f} s"    # Misal: "1.50 s" (lebih dari 1 detik)
        else:
            latency_text = "Timeout"                          # Tidak dapat latency
        self.latency_label.configure(text=latency_text)

        # ── Update status port ──
        port_status = f"{port} ({'Open' if port_open else 'Closed'})"  # Misal: "443 (Open)"
        port_color = COLORS["success"] if port_open else COLORS["error"]
        self.port_label.configure(text=port_status, text_color=port_color)

        # ── Update badge HTTP status ──
        if status_code < 0:
            badge_text = f"  {error_message or 'Error'}  "  # Misal: "Connection failed"
            badge_color = COLORS["error"]                     # Merah
        else:
            badge_text = f"  HTTP {status_code}  "            # Misal: "HTTP 200"
            badge_color = get_status_code_color(status_code)  # Warna sesuai kode

        self.status_badge.configure(
            text=badge_text,
            fg_color=badge_color,                             # Background badge berwarna
            text_color=COLORS["text_primary"]                 # Teks putih
        )

    def _on_delete_click(self):
        """Handler saat tombol hapus (×) diklik"""
        if self.on_delete:
            self.on_delete(self.url)  # Panggil callback dengan URL sebagai argumen

    def _on_refresh_click(self):
        """Handler saat tombol refresh (↻) diklik"""
        self._set_default_state()     # Reset tampilan ke "Checking..."
        if self.on_refresh:
            self.on_refresh(self.url)  # Panggil callback untuk force check


# ══════════════════════════════════════════════════════
# KOMPONEN 2: AddURLDialog
# Dialog popup modal untuk memasukkan URL baru
# ══════════════════════════════════════════════════════

class AddURLDialog(ctk.CTkToplevel):
    """
    Jendela dialog modal untuk menambahkan URL website baru ke monitoring.
    Mewarisi CTkToplevel (jendela terpisah dari window utama).

    Modal = user HARUS menutup dialog ini dulu sebelum bisa berinteraksi
    dengan window utama lagi.
    """

    def __init__(self, master, on_submit: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)

        self.on_submit = on_submit  # Fungsi yang dipanggil saat URL di-submit
        self.result = None          # Menyimpan URL yang dimasukkan

        # ── Konfigurasi Window Dialog ──
        self.title("Add Website")
        self.geometry("450x200")           # Ukuran dialog 450×200 pixel
        self.resizable(False, False)       # Tidak bisa di-resize

        # transient(master) = dialog selalu muncul DI ATAS window utama
        self.transient(master)
        # grab_set() = membuat dialog MODAL (tidak bisa klik window lain)
        self.grab_set()

        # Warna background dialog
        self.configure(fg_color=COLORS["bg_dark"])

        self._setup_ui()

        # Fokuskan kursor ke input field (agar bisa langsung mengetik)
        self.url_entry.focus_set()

        # ── Keyboard Shortcuts ──
        self.bind("<Return>", lambda e: self._on_submit())  # Enter = submit
        self.bind("<Escape>", lambda e: self.destroy())     # Esc = cancel/tutup

    def _setup_ui(self):
        """Menyusun tampilan dialog"""

        # Container utama dengan padding
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=24)

        # Judul dialog
        ctk.CTkLabel(
            container,
            text="Add Website to Monitor",
            font=(FONTS["family"], FONTS["heading_size"], "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")  # anchor="w" = rata kiri (west)

        # Subjudul/instruksi
        ctk.CTkLabel(
            container,
            text="Enter the URL of the website you want to monitor",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(4, 16))

        # ── Input field untuk URL ──
        self.url_entry = ctk.CTkEntry(
            container,
            placeholder_text="https://example.com",  # Teks placeholder (hilang saat mengetik)
            font=(FONTS["family"], FONTS["body_size"]),
            height=SIZES["input_height"],
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"]
        )
        self.url_entry.pack(fill="x", pady=(0, 16))  # fill="x" = lebar mengikuti container

        # Label error (tersembunyi secara default, muncul saat validasi gagal)
        self.error_label = ctk.CTkLabel(
            container,
            text="",  # Kosong by default
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["error"]  # Merah
        )
        self.error_label.pack(anchor="w")

        # ── Frame tombol (Cancel + Add Website) ──
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8, 0))

        # Tombol Cancel
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=(FONTS["family"], FONTS["body_size"]),
            height=SIZES["button_height"],
            fg_color="transparent",                     # Background transparan
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_secondary"],
            border_width=1,                             # Border tipis
            border_color=COLORS["border"],
            command=self.destroy                        # Tutup dialog saat diklik
        ).pack(side="right", padx=(8, 0))

        # Tombol Add Website
        ctk.CTkButton(
            btn_frame,
            text="Add Website",
            font=(FONTS["family"], FONTS["body_size"]),
            height=SIZES["button_height"],
            fg_color=COLORS["primary"],                 # Background ungu
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_primary"],
            command=self._on_submit
        ).pack(side="right")

    def _on_submit(self):
        """Handler saat user menekan tombol Add atau tekan Enter"""
        url = self.url_entry.get().strip()  # Ambil teks dari input, hapus spasi

        # Validasi: URL tidak boleh kosong
        if not url:
            self.error_label.configure(text="Please enter a URL")
            return

        # Normalisasi: tambahkan https:// jika belum ada
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        self.result = url
        self.on_submit(url)  # Panggil callback dengan URL
        self.destroy()        # Tutup dialog


# ══════════════════════════════════════════════════════
# KOMPONEN 3: Sidebar
# Menu navigasi di sisi kiri aplikasi
# ══════════════════════════════════════════════════════

class Sidebar(ctk.CTkFrame):
    """
    Komponen navigasi sidebar di sisi kiri window.
    Berisi tombol-tombol menu: Dashboard, Sites, Alerts, Settings.
    """

    def __init__(self, master, on_nav_select: Callable[[str], None], **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_sidebar"],          # Warna background sidebar
            corner_radius=0,                         # Tanpa sudut membulat (persegi)
            width=SIZES["sidebar_width"],            # Lebar 200px
            **kwargs
        )

        self.on_nav_select = on_nav_select  # Callback saat menu diklik
        self.active_nav = "dashboard"        # Menu yang sedang aktif
        self.nav_buttons = {}                # Dictionary menyimpan referensi tombol

        self._setup_ui()

    def _setup_ui(self):
        """Menyusun tampilan sidebar"""

        # Mencegah frame mengecil mengikuti konten di dalamnya
        self.grid_propagate(False)

        # ── Logo / Judul Aplikasi ──
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=20)

        ctk.CTkLabel(
            title_frame,
            text="🌐 Py-SiteCheck",                  # Logo + nama aplikasi
            font=(FONTS["family"], FONTS["heading_size"], "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Web Availability Monitor",          # Tagline
            font=(FONTS["family"], FONTS["tiny_size"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(2, 0))

        # ── Menu Navigasi ──
        # Daftar item navigasi: (id, emoji, label)
        nav_items = [
            ("dashboard", "📊", "Dashboard"),   # Ringkasan status dalam kartu
            ("sites", "🌍", "Sites"),            # Tabel detail semua website
            ("alerts", "🔔", "Alerts"),          # Log alert perubahan status
            ("settings", "⚙️", "Settings"),      # Pengaturan monitoring
        ]

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=8)

        # Buat tombol untuk setiap item navigasi
        for nav_id, icon, label in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icon}  {label}",
                font=(FONTS["family"], FONTS["body_size"]),
                height=40,
                anchor="w",                                     # Teks rata kiri
                # Tombol aktif = warna ungu, tombol tidak aktif = transparan
                fg_color=COLORS["primary"] if nav_id == self.active_nav else "transparent",
                hover_color=COLORS["bg_card_hover"],
                text_color=COLORS["text_primary"],
                corner_radius=8,
                # lambda dengan default argument (nid=nav_id) untuk menangkap nilai nav_id
                # Tanpa ini, semua tombol akan memanggil callback dengan nav_id terakhir ("settings")
                command=lambda nid=nav_id: self._on_nav_click(nid)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[nav_id] = btn  # Simpan referensi untuk update styling nanti

        # ── Versi Aplikasi (di bagian bawah sidebar) ──
        version_label = ctk.CTkLabel(
            self,
            text="v1.0.0",
            font=(FONTS["family"], FONTS["tiny_size"]),
            text_color=COLORS["text_muted"]
        )
        version_label.pack(side="bottom", pady=16)  # Ditaruh di bottom sidebar

    def _on_nav_click(self, nav_id: str):
        """
        Handler saat tombol navigasi diklik.
        Mengupdate tampilan tombol (aktif/tidak aktif) dan memberi tahu app.py.
        """
        # Update styling semua tombol
        for nid, btn in self.nav_buttons.items():
            if nid == nav_id:
                btn.configure(fg_color=COLORS["primary"])    # Aktif = background ungu
            else:
                btn.configure(fg_color="transparent")         # Tidak aktif = transparan

        self.active_nav = nav_id
        self.on_nav_select(nav_id)  # Panggil callback → app.py._on_nav_select()


# ══════════════════════════════════════════════════════
# KOMPONEN 4: StatusBar
# Bar informasi di bagian bawah window
# ══════════════════════════════════════════════════════

class StatusBar(ctk.CTkFrame):
    """
    Bar status di bagian bawah window.
    Menampilkan dua informasi:
    - Kiri: Status monitoring (aktif/paused)
    - Kanan: Jumlah website yang dimonitor
    """

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_sidebar"],  # Warna sama dengan sidebar
            corner_radius=0,
            height=32,                       # Tinggi 32px (tipis)
            **kwargs
        )

        self._setup_ui()

    def _setup_ui(self):
        """Menyusun tampilan status bar"""
        self.grid_propagate(False)  # Mencegah bar mengecil

        # ── Sisi Kiri: Status Monitoring ──
        self.status_label = ctk.CTkLabel(
            self,
            text="● Monitoring Active",              # Default: aktif
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["success"]              # Hijau
        )
        self.status_label.pack(side="left", padx=16)

        # ── Sisi Kanan: Jumlah Website ──
        self.site_count_label = ctk.CTkLabel(
            self,
            text="0 sites monitored",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        )
        self.site_count_label.pack(side="right", padx=16)

    def update_status(self, is_monitoring: bool, site_count: int):
        """
        Memperbarui tampilan status bar.

        Args:
            is_monitoring: Apakah monitoring sedang aktif?
            site_count: Jumlah website yang dimonitor
        """
        if is_monitoring:
            self.status_label.configure(
                text="● Monitoring Active",        # Titik penuh + teks
                text_color=COLORS["success"]        # Hijau
            )
        else:
            self.status_label.configure(
                text="○ Monitoring Paused",         # Titik kosong + teks
                text_color=COLORS["text_muted"]     # Abu-abu
            )

        # Update jumlah website (dengan handling singular/plural)
        self.site_count_label.configure(
            text=f"{site_count} site{'s' if site_count != 1 else ''} monitored"
            # 1 site monitored / 3 sites monitored
        )
