# Package core/ untuk Py-SiteCheck
# Berisi logika inti (core logic) aplikasi yang TIDAK tergantung GUI:
#
# - monitor.py : Kelas SiteMonitor untuk mengecek HTTP status, TCP port,
#                dan menjalankan monitoring berkala di background thread
#
# - utils.py   : Fungsi utilitas (helper) seperti validasi URL,
#                extract domain, format latency, dll
#
# File __init__.py ini menandakan bahwa folder core/ adalah sebuah Python package
# sehingga bisa di-import dengan: from core.monitor import SiteMonitor
