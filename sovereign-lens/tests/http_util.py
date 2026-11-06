"""Raw HTTP/1.0 and HTTP/1.1 exchanges that keep every byte the server writes."""
import json
import re
import socket

STATUS_RE = re.compile(br"HTTP/1\.[01] \d{3}")


def exchange(port, method, path, body=b"", headers=None):
    header_lines = [
        f"{method} {path} HTTP/1.1",
        "Host: 127.0.0.1",
        "Connection: close",
        "Accept: */*",
    ]
    for key, value in (headers or {}).items():
        header_lines.append(f"{key}: {value}")
    if body:
        header_lines.append("Content-Type: application/json")
        header_lines.append(f"Content-Length: {len(body)}")
    raw_request = ("\r\n".join(header_lines) + "\r\n\r\n").encode() + body
    sock = socket.create_connection(("127.0.0.1", port), 3)
    try:
        sock.sendall(raw_request)
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        sock.close()
    data = b"".join(chunks)
    return data, parse_response(data)


def parse_response(data):
    statuses = STATUS_RE.findall(data)
    if not data.startswith(b"HTTP/"):
        raise AssertionError(f"response does not start with a status line: {data[:120]!r}")
    try:
        header_blob, rest = data.split(b"\r\n\r\n", 1)
    except ValueError as exc:
        raise AssertionError("response has no header terminator") from exc
    lines = header_blob.split(b"\r\n")
    headers = {}
    for line in lines[1:]:
        if b":" not in line:
            continue
        key, value = line.split(b":", 1)
        headers[key.decode().lower()] = value.strip().decode()
    return {
        "status_line": lines[0].decode(),
        "status_count": len(statuses),
        "headers": headers,
        "body": rest,
        "raw": data,
    }


def assert_single_response(parsed, expected_status):
    assert parsed["status_count"] == 1, parsed["raw"][:400]
    assert int(parsed["status_line"].split()[1]) == expected_status, parsed["status_line"]
    assert "content-length" in parsed["headers"]
    assert int(parsed["headers"]["content-length"]) == len(parsed["body"])
    # Nothing after the declared body: a second response would show up here
    # or as a second status line.
    assert parsed["raw"].endswith(parsed["body"])


def json_body(parsed):
    return json.loads(parsed["body"].decode())
