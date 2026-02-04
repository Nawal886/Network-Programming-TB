"""
GUI Components for Py-SiteCheck
Custom widgets with modern styling
"""

import customtkinter as ctk
from typing import Callable, Optional
import time

from .theme import COLORS, FONTS, SIZES, get_status_code_color


class SiteCard(ctk.CTkFrame):
    """
    Card widget displaying website status information.
    Shows URL, status indicator, response time, and HTTP status code.
    """
    
    def __init__(
        self,
        master,
        url: str,
        on_delete: Optional[Callable[[str], None]] = None,
        on_refresh: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=SIZES["card_radius"],
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        
        self.url = url
        self.on_delete = on_delete
        self.on_refresh = on_refresh
        
        self._setup_ui()
        self._set_default_state()
    
    def _setup_ui(self):
        """Setup the card UI layout"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Header frame with status indicator and delete button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=SIZES["card_padding"], pady=(SIZES["card_padding"], 8))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator (colored dot)
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text="●",
            font=(FONTS["family"], 16),
            text_color=COLORS["text_muted"],
            width=20
        )
        self.status_indicator.grid(row=0, column=0, padx=(0, 8))
        
        # URL label
        display_url = self.url
        if len(display_url) > 28:
            display_url = display_url[:25] + "..."
        
        self.url_label = ctk.CTkLabel(
            header_frame,
            text=display_url,
            font=(FONTS["family"], FONTS["body_size"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.url_label.grid(row=0, column=1, sticky="w")
        
        # Delete button
        self.delete_btn = ctk.CTkButton(
            header_frame,
            text="×",
            width=28,
            height=28,
            font=(FONTS["family"], 16),
            fg_color="transparent",
            hover_color=COLORS["error"],
            text_color=COLORS["text_muted"],
            corner_radius=6,
            command=self._on_delete_click
        )
        self.delete_btn.grid(row=0, column=2)
        
        # Response time frame
        response_frame = ctk.CTkFrame(self, fg_color="transparent")
        response_frame.grid(row=1, column=0, sticky="ew", padx=SIZES["card_padding"], pady=4)
        
        ctk.CTkLabel(
            response_frame,
            text="⏱",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")
        
        ctk.CTkLabel(
            response_frame,
            text=" Response: ",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")
        
        self.latency_label = ctk.CTkLabel(
            response_frame,
            text="-- ms",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_secondary"]
        )
        self.latency_label.pack(side="left")
        
        # Port status frame
        port_frame = ctk.CTkFrame(self, fg_color="transparent")
        port_frame.grid(row=2, column=0, sticky="ew", padx=SIZES["card_padding"], pady=4)
        
        ctk.CTkLabel(
            port_frame,
            text="🔌",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")
        
        ctk.CTkLabel(
            port_frame,
            text=" Port: ",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")
        
        self.port_label = ctk.CTkLabel(
            port_frame,
            text="--",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_secondary"]
        )
        self.port_label.pack(side="left")
        
        # HTTP status badge frame
        badge_frame = ctk.CTkFrame(self, fg_color="transparent")
        badge_frame.grid(row=3, column=0, sticky="ew", padx=SIZES["card_padding"], pady=(8, SIZES["card_padding"]))
        
        self.status_badge = ctk.CTkLabel(
            badge_frame,
            text="  Checking...  ",
            font=(FONTS["family"], FONTS["small_size"], "bold"),
            fg_color=COLORS["bg_input"],
            corner_radius=6,
            text_color=COLORS["text_muted"],
            padx=8,
            pady=4
        )
        self.status_badge.pack(side="left")
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            badge_frame,
            text="↻",
            width=28,
            height=28,
            font=(FONTS["family"], 14),
            fg_color="transparent",
            hover_color=COLORS["primary"],
            text_color=COLORS["text_muted"],
            corner_radius=6,
            command=self._on_refresh_click
        )
        self.refresh_btn.pack(side="right")
    
    def _set_default_state(self):
        """Set the default checking state"""
        self.status_indicator.configure(text_color=COLORS["text_muted"])
        self.latency_label.configure(text="-- ms")
        self.port_label.configure(text="--")
        self.status_badge.configure(
            text="  Checking...  ",
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_muted"]
        )
    
    def update_status(
        self,
        is_online: bool,
        status_code: int,
        latency_ms: float,
        port_open: bool,
        port: int,
        error_message: str = ""
    ):
        """Update the card with new status information"""
        # Update status indicator
        if status_code < 0:
            indicator_color = COLORS["error"]
        elif is_online:
            indicator_color = COLORS["success"]
        else:
            indicator_color = COLORS["warning"] if 300 <= status_code < 400 else COLORS["error"]
        
        self.status_indicator.configure(text_color=indicator_color)
        
        # Update latency
        if latency_ms >= 0:
            if latency_ms < 1000:
                latency_text = f"{latency_ms:.0f} ms"
            else:
                latency_text = f"{latency_ms/1000:.2f} s"
        else:
            latency_text = "Timeout"
        self.latency_label.configure(text=latency_text)
        
        # Update port status
        port_status = f"{port} ({'Open' if port_open else 'Closed'})"
        port_color = COLORS["success"] if port_open else COLORS["error"]
        self.port_label.configure(text=port_status, text_color=port_color)
        
        # Update status badge
        if status_code < 0:
            badge_text = f"  {error_message or 'Error'}  "
            badge_color = COLORS["error"]
        else:
            badge_text = f"  HTTP {status_code}  "
            badge_color = get_status_code_color(status_code)
        
        self.status_badge.configure(
            text=badge_text,
            fg_color=badge_color,
            text_color=COLORS["text_primary"]
        )
    
    def _on_delete_click(self):
        """Handle delete button click"""
        if self.on_delete:
            self.on_delete(self.url)
    
    def _on_refresh_click(self):
        """Handle refresh button click"""
        self._set_default_state()
        if self.on_refresh:
            self.on_refresh(self.url)


class AddURLDialog(ctk.CTkToplevel):
    """Modal dialog for adding a new URL to monitor"""
    
    def __init__(self, master, on_submit: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        
        self.on_submit = on_submit
        self.result = None
        
        # Window configuration
        self.title("Add Website")
        self.geometry("450x200")
        self.resizable(False, False)
        
        # Center the dialog
        self.transient(master)
        self.grab_set()
        
        # Configure colors
        self.configure(fg_color=COLORS["bg_dark"])
        
        self._setup_ui()
        
        # Focus the entry
        self.url_entry.focus_set()
        
        # Bind Enter key
        self.bind("<Return>", lambda e: self._on_submit())
        self.bind("<Escape>", lambda e: self.destroy())
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        # Main container with padding
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=24)
        
        # Title
        ctk.CTkLabel(
            container,
            text="Add Website to Monitor",
            font=(FONTS["family"], FONTS["heading_size"], "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")
        
        # Subtitle
        ctk.CTkLabel(
            container,
            text="Enter the URL of the website you want to monitor",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(4, 16))
        
        # URL Entry
        self.url_entry = ctk.CTkEntry(
            container,
            placeholder_text="https://example.com",
            font=(FONTS["family"], FONTS["body_size"]),
            height=SIZES["input_height"],
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"]
        )
        self.url_entry.pack(fill="x", pady=(0, 16))
        
        # Error label (hidden by default)
        self.error_label = ctk.CTkLabel(
            container,
            text="",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["error"]
        )
        self.error_label.pack(anchor="w")
        
        # Button frame
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8, 0))
        
        # Cancel button
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=(FONTS["family"], FONTS["body_size"]),
            height=SIZES["button_height"],
            fg_color="transparent",
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_secondary"],
            border_width=1,
            border_color=COLORS["border"],
            command=self.destroy
        ).pack(side="right", padx=(8, 0))
        
        # Add button
        ctk.CTkButton(
            btn_frame,
            text="Add Website",
            font=(FONTS["family"], FONTS["body_size"]),
            height=SIZES["button_height"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_primary"],
            command=self._on_submit
        ).pack(side="right")
    
    def _on_submit(self):
        """Handle form submission"""
        url = self.url_entry.get().strip()
        
        if not url:
            self.error_label.configure(text="Please enter a URL")
            return
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        self.result = url
        self.on_submit(url)
        self.destroy()


class Sidebar(ctk.CTkFrame):
    """Sidebar navigation component"""
    
    def __init__(self, master, on_nav_select: Callable[[str], None], **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0,
            width=SIZES["sidebar_width"],
            **kwargs
        )
        
        self.on_nav_select = on_nav_select
        self.active_nav = "dashboard"
        self.nav_buttons = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup sidebar UI"""
        # Prevent the frame from shrinking
        self.grid_propagate(False)
        
        # App title/logo
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=20)
        
        ctk.CTkLabel(
            title_frame,
            text="🌐 Py-SiteCheck",
            font=(FONTS["family"], FONTS["heading_size"], "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Web Availability Monitor",
            font=(FONTS["family"], FONTS["tiny_size"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(2, 0))
        
        # Navigation items
        nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("sites", "🌍", "Sites"),
            ("alerts", "🔔", "Alerts"),
            ("settings", "⚙️", "Settings"),
        ]
        
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=8)
        
        for nav_id, icon, label in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icon}  {label}",
                font=(FONTS["family"], FONTS["body_size"]),
                height=40,
                anchor="w",
                fg_color=COLORS["primary"] if nav_id == self.active_nav else "transparent",
                hover_color=COLORS["bg_card_hover"],
                text_color=COLORS["text_primary"],
                corner_radius=8,
                command=lambda nid=nav_id: self._on_nav_click(nid)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[nav_id] = btn
        
        # Version info at bottom
        version_label = ctk.CTkLabel(
            self,
            text="v1.0.0",
            font=(FONTS["family"], FONTS["tiny_size"]),
            text_color=COLORS["text_muted"]
        )
        version_label.pack(side="bottom", pady=16)
    
    def _on_nav_click(self, nav_id: str):
        """Handle navigation item click"""
        # Update button states
        for nid, btn in self.nav_buttons.items():
            if nid == nav_id:
                btn.configure(fg_color=COLORS["primary"])
            else:
                btn.configure(fg_color="transparent")
        
        self.active_nav = nav_id
        self.on_nav_select(nav_id)


class StatusBar(ctk.CTkFrame):
    """Bottom status bar showing monitoring status"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0,
            height=32,
            **kwargs
        )
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup status bar UI"""
        self.grid_propagate(False)
        
        # Left side - monitoring status
        self.status_label = ctk.CTkLabel(
            self,
            text="● Monitoring Active",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["success"]
        )
        self.status_label.pack(side="left", padx=16)
        
        # Right side - site count
        self.site_count_label = ctk.CTkLabel(
            self,
            text="0 sites monitored",
            font=(FONTS["family"], FONTS["small_size"]),
            text_color=COLORS["text_muted"]
        )
        self.site_count_label.pack(side="right", padx=16)
    
    def update_status(self, is_monitoring: bool, site_count: int):
        """Update the status bar"""
        if is_monitoring:
            self.status_label.configure(
                text="● Monitoring Active",
                text_color=COLORS["success"]
            )
        else:
            self.status_label.configure(
                text="○ Monitoring Paused",
                text_color=COLORS["text_muted"]
            )
        
        self.site_count_label.configure(
            text=f"{site_count} site{'s' if site_count != 1 else ''} monitored"
        )
