import tempfile
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from src.config import DEFAULT_INDEX_NAME, LLM_BASE_URL
from src.ingestion import ingest_pdf
from src.rag_engine import RAGEngine
from src.vector_store import client as opensearch_client
from src.vector_store import get_index_summary

APP_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = APP_ROOT / "frontend"
STATIC_DIR = FRONTEND_DIR
UPLOAD_DIR = APP_ROOT / "runtime" / "uploads"
PROMPT_PATH = APP_ROOT / "prompts" / "rag_v1.json"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024
MAX_HISTORY_MESSAGES = 10

engine = RAGEngine(LLM_BASE_URL, str(PROMPT_PATH))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def simplify_sources(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for hit in hits:
        source = hit.get("_source", {})
        items.append(
            {
                "source": source.get("source", "Unknown"),
                "text": source.get("text", ""),
                "score": round(hit.get("_score", 0.0), 4),
            }
        )
    return items


def normalize_history(raw_history: Any) -> list[dict[str, str]]:
    if not isinstance(raw_history, list):
        return []

    history: list[dict[str, str]] = []
    for item in raw_history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            history.append({"role": role, "content": content})
    return history


async def save_upload_to_disk(upload) -> Path:
    suffix = Path(upload.filename or "upload.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        prefix="rag-upload-",
        dir=UPLOAD_DIR,
    ) as tmp_file:
        while True:
            chunk = await upload.read(UPLOAD_CHUNK_SIZE)
            if not chunk:
                break
            tmp_file.write(chunk)
    await upload.close()
    return Path(tmp_file.name)


@dataclass
class IngestionJob:
    job_id: str
    filename: str
    index_name: str
    status: str
    stage: str
    page_number: int
    total_pages: int
    chunks_indexed: int
    created_at: str
    updated_at: str
    error: str | None = None


class IngestionJobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, IngestionJob] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            job_ids = list(reversed(self._order[-20:]))
            return [asdict(self._jobs[job_id]) for job_id in job_ids]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return asdict(job) if job else None

    def create_job(self, file_path: Path, filename: str, index_name: str) -> dict[str, Any]:
        job = IngestionJob(
            job_id=uuid4().hex,
            filename=filename,
            index_name=index_name,
            status="queued",
            stage="queued",
            page_number=0,
            total_pages=0,
            chunks_indexed=0,
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        with self._lock:
            self._jobs[job.job_id] = job
            self._order.append(job.job_id)

        worker = threading.Thread(
            target=self._run_job,
            args=(job.job_id, file_path, filename, index_name),
            daemon=True,
        )
        worker.start()
        return asdict(job)

    def _update_job(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in changes.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = utc_now_iso()

    def _run_job(self, job_id: str, file_path: Path, filename: str, index_name: str) -> None:
        self._update_job(job_id, status="running", stage="starting")

        def progress_callback(payload: dict[str, Any]) -> None:
            self._update_job(
                job_id,
                stage=payload.get("stage", "running"),
                page_number=payload.get("page_number", 0),
                total_pages=payload.get("total_pages", 0),
                chunks_indexed=payload.get("chunks_indexed", 0),
            )

        try:
            ingest_pdf(
                str(file_path),
                index_name=index_name,
                source_label=filename,
                progress_callback=progress_callback,
            )
            self._update_job(job_id, status="completed", stage="completed")
        except Exception as exc:
            self._update_job(
                job_id,
                status="failed",
                stage="failed",
                error=str(exc),
            )
        finally:
            if file_path.exists():
                file_path.unlink()


jobs = IngestionJobManager()


async def index_page(_: Request) -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "opensearch_reachable": opensearch_client.ping(),
            "default_index_name": DEFAULT_INDEX_NAME,
            "llm_base_url": LLM_BASE_URL,
        }
    )


async def create_ingestion_job(request: Request) -> JSONResponse:
    form = await request.form()
    upload = form.get("file")
    index_name = str(form.get("index_name") or DEFAULT_INDEX_NAME).strip()

    if upload is None:
        return JSONResponse({"error": "A PDF file is required."}, status_code=400)

    filename = upload.filename or "upload.pdf"
    if not filename.lower().endswith(".pdf"):
        return JSONResponse({"error": "Only PDF uploads are supported."}, status_code=400)

    file_path = await save_upload_to_disk(upload)
    job = jobs.create_job(file_path=file_path, filename=filename, index_name=index_name)
    return JSONResponse(job, status_code=202)


async def list_ingestion_jobs(_: Request) -> JSONResponse:
    return JSONResponse({"jobs": jobs.list_jobs()})


async def get_ingestion_job(request: Request) -> JSONResponse:
    job_id = request.path_params["job_id"]
    job = jobs.get_job(job_id)
    if job is None:
        return JSONResponse({"error": "Job not found."}, status_code=404)
    return JSONResponse(job)


async def query_documents(request: Request) -> JSONResponse:
    payload = await request.json()
    question = str(payload.get("question", "")).strip()
    index_name = str(payload.get("index_name") or DEFAULT_INDEX_NAME).strip()
    raw_top_k = payload.get("top_k", 5)
    history = normalize_history(payload.get("history", []))

    if not question:
        return JSONResponse({"error": "Question is required."}, status_code=400)

    try:
        top_k = max(1, min(int(raw_top_k), 12))
    except (TypeError, ValueError):
        return JSONResponse({"error": "top_k must be an integer."}, status_code=400)

    try:
        reply, usage_stats, sources, search_stats = engine.query(
            question,
            index_name=index_name,
            k=top_k,
            history=history,
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)

    return JSONResponse(
        {
            "reply": reply,
            "usage_stats": usage_stats,
            "sources": simplify_sources(sources),
            "search_stats": search_stats,
        }
    )


async def index_summary(request: Request) -> JSONResponse:
    index_name = request.path_params["index_name"]
    try:
        summary = get_index_summary(index_name)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    return JSONResponse(summary)


routes = [
    Route("/", index_page),
    Route("/api/health", health),
    Route("/api/ingest", create_ingestion_job, methods=["POST"]),
    Route("/api/jobs", list_ingestion_jobs),
    Route("/api/jobs/{job_id}", get_ingestion_job),
    Route("/api/query", query_documents, methods=["POST"]),
    Route("/api/indexes/{index_name}", index_summary),
    Mount("/static", app=StaticFiles(directory=STATIC_DIR), name="static"),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(debug=False, routes=routes, middleware=middleware)
