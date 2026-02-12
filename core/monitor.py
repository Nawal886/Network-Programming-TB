"""
Site Monitor - Modul inti monitoring untuk Py-SiteCheck
Menangani HTTP requests, pengecekan port TCP, dan pengukuran latency.

File ini adalah INTI dari aspek Network Programming aplikasi ini.
Konsep yang digunakan: HTTP Protocol, TCP Socket, Multi-threading, Thread Safety.
"""

# ── Import Module ──
import socket       # Module bawaan Python untuk komunikasi jaringan level rendah (TCP/UDP socket)
import threading    # Module untuk menjalankan kode secara paralel (multi-threading)
import time         # Module untuk operasi waktu (mengukur latency, timestamp, delay)
from dataclasses import dataclass, field  # Untuk membuat class penyimpan data secara ringkas
from typing import Callable, Optional     # Type hints - penanda tipe data untuk dokumentasi
from urllib.parse import urlparse         # Untuk mem-parsing/mengurai URL menjadi komponen-komponennya

import requests     # Library pihak ketiga untuk mengirim HTTP request (pip install requests)


# ══════════════════════════════════════════════════════
# DATA CLASS: SiteStatus
# Menyimpan seluruh informasi status sebuah website
# ══════════════════════════════════════════════════════

@dataclass  # Dekorator yang otomatis membuat __init__, __repr__, dll
class SiteStatus:
    """Data class yang merepresentasikan status sebuah website yang dimonitor"""

    url: str                    # URL website (contoh: "https://google.com")
    is_online: bool = False     # Apakah website online? (True/False)
    status_code: int = -1       # HTTP status code (200=OK, 404=Not Found, -1=gagal)
    latency_ms: float = -1.0    # Waktu respons dalam milidetik (ms), -1 jika gagal
    port_open: bool = False     # Apakah port TCP terbuka? (True/False)
    port_checked: int = 443     # Port yang dicek (443 untuk HTTPS, 80 untuk HTTP)
    last_check: float = field(default_factory=time.time)  # Timestamp pengecekan terakhir
    error_message: str = ""     # Pesan error jika ada masalah

    def to_dict(self) -> dict:
        """Mengubah data ke bentuk dictionary (berguna untuk export/serialisasi)"""
        return {
            'url': self.url,
            'is_online': self.is_online,
            'status_code': self.status_code,
            'latency_ms': self.latency_ms,
            'port_open': self.port_open,
            'port_checked': self.port_checked,
            'last_check': self.last_check,
            'error_message': self.error_message
        }


# ══════════════════════════════════════════════════════
# DATA CLASS: AlertEntry
# Menyimpan data satu event alert (perubahan status website)
# ══════════════════════════════════════════════════════

@dataclass
class AlertEntry:
    """Data class yang merepresentasikan event alert (perubahan status)"""

    url: str              # URL website yang berubah status
    alert_type: str       # Tipe alert: "down" (mati) atau "recovered" (pulih)
    message: str          # Pesan deskripsi (contoh: "Site is back online (HTTP 200)")
    timestamp: float = field(default_factory=time.time)  # Waktu kejadian
    status_code: int = -1  # HTTP status code saat kejadian


# ══════════════════════════════════════════════════════
# CLASS UTAMA: SiteMonitor
# Kelas yang menjalankan semua logika monitoring website
# ══════════════════════════════════════════════════════

class SiteMonitor:
    """
    Memonitor ketersediaan website menggunakan HTTP requests dan koneksi TCP socket.
    Mendukung monitoring banyak URL secara paralel dengan threading.

    Alur kerja:
    1. User menambahkan URL via add_site()
    2. start_monitoring() memulai thread background
    3. Thread background menjalankan _monitor_loop() → cek semua site setiap interval
    4. Setiap ada update, callback dipanggil untuk memperbarui GUI
    """

    def __init__(self, check_interval: float = 30.0, timeout: float = 10.0):
        """
        Inisialisasi Site Monitor.

        Args:
            check_interval: Jeda waktu antar pengecekan dalam detik (default: 30 detik)
            timeout: Batas waktu tunggu respons dari server dalam detik (default: 10 detik)
        """
        self.check_interval = check_interval  # Seberapa sering cek (detik)
        self.timeout = timeout                # Batas waktu tunggu respons (detik)

        # Dictionary untuk menyimpan status semua website yang dimonitor
        # Key: URL (string), Value: objek SiteStatus
        self.sites: dict[str, SiteStatus] = {}

        # ── Callback System ──
        # Callback = fungsi yang akan dipanggil saat ada event tertentu
        # GUI mendaftarkan fungsinya di sini agar bisa update tampilan saat data berubah
        self._callbacks: list[Callable[[SiteStatus], None]] = []       # Callback untuk update status
        self._alert_callbacks: list[Callable] = []                     # Callback untuk alert baru
        self._alerts: list[AlertEntry] = []                            # Riwayat semua alert
        self._previous_states: dict[str, bool] = {}  # Menyimpan status sebelumnya tiap URL
                                                      # Digunakan untuk mendeteksi PERUBAHAN status

        # ── Threading Control ──
        self._running = False                              # Flag: apakah monitoring sedang aktif?
        self._monitor_thread: Optional[threading.Thread] = None  # Referensi ke thread background
        self._lock = threading.Lock()  # Lock untuk thread safety
        # Lock mencegah 2 thread mengakses/mengubah self.sites secara bersamaan
        # Tanpa lock, bisa terjadi "race condition" yang menyebabkan data corrupt

    # ────────────────────────────────────────────────────
    # CALLBACK MANAGEMENT
    # Sistem Observer Pattern: monitor memberi tahu GUI saat ada perubahan
    # ────────────────────────────────────────────────────

    def add_callback(self, callback: Callable[[SiteStatus], None]):
        """Mendaftarkan fungsi callback yang dipanggil setiap ada update status website"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[SiteStatus], None]):
        """Menghapus fungsi callback dari daftar"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_callbacks(self, status: SiteStatus):
        """Memanggil semua callback yang terdaftar dengan data status terbaru"""
        for callback in self._callbacks:
            try:
                callback(status)  # Panggil fungsi callback (biasanya update GUI)
            except Exception as e:
                # Error di callback tidak boleh meng-crash proses monitoring
                print(f"Callback error: {e}")

    def add_alert_callback(self, callback: Callable):
        """Mendaftarkan fungsi callback yang dipanggil saat ada alert baru"""
        self._alert_callbacks.append(callback)

    def _notify_alert_callbacks(self, alert: AlertEntry):
        """Memanggil semua alert callback saat terjadi perubahan status"""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Alert callback error: {e}")

    def get_alerts(self) -> list:
        """Mendapatkan semua alert yang tercatat (terbaru duluan)"""
        return list(reversed(self._alerts))

    def clear_alerts(self):
        """Menghapus semua riwayat alert"""
        self._alerts.clear()

    # ────────────────────────────────────────────────────
    # SITE MANAGEMENT
    # Menambah dan menghapus website dari daftar monitoring
    # ────────────────────────────────────────────────────

    def add_site(self, url: str) -> SiteStatus:
        """
        Menambahkan website ke daftar monitoring.
        Langsung melakukan pengecekan pertama secara asinkron (non-blocking).
        """
        with self._lock:  # Kunci akses data agar thread-safe
            if url not in self.sites:
                status = SiteStatus(url=url)    # Buat objek status baru dengan default values
                self.sites[url] = status         # Simpan ke dictionary
                # Langsung cek website ini di thread terpisah (agar GUI tidak freeze)
                self.force_check(url)
                return self.sites[url]
            return self.sites[url]  # Kalau sudah ada, return yang existing

    def remove_site(self, url: str):
        """Menghapus website dari daftar monitoring"""
        with self._lock:
            if url in self.sites:
                del self.sites[url]              # Hapus dari dictionary utama
            if url in self._previous_states:
                del self._previous_states[url]   # Hapus juga tracking status sebelumnya

    def get_site_status(self, url: str) -> Optional[SiteStatus]:
        """Mendapatkan status terkini dari website tertentu"""
        return self.sites.get(url)

    def get_all_sites(self) -> list[SiteStatus]:
        """Mendapatkan status semua website yang dimonitor"""
        return list(self.sites.values())

    # ════════════════════════════════════════════════════
    # ★ NETWORK PROGRAMMING: HTTP STATUS CHECK ★
    # Mengirim HTTP GET request ke website dan membaca respons
    # ════════════════════════════════════════════════════

    def check_http_status(self, url: str) -> tuple[int, float, str]:
        """
        Mengirim HTTP GET request ke URL dan mendapatkan status code beserta latency.

        Cara kerja:
        1. Catat waktu mulai
        2. Kirim HTTP GET request ke URL
        3. Catat waktu selesai
        4. Hitung selisih waktu = latency (dalam milidetik)
        5. Return status code, latency, dan pesan error (kosong jika sukses)

        Returns:
            Tuple berisi (status_code, latency_ms, error_message)
            status_code = -1 jika request gagal
        """
        try:
            start_time = time.time()  # Catat waktu SEBELUM request (untuk hitung latency)

            # ── Kirim HTTP GET Request ──
            # Ini adalah inti dari Network Programming - komunikasi HTTP
            response = requests.get(
                url,                          # URL tujuan
                timeout=self.timeout,         # Batas waktu tunggu (detik). Kalau lewat, raise Timeout
                allow_redirects=True,         # Ikuti redirect otomatis (misal HTTP→HTTPS, 301, 302)
                headers={
                    # User-Agent header: mengidentifikasi diri kita ke web server
                    # Web server bisa memblokir request tanpa User-Agent
                    'User-Agent': 'Py-SiteCheck/1.0 (Web Availability Monitor)'
                }
            )

            # Hitung latency: waktu SESUDAH request - waktu SEBELUM request
            # Dikali 1000 untuk konversi dari detik ke milidetik (ms)
            latency = (time.time() - start_time) * 1000

            # Return sukses: status code (misal 200), latency, dan string kosong (tidak ada error)
            return response.status_code, latency, ""

        # ── Error Handling Jaringan ──
        # Berbagai jenis error yang bisa terjadi saat mengirim HTTP request:

        except requests.exceptions.Timeout:
            # Server tidak merespons dalam batas waktu yang ditentukan
            return -1, -1, "Connection timeout"

        except requests.exceptions.ConnectionError:
            # Tidak bisa terhubung ke server (DNS gagal, server mati, tidak ada internet, dll)
            return -1, -1, "Connection failed"

        except requests.exceptions.SSLError:
            # Sertifikat SSL/TLS website bermasalah (expired, tidak valid, dll)
            return -1, -1, "SSL certificate error"

        except requests.exceptions.TooManyRedirects:
            # Website melakukan redirect berulang-ulang tanpa akhir (infinite loop)
            return -1, -1, "Too many redirects"

        except Exception as e:
            # Error lainnya yang tidak terduga
            return -1, -1, str(e)

    # ════════════════════════════════════════════════════
    # ★ NETWORK PROGRAMMING: TCP PORT CHECK ★
    # Mengecek apakah port tertentu terbuka menggunakan TCP socket
    # ════════════════════════════════════════════════════

    def check_port(self, host: str, port: int) -> bool:
        """
        Mengecek apakah port tertentu terbuka pada host menggunakan TCP socket.

        Cara kerja:
        1. Buat TCP socket
        2. Coba koneksi ke host:port
        3. Kalau berhasil (return 0) → port terbuka
        4. Kalau gagal → port tertutup atau host tidak bisa dijangkau

        Args:
            host: Hostname atau alamat IP (contoh: "google.com" atau "142.250.185.206")
            port: Nomor port yang dicek (contoh: 80 untuk HTTP, 443 untuk HTTPS)

        Returns:
            True jika port terbuka, False jika tertutup/gagal
        """
        try:
            # ── Membuat TCP Socket ──
            # socket.AF_INET    = Menggunakan alamat IPv4 (Internet Protocol version 4)
            # socket.SOCK_STREAM = Menggunakan protokol TCP (Transmission Control Protocol)
            #                      TCP = connection-oriented, reliable, ordered delivery
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set batas waktu untuk koneksi socket
            # Kalau tidak ada respons dalam waktu ini, akan raise socket.timeout
            sock.settimeout(self.timeout)

            # ── Mencoba Koneksi TCP ──
            # connect_ex() mirip connect(), tapi TIDAK raise exception saat gagal
            # Return 0 = koneksi berhasil (port terbuka)
            # Return non-zero = koneksi gagal (port tertutup/unreachable)
            result = sock.connect_ex((host, port))

            # Tutup socket setelah selesai (penting! agar resource tidak bocor)
            sock.close()

            # Port terbuka jika result == 0
            return result == 0

        except socket.gaierror:
            # gaierror = "getaddrinfo error"
            # Terjadi saat DNS resolution gagal (domain tidak bisa ditemukan)
            # Contoh: host "asdfghjkl.xyz" tidak terdaftar di DNS
            return False

        except socket.timeout:
            # Koneksi TCP timeout - server tidak merespons dalam batas waktu
            return False

        except Exception:
            # Error lainnya (permission denied, network unreachable, dll)
            return False

    def _get_host_and_port(self, url: str) -> tuple[str, int]:
        """
        Mengekstrak hostname dan port dari URL.

        Contoh:
        - "https://google.com"       → ("google.com", 443)
        - "http://example.com"       → ("example.com", 80)
        - "https://api.server.com:8443" → ("api.server.com", 8443)
        """
        try:
            parsed = urlparse(url)                    # Parse URL menjadi komponen
            host = parsed.netloc.split(':')[0]        # Ambil hostname (tanpa port)
            if parsed.port:
                port = parsed.port                    # Pakai port dari URL jika ada
            else:
                # Default: HTTPS = port 443, HTTP = port 80
                port = 443 if parsed.scheme == 'https' else 80
            return host, port
        except:
            return "", 443  # Fallback jika parsing gagal

    # ────────────────────────────────────────────────────
    # PENGECEKAN WEBSITE (GABUNGAN HTTP + PORT + ALERT)
    # ────────────────────────────────────────────────────

    def _check_site(self, url: str):
        """
        Melakukan SEMUA pengecekan pada satu website:
        1. HTTP status check (status code + latency)
        2. TCP port check (port terbuka/tertutup)
        3. Deteksi perubahan status → generate alert jika berubah
        4. Notify callback → update GUI
        """
        # Pastikan URL masih ada di daftar (bisa saja sudah dihapus user)
        if url not in self.sites:
            return

        # LANGKAH 1: Dapatkan hostname dan port dari URL
        host, port = self._get_host_and_port(url)

        # LANGKAH 2: Cek HTTP status dan latency
        # Mengirim HTTP GET request ke website
        status_code, latency, error = self.check_http_status(url)

        # LANGKAH 3: Cek apakah port TCP terbuka
        # Membuka koneksi TCP socket ke host:port
        port_open = self.check_port(host, port) if host else False

        # LANGKAH 4: Update data status (thread-safe dengan lock)
        with self._lock:
            if url in self.sites:
                status = self.sites[url]
                status.status_code = status_code
                status.latency_ms = latency
                # Website dianggap online jika HTTP status code antara 200-399
                # 200-299 = Success (OK, Created, dll)
                # 300-399 = Redirect (Moved Permanently, Found, dll)
                status.is_online = 200 <= status_code < 400
                status.port_open = port_open
                status.port_checked = port
                status.last_check = time.time()    # Catat waktu pengecekan
                status.error_message = error

                # ── LANGKAH 5: Deteksi Perubahan Status → Generate Alert ──
                # Bandingkan status SEKARANG vs SEBELUMNYA
                was_online = self._previous_states.get(url)      # Status sebelumnya (bisa None jika pertama kali)
                is_now_online = status.is_online                 # Status sekarang

                if was_online is not None and was_online != is_now_online:
                    # STATUS BERUBAH! (online→offline ATAU offline→online)
                    if is_now_online:
                        # Website PULIH (tadinya offline, sekarang online lagi)
                        alert = AlertEntry(
                            url=url,
                            alert_type="recovered",
                            message=f"Site is back online (HTTP {status_code})",
                            status_code=status_code
                        )
                    else:
                        # Website DOWN (tadinya online, sekarang offline)
                        alert = AlertEntry(
                            url=url,
                            alert_type="down",
                            message=error or f"Site is down (HTTP {status_code})",
                            status_code=status_code
                        )
                    self._alerts.append(alert)                # Simpan ke riwayat
                    self._notify_alert_callbacks(alert)        # Beritahu GUI

                elif was_online is None and not is_now_online:
                    # Pengecekan PERTAMA KALI dan website sudah offline
                    alert = AlertEntry(
                        url=url,
                        alert_type="down",
                        message=error or f"Site is unreachable (HTTP {status_code})",
                        status_code=status_code
                    )
                    self._alerts.append(alert)
                    self._notify_alert_callbacks(alert)

                # Simpan status sekarang sebagai "status sebelumnya" untuk pengecekan berikutnya
                self._previous_states[url] = is_now_online

                # LANGKAH 6: Beritahu GUI bahwa ada data baru (panggil semua callback)
                self._notify_callbacks(status)

    def check_all_sites(self):
        """Menjalankan pengecekan untuk SEMUA website yang terdaftar"""
        urls = list(self.sites.keys())  # Ambil semua URL (copy list agar aman)
        for url in urls:
            if not self._running:       # Cek apakah monitoring masih aktif
                break                   # Kalau sudah distop, hentikan loop
            self._check_site(url)       # Cek satu per satu

    # ════════════════════════════════════════════════════
    # ★ MULTI-THREADING: Background Monitoring ★
    # Monitoring berjalan di thread terpisah agar GUI tidak freeze
    # ════════════════════════════════════════════════════

    def _monitor_loop(self):
        """
        Loop utama monitoring yang berjalan di background thread.

        Alur:
        1. Cek semua website
        2. Tunggu selama check_interval detik
        3. Ulangi dari langkah 1
        4. Berhenti jika self._running = False
        """
        while self._running:        # Terus looping selama flag _running = True
            self.check_all_sites()  # Cek semua website

            # ── Menunggu interval dengan cara yang bisa diinterupsi ──
            # KENAPA tidak pakai time.sleep(self.check_interval) saja?
            # Karena kalau pakai sleep(30), saat user tutup aplikasi,
            # program harus MENUNGGU 30 DETIK sebelum thread bisa berhenti!
            #
            # Solusi: Kita pecah jadi sleep(0.5) yang diulang.
            # Setiap 0.5 detik, kita cek apakah monitoring sudah dihentikan.
            # Jadi thread bisa berhenti dalam waktu MAKSIMAL 0.5 detik.
            start_wait = time.time()
            while self._running and (time.time() - start_wait) < self.check_interval:
                time.sleep(0.5)  # Tidur 0.5 detik, lalu cek ulang

    def start_monitoring(self):
        """Memulai thread background untuk monitoring otomatis"""
        if self._running:
            return  # Sudah berjalan, tidak perlu mulai lagi

        self._running = True  # Set flag aktif

        # Membuat thread baru yang menjalankan _monitor_loop()
        # daemon=True berarti thread ini akan otomatis mati saat program utama selesai
        # (tidak menghalangi aplikasi untuk ditutup)
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()  # Mulai jalankan thread

    def stop_monitoring(self):
        """
        Menghentikan thread monitoring dengan aman (graceful shutdown).

        Alur:
        1. Set flag _running = False → _monitor_loop() akan berhenti
        2. Tunggu thread selesai dengan join() (maksimal 5 detik)
        3. Hapus referensi thread
        """
        self._running = False  # Beri sinyal agar loop berhenti

        if self._monitor_thread and self._monitor_thread.is_alive():
            # join() = tunggu sampai thread benar-benar selesai
            # timeout=5.0 = jangan tunggu lebih dari 5 detik
            self._monitor_thread.join(timeout=5.0)

        self._monitor_thread = None  # Bersihkan referensi

    def force_check(self, url: str):
        """
        Memaksa pengecekan langsung pada satu website tertentu.
        Dijalankan di thread baru agar tidak memblokir GUI (non-blocking).
        Digunakan saat user klik tombol refresh ↻
        """
        threading.Thread(target=self._check_site, args=(url,), daemon=True).start()

    def is_running(self) -> bool:
        """Mengecek apakah monitoring sedang aktif"""
        return self._running
