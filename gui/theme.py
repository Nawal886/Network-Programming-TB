"""
Theme configuration for Py-SiteCheck GUI
Modern dark theme with glassmorphism effects
"""

# Color Palette
COLORS = {
    # Primary colors
    "primary": "#8B5CF6",       # Purple
    "primary_hover": "#7C3AED",
    "primary_light": "#A78BFA",
    
    # Secondary colors
    "secondary": "#06B6D4",     # Cyan
    "secondary_hover": "#0891B2",
    
    # Background colors
    "bg_dark": "#0F0F1A",       # Main background
    "bg_card": "#1A1A2E",       # Card background
    "bg_card_hover": "#252542",
    "bg_sidebar": "#16162A",    # Sidebar background
    "bg_input": "#252542",      # Input background
    
    # Text colors
    "text_primary": "#FFFFFF",
    "text_secondary": "#A0A0B8",
    "text_muted": "#6B6B80",
    
    # Status colors
    "success": "#10B981",       # Green - online
    "success_light": "#34D399",
    "warning": "#F59E0B",       # Yellow/Orange - redirect
    "warning_light": "#FBBF24",
    "error": "#EF4444",         # Red - offline/error
    "error_light": "#F87171",
    
    # Border colors
    "border": "#2D2D44",
    "border_light": "#3D3D5C",
    
    # Gradient colors (for glassmorphism)
    "gradient_start": "#8B5CF6",
    "gradient_end": "#06B6D4",
}

# Font configurations
FONTS = {
    "family": "Segoe UI",
    "title_size": 24,
    "heading_size": 18,
    "body_size": 14,
    "small_size": 12,
    "tiny_size": 10,
}

# Sizing
SIZES = {
    "sidebar_width": 200,
    "card_width": 280,
    "card_height": 140,
    "card_padding": 16,
    "card_radius": 12,
    "button_height": 36,
    "input_height": 40,
    "spacing_xs": 4,
    "spacing_sm": 8,
    "spacing_md": 16,
    "spacing_lg": 24,
    "spacing_xl": 32,
}

# Animation durations (in ms)
ANIMATIONS = {
    "fast": 150,
    "normal": 300,
    "slow": 500,
}


def get_status_color(status: str) -> str:
    """Get color based on status string"""
    status_colors = {
        "online": COLORS["success"],
        "offline": COLORS["error"],
        "warning": COLORS["warning"],
        "checking": COLORS["text_muted"],
    }
    return status_colors.get(status, COLORS["text_muted"])


def get_status_code_color(code: int) -> str:
    """Get color based on HTTP status code"""
    if code < 0:
        return COLORS["error"]
    elif 200 <= code < 300:
        return COLORS["success"]
    elif 300 <= code < 400:
        return COLORS["warning"]
    else:
        return COLORS["error"]
