import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
import wave
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[2]


class BrowserCycleTest(unittest.TestCase):
    def test_clone_generate_download_and_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            sample = folder / "sample.wav"
            with wave.open(str(sample), "wb") as audio:
                audio.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
                audio.writeframes(b"\0\0" * 800)
            events = folder / "events.jsonl"
            with socket.socket() as address:
                address.bind(("127.0.0.1", 0))
                port = address.getsockname()[1]
            env = dict(os.environ, ELEVENLABS_API_KEY="env-test-key", E2E_VOICE_FILE=str(folder / ".local" / "voice_id"), E2E_EVENTS_FILE=str(events))
            server = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "tests/e2e/e2e_app.py", "--server.headless=true", f"--server.port={port}", "--server.address=127.0.0.1", "--browser.gatherUsageStats=false"],
                cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
            try:
                for _ in range(100):
                    if server.poll() is not None:
                        self.fail(f"Streamlit exited: {server.stderr.read().decode()}")
                    try:
                        urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=0.2).close()
                        break
                    except (OSError, TimeoutError):
                        time.sleep(0.1)
                else:
                    self.fail("Streamlit did not start")

                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    try:
                        page = browser.new_page(accept_downloads=True)
                        page.goto(f"http://127.0.0.1:{port}")
                        page.get_by_role("heading", name="منطوق").wait_for()
                        page.get_by_text("أحد منتجات منفذ").wait_for()
                        self.assertEqual(page.get_by_role("img", name="منفذ").count(), 1)
                        for name in ("منطوق", "نصك، بصوتك", "الاستماع"):
                            heading = page.get_by_role("heading", name=name)
                            self.assertEqual(heading.evaluate("element => getComputedStyle(element).textAlign"), "right")
                        self.assertEqual(page.get_by_text("شيّك هنا بعد توليد الصوت").evaluate("element => getComputedStyle(element).textAlign"), "right")
                        page.get_by_role("textbox", name="معرّف الصوت").fill("library-e2e-id")
                        page.get_by_role("textbox", name="النص العربي").fill("نص تجريبي")
                        page.get_by_role("button", name="مفتاح API").click()
                        page.get_by_role("textbox", name="مفتاح API").fill("test-key")
                        page.get_by_role("button", name="امسح مفتاح API").click()
                        expect(page.get_by_role("textbox", name="مفتاح API")).to_have_value("")
                        page.get_by_text("مفتاح API مطلوب").wait_for()
                        page.wait_for_function("() => new URLSearchParams(location.search).get('api_key_cleared') === '1'")
                        page.reload()
                        page.get_by_text("مفتاح API مطلوب").wait_for()
                        page.get_by_role("button", name="ولّد الصوت").click()
                        page.get_by_text("أدخل مفتاح ElevenLabs API.").wait_for()
                        self.assertFalse(events.exists())
                        page.get_by_role("button", name="مفتاح API").click()
                        page.get_by_role("textbox", name="مفتاح API").fill("test-key")
                        page.get_by_role("tab", name="استنساخ صوت").click()
                        page.get_by_role("button", name="استنسخ الصوت").click()
                        page.get_by_text("ارفع تسجيلًا صوتيًا غير فارغ.").wait_for()
                        self.assertTrue(page.get_by_text("ارفع تسجيلًا صوتيًا غير فارغ.").is_visible())
                        self.assertFalse(events.exists())
                        page.locator('input[type="file"]').set_input_files(str(sample))
                        page.get_by_role("button", name="استنسخ الصوت").click()
                        page.get_by_text("أدخل اسمًا للصوت.").wait_for()
                        self.assertFalse(events.exists())
                        page.get_by_role("textbox", name="اسم الصوت").fill("صوت تجريبي")
                        page.get_by_role("button", name="استنسخ الصوت").click()
                        page.get_by_text("استنسخت صوتك وحفظته للاستخدام تلقائيًا.", exact=False).wait_for()
                        self.assertEqual((folder / ".local" / "voice_id").read_text().strip(), "cloned-e2e-id")

                        page.get_by_role("tab", name="توليد الصوت").click()
                        page.get_by_role("button", name="إعدادات النبرة").click()
                        page.get_by_role("spinbutton", name="النبرة").wait_for()
                        page.get_by_role("button", name="نبرة جديدة").click()
                        generated_seed = int(page.get_by_role("spinbutton", name="النبرة").input_value())
                        self.assertIn(generated_seed, json.loads((folder / ".local" / "seeds.json").read_text()))
                        page.keyboard.press("Escape")
                        page.get_by_role("button", name="ولّد الصوت").click()
                        page.get_by_text("أدخل النص المراد تحويله إلى صوت.").wait_for()
                        self.assertTrue(page.get_by_text("أدخل النص المراد تحويله إلى صوت.").is_visible())
                        page.get_by_role("textbox", name="النص العربي").fill("مرحبًا بالعالم")
                        page.get_by_role("button", name="ولّد الصوت").click()
                        page.get_by_role("button", name="حمّل ملف MP3").wait_for()
                        self.assertTrue(page.locator("audio").is_visible())
                        with page.expect_download() as download_info:
                            page.get_by_role("button", name="حمّل ملف MP3").click()
                        download = download_info.value
                        self.assertEqual(download.suggested_filename, "speech.mp3")
                        saved = folder / "speech.mp3"
                        download.save_as(saved)
                        self.assertEqual(saved.read_bytes(), b"ID3\x04\x00\x00\x00\x00\x00\x00")

                        page.get_by_role("radio", name="صوت من المكتبة").click()
                        page.get_by_role("textbox", name="معرّف الصوت").fill("library-e2e-id")
                        page.get_by_role("textbox", name="النص العربي").fill("نص من المكتبة")
                        page.get_by_role("button", name="ولّد الصوت").click()
                        for _ in range(50):
                            if len(list((folder / ".local" / "generated_audio").glob("*.mp3"))) == 2:
                                break
                            time.sleep(0.1)
                        self.assertEqual(len(list((folder / ".local" / "generated_audio").glob("*.mp3"))), 2)

                        page.get_by_role("textbox", name="النص العربي").fill("E2E_FAIL")
                        page.get_by_role("button", name="ولّد الصوت").click()
                        page.get_by_text("تعذّر توليد الصوت.", exact=False).wait_for()
                        self.assertEqual(page.get_by_role("button", name="حمّل ملف MP3").count(), 1)
                        self.assertTrue(page.locator("audio").is_visible())
                        page.get_by_role("tab", name="الأصوات المحفوظة").click()
                        page.get_by_text("تسجيل 2").wait_for()
                        self.assertEqual(page.locator("audio").count(), 2)
                        page.get_by_role("button", name="حمّل ملف MP3").first.hover()
                        page.get_by_text(f"رقم النبرة: {generated_seed}").wait_for()
                        page.reload()
                        page.get_by_role("tab", name="الأصوات المحفوظة").click()
                        page.get_by_text("تسجيل 2").wait_for()
                        self.assertEqual(len(list((folder / ".local" / "generated_audio").glob("*.mp3"))), 2)
                        self.assertEqual([json.loads(line) for line in events.read_text().splitlines()], [
                            {"action": "clone", "name": "صوت تجريبي", "filename": "sample.wav", "has_key": True},
                            {"action": "speak", "text": "مرحبًا بالعالم", "voice_id": "cloned-e2e-id", "seed": generated_seed, "has_key": True},
                            {"action": "speak", "text": "نص من المكتبة", "voice_id": "library-e2e-id", "seed": generated_seed, "has_key": True},
                            {"action": "speak", "text": "E2E_FAIL", "voice_id": "library-e2e-id", "seed": generated_seed, "has_key": True},
                        ])
                    finally:
                        browser.close()
            finally:
                server.terminate()
                try:
                    server.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.communicate()


if __name__ == "__main__":
    unittest.main()
