# Porting a Mod from the Old ModKit (`modKitVersion` 2 → 3)

> **Source:** Variant of the official Donkey Crew doc [*Porting a mod from old ModKit version to the new one*](https://docs.google.com/document/d/1VHZTpzI3CgacgyHTwb017DIjjKXGaa0vvQ3dygjl_HA/). Expanded with a recovery path for lost source, a field-by-field schema diff, and a verification checklist. Verify volatile claims against the [#modkit channels on the official Discord](https://discord.gg/lastoasis).

The Modkit 2.0 release shipped alongside Season 6 ("Moving Forward"). It changed both **where mod source lives on disk** and **the shape of `modinfo.json`**. Old mods (`modKitVersion: 2`) won't load in the new editor until both are migrated.

This guide walks the migration end-to-end, with two starting points:

1. **You still have your old mod folder on disk** → start at [Step 1](#step-1-locate-the-old-mod).
2. **You lost the source but the mod is still on Steam Workshop** → start at [Recovering source from Workshop](#recovering-source-from-workshop), then return to Step 1.

> **Prefer to automate the file-shuffling and JSON rewrite?** This repo ships a migration script at [scripts/migrate_mod_v2_to_v3.py](../../scripts/migrate_mod_v2_to_v3.py) that does Steps 2–5 below mechanically (zip-backs-up the v2 mod, moves files into `Saved/Mods/<Mod>/Assets/`, and rewrites `modinfo.json` to the v3 schema). It defaults to dry-run; you still do Steps 6–7 (verify in editor, click *Save Mod*, cook, test) by hand. See [Automating with the migration script](#automating-with-the-migration-script) at the bottom of this guide.

---

## Recovering source from Workshop

If your only copy of the mod is the cooked package on Steam Workshop, you can pull the assets back down:

1. Subscribe to your own mod on Workshop.
2. Open `<YourSteamFolder>/steamapps/workshop/content/903950/<YourModID>/` — `903950` is Last Oasis's app ID; `<YourModID>` is the long numeric Workshop ID.
3. Inside, you'll find a zip containing the `.uasset` files and `modinfo.json`. Unzip it somewhere outside the ModKit first (so you can review what's there before reimporting).

The recovered files are the **cooked** versions of your assets, but they're still loadable in the editor — they re-import as the same `.uasset` files. You won't get back any *uncooked-only* development scratch; if you stripped editor-only metadata at cook time, that's gone.

Once you have the assets, follow the migration steps below as if you'd never lost them.

> **Faster path: the Modkit may have already cached the Workshop download for you.** When you subscribe to a mod (or it's already loaded by the Modkit's mod manager), the cached assets land at `<ModkitRoot>/Game/Saved/Mods/<ModName>/<WORKSHOP_ID>.zip` alongside the v2 `modinfo.json`. The repo's [scripts/recover_mod_from_workshop.py](../../scripts/recover_mod_from_workshop.py) auto-discovers every such mod and migrates them to v3 in one pass — see [Automating recovery from Workshop downloads](#automating-recovery-from-workshop-downloads) below.

---

## Step 1: Locate the old mod

Old mods lived under the editor's `Content` directory:

```
ModKit/Game/Content/Mods/<YourModName>/
```

Worked example used throughout this guide: `<YourModName>` is `MyTestMod`.

```
ModKit/Game/Content/Mods/MyTestMod/
├── modinfo.json
├── MyTestActor.uasset
└── ... (other mod assets)
```

Some legacy mods also touched original game assets directly under paths like `ModKit/Game/Content/Mist/Data/...`. Track those down too — they need to move with the mod.

---

## Step 2: Build the new on-disk layout

The new ModKit moves mod source out of `Content/` and into `Saved/Mods/<YourModName>/Assets/`, mirroring the same internal folder tree.

Create:

```
ModKit/Game/Saved/Mods/MyTestMod/
└── Assets/
```

---

## Step 3: Move `modinfo.json`

Move (don't copy) the JSON manifest:

```
FROM: ModKit/Game/Content/Mods/MyTestMod/modinfo.json
TO:   ModKit/Game/Saved/Mods/MyTestMod/modinfo.json
```

> Note: it goes **next to** `Assets/`, not inside it.

---

## Step 4: Move the assets

Move every `.uasset` belonging to your mod from `Content/...` into `Saved/Mods/<YourModName>/Assets/...`, **preserving the relative path** below `Content/`.

Two examples:

| Old path (`Content/...`) | New path (`Saved/Mods/MyTestMod/Assets/...`) |
| --- | --- |
| `ModKit/Game/Content/Mist/Data/MyTestAsset.uasset` | `ModKit/Saved/Mods/MyTestMod/Assets/Mist/Data/MyTestAsset.uasset` |
| `ModKit/Game/Content/Mods/MyTestMod/MyTestActor.uasset` | `ModKit/Saved/Mods/MyTestMod/Assets/Mods/MyTestMod/MyTestActor.uasset` |

The rule: whatever was under `Content/` becomes the path under `Assets/`. Keep `.uexp` and `.ubulk` siblings together with their `.uasset`.

> **Move, don't copy.** Leftover originals under `Content/` will be re-detected by the editor as overrides of stock game assets and may either get reverted on next ModKit boot or, worse, conflict with the relocated copies.

---

## Step 5: Rewrite `modinfo.json`

The schema changes substantially. Old format:

```json
{
  "title": "My Test Mod",
  "description": "My mod description",
  "iD": 3263447442,
  "tag": "General",
  "thumbnailPath": "/thumb.jpg",
  "creator": 76561198073588512,
  "active": false,
  "folderName": "MyTestMod",
  "modDependencies": [],
  "assetsToCook": {
    "/Game/Mods/MyTestMod/MyTestActor": "Blueprint"
  },
  "modKitVersion": 2
}
```

New format:

```json
{
  "title": "My Test Mod",
  "description": "My mod description",
  "author": "BryanTheHacker",
  "steamId": 3263447442,
  "tag": "General",
  "creator": 76561198073588511,
  "active": true,
  "folderName": "MyTestMod",
  "modDependencies": [],
  "assetsToCook": {
    "/Game/Mods/MyTestMod/MyTestActor": "Blueprint"
  },
  "createdAssets": [
    "/Game/Mods/MyTestMod/MyTestActor": "Blueprint"
  ],
  "modifiedAssets": [
    "/Game/Mods/MyTestMod/MyTestActor": "Blueprint"
  ],
  "deletedAssets": [],
  "referencingAssets": [
    "/Game/Mods/MyTestMod/MyTestActor": "Blueprint"
  ],
  "referencingAssetsToNotCook": [],
  "assetTree": [],
  "assetHashes": {},
  "modKitVersion": 3,
  "enforceSameMods": "WarningOnly",
  "modHash": 0,
  "version": {
    "Main": 1,
    "Major": 0,
    "Minor": 0,
    "Micro": 0
  }
}
```

> The blocks above are reproduced verbatim from the official doc — including the slightly unusual mixed object/array notation in `createdAssets`, `modifiedAssets`, and `referencingAssets`. If your editor's JSON linter complains, treat the official sample as authoritative for the ModKit's own loader; the published Mod Manager is what consumes this file in practice. When in doubt, **save the mod once from Mod Manager**: it will rewrite the file in the canonical shape the new ModKit expects.

### Field-by-field diff

| Field | v2 | v3 | Notes |
| --- | --- | --- | --- |
| `iD` | required | renamed → `steamId` | Same Workshop ID, new key. |
| `thumbnailPath` | required | dropped | Thumbnail is now picked at upload time in Mod Manager (Workshop UI). |
| `active` | typically `false` | typically `true` | Controls whether this mod is enabled when the ModKit boots into mod-selection. |
| `creator` | SteamID64 of author | unchanged | The example in the official doc shows different trailing digits between v2 and v3; in practice this should be your own SteamID64. |
| `assetsToCook` | required | unchanged | Path → asset-type map. Drives the cooker. |
| `modDependencies` | `[]` | `[]` | Workshop IDs of referenced mods. See [Mod references](mod-references.md). |
| `author` | — | new | Display name (string), distinct from `creator` SteamID64. |
| `createdAssets` | — | new | Assets newly authored by this mod. |
| `modifiedAssets` | — | new | Stock assets this mod overrides. |
| `deletedAssets` | — | new | Stock assets this mod removes. |
| `referencingAssets` | — | new | Assets that reference others (used for dependency-graph cooking). |
| `referencingAssetsToNotCook` | — | new | Excludes referenced-but-shouldn't-ship assets from the cook. |
| `assetTree` | — | new | Cooker-managed; usually leave as `[]`, Mod Manager fills it on save. |
| `assetHashes` | — | new | Cooker-managed; usually leave as `{}`. |
| `enforceSameMods` | — | new | `"WarningOnly"` is the safe default. |
| `modHash` | — | new | Cooker-managed; `0` is fine pre-cook. |
| `version` | — | new | Semver-ish struct (`Main`/`Major`/`Minor`/`Micro`). Bump on each release. |
| `modKitVersion` | `2` | `3` | The version sentinel — must say `3` for the new ModKit to pick the mod up. |

> **Anything you're not sure about → leave to Mod Manager.** The cooker-managed fields (`assetTree`, `assetHashes`, `modHash`) are filled in automatically the first time you save the mod through Mod Manager. The required things to get right by hand are `steamId`, `folderName`, `assetsToCook`, and `modKitVersion: 3`.

---

## Step 6: Boot the ModKit and verify

1. Launch the ModKit from the Epic Games launcher or `RunDevKit.bat`.
2. The mod selection screen should now list your mod. If it doesn't:
    - The folder name on disk doesn't match `folderName` in `modinfo.json`.
    - `modKitVersion` isn't `3`.
    - `modinfo.json` is in the wrong place (it should sit at `Saved/Mods/<YourModName>/modinfo.json`, **not** inside `Assets/`).
3. Select the mod. The editor boots and mounts only this mod's assets.
4. Open the Content Browser and confirm every asset you moved is visible. Missing assets usually mean a path mismatch — recheck Step 4 against your actual on-disk layout.
5. **Resave each migrated asset** (Content Browser → right-click → *Save*, or *File → Save All*). This re-flags them as edited in the new editor and writes the new `.uasset` headers.
6. Open Mod Manager and click **Save Mod**. This is what marks your mod's assets as `ModifiedByModkit` so they're preserved across ModKit restarts. Without this step, the next boot may treat them as stale and clean them up.

---

## Step 7: Cook a test build (don't upload yet)

Before pushing the migrated mod to the live Workshop item:

1. Mod Manager → **Cook and Package Mod**. Wait for the batch script to finish — never close the cook window mid-cook.
2. Spin up a local modded server with **only this mod** in `Mods=`. See [Host a modded server](host-a-modded-server.md).
3. Join the server with your Last Oasis client (default Steam branch — `SDKTest` is no longer required) and verify the modded content loads, behaves as expected, and produces no errors in the server log.

If everything looks good, then upload from Mod Manager. **Bump `version.Minor` (or higher) before re-uploading**, so subscribers get the migrated build picked up by Steam.

---

## Common pitfalls

- **Mod doesn't appear in the selection screen.** `modKitVersion` is still `2`, or `folderName` is wrong, or `modinfo.json` is inside `Assets/` rather than next to it.
- **Mod appears but assets show as "missing" / red icons in Content Browser.** Path under `Assets/` doesn't mirror the original `Content/` path, or you copied instead of moved and the editor mounted the originals instead.
- **Editor "restores" your assets back to vanilla on next boot.** You forgot to *Save Mod* after resaving the assets. The ModKit garbage-collects anything not flagged `ModifiedByModkit`.
- **Cook silently strips assets you expect.** Check `assetsToCook` — it's the canonical "what gets shipped" list. If an asset isn't in there, it doesn't go into the `.pak`, regardless of whether it exists on disk.
- **Workshop subscribers get an old version after you re-upload.** Increment `version` in `modinfo.json`. Steam compares versions to decide whether to pull the update.

---

## Automating with the migration script

The repo ships [`scripts/migrate_mod_v2_to_v3.py`](../../scripts/migrate_mod_v2_to_v3.py) — a standalone Python 3 script that handles the smallest mechanical step needed to get a v2 mod into the new Modkit: **moving `modinfo.json` from `Content/Mods/<Mod>/` to `Saved/Mods/<Mod>/`**, so the new Modkit's mod-selection screen can find it.

It deliberately does NOT do the full Steps 2–5 layout move and Step 6 schema rewrite. Both of those are better done **inside the Modkit** via **Mod Manager → Save Mod**, which:

- Properly populates the v3 manifest's `createdAssets` / `modifiedAssets` / `referencingAssets` / `assetTree` / `assetHashes` fields.
- Moves assets into `Saved/Mods/<Mod>/Assets/` *with the asset-list fields already populated*, so the Modkit's GC doesn't wipe them.

> **Why doesn't the script do the full v3 conversion?** An earlier version did — it moved assets into `Saved/Mods/<Mod>/Assets/` and emitted a v3 manifest with the asset-list fields left empty (relying on Mod Manager to populate them on first **Save Mod**). That doesn't work: the Modkit's mod-load sequence garbage-collects anything in `Saved/Mods/<Mod>/Assets/` that isn't already flagged in those fields, so the assets vanish before you can reach **Save Mod**. By keeping the manifest as v2 and the assets at the v2 source location, the GC doesn't kick in (it's scoped to v3-layout `Assets/` trees), and **Save Mod**'s in-Modkit migration generates the v3 manifest with everything correct.

### What the script covers

- Validates that the source mod's `modinfo.json` is `modKitVersion: 2`.
- Refuses if `Saved/Mods/<Mod>/modinfo.json` already exists (unless `--force`).
- Refuses if `Saved/Mods/<Mod>/Assets/` exists from a prior broken-v3 attempt (unless `--force`, which removes it).
- On `--apply`: zips a backup of the v2 manifest (and any pre-existing `Saved/Mods/<Mod>/` state) to `<modkit>/<Mod>_v2_backup_<timestamp>.zip`, then moves `modinfo.json` from `Content/Mods/<Mod>/` to `Saved/Mods/<Mod>/`. Assets stay at `Content/Mods/<Mod>/<files>` (the v2 source location, where v2 manifests reference assets from).

### What the script does NOT cover

- Steps 4–5 (asset move into `Saved/Mods/<Mod>/Assets/`) — Save Mod does this.
- Step 6 (manifest rewrite to v3) — Save Mod does this.
- Step 7 (cook + local server smoke test) — by hand.

### Usage

```
# Dry-run (default): print the move plan, change nothing.
python scripts/migrate_mod_v2_to_v3.py \
    --modkit "D:/Program Files/Epic Games/LastOasisModkit" \
    --mod MyTestMod

# Actually do it (creates zip backup first).
python scripts/migrate_mod_v2_to_v3.py \
    --modkit "D:/Program Files/Epic Games/LastOasisModkit" \
    --mod MyTestMod \
    --apply
```

`--force` lets you proceed even if `Saved/Mods/<Mod>/modinfo.json` already exists or there's a leftover `Saved/Mods/<Mod>/Assets/` from a prior broken-v3 attempt (destructive — only use if you intend to overwrite).

### Recovery

If anything looks wrong after `--apply`:

1. Unzip the auto-generated backup at `<modkit>/<Mod>_v2_backup_<timestamp>.zip` back into the modkit root — that restores the v2 manifest at its original location and any prior `Saved/Mods/<Mod>/` state.
2. Re-run with the right flags.

## Automating recovery from Workshop downloads

Where the migration script in the previous section assumes the v2 mod is already laid out under `Content/Mods/<Mod>/`, [`scripts/recover_mod_from_workshop.py`](../../scripts/recover_mod_from_workshop.py) handles the **other common starting point**: the Workshop download cached at `<ModkitRoot>/Game/Saved/Mods/<ModName>/<WORKSHOP_ID>.zip`.

The script extracts the Workshop zip into `Game/Content/` (entries already start with `Content/...`, so they land at `Game/Content/Mods/<Mod>/...` and `Game/Content/Mist/...` for overridden game assets). Crucially it **leaves the v2 `modinfo.json` exactly where the Modkit's mod-selection screen scans for it** — at `Saved/Mods/<Mod>/modinfo.json`. With this layout the Modkit:

1. Finds the mod in the selection screen (via the v2 manifest at `Saved/Mods/<Mod>/`).
2. Reads the manifest, sees `modKitVersion: 2`.
3. Loads the assets from `Content/Mods/<Mod>/` (the v2 source location the manifest references).
4. Lets you edit them.

From there you can either:

- **Click Mod Manager → Save Mod inside the Modkit** — the Modkit handles the v3 migration internally and properly populates the asset-list fields, so the assets stay flagged and survive future boots.
- **Run [`scripts/migrate_mod_v2_to_v3.py`](../../scripts/migrate_mod_v2_to_v3.py)** to do the v2 → v3 layout move offline (still requires **Save Mod** in the Modkit afterwards to flag the assets).

### Two failure modes the script avoids

This took two iterations to get right. Documenting both so the constraints are visible:

1. **Don't extract to `Saved/Mods/<Mod>/Assets/` with an empty v3 manifest.** The Modkit's mod-load sequence garbage-collects anything in `Saved/Mods/<Mod>/Assets/` that isn't already flagged in `createdAssets` / `modifiedAssets` / `assetTree` / `assetHashes`. If the manifest leaves those empty (relying on Mod Manager to populate them on first **Save Mod**), the assets vanish before you can reach **Save Mod**. Chicken-and-egg.

2. **Don't move the manifest from `Saved/Mods/<Mod>/` to `Content/Mods/<Mod>/`.** The Modkit's mod-selection screen *only* scans `Saved/Mods/<Mod>/modinfo.json` — moving the manifest to the Content side makes the mod invisible in the selection screen.

The working layout: manifest stays at `Saved/Mods/<Mod>/modinfo.json`, assets land at `Content/Mods/<Mod>/<files>`. Best of both: discoverable AND editable AND no GC.

### What the script does

- **Auto-discovers** every folder under `Game/Saved/Mods/` that has both a `modinfo.json` and a `<numeric-id>.zip` alongside it. Skips folders without a zip (so manual / partial folders don't trigger).
- For each, plans extraction: every zip entry under `Content/...` lands at the same path under `Game/Content/` (so `Content/Mods/Foo/Bar.uasset` → `Game/Content/Mods/Foo/Bar.uasset`).
- **Zipslip-safe**: rejects any zip entry whose path contains `..` or is absolute.
- On `--apply`: zip-backs-up the existing `Saved/Mods/<Mod>/modinfo.json` (and any pre-existing `Saved/Mods/<Mod>/Assets/`) to `<modkit>/<Mod>_recovery_backup_<timestamp>.zip`, extracts the zip, **post-extraction-verifies every file** (size matches the zip entry), then removes any leftover `Saved/Mods/<Mod>/Assets/` from a prior broken-v3 attempt. **The manifest at `Saved/Mods/<Mod>/modinfo.json` is left untouched.**
- Refuses if `Content/Mods/<Mod>/` already exists, unless `--force`.
- Refuses if `Saved/Mods/<Mod>/modinfo.json` is already `modKitVersion: 3` (someone tried an earlier broken-v3 migration). See [Recovery if something looks wrong](#recovery-if-something-looks-wrong) below.
- `--remove-workshop-cache` optionally deletes the now-redundant `.zip`/`.pak`/`.sig` Workshop cache files after successful extraction. (The manifest stays even with this flag — without it, the Modkit can't find the mod.)

### Usage

```
# Dry-run: discover all recoverable mods and print their plans.
python scripts/recover_mod_from_workshop.py \
    --modkit "D:/Program Files/Epic Games/LastOasisModkit"

# Recover one named mod.
python scripts/recover_mod_from_workshop.py \
    --modkit "..." --mod BetterRupuSling --apply

# Recover every discovered mod and clean up cache files.
python scripts/recover_mod_from_workshop.py \
    --modkit "..." --apply --remove-workshop-cache
```

After running, the next step is in the Modkit:

1. Launch the Modkit; each recovered mod appears in the selection screen as a v2 mod.
2. Select a mod, edit if you want, then **Mod Manager → Save Mod**.
3. The Modkit migrates it to v3 properly (populating the asset-list fields the manual approach can't safely guess).

### Recovery if something looks wrong

If you ran an **earlier (pre-fix) version** of the script and your mod is now stuck in a broken-v3 state (manifest is `modKitVersion: 3` at `Saved/Mods/<Mod>/modinfo.json`, and/or `Assets/` is empty or vanishes on Modkit load):

1. Open `<modkit>/<Mod>_recovery_backup_<timestamp>.zip`.
2. Extract `Game/Saved/Mods/<Mod>/modinfo.json` from the backup and **place it back at that path** (overwriting the broken v3 one). This is the original v2 manifest from before the broken migration ran.
3. Delete the empty `Saved/Mods/<Mod>/Assets/` folder if it exists.
4. If an earlier script left a `Content/Mods/<Mod>/modinfo.json`, delete it too (the canonical manifest is the one at `Saved/Mods/<Mod>/`).
5. Re-run the recovery script — it now sees a clean v2 starting state and will extract to `Content/Mods/<Mod>/` correctly.

For the current (fixed) script, recovery is rarely needed: post-extraction verification catches silent failures before any cleanup, and the `Saved/Mods/<Mod>/` state is left untouched if anything fails. If you do hit a problem, the same backup zip restores the original state.

### When to use which script

| Starting point | Script |
| --- | --- |
| Old v2 mod source on disk under `Content/Mods/<Mod>/` | [`scripts/migrate_mod_v2_to_v3.py`](../../scripts/migrate_mod_v2_to_v3.py) (v2 → v3 layout move) |
| Workshop download cached under `Saved/Mods/<Mod>/` (zip + v2 modinfo) | [`scripts/recover_mod_from_workshop.py`](../../scripts/recover_mod_from_workshop.py) (zip → v2 source, then use either of the two above paths to v3) |
| Already in v3 layout but want to re-pack/cook | Neither — use the Modkit's Mod Manager directly. |

## Related guides

- [How to make and upload a mod](how-to-make-and-upload-a-mod.md) — Mod Manager, cooking, and Workshop upload from scratch.
- [Host a modded server](host-a-modded-server.md) — for verifying the migrated mod in a real server before re-publishing.
- [Mod references](mod-references.md) — if your old mod listed dependencies under v2, double-check they're still in `modDependencies` after the migration.
