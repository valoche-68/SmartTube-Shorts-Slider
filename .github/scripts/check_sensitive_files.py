#!/usr/bin/env python3
"""Reject private files and recognizable credentials without printing their contents."""
import argparse
from pathlib import PurePosixPath
import re
import subprocess
import sys


def private_path(name):
    path = PurePosixPath(name)
    parts = [part.lower() for part in path.parts]
    leaf = parts[-1]
    return (any(part.startswith(("chat-google-antigravity", "chat google antigravity", "backup_")) for part in parts)
            or leaf in ("original.zip", "configured.zip", "undo.json", "keystore.properties") or leaf == ".env" or leaf.startswith(".env.")
            or leaf.endswith((".jks", ".keystore", ".p12", ".pfx", ".key", ".env")))


SECRET = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
                    rb"gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{70,}|"
                    rb"(?im:^\s*(?:storePassword|keyPassword)\s*=\s*[\"\'][^\"\'\r\n]{6,}[\"\'])")


def check(staged=False):
    args = (["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"] if staged
            else ["ls-files", "-z"])
    names = subprocess.check_output(["git", *args]).decode().split("\0")
    failures = []
    for name in filter(None, names):
        if private_path(name):
            failures.append((name, "private file"))
            continue
        # Always inspect the Git index, including staged content hidden by later edits.
        result = subprocess.run(["git", "show", ":" + name], capture_output=True)
        if result.returncode == 0 and SECRET.search(result.stdout):
            failures.append((name, "possible credential"))
    for name, reason in failures:
        print(f"BLOCKED: {reason}: {name}", file=sys.stderr)
    return bool(failures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true")
    sys.exit(check(parser.parse_args().staged))
