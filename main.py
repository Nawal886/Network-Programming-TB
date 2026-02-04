"""
Py-SiteCheck - Web Availability Monitor
A network utility application for monitoring website status in real-time.

Author: Nawal Haromaen (NIM: 714240038)
Course: Network Programming
Lecturer: Muhammad Yusril Helmi Setyawan, S.Kom., M.Kom.
Institution: Universitas Logistik Dan Bisnis Internasional (ULBI)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import run_app


def main():
    """Main entry point for Py-SiteCheck application"""
    print("=" * 50)
    print("  Py-SiteCheck - Web Availability Monitor")
    print("  by Nawal Haromaen (714240038)")
    print("=" * 50)
    print("\nStarting application...")
    
    try:
        run_app()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
