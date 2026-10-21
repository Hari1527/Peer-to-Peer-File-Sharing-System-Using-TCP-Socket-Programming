"""Core TCP wire protocol implementation for P2P file sharing.

Defines the binary frame header, message types, error codes, and helper
functions to serialize and deserialize messages over raw TCP sockets.
"""

from enum import IntEnum
import json
import logging
import socket
import struct
from typing import Any

logger = logging.getLogger(__name__)

# Protocol framing constants
PROTOCOL_MAGIC: bytes = b"\x50\x32"  # ASCII 'P2'
PROTOCOL_VERSION: int = 1
HEADER_SIZE: int = 8  # 2 bytes magic + 1 byte version + 1 byte type + 4 bytes length
HEADER_FORMAT: str = "!2sBBI"  # Network big-endian: 2-byte magic, uint8 version, uint8 type, uint32 length
MAX_PAYLOAD_SIZE: int = 100 * 1024 * 1024  # 100 MB safety limit
DEFAULT_CHUNK_SIZE: int = 65536  # 64 KB


class MessageType(IntEnum):
    """Enumeration of TCP protocol message types."""
    FILE_REQUEST = 1
    FILE_RESPONSE = 2
    FILE_DATA = 3
    TRANSFER_COMPLETE = 4
    ERROR = 5
    CANCEL = 6


class ErrorCode(IntEnum):
    """Enumeration of protocol-level error codes."""
    INVALID_REQUEST = 400
    FILE_NOT_FOUND = 404
    TRANSFER_CANCELLED = 499
    SERVER_ERROR = 500
    UNSUPPORTED_VERSION = 505


class ProtocolError(Exception):
    """Exception raised for violations of the wire protocol."""

    def __init__(self, message: str, code: ErrorCode | int = ErrorCode.SERVER_ERROR):
        super().__init__(message)
        self.message = message
        self.code = code if isinstance(code, ErrorCode) else ErrorCode(code) if code in [e.value for e in ErrorCode] else ErrorCode.SERVER_ERROR

    def __str__(self) -> str:
        return f"[ProtocolError {self.code.value} {self.code.name}]: {self.message}"


def pack_header(msg_type: MessageType, payload_length: int) -> bytes:
    """Pack protocol header into 8 bytes.

    Args:
        msg_type: MessageType enum value.
        payload_length: Length of the payload in bytes.

    Returns:
        bytes: 8-byte packed header.

    Raises:
        ProtocolError: If payload length exceeds MAX_PAYLOAD_SIZE or is negative.
    """
    if payload_length < 0 or payload_length > MAX_PAYLOAD_SIZE:
        raise ProtocolError(
            f"Invalid payload length: {payload_length} (max allowed {MAX_PAYLOAD_SIZE})",
            code=ErrorCode.INVALID_REQUEST,
        )
    return struct.pack(HEADER_FORMAT, PROTOCOL_MAGIC, PROTOCOL_VERSION, int(msg_type), payload_length)


def unpack_header(header: bytes) -> tuple[int, MessageType, int]:
    """Unpack and validate an 8-byte protocol header.

    Args:
        header: 8-byte header bytes.

    Returns:
        tuple[int, MessageType, int]: (version, msg_type, payload_length)

    Raises:
        ProtocolError: On invalid header size, bad magic, unsupported version,
                       or unknown message type.
    """
    if len(header) != HEADER_SIZE:
        raise ProtocolError(
            f"Invalid header size: expected {HEADER_SIZE} bytes, got {len(header)}",
            code=ErrorCode.INVALID_REQUEST,
        )

    magic, version, type_val, payload_length = struct.unpack(HEADER_FORMAT, header)

    if magic != PROTOCOL_MAGIC:
        raise ProtocolError(
            f"Invalid protocol magic bytes: {magic!r}",
            code=ErrorCode.INVALID_REQUEST,
        )

    if version != PROTOCOL_VERSION:
        raise ProtocolError(
            f"Unsupported protocol version {version} (expected {PROTOCOL_VERSION})",
            code=ErrorCode.UNSUPPORTED_VERSION,
        )

    try:
        msg_type = MessageType(type_val)
    except ValueError:
        raise ProtocolError(
            f"Unknown message type: {type_val}",
            code=ErrorCode.INVALID_REQUEST,
        )

    if payload_length > MAX_PAYLOAD_SIZE:
        raise ProtocolError(
            f"Payload length {payload_length} exceeds limit of {MAX_PAYLOAD_SIZE} bytes",
            code=ErrorCode.INVALID_REQUEST,
        )

    return version, msg_type, payload_length


def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes from a socket.

    Loops on recv() until n bytes are received or connection is lost.

    Args:
        sock: Connected socket.
        n: Number of bytes to receive.

    Returns:
        bytes: Exactly n bytes.

    Raises:
        ConnectionError: If peer disconnects before n bytes are read.
        socket.timeout: If socket read times out.
    """
    if n == 0:
        return b""

    buf = bytearray(n)
    view = memoryview(buf)
    bytes_read = 0

    while bytes_read < n:
        try:
            chunk_size = sock.recv_into(view[bytes_read:], n - bytes_read)
        except (ConnectionResetError, BrokenPipeError) as e:
            raise ConnectionError(f"Connection closed by peer after {bytes_read}/{n} bytes") from e

        if chunk_size == 0:
            raise ConnectionError(f"Connection closed by peer after {bytes_read}/{n} bytes")
        bytes_read += chunk_size

    return bytes(buf)


def send_all(sock: socket.socket, data: bytes) -> None:
    """Send all data through the socket.

    Args:
        sock: Connected socket.
        data: Bytes to send.

    Raises:
        ConnectionError: If peer closes the connection during sending.
        socket.timeout: If sending times out.
    """
    try:
        sock.sendall(data)
    except (ConnectionResetError, BrokenPipeError) as e:
        raise ConnectionError(f"Failed to send data: socket closed by peer") from e


def send_message(sock: socket.socket, msg_type: MessageType, payload: bytes = b"") -> None:
    """Send a framed protocol message (header + payload).

    Args:
        sock: Connected socket.
        msg_type: Type of the message.
        payload: Binary payload bytes (empty by default).
    """
    header = pack_header(msg_type, len(payload))
    send_all(sock, header + payload)


def recv_message(sock: socket.socket) -> tuple[MessageType, bytes]:
    """Receive a framed protocol message.

    Reads the 8-byte header, decodes it, and reads the full payload.

    Args:
        sock: Connected socket.

    Returns:
        tuple[MessageType, bytes]: (msg_type, payload)

    Raises:
        ProtocolError: If header validation fails.
        ConnectionError: If connection is broken.
        socket.timeout: If socket read times out.
    """
    header_bytes = recv_exact(sock, HEADER_SIZE)
    _, msg_type, payload_length = unpack_header(header_bytes)
    payload = recv_exact(sock, payload_length) if payload_length > 0 else b""
    return msg_type, payload


# =========================================================================
# Specialized message senders and receivers
# =========================================================================

def send_file_request(sock: socket.socket, file_id: str, filename: str) -> None:
    """Send a FILE_REQUEST message with JSON payload.

    Args:
        sock: Connected socket.
        file_id: SHA-256 hex digest of file.
        filename: Requested filename.
    """
    payload_dict = {"file_id": file_id, "filename": filename}
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    send_message(sock, MessageType.FILE_REQUEST, payload_bytes)


def recv_file_request(sock: socket.socket) -> dict[str, Any]:
    """Receive and parse a FILE_REQUEST message.

    Args:
        sock: Connected socket.

    Returns:
        dict: Parsed JSON with 'file_id' and 'filename'.

    Raises:
        ProtocolError: If message is not FILE_REQUEST or JSON is malformed.
    """
    msg_type, payload = recv_message(sock)
    if msg_type != MessageType.FILE_REQUEST:
        raise ProtocolError(
            f"Expected FILE_REQUEST ({MessageType.FILE_REQUEST.name}), got {msg_type.name}",
            code=ErrorCode.INVALID_REQUEST,
        )
    try:
        data = json.loads(payload.decode("utf-8"))
    except Exception as e:
        raise ProtocolError(f"Malformed FILE_REQUEST JSON: {e}", code=ErrorCode.INVALID_REQUEST) from e

    if not isinstance(data, dict):
        raise ProtocolError("FILE_REQUEST payload must be a JSON object", code=ErrorCode.INVALID_REQUEST)

    return {"file_id": data.get("file_id", ""), "filename": data.get("filename", "")}


def send_file_response(
    sock: socket.socket,
    status: str,
    filename: str,
    file_size: int,
    checksum: str,
    error_message: str | None = None,
) -> None:
    """Send a FILE_RESPONSE message with JSON payload.

    Args:
        sock: Connected socket.
        status: "ok" or "error"
        filename: File name.
        file_size: Size in bytes.
        checksum: SHA-256 checksum string.
        error_message: Optional error message if status is "error".
    """
    payload_dict = {
        "status": status,
        "filename": filename,
        "file_size": file_size,
        "checksum": checksum,
        "error_message": error_message,
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    send_message(sock, MessageType.FILE_RESPONSE, payload_bytes)


def recv_file_response(sock: socket.socket) -> dict[str, Any]:
    """Receive and parse a FILE_RESPONSE message.

    Handles both FILE_RESPONSE and incoming ERROR messages.

    Args:
        sock: Connected socket.

    Returns:
        dict: Parsed file response dictionary.

    Raises:
        ProtocolError: If response is ERROR or invalid message type.
    """
    msg_type, payload = recv_message(sock)
    if msg_type == MessageType.ERROR:
        try:
            err_data = json.loads(payload.decode("utf-8"))
        except Exception:
            err_data = {"code": int(ErrorCode.SERVER_ERROR), "message": "Unknown server error"}
        raise ProtocolError(
            err_data.get("message", "Error from peer"),
            code=err_data.get("code", ErrorCode.SERVER_ERROR),
        )

    if msg_type != MessageType.FILE_RESPONSE:
        raise ProtocolError(
            f"Expected FILE_RESPONSE ({MessageType.FILE_RESPONSE.name}), got {msg_type.name}",
            code=ErrorCode.INVALID_REQUEST,
        )

    try:
        data = json.loads(payload.decode("utf-8"))
    except Exception as e:
        raise ProtocolError(f"Malformed FILE_RESPONSE JSON: {e}", code=ErrorCode.INVALID_REQUEST) from e

    return data


def send_file_data(sock: socket.socket, chunk: bytes) -> None:
    """Send a chunk of raw binary data as FILE_DATA message.

    Args:
        sock: Connected socket.
        chunk: Raw binary bytes.
    """
    send_message(sock, MessageType.FILE_DATA, chunk)


def send_transfer_complete(sock: socket.socket, checksum: str) -> None:
    """Send a TRANSFER_COMPLETE message with the final file checksum.

    Args:
        sock: Connected socket.
        checksum: SHA-256 checksum string.
    """
    payload_dict = {"checksum": checksum}
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    send_message(sock, MessageType.TRANSFER_COMPLETE, payload_bytes)


def recv_transfer_complete(sock: socket.socket) -> dict[str, Any]:
    """Receive and parse a TRANSFER_COMPLETE message.

    Args:
        sock: Connected socket.

    Returns:
        dict: Parsed dictionary containing 'checksum'.
    """
    msg_type, payload = recv_message(sock)
    if msg_type != MessageType.TRANSFER_COMPLETE:
        raise ProtocolError(
            f"Expected TRANSFER_COMPLETE ({MessageType.TRANSFER_COMPLETE.name}), got {msg_type.name}",
            code=ErrorCode.INVALID_REQUEST,
        )
    try:
        return json.loads(payload.decode("utf-8"))
    except Exception as e:
        raise ProtocolError(f"Malformed TRANSFER_COMPLETE JSON: {e}", code=ErrorCode.INVALID_REQUEST) from e


def send_error(sock: socket.socket, code: ErrorCode | int, message: str) -> None:
    """Send an ERROR message with code and message description.

    Args:
        sock: Connected socket.
        code: ErrorCode enum or int code.
        message: Descriptive error message.
    """
    code_val = int(code.value if isinstance(code, ErrorCode) else code)
    payload_dict = {"code": code_val, "message": message}
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    send_message(sock, MessageType.ERROR, payload_bytes)


def send_cancel(sock: socket.socket) -> None:
    """Send a CANCEL message to abort an in-progress transfer.

    Args:
        sock: Connected socket.
    """
    send_message(sock, MessageType.CANCEL, b"{}")
