#!/usr/bin/env python3
"""
compare_workshop_pak.py
=======================

Compare every .uasset file inside a Last Oasis workshop pak archive
against the matching live file in a Modkit project, and triage the
results into actionable buckets.

Use this after porting a workshop mod into the Modkit (or after
suspecting that the editor's load + re-save cycle has damaged some
assets) to quickly see what looks like genuine data loss vs. a benign
re-save.

Buckets reported
----------------

  MISSING        — the asset is in the workshop pak but not in the project.
  SHRUNK         — the live file is at least 10% smaller than the original.
                   Strong signal of data loss (e.g. property bag pruning,
                   component overrides dropped, function graphs gutted).
  STRUCT_RENAMED — the original referenced a known-renamed struct (set
                   the marker via --struct-marker) that no longer appears
                   in the live file. Recoverable via `patch_struct_rename.py`.
  DIFF           — files differ but sizes are close. Usually benign editor
                   re-save with newer formatting.
  IDENTICAL      — byte-for-byte identical. Listed as a count only.

Usage
-----

    python compare_workshop_pak.py <pak_zip> <project_root>
                                  [--struct-marker <name>]

  pak_zip          Path to the workshop archive (e.g. Saved/Mods/<Mod>/<id>.zip).
                   The Modkit always produces these alongside the .pak.
  project_root     The Modkit's `Game/` folder (the parent of `Content/`).
  --struct-marker  Old struct name to flag for the STRUCT_RENAMED bucket.
                   Pass once per known C++ rename. If omitted, the
                   STRUCT_RENAMED bucket is skipped entirely.

Example
-------

    python compare_workshop_pak.py \\
        "D:/Program Files/Epic Games/LastOasisModkit/Game/Saved/Mods/MyMod/1234567890.zip" \\
        "D:/Program Files/Epic Games/LastOasisModkit/Game" \\
        --struct-marker OldStructName

Standard library only — no `pip install` step.
"""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path


def sha(b): return hashlib.sha256(b).hexdigest()


def has_marker(b: bytes, marker: str) -> bool:
    return marker.encode("ascii") in b


def main():
    ap = argparse.ArgumentParser(description="Compare workshop pak .uasset files vs. live project files.")
    ap.add_argument("pak_zip", help="Path to the workshop archive (Saved/Mods/<Mod>/<id>.zip)")
    ap.add_argument("project_root", help="Path to the Modkit's Game/ folder")
    ap.add_argument("--struct-marker", action="append", default=[],
                    help="Old struct name to flag for the STRUCT_RENAMED bucket. Pass once per known C++ rename.")
    ap.add_argument("--shrink-threshold", type=float, default=0.9,
                    help="Treat as SHRUNK when current size < orig*threshold (default 0.9)")
    args = ap.parse_args()

    zip_path = Path(args.pak_zip)
    if not zip_path.exists():
        print(f"Workshop zip not found: {zip_path}", file=sys.stderr)
        sys.exit(2)
    project_root = Path(args.project_root)
    content_root = project_root / "Content"
    if not content_root.exists():
        print(f"Project Content/ folder not found: {content_root}", file=sys.stderr)
        sys.exit(2)

    z = zipfile.ZipFile(zip_path)
    entries = [e for e in z.infolist() if e.filename.lower().endswith(".uasset")]
    print(f"Workshop pak has {len(entries)} .uasset files")
    print()

    rows = []  # (status, rel_path, orig_size, curr_size, delta, has_walker)
    for e in entries:
        # Workshop archives use backslash-style paths; normalize.
        rel = e.filename.replace("\\", "/")
        if not rel.lower().startswith("content/"):
            continue
        rel_under_content = rel[len("Content/"):]
        live_path = content_root / Path(rel_under_content)
        with z.open(e) as f:
            orig_bytes = f.read()
        orig_size = len(orig_bytes)

        if not live_path.exists():
            rows.append(("MISSING", rel_under_content, orig_size, 0, -orig_size, False))
            continue

        curr_bytes = live_path.read_bytes()
        curr_size = len(curr_bytes)
        delta = curr_size - orig_size
        marker_in_orig = any(has_marker(orig_bytes, m) for m in args.struct_marker)
        marker_in_curr = any(has_marker(curr_bytes, m) for m in args.struct_marker)

        if sha(orig_bytes) == sha(curr_bytes):
            status = "IDENTICAL"
        elif curr_size < orig_size * args.shrink_threshold:
            status = "SHRUNK"
        elif marker_in_orig and not marker_in_curr:
            status = "STRUCT_RENAMED"
        else:
            status = "DIFF"
        rows.append((status, rel_under_content, orig_size, curr_size, delta, marker_in_orig))

    by_status = {}
    for r in rows:
        by_status.setdefault(r[0], []).append(r)

    for status in ["MISSING", "SHRUNK", "STRUCT_RENAMED", "DIFF", "IDENTICAL"]:
        items = by_status.get(status, [])
        if not items: continue
        print(f"=== {status} ({len(items)}) ===")
        if status == "IDENTICAL":
            print("  (omitted from listing)")
            print()
            continue
        items.sort(key=lambda r: r[4])  # ascending delta = biggest losses first
        for _status, rel, orig, curr, delta, marker in items:
            mark = f"  [{','.join(args.struct_marker)}]" if marker else ""
            print(f"  {orig:>8}  ->  {curr:>8}  ({delta:+8})  {rel}{mark}")
        print()


if __name__ == "__main__":
    main()
