# Scripts

Standalone Python 3 scripts that run **on the host** (not inside the Modkit's UE editor). Standard library only — no `pip install` step.

For editor-side scripts (Python that runs inside the Modkit), see [`modkit/`](modkit/).

## At a glance

| Script | Purpose |
| --- | --- |
| [`mod_workflow.py`](mod_workflow.py) | Interactive wizard that walks a Last Oasis mod from any starting state through Cook + Upload to Steam Workshop. The canonical migration tool. |

---

## `mod_workflow.py`

Migrating a v2 mod into the new Modkit involves several cooperating constraints — the Modkit's GC wipes assets it doesn't recognise, Save Mod regenerates a blank manifest, the cook step doesn't auto-stage to `Upload/`. The wizard handles all of that, pausing for the steps that have to happen inside the Modkit (Cook, Upload) and verifying after each.

```
python scripts/mod_workflow.py \
    --modkit "D:/Program Files/Epic Games/LastOasisModkit" \
    --mod BetterRupuSling \
    --author "yourname"
```

**Auto-detects starting state**: Workshop-cached zip / partially prepped / fully prepped / freshly authored in Modkit. Runs only the steps actually needed.

| Flag | Effect |
| --- | --- |
| `--modkit <path>` | **Required.** Modkit install root (folder containing `Game/`). |
| `--mod <name>` | **Required.** Mod folder name. |
| `--author <name>` | Author display name. Used only if not already set in the manifest. |

### What it does

1. **Diagnose & plan** — classifies your mod's current state, prints what it'll do, asks for confirmation.
2. **Backup** — zips your current mod state to `<modkit>/<Mod>_workflow_backup_<timestamp>.zip`.
3. **Cleanup other Content/Mods/ folders** — byte-compares each to its `Saved/.../Assets/` mirror, deletes only those that are 100% identical (avoids cross-mod ghost entries in the next Cook).
4. **Stage source files** at BOTH `Content/Mods/<Mod>/` and `Saved/Mods/<Mod>/Assets/Mods/<Mod>/` (Mist game-asset overrides go at both `Content/Mist/` and `Saved/.../Assets/Mist/`).
5. **Patch the v3 manifest** with `steamId`, `author`, `active: true`, populated `assetsToCook` / `createdAssets` / `modifiedAssets` / `referencingAssets`.
6. **Write `thumbnail.png`** at `Saved/Mods/<Mod>/` from the mod's `mod-image.png`.
7. **`chmod -w`** on every file written. Read-only blocks the Modkit's destructive overwrite attempts (manifest regen, asset cleanup) silently.
8. **Pauses for Cook in the Modkit.** Tells you exactly what to click — including *don't* click Save Mod (it would try to overwrite the locked manifest).
9. **Verifies cook output** — checks `Pak/<Mod>.pak` is a reasonable size (not 238 bytes, which means an empty cook).
10. **Builds the Upload payload** by hand — `Upload/<steamId>.{pak,sig,zip}` + manifest copy. The source zip mirrors the original Workshop zip's layout.
11. **Pauses for Upload to Workshop in the Modkit.**
12. **Optionally `chmod +w`** everything afterwards so you can edit later.

### Recovery

The wizard makes a backup zip before any destructive action. If anything looks wrong:

1. Close the Modkit.
2. Unzip `<modkit>/<Mod>_workflow_backup_<timestamp>.zip` back into the modkit root.
3. Re-run the wizard — it'll re-diagnose and pick up from the right state.

If your source files have been wiped from disk entirely (e.g., the Modkit's GC fired before the wizard could lock things), the original Workshop zip at `Saved/Mods/<Mod>/<workshop-id>.zip` is the source of truth — the wizard re-extracts from it automatically when nothing else is available.

### Full porting guide

For the why behind the recipe (Modkit GC, Save Mod regenerating blank manifest, etc.), and the manual-process reference, see [docs/modkit-guides/porting-a-mod-from-old-modkit.md](../docs/modkit-guides/porting-a-mod-from-old-modkit.md#automating-with-mod_workflowpy).
