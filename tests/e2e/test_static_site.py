import json
import tempfile
import threading
import unittest
import wave
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright


WEB = Path(__file__).resolve().parents[2] / "web"


class StaticSiteTest(unittest.TestCase):
    def test_clone_generate_download_and_browser_persistence(self):
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(WEB), **kwargs)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as folder, sync_playwright() as playwright:
                sample = Path(folder) / "sample.wav"
                with wave.open(str(sample), "wb") as audio:
                    audio.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
                    audio.writeframes(b"\0\0" * 800)

                browser = playwright.chromium.launch()
                try:
                    page = browser.new_page(accept_downloads=True)
                    calls = []

                    def mock_api(route):
                        request = route.request
                        calls.append(request)
                        self.assertEqual(request.headers["xi-api-key"], "visitor-key")
                        if request.url.endswith("/voices/add"):
                            self.assertIn('name="files"', request.post_data)
                            route.fulfill(status=200, content_type="application/json", body='{"voice_id":"cloned-id"}')
                        else:
                            payload = request.post_data_json
                            self.assertEqual(payload["model_id"], "eleven_v3")
                            self.assertEqual(payload["voice_settings"]["speed"], 0.95)
                            self.assertEqual(payload["text"], "مرحبًا بالعالم")
                            route.fulfill(status=200, content_type="audio/mpeg", body=b"ID3\x04\x00test")

                    page.route("https://api.elevenlabs.io/**", mock_api)
                    page.goto(f"http://127.0.0.1:{server.server_port}/")
                    self.assertEqual(page.locator("html").get_attribute("dir"), "rtl")
                    page.get_by_role("button", name="ولّد الصوت").click()
                    page.get_by_text("أدخل مفتاح ElevenLabs API.").wait_for()
                    self.assertEqual(calls, [])
                    page.locator("#key-menu summary").click()
                    page.get_by_label("مفتاح ElevenLabs").fill("visitor-key")
                    page.get_by_role("tab", name="استنساخ صوت").click()
                    page.get_by_role("button", name="استنسخ الصوت").click()
                    page.get_by_text("ارفع تسجيلًا صوتيًا غير فارغ.").wait_for()
                    page.locator("#sample").set_input_files(str(sample))
                    page.get_by_label("اسم الصوت").fill("صوتي")
                    page.get_by_role("button", name="استنسخ الصوت").click()
                    page.get_by_text("استنسخت صوتك وحفظته للاستخدام تلقائيًا.").wait_for()
                    page.get_by_role("tab", name="توليد الصوت").click()
                    page.get_by_label("النص العربي").fill("مرحبًا بالعالم")
                    page.get_by_role("button", name="ولّد الصوت").click()
                    page.get_by_text("صوتك جاهز للاستماع والتحميل.").wait_for()
                    self.assertEqual(len(calls), 2)
                    self.assertTrue(calls[1].url.endswith("/cloned-id?output_format=mp3_44100_128"))
                    page.get_by_role("radio", name="اصوات مختارة").click()
                    self.assertEqual(page.get_by_label("الصوت المختار").input_value(), "cFUFIbKkO2iZFwS8cRnY")
                    page.get_by_role("button", name="ولّد الصوت").click()
                    self.assertEqual(len(calls), 3)
                    self.assertTrue(calls[2].url.endswith("/cFUFIbKkO2iZFwS8cRnY?output_format=mp3_44100_128"))
                    with page.expect_download() as download_info:
                        page.get_by_role("link", name="حمّل ملف MP3").click()
                    self.assertEqual(download_info.value.suggested_filename, "speech.mp3")
                    page.reload()
                    self.assertEqual(page.get_by_label("مفتاح ElevenLabs").input_value(), "visitor-key")
                    page.get_by_role("tab", name="الأصوات المحفوظة").click()
                    page.get_by_text("تسجيل 2").wait_for()
                    self.assertEqual(page.locator("#recordings audio").count(), 2)
                    self.assertEqual(page.evaluate("localStorage.getItem('mantooq:voice')"), "cloned-id")
                    self.assertNotIn("visitor-key", json.dumps(page.evaluate("Object.entries(localStorage).filter(([key]) => key !== 'mantooq:key')")))
                    page.locator("#key-menu summary").click()
                    page.get_by_role("button", name="امسح مفتاح API").click()
                    self.assertIsNone(page.evaluate("localStorage.getItem('mantooq:key')"))
                    page.reload()
                    self.assertEqual(page.get_by_label("مفتاح ElevenLabs").input_value(), "")
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
