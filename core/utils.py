"""
Utility functions for Py-SiteCheck
"""

from urllib.parse import urlparse
import re

# HTTP Status Code Descriptions
STATUS_CODES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

def get_status_description(code: int) -> str:
    """Get human-readable description for HTTP status code"""
    return STATUS_CODES.get(code, "Unknown Status")

def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate and normalize a URL
    Returns: (is_valid, normalized_url or error_message)
    """
    url = url.strip()
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        
        # Check if we have a valid netloc (domain)
        if not parsed.netloc:
            return False, "Invalid URL: No domain found"
        
        # Basic domain validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        domain = parsed.netloc.split(':')[0]  # Remove port if present
        
        if not re.match(domain_pattern, domain):
            return False, f"Invalid domain: {domain}"
        
        return True, url
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"

def extract_domain(url: str) -> str:
    """Extract domain name from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc or url
    except:
        return url

def get_port_from_url(url: str) -> int:
    """Get the appropriate port for a URL (80 for HTTP, 443 for HTTPS)"""
    try:
        parsed = urlparse(url)
        if parsed.port:
            return parsed.port
        return 443 if parsed.scheme == 'https' else 80
    except:
        return 443

def format_latency(latency_ms: float) -> str:
    """Format latency in human-readable format"""
    if latency_ms < 0:
        return "N/A"
    elif latency_ms < 1000:
        return f"{latency_ms:.0f} ms"
    else:
        return f"{latency_ms/1000:.2f} s"

def get_status_color(status_code: int) -> str:
    """Get color based on HTTP status code"""
    if 200 <= status_code < 300:
        return "green"
    elif 300 <= status_code < 400:
        return "yellow"
    elif status_code < 0:
        return "red"
    else:
        return "red"
