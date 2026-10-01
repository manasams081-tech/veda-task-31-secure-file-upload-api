from pathlib import Path
import json
import os
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
# Intentionally outside the application directory by default.
DEFAULT_STORAGE = Path.home() / "veda_secure_uploads"
STORAGE_DIR = Path(os.environ.get("UPLOAD_STORAGE_DIR", DEFAULT_STORAGE)).expanduser().resolve()
METADATA_FILE = STORAGE_DIR / "metadata.json"

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".gif": {"image/gif"},
    ".txt": {"text/plain"},
    ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"},
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
app.config["JSON_SORT_KEYS"] = False


def ensure_storage():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not METADATA_FILE.exists():
        METADATA_FILE.write_text("[]", encoding="utf-8")


def load_metadata():
    ensure_storage()
    try:
        data = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_metadata(data):
    ensure_storage()
    temp = METADATA_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp.replace(METADATA_FILE)


def extension_of(filename):
    return Path(filename).suffix.lower()


def detect_signature(ext, data):
    """Return True when a binary file has the expected common magic bytes."""
    signatures = {
        ".pdf": lambda b: b.startswith(b"%PDF-"),
        ".png": lambda b: b.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": lambda b: b.startswith(b"\xff\xd8\xff"),
        ".jpeg": lambda b: b.startswith(b"\xff\xd8\xff"),
        ".gif": lambda b: b.startswith((b"GIF87a", b"GIF89a")),
    }
    checker = signatures.get(ext)
    return True if checker is None else checker(data)


def validate_upload(file_storage):
    if file_storage is None or not file_storage.filename:
        return False, "Choose a file before uploading."

    original = file_storage.filename
    safe_name = secure_filename(original)
    if not safe_name:
        return False, "The filename is not valid after sanitization."

    ext = extension_of(safe_name)
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"File type is not allowed. Use: {allowed}"

    mime = (file_storage.mimetype or "").lower().split(";", 1)[0].strip()
    if mime and mime not in ALLOWED_EXTENSIONS[ext]:
        return False, f"MIME type '{mime or 'unknown'}' does not match {ext}."

    # Read only the configured maximum + 1 bytes so a client cannot bypass the limit.
    data = file_storage.read(MAX_FILE_SIZE + 1)
    file_storage.seek(0)
    if len(data) > MAX_FILE_SIZE:
        return False, "File exceeds the 5 MB upload limit."

    if not detect_signature(ext, data):
        return False, "The file content does not match its declared file type."

    if ext in {".txt", ".csv"}:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            return False, "Text and CSV uploads must be valid UTF-8 files."

    return True, safe_name


def public_record(record):
    return {
        "id": record["id"],
        "original_name": record["original_name"],
        "stored_name": record["stored_name"],
        "size": record["size"],
        "type": record["content_type"],
        "uploaded_at": record["uploaded_at"],
    }


@app.get("/")
def index():
    return render_template(
        "index.html",
        max_file_size=MAX_FILE_SIZE,
        allowed_types=sorted(ALLOWED_EXTENSIONS),
    )


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Secure File Upload API",
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        "allowed_extensions": sorted(ALLOWED_EXTENSIONS),
        "storage": "external application storage",
    })


@app.get("/api/files")
def list_files():
    records = load_metadata()
    return jsonify({"count": len(records), "files": [public_record(r) for r in reversed(records)]})


@app.post("/api/upload")
def upload_file():
    file_storage = request.files.get("file")
    valid, result = validate_upload(file_storage)
    if not valid:
        return jsonify({"success": False, "error": result}), 400

    safe_original = result
    ext = extension_of(safe_original)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    destination = (STORAGE_DIR / stored_name).resolve()

    # Defense-in-depth: destination must remain inside the external storage directory.
    if STORAGE_DIR not in destination.parents:
        return jsonify({"success": False, "error": "Unsafe storage path."}), 500

    try:
        file_storage.save(destination)
        size = destination.stat().st_size
        record = {
            "id": uuid.uuid4().hex,
            "original_name": safe_original,
            "stored_name": stored_name,
            "size": size,
            "content_type": file_storage.mimetype or "application/octet-stream",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        records = load_metadata()
        records.append(record)
        save_metadata(records)
    except OSError:
        if destination.exists():
            destination.unlink(missing_ok=True)
        return jsonify({"success": False, "error": "The server could not store the file."}), 500

    return jsonify({
        "success": True,
        "message": "File validated and stored securely.",
        "file": public_record(record),
    }), 201


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(_error):
    return jsonify({"success": False, "error": "File exceeds the 5 MB upload limit."}), 413


@app.errorhandler(400)
def handle_bad_request(error):
    # Keep API errors JSON while allowing Flask to handle ordinary browser errors.
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": str(error)}), 400
    return error


if __name__ == "__main__":
    ensure_storage()
    app.run(host="127.0.0.1", port=5000, debug=False)
