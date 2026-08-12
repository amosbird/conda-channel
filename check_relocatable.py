#!/usr/bin/env python3
"""Fail when custom-package runtime files contain personal absolute paths."""
import json
import os
import sys

FORBIDDEN = (b"/tmp/gentoo/home/amos",)
BUILD_MARKERS = (b"/output/bld/rattler-build_", b"/conda-bld/bld/rattler-build_")


def package_record(prefix, name):
    meta = os.path.join(prefix, "conda-meta")
    matches = []
    for entry in os.listdir(meta):
        if not entry.endswith(".json"):
            continue
        path = os.path.join(meta, entry)
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)
        if record.get("name") == name:
            matches.append(record)
    if len(matches) != 1:
        raise SystemExit(f"expected one installed record for {name}, found {len(matches)}")
    return matches[0]


def main():
    if len(sys.argv) < 3:
        raise SystemExit(f"usage: {sys.argv[0]} PREFIX PACKAGE...")
    prefix = os.path.abspath(os.path.expanduser(sys.argv[1]))
    prefix_bytes = prefix.encode()
    findings = []
    for package in sys.argv[2:]:
        record = package_record(prefix, package)
        for relative in record.get("files", []):
            path = os.path.join(prefix, relative)
            if not os.path.isfile(path) or os.path.islink(path):
                continue
            try:
                with open(path, "rb") as handle:
                    data = handle.read()
            except OSError:
                continue
            for needle in FORBIDDEN:
                if needle in data:
                    findings.append((package, relative, needle.decode()))
            for marker in BUILD_MARKERS:
                if marker in data:
                    findings.append((package, relative, marker.decode()))
            # The current installation prefix is legitimate conda relocation.
            # Reject another known personal prefix, but permit this prefix.
            current_home = b"/data/home/amos"
            if current_home not in prefix_bytes and current_home in data:
                findings.append((package, relative, current_home.decode()))
    for package, relative, needle in findings:
        print(f"{package}: {relative}: contains {needle}")
    if findings:
        raise SystemExit(1)
    print("relocation scan: PASS")


if __name__ == "__main__":
    main()
