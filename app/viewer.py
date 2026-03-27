from __future__ import annotations

import http.server
import os
import socketserver
import webbrowser
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PORT = 8765
PID_FILE = ROOT_DIR / '.viewer.pid'


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:
        # pythonw 실행 시 stderr가 없어 요청 로그 출력에서 깨질 수 있으므로 무시합니다.
        return


def main() -> None:
    url = f"http://localhost:{DEFAULT_PORT}/web/index.html"

    try:
        with ReusableTCPServer(("", DEFAULT_PORT), NoCacheHandler) as server:
            PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

            print(f"Starting calendar server: {url}")
            print("If the browser does not open, visit the URL above.")
            webbrowser.open(url)

            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nServer stopped.")
            finally:
                if PID_FILE.exists() and PID_FILE.read_text(encoding="utf-8").strip() == str(os.getpid()):
                    PID_FILE.unlink(missing_ok=True)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 10048:
            webbrowser.open(url)
            return
        raise


if __name__ == "__main__":
    main()
