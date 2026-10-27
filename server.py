import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

load_dotenv()
import agent  # noqa: E402

ROOT = Path(__file__).parent
app = FastAPI(title="Greenlight")

# Whitelist: the query parameter maps to a fixed directory, never a path.
REPOS = {"sample_repo": ROOT / "sample_repo", "sample_repo_2": ROOT / "sample_repo_2"}
DEFAULT_REPO = "sample_repo"

PER_IP_LIMIT = 3
PER_IP_WINDOW = 3600  # seconds
RUN_LEASE = 300  # a slot held longer than this is considered leaked and is reclaimed

_lock = threading.Lock()
_ip_hits: dict[str, list[float]] = {}
_active_since: float | None = None
_day = {"date": "", "count": 0}


def reset_limits():
    global _active_since
    with _lock:
        _ip_hits.clear()
        _active_since = None
        _day.update(date="", count=0)


def max_runs_per_day() -> int:
    try:
        return int(os.environ.get("MAX_RUNS_PER_DAY", "100"))
    except ValueError:
        return 100


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd.strip():
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def try_admit(ip: str):
    """Returns None if admitted (and records it), else (message, retry_after_seconds)."""
    global _active_since
    now = time.time()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _lock:
        if _day["date"] != today:
            _day.update(date=today, count=0)
        if _day["count"] >= max_runs_per_day():
            return ("Daily limit reached: this demo allows a limited number of runs per day. Try again tomorrow (UTC).", 3600)
        if _active_since is not None and now - _active_since < RUN_LEASE:
            return ("Concurrency limit reached: only 1 run at a time and one is in progress. Try again in about a minute.", 30)
        hits = [t for t in _ip_hits.get(ip, []) if now - t < PER_IP_WINDOW]
        if len(hits) >= PER_IP_LIMIT:
            wait = int(PER_IP_WINDOW - (now - hits[0])) + 1
            return (f"Limit reached: {PER_IP_LIMIT} runs per hour per visitor. "
                    f"Try again in {max(1, wait // 60)} minute(s).", wait)
        hits.append(now)
        _ip_hits[ip] = hits
        _day["count"] += 1
        _active_since = now
    return None


def release():
    global _active_since
    with _lock:
        _active_since = None


def refund(ip: str):
    """Give back quota for a run that failed before doing any work (e.g. missing config)."""
    with _lock:
        if _ip_hits.get(ip):
            _ip_hits[ip].pop()
        _day["count"] = max(0, _day["count"] - 1)


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/repos")
def repos():
    return {"repos": list(REPOS), "default": DEFAULT_REPO}


def _stream(path, ip=None):
    """SSE generator. The slot is always released: on completion, error, or client disconnect (generator close)."""
    try:
        first = True
        for ev in agent.fix(path):
            if first and ev.get("type") == "error" and ip:
                refund(ip)  # fix() reports config errors before doing any work
            first = False
            yield f"data: {json.dumps(ev)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'status': 'error', 'diff': ''})}\n\n"
    finally:
        release()


@app.get("/run")
def run(request: Request, repo: str = DEFAULT_REPO):
    if repo not in REPOS:
        return JSONResponse({"message": f"Unknown repo. Choose one of: {', '.join(REPOS)}."}, status_code=400)
    ip = client_ip(request)
    denied = try_admit(ip)
    if denied:
        message, retry = denied
        return JSONResponse({"message": message}, status_code=429, headers={"Retry-After": str(retry)})

    return StreamingResponse(_stream(REPOS[repo], ip), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})



@app.get("/health")
def health():
    return {"ok": True}
