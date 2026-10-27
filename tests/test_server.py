import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    server.reset_limits()
    monkeypatch.delenv("MAX_RUNS_PER_DAY", raising=False)
    calls = []

    def fake_fix(path):
        calls.append(path)
        yield {"type": "start", "files": [], "max_rounds": 5}
        yield {"type": "done", "status": "passed", "diff": ""}

    monkeypatch.setattr(server.agent, "fix", fake_fix)
    yield calls
    server.reset_limits()


client = TestClient(server.app)


def test_run_streams_events(clean):
    r = client.get("/run")
    assert r.status_code == 200
    assert '"type": "done"' in r.text
    assert clean[0] == server.REPOS["sample_repo"]


def test_per_ip_limit_is_three_per_hour():
    for _ in range(3):
        assert client.get("/run").status_code == 200
    r = client.get("/run")
    assert r.status_code == 429
    assert "3 runs per hour" in r.json()["message"]
    assert "Retry-After" in r.headers


def test_other_ip_not_affected(monkeypatch):
    for _ in range(3):
        assert client.get("/run", headers={"x-forwarded-for": "1.1.1.1"}).status_code == 200
    assert client.get("/run", headers={"x-forwarded-for": "1.1.1.1"}).status_code == 429
    assert client.get("/run", headers={"x-forwarded-for": "2.2.2.2"}).status_code == 200


def test_falls_back_to_socket_ip_without_header():
    for _ in range(3):
        assert client.get("/run").status_code == 200
    assert client.get("/run").status_code == 429


def test_only_one_concurrent_run(monkeypatch):
    seen = {}

    def slow_fix(path):
        # while this run is active, a second request must be refused
        seen["second"] = client.get("/run", headers={"x-forwarded-for": "5.5.5.5"})
        yield {"type": "done", "status": "passed", "diff": ""}

    monkeypatch.setattr(server.agent, "fix", slow_fix)
    assert client.get("/run", headers={"x-forwarded-for": "4.4.4.4"}).status_code == 200
    assert seen["second"].status_code == 429
    assert "Concurrency limit" in seen["second"].json()["message"]
    # slot released afterwards
    monkeypatch.setattr(server.agent, "fix", lambda p: iter([{"type": "done", "status": "passed", "diff": ""}]))
    assert client.get("/run", headers={"x-forwarded-for": "6.6.6.6"}).status_code == 200


def test_slot_released_after_agent_crash(monkeypatch):
    def boom(path):
        raise RuntimeError("kaput")
        yield

    monkeypatch.setattr(server.agent, "fix", boom)
    r = client.get("/run")
    assert "kaput" in r.text
    monkeypatch.setattr(server.agent, "fix", lambda p: iter([{"type": "done", "status": "passed", "diff": ""}]))
    assert client.get("/run", headers={"x-forwarded-for": "7.7.7.7"}).status_code == 200


def test_daily_cap(monkeypatch):
    monkeypatch.setenv("MAX_RUNS_PER_DAY", "2")
    assert client.get("/run", headers={"x-forwarded-for": "1.0.0.1"}).status_code == 200
    assert client.get("/run", headers={"x-forwarded-for": "1.0.0.2"}).status_code == 200
    r = client.get("/run", headers={"x-forwarded-for": "1.0.0.3"})
    assert r.status_code == 429 and "Daily limit" in r.json()["message"]


def test_repo_whitelist(clean):
    assert client.get("/run?repo=sample_repo_2").status_code == 200
    assert clean[-1] == server.REPOS["sample_repo_2"]
    for bad in ["../etc", "/etc", "tests", "sample_repo/../x", ""]:
        r = client.get("/run", params={"repo": bad})
        assert r.status_code == 400 and "message" in r.json()
    assert len(clean) == 1  # rejected requests never reach the agent or use quota


def test_repos_endpoint_and_health():
    assert set(client.get("/repos").json()["repos"]) == {"sample_repo", "sample_repo_2"}
    assert client.get("/health").json() == {"ok": True}


def test_index_uses_fetch_stream_and_handles_model_reply():
    html = client.get("/").text
    assert "model_reply" in html and "EventSource" not in html
    assert "429" in html and "getReader" in html


def test_first_forwarded_value_is_the_client_key():
    for tail in ("8.8.8.8", "9.9.9.9", "7.7.7.7"):
        assert client.get("/run", headers={"x-forwarded-for": f"3.3.3.3, {tail}"}).status_code == 200
    assert client.get("/run", headers={"x-forwarded-for": "3.3.3.3, 1.2.3.4"}).status_code == 429


def test_slot_released_when_client_disconnects(monkeypatch):
    def endless(path):
        while True:
            yield {"type": "start", "files": [], "max_rounds": 5}

    monkeypatch.setattr(server.agent, "fix", endless)
    assert server.try_admit("10.0.0.1") is None
    gen = server._stream(server.REPOS["sample_repo"])
    next(gen)
    assert server.try_admit("10.0.0.2") is not None  # slot busy
    gen.close()  # what Starlette does when the client goes away
    assert server.try_admit("10.0.0.2") is None


def test_config_error_does_not_consume_quota(monkeypatch):
    def no_config(path):
        yield {"type": "error", "message": "Missing required environment variable(s): X"}
        yield {"type": "done", "status": "error", "diff": ""}

    monkeypatch.setattr(server.agent, "fix", no_config)
    for _ in range(5):
        r = client.get("/run")
        assert r.status_code == 200 and "Missing required" in r.text
