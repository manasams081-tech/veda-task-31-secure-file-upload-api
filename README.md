# VEDA Technology — Task 31: Secure File Upload API

A beginner-friendly Flask implementation of **Task 31: Build a Secure File Upload API**.

## What this project demonstrates

- `POST /api/upload` file-upload endpoint
- Allow-list validation for PDF, PNG, JPG/JPEG, GIF, TXT and CSV
- 5 MB maximum request/file size
- MIME-type cross-checking
- Common magic-byte/content-signature checks for binary formats
- UTF-8 validation for text and CSV files
- Safe filename sanitization with Werkzeug `secure_filename`
- UUID-based stored filenames to avoid collisions and predictable paths
- Storage outside the application directory by default: `~/veda_secure_uploads`
- Atomic JSON metadata writes
- JSON error responses for API failures
- Small browser dashboard for testing the API

## Project structure

```text
VEDA-Task-31-Secure-File-Upload-API/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── tests/
    └── test_api.py
```

## 1. Create the virtual environment

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt instead:

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Run the application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The browser page is a custom VaultDrop interface. It is only a test client; the actual upload functionality is the Flask API.

## 3. API endpoints

### Health check

`GET /api/health`

### List stored upload metadata

`GET /api/files`

### Upload a file

`POST /api/upload`

Multipart field name:

```text
file
```

Example with PowerShell:

```powershell
curl.exe -X POST -F "file=@sample.txt" http://127.0.0.1:5000/api/upload
```

## Security decisions

1. **Never trust the client filename** — the original name is passed through `secure_filename`.
2. **Do not use the original name as the storage path** — a random UUID is generated for the stored filename.
3. **Restrict size** — Flask rejects requests over 5 MB and the validator also checks the actual read size.
4. **Restrict extensions** — only an explicit allow-list is accepted.
5. **Cross-check MIME type** — a declared MIME type must match the selected extension.
6. **Check content signatures** — PDF/image uploads are checked against common file signatures instead of trusting the extension alone.
7. **Validate text encoding** — TXT/CSV uploads must be valid UTF-8.
8. **Keep uploads outside the app** — default storage is `~/veda_secure_uploads`, not a public/static application directory.
9. **Contain the destination path** — the final resolved path must remain inside the configured storage directory.
10. **Avoid exposing files directly** — this demo has no public download route, reducing accidental exposure.

> This is an educational project. Production systems should also consider malware scanning, authentication/authorization, quotas, rate limiting, audit logging, encrypted storage, and isolated object storage.

## 4. Optional storage location

You can override the external storage directory.

PowerShell:

```powershell
$env:UPLOAD_STORAGE_DIR="$HOME\veda_secure_uploads"
python app.py
```

Linux/macOS:

```bash
export UPLOAD_STORAGE_DIR="$HOME/veda_secure_uploads"
python app.py
```

## 5. Test checklist for the VEDA task

- Upload a valid `.pdf`, `.png`, `.jpg`, `.gif`, `.txt`, or `.csv` file → accepted when content/MIME match.
- Rename a non-PDF file to `.pdf` → rejected by signature validation.
- Upload an unsupported extension such as `.exe` → rejected.
- Upload a file above 5 MB → rejected.
- Try a filename such as `../../secret.txt` → sanitized and never used as the stored path.
- Confirm stored files appear under `~/veda_secure_uploads` rather than inside the project.
- Open `/api/health` and `/api/files` to show the API is working.

## GitHub submission

Recommended repository name:

`veda-task-31-secure-file-upload-api`

Repository description:

`VEDA Technology Task 31 - Secure File Upload API using Python and Flask with file validation, size restrictions, safe filename handling and external storage.`

### Git commands

Run these from the project root — the folder containing `app.py`:

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Complete VEDA Technology Task 31"
git remote add origin https://github.com/manasams081-tech/veda-task-31-secure-file-upload-api.git
git push -u origin main
```

If you accidentally added the wrong remote:

```powershell
git remote -v
git remote set-url origin https://github.com/manasams081-tech/veda-task-31-secure-file-upload-api.git
git push -u origin main
```

## Important GitHub rule

Do **not** commit `.venv`, personal upload files, secrets, or the external upload directory. The included `.gitignore` protects the normal local virtual environment and upload paths.
