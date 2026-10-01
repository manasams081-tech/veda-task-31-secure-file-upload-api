import io
import os
import tempfile
import unittest
from pathlib import Path

os.environ["UPLOAD_STORAGE_DIR"] = tempfile.mkdtemp(prefix="veda_task31_test_")

from app import app  # noqa: E402


class UploadApiTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_valid_text_upload(self):
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b"hello secure upload"), "hello.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["success"])

    def test_rejects_executable_extension(self):
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b"MZ fake executable"), "malware.exe")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
