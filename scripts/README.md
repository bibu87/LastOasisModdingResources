# Scripts

Standalone Python 3 scripts that run **on the host** (not inside the Modkit's UE editor). Standard library only — no `pip install` step.

For editor-side scripts (Python that runs inside the Modkit), see [`modkit/`](modkit/).

For UAsset diagnostic + recovery tools (when the editor's load + re-save cycle damaged assets), see [`uasset/`](uasset/).

## At a glance

| Script | Purpose |
| --- | --- |
| [`mod_workflow.py`](mod_workflow.py) | Interactive wizard that walks a Last Oasis mod from any starting state through Cook + Upload to Steam Workshop. The canonical migration tool. |
| [`uasset/`](uasset/) | Toolkit for diagnosing and recovering `.uasset` files damaged by upstream renames or migration. Workshop-pak vs. project triage, header/property dumpers, and a binary patcher for struct renames without CoreRedirects. |

---

## `mod_workflow.py`

Migrating a v2 mod into the new Modkit involves a few cooperating Modkit-side gaps — the cook step doesn't auto-stage to `Upload/`, Save Mod *can* regenerate a blank manifest if it doesn't recognise the state, the GC may wipe assets it doesn't have hashes for. The wizard handles all of that, pausing for the steps that have to happen inside the Modkit (Cook, Upload) and verifying after each.

```
python scripts/mod_workflow.py \
    --modkit "D:/Program Files/Epic Games/LastOasisModkit" \
    --mod MyMod \
    --author "yourname"
```

**Auto-detects starting state**:

| State | Trigger |
| --- | --- |
| `WORKSHOP_CACHED` | v2 manifest + `<id>.zip` in `Saved/Mods/<Mod>/`, no extracted source. |
| `SOURCE_AT_SAVED_ROOT` | v2 manifest + source `.uasset` files at `Saved/Mods/<Mod>/<x>.uasset` (alternate-root layout, common when source lives in a git repo). |
| `PARTIAL_PREPPED` | A previous wizard run already populated `Content/Mods/<Mod>/` or the v3 mirror. |
| `RECIPE_PREPPED` | Already prepped, locked, ready for Cook. |
| `ALREADY_DONE` | Fully populated v3 manifest with `assetHashes` (modkit-authored mod) — wizard steps aside. |

| Flag | Effect |
| --- | --- |
| `--modkit <path>` | **Required.** Modkit install root (folder containing `Game/`). |
| `--mod <name>` | Mod folder name. **Required** unless `--workshop-id` is given. |
| `--workshop-id <ID>` | Steam Workshop item ID. Wizard runs `steamcmd` to download the item first (anonymous login — works for public items), then proceeds as if `--mod` had been passed for the downloaded mod. Requires `steamcmd` installed locally (PATH lookup, common Windows locations, or `--steamcmd <path>`). |
| `--steamcmd <path>` | Override path to the steamcmd binary. |
| `--author <name>` | Author display name. Used only if not already set in the manifest. |
| `--lock` | Optional defense-in-depth: `chmod -w` on the patched manifest and source files so an accidental Save Mod click can't overwrite them. **Default is unlocked** — empirically Cook reads the manifest cleanly and doesn't overwrite anything *as long as you skip Save Mod*. |

### Workshop download example

```
python scripts/mod_workflow.py \
    --modkit "D:/Program Files/Epic Games/LastOasisModkit" \
    --workshop-id 1234567890 \
    --author "yourname"
```

The wizard runs `steamcmd +force_install_dir <temp> +login anonymous +workshop_download_item 903950 <ID> +quit`, reads `folderName` from the downloaded `modinfo.json`, copies the files into `<modkit>/Game/Saved/Mods/<folderName>/`, then continues with the normal flow (which will classify the new state as `WORKSHOP_CACHED`).

If the Workshop item is private/restricted and anonymous login fails, you'll need to subscribe via the Steam client (which makes the Modkit's own cache pick it up) and use `--mod <folderName>` instead.

### What it does

1. **Diagnose & plan** — classifies your mod's current state, prints what it'll do, asks for confirmation.
2. **Backup** — zips your current mod state to `<modkit>/<Mod>_workflow_backup_<timestamp>.zip`.
3. **Cleanup other Content/Mods/ folders** — byte-compares each to its `Saved/.../Assets/` mirror, deletes those that are 100% identical. For folders where files differ (typically cook artifacts), lists the actual diffs and *prompts* to force-delete (default No).
4. **Stage source files** at both `Content/Mods/<Mod>/` (cook source) and `Saved/Mods/<Mod>/Assets/Mods/<Mod>/` (v3 mirror). Mist game-asset overrides land at both `Content/Mist/` and `Saved/.../Assets/Mist/`. For `SOURCE_AT_SAVED_ROOT` mods, the wizard *moves* (not copies) source files out of the saved-root and cleans up empty parent dirs — single source of truth, no triple-stored confusion.
5. **Patch the v3 manifest** with `steamId`, `author`, `active: true`, populated `assetsToCook` / `createdAssets` / `modifiedAssets` / `referencingAssets`. Preserves `thumbnailPath` if present (looks at backup zips when the current manifest doesn't carry it).
6. **Write `thumbnail.png`** at `Saved/Mods/<Mod>/` from the file `thumbnailPath` points at (commonly `mod-image.png`, but any image filename works). The thumbnail source stays where it is — it doesn't need to be in `Content/Mods/`.
7. **Optional: `chmod -w`** on the patched state if `--lock` was passed.
8. **Pauses for Cook in the Modkit.** Tells you exactly what to click — including *don't* click Save Mod (it can regenerate a blank manifest if the in-memory state isn't recognised; the impact varies per mod).
9. **Verifies cook output** — checks `Pak/<Mod>.pak` is a reasonable size (not 238 bytes, which means an empty cook).
10. **Builds the Upload payload** by hand — `Upload/<steamId>.{pak,sig,zip}` + manifest copy. The source zip is built from `Content/Mods/<Mod>/`.
11. **Pauses for Upload to Workshop in the Modkit.**
12. If `--lock` was used: **prompts to `chmod +w`** everything so you can edit later.

### Recovery

The wizard makes a backup zip before any destructive action. If anything looks wrong:

1. Close the Modkit.
2. Unzip `<modkit>/<Mod>_workflow_backup_<timestamp>.zip` back into the modkit root.
3. Re-run the wizard — it'll re-diagnose and pick up from the right state.

If your source files have been wiped from disk entirely (e.g. the Modkit's GC fired between unrelated steps), the original Workshop zip at `Saved/Mods/<Mod>/<workshop-id>.zip` is the source of truth — the wizard re-extracts from it automatically when nothing else is available.

### Full porting guide

For the why behind the recipe (Modkit GC, Save Mod's behaviour, the empirical findings across multiple mods), see [docs/modkit-guides/porting-a-mod-from-old-modkit.md](../docs/modkit-guides/porting-a-mod-from-old-modkit.md#automating-with-mod_workflowpy).
