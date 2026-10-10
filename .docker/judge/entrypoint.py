#!/usr/bin/env python3
"""Inject the deployment-provided judge key into the mounted config."""

import json
import os
import sys
from pathlib import Path

source = Path("/home/judge/judge.yml")
target = Path("/tmp/judge.yml")
key = os.environ["JUDGE_AUTH_KEY"]
if key.startswith("change-me") or len(key) < 32:
    raise RuntimeError("JUDGE_AUTH_KEY must be replaced with a strong secret")
target.write_text(f"key: {json.dumps(key)}\n" + source.read_text())

os.execvp("dmoj", ["dmoj", *sys.argv[1:]])
