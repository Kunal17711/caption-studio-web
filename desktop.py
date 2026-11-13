"""Caption Studio 2.1: offline Windows desktop shell around the local FastAPI editor."""
from __future__ import annotations
import atexit
import socket
import threading
import time
import urllib.request

import uvicorn
import webview
from server import app


def available_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    port = available_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, access_log=False, log_level="warning")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, name="caption-local-api", daemon=True).start()
    atexit.register(lambda: setattr(server, "should_exit", True))

    url = f"http://127.0.0.1:{port}"
    for _ in range(120):
        try:
            with urllib.request.urlopen(url + "/api/health", timeout=1) as res:
                if res.status == 200:
                    break
        except Exception:
            time.sleep(0.15)
    else:
        raise RuntimeError("Local Caption Studio server could not start")

    webview.create_window("Caption Studio | Free Desktop Editor", url, width=1440, height=900,
                          min_size=(1000, 650), background_color="#0b101d")
    try:
        webview.start(gui="edge", debug=False)
    finally:
        server.should_exit = True


if __name__ == "__main__":
    main()
