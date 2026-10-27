import json
from pathlib import Path

import pytest

from agent import fix, parse_reply, run_tests, safe_path

SAMPLE = Path(__file__).resolve().parent.parent / "sample_repo"

FIXED = '''def average(nums):
    return sum(nums) / len(nums)


def divide(a, b):
    if b == 0:
        raise ValueError("division by zero")
    return a / b


def percent(part, whole):
    if whole == 0:
        return 0.0
    return part / whole * 100


def clamp(x, low, high):
    return max(low, min(x, high))
'''


def test_safe_path_rules(tmp_path):
    assert safe_path(tmp_path, "calc.py").name == "calc.py"
    for bad in ["/etc/passwd.py", "../x.py", "a/../../x.py", "test_calc.py", "notes.txt", "conftest.py"]:
        with pytest.raises(ValueError):
            safe_path(tmp_path, bad)


def test_parse_reply_strips_fences():
    raw = '```json\n{"diagnosis": "d", "files": []}\n```'
    assert parse_reply(raw)["diagnosis"] == "d"
    with pytest.raises(ValueError):
        parse_reply("no json here")


def test_truncated_json_warning_includes_raw_prefix():
    from llm import Reply

    def fake_ask(model, system, user):
        r = Reply('{"diagnosis": "d", "files": [{"path": "calc.py", "new_con')
        r.finish_reason = "length"
        r.usage = {"total_tokens": 5}
        return r

    events = list(fix(SAMPLE, ask=fake_ask, max_rounds=2))
    warns = [e for e in events if e["type"] == "warning"]
    assert warns and "truncated" in warns[0]["message"] and '{"diagnosis"' in warns[0]["message"]
    calls = [e for e in events if e["type"] == "model_call"]
    assert calls and "latency_ms" in calls[0] and calls[0]["usage"] == {"total_tokens": 5}


def test_sample_repo_really_fails():
    passed, out = run_tests(SAMPLE)
    assert not passed and "failed" in out


def test_agent_fixes_sample_repo_with_mock_model():
    def fake_ask(model, system, user):
        return json.dumps({"diagnosis": "three bugs",
                           "files": [{"path": "calc.py", "new_content": FIXED},
                                     {"path": "test_calc.py", "new_content": "assert True"}]})

    events = list(fix(SAMPLE, ask=fake_ask))
    done = events[-1]
    assert done["status"] == "passed"
    assert "-    return sum(nums) / (len(nums) - 1)" in done["diff"]
    assert any(e["type"] == "warning" and "read-only" in e["message"] for e in events)
    assert "def test_average" in (SAMPLE / "test_calc.py").read_text()


def test_sample_repo_2_is_fixable_with_mock_model():
    repo2 = SAMPLE.parent / "sample_repo_2"
    assert not run_tests(repo2)[0]
    cfg = (repo2 / "config.py").read_text().replace('SEPARATOR = "_"', 'SEPARATOR = "-"')
    utils = (repo2 / "text_utils.py").read_text()
    utils = utils.replace("text[:width] + ELLIPSIS", "text[: width - len(ELLIPSIS)] + ELLIPSIS")
    utils = utils.replace('text.split(" ")', "text.split()")
    utils = utils.replace(
        "return text == text[::-1]",
        'cleaned = "".join(c.lower() for c in text if c.isalnum())\n    return cleaned == cleaned[::-1]')

    def fake_ask(model, system, user):
        return json.dumps({"diagnosis": "four bugs", "files": [
            {"path": "config.py", "new_content": cfg}, {"path": "text_utils.py", "new_content": utils}]})

    assert list(fix(repo2, ask=fake_ask))[-1]["status"] == "passed"


@pytest.mark.parametrize("name", ["sample_repo", "sample_repo_2"])
def test_each_sample_repo_fails_before_fixing(name):
    passed, out = run_tests(SAMPLE.parent / name)
    assert not passed and "failed" in out
