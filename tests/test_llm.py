import httpx
import openai
import pytest

import agent
import llm

ENV = {"TOKEN_FACTORY_BASE_URL": "http://example.invalid/v1", "TOKEN_FACTORY_API_KEY": "k",
       "PLANNER_MODEL": "big", "FIXER_MODEL": "small"}


def status_error(code):
    req = httpx.Request("POST", "http://example.invalid/v1/chat/completions")
    resp = httpx.Response(code, request=req)
    cls = {429: openai.RateLimitError, 401: openai.AuthenticationError, 404: openai.NotFoundError,
           500: openai.InternalServerError, 503: openai.InternalServerError}[code]
    return cls(f"status {code}", response=resp, body=None)


class FakeClient:
    def __init__(self, errors):
        self.errors, self.calls = list(errors), 0
        self.chat = self
        self.completions = self

    def create(self, **kw):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)

        class M:
            content = '{"diagnosis": "d", "files": []}'

        class C:
            message, finish_reason = M, "stop"

        class R:
            choices, usage = [C], None

        return R


@pytest.fixture
def env(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)
    sleeps = []
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    return sleeps


def use(monkeypatch, client):
    monkeypatch.setattr(llm, "_get_client", lambda: client)
    return client


def test_missing_config_raises_immediately_listing_variables(monkeypatch):
    for k in ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("TOKEN_FACTORY_API_KEY", "   ")  # blank counts as missing
    sleeps = []
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    with pytest.raises(llm.ConfigError) as ei:
        llm.ask("m", "s", "u")
    msg = str(ei.value)
    for k in ENV:
        assert k in msg
    assert "copy .env.example to .env and restart the server" in msg.lower()
    assert sleeps == []


def test_only_missing_variables_are_listed(monkeypatch, env):
    monkeypatch.delenv("FIXER_MODEL")
    with pytest.raises(llm.ConfigError) as ei:
        llm.ask("m", "s", "u")
    assert "FIXER_MODEL" in str(ei.value) and "PLANNER_MODEL" not in str(ei.value)


@pytest.mark.parametrize("code", [401, 404])
def test_auth_and_not_found_are_not_retried(monkeypatch, env, code):
    client = use(monkeypatch, FakeClient([status_error(code)] * 3))
    with pytest.raises(llm.LLMError) as ei:
        llm.ask("m", "s", "u")
    assert client.calls == 1 and env == []
    assert f"HTTP {code}" in str(ei.value) and ei.value.status == code


@pytest.mark.parametrize("code", [429, 503])
def test_429_and_5xx_are_retried_then_succeed(monkeypatch, env, code):
    client = use(monkeypatch, FakeClient([status_error(code), status_error(code)]))
    assert "diagnosis" in llm.ask("m", "s", "u")
    assert client.calls == 3 and len(env) == 2


def test_retries_exhausted_reports_status(monkeypatch, env):
    client = use(monkeypatch, FakeClient([status_error(500)] * 5))
    with pytest.raises(llm.LLMError) as ei:
        llm.ask("m", "s", "u", retries=2)
    assert client.calls == 3 and "HTTP 500" in str(ei.value) and "3 attempts" in str(ei.value)


def test_network_errors_and_timeouts_are_retried(monkeypatch, env):
    req = httpx.Request("POST", "http://example.invalid")
    errs = [openai.APIConnectionError(request=req), openai.APITimeoutError(request=req)]
    client = use(monkeypatch, FakeClient(errs))
    assert llm.ask("m", "s", "u")
    assert client.calls == 3


def test_fix_yields_error_first_when_config_missing(monkeypatch, tmp_path):
    for k in ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(agent, "run_tests", lambda *_: pytest.fail("tests must not run"))
    events = list(agent.fix(tmp_path))
    assert [e["type"] for e in events] == ["error", "done"]
    assert "TOKEN_FACTORY_BASE_URL" in events[0]["message"]
    assert "restart the server" in events[0]["message"]
    assert events[1]["status"] == "error"
