"""
Main Application Window for Py-SiteCheck
"""

import customtkinter as ctk
from typing import Optional
import threading

from .theme import COLORS, FONTS, SIZES
from .components import SiteCard, AddURLDialog, Sidebar, StatusBar
from core.monitor import SiteMonitor, SiteStatus
from core.utils import validate_url, extract_domain


class PySiteCheckApp(ctk.CTk):
    """Main application window for Py-SiteCheck"""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Py-SiteCheck - Web Availability Monitor")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        # Set appearance mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Configure main window color
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Initialize monitor
        self.monitor = SiteMonitor(check_interval=30.0, timeout=10.0)
        self.monitor.add_callback(self._on_status_update)
        
        # Site cards dictionary
        self.site_cards: dict[str, SiteCard] = {}
        
        # Setup UI
        self._setup_ui()
        
        # Add some default sites for demo
        self._add_default_sites()
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_ui(self):
        """Setup the main UI layout"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = Sidebar(self, on_nav_select=self._on_nav_select)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Dashboard content
        self._create_dashboard()
        
        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=1, sticky="ew")
    
    def _create_header(self):
        """Create the header section with title and add button"""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title section
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
        
        # Add button
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
        self.add_btn.grid(row=0, column=1, sticky="e")
    
    def _create_dashboard(self):
        """Create the dashboard content area"""
        # Scrollable frame for cards
        self.dashboard_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["border_light"]
        )
        self.dashboard_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        
        # Configure grid for cards
        self.dashboard_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="card")
        
        # Empty state label
        self.empty_label = ctk.CTkLabel(
            self.dashboard_frame,
            text="No websites added yet.\nClick '+ Add URL' to start monitoring.",
            font=(FONTS["family"], FONTS["body_size"]),
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self.empty_label.grid(row=0, column=0, columnspan=3, pady=100)
    
    def _add_default_sites(self):
        """Add some default sites for demonstration"""
        default_sites = [
            "https://www.google.com",
            "https://www.github.com",
            "https://www.ulbi.ac.id",
        ]
        
        for url in default_sites:
            self._add_site(url)
    
    def _show_add_dialog(self):
        """Show the add URL dialog"""
        dialog = AddURLDialog(self, on_submit=self._add_site)
        dialog.wait_window()
    
    def _add_site(self, url: str):
        """Add a new site to monitor"""
        # Validate URL
        is_valid, result = validate_url(url)
        if not is_valid:
            return
        
        url = result
        
        # Check if already exists
        if url in self.site_cards:
            return
        
        # Hide empty label
        self.empty_label.grid_forget()
        
        # Create card
        card = SiteCard(
            self.dashboard_frame,
            url=url,
            on_delete=self._remove_site,
            on_refresh=self._refresh_site
        )
        
        # Position card in grid
        num_cards = len(self.site_cards)
        row = num_cards // 3
        col = num_cards % 3
        card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
        
        # Store reference
        self.site_cards[url] = card
        
        # Add to monitor
        self.monitor.add_site(url)
        
        # Update status bar
        self._update_status_bar()
    
    def _remove_site(self, url: str):
        """Remove a site from monitoring"""
        if url in self.site_cards:
            # Destroy the card widget
            self.site_cards[url].destroy()
            del self.site_cards[url]
            
            # Remove from monitor
            self.monitor.remove_site(url)
            
            # Reposition remaining cards
            self._reposition_cards()
            
            # Show empty label if no sites
            if not self.site_cards:
                self.empty_label.grid(row=0, column=0, columnspan=3, pady=100)
            
            # Update status bar
            self._update_status_bar()
    
    def _refresh_site(self, url: str):
        """Force refresh a specific site"""
        self.monitor.force_check(url)
    
    def _reposition_cards(self):
        """Reposition all cards after removal"""
        for i, (url, card) in enumerate(self.site_cards.items()):
            row = i // 3
            col = i % 3
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
    
    def _on_status_update(self, status: SiteStatus):
        """Callback when site status is updated"""
        # Update UI in main thread
        self.after(0, lambda: self._update_card(status))
    
    def _update_card(self, status: SiteStatus):
        """Update a card with new status"""
        if status.url in self.site_cards:
            self.site_cards[status.url].update_status(
                is_online=status.is_online,
                status_code=status.status_code,
                latency_ms=status.latency_ms,
                port_open=status.port_open,
                port=status.port_checked,
                error_message=status.error_message
            )
    
    def _update_status_bar(self):
        """Update the status bar"""
        self.status_bar.update_status(
            is_monitoring=self.monitor.is_running(),
            site_count=len(self.site_cards)
        )
    
    def _on_nav_select(self, nav_id: str):
        """Handle navigation selection"""
        # For now, just show dashboard
        # Future: implement different views
        pass
    
    def _on_close(self):
        """Handle window close - graceful shutdown"""
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Destroy window
        self.destroy()


def run_app():
    """Entry point to run the application"""
    app = PySiteCheckApp()
    app.mainloop()
