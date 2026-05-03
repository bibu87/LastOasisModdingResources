#!/usr/bin/env python3
"""
mod_workflow.py
===============

Interactive wizard that walks a Last Oasis mod from any starting state
through Cook + Upload to Steam Workshop.

This is the canonical migration tool. The recipe below was derived
empirically across three real mods after several earlier approaches
failed. See docs/modkit-guides/porting-a-mod-from-old-modkit.md for
the failure-mode taxonomy that motivates each step.

The recipe (proved working empirically on three real mods)
--------------------------------------------------------

The new Modkit's mod-load + cook + upload pipeline has several traps
that cooperate to wipe a migrated mod's source assets. The recipe
below sidesteps all of them:

  1. Source files go into BOTH locations:
       - Content/Mods/<Mod>/<files>          (for editor visibility)
       - Saved/Mods/<Mod>/Assets/Mods/<Mod>/<files>   (for cook + upload)
     Stock-game overrides go into BOTH:
       - Content/Mist/<rel>
       - Saved/Mods/<Mod>/Assets/Mist/<rel>

  2. Manifest at Saved/Mods/<Mod>/modinfo.json is **fully patched**:
       - steamId, author, active: true
       - assetsToCook (path -> UE type map)
       - createdAssets (mod-owned paths only)
       - modifiedAssets / referencingAssets (all paths)
     (Save Mod produces a *blank* v3 manifest from migrated mods,
     losing all of these. We have to write them ourselves.)

  3. Thumbnail at Saved/Mods/<Mod>/thumbnail.png = copy of whatever
     file the v2 manifest's `thumbnailPath` points at (commonly
     `mod-image.png` but the field can name any image file).

  4. **All of the above is `chmod -w` (read-only) on disk.** Without
     this, the Modkit's load + Cook overwrite the manifest and wipe
     the source. With it, the Modkit's writes silently fail and the
     state we want survives.

  5. Other mods' folders under Content/Mods/ are removed *if* they
     are byte-identical to their Saved-side mirrors (avoids ghost
     entries showing up in this mod's Content Browser).

  6. **In the Modkit**: clean restart -> select mod -> Cook
     (skip Save Mod, it would only try to overwrite our locked manifest).

  7. The Modkit's Cook produces Pak/<ModName>.pak but does NOT stage
     anything to Upload/. The wizard builds Upload/ manually:
       - Upload/<steamId>.pak  (copy of Pak/<ModName>.pak)
       - Upload/<steamId>.sig  (copy of Pak/<ModName>.sig)
       - Upload/<steamId>.zip  (built from Content/Mods/<Mod>/ +
                                Mist overrides, mirroring the original
                                Workshop zip's layout)
       - Upload/modinfo.json   (copy of Saved/.../modinfo.json)

  8. **In the Modkit**: Upload to Workshop -> publishes to the
     existing Workshop item identified by steamId.

  9. After all cook+upload work is done, the wizard offers to
     unlock the read-only files so you can edit later.

Reference: docs/modkit-guides/porting-a-mod-from-old-modkit.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import time
import zipfile
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


def section(title: str) -> None:
    bar = "=" * 70
    print(f"\n{bar}\n{title}\n{bar}")


def info(msg: str) -> None: print(f"  {msg}")
def ok(msg: str) -> None: print(f"  [OK] {msg}")
def warn(msg: str) -> None: print(f"  [WARN] {msg}")
def err(msg: str) -> None: print(f"  [ERROR] {msg}", file=sys.stderr)


def confirm(prompt: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    while True:
        ans = input(f"\n>> {prompt} {suffix} ").strip().lower()
        if ans == "":
            return default_yes
        if ans in ("y", "yes"): return True
        if ans in ("n", "no"): return False
        print("    please answer y or n")


def wait(prompt: str) -> None:
    print()
    input(f">> {prompt}\n   Press Enter when done... ")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


@dataclass
class State:
    modkit_root: Path
    mod_name: str

    # Resolved paths
    game_root: Path = field(init=False)
    content_root: Path = field(init=False)
    saved_mod_folder: Path = field(init=False)
    saved_manifest: Path = field(init=False)
    saved_assets_root: Path = field(init=False)
    content_mod_folder: Path = field(init=False)

    # Discovered
    workshop_zip: Optional[Path] = None
    manifest: Optional[Dict] = None
    manifest_kit_version: Optional[int] = None
    assets_to_cook_count: int = 0
    asset_hashes_count: int = 0
    saved_assets_count: int = 0
    content_assets_count: int = 0

    def __post_init__(self):
        self.game_root = self.modkit_root / "Game"
        self.content_root = self.game_root / "Content"
        self.saved_mod_folder = self.game_root / "Saved" / "Mods" / self.mod_name
        self.saved_manifest = self.saved_mod_folder / "modinfo.json"
        self.saved_assets_root = self.saved_mod_folder / "Assets"
        self.content_mod_folder = self.content_root / "Mods" / self.mod_name


def diagnose(s: State) -> None:
    # Workshop zip (numeric stem, in Saved/Mods/<Mod>/)
    s.workshop_zip = None
    if s.saved_mod_folder.is_dir():
        for p in s.saved_mod_folder.iterdir():
            if p.is_file() and p.suffix.lower() == ".zip" and p.stem.isdigit():
                if s.workshop_zip is None or p.stat().st_size > s.workshop_zip.stat().st_size:
                    s.workshop_zip = p

    # Manifest
    s.manifest = None
    s.manifest_kit_version = None
    s.assets_to_cook_count = 0
    s.asset_hashes_count = 0
    if s.saved_manifest.is_file():
        try:
            s.manifest = json.loads(s.saved_manifest.read_text(encoding="utf-8"))
            s.manifest_kit_version = s.manifest.get("modKitVersion")
            s.assets_to_cook_count = len(s.manifest.get("assetsToCook", {}))
            s.asset_hashes_count = len(s.manifest.get("assetHashes", {}))
        except (json.JSONDecodeError, OSError):
            pass

    # Asset counts on disk
    s.saved_assets_count = sum(
        1 for p in s.saved_assets_root.rglob("*") if p.is_file()
    ) if s.saved_assets_root.is_dir() else 0
    s.content_assets_count = sum(
        1 for p in s.content_mod_folder.rglob("*")
        if p.is_file() and p.name != "modinfo.json"
    ) if s.content_mod_folder.is_dir() else 0


def print_diagnosis(s: State) -> None:
    section(f"Diagnosis: {s.mod_name}")
    info(f"Modkit root:                       {s.modkit_root}")
    info(f"Workshop zip present:              "
         f"{s.workshop_zip.name if s.workshop_zip else 'no'}")
    info(f"Saved/Mods/{s.mod_name}/modinfo.json:  "
         f"{'yes (v' + str(s.manifest_kit_version) + ')' if s.manifest else 'no'}")
    info(f"  assetsToCook entries:            {s.assets_to_cook_count}")
    info(f"  assetHashes entries:             {s.asset_hashes_count}")
    info(f"Source files in Content/Mods/:     {s.content_assets_count}")
    info(f"Source files in Saved/.../Assets/: {s.saved_assets_count}")


CLASS_DESCRIPTIONS = {
    "WORKSHOP_CACHED":
        "Workshop cache only - v2 manifest + zip in Saved/Mods/, no extracted source. "
        "Wizard will extract zip into Content/Mods/<Mod>/ AND Saved/.../Assets/, "
        "patch the manifest, and lock everything read-only.",
    "PARTIAL_PREPPED":
        "Partial state from a prior wizard run. Will refresh staging "
        "(re-extract / re-mirror as needed) and re-lock.",
    "RECIPE_PREPPED":
        "Already prepped with the recipe. Skip prep, jump to Cook step.",
    "ALREADY_DONE":
        "Mod has a fully populated v3 manifest with assetHashes (like a "
        "modkit-authored mod). Skip prep, no migration needed.",
    "SOURCE_AT_SAVED_ROOT":
        "Alternate layout: source files (.uasset/.umap) live at "
        "Saved/Mods/<Mod>/<x>.uasset, not under Content/Mods/ or Assets/. "
        "Wizard will copy them into Content/Mods/<Mod>/ AND mirror to "
        "Saved/.../Assets/, patch the manifest, and lock read-only.",
    "UNKNOWN":
        "Could not classify - manual inspection needed.",
}


def classify(s: State) -> str:
    is_locked = s.saved_manifest.is_file() and not os.access(s.saved_manifest, os.W_OK)
    has_v3_with_data = (
        s.manifest_kit_version == 3
        and s.assets_to_cook_count > 0
    )
    if has_v3_with_data and s.asset_hashes_count > 0:
        return "ALREADY_DONE"
    if (has_v3_with_data and is_locked
            and s.saved_assets_count > 0 and s.content_assets_count > 0):
        return "RECIPE_PREPPED"
    if s.manifest_kit_version in (2, 3) and s.assets_to_cook_count > 0:
        if s.saved_assets_count or s.content_assets_count:
            return "PARTIAL_PREPPED"
        # Source not at standard locations - check the alternate layout
        # (some mods commit source at Saved/Mods/<Mod>/ root, e.g. via git).
        atc = (s.manifest or {}).get("assetsToCook") or {}
        if has_source_at_saved_root(s, atc):
            return "SOURCE_AT_SAVED_ROOT"
        if s.workshop_zip:
            return "WORKSHOP_CACHED"
    if s.manifest_kit_version in (2, 3) and s.workshop_zip:
        return "WORKSHOP_CACHED"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Helpers shared across phases
# ---------------------------------------------------------------------------


def file_sha1(p: Path) -> str:
    h = hashlib.sha1()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lock_path(p: Path) -> None:
    if p.is_file():
        p.chmod(stat.S_IREAD)


def unlock_path(p: Path) -> None:
    if p.is_file():
        p.chmod(stat.S_IWRITE | stat.S_IREAD)


def lock_tree(root: Path) -> int:
    n = 0
    if root.is_dir():
        for p in root.rglob("*"):
            if p.is_file():
                lock_path(p)
                n += 1
    return n


def unlock_tree(root: Path) -> int:
    n = 0
    if root.is_dir():
        for p in root.rglob("*"):
            if p.is_file():
                unlock_path(p)
                n += 1
    return n


# ---------------------------------------------------------------------------
# Phase: backup
# ---------------------------------------------------------------------------


def make_backup(s: State) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = s.modkit_root / f"{s.mod_name}_workflow_backup_{timestamp}.zip"
    info(f"Backing up to {backup_path.name}...")
    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for tree in (s.saved_mod_folder, s.content_mod_folder):
            if tree.is_dir():
                for root, _dirs, files in os.walk(tree):
                    for f in files:
                        full = Path(root) / f
                        zf.write(full, full.relative_to(s.modkit_root))
    ok(f"backup ready: {backup_path}")
    return backup_path


# ---------------------------------------------------------------------------
# Phase: cleanup other Content/Mods/ folders
# ---------------------------------------------------------------------------


def cleanup_other_content_mods(s: State) -> Tuple[List[str], List[str]]:
    """For every <other_mod> folder under Content/Mods/ (except this one):
       compare its files byte-for-byte to Saved/Mods/<other_mod>/Assets/Mods/<other_mod>/.
       If 100% identical, delete the Content/-side folder.
       Returns (deleted, kept_with_reason)."""
    deleted = []
    kept = []
    content_mods = s.content_root / "Mods"
    if not content_mods.is_dir():
        return deleted, kept

    for mod_dir in sorted(content_mods.iterdir()):
        if not mod_dir.is_dir():
            continue
        if mod_dir.name == s.mod_name:
            continue
        mirror = s.game_root / "Saved" / "Mods" / mod_dir.name / "Assets" / "Mods" / mod_dir.name
        if not mirror.is_dir():
            kept.append(f"{mod_dir.name} (no mirror at Saved/.../Assets/Mods/{mod_dir.name}/)")
            continue
        # Byte-compare
        content_files = {p.relative_to(mod_dir): p
                         for p in mod_dir.rglob("*") if p.is_file()}
        mirror_files = {p.relative_to(mirror): p
                        for p in mirror.rglob("*") if p.is_file()}
        only_in_content = [r for r in content_files if r not in mirror_files]
        differs = []
        for rel, src in content_files.items():
            dst = mirror_files.get(rel)
            if dst is None:
                continue
            if src.stat().st_size != dst.stat().st_size or file_sha1(src) != file_sha1(dst):
                differs.append(rel)
        if only_in_content or differs:
            kept.append(
                f"{mod_dir.name} (would lose {len(only_in_content)} unique + "
                f"{len(differs)} modified file(s))"
            )
            continue
        # Safe to delete
        unlock_tree(mod_dir)  # files may be read-only from prior wizard runs
        shutil.rmtree(mod_dir)
        deleted.append(mod_dir.name)
    return deleted, kept


# ---------------------------------------------------------------------------
# Phase: stage source assets at both locations
# ---------------------------------------------------------------------------


def get_v2_asset_paths(s: State) -> OrderedDict:
    """Return assetsToCook (path -> type) from the most authoritative source."""
    if s.manifest and s.assets_to_cook_count > 0:
        # Treat this as authoritative even if the manifest is already v3 -
        # if assetsToCook is non-empty, the path list is good.
        return OrderedDict(s.manifest.get("assetsToCook"))
    # Try recovery backups
    for pattern in (f"{s.mod_name}_recovery_backup_*.zip",
                    f"{s.mod_name}_workflow_backup_*.zip",
                    f"{s.mod_name}_v2_backup_*.zip",
                    f"{s.mod_name}_assetmove_backup_*.zip"):
        for backup in sorted(s.modkit_root.glob(pattern), reverse=True):
            try:
                with zipfile.ZipFile(backup) as zf:
                    for name in zf.namelist():
                        norm = name.replace("\\", "/")
                        if norm.endswith(f"Saved/Mods/{s.mod_name}/modinfo.json"):
                            data = json.loads(zf.read(name).decode("utf-8"))
                            assets = data.get("assetsToCook")
                            if assets:
                                return OrderedDict(assets)
            except Exception:
                continue
    raise RuntimeError(
        f"Could not find a valid assetsToCook list for {s.mod_name}. "
        "Looked at the current manifest and any *_backup_*.zip files at "
        "the Modkit root."
    )


def has_source_at_saved_root(s: State, assets_to_cook: OrderedDict) -> bool:
    """Return True if at least one /Game/Mods/<Mod>/<x> path in assetsToCook
    has its source file at Saved/Mods/<Mod>/<x>.{uasset,umap} - the
    'alternate layout' some mods use (source committed at the mod folder
    root, not under Content/Mods/ or Assets/)."""
    if not s.saved_mod_folder.is_dir():
        return False
    prefix = f"/Game/Mods/{s.mod_name}/"
    for vp in assets_to_cook.keys():
        if not vp.startswith(prefix):
            continue
        rel_no_ext = vp[len(prefix):]
        for ext in (".uasset", ".umap"):
            if (s.saved_mod_folder / (rel_no_ext + ext)).is_file():
                return True
    return False


def stage_source(s: State, assets_to_cook: OrderedDict) -> None:
    """Place source files at BOTH Content/Mods/<Mod>/<...> AND
    Saved/Mods/<Mod>/Assets/Mods/<Mod>/<...>. Handle Mist overrides too.

    Source priority (most-current first):
      1. Saved/.../Assets/Mods/<Mod>/  (prior cook prep)
      2. Content/Mods/<Mod>/           (standard v2 layout)
      3. Saved/Mods/<Mod>/<x>.uasset   (alternate layout: source at mod root)
      4. Workshop zip                  (original published bytes)
    """

    have_content = s.content_mod_folder.is_dir() and s.content_assets_count > 0
    mods_in_assets = s.saved_assets_root / "Mods" / s.mod_name
    have_assets = mods_in_assets.is_dir() and any(p.is_file() for p in mods_in_assets.rglob("*"))
    have_saved_root = (
        not have_content and not have_assets
        and has_source_at_saved_root(s, assets_to_cook)
    )

    if have_content:
        info(f"Using existing files at Content/Mods/{s.mod_name}/")
    elif have_assets:
        info(f"Restoring source from Saved/.../Assets/Mods/{s.mod_name}/ -> Content/Mods/{s.mod_name}/")
        unlock_tree(s.content_mod_folder)
        n = 0
        for src in mods_in_assets.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(mods_in_assets)
            dst = s.content_mod_folder / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                unlock_path(dst)
            shutil.copy2(str(src), str(dst))
            n += 1
        # Also restore Mist overrides from Assets/Mist/* -> Content/Mist/*
        mist_in_assets = s.saved_assets_root / "Mist"
        if mist_in_assets.is_dir():
            for src in mist_in_assets.rglob("*"):
                if not src.is_file():
                    continue
                rel = src.relative_to(mist_in_assets)
                dst = s.content_root / "Mist" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    unlock_path(dst)
                shutil.copy2(str(src), str(dst))
                n += 1
        ok(f"restored {n} files into Content/")
    elif have_saved_root:
        # Alternate layout: source files live at Saved/Mods/<Mod>/<x>.uasset
        # (some users keep their mod source in a git repo at the Saved-mod-folder
        # root rather than the standard Content/Mods/<Mod>/ location). Resolve
        # each /Game/Mods/<Mod>/<x> path in assetsToCook to its on-disk source
        # there, and copy to Content/Mods/<Mod>/<x>.uasset.
        info(f"Restoring source from Saved/Mods/{s.mod_name}/ root -> Content/Mods/{s.mod_name}/")
        unlock_tree(s.content_mod_folder)
        n = 0
        prefix = f"/Game/Mods/{s.mod_name}/"
        for vp in assets_to_cook.keys():
            if not vp.startswith(prefix):
                continue
            rel_no_ext = vp[len(prefix):]
            for ext in (".uasset", ".umap"):
                src = s.saved_mod_folder / (rel_no_ext + ext)
                if src.is_file():
                    dst = s.content_mod_folder / (rel_no_ext + ext)
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if dst.exists():
                        unlock_path(dst)
                    shutil.copy2(str(src), str(dst))
                    n += 1
                    break
            else:
                warn(f"asset not found at Saved/Mods/{s.mod_name}/ root: {vp}")
        # The thumbnail (if it lives at the saved-root) - copy too so write_thumbnail finds it.
        thumb_rel = (s.manifest or {}).get("thumbnailPath", "").lstrip("/").lstrip("\\")
        if thumb_rel:
            thumb_src = s.saved_mod_folder / thumb_rel
            if thumb_src.is_file():
                thumb_dst = s.content_mod_folder / thumb_rel
                thumb_dst.parent.mkdir(parents=True, exist_ok=True)
                if thumb_dst.exists():
                    unlock_path(thumb_dst)
                shutil.copy2(str(thumb_src), str(thumb_dst))
                n += 1
        ok(f"restored {n} files into Content/Mods/{s.mod_name}/")
    elif s.workshop_zip is not None:
        info(f"Extracting {s.workshop_zip.name} into Content/...")
        unlock_tree(s.content_root / "Mist")
        unlock_tree(s.content_mod_folder)
        with zipfile.ZipFile(s.workshop_zip) as zf:
            for entry in zf.infolist():
                if entry.filename.endswith("/"):
                    continue
                if not entry.filename.startswith("Content/"):
                    continue
                if ".." in Path(entry.filename).parts:
                    continue
                dst = s.game_root / entry.filename  # Game/Content/<rest>
                if dst.exists():
                    unlock_path(dst)
                dst.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(entry) as src, dst.open("wb") as out:
                    shutil.copyfileobj(src, out)
    else:
        raise RuntimeError(
            f"No source found for {s.mod_name}. Looked at: "
            f"Content/Mods/{s.mod_name}/, "
            f"Saved/Mods/{s.mod_name}/Assets/Mods/{s.mod_name}/, "
            f"Saved/Mods/{s.mod_name}/<x>.uasset (alternate root layout), "
            f"and the Workshop zip - all empty/missing."
        )

    # Re-diagnose after the source restore so subsequent steps see fresh counts
    diagnose(s)

    # Now mirror Content/Mods/<Mod>/<files> -> Saved/.../Assets/Mods/<Mod>/<files>
    v3_mods_dst = s.saved_assets_root / "Mods" / s.mod_name
    if v3_mods_dst.exists():
        unlock_tree(v3_mods_dst)
    v3_mods_dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in s.content_mod_folder.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(s.content_mod_folder)
        dst = v3_mods_dst / rel
        if dst.exists():
            unlock_path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        n += 1
    ok(f"mirrored {n} mod-folder files into Saved/.../Assets/Mods/{s.mod_name}/")

    # Mist overrides: mirror Content/Mist/<rel> -> Saved/.../Assets/Mist/<rel>
    # for any /Game/Mist/... path in assetsToCook.
    mist_n = 0
    for vp in assets_to_cook.keys():
        if not vp.startswith("/Game/Mist/"):
            continue
        rel = vp[len("/Game/"):]  # Mist/<rest>
        for ext in (".uasset", ".umap"):
            content_path = s.content_root / Path(rel + ext)
            if content_path.is_file():
                v3_path = s.saved_assets_root / Path(rel + ext)
                if v3_path.exists():
                    unlock_path(v3_path)
                v3_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(content_path), str(v3_path))
                mist_n += 1
                break
        else:
            warn(f"Mist override missing on disk: {vp}")
    if mist_n:
        ok(f"mirrored {mist_n} Mist override file(s) into Saved/.../Assets/Mist/")


# ---------------------------------------------------------------------------
# Phase: patch v3 manifest
# ---------------------------------------------------------------------------


def patch_manifest(s: State, assets_to_cook: OrderedDict, author: str) -> None:
    # Pull defaults from existing manifest if present
    existing = s.manifest or {}
    # If existing has v2 'iD' use that as steamId; v3 'steamId' wins if non-zero
    steam_id = existing.get("steamId") or existing.get("iD") or 0
    if not steam_id:
        # Fall back to the workshop zip stem
        if s.workshop_zip:
            steam_id = int(s.workshop_zip.stem)
        else:
            raise RuntimeError(
                f"Could not determine steamId for {s.mod_name}. "
                "Manifest has neither 'iD' nor 'steamId', and no Workshop zip."
            )

    all_paths = list(assets_to_cook.keys())
    created = [p for p in all_paths if p.startswith(f"/Game/Mods/{s.mod_name}/")]

    # Preserve thumbnailPath from the existing manifest, OR look it up
    # from a backup (so re-runs of the wizard don't lose the value when
    # patching successive times). The Modkit's v3 spec doesn't require
    # this field but ignores unknown fields, so it's safe to keep.
    thumbnail_path = existing.get("thumbnailPath") or find_thumbnail_path(s)

    fields = [
        ("title", existing.get("title", s.mod_name)),
        ("description", existing.get("description", "")),
        ("author", existing.get("author") or author),
        ("steamId", int(steam_id)),
        ("tag", existing.get("tag", "General")),
        ("creator", existing.get("creator", 0)),
        ("active", True),
        ("folderName", s.mod_name),
        ("modDependencies", existing.get("modDependencies", [])),
    ]
    if thumbnail_path:
        fields.append(("thumbnailPath", thumbnail_path))
    fields.append(("assetsToCook", assets_to_cook))
    manifest = OrderedDict(fields + [
        ("createdAssets", created),
        ("modifiedAssets", all_paths),
        ("deletedAssets", []),
        ("referencingAssets", all_paths),
        ("referencingAssetsToNotCook", []),
        ("assetTree", []),
        ("assetHashes", {}),
        ("modKitVersion", 3),
        ("enforceSameMods", existing.get("enforceSameMods", "WarningOnly")),
        ("modHash", existing.get("modHash", 0)),
        ("version", existing.get("version", {"Main": 1, "Major": 0, "Minor": 0, "Micro": 0})),
    ])

    if s.saved_manifest.exists():
        unlock_path(s.saved_manifest)
    s.saved_mod_folder.mkdir(parents=True, exist_ok=True)
    s.saved_manifest.write_text(json.dumps(manifest, indent="\t") + "\n", encoding="utf-8")
    ok(f"manifest patched: steamId={steam_id}, "
       f"{len(assets_to_cook)} assetsToCook, {len(created)} createdAssets")


# ---------------------------------------------------------------------------
# Phase: thumbnail
# ---------------------------------------------------------------------------


def find_thumbnail_path(s: State) -> Optional[str]:
    """Return the v2 manifest's `thumbnailPath` value (e.g. '/mod-image.png',
    '/modpicture.jpg'). Looks first at the current on-disk manifest, then
    falls back to any *_backup_*.zip at the modkit root."""
    if s.manifest and s.manifest.get("thumbnailPath"):
        return s.manifest["thumbnailPath"]
    for pattern in (f"{s.mod_name}_workflow_backup_*.zip",
                    f"{s.mod_name}_recovery_backup_*.zip",
                    f"{s.mod_name}_v2_backup_*.zip",
                    f"{s.mod_name}_assetmove_backup_*.zip"):
        for backup in sorted(s.modkit_root.glob(pattern), reverse=True):
            try:
                with zipfile.ZipFile(backup) as zf:
                    for name in zf.namelist():
                        norm = name.replace("\\", "/")
                        if norm.endswith(f"Saved/Mods/{s.mod_name}/modinfo.json"):
                            data = json.loads(zf.read(name).decode("utf-8"))
                            tp = data.get("thumbnailPath")
                            if tp:
                                return tp
            except Exception:
                continue
    return None


def write_thumbnail(s: State) -> bool:
    """Copy the mod's thumbnail image to Saved/Mods/<Mod>/thumbnail.png.

    Source filename comes from the v2 manifest's `thumbnailPath` field
    (the v3 manifest doesn't have this field, so we recover it from a
    backup zip if needed). The Workshop UI uses thumbnail.png as the
    item's actual thumbnail.
    """
    raw = find_thumbnail_path(s)
    if not raw:
        warn(f"no thumbnailPath in manifest - skipping thumbnail "
             "(was the v2 manifest lost?)")
        return False
    # thumbnailPath is typically "/mod-image.png" - relative to the mod's
    # Content/Mods/<Mod>/ root. Strip the leading slash.
    rel = raw.lstrip("/").lstrip("\\")
    # Look at multiple candidate locations - mods using the alternate
    # root layout keep the thumbnail at Saved/Mods/<Mod>/<file>.
    candidates = [
        s.content_mod_folder / rel,
        s.saved_mod_folder / rel,
        s.saved_assets_root / "Mods" / s.mod_name / rel,
    ]
    src = next((p for p in candidates if p.is_file()), None)
    if src is None:
        warn(f"thumbnail file not found on disk (thumbnailPath={raw!r}). "
             f"Looked at: {[str(p) for p in candidates]}")
        return False
    dst = s.saved_mod_folder / "thumbnail.png"
    if dst.exists():
        unlock_path(dst)
    shutil.copy2(str(src), str(dst))
    ok(f"thumbnail.png written from {src.relative_to(s.modkit_root)} "
       f"({dst.stat().st_size:,} bytes)")
    return True


# ---------------------------------------------------------------------------
# Phase: lock everything read-only
# ---------------------------------------------------------------------------


def lock_recipe_state(s: State, assets_to_cook: OrderedDict) -> int:
    locked = 0
    if s.saved_manifest.is_file():
        lock_path(s.saved_manifest)
        locked += 1
    locked += lock_tree(s.content_mod_folder)
    locked += lock_tree(s.saved_assets_root)
    # Lock Mist overrides at the Content side too
    for vp in assets_to_cook.keys():
        if not vp.startswith("/Game/Mist/"):
            continue
        rel = vp[len("/Game/"):]
        for ext in (".uasset", ".umap"):
            p = s.content_root / Path(rel + ext)
            if p.is_file():
                lock_path(p)
                locked += 1
                break
    thumbnail = s.saved_mod_folder / "thumbnail.png"
    if thumbnail.is_file():
        lock_path(thumbnail)
        locked += 1
    return locked


# ---------------------------------------------------------------------------
# Phase: verify cook & build Upload payload
# ---------------------------------------------------------------------------


def verify_cook(s: State) -> Tuple[bool, Optional[Path]]:
    pak_dir = s.saved_mod_folder / "Pak"
    pak = pak_dir / f"{s.mod_name}.pak"
    sig = pak_dir / f"{s.mod_name}.sig"
    if not pak.is_file() or not sig.is_file():
        err(f"cook output missing: expected {pak.name} + {sig.name} in Pak/")
        return False, None
    size = pak.stat().st_size
    if size < 1024:
        warn(f"{pak.name} is suspiciously small ({size} bytes) - cook may have shipped nothing")
        return False, pak
    ok(f"{pak.name} present ({size:,} bytes)")
    return True, pak


def build_upload_payload(s: State, assets_to_cook: OrderedDict) -> None:
    upload_dir = s.saved_mod_folder / "Upload"
    upload_dir.mkdir(exist_ok=True)
    pak_dir = s.saved_mod_folder / "Pak"
    steam_id = str(s.manifest["steamId"])

    # 1. ID-prefixed pak + sig
    for ext in ("pak", "sig"):
        src = pak_dir / f"{s.mod_name}.{ext}"
        dst = upload_dir / f"{steam_id}.{ext}"
        if dst.exists(): unlock_path(dst)
        shutil.copy2(str(src), str(dst))
    ok(f"{steam_id}.pak ({(upload_dir / f'{steam_id}.pak').stat().st_size:,} bytes) + .sig staged")

    # 2. modinfo.json copy
    dst_mi = upload_dir / "modinfo.json"
    if dst_mi.exists(): unlock_path(dst_mi)
    shutil.copy2(str(s.saved_manifest), str(dst_mi))
    unlock_path(dst_mi)
    ok("modinfo.json copied")

    # 3. Source zip - layout matches the original Workshop zip
    zip_path = upload_dir / f"{steam_id}.zip"
    if zip_path.exists(): unlock_path(zip_path)
    n = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Mod folder content
        for src in sorted(s.content_mod_folder.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(s.game_root)
            zf.write(src, str(rel).replace("\\", "/"))
            n += 1
        # Mist overrides
        for vp in assets_to_cook.keys():
            if not vp.startswith("/Game/Mist/"):
                continue
            rel = vp[len("/Game/"):]
            for ext in (".uasset", ".umap"):
                src = s.content_root / Path(rel + ext)
                if src.is_file():
                    arc = "Content/" + rel + ext
                    zf.write(src, arc.replace("\\", "/"))
                    n += 1
                    break
    ok(f"{steam_id}.zip built with {n} files ({zip_path.stat().st_size:,} bytes)")


# ---------------------------------------------------------------------------
# Phase: unlock
# ---------------------------------------------------------------------------


def unlock_all(s: State, assets_to_cook: OrderedDict) -> int:
    n = 0
    if s.saved_manifest.is_file():
        unlock_path(s.saved_manifest); n += 1
    n += unlock_tree(s.content_mod_folder)
    n += unlock_tree(s.saved_assets_root)
    for vp in assets_to_cook.keys():
        if not vp.startswith("/Game/Mist/"):
            continue
        rel = vp[len("/Game/"):]
        for ext in (".uasset", ".umap"):
            p = s.content_root / Path(rel + ext)
            if p.is_file():
                unlock_path(p); n += 1
                break
    thumbnail = s.saved_mod_folder / "thumbnail.png"
    if thumbnail.is_file():
        unlock_path(thumbnail); n += 1
    return n


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=("Interactive wizard that walks a Last Oasis mod from "
                     "any starting state through Cook + Upload to Steam Workshop.")
    )
    parser.add_argument("--modkit", required=True, type=Path,
                        help="Modkit install root (folder containing 'Game/').")
    parser.add_argument("--mod", required=True,
                        help="Mod folder name.")
    parser.add_argument("--author", default="",
                        help="Author name (used only if not already set in the manifest).")
    args = parser.parse_args(argv)

    modkit_root = args.modkit.resolve()
    if not (modkit_root / "Game").is_dir():
        err(f"--modkit doesn't look like a Modkit install: {modkit_root}")
        return 2

    s = State(modkit_root=modkit_root, mod_name=args.mod)
    diagnose(s)
    print_diagnosis(s)
    classification = classify(s)

    section(f"Plan: {classification}")
    info(CLASS_DESCRIPTIONS.get(classification, "(no description)"))

    if classification == "UNKNOWN":
        return 2

    if classification == "ALREADY_DONE":
        info("Nothing to do here. Use the Modkit's normal Cook + Upload flow.")
        return 0

    if not confirm("Proceed?"):
        info("Aborted.")
        return 0

    # ============================================================
    # PHASE A: prep (script-only, destructive — needs Modkit closed)
    # ============================================================

    info("\nMAKE SURE THE MODKIT IS CLOSED before continuing - we'll be editing files.")
    if not confirm("Modkit is closed?"):
        return 0

    section("Phase A: prep")
    make_backup(s)

    # Authoritative asset list
    try:
        assets_to_cook = get_v2_asset_paths(s)
    except RuntimeError as e:
        err(str(e))
        return 1

    # Cleanup other Content/Mods/ folders
    info("\nChecking other mods in Content/Mods/...")
    deleted, kept = cleanup_other_content_mods(s)
    if deleted:
        ok(f"deleted {len(deleted)} verified-safe folder(s): {', '.join(deleted)}")
    for note in kept:
        warn(f"kept: {note}")

    # Stage, patch, thumbnail, lock
    info("\nStaging source...")
    stage_source(s, assets_to_cook)

    info("\nPatching manifest...")
    patch_manifest(s, assets_to_cook, args.author)

    info("\nWriting thumbnail...")
    write_thumbnail(s)

    info("\nLocking everything read-only...")
    locked = lock_recipe_state(s, assets_to_cook)
    ok(f"locked {locked} file(s)")

    # Re-diagnose
    diagnose(s)
    info(f"\nReady. Saved/.../Assets/ now has {s.saved_assets_count} files; "
         f"manifest is v3 with {s.assets_to_cook_count} assetsToCook.")

    # ============================================================
    # PHASE B: User does Cook in the Modkit
    # ============================================================

    section("Phase B: Cook in the Modkit")
    print(f"""
What to do in the Modkit:

  1. Launch the Modkit (Epic Launcher / RunDevKit.bat).
  2. Select '{s.mod_name}' in the mod-selection screen.
  3. If the Mod Manager UI is empty or shows assets from other mods:
     close the Modkit and relaunch (the asset registry caches stale state
     across runs - a clean restart usually fixes it).
  4. Verify Mod Manager -> Assets to Cook lists all {s.assets_to_cook_count}
     entries from the patched manifest.
  5. Mod Manager -> *Cook and Package Mod*.
     DO NOT click "Save Mod" - it would try to overwrite the locked manifest.
  6. Wait for the cook batch script to finish. *** DO NOT close that
     batch window mid-cook *** or you'll lose the cook cache and the next
     cook will take hours.
  7. Close the Modkit.

The cook should produce Pak/{s.mod_name}.pak (kilobytes to megabytes,
NOT 238 bytes - that would mean an empty cook).
""")
    wait("Done with Cook?")

    section("Verifying cook output")
    success, pak = verify_cook(s)
    if not success:
        return 1

    # ============================================================
    # PHASE C: build Upload payload (script-only)
    # ============================================================

    section("Phase C: build Upload/ payload")
    build_upload_payload(s, assets_to_cook)

    upload_dir = s.saved_mod_folder / "Upload"
    print()
    info("Upload/ now contains:")
    for p in sorted(upload_dir.iterdir()):
        info(f"  {p.stat().st_size:>10,}  {p.name}")

    # ============================================================
    # PHASE D: User uploads in the Modkit
    # ============================================================

    section("Phase D: Upload to Workshop")
    print(f"""
What to do in the Modkit:

  1. Launch the Modkit (or keep it open from before - either is fine).
  2. Select '{s.mod_name}'.
  3. Mod Manager -> *Upload to Workshop*.
  4. The upload pushes to Workshop item {s.manifest['steamId']}.
  5. Verify on the Workshop page (steamcommunity.com/sharedfiles/...)
     that the "Updated" timestamp is current.
""")
    if not confirm("Upload finished?"):
        info("Stopping here. The Upload/ payload remains; you can upload later.")
        return 0

    # ============================================================
    # PHASE E: cleanup (offer to unlock)
    # ============================================================

    section("Phase E: cleanup")
    if confirm("Unlock all the read-only files now (so you can edit later)?"):
        n = unlock_all(s, assets_to_cook)
        ok(f"unlocked {n} file(s)")
        info("Re-run the wizard before your next cook to re-stage and re-lock.")
    else:
        info("Files left locked. Re-run the wizard to unlock when needed.")

    section("Done")
    info(f"Recovery backups: {s.modkit_root}/{s.mod_name}_workflow_backup_*.zip")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
