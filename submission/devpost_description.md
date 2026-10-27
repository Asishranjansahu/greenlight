# Greenlight: Devpost description

Fill every **[TODO]** with a real result before submitting.

## Inspiration
Red test suites are a daily time sink. The failing tests already say what correct behaviour is, which makes them a precise spec for an AI agent: the model has to make the code match the tests, and the tests can verify the result. **[TODO: add a personal story or motivation in one or two sentences.]**

## What it does
Greenlight runs a repo's pytest suite, sends the failures and source files to an NVIDIA Nemotron model on Nebius Token Factory, applies the returned patch, and reruns until the tests pass or 5 rounds are used. It then shows a unified diff. The web UI has a traffic-light indicator and a timeline showing, for each model call, the model, role (planner or fixer), time and token usage. Two demo repos are bundled: a calculator module (3 bugs) and a text-utilities module (4 bugs, one needing two files to understand). Test files are read-only to the agent.

## How we built it
- Python agent loop (`agent.py`) that emits events; the CLI and the FastAPI/SSE web server are thin front ends over it.
- Tiered models: a large Nemotron **[TODO: model ID]** as planner for the first diagnosis, a smaller one **[TODO: model ID]** as fixer for retries.
- Token Factory via its OpenAI-compatible API, with retries, a configurable `MAX_TOKENS`, and per-call latency/usage logging.
- Safety: temp copy, strict path validation, read-only tests, 60 s pytest timeout, in-memory rate limits for the public demo (per-IP, global concurrency, daily cap).
- Tests with a mock model, so the suite runs without an API key.
- Deployed on **[TODO: where, e.g. Nebius Serverless Endpoints]**.

## Challenges we ran into
- Getting models to return strict JSON with whole-file contents; we handle malformed or truncated replies with a retry and log the first 200 characters of the raw reply. **[TODO: describe what the real models actually did and how you tuned the prompt.]**
- Stopping the agent from "fixing" tests instead of code, solved by rejecting writes to test files.
- Protecting a public demo from draining credits.
- **[TODO: any other real challenge you hit.]**

## Accomplishments that we're proud of
- Closed loop that verifies its own work with the real test runner.
- **[TODO: real result, e.g. "fixed sample_repo in N rounds, X seconds, Y tokens".]**
- **[TODO: real result for sample_repo_2.]**

## What we learned
- **[TODO: what you learned about Nemotron models, e.g. planner vs fixer behaviour, JSON compliance.]**
- **[TODO: what you learned about Token Factory, e.g. latency, setup.]**

## What's next for Greenlight
- Container sandbox for running tests.
- Patch diffs instead of whole files.
- CI integration that opens a pull request with the fix.
- Support for more languages and test runners.
