"""
Konfigurasi Tema (Theme) untuk GUI Py-SiteCheck
Mendefinisikan semua warna, font, ukuran, dan animasi yang digunakan di seluruh aplikasi.

File ini berfungsi sebagai "Design System" — semua konstanta visual ada di satu tempat.
Kalau ingin mengubah tampilan aplikasi (misal ganti warna), cukup ubah file ini saja.
"""

# ══════════════════════════════════════════════════════
# PALET WARNA (Color Palette)
# Menggunakan format HEX (#RRGGBB)
# Tema: Dark mode dengan aksen ungu dan cyan
# ══════════════════════════════════════════════════════

COLORS = {
    # ── Warna Utama (Primary) ──
    # Digunakan untuk tombol utama, navigasi aktif, dan elemen interaktif utama
    "primary": "#8B5CF6",         # Ungu - warna brand utama
    "primary_hover": "#7C3AED",   # Ungu lebih gelap - saat mouse hover di tombol
    "primary_light": "#A78BFA",   # Ungu lebih terang - untuk aksen/highlight

    # ── Warna Sekunder (Secondary) ──
    # Digunakan untuk elemen pendukung (misal slider timeout)
    "secondary": "#06B6D4",       # Cyan/biru muda
    "secondary_hover": "#0891B2", # Cyan lebih gelap saat hover

    # ── Warna Background ──
    # Gradasi gelap dari paling gelap (bg_dark) ke paling terang (bg_input)
    "bg_dark": "#0F0F1A",        # Background utama aplikasi (paling gelap)
    "bg_card": "#1A1A2E",        # Background card/kartu (sedikit lebih terang)
    "bg_card_hover": "#252542",  # Background card saat mouse hover
    "bg_sidebar": "#16162A",     # Background sidebar navigasi
    "bg_input": "#252542",       # Background text input dan slider

    # ── Warna Teks ──
    # Tiga tingkat kontras untuk hierarki informasi
    "text_primary": "#FFFFFF",    # Putih - teks utama (judul, konten penting)
    "text_secondary": "#A0A0B8",  # Abu-abu terang - teks sekunder (deskripsi)
    "text_muted": "#6B6B80",      # Abu-abu gelap - teks tidak terlalu penting (hint, placeholder)

    # ── Warna Status ──
    # Warna-warna untuk menunjukkan kondisi website
    "success": "#10B981",         # Hijau - website online / port terbuka
    "success_light": "#34D399",   # Hijau terang
    "warning": "#F59E0B",         # Kuning/Orange - redirect (301, 302)
    "warning_light": "#FBBF24",   # Kuning terang
    "error": "#EF4444",           # Merah - website offline / port tertutup / error
    "error_light": "#F87171",     # Merah terang

    # ── Warna Border (Garis Tepi) ──
    "border": "#2D2D44",          # Garis tepi normal (subtle, tidak terlalu terlihat)
    "border_light": "#3D3D5C",    # Garis tepi saat hover (sedikit lebih terang)

    # ── Warna Gradient ──
    # Untuk efek glassmorphism (transparan seperti kaca)
    "gradient_start": "#8B5CF6",  # Mulai dari ungu
    "gradient_end": "#06B6D4",    # Berakhir di cyan
}

# ══════════════════════════════════════════════════════
# KONFIGURASI FONT
# Menggunakan Segoe UI (font default Windows yang modern)
# ══════════════════════════════════════════════════════

FONTS = {
    "family": "Segoe UI",     # Nama font yang digunakan
    "title_size": 24,         # Ukuran judul halaman (misal "Dashboard", "Settings")
    "heading_size": 18,       # Ukuran heading/sub-judul (misal judul card)
    "body_size": 14,          # Ukuran teks biasa (konten, label)
    "small_size": 12,         # Ukuran teks kecil (keterangan, sub-info)
    "tiny_size": 10,          # Ukuran teks sangat kecil (footer, metadata)
}

# ══════════════════════════════════════════════════════
# KONFIGURASI UKURAN (Sizing)
# Dimensi komponen-komponen UI dalam pixel
# ══════════════════════════════════════════════════════

SIZES = {
    "sidebar_width": 200,     # Lebar sidebar navigasi (pixel)
    "card_width": 280,        # Lebar kartu website di dashboard
    "card_height": 140,       # Tinggi kartu website
    "card_padding": 16,       # Jarak konten dari tepi card (padding internal)
    "card_radius": 12,        # Radius sudut membulat pada card (border-radius)
    "button_height": 36,      # Tinggi tombol standar
    "input_height": 40,       # Tinggi input text
    "spacing_xs": 4,          # Jarak extra small (4px)
    "spacing_sm": 8,          # Jarak small (8px)
    "spacing_md": 16,         # Jarak medium (16px)
    "spacing_lg": 24,         # Jarak large (24px)
    "spacing_xl": 32,         # Jarak extra large (32px)
}

# ══════════════════════════════════════════════════════
# KONFIGURASI ANIMASI
# Durasi animasi dalam milidetik (ms)
# (Saat ini belum diimplementasikan penuh di CustomTkinter)
# ══════════════════════════════════════════════════════

ANIMATIONS = {
    "fast": 150,              # Animasi cepat (150ms) - untuk hover effect
    "normal": 300,            # Animasi normal (300ms) - untuk transisi
    "slow": 500,              # Animasi lambat (500ms) - untuk perubahan halaman
}


# ══════════════════════════════════════════════════════
# FUNGSI HELPER UNTUK WARNA STATUS
# ══════════════════════════════════════════════════════

def get_status_color(status: str) -> str:
    """
    Mendapatkan warna HEX berdasarkan string status.

    Args:
        status: String status ("online", "offline", "warning", "checking")

    Returns:
        Warna HEX yang sesuai (misal "#10B981" untuk online)
    """
    status_colors = {
        "online": COLORS["success"],       # Hijau
        "offline": COLORS["error"],        # Merah
        "warning": COLORS["warning"],      # Kuning
        "checking": COLORS["text_muted"],  # Abu-abu (sedang dicek)
    }
    return status_colors.get(status, COLORS["text_muted"])


def get_status_code_color(code: int) -> str:
    """
    Mendapatkan warna HEX berdasarkan HTTP status code.
    Digunakan untuk mewarnai badge status code di kartu website.

    Mapping:
        code < 0     → Merah (gagal koneksi, tidak dapat status code)
        200 - 299    → Hijau (sukses)
        300 - 399    → Kuning (redirect)
        400+         → Merah (client error / server error)

    Contoh:
        get_status_code_color(200) → "#10B981" (hijau)
        get_status_code_color(404) → "#EF4444" (merah)
        get_status_code_color(-1)  → "#EF4444" (merah)
    """
    if code < 0:
        return COLORS["error"]      # Merah - gagal total (tidak bisa connect)
    elif 200 <= code < 300:
        return COLORS["success"]    # Hijau - success (OK)
    elif 300 <= code < 400:
        return COLORS["warning"]    # Kuning - redirect
    else:
        return COLORS["error"]      # Merah - 4xx/5xx error
