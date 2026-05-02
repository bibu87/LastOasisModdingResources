#!/usr/bin/env python3
"""
recover_mod_from_workshop.py
============================

Recover a Last Oasis mod from its Steam Workshop download (cached by the
Modkit under Game/Saved/Mods/<ModName>/) into a state where it can be
loaded and edited in the Modkit.

When you subscribe to a mod on Steam Workshop, the Modkit deposits the
Workshop download into:

    <ModkitRoot>/Game/Saved/Mods/<ModName>/
        <WORKSHOP_ID>.zip       <- source assets in old (v2) layout
        <WORKSHOP_ID>.pak       <- cooked pak
        <WORKSHOP_ID>.sig       <- signature
        modinfo.json            <- v2 manifest (this is what the Modkit's
                                   mod-selection screen scans for)

This script unpacks <WORKSHOP_ID>.zip into Game/Content/ (its entries
already start with "Content/Mods/<ModName>/...") so the assets land at
the v2 source location: Game/Content/Mods/<ModName>/. The v2 modinfo.json
is left untouched at Saved/Mods/<ModName>/modinfo.json - that's where
the Modkit looks for the mod entry. Once you load the mod in the Modkit
you can edit, then click Mod Manager -> Save Mod, which migrates it to
v3 properly.

Why this layout?
----------------

Two earlier approaches DIDN'T work:

  1. Extract to Saved/Mods/<ModName>/Assets/ + rewrite manifest to v3.
     The Modkit garbage-collects anything in Saved/Mods/<ModName>/Assets/
     that isn't already flagged in the manifest's createdAssets /
     modifiedAssets / assetTree / assetHashes fields - so the assets
     vanish before you can reach Save Mod. Chicken-and-egg.

  2. Extract to Content/Mods/<ModName>/ AND move modinfo there too.
     The Modkit's mod-selection screen only scans Saved/Mods/<Mod>/
     for modinfo.json - moving it to Content/ makes the mod invisible.

What WORKS (this script's behavior):

  - Manifest stays at Saved/Mods/<ModName>/modinfo.json (Modkit finds it).
  - Assets land at Content/Mods/<ModName>/<files> (v2 source location;
    no GC there).
  - Modkit reads the v2 manifest, sees modKitVersion=2, loads assets
    from Content/Mods/<ModName>/. Editable. Then Save Mod migrates
    properly to v3.

After running this script you have two paths to v3:

  - Open the mod in the Modkit, edit, then Mod Manager -> Save Mod
    (the Modkit handles the v3 migration internally and populates the
    asset-list fields properly).
  - Run scripts/migrate_mod_v2_to_v3.py to do the v2 -> v3 layout
    move offline (still requires Save Mod afterwards).

Reference:
  docs/modkit-guides/porting-a-mod-from-old-modkit.md  (in this repo)
  scripts/migrate_mod_v2_to_v3.py - sibling script for v2->v3 migration

Usage
-----

    # Dry-run (default): print what would happen, change nothing.
    python recover_mod_from_workshop.py \\
        --modkit "D:/Program Files/Epic Games/LastOasisModkit"

    # Recover a single named mod.
    python recover_mod_from_workshop.py \\
        --modkit "..." --mod BetterRupuSling --apply

    # Recover all auto-discovered Workshop mods at once.
    python recover_mod_from_workshop.py \\
        --modkit "..." --apply

    # Also delete the now-redundant Workshop cache (.zip/.pak/.sig).
    python recover_mod_from_workshop.py \\
        --modkit "..." --apply --remove-workshop-cache
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
from typing import Dict, List, Optional, Tuple


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
# Discovery
# ---------------------------------------------------------------------------


def find_workshop_zip(mod_folder: Path) -> Optional[Path]:
    """Find the <WORKSHOP_ID>.zip inside a Saved/Mods/<ModName>/ folder.

    Workshop IDs are long numeric strings; we accept any .zip whose stem
    is all-digits, preferring the largest if more than one matches.
    """
    candidates = [
        p for p in mod_folder.iterdir()
        if p.is_file() and p.suffix.lower() == ".zip" and p.stem.isdigit()
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0]


def discover_mods(saved_mods_root: Path) -> List[Tuple[str, Path, Path, Path]]:
    """Return a list of (mod_name, mod_folder, modinfo_path, zip_path).

    Includes only folders that have both a modinfo.json and a Workshop zip.
    """
    out: List[Tuple[str, Path, Path, Path]] = []
    if not saved_mods_root.is_dir():
        return out
    for entry in sorted(saved_mods_root.iterdir()):
        if not entry.is_dir():
            continue
        mi = entry / "modinfo.json"
        if not mi.is_file():
            continue
        zp = find_workshop_zip(entry)
        if zp is None:
            continue
        out.append((entry.name, entry, mi, zp))
    return out


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


def plan_extractions(zip_path: Path, content_root: Path) \
        -> Tuple[List[Tuple[str, Path]], List[str]]:
    """Build (zip_entry_name -> destination_path) for each file in the zip.

    Workshop zips put files at "Content/<rest>"; we extract relative to
    Game/Content/, so "Content/Mods/Foo/Bar.uasset" lands at
    Game/Content/Mods/Foo/Bar.uasset (no path manipulation needed beyond
    stripping the leading "Content/").

    Anything not under Content/ is rejected; anything attempting path
    traversal via '..' or absolute paths is rejected.
    """
    plans: List[Tuple[str, Path]] = []
    warnings: List[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            if not name.startswith("Content/"):
                warnings.append(f"zip entry not under 'Content/': {name!r} (skipped)")
                continue
            rel = name[len("Content/"):]
            if ".." in Path(rel).parts or Path(rel).is_absolute():
                warnings.append(f"REJECTED unsafe zip entry: {name!r}")
                continue
            dst = content_root / rel
            plans.append((name, dst))
    return plans, warnings


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def make_backup(modkit_root: Path, mod_name: str, saved_mod_folder: Path,
                content_mod_folder: Path) -> Path:
    """Zip up everything we might touch:
       - the v2 modinfo at Saved/Mods/<Mod>/modinfo.json (in case the
         Modkit ever rewrites it during edit)
       - the entire Saved/Mods/<Mod>/Assets/ tree (if any from a prior
         broken v3-target run that we're cleaning up)
       - any pre-existing Content/Mods/<Mod>/ files (if --force is
         overwriting a previous recovery)
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = modkit_root / f"{mod_name}_recovery_backup_{timestamp}.zip"
    log(f"  Creating backup: {backup_path}")
    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for source in (saved_mod_folder / "modinfo.json",):
            if source.is_file():
                zf.write(source, source.relative_to(modkit_root))
        for tree in (saved_mod_folder / "Assets", content_mod_folder):
            if tree.is_dir():
                for root, _dirs, files in os.walk(tree):
                    for name in files:
                        full = Path(root) / name
                        zf.write(full, full.relative_to(modkit_root))
    return backup_path


def extract_plans(zip_path: Path, plans: List[Tuple[str, Path]]) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        for entry, dst in plans:
            dst.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(entry) as src, dst.open("wb") as out:
                shutil.copyfileobj(src, out)


def remove_workshop_cache(saved_mod_folder: Path) -> List[Path]:
    """Delete .zip/.pak/.sig files whose stems are numeric (Workshop IDs)."""
    removed = []
    for p in saved_mod_folder.iterdir():
        if not p.is_file():
            continue
        if p.stem.isdigit() and p.suffix.lower() in (".zip", ".pak", ".sig"):
            p.unlink()
            removed.append(p)
    return removed


# ---------------------------------------------------------------------------
# Per-mod processing
# ---------------------------------------------------------------------------


def process_mod(
    mod_name: str,
    saved_mod_folder: Path,
    saved_manifest: Path,
    zip_path: Path,
    modkit_root: Path,
    content_root: Path,
    apply: bool,
    force: bool,
    remove_cache: bool,
) -> bool:
    section(f"[{mod_name}]")
    log(f"  Saved folder:    {saved_mod_folder.relative_to(modkit_root)}")
    log(f"  Workshop zip:    {zip_path.name} ({zip_path.stat().st_size:,} bytes)")
    log(f"  v2 modinfo.json: {saved_manifest.relative_to(modkit_root)}")

    # Load the v2 manifest
    try:
        with saved_manifest.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        err(f"  modinfo.json is not valid JSON: {e}")
        return False
    except OSError as e:
        err(f"  could not read modinfo.json: {e}")
        return False

    version = manifest.get("modKitVersion")
    if version != 2:
        err(f"  unexpected modKitVersion {version!r} (expected 2). "
            "If an earlier broken recovery left a v3 manifest here, restore "
            "the v2 one from the backup zip - see the porting guide's "
            "'Recovery if something looks wrong' section.")
        return False

    declared_folder = manifest.get("folderName")
    if declared_folder and declared_folder != mod_name:
        log(f"  WARNING: manifest folderName={declared_folder!r} differs from "
            f"folder name {mod_name!r}; using folder name.")

    content_mod_folder = content_root / "Mods" / mod_name
    if content_mod_folder.exists() and not force:
        err(f"  Content/Mods/{mod_name}/ already exists "
            f"({content_mod_folder.relative_to(modkit_root)}).")
        log(f"         Refusing to overwrite. Re-run with --force to override.")
        return False

    saved_assets = saved_mod_folder / "Assets"
    if saved_assets.exists() and not force:
        err(f"  Saved/Mods/{mod_name}/Assets/ exists - probably from an "
            "earlier broken v3-target migration attempt. Re-run with --force "
            "to remove it.")
        return False

    # Plan extractions
    try:
        plans, warnings = plan_extractions(zip_path, content_root)
    except (zipfile.BadZipFile, OSError) as e:
        err(f"  could not read zip: {e}")
        return False

    log(f"\n  Plan: extract {len(plans)} file(s) into Game\\Content\\")
    for entry, dst in plans[:8]:
        log(f"    {entry}\n      -> {dst.relative_to(modkit_root)}")
    if len(plans) > 8:
        log(f"    ... and {len(plans) - 8} more")

    log(f"\n  v2 modinfo.json STAYS at {saved_manifest.relative_to(modkit_root)} "
        "(Modkit's mod-selection screen scans there).")
    if saved_assets.exists():
        log(f"  Existing Saved/Mods/{mod_name}/Assets/ will be removed "
            "(broken state from a prior run).")
    if remove_cache:
        log(f"  Workshop cache files (.zip/.pak/.sig) will be removed after "
            "successful extraction.")

    if warnings:
        log(f"\n  Warnings ({len(warnings)}):")
        for w in warnings:
            log(f"    - {w}")

    if not apply:
        log("\n  [dry run - no changes made]")
        return True

    # --- Apply ---
    log("\n  Applying...")
    backup_path = make_backup(modkit_root, mod_name, saved_mod_folder,
                              content_mod_folder)

    # If --force overwriting an existing Content/Mods/<Mod>/, clear it first.
    if force and content_mod_folder.exists():
        shutil.rmtree(content_mod_folder)

    try:
        extract_plans(zip_path, plans)
    except (zipfile.BadZipFile, OSError) as e:
        err(f"  extraction failed: {e}")
        log(f"  Backup remains at {backup_path}.")
        return False

    # Verify every extracted file is on disk with the right size BEFORE we
    # touch the leftover Saved/Mods/<Mod>/Assets/. If verification fails the
    # user still has the original Saved/Mods/<Mod>/ state (and the backup).
    bad = []
    with zipfile.ZipFile(zip_path) as zf:
        for entry, dst in plans:
            expected = zf.getinfo(entry).file_size
            if not dst.is_file():
                bad.append(f"missing: {dst}")
            elif dst.stat().st_size != expected:
                bad.append(f"size mismatch ({dst.stat().st_size} != {expected}): {dst}")
    if bad:
        err(f"  post-extraction verification failed:")
        for b in bad:
            err(f"    {b}")
        log(f"  Saved/Mods/{mod_name}/ left untouched. Backup at {backup_path}.")
        return False

    # Now safe to clean up any leftover Saved/Mods/<Mod>/Assets/ from a prior
    # broken run. The Saved/Mods/<Mod>/modinfo.json STAYS - that's what the
    # Modkit reads.
    if saved_assets.exists():
        shutil.rmtree(saved_assets)

    removed = []
    if remove_cache:
        removed = remove_workshop_cache(saved_mod_folder)

    log(f"  Backup:    {backup_path}")
    log(f"  Extracted: {len(plans)} file(s) into Game\\Content\\")
    log(f"  Manifest:  v2 left in place at Saved/Mods/{mod_name}/modinfo.json")
    if saved_assets.exists() is False and (saved_mod_folder / "Assets").exists() is False:
        # Re-check after potential cleanup
        pass
    log(f"  Cleaned:   leftover Assets/ (if any)")
    if removed:
        log(f"  Removed:   {len(removed)} Workshop cache file(s)")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=("Recover Last Oasis mods from Steam Workshop downloads "
                     "(zips cached under Game/Saved/Mods/<Mod>/) into the "
                     "v2 source layout: assets at Game/Content/Mods/<Mod>/, "
                     "v2 manifest left in place at Saved/Mods/<Mod>/."),
    )
    parser.add_argument("--modkit", required=True, type=Path,
                        help="Path to the Modkit install root "
                             "(folder containing 'Game/').")
    parser.add_argument("--mod",
                        help="Name of a single mod folder under Saved/Mods/. "
                             "If omitted, processes every recoverable mod.")
    parser.add_argument("--apply", action="store_true",
                        help="Actually perform the recovery. Default is dry-run.")
    parser.add_argument("--force", action="store_true",
                        help="Allow overwriting an existing Content/Mods/<Mod>/ "
                             "or removing a leftover Saved/Mods/<Mod>/Assets/.")
    parser.add_argument("--remove-workshop-cache", action="store_true",
                        help="After extraction, delete the .zip/.pak/.sig "
                             "Workshop cache files in Saved/Mods/<Mod>/.")
    args = parser.parse_args(argv)

    modkit_root: Path = args.modkit.resolve()
    if not modkit_root.is_dir():
        err(f"--modkit path does not exist: {modkit_root}")
        return 2

    game_root = modkit_root / "Game"
    if not game_root.is_dir():
        err(f"Game/ not found under {modkit_root}")
        return 2

    content_root = game_root / "Content"
    saved_mods = game_root / "Saved" / "Mods"
    if not saved_mods.is_dir():
        err(f"Game/Saved/Mods/ not found under {modkit_root}")
        return 2

    section("Inputs")
    log(f"Modkit root:         {modkit_root}")
    log(f"Saved/Mods/ folder:  {saved_mods}")
    log(f"Content target:      {content_root}/Mods/<Mod>/")
    log(f"Mode:                {'APPLY' if args.apply else 'dry-run'}"
        + (" (force)" if args.force else "")
        + (" (remove-cache)" if args.remove_workshop_cache else ""))

    # Discovery
    if args.mod:
        single = saved_mods / args.mod
        if not single.is_dir():
            err(f"--mod folder does not exist: {single}")
            return 2
        mi = single / "modinfo.json"
        if not mi.is_file():
            err(f"--mod folder has no modinfo.json: {mi}")
            return 2
        zp = find_workshop_zip(single)
        if zp is None:
            err(f"--mod folder has no <ID>.zip: {single}")
            return 2
        candidates = [(args.mod, single, mi, zp)]
    else:
        candidates = discover_mods(saved_mods)

    section(f"Discovered {len(candidates)} mod(s)")
    if not candidates:
        log("(nothing to do - no folders have both modinfo.json and a numeric .zip)")
        return 0
    for name, _folder, _mi, zp in candidates:
        log(f"  - {name}  (zip: {zp.name})")

    # Process each
    successes = 0
    skips = 0
    for name, folder, mi, zp in candidates:
        ok = process_mod(
            name, folder, mi, zp, modkit_root, content_root,
            apply=args.apply, force=args.force,
            remove_cache=args.remove_workshop_cache,
        )
        if ok:
            successes += 1
        else:
            skips += 1

    section("Summary")
    log(f"  Processed: {successes}")
    log(f"  Skipped:   {skips}")
    if not args.apply:
        log("\n  This was a dry run. Re-run with --apply to perform recovery.")
    else:
        log("\n  Next steps for each recovered mod:")
        log("    1. Launch the Modkit. Each mod should appear in the selection")
        log("       screen (the v2 modinfo at Saved/Mods/<Mod>/ is what gets")
        log("       discovered).")
        log("    2. Select a mod. The Modkit boots scoped to it and loads")
        log("       the assets from Content/Mods/<Mod>/.")
        log("    3. Edit as needed.")
        log("    4. Mod Manager -> Save Mod. The Modkit handles the v3")
        log("       migration internally and properly populates the asset-list")
        log("       fields - so the assets stay flagged and survive future boots.")
        log("    5. Cook & test against a local modded server before re-uploading.")
        log("\n  If you need to undo, the backup zips are at:")
        log(f"    {modkit_root}/<ModName>_recovery_backup_<timestamp>.zip")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
