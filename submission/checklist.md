# Final submission checklist

**Deadline: Friday Oct 30, 2026, 10:00 am PT (10:30 pm IST).** Aim to submit on the evening of Oct 29 (IST).

## Project
- [ ] Project works end to end with real Nemotron models (`python cli.py sample_repo` goes red to green)
- [ ] Track chosen on Devpost: Coding and Agentic Engineering
- [ ] Devpost description filled in from `submission/devpost_description.md`, no **[TODO]** left

## Demo
- [ ] Public demo URL works in a private/incognito window
- [ ] Demo's `/health` returns `{"ok":true}`
- [ ] Demo limits work (3 runs per IP per hour, 1 concurrent, `MAX_RUNS_PER_DAY`) and a 429 shows a message, not "Connection lost"
- [ ] Demo URL added to README and Devpost

## Repository
- [ ] Repo is public
- [ ] MIT license is visible in the repo's About box
- [ ] README has the Nemotron, Token Factory and other Nebius sections filled in (no TODOs)
- [ ] `python -m pytest` passes
- [ ] No secrets in git history (`.env` never committed; run a secret scan, including old commits)
- [ ] API key rotated or spend-limited after the event

## Video
- [ ] Public YouTube video, under 3 minutes
- [ ] Opens in a private window; no API keys on screen; no copyrighted music
- [ ] Video URL added to README and Devpost

## Feedback
- [ ] `submission/feedback.md` filled in with real numbers (Token Factory, AI Cloud/Serverless, Nemotron)
- [ ] Feedback pasted into the hackathon form

## Last step
- [ ] Submit before the deadline, then re-open the submission to confirm it saved
