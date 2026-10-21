"""Networking utilities for IP resolution, port checks, and polling."""

import socket
import time


def get_local_ip() -> str:
    """Determine the local machine's primary non-loopback IP address.

    Falls back to '127.0.0.1' if disconnected or unavailable.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Does not send actual traffic; used to resolve routing interface
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def is_port_available(host: str, port: int) -> bool:
    """Test whether a port can be bound on the given host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    """Poll until a TCP service is accepting connections on host:port.

    Args:
        host: Hostname or IP to connect to.
        port: TCP port number.
        timeout: Maximum duration in seconds to poll.

    Returns:
        True if connection succeeded within timeout, False otherwise.
    """
    connect_host = "127.0.0.1" if host in ("0.0.0.0", "") else host
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            with socket.create_connection((connect_host, port), timeout=0.5):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.1)
    return False
