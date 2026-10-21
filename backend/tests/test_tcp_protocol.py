"""Tests for the TCP binary wire protocol framing and message handling."""

import json
import socket
import struct
import pytest
from app.core.tcp_protocol import (
    PROTOCOL_MAGIC,
    PROTOCOL_VERSION,
    HEADER_SIZE,
    MessageType,
    ErrorCode,
    ProtocolError,
    pack_header,
    unpack_header,
    recv_exact,
    send_all,
    send_message,
    recv_message,
    send_file_request,
    recv_file_request,
    send_file_response,
    recv_file_response,
    send_file_data,
    send_transfer_complete,
    recv_transfer_complete,
    send_error,
    send_cancel,
)


@pytest.fixture
def socket_pair():
    """Create a connected pair of local sockets."""
    s1, s2 = socket.socketpair()
    s1.settimeout(2.0)
    s2.settimeout(2.0)
    try:
        yield s1, s2
    finally:
        s1.close()
        s2.close()


def test_pack_unpack_header():
    """pack_header and unpack_header serialize and deserialize accurately."""
    msg_type = MessageType.FILE_REQUEST
    payload_len = 1024
    
    header_bytes = pack_header(msg_type, payload_len)
    assert len(header_bytes) == HEADER_SIZE

    version, unpacked_type, unpacked_len = unpack_header(header_bytes)
    assert version == PROTOCOL_VERSION
    assert unpacked_type == msg_type
    assert unpacked_len == payload_len


def test_send_recv_message(socket_pair):
    """send_message and recv_message roundtrip data correctly."""
    s1, s2 = socket_pair
    payload = b"Hello socket messaging!"
    
    send_message(s1, MessageType.FILE_DATA, payload)
    msg_type, received_payload = recv_message(s2)

    assert msg_type == MessageType.FILE_DATA
    assert received_payload == payload


def test_file_request_roundtrip(socket_pair):
    """send_file_request and recv_file_request preserve request fields."""
    s1, s2 = socket_pair
    file_id = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    filename = "document.pdf"

    send_file_request(s1, file_id=file_id, filename=filename)
    req = recv_file_request(s2)

    assert req["file_id"] == file_id
    assert req["filename"] == filename


def test_file_response_roundtrip(socket_pair):
    """send_file_response and recv_file_response preserve file metadata."""
    s1, s2 = socket_pair
    send_file_response(
        s1,
        status="ok",
        filename="image.png",
        file_size=20480,
        checksum="1234567890abcdef",
        error_message=None,
    )
    res = recv_file_response(s2)

    assert res["status"] == "ok"
    assert res["filename"] == "image.png"
    assert res["file_size"] == 20480
    assert res["checksum"] == "1234567890abcdef"
    assert res.get("error_message") is None


def test_invalid_magic():
    """Unpacking a header with invalid magic bytes raises ProtocolError."""
    # Create valid header, then corrupt magic bytes
    valid_header = pack_header(MessageType.FILE_REQUEST, 100)
    bad_header = b"XX" + valid_header[2:]

    with pytest.raises(ProtocolError) as exc_info:
        unpack_header(bad_header)
    assert "Invalid protocol magic" in str(exc_info.value)


def test_invalid_version():
    """Unpacking a header with an unsupported version raises ProtocolError."""
    bad_header = struct.pack("!2sBBI", PROTOCOL_MAGIC, 99, int(MessageType.FILE_REQUEST), 100)
    with pytest.raises(ProtocolError) as exc_info:
        unpack_header(bad_header)
    assert "Unsupported protocol version" in str(exc_info.value)


def test_recv_exact_partial():
    """recv_exact correctly reads across multiple partial chunks."""
    class ChunkedSocketMock:
        def __init__(self, data: bytes, chunk_size: int = 3):
            self.data = data
            self.offset = 0
            self.chunk_size = chunk_size

        def recv_into(self, buffer, nbytes=None):
            if self.offset >= len(self.data):
                return 0
            remaining = len(self.data) - self.offset
            to_read = min(self.chunk_size, remaining)
            if nbytes is not None:
                to_read = min(to_read, nbytes)
            buffer[:to_read] = self.data[self.offset : self.offset + to_read]
            self.offset += to_read
            return to_read

    data = b"Testing partial chunk reads in socket"
    mock_sock = ChunkedSocketMock(data, chunk_size=4)
    result = recv_exact(mock_sock, len(data))
    assert result == data


def test_recv_exact_disconnect(socket_pair):
    """recv_exact raises ConnectionError if peer disconnects prematurely."""
    s1, s2 = socket_pair
    # Close sender immediately
    s1.close()
    with pytest.raises(ConnectionError):
        recv_exact(s2, 10)


def test_send_error(socket_pair):
    """send_error transmits structured error and message."""
    s1, s2 = socket_pair
    send_error(s1, ErrorCode.FILE_NOT_FOUND, "Target file does not exist")
    msg_type, payload = recv_message(s2)

    assert msg_type == MessageType.ERROR
    data = json.loads(payload.decode("utf-8"))
    assert data["code"] == 404
    assert data["message"] == "Target file does not exist"


def test_send_cancel(socket_pair):
    """send_cancel sends a CANCEL message."""
    s1, s2 = socket_pair
    send_cancel(s1)
    msg_type, payload = recv_message(s2)

    assert msg_type == MessageType.CANCEL


def test_file_data(socket_pair):
    """send_file_data sends raw binary chunks as FILE_DATA."""
    s1, s2 = socket_pair
    raw_chunk = b"\x00\x01\x02\xff" * 256
    send_file_data(s1, raw_chunk)

    msg_type, payload = recv_message(s2)
    assert msg_type == MessageType.FILE_DATA
    assert payload == raw_chunk


def test_transfer_complete(socket_pair):
    """send_transfer_complete and recv_transfer_complete roundtrip final checksum."""
    s1, s2 = socket_pair
    expected_sum = "abcdef0123456789abcdef0123456789"
    send_transfer_complete(s1, expected_sum)

    data = recv_transfer_complete(s2)
    assert data["checksum"] == expected_sum
