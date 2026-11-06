"""Live server fixtures. Each test module shares one process per auth mode."""
import os
import socket
import subprocess
import sys
import time

import pytest

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(APP_ROOT, "backend", "server.py")


def _free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _wait_until_up(proc, port):
    deadline = time.time() + 5
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited {proc.returncode}")
        try:
            with socket.create_connection(("127.0.0.1", port), 0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError("server did not accept connections")


class RunningServer:
    def __init__(self, port, api_key):
        self.port = port
        self.api_key = api_key
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["HOST"] = "127.0.0.1"
        if api_key:
            env["SOVEREIGN_API_KEY"] = api_key
        else:
            env.pop("SOVEREIGN_API_KEY", None)
        self.proc = subprocess.Popen(
            [sys.executable, SERVER],
            cwd=APP_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        try:
            _wait_until_up(self.proc, port)
        except Exception:
            err = b""
            if self.proc.stderr:
                err = self.proc.stderr.read()
            self.proc.kill()
            raise RuntimeError(err.decode("utf-8", "replace"))

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()


@pytest.fixture(scope="module")
def auth_server():
    server = RunningServer(_free_port(), "test-key")
    yield server
    server.stop()


@pytest.fixture(scope="module")
def open_server():
    server = RunningServer(_free_port(), "")
    yield server
    server.stop()
