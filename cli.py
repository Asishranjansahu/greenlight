import sys

from dotenv import load_dotenv

load_dotenv()
from agent import fix  # noqa: E402

verbose = "--verbose" in sys.argv[1:]
args = [a for a in sys.argv[1:] if a != "--verbose"]
path = args[0] if args else "sample_repo"
for ev in fix(path, verbose=verbose):
    if ev["type"] == "done":
        print(f"\n== {ev['status'].upper()} ==\n{ev['diff']}")
    elif ev["type"] == "test_result":
        print(f"[round {ev['round']}] tests {'PASS' if ev['passed'] else 'FAIL'}")
    elif ev["type"] == "model_call":
        print(f"[round {ev['round']}] {ev['role']} ({ev['model']}) replied in {ev['latency_ms']} ms, usage={ev['usage']}")
    elif ev["type"] == "raw_reply":
        print(f"  raw reply:\n{ev['text']}")
    elif ev["type"] == "diagnosis":
        print(f"  diagnosis: {ev['text']}")
    else:
        print(f"  {ev['type']}: {ev.get('files') or ev.get('message', '')}")
