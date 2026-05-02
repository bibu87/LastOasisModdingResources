# Scripts

Standalone Python 3 scripts that run **on the host** (not inside the Modkit's UE editor). Standard library only — no `pip install` step.

For editor-side scripts (Python that runs inside the Modkit), see [`modkit/`](modkit/).

## At a glance

| Script | Purpose | Default mode |
| --- | --- | --- |
| [`migrate_mod_v2_to_v3.py`](migrate_mod_v2_to_v3.py) | Stage an existing v2 mod (assets at `Content/Mods/<Mod>/`) so the new Modkit can find and edit it. | dry-run (`--apply` to act) |
| [`recover_mod_from_workshop.py`](recover_mod_from_workshop.py) | Recover a Workshop-cached mod (zip at `Saved/Mods/<Mod>/<ID>.zip`) into editable form. | dry-run (`--apply` to act) |

Both scripts:
- Default to dry-run; require explicit `--apply` to touch files.
- Create a timestamped zip backup at the modkit root before any change.
- Refuse to overwrite existing target state without `--force`.

---

## `migrate_mod_v2_to_v3.py`

You have an existing v2 mod sitting at `Content/Mods/<Mod>/` (your own work, an old copy, etc.) and want to use it in the new Modkit. The Modkit's mod-selection screen scans `Saved/Mods/<Mod>/modinfo.json` — so the only thing missing is the manifest at the right place.

This script **moves `modinfo.json` from `Content/Mods/<Mod>/` to `Saved/Mods/<Mod>/`** and stops. Assets stay where they are. The schema stays as v2. The actual v3 conversion happens inside the Modkit when you click **Mod Manager → Save Mod** (which is the only safe way to populate the v3 asset-list fields without tripping the Modkit's GC).

```
# Preview (no changes)
python scripts/migrate_mod_v2_to_v3.py \
    --modkit "D:/Program Files/Epic Games/LastOasisModkit" \
    --mod MyTestMod

# Do it
python scripts/migrate_mod_v2_to_v3.py \
    --modkit "..." --mod MyTestMod --apply
```

| Flag | Effect |
| --- | --- |
| `--modkit <path>` | **Required.** Modkit install root (folder containing `Game/`). |
| `--mod <name>` | **Required.** Mod folder name. |
| `--apply` | Actually perform the move. Default is dry-run. |
| `--force` | Allow overwriting an existing `Saved/Mods/<Mod>/modinfo.json` and removing a leftover `Saved/Mods/<Mod>/Assets/`. |

Backup zip: `<modkit>/<Mod>_v2_backup_<timestamp>.zip`.

Full guide: [docs/modkit-guides/porting-a-mod-from-old-modkit.md](../docs/modkit-guides/porting-a-mod-from-old-modkit.md#automating-with-the-migration-script).

---

## `recover_mod_from_workshop.py`

When you subscribe to a Workshop mod, the Modkit caches it at `<modkit>/Game/Saved/Mods/<Mod>/` as `<WORKSHOP_ID>.zip` (source assets) + `.pak` (cooked) + `.sig` + `modinfo.json` (v2). You can see it in the selection screen but can't edit it — the assets are still inside the zip.

This script **extracts the zip into `Game/Content/`** (entries already start with `Content/...`, so they land at `Content/Mods/<Mod>/...` and `Content/Mist/...` for any overridden game assets). The v2 manifest at `Saved/Mods/<Mod>/modinfo.json` is **left in place** — that's where the Modkit looks for the mod entry.

```
# Preview, all auto-discovered mods
python scripts/recover_mod_from_workshop.py \
    --modkit "D:/Program Files/Epic Games/LastOasisModkit"

# Recover a single mod
python scripts/recover_mod_from_workshop.py \
    --modkit "..." --mod BetterRupuSling --apply

# Recover everything + remove the now-redundant cache files
python scripts/recover_mod_from_workshop.py \
    --modkit "..." --apply --remove-workshop-cache
```

| Flag | Effect |
| --- | --- |
| `--modkit <path>` | **Required.** Modkit install root. |
| `--mod <name>` | Process one mod. Omit to auto-discover and process all. |
| `--apply` | Actually extract. Default is dry-run. |
| `--force` | Allow overwriting an existing `Content/Mods/<Mod>/` or removing a leftover `Saved/Mods/<Mod>/Assets/`. |
| `--remove-workshop-cache` | After extraction, delete the `.zip`/`.pak`/`.sig` cache files. (Manifest stays — without it, the Modkit can't find the mod.) |

Zipslip-protected. Post-extraction-verifies file sizes before any cleanup.

Backup zip: `<modkit>/<Mod>_recovery_backup_<timestamp>.zip`.

Full guide: [docs/modkit-guides/porting-a-mod-from-old-modkit.md](../docs/modkit-guides/porting-a-mod-from-old-modkit.md#automating-recovery-from-workshop-downloads).

---

## After either script: open the Modkit

1. Each recovered/staged mod appears in the selection screen.
2. Select it. Edit if you want.
3. **Mod Manager → Save Mod** — this is what migrates the mod to v3 properly (populating `createdAssets` / `modifiedAssets` / `assetTree` / `assetHashes`, then atomically moving assets into `Saved/Mods/<Mod>/Assets/` with everything flagged correctly).
4. Cook & test against a local modded server before re-uploading.

## When to use which?

| You have… | Use |
| --- | --- |
| A v2 mod source on disk under `Content/Mods/<Mod>/` (assets + manifest) | [`migrate_mod_v2_to_v3.py`](migrate_mod_v2_to_v3.py) |
| A subscribed Workshop mod cached under `Saved/Mods/<Mod>/` (zip + manifest) | [`recover_mod_from_workshop.py`](recover_mod_from_workshop.py) |
| Already in v3 layout, want to re-cook / re-publish | Neither — use the Modkit's Mod Manager directly. |
