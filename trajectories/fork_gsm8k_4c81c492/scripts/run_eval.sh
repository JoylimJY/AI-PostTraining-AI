#!/usr/bin/env python3
"""Fast eval helper: runs evaluate.py and reports accuracy from the JSON output."""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model_path")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--max-connections", type=int, default=2)
    a = ap.parse_args()

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    cmd = [
        sys.executable, "evaluate.py",
        "--model-path", a.model_path,
        "--limit", str(a.limit),
        "--max-tokens", str(a.max_tokens),
        "--max-connections", str(a.max_connections),
        "--json-output-file", a.out,
    ]
    print("Running:", " ".join(cmd), flush=True)
    start = datetime.now()
    r = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = (datetime.now() - start).total_seconds()
    print(r.stdout[-3000:])
    if r.returncode != 0:
        print("STDERR:", r.stderr[-2000:])
    if os.path.exists(a.out):
        with open(a.out) as f:
            m = json.load(f)
        print(f"RESULT {a.out}: {json.dumps(m)} elapsed={elapsed:.0f}s")
    else:
        print(f"NO JSON OUTPUT (returncode={r.returncode}) elapsed={elapsed:.0f}s")


if __name__ == "__main__":
    main()
