const API_BASE = "http://127.0.0.1:8000";

const form = document.getElementById("extract-form");
const fileInput = document.getElementById("files");
const dropzone = document.getElementById("dropzone");
const fileList = document.getElementById("file-list");
const formatSelect = document.getElementById("format");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

let selectedFiles = [];

function renderFileList() {
  fileList.innerHTML = "";
  for (const file of selectedFiles) {
    const li = document.createElement("li");
    li.textContent = file.name;
    fileList.appendChild(li);
  }
}

function setFiles(fileListLike) {
  selectedFiles = Array.from(fileListLike);
  renderFileList();
}

fileInput.addEventListener("change", () => setFiles(fileInput.files));

["dragenter", "dragover"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  });
});

dropzone.addEventListener("drop", (e) => {
  setFiles(e.dataTransfer.files);
});

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "var(--error)" : "var(--muted)";
}

function renderErrors(errors) {
  for (const err of errors) {
    const div = document.createElement("div");
    div.className = "error-card";
    div.innerHTML = `<strong>${err.filename}</strong>: ${err.error}`;
    resultsEl.appendChild(div);
  }
}

function renderCourses(courses) {
  for (const course of courses) {
    const div = document.createElement("div");
    div.className = "course-card";
    const itemCount = course.groups.reduce((sum, g) => sum + g.items.length, 0);
    div.innerHTML = `<h3>${course.code} — ${course.name}</h3><p>${course.groups.length} categories, ${itemCount} graded items</p>`;
    resultsEl.appendChild(div);
  }
}

function filenameFromDisposition(header, fallback) {
  const match = header && header.match(/filename="?([^"]+)"?/);
  return match ? match[1] : fallback;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  resultsEl.innerHTML = "";

  if (selectedFiles.length === 0) {
    setStatus("Choose at least one syllabus file first.", true);
    return;
  }

  const format = formatSelect.value;
  const data = new FormData();
  for (const file of selectedFiles) data.append("files", file);

  submitBtn.disabled = true;
  setStatus(`Extracting ${selectedFiles.length} file(s)...`);

  try {
    const res = await fetch(`${API_BASE}/extract?format=${format}`, {
      method: "POST",
      body: data,
    });

    if (format === "json") {
      const payload = await res.json();
      if (!res.ok) {
        setStatus("Extraction failed.", true);
        renderErrors(payload.detail?.errors ?? []);
        return;
      }
      setStatus(`Done: ${payload.courses.length} course(s), ${payload.errors.length} error(s).`);
      renderCourses(payload.courses);
      renderErrors(payload.errors);
      return;
    }

    if (!res.ok) {
      const payload = await res.json();
      setStatus("Extraction failed.", true);
      renderErrors(payload.detail?.errors ?? []);
      return;
    }

    const blob = await res.blob();
    const filename = filenameFromDisposition(res.headers.get("Content-Disposition"), `courses.${format}`);
    downloadBlob(blob, filename);
    setStatus(`Downloaded ${filename}.`);
  } catch (err) {
    setStatus(`Could not reach the server: ${err.message}`, true);
  } finally {
    submitBtn.disabled = false;
  }
});
