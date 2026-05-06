#!/usr/bin/env python3
"""
PDF Squeeze — Local drag-and-drop PDF compressor powered by Ghostscript.
Run:  python3 pdf_squeeze.py
Then open http://localhost:8484 in your browser.

Requires: Python 3.8+, Ghostscript installed (gs).
"""

import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import uuid
import webbrowser
import zipfile
from io import BytesIO
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8484

# Temp storage for uploads and results
WORK_DIR = Path(tempfile.mkdtemp(prefix="pdfsqueeze_"))
JOBS: dict[str, dict] = {}

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PDF Squeeze</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0e0f11;
    --surface: #161719;
    --surface2: #1e2023;
    --border: #2a2d31;
    --border-hi: #3a3d42;
    --text: #e8e6e3;
    --text2: #9b9a97;
    --accent: #f0745f;
    --accent2: #f0975f;
    --accent-dim: rgba(240,116,95,0.12);
    --green: #5fcf80;
    --green-dim: rgba(95,207,128,0.12);
    --red: #e05555;
    --font: 'DM Sans', system-ui, sans-serif;
    --mono: 'JetBrains Mono', monospace;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px;
    line-height: 1.5;
  }

  h1 {
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
  }
  h1 span { color: var(--accent); }

  .subtitle {
    color: var(--text2);
    font-size: 14px;
    margin-bottom: 32px;
  }

  .app {
    width: 100%;
    max-width: 660px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  /* Drop zone */
  .dropzone {
    border: 2px dashed var(--border);
    border-radius: 16px;
    padding: 48px 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    background: var(--surface);
    position: relative;
  }
  .dropzone:hover, .dropzone.dragover {
    border-color: var(--accent);
    background: var(--accent-dim);
  }
  .dropzone.dragover .drop-icon { transform: scale(1.15); }
  .drop-icon {
    font-size: 40px;
    margin-bottom: 12px;
    transition: transform 0.2s ease;
    display: block;
  }
  .drop-label { font-size: 15px; font-weight: 500; }
  .drop-hint { font-size: 13px; color: var(--text2); margin-top: 4px; }
  .dropzone input { display: none; }

  /* Settings bar */
  .settings {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }
  .setting-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 160px;
  }
  .setting-group label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text2);
    font-weight: 500;
  }
  .setting-group select {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    font-family: var(--font);
    font-size: 14px;
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%239b9a97' stroke-width='1.5' fill='none'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
  }
  .setting-group select:hover { border-color: var(--border-hi); }

  /* Compress button */
  .compress-btn {
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-family: var(--font);
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    align-self: flex-start;
    letter-spacing: -0.2px;
  }
  .compress-btn:hover { background: var(--accent2); transform: translateY(-1px); }
  .compress-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
    transform: none;
  }

  /* File list */
  .file-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .file-item {
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 14px;
    animation: slideIn 0.25s ease;
  }
  @keyframes slideIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .file-icon { font-size: 20px; flex-shrink: 0; }
  .file-info { flex: 1; min-width: 0; }
  .file-name {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .file-size { font-family: var(--mono); font-size: 12px; color: var(--text2); }
  .file-remove {
    background: none;
    border: none;
    color: var(--text2);
    cursor: pointer;
    font-size: 18px;
    padding: 4px 8px;
    border-radius: 6px;
    transition: all 0.15s;
  }
  .file-remove:hover { color: var(--red); background: rgba(224,85,85,0.1); }

  /* Progress & results */
  .progress-bar-outer {
    width: 100%;
    height: 6px;
    background: var(--surface2);
    border-radius: 3px;
    overflow: hidden;
    display: none;
  }
  .progress-bar-outer.active { display: block; }
  .progress-bar-inner {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    border-radius: 3px;
    width: 0%;
    transition: width 0.3s ease;
  }

  .result-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    display: none;
  }
  .result-panel.active { display: block; animation: slideIn 0.3s ease; }
  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  .result-title { font-weight: 600; font-size: 15px; }
  .result-summary {
    font-family: var(--mono);
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 8px;
  }
  .result-summary.good { background: var(--green-dim); color: var(--green); }

  .result-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  .result-table th {
    text-align: left;
    color: var(--text2);
    font-weight: 500;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    padding: 0 8px 10px;
    border-bottom: 1px solid var(--border);
  }
  .result-table td {
    padding: 10px 8px;
    border-bottom: 1px solid var(--border);
  }
  .result-table tr:last-child td { border-bottom: none; }
  .result-table .mono { font-family: var(--mono); }
  .result-table .saved { color: var(--green); font-weight: 500; }
  .result-table .fname {
    max-width: 220px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .download-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--green);
    color: #0e0f11;
    border: none;
    border-radius: 8px;
    padding: 10px 22px;
    font-family: var(--font);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 16px;
    transition: all 0.15s ease;
  }
  .download-btn:hover { transform: translateY(-1px); filter: brightness(1.1); }

  .status-msg {
    font-size: 13px;
    color: var(--text2);
    text-align: center;
    padding: 8px;
  }
  .status-msg.error { color: var(--red); }
</style>
</head>
<body>

<h1>PDF <span>Squeeze</span></h1>
<p class="subtitle">Drop your PDFs, pick a quality, squeeze them down.</p>

<div class="app">
  <div class="dropzone" id="dropzone">
    <span class="drop-icon">&#128196;</span>
    <div class="drop-label">Drop PDF files here</div>
    <div class="drop-hint">or click to browse</div>
    <input type="file" id="fileInput" accept=".pdf" multiple>
  </div>

  <div class="file-list" id="fileList"></div>

  <div class="settings">
    <div class="setting-group">
      <label>Quality preset</label>
      <select id="quality">
        <option value="screen">Screen — max compression</option>
        <option value="ebook" selected>Ebook — balanced (150 dpi)</option>
        <option value="printer">Printer — high quality (300 dpi)</option>
        <option value="prepress">Prepress — minimal compression</option>
      </select>
    </div>
  </div>

  <button class="compress-btn" id="compressBtn" disabled>Squeeze files</button>

  <div class="progress-bar-outer" id="progressOuter">
    <div class="progress-bar-inner" id="progressInner"></div>
  </div>

  <div id="statusMsg" class="status-msg"></div>

  <div class="result-panel" id="resultPanel">
    <div class="result-header">
      <span class="result-title">Results</span>
      <span class="result-summary good" id="totalSaved"></span>
    </div>
    <table class="result-table">
      <thead><tr><th>File</th><th>Original</th><th>Compressed</th><th>Saved</th></tr></thead>
      <tbody id="resultBody"></tbody>
    </table>
    <button class="download-btn" id="downloadBtn">&#11015;&#65039; Download all</button>
  </div>
</div>

<script>
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const compressBtn = document.getElementById('compressBtn');
const quality = document.getElementById('quality');
const progressOuter = document.getElementById('progressOuter');
const progressInner = document.getElementById('progressInner');
const statusMsg = document.getElementById('statusMsg');
const resultPanel = document.getElementById('resultPanel');
const resultBody = document.getElementById('resultBody');
const totalSaved = document.getElementById('totalSaved');
const downloadBtn = document.getElementById('downloadBtn');

let files = [];
let currentJobId = null;

function fmtSize(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
  return (b / 1048576).toFixed(2) + ' MB';
}

function updateBtn() {
  compressBtn.disabled = files.length === 0;
  compressBtn.textContent = files.length > 1
    ? `Squeeze ${files.length} files`
    : files.length === 1 ? 'Squeeze file' : 'Squeeze files';
}

function renderFiles() {
  fileList.innerHTML = '';
  files.forEach((f, i) => {
    const div = document.createElement('div');
    div.className = 'file-item';
    div.innerHTML = `
      <span class="file-icon">&#128459;</span>
      <div class="file-info">
        <div class="file-name">${f.name}</div>
        <div class="file-size">${fmtSize(f.size)}</div>
      </div>
      <button class="file-remove" data-idx="${i}">&times;</button>`;
    fileList.appendChild(div);
  });
  updateBtn();
}

function addFiles(newFiles) {
  for (const f of newFiles) {
    if (f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')) {
      if (!files.some(e => e.name === f.name && e.size === f.size)) {
        files.push(f);
      }
    }
  }
  renderFiles();
}

dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => { addFiles(e.target.files); fileInput.value = ''; });
dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  addFiles(e.dataTransfer.files);
});
fileList.addEventListener('click', e => {
  const btn = e.target.closest('.file-remove');
  if (btn) { files.splice(+btn.dataset.idx, 1); renderFiles(); }
});

compressBtn.addEventListener('click', async () => {
  if (files.length === 0) return;
  compressBtn.disabled = true;
  resultPanel.classList.remove('active');
  statusMsg.textContent = '';
  statusMsg.className = 'status-msg';
  progressOuter.classList.add('active');
  progressInner.style.width = '0%';

  const fd = new FormData();
  fd.append('quality', quality.value);
  files.forEach(f => fd.append('files', f));

  try {
    statusMsg.textContent = 'Uploading…';
    const resp = await fetch('/compress', { method: 'POST', body: fd });
    if (!resp.ok) throw new Error(await resp.text());
    const data = await resp.json();
    currentJobId = data.job_id;
    pollJob();
  } catch (err) {
    statusMsg.textContent = 'Error: ' + err.message;
    statusMsg.className = 'status-msg error';
    progressOuter.classList.remove('active');
    compressBtn.disabled = false;
  }
});

async function pollJob() {
  try {
    const resp = await fetch('/status/' + currentJobId);
    const data = await resp.json();

    if (data.state === 'processing') {
      progressInner.style.width = data.progress + '%';
      statusMsg.textContent = `Squeezing… ${data.done}/${data.total}`;
      setTimeout(pollJob, 400);
    } else if (data.state === 'done') {
      progressInner.style.width = '100%';
      statusMsg.textContent = '';
      showResults(data.results);
      setTimeout(() => progressOuter.classList.remove('active'), 600);
      compressBtn.disabled = false;
    } else {
      statusMsg.textContent = 'Error: ' + (data.error || 'unknown');
      statusMsg.className = 'status-msg error';
      progressOuter.classList.remove('active');
      compressBtn.disabled = false;
    }
  } catch (e) {
    setTimeout(pollJob, 800);
  }
}

function showResults(results) {
  resultBody.innerHTML = '';
  let totalOrig = 0, totalComp = 0;
  results.forEach(r => {
    totalOrig += r.original_size;
    totalComp += r.compressed_size;
    const pct = r.original_size > 0
      ? ((1 - r.compressed_size / r.original_size) * 100).toFixed(1)
      : '0';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="fname">${r.name}</td>
      <td class="mono">${fmtSize(r.original_size)}</td>
      <td class="mono">${fmtSize(r.compressed_size)}</td>
      <td class="mono saved">-${pct}%</td>`;
    resultBody.appendChild(tr);
  });
  const totalPct = totalOrig > 0
    ? ((1 - totalComp / totalOrig) * 100).toFixed(1)
    : '0';
  totalSaved.textContent = `Total: ${fmtSize(totalOrig)} → ${fmtSize(totalComp)}  (-${totalPct}%)`;
  resultPanel.classList.add('active');

  downloadBtn.onclick = () => {
    window.location.href = '/download/' + currentJobId;
  };
}
</script>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Quieter logging
        msg = fmt % args
        if "GET /status" not in msg:
            print(f"  {msg}")

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(msg.encode())

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            body = HTML_PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith("/status/"):
            job_id = self.path.split("/status/")[1]
            job = JOBS.get(job_id)
            if not job:
                return self._json(404, {"error": "job not found"})
            self._json(200, job["status"])

        elif self.path.startswith("/download/"):
            job_id = self.path.split("/download/")[1]
            job = JOBS.get(job_id)
            if not job or job["status"]["state"] != "done":
                return self._error(404, "Job not ready")

            results = job["status"]["results"]
            if len(results) == 1:
                # Single file: download PDF directly
                fpath = Path(results[0]["path"])
                data = fpath.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition",
                                 f'attachment; filename="squeezed_{results[0]["name"]}"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                # Multiple files: zip them
                buf = BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for r in results:
                        zf.write(r["path"], f"squeezed_{r['name']}")
                data = buf.getvalue()
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition",
                                 'attachment; filename="squeezed_pdfs.zip"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        else:
            self._error(404, "Not found")

    def do_POST(self):
        if self.path != "/compress":
            return self._error(404, "Not found")

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            return self._error(400, "Expected multipart/form-data")

        # Parse multipart
        import cgi
        env = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
        }
        fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=env)

        quality_val = "ebook"
        if "quality" in fs:
            q = fs["quality"].value
            if q in ("screen", "ebook", "printer", "prepress"):
                quality_val = q

        file_items = fs["files"] if "files" in fs else []
        if not isinstance(file_items, list):
            file_items = [file_items]
        file_items = [f for f in file_items if f.filename]

        if not file_items:
            return self._error(400, "No PDF files received")

        job_id = uuid.uuid4().hex[:12]
        job_dir = WORK_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        input_dir = job_dir / "input"
        output_dir = job_dir / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        saved_files = []
        for item in file_items:
            safe_name = Path(item.filename).name
            dest = input_dir / safe_name
            dest.write_bytes(item.file.read())
            saved_files.append(safe_name)

        JOBS[job_id] = {
            "status": {
                "state": "processing",
                "progress": 0,
                "done": 0,
                "total": len(saved_files),
                "results": [],
            },
            "quality": quality_val,
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "files": saved_files,
        }

        thread = threading.Thread(target=run_compression, args=(job_id,), daemon=True)
        thread.start()

        self._json(200, {"job_id": job_id})


def run_compression(job_id: str):
    job = JOBS[job_id]
    status = job["status"]
    quality = job["quality"]
    input_dir = Path(job["input_dir"])
    output_dir = Path(job["output_dir"])
    results = []

    for i, fname in enumerate(job["files"]):
        inp = input_dir / fname
        out = output_dir / fname
        orig_size = inp.stat().st_size

        try:
            subprocess.run(
                [
                    "gs",
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",
                    f"-dPDFSETTINGS=/{quality}",
                    "-dNOPAUSE",
                    "-dBATCH",
                    "-dQUIET",
                    f"-sOutputFile={out}",
                    str(inp),
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
            comp_size = out.stat().st_size
        except Exception as e:
            # If GS fails, copy original as fallback
            shutil.copy2(inp, out)
            comp_size = orig_size
            print(f"  Warning: gs failed for {fname}: {e}")

        results.append({
            "name": fname,
            "original_size": orig_size,
            "compressed_size": comp_size,
            "path": str(out),
        })

        status["done"] = i + 1
        status["progress"] = int((i + 1) / len(job["files"]) * 100)

    status["state"] = "done"
    status["results"] = results


def check_ghostscript():
    try:
        subprocess.run(["gs", "--version"], capture_output=True, check=True)
        return True
    except FileNotFoundError:
        return False


def main():
    if not check_ghostscript():
        print("Error: Ghostscript (gs) is not installed or not on PATH.")
        print("  Ubuntu/Debian:  sudo apt install ghostscript")
        print("  macOS:          brew install ghostscript")
        print("  Windows:        https://ghostscript.com/releases/gsdnld.html")
        sys.exit(1)

    server = http.server.HTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"\n  PDF Squeeze running at {url}")
    print(f"  Temp dir: {WORK_DIR}")
    print("  Press Ctrl+C to stop.\n")

    # Open browser after a short delay
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down…")
    finally:
        server.server_close()
        shutil.rmtree(WORK_DIR, ignore_errors=True)
        print("  Cleaned up temp files. Bye!")


if __name__ == "__main__":
    main()