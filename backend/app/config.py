"""Configuration settings for Tracker and Peer nodes."""

import uuid
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TrackerConfig(BaseSettings):
    """Configuration for the Tracker server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )

    host: str = Field(
        default="0.0.0.0",
        validation_alias=AliasChoices("host", "TRACKER_HOST"),
    )
    port: int = Field(
        default=8000,
        validation_alias=AliasChoices("port", "TRACKER_PORT"),
    )
    db_path: str = Field(
        default="tracker.db",
        validation_alias=AliasChoices("db_path", "TRACKER_DB_PATH"),
    )
    heartbeat_timeout: int = Field(
        default=30,
        validation_alias=AliasChoices("heartbeat_timeout", "HEARTBEAT_TIMEOUT"),
    )
    peer_expiry_seconds: int = Field(
        default=90,
        validation_alias=AliasChoices("peer_expiry_seconds", "PEER_EXPIRY_SECONDS"),
    )
    max_file_size: int = Field(
        default=1_073_741_824,  # 1 GB
        validation_alias=AliasChoices("max_file_size", "MAX_FILE_SIZE"),
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        validation_alias=AliasChoices("cors_origins", "CORS_ORIGINS"),
    )


class PeerConfig(BaseSettings):
    """Configuration for a Peer node."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )

    peer_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        validation_alias=AliasChoices("peer_id", "PEER_ID"),
    )
    host: str = Field(
        default="0.0.0.0",
        validation_alias=AliasChoices("host", "PEER_HOST"),
    )
    tcp_port: int = Field(
        default=9001,
        validation_alias=AliasChoices("tcp_port", "PEER_TCP_PORT"),
    )
    api_port: int = Field(
        default=8001,
        validation_alias=AliasChoices("api_port", "PEER_API_PORT"),
    )
    tracker_url: str = Field(
        default="http://localhost:8000",
        validation_alias=AliasChoices("tracker_url", "TRACKER_URL"),
    )
    shared_dir: str = Field(
        default="./shared",
        validation_alias=AliasChoices("shared_dir", "SHARED_DIR"),
    )
    download_dir: str = Field(
        default="./downloads",
        validation_alias=AliasChoices("download_dir", "DOWNLOAD_DIR"),
    )
    chunk_size: int = Field(
        default=65536,
        validation_alias=AliasChoices("chunk_size", "CHUNK_SIZE"),
    )
    max_connections: int = Field(
        default=10,
        validation_alias=AliasChoices("max_connections", "MAX_CONNECTIONS"),
    )
    socket_timeout: int = Field(
        default=30,
        validation_alias=AliasChoices("socket_timeout", "SOCKET_TIMEOUT"),
    )
    max_file_size: int = Field(
        default=1_073_741_824,  # 1 GB
        validation_alias=AliasChoices("max_file_size", "MAX_FILE_SIZE"),
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        validation_alias=AliasChoices("cors_origins", "CORS_ORIGINS"),
    )

    @field_validator("peer_id", mode="before")
    @classmethod
    def set_default_peer_id(cls, v: str | None) -> str:
        """Fallback to a newly generated UUID if peer_id is empty or None."""
        if not v:
            return uuid.uuid4().hex
        return str(v)
