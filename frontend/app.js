const state = {
  indexName: "pdf-rag",
  topK: 5,
  messages: [
    {
      role: "assistant",
      content:
        "The backend is ready. Upload a PDF, wait for ingestion to finish, then ask a question.",
    },
  ],
  jobs: [],
  latestSources: [],
  latestStats: null,
};

const elements = {
  healthLabel: document.getElementById("health-label"),
  indexName: document.getElementById("index-name"),
  uploadForm: document.getElementById("upload-form"),
  pdfFile: document.getElementById("pdf-file"),
  uploadFileName: document.getElementById("upload-file-name"),
  uploadFeedback: document.getElementById("upload-feedback"),
  jobsList: document.getElementById("jobs-list"),
  refreshJobs: document.getElementById("refresh-jobs"),
  chatFeed: document.getElementById("chat-feed"),
  chatForm: document.getElementById("chat-form"),
  questionInput: document.getElementById("question-input"),
  topKInput: document.getElementById("top-k-input"),
  topKValue: document.getElementById("top-k-value"),
  chunkCount: document.getElementById("chunk-count"),
  librarySummary: document.getElementById("library-summary"),
  sourceCatalog: document.getElementById("source-catalog"),
  latestSources: document.getElementById("latest-sources"),
};

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatTextBlock(text) {
  return escapeHtml(text).replaceAll("\n", "<br />");
}

function showFeedback(message, tone = "info") {
  elements.uploadFeedback.textContent = message;
  elements.uploadFeedback.dataset.tone = tone;
}

function setChatBusy(isBusy) {
  elements.questionInput.disabled = isBusy;
  elements.topKInput.disabled = isBusy;
}

function renderMessages() {
  elements.chatFeed.innerHTML = state.messages
    .map((message) => {
      const body = formatTextBlock(message.content);
      return `
        <article class="chat-bubble ${message.role}">
          <p class="bubble-role">${message.role === "assistant" ? "Assistant" : "You"}</p>
          <div class="bubble-body">${body}</div>
        </article>
      `;
    })
    .join("");
  elements.chatFeed.scrollTop = elements.chatFeed.scrollHeight;
}

function renderJobs() {
  if (!state.jobs.length) {
    elements.jobsList.className = "job-list empty-state";
    elements.jobsList.textContent = "No ingestion jobs yet.";
    return;
  }

  elements.jobsList.className = "job-list";
  elements.jobsList.innerHTML = state.jobs
    .map((job) => {
      const progress =
        job.status === "completed"
          ? 100
          : job.total_pages > 0
            ? Math.min(Math.round((job.page_number / job.total_pages) * 100), 99)
            : 0;
      const error = job.error
        ? `<p class="job-error">${escapeHtml(job.error)}</p>`
        : "";
      return `
        <article class="job-card">
          <div class="job-topline">
            <div>
              <p class="job-file">${escapeHtml(job.filename)}</p>
              <p class="job-meta">${escapeHtml(job.index_name)} · ${escapeHtml(job.stage)}</p>
            </div>
            <span class="job-badge ${job.status}">${escapeHtml(job.status)}</span>
          </div>
          <div class="progress-track">
            <span class="progress-bar" style="width:${progress}%"></span>
          </div>
          <p class="job-stats">
            Pages: ${job.page_number}/${job.total_pages || "?"} · Chunks indexed: ${job.chunks_indexed}
          </p>
          ${error}
        </article>
      `;
    })
    .join("");
}

function renderSummary(summary) {
  if (!summary || !summary.exists) {
    elements.chunkCount.textContent = "0";
    elements.librarySummary.innerHTML = `
      <article class="summary-card">
        <span class="summary-label">Index</span>
        <strong>${escapeHtml(state.indexName)}</strong>
      </article>
      <article class="summary-card">
        <span class="summary-label">Status</span>
        <strong>Empty</strong>
      </article>
    `;
    elements.sourceCatalog.className = "source-catalog empty-state";
    elements.sourceCatalog.textContent = "This index has not been created yet.";
    return;
  }

  elements.chunkCount.textContent = String(summary.document_count);
  elements.librarySummary.innerHTML = `
    <article class="summary-card">
      <span class="summary-label">Index</span>
      <strong>${escapeHtml(summary.index_name)}</strong>
    </article>
    <article class="summary-card">
      <span class="summary-label">Chunks</span>
      <strong>${summary.document_count}</strong>
    </article>
    <article class="summary-card">
      <span class="summary-label">Sources</span>
      <strong>${summary.source_count}</strong>
    </article>
  `;

  if (!summary.sources.length) {
    elements.sourceCatalog.className = "source-catalog empty-state";
    elements.sourceCatalog.textContent = "No source entries have been indexed yet.";
    return;
  }

  elements.sourceCatalog.className = "source-catalog";
  elements.sourceCatalog.innerHTML = summary.sources
    .map(
      (source) => `
        <article class="source-pill">
          <strong>${escapeHtml(source.name)}</strong>
          <span>${source.chunk_count} chunks</span>
        </article>
      `
    )
    .join("");
}

function renderLatestSources() {
  if (!state.latestSources.length) {
    elements.latestSources.className = "source-list empty-state";
    elements.latestSources.textContent = "Ask a question to inspect the retrieved chunks.";
    return;
  }

  elements.latestSources.className = "source-list";
  elements.latestSources.innerHTML = state.latestSources
    .map(
      (source, index) => `
        <article class="source-card">
          <div class="source-head">
            <strong>Source ${index + 1}</strong>
            <span>${source.score}</span>
          </div>
          <p class="source-name">${escapeHtml(source.source)}</p>
          <p class="source-snippet">${escapeHtml(source.text.slice(0, 280))}</p>
        </article>
      `
    )
    .join("");
}

async function apiJson(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const errorMessage =
      typeof payload === "string" ? payload : payload.error || "Request failed.";
    throw new Error(errorMessage);
  }

  return payload;
}

async function refreshHealth() {
  try {
    const payload = await apiJson("/api/health");
    const status = payload.opensearch_reachable ? "Backend live" : "OpenSearch unreachable";
    elements.healthLabel.textContent = `${status} · ${payload.default_index_name}`;
  } catch (error) {
    elements.healthLabel.textContent = `Health check failed: ${error.message}`;
  }
}

async function refreshSummary() {
  try {
    const summary = await apiJson(`/api/indexes/${encodeURIComponent(state.indexName)}`);
    renderSummary(summary);
  } catch (error) {
    elements.librarySummary.innerHTML = `
      <article class="summary-card">
        <span class="summary-label">Error</span>
        <strong>${escapeHtml(error.message)}</strong>
      </article>
    `;
  }
}

async function refreshJobs() {
  try {
    const payload = await apiJson("/api/jobs");
    state.jobs = payload.jobs || [];
    renderJobs();
    if (state.jobs.some((job) => job.status === "running" || job.status === "queued")) {
      setTimeout(refreshJobs, 2500);
    } else {
      refreshSummary();
    }
  } catch (error) {
    elements.jobsList.className = "job-list empty-state";
    elements.jobsList.textContent = `Could not load jobs: ${error.message}`;
  }
}

async function submitUpload(event) {
  event.preventDefault();
  const file = elements.pdfFile.files[0];
  if (!file) {
    showFeedback("Choose a PDF before starting ingestion.", "error");
    return;
  }

  showFeedback("Uploading file and starting background ingestion...", "info");
  const formData = new FormData();
  formData.append("file", file);
  formData.append("index_name", state.indexName);

  try {
    const job = await apiJson("/api/ingest", {
      method: "POST",
      body: formData,
    });
    showFeedback(`Ingestion started for ${job.filename}.`, "success");
    elements.uploadForm.reset();
    elements.uploadFileName.textContent = "Up to 2 GB";
    await refreshJobs();
  } catch (error) {
    showFeedback(`Upload failed: ${error.message}`, "error");
  }
}

async function submitQuestion(event) {
  event.preventDefault();
  const question = elements.questionInput.value.trim();
  if (!question) {
    return;
  }

  const history = state.messages.slice(-8);
  state.messages.push({ role: "user", content: question });
  renderMessages();
  elements.questionInput.value = "";
  setChatBusy(true);

  try {
    const payload = await apiJson("/api/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        index_name: state.indexName,
        top_k: state.topK,
        history,
      }),
    });

    state.messages.push({ role: "assistant", content: payload.reply });
    state.latestSources = payload.sources || [];
    state.latestStats = payload.search_stats || null;
    renderMessages();
    renderLatestSources();
  } catch (error) {
    state.messages.push({
      role: "assistant",
      content: `The query could not be completed: ${error.message}`,
    });
    renderMessages();
  } finally {
    setChatBusy(false);
  }
}

function handleFileSelected() {
  const file = elements.pdfFile.files[0];
  if (!file) {
    elements.uploadFileName.textContent = "Up to 2 GB";
    return;
  }

  const sizeMb = file.size / (1024 * 1024);
  elements.uploadFileName.textContent = `${file.name} · ${sizeMb.toFixed(1)} MB`;
}

function handleIndexChange() {
  state.indexName = elements.indexName.value.trim() || "pdf-rag";
  refreshSummary();
}

function handleTopKChange() {
  state.topK = Number(elements.topKInput.value);
  elements.topKValue.textContent = String(state.topK);
}

function boot() {
  renderMessages();
  renderJobs();
  renderLatestSources();
  handleTopKChange();
  refreshHealth();
  refreshSummary();
  refreshJobs();

  elements.uploadForm.addEventListener("submit", submitUpload);
  elements.chatForm.addEventListener("submit", submitQuestion);
  elements.refreshJobs.addEventListener("click", refreshJobs);
  elements.pdfFile.addEventListener("change", handleFileSelected);
  elements.indexName.addEventListener("change", handleIndexChange);
  elements.topKInput.addEventListener("input", handleTopKChange);

  setInterval(refreshHealth, 15000);
}

boot();
