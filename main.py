"""
Py-SiteCheck - Web Availability Monitor
Aplikasi monitoring ketersediaan website secara real-time.
Mengecek apakah website online/offline menggunakan HTTP request dan TCP socket.

Author: Nawal Haromaen (NIM: 714240038)
Course: Network Programming
Lecturer: Muhammad Yusril Helmi Setyawan, S.Kom., M.Kom.
Institution: Universitas Logistik Dan Bisnis Internasional (ULBI)
"""

# ── Import Module ──
import sys  # Module untuk mengakses konfigurasi sistem Python (sys.path, dll)
import os   # Module untuk operasi file dan folder (path, directory, dll)

# Menambahkan folder proyek ke dalam Python path
# Tujuannya agar Python bisa menemukan module 'core' dan 'gui' saat di-import
# __file__ = path file ini sendiri (main.py)
# os.path.abspath(__file__) = ubah ke absolute path (path lengkap)
# os.path.dirname(...) = ambil folder induk dari file ini
# sys.path.insert(0, ...) = masukkan ke urutan pertama di daftar pencarian module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import fungsi run_app dari module gui/app.py
# Fungsi ini yang akan membuka jendela GUI aplikasi
from gui.app import run_app


def main():
    """Fungsi utama - titik masuk aplikasi Py-SiteCheck"""

    # Menampilkan banner/header di terminal saat aplikasi dijalankan
    print("=" * 50)
    print("  Py-SiteCheck - Web Availability Monitor")
    print("  by Nawal Haromaen (714240038)")
    print("=" * 50)
    print("\nStarting application...")

    # Menjalankan aplikasi dalam blok try-except untuk menangani error
    try:
        # Memanggil fungsi run_app() yang akan membuka jendela GUI
        # Program akan "terjebak" di sini sampai user menutup window
        run_app()

    except KeyboardInterrupt:
        # KeyboardInterrupt terjadi saat user menekan Ctrl+C di terminal
        # Kita tangkap agar tidak menampilkan traceback yang menyeramkan
        print("\nApplication terminated by user.")

    except Exception as e:
        # Menangkap semua error lainnya yang tidak terduga
        # Cetak pesan error, lalu raise kembali agar traceback tetap muncul
        # (berguna untuk debugging)
        print(f"\nError: {e}")
        raise


# Guard clause standar Python:
# Kode di bawah ini HANYA dijalankan kalau file ini dieksekusi langsung (python main.py)
# TIDAK dijalankan kalau file ini di-import sebagai module oleh file lain
if __name__ == "__main__":
    main()
