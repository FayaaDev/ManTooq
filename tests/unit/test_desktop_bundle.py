"""Smoke-test a built server from a directory outside the source tree."""

import socket
import subprocess
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class DesktopBundleTest(unittest.TestCase):
    def test_bundled_server_starts_outside_repository(self):
        binary = Path(__file__).resolve().parents[2] / "dist/mantooq-server/mantooq-server"
        if not binary.exists():
            self.skipTest("Build with scripts/build-macos.sh first")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with tempfile.TemporaryDirectory() as folder:
            process = subprocess.Popen(
                [str(binary), f"--server.port={port}"], cwd=folder,
                env={"MANTOOQ_DATA_DIR": str(Path(folder) / "data"), "PATH": "/usr/bin:/bin"},
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        self.fail(f"packaged server exited: {process.returncode}: {process.stderr.read().decode()}")
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
                            self.assertEqual(response.status, 200)
                        with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=1) as response:
                            self.assertEqual(response.status, 200)
                        with sync_playwright() as playwright:
                            browser = playwright.chromium.launch()
                            try:
                                page = browser.new_page()
                                page.goto(f"http://127.0.0.1:{port}")
                                try:
                                    page.get_by_role("heading", name="منطوق").wait_for(timeout=15000)
                                except PlaywrightTimeoutError:
                                    self.fail(f"bundled page did not render: {page.locator('body').inner_text()}")
                                self.assertEqual(page.get_by_role("heading", name="منطوق").evaluate(
                                    "node => getComputedStyle(node).textAlign"), "right")
                                page.wait_for_function("Array.from(document.fonts).some(font => font.family === 'Thmanyah')")
                                self.assertGreater(len(page.evaluate("document.fonts.load('700 16px Thmanyah')")), 0)
                            finally:
                                browser.close()
                        break
                    except OSError:
                        time.sleep(0.3)
                else:
                    self.fail("packaged server did not start")
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                process.stderr.close()


if __name__ == "__main__":
    unittest.main()
