#!/usr/bin/env python3
"""Inject the deployment-provided judge key into the mounted config."""

import json
import os
import pwd
import sys
from pathlib import Path

source = Path("/home/judge/judge.yml")
target = Path("/tmp/judge.yml")
key = os.environ["JUDGE_AUTH_KEY"]
if key.startswith("change-me") or len(key) < 32:
    raise RuntimeError("JUDGE_AUTH_KEY must be replaced with a strong secret")
target.write_text(f"key: {json.dumps(key)}\n" + source.read_text())
judge = pwd.getpwnam("judge")
os.chown(target, judge.pw_uid, judge.pw_gid)
target.chmod(0o600)

os.execv("/judge/.docker/entry", ["/judge/.docker/entry", *sys.argv[1:]])
