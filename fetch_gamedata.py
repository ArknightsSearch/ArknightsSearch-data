#!/usr/bin/env python3
"""
Helper script to fetch Arknights game data from upstream repositories.

Clones/pulls:
  - Kengxxiao/ArknightsGameData     (zh_CN)      → ./gamedata/
  - Kengxxiao/ArknightsGameData_YoStar (en_US, ja_JP, ko_KR) → ./gamedata_yoster/

Then merges en_US and ja_JP from gamedata_yoster into gamedata/.

Usage:
    python fetch_gamedata.py              # fetch data for all languages
    python fetch_gamedata.py --no-yoster  # skip YoStar (zh_CN only)
    python fetch_gamedata.py --no-pull    # skip git pull, only merge yoster data
    python fetch_gamedata.py --languages en_US ja_JP  # only merge specific languages
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

CWD = Path(__file__).resolve().parent

GAMEDATA_REPO = "https://github.com/Kengxxiao/ArknightsGameData.git"
GAMEDATA_YOSTER_REPO = "https://github.com/Kengxxiao/ArknightsGameData_YoStar.git"

GAMEDATA_DIR = CWD / "gamedata"
GAMEDATA_YOSTER_DIR = CWD / "gamedata_yoster"

YOSTER_LANGUAGES = ("en_US", "ja_JP", "ko_KR")


def _git_run(cmd: list[str], cwd: Path | None = None) -> bool:
    process = subprocess.Popen(
        cmd, cwd=cwd,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    assert process.stderr is not None
    for line in process.stderr:
        line = line.rstrip()
        if line:
            print(f"  {line}")
    process.wait()
    if process.returncode != 0:
        print(f"[ERROR] git command failed (exit {process.returncode})", file=sys.stderr)
        return False
    return True


def clone_or_pull(repo_url: str, target: Path) -> bool:
    if (target / ".git").exists():
        print(f"[pull] {target.name} ...")
        return _git_run(["git", "pull", "--ff-only", "--progress"], cwd=target)
    else:
        print(f"[clone] {repo_url} → {target}")
        return _git_run(["git", "clone", "--progress", "--depth", "1", repo_url, str(target)])


def merge_yoster_languages(languages: tuple[str, ...]) -> None:
    for lang in languages:
        src = GAMEDATA_YOSTER_DIR / lang
        dst = GAMEDATA_DIR / lang
        if not src.is_dir():
            print(f"[warn] YoStar source not found: {src}", file=sys.stderr)
            continue

        if dst.exists():
            print(f"[rm] {dst}")
            shutil.rmtree(dst)

        print(f"[cp] {src} → {dst}")
        shutil.copytree(src, dst)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Arknights game data from upstream repositories."
    )
    parser.add_argument(
        "--no-pull",
        action="store_true",
        help="Skip git pull/clone, only merge yoster data (if applicable).",
    )
    parser.add_argument(
        "--no-yoster",
        action="store_true",
        help="Skip YoStar repo entirely (zh_CN only).",
    )
    parser.add_argument(
        "--languages",
        nargs="*",
        default=list(YOSTER_LANGUAGES),
        help=f"Languages to merge from yoster. Default: {' '.join(YOSTER_LANGUAGES)}",
    )
    args = parser.parse_args()

    ok = True

    if not args.no_pull:
        ok &= clone_or_pull(GAMEDATA_REPO, GAMEDATA_DIR)

    if not args.no_yoster and not args.no_pull:
        ok &= clone_or_pull(GAMEDATA_YOSTER_REPO, GAMEDATA_YOSTER_DIR)

    if not args.no_yoster and args.languages:
        merge_yoster_languages(tuple(args.languages))

    if not args.no_yoster and GAMEDATA_YOSTER_DIR.exists() and ok:
        print(f"[cleanup] Removing {GAMEDATA_YOSTER_DIR.name}")
        shutil.rmtree(GAMEDATA_YOSTER_DIR)

    if ok:
        print("[done] gamedata fetched successfully.")
    else:
        print("[error] Some steps failed. Check output above.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
