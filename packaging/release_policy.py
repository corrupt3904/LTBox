"""Validate stable release versions without third-party dependencies."""

import argparse
import json
from pathlib import Path
import re
import tomllib


def version(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value):
        raise ValueError(f"Expected a stable X.Y.Z version, got {value!r}")
    return tuple(map(int, value.removeprefix("v").split(".")))


def check_tag(tag: str, manifest: Path) -> None:
    if not tag.startswith("v"):
        raise ValueError("Release tags must start with v")
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    current = data["workspace"]["package"]["version"]
    if version(tag) != version(current):
        raise ValueError(f"Tag {tag} does not match workspace version {current}")


def compare(tag: str, destination: Path) -> None:
    incoming = version(tag)
    if not destination.exists():
        return  # First publication into an initialized repository.
    text = destination.read_text(encoding="utf-8")
    if destination.suffix == ".json":
        current = json.loads(text)["version"]
    else:
        pattern = r'^\s*version\s+"([^"]+)"' if destination.suffix == ".rb" else r"^Version: (\S+)"
        match = re.search(pattern, text, re.MULTILINE)
        if match is None:
            raise ValueError(f"Cannot determine published version in {destination}")
        current = match.group(1)
    if incoming < version(current):
        raise ValueError(f"Refusing downgrade from {current} to {tag}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["tag", "compare"])
    parser.add_argument("tag")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.operation == "tag":
        check_tag(args.tag, args.path)
    else:
        compare(args.tag, args.path)
