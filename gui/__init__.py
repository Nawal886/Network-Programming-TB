# Package gui/ untuk Py-SiteCheck
# Berisi semua komponen antarmuka grafis (GUI) menggunakan CustomTkinter:
#
# - app.py        : Kelas utama PySiteCheckApp (jendela aplikasi + pengatur view)
# - components.py : Widget reusable (SiteCard, AddURLDialog, Sidebar, StatusBar)
# - views.py      : Halaman-halaman view (SitesView, AlertsView, SettingsView)
# - theme.py      : Design system (warna, font, ukuran, animasi)
#
# File __init__.py ini menandakan bahwa folder gui/ adalah sebuah Python package
# sehingga bisa di-import dengan: from gui.app import run_app
