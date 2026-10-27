# Video script (target 2:20, hard limit under 3:00)

Do one successful real run before recording and keep it as a fallback clip. Fill in **[TODO]** numbers from your real run.

| Time | Show | Say |
|---|---|---|
| 0:00-0:15 | Terminal: `cd sample_repo && pytest`, red output | "Broken tests cost developers hours. This small repo has 7 tests, and 4 of them fail." |
| 0:15-1:15 | Web UI: pick `sample_repo`, click Fix. Lamp goes red, amber, green. Timeline fills in. | "Greenlight runs the tests, sends the failures to NVIDIA Nemotron on Nebius Token Factory, applies the patch and reruns, until the tests pass. Here the planner model diagnosed it in **[TODO] s**, using **[TODO] tokens**." |
| 1:15-1:35 | The diff and the summary line | "Three bugs fixed, and it never touched the tests. They are read-only to the agent." |
| 1:35-1:55 | Switch to `sample_repo_2` (optionally speed up the footage) | "A second repo, where one bug spans two files, so the model has to read both." |
| 1:55-2:15 | README architecture diagram | "A large Nemotron model plans, a smaller one retries. Token Factory's OpenAI-compatible API made integration simple. **[TODO: one real observation about latency or cost.]** Paths are validated, tests are read-only, and the demo is rate-limited." |
| 2:15-2:25 | Title card | "Next: container sandboxing and opening pull requests from CI. Greenlight." |

## Shot list
1. Terminal, red pytest output (`sample_repo`).
2. Browser at the demo URL (or localhost), the dropdown, and the Fix button.
3. Timeline with model call lines (model, role badge, seconds, tokens).
4. Green lamp, summary line, diff section.
5. `sample_repo_2` run.
6. README architecture section.
7. Closing card with the repo URL.

## Recording checklist
- [ ] Screen recorded at 1080p; browser zoom so text is readable (about 125%).
- [ ] Terminal font large enough to read in a small player.
- [ ] No API keys or `.env` on screen (close the editor tab, don't `cat .env`).
- [ ] No copyrighted music (none, or royalty-free only).
- [ ] Voice clear, under 3:00 total (aim for 2:30 or less).
- [ ] One successful take saved as a fallback in case the live run hiccups.
- [ ] Notifications off.

## YouTube upload steps
1. Go to YouTube Studio, then Create, then Upload video.
2. Title: "Greenlight: AI agent that fixes failing tests (Nemotron on Nebius)". Add the repo link in the description.
3. Audience: select "No, it's not made for kids".
4. Visibility: **Public** (not Unlisted or Private, unless the rules explicitly allow it).
5. Confirm the length is under 3 minutes in the video list.
6. Open the link in a private window to confirm it plays, then copy it into the README and Devpost.
