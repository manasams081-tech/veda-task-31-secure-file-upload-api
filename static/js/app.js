const input = document.getElementById('fileInput');
const dropzone = document.getElementById('dropzone');
const uploadBtn = document.getElementById('uploadBtn');
const dropTitle = document.getElementById('dropTitle');
const dropMeta = document.getElementById('dropMeta');
const statusBox = document.getElementById('status');
const fileList = document.getElementById('fileList');
const refreshBtn = document.getElementById('refreshBtn');

function setStatus(message, type='') {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024*1024) return `${(bytes/1024).toFixed(1)} KB`;
  return `${(bytes/(1024*1024)).toFixed(2)} MB`;
}

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function selectFile(file) {
  if (!file) return;
  input.files = (() => {
    const dt = new DataTransfer();
    dt.items.add(file);
    return dt.files;
  })();
  uploadBtn.disabled = false;
  dropTitle.textContent = file.name;
  dropMeta.textContent = `${formatBytes(file.size)} · ready for validation`;
  setStatus('File selected. Validation will happen on upload.');
}

input.addEventListener('change', () => selectFile(input.files[0]));
['dragenter','dragover'].forEach(evt => dropzone.addEventListener(evt, e => {
  e.preventDefault(); dropzone.classList.add('dragging');
}));
['dragleave','drop'].forEach(evt => dropzone.addEventListener(evt, e => {
  e.preventDefault(); dropzone.classList.remove('dragging');
}));
dropzone.addEventListener('drop', e => selectFile(e.dataTransfer.files[0]));

uploadBtn.addEventListener('click', async () => {
  const file = input.files[0];
  if (!file) return;
  uploadBtn.disabled = true;
  setStatus('Checking size, type, content and safe storage path…');
  const form = new FormData();
  form.append('file', file);
  try {
    const response = await fetch('/api/upload', {method:'POST', body:form});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Upload failed.');
    setStatus(`✓ ${data.message}`, 'ok');
    input.value = '';
    dropTitle.textContent = 'Choose a file or drag it here';
    dropMeta.textContent = 'PDF · PNG · JPG · GIF · TXT · CSV · max 5 MB';
    await loadFiles();
  } catch (error) {
    setStatus(`✕ ${error.message}`, 'error');
    uploadBtn.disabled = false;
  }
});

async function loadFiles() {
  fileList.innerHTML = '<div class="empty"><span>◌</span><p>Loading secure records…</p></div>';
  try {
    const response = await fetch('/api/files');
    const data = await response.json();
    if (!data.files.length) {
      fileList.innerHTML = '<div class="empty"><span>＋</span><p>No uploads yet. Your validated files will appear here.</p></div>';
      return;
    }
    fileList.innerHTML = data.files.map(file => {
      const ext = file.original_name.split('.').pop().toUpperCase();
      return `<div class="file-row">
        <div class="file-icon">${ext.slice(0,4)}</div>
        <div><strong title="${file.original_name}">${file.original_name}</strong><small>${file.type} · ${formatDate(file.uploaded_at)}</small></div>
        <div class="file-size">${formatBytes(file.size)}</div>
      </div>`;
    }).join('');
  } catch {
    fileList.innerHTML = '<div class="empty"><span>!</span><p>Could not load the secure record list.</p></div>';
  }
}

refreshBtn.addEventListener('click', loadFiles);
loadFiles();
