"""Client registry manager for communication between Peer nodes and Tracker."""

import logging
import threading
from typing import Any
import httpx

logger = logging.getLogger("p2p.peer_registry")


class PeerRegistryClient:
    """Client used by peer nodes to register, send heartbeats, and query tracker."""

    def __init__(
        self,
        tracker_url: str,
        peer_id: str,
        host: str,
        tcp_port: int,
        api_port: int,
    ) -> None:
        self.tracker_url = tracker_url.rstrip("/")
        self.peer_id = peer_id
        self.host = host
        self.tcp_port = tcp_port
        self.api_port = api_port

        self._is_registered: bool = False
        self._running: bool = False
        self._heartbeat_timer: threading.Timer | None = None
        self._lock = threading.Lock()

    @property
    def is_registered(self) -> bool:
        """Return registration state with the tracker."""
        return self._is_registered

    def register(self, shared_files: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Register peer with tracker and provide initial list of shared files.

        Endpoint: POST /api/peers/register
        """
        payload = {
            "peer_id": self.peer_id,
            "host": self.host,
            "tcp_port": self.tcp_port,
            "api_port": self.api_port,
            "shared_files": shared_files or [],
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{self.tracker_url}/api/peers/register", json=payload)
                resp.raise_for_status()
                self._is_registered = True
                logger.info("Successfully registered peer %s with tracker", self.peer_id)
                return resp.json()
        except httpx.HTTPError as e:
            logger.error("Failed to register peer %s with tracker: %s", self.peer_id, e)
            return {}

    def heartbeat(
        self, shared_files: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Send heartbeat to maintain online status and optionally update shared files.

        Endpoint: POST /api/peers/heartbeat
        """
        payload: dict[str, Any] = {"peer_id": self.peer_id}
        if shared_files is not None:
            payload["shared_files"] = shared_files

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{self.tracker_url}/api/peers/heartbeat", json=payload)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.warning("Heartbeat failed for peer %s: %s", self.peer_id, e)
            return {}

    def unregister(self) -> bool:
        """Unregister peer from the tracker.

        Endpoint: DELETE /api/peers/{peer_id}
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.delete(f"{self.tracker_url}/api/peers/{self.peer_id}")
                self._is_registered = False
                logger.info("Unregistered peer %s from tracker", self.peer_id)
                return resp.is_success
        except httpx.HTTPError as e:
            logger.error("Failed to unregister peer %s: %s", self.peer_id, e)
            return False

    def get_peers(self) -> list[dict[str, Any]]:
        """Fetch list of all active peers from tracker.

        Endpoint: GET /api/peers
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.tracker_url}/api/peers")
                resp.raise_for_status()
                data = resp.json()
                return data.get("peers", [])
        except httpx.HTTPError as e:
            logger.error("Failed to get peers from tracker: %s", e)
            return []

    def search_files(self, query: str) -> list[dict[str, Any]]:
        """Query tracker for files matching a search query.

        Endpoint: GET /api/files/search?q={query}
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{self.tracker_url}/api/files/search",
                    params={"q": query},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("files", [])
        except httpx.HTTPError as e:
            logger.error("Failed to search files on tracker: %s", e)
            return []

    def get_file_peers(self, file_id: str) -> dict[str, Any]:
        """Fetch online peers hosting a specific file.

        Endpoint: GET /api/files/{file_id}/peers
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.tracker_url}/api/files/{file_id}/peers")
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error("Failed to get peers for file %s: %s", file_id, e)
            return {}

    def report_transfer(self, transfer_info: dict[str, Any]) -> None:
        """Report local transfer activity/progress to tracker.

        Endpoint: POST /api/transfers/report
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self.tracker_url}/api/transfers/report",
                    json=transfer_info,
                )
                resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("Failed to report transfer to tracker: %s", e)

    def _run_heartbeat_cycle(self, interval: float) -> None:
        """Internal execution cycle for sending recurring heartbeats."""
        with self._lock:
            if not self._running:
                return

        try:
            if self._is_registered:
                self.heartbeat()
        except Exception as e:
            logger.warning("Exception in peer registry heartbeat cycle: %s", e)
        finally:
            with self._lock:
                if self._running:
                    self._heartbeat_timer = threading.Timer(
                        interval, self._run_heartbeat_cycle, args=[interval]
                    )
                    self._heartbeat_timer.daemon = True
                    self._heartbeat_timer.start()

    def start_heartbeat(self, interval: float = 25.0) -> None:
        """Start background heartbeat loop to ping tracker every interval seconds."""
        with self._lock:
            self._running = True
            if self._heartbeat_timer is not None:
                self._heartbeat_timer.cancel()
            self._heartbeat_timer = threading.Timer(
                interval, self._run_heartbeat_cycle, args=[interval]
            )
            self._heartbeat_timer.daemon = True
            self._heartbeat_timer.start()
        logger.info("Started heartbeat background loop (interval=%ss)", interval)

    def stop_heartbeat(self) -> None:
        """Stop background heartbeat loop."""
        with self._lock:
            self._running = False
            if self._heartbeat_timer is not None:
                self._heartbeat_timer.cancel()
                self._heartbeat_timer = None
        logger.info("Stopped heartbeat background loop")
