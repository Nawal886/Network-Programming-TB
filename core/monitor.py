"""
Site Monitor - Core monitoring functionality for Py-SiteCheck
Handles HTTP requests, port checking, and latency measurement
"""

import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from urllib.parse import urlparse

import requests


@dataclass
class SiteStatus:
    """Data class representing the status of a monitored site"""
    url: str
    is_online: bool = False
    status_code: int = -1
    latency_ms: float = -1.0
    port_open: bool = False
    port_checked: int = 443
    last_check: float = field(default_factory=time.time)
    error_message: str = ""
    
    def to_dict(self) -> dict:
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


class SiteMonitor:
    """
    Monitors website availability using HTTP requests and TCP socket connections.
    Supports multi-URL monitoring with threading.
    """
    
    def __init__(self, check_interval: float = 30.0, timeout: float = 10.0):
        """
        Initialize the site monitor.
        
        Args:
            check_interval: Time between checks in seconds
            timeout: Request timeout in seconds
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.sites: dict[str, SiteStatus] = {}
        self._callbacks: list[Callable[[SiteStatus], None]] = []
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def add_callback(self, callback: Callable[[SiteStatus], None]):
        """Add a callback to be called when site status changes"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[SiteStatus], None]):
        """Remove a callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self, status: SiteStatus):
        """Notify all callbacks of a status update"""
        for callback in self._callbacks:
            try:
                callback(status)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def add_site(self, url: str) -> SiteStatus:
        """Add a site to monitor"""
        with self._lock:
            if url not in self.sites:
                status = SiteStatus(url=url)
                self.sites[url] = status
                # Check the site asynchronously to avoid blocking the caller (e.g. GUI thread)
                self.force_check(url)
                return self.sites[url]
            return self.sites[url]
    
    def remove_site(self, url: str):
        """Remove a site from monitoring"""
        with self._lock:
            if url in self.sites:
                del self.sites[url]
    
    def get_site_status(self, url: str) -> Optional[SiteStatus]:
        """Get the current status of a monitored site"""
        return self.sites.get(url)
    
    def get_all_sites(self) -> list[SiteStatus]:
        """Get status of all monitored sites"""
        return list(self.sites.values())
    
    def check_http_status(self, url: str) -> tuple[int, float, str]:
        """
        Send HTTP request and get status code with latency.
        
        Returns:
            Tuple of (status_code, latency_ms, error_message)
            status_code is -1 if request failed
        """
        try:
            start_time = time.time()
            response = requests.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                headers={
                    'User-Agent': 'Py-SiteCheck/1.0 (Web Availability Monitor)'
                }
            )
            latency = (time.time() - start_time) * 1000  # Convert to ms
            return response.status_code, latency, ""
        except requests.exceptions.Timeout:
            return -1, -1, "Connection timeout"
        except requests.exceptions.ConnectionError:
            return -1, -1, "Connection failed"
        except requests.exceptions.SSLError:
            return -1, -1, "SSL certificate error"
        except requests.exceptions.TooManyRedirects:
            return -1, -1, "Too many redirects"
        except Exception as e:
            return -1, -1, str(e)
    
    def check_port(self, host: str, port: int) -> bool:
        """
        Check if a specific port is open on the host using TCP socket.
        
        Args:
            host: Hostname or IP address
            port: Port number to check
            
        Returns:
            True if port is open, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except socket.gaierror:
            # Hostname resolution failed
            return False
        except socket.timeout:
            return False
        except Exception:
            return False
    
    def _get_host_and_port(self, url: str) -> tuple[str, int]:
        """Extract host and port from URL"""
        try:
            parsed = urlparse(url)
            host = parsed.netloc.split(':')[0]
            if parsed.port:
                port = parsed.port
            else:
                port = 443 if parsed.scheme == 'https' else 80
            return host, port
        except:
            return "", 443
    
    def _check_site(self, url: str):
        """Perform all checks on a single site"""
        if url not in self.sites:
            return
        
        # Get host and port for port checking
        host, port = self._get_host_and_port(url)
        
        # Check HTTP status and latency
        status_code, latency, error = self.check_http_status(url)
        
        # Check port
        port_open = self.check_port(host, port) if host else False
        
        # Update status
        with self._lock:
            if url in self.sites:
                status = self.sites[url]
                status.status_code = status_code
                status.latency_ms = latency
                status.is_online = 200 <= status_code < 400
                status.port_open = port_open
                status.port_checked = port
                status.last_check = time.time()
                status.error_message = error
                
                # Notify callbacks
                self._notify_callbacks(status)
    
    def check_all_sites(self):
        """Check all monitored sites"""
        urls = list(self.sites.keys())
        for url in urls:
            if not self._running:
                break
            self._check_site(url)
    
    def _monitor_loop(self):
        """Main monitoring loop running in background thread"""
        while self._running:
            self.check_all_sites()
            
            # Wait for interval or until stopped
            start_wait = time.time()
            while self._running and (time.time() - start_wait) < self.check_interval:
                time.sleep(0.5)  # Check every 0.5s if we should stop
    
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the background monitoring thread gracefully"""
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        self._monitor_thread = None
    
    def force_check(self, url: str):
        """Force an immediate check on a specific site"""
        threading.Thread(target=self._check_site, args=(url,), daemon=True).start()
    
    def is_running(self) -> bool:
        """Check if monitoring is active"""
        return self._running
