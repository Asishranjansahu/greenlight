# Feedback (hackathon form)

Specific numbers beat general praise. Fill each **[TODO]** from your real runs.

## Measurements
Run `python cli.py sample_repo --verbose` (and `sample_repo_2`). Each model call prints `[round N] <role> (<model>) replied in <ms> ms, usage={...}`.

| Repo | Round | Role | Model ID | Latency (ms) | Prompt tokens | Completion tokens | Valid JSON first try? |
|---|---|---|---|---|---|---|---|
| sample_repo | 1 | planner | **[TODO]** | **[TODO]** | **[TODO]** | **[TODO]** | **[TODO]** |
| sample_repo | 2 | fixer | **[TODO]** | **[TODO]** | **[TODO]** | **[TODO]** | **[TODO]** |
| sample_repo_2 | 1 | planner | **[TODO]** | **[TODO]** | **[TODO]** | **[TODO]** | **[TODO]** |

Total rounds to green: **[TODO]**. Credits used per full run: **[TODO from the Token Factory console]**.

## Nebius Token Factory
- Setup experience (time from signup to first successful call, doc clarity): **[TODO]**
- Model catalog (how easy to find the right Nemotron IDs): **[TODO]**
- Latency and cost (use the table above): **[TODO]**
- Reliability (errors, rate limits, timeouts, retries needed): **[TODO]**
- Usage data in responses (was `usage` always returned?): **[TODO]**
- One concrete suggestion: **[TODO]**

## Nebius AI Cloud / Serverless Endpoints (if used)
- Setup and deploy experience (image, port, env vars/secrets, health check): **[TODO]**
- Cold start and responsiveness: **[TODO]**
- Docs gaps (we had to guess or leave TODOs for: registry setup, secret selectors, health-check setting): **[TODO: confirm which were real gaps]**
- One concrete suggestion: **[TODO]**

## NVIDIA Nemotron
- Model IDs used: planner **[TODO]**, fixer **[TODO]**
- JSON-format compliance (how often "reply with only JSON" was followed; fences, prose, truncation): **[TODO]**
- Fix quality (bugs found, missed or wrongly "fixed"): **[TODO]**
- Planner vs fixer difference (speed, quality): **[TODO]**
- Failures worth reporting (include the first 200 characters of a bad raw reply from the warning, with secrets removed): **[TODO]**
- One concrete suggestion: **[TODO]**
