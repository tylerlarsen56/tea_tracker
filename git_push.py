#!/usr/bin/env python3
"""
Quick helper to add, commit, and push index.html.

Usage:
    python git_push.py "commit message here"
"""

import subprocess
import sys


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    if len(sys.argv) != 2:
        print('Usage: python git_push.py "commit message"')
        sys.exit(1)

    commit_message = sys.argv[1]

    run(["git", "add", "index.html"])
    run(["git", "commit", "-m", commit_message])
    run(["git", "push"])


if __name__ == "__main__":
    main()
