"""
Utility Functions (Fungsi Utilitas) untuk Py-SiteCheck
Berisi fungsi-fungsi helper yang digunakan di berbagai bagian aplikasi.
"""

from urllib.parse import urlparse  # Untuk mengurai URL menjadi komponen (scheme, host, path, dll)
import re  # Module Regular Expression untuk validasi pola teks (misal: format domain)

# ══════════════════════════════════════════════════════
# DAFTAR HTTP STATUS CODE
# Mapping kode HTTP ke deskripsi yang mudah dipahami manusia
# Referensi: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
# ══════════════════════════════════════════════════════

STATUS_CODES = {
    # 2xx - Success (Berhasil)
    200: "OK",              # Request berhasil, server mengirimkan respons
    201: "Created",         # Resource baru berhasil dibuat (biasanya untuk POST)
    204: "No Content",      # Berhasil tapi tidak ada konten untuk dikirimkan

    # 3xx - Redirection (Pengalihan)
    301: "Moved Permanently",  # URL sudah pindah permanen ke URL baru
    302: "Found",              # URL sementara dialihkan ke URL lain
    304: "Not Modified",       # Konten tidak berubah sejak request terakhir (cache)

    # 4xx - Client Error (Kesalahan dari sisi client/pengguna)
    400: "Bad Request",        # Server tidak mengerti request yang dikirim
    401: "Unauthorized",       # Perlu autentikasi (login) untuk mengakses
    403: "Forbidden",          # Akses ditolak walaupun sudah login
    404: "Not Found",          # Halaman/resource yang diminta tidak ditemukan
    405: "Method Not Allowed", # Metode HTTP (GET/POST/dll) tidak diizinkan
    408: "Request Timeout",    # Server terlalu lama menunggu request dari client
    429: "Too Many Requests",  # Terlalu banyak request (rate limiting)

    # 5xx - Server Error (Kesalahan dari sisi server)
    500: "Internal Server Error",  # Kesalahan internal di server
    502: "Bad Gateway",            # Server perantara mendapat respons invalid
    503: "Service Unavailable",    # Server sedang overload atau maintenance
    504: "Gateway Timeout",        # Server perantara tidak mendapat respons tepat waktu
}


def get_status_description(code: int) -> str:
    """
    Mendapatkan deskripsi yang mudah dipahami dari HTTP status code.

    Contoh:
        get_status_description(200) → "OK"
        get_status_description(404) → "Not Found"
        get_status_description(999) → "Unknown Status"
    """
    return STATUS_CODES.get(code, "Unknown Status")


def validate_url(url: str) -> tuple[bool, str]:
    """
    Memvalidasi dan menormalisasi URL yang dimasukkan user.

    Proses validasi:
    1. Hapus spasi di awal/akhir
    2. Tambahkan "https://" jika belum ada scheme
    3. Parse URL dan periksa apakah ada domain
    4. Validasi format domain dengan regex

    Args:
        url: URL yang akan divalidasi (contoh: "google.com" atau "https://google.com")

    Returns:
        Tuple (is_valid, result):
        - Jika valid: (True, "https://google.com") → URL yang sudah dinormalisasi
        - Jika tidak valid: (False, "Invalid URL: pesan error")
    """
    url = url.strip()  # Hapus spasi/whitespace di awal dan akhir

    # Tambahkan scheme https:// jika user tidak mengetikkannya
    # Misal user input "google.com" → menjadi "https://google.com"
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        # Parse URL menjadi komponen-komponen
        # urlparse("https://google.com/search") menghasilkan:
        # - scheme: "https"
        # - netloc: "google.com"   (ini yang kita butuhkan)
        # - path: "/search"
        parsed = urlparse(url)

        # Cek apakah ada domain/netloc
        if not parsed.netloc:
            return False, "Invalid URL: No domain found"

        # Validasi format domain menggunakan Regular Expression (Regex)
        # Domain yang valid:
        # - Dimulai dengan huruf/angka
        # - Boleh mengandung huruf, angka, dan tanda hubung (-)
        # - Dipisahkan oleh titik (.) untuk subdomain/TLD
        # Contoh valid: "google.com", "api.github.com", "my-site.co.id"
        # Contoh invalid: "-invalid.com", "!!!.com"
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        domain = parsed.netloc.split(':')[0]  # Hapus port jika ada (misal "example.com:8080" → "example.com")

        if not re.match(domain_pattern, domain):
            return False, f"Invalid domain: {domain}"

        return True, url  # URL valid! Return URL yang sudah dinormalisasi

    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def extract_domain(url: str) -> str:
    """
    Mengekstrak nama domain dari URL.

    Contoh:
        extract_domain("https://www.google.com/search?q=test") → "www.google.com"
        extract_domain("http://example.com:8080/path")         → "example.com:8080"
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc or url  # Kembalikan netloc, atau URL asli jika parsing gagal
    except:
        return url


def get_port_from_url(url: str) -> int:
    """
    Mendapatkan port yang sesuai dari URL.
    HTTPS menggunakan port 443, HTTP menggunakan port 80.

    Contoh:
        get_port_from_url("https://google.com")       → 443
        get_port_from_url("http://example.com")        → 80
        get_port_from_url("https://api.com:8443")      → 8443  (port custom)
    """
    try:
        parsed = urlparse(url)
        if parsed.port:
            return parsed.port       # Gunakan port custom jika ada di URL
        return 443 if parsed.scheme == 'https' else 80  # Default: HTTPS=443, HTTP=80
    except:
        return 443  # Fallback ke port HTTPS


def format_latency(latency_ms: float) -> str:
    """
    Memformat angka latency agar mudah dibaca manusia.

    Contoh:
        format_latency(-1)   → "N/A"        (gagal/tidak tersedia)
        format_latency(250)  → "250 ms"     (cepat, dalam milidetik)
        format_latency(1500) → "1.50 s"     (lambat, dikonversi ke detik)
    """
    if latency_ms < 0:
        return "N/A"                           # Tidak tersedia (gagal)
    elif latency_ms < 1000:
        return f"{latency_ms:.0f} ms"          # Tampilkan dalam milidetik (tanpa desimal)
    else:
        return f"{latency_ms/1000:.2f} s"      # Konversi ke detik (2 desimal)


def get_status_color(status_code: int) -> str:
    """
    Mendapatkan nama warna berdasarkan HTTP status code.
    Digunakan untuk pewarnaan indikator status.

    - 2xx (200-299) → hijau (sukses, website online)
    - 3xx (300-399) → kuning (redirect, masih dianggap OK)
    - 4xx, 5xx, <0  → merah (error client/server, atau gagal koneksi)
    """
    if 200 <= status_code < 300:
        return "green"    # Success
    elif 300 <= status_code < 400:
        return "yellow"   # Redirect
    elif status_code < 0:
        return "red"      # Connection failed
    else:
        return "red"      # Client/Server error (4xx/5xx)
