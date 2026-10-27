"""Greenlight agent: run tests -> ask Nemotron -> patch -> repeat."""
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAX_OUTPUT = 6000
MAX_FILE_CHARS = 20000

SYSTEM = (
    "You are an expert Python engineer fixing failing pytest tests by editing the "
    "SOURCE code only. Never modify test files; the tests define correct behaviour. "
    "Reply with ONLY a JSON object, no markdown: "
    '{"diagnosis": "<short explanation of the root causes>", '
    '"files": [{"path": "<relative .py path>", "new_content": "<complete new file content>"}]}. '
    "Include only files you change, each with its full new content."
)


def is_test_file(p: Path) -> bool:
    n = p.name
    return n.startswith("test_") or n.endswith("_test.py") or n == "conftest.py"


def run_tests(path) -> tuple[bool, str]:
    try:
        p = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
            cwd=path, capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False, "pytest timed out after 60s"
    return p.returncode == 0, (p.stdout + p.stderr)[-MAX_OUTPUT:]


def read_sources(root: Path) -> dict[str, str]:
    out = {}
    for f in sorted(root.rglob("*.py")):
        if any(part in {".venv", "__pycache__", ".git"} for part in f.parts):
            continue
        out[str(f.relative_to(root))] = f.read_text(errors="replace")[:MAX_FILE_CHARS]
    return out


def safe_path(root: Path, rel: str) -> Path:
    """Validate a model-supplied path. Raises ValueError if unsafe."""
    if not isinstance(rel, str) or not rel.strip():
        raise ValueError("empty path")
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"unsafe path: {rel}")
    if p.suffix != ".py":
        raise ValueError(f"only .py files may be changed: {rel}")
    if is_test_file(p):
        raise ValueError(f"test files are read-only: {rel}")
    full = (root / p).resolve()
    if root.resolve() not in full.parents:
        raise ValueError(f"path escapes repo: {rel}")
    return full


def parse_reply(text: str) -> dict:
    t = re.sub(r"```(?:json)?", "", text).strip()
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in reply")
    data = json.loads(t[start : end + 1])
    if not isinstance(data.get("files"), list):
        raise ValueError("missing 'files' list")
    return data


def build_prompt(sources: dict[str, str], output: str, history: list[str]) -> str:
    code = "\n\n".join(f"### {name}\n{body}" for name, body in sources.items())
    prev = ("\n\nPrevious attempts did not fully work:\n" + "\n".join(history)) if history else ""
    return f"Repository files:\n\n{code}\n\nFailing pytest output:\n{output}{prev}"


def make_diff(before: dict[str, str], after: dict[str, str]) -> str:
    chunks = []
    for name in sorted(set(before) | set(after)):
        a, b = before.get(name, ""), after.get(name, "")
        if a != b:
            chunks.extend(difflib.unified_diff(
                a.splitlines(True), b.splitlines(True), f"a/{name}", f"b/{name}"))
    return "".join(chunks)


def fix(src, ask=None, max_rounds: int = 5, verbose: bool = False):
    """Generator of event dicts. Works on a temp copy; `src` is never modified."""
    if ask is None:
        import llm
        try:
            llm.check_config()
        except llm.ConfigError as e:
            yield {"type": "error", "message": str(e)}
            yield {"type": "done", "status": "error", "diff": ""}
            return
        ask = llm.ask
    planner = os.environ.get("PLANNER_MODEL", "planner")
    fixer = os.environ.get("FIXER_MODEL", "fixer")

    work = Path(tempfile.mkdtemp(prefix="greenlight_")) / "repo"
    shutil.copytree(src, work, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    before = read_sources(work)
    history: list[str] = []
    yield {"type": "start", "files": sorted(before), "max_rounds": max_rounds}

    status = "gave_up"
    try:
        for rnd in range(1, max_rounds + 1):
            passed, output = run_tests(work)
            yield {"type": "test_result", "round": rnd, "passed": passed, "output": output}
            if passed:
                status = "passed"
                break
            if rnd == max_rounds:
                break

            role, model = ("planner", planner) if rnd == 1 else ("fixer", fixer)
            prompt = build_prompt(read_sources(work), output, history)

            reply = None
            stats: dict = {}
            for attempt in range(2):
                raw = ""
                try:
                    t0 = time.perf_counter()
                    raw = ask(model, SYSTEM, prompt if attempt == 0 else
                              prompt + "\n\nYour last reply was not valid JSON. Reply with ONLY the JSON object.")
                    stats = {"latency_ms": round((time.perf_counter() - t0) * 1000),
                             "usage": getattr(raw, "usage", None)}
                    yield {"type": "model_call", "round": rnd, "role": role, "model": model,
                           "attempt": attempt + 1, **stats}
                    if verbose:
                        yield {"type": "raw_reply", "round": rnd, "text": str(raw)}
                    if getattr(raw, "finish_reason", None) == "length":
                        raise ValueError("reply truncated (finish_reason=length)")
                    reply = parse_reply(raw)
                    break
                except (ValueError, json.JSONDecodeError) as e:
                    yield {"type": "warning",
                           "message": f"Invalid model reply ({e}); raw[:200]={str(raw)[:200]!r}"}
            if reply is None:
                history.append(f"Round {rnd}: model returned unusable output.")
                continue

            diagnosis = str(reply.get("diagnosis", ""))
            yield {"type": "diagnosis", "round": rnd, "text": diagnosis, **stats}

            changed = []
            for f in reply["files"]:
                try:
                    target = safe_path(work, f.get("path"))
                    content = f.get("new_content")
                    if not isinstance(content, str):
                        raise ValueError("new_content must be a string")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content)
                    changed.append(str(target.relative_to(work.resolve())))
                except ValueError as e:
                    yield {"type": "warning", "message": f"Rejected patch: {e}"}
            yield {"type": "patch", "round": rnd, "files": changed}
            history.append(f"Round {rnd}: changed {changed or 'nothing'}; diagnosis: {diagnosis[:300]}")
    except Exception as e:
        yield {"type": "error", "message": str(e)}
        status = "error"

    diff = make_diff(before, read_sources(work))
    yield {"type": "done", "status": status, "diff": diff}
    shutil.rmtree(work.parent, ignore_errors=True)
