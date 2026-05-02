#!/usr/bin/env python3
"""
migrate_mod_v2_to_v3.py
=======================

Stage an existing v2 Last Oasis mod (assets + manifest under
Content/Mods/<Mod>/) so the new Modkit can find and edit it. The actual
v2 -> v3 schema conversion happens inside the Modkit when you click
Mod Manager -> Save Mod.

What it does
------------

The new Modkit's mod-selection screen scans
<ModkitRoot>/Game/Saved/Mods/<Mod>/modinfo.json for mod entries; it
does NOT look in Content/Mods/<Mod>/. So an old v2 mod that has its
modinfo.json sitting at Content/Mods/<Mod>/modinfo.json is invisible
in the new Modkit until the manifest is moved to the Saved/ side.

This script does exactly that: it moves modinfo.json from
Content/Mods/<Mod>/ to Saved/Mods/<Mod>/, leaves the assets where they
already are at Content/Mods/<Mod>/<files>, and keeps the manifest as
modKitVersion 2. The Modkit then:

  1. Finds the mod in the selection screen via the Saved/-side manifest.
  2. Reads it, sees modKitVersion 2.
  3. Loads the assets from Content/Mods/<Mod>/ (the v2 source location).
  4. Lets you edit them.
  5. Mod Manager -> Save Mod migrates to v3 properly, populating the
     asset-list fields (createdAssets / modifiedAssets / assetTree /
     assetHashes) so the assets stay flagged and survive future boots.

Why not perform the v2 -> v3 schema rewrite here?
-------------------------------------------------

An earlier version of this script DID do the rewrite (move assets into
Saved/Mods/<Mod>/Assets/ and emit a v3 manifest with empty asset-list
fields, expecting Mod Manager to populate them on first Save Mod).
That doesn't work: the Modkit's mod-load sequence garbage-collects
anything in Saved/Mods/<Mod>/Assets/ that isn't already flagged in
those fields, so the assets vanish before you can reach Save Mod.
Chicken-and-egg.

By leaving the manifest as v2 and the assets at the v2 source location,
the Modkit's GC doesn't kick in (the GC is scoped to v3-layout
Saved/Mods/<Mod>/Assets/ trees), and Save Mod's in-Modkit migration
generates a v3 manifest with the asset-list fields populated correctly
(which is something this script can't do safely on its own - the
official v3 sample uses syntax that isn't strictly valid JSON, and
the Modkit's loader expects specific shapes that vary by asset type).

Reference:
  docs/modkit-guides/porting-a-mod-from-old-modkit.md  (in this repo)
  scripts/recover_mod_from_workshop.py - sibling script for the case
    where the starting point is a Workshop-cached zip rather than an
    existing v2 source tree.

Usage
-----

    # Dry-run (default): print the move plan, change nothing.
    python migrate_mod_v2_to_v3.py \\
        --modkit "D:/Program Files/Epic Games/LastOasisModkit" \\
        --mod MyTestMod

    # Actually do it (creates zip backup first).
    python migrate_mod_v2_to_v3.py \\
        --modkit "..." --mod MyTestMod --apply

What it does NOT cover
----------------------

- Moving assets into Saved/Mods/<Mod>/Assets/. They stay at
  Content/Mods/<Mod>/<files>. Save Mod inside the Modkit moves them
  during its v3 migration.
- Rewriting the manifest schema. Save Mod handles that too.
- Any post-migration steps (cooking, uploading, etc).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Dict, List


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def log(msg: str = "") -> None:
    print(msg)


def section(title: str) -> None:
    bar = "=" * 70
    print(f"\n{bar}\n{title}\n{bar}")


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def load_v2_manifest(manifest_path: Path) -> Dict:
    if not manifest_path.is_file():
        err(f"v2 modinfo.json not found at {manifest_path}")
        sys.exit(2)
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        err(f"v2 modinfo.json is not valid JSON: {e}")
        sys.exit(2)

    version = data.get("modKitVersion")
    if version == 3:
        err(f"This mod is already modKitVersion 3 ({manifest_path}). "
            "Nothing to do.")
        sys.exit(2)
    if version != 2:
        err(f"Unexpected modKitVersion {version!r} in {manifest_path}. "
            "Expected 2.")
        sys.exit(2)

    return data


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------


def make_backup(modkit_root: Path, mod_name: str,
                content_mod_folder: Path,
                saved_mod_folder: Path) -> Path:
    """Zip up the v2 manifest at the Content/ side (about to be moved)
    and any pre-existing Saved/Mods/<Mod>/ state (for --force overwrites
    or leftover broken-v3 trees we're cleaning up)."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = modkit_root / f"{mod_name}_v2_backup_{timestamp}.zip"
    log(f"  Creating backup: {backup_path}")
    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest = content_mod_folder / "modinfo.json"
        if manifest.is_file():
            zf.write(manifest, manifest.relative_to(modkit_root))
        if saved_mod_folder.is_dir():
            for root, _dirs, files in os.walk(saved_mod_folder):
                for name in files:
                    full = Path(root) / name
                    zf.write(full, full.relative_to(modkit_root))
    return backup_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=("Stage a v2 Last Oasis mod so the new Modkit can find "
                     "and edit it. Moves modinfo.json from "
                     "Content/Mods/<Mod>/ to Saved/Mods/<Mod>/, leaves "
                     "assets at Content/Mods/<Mod>/. Does NOT rewrite "
                     "the manifest to v3 - Save Mod inside the Modkit does "
                     "that step properly."),
    )
    parser.add_argument(
        "--modkit",
        required=True,
        type=Path,
        help="Path to the Modkit install root (the folder containing 'Game/').",
    )
    parser.add_argument(
        "--mod",
        required=True,
        help="Mod folder name (matches v2 'folderName', e.g. MyTestMod).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform the move. Default is dry-run.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting an existing Saved/Mods/<Mod>/modinfo.json "
             "and removing any leftover Saved/Mods/<Mod>/Assets/.",
    )
    args = parser.parse_args(argv)

    modkit_root: Path = args.modkit.resolve()
    if not modkit_root.is_dir():
        err(f"--modkit path does not exist: {modkit_root}")
        return 2

    game_root = modkit_root / "Game"
    if not game_root.is_dir():
        err(f"Could not find 'Game/' under modkit root: {game_root}")
        return 2

    content_root = game_root / "Content"
    saved_root = game_root / "Saved"
    mod_name: str = args.mod

    content_mod_folder = content_root / "Mods" / mod_name
    content_manifest = content_mod_folder / "modinfo.json"
    saved_mod_folder = saved_root / "Mods" / mod_name
    saved_manifest = saved_mod_folder / "modinfo.json"
    saved_assets = saved_mod_folder / "Assets"

    section("Inputs")
    log(f"Modkit root:           {modkit_root}")
    log(f"Mod name:              {mod_name}")
    log(f"v2 source folder:      {content_mod_folder}")
    log(f"v2 modinfo.json:       {content_manifest}")
    log(f"Target manifest path:  {saved_manifest}")

    # --- Validation ---------------------------------------------------------

    if not content_mod_folder.is_dir():
        err(f"v2 mod folder not found: {content_mod_folder}")
        return 2

    v2 = load_v2_manifest(content_manifest)

    declared_folder = v2.get("folderName")
    if declared_folder and declared_folder != mod_name:
        log(f"WARNING: --mod {mod_name!r} differs from manifest folderName "
            f"{declared_folder!r}; using --mod.")

    if saved_manifest.exists() and not args.force:
        err(f"Saved/Mods/{mod_name}/modinfo.json already exists.")
        log(f"       Refusing to overwrite. Re-run with --force to override.")
        return 2

    if saved_assets.exists() and not args.force:
        err(f"Saved/Mods/{mod_name}/Assets/ exists - probably from an "
            "earlier broken v3-target migration attempt. Re-run with --force "
            "to remove it.")
        return 2

    # Quick asset count for reassurance
    asset_count = sum(1 for p in content_mod_folder.rglob("*")
                      if p.is_file() and p.name != "modinfo.json")

    section("Plan")
    log(f"  MOVE  {content_manifest.relative_to(modkit_root)}")
    log(f"   ->   {saved_manifest.relative_to(modkit_root)}")
    log(f"")
    log(f"  KEEP  {content_mod_folder.relative_to(modkit_root)}/  "
        f"({asset_count} asset file(s) - stay where they are)")
    if saved_assets.exists():
        log(f"")
        log(f"  REMOVE  {saved_assets.relative_to(modkit_root)}/  "
            "(leftover from a prior broken-v3 attempt)")

    if not args.apply:
        section("Dry run - no changes made")
        log("Re-run with --apply to perform the move. A zip backup of\n"
            "the v2 manifest (and any pre-existing Saved/Mods/<Mod>/ state)\n"
            "will be created automatically before any change.")
        return 0

    # --- Apply --------------------------------------------------------------

    section("Applying")

    backup_path = make_backup(modkit_root, mod_name, content_mod_folder,
                              saved_mod_folder)
    log(f"  Backup created:    {backup_path}")

    # Clean up leftover broken-v3 Assets/ if --force was used
    if saved_assets.exists():
        shutil.rmtree(saved_assets)
        log(f"  Removed leftover:  {saved_assets.relative_to(modkit_root)}/")

    # Move the manifest
    saved_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(content_manifest), str(saved_manifest))
    log(f"  Manifest moved:    Content/Mods/{mod_name}/modinfo.json")
    log(f"                  -> Saved/Mods/{mod_name}/modinfo.json")

    section("Done")
    log("Next steps:")
    log("  1. Launch the Modkit. The mod should appear in the selection")
    log("     screen as a v2 mod loadable from Content/Mods/<Mod>/.")
    log("  2. Select it. Edit as needed.")
    log("  3. Mod Manager -> Save Mod. The Modkit handles the v3")
    log("     migration internally and properly populates the asset-list")
    log("     fields (so the assets stay flagged and survive future boots).")
    log("  4. Cook & test against a local modded server before re-uploading.")
    log(f"\nIf anything went wrong, restore from {backup_path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
