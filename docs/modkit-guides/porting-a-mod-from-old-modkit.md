# Porting a Mod from the Old ModKit (`modKitVersion` 2 → 3)

> **Source:** Variant of the official Donkey Crew doc [*Porting a mod from old ModKit version to the new one*](https://docs.google.com/document/d/1VHZTpzI3CgacgyHTwb017DIjjKXGaa0vvQ3dygjl_HA/). Expanded with a recovery path for lost source, a field-by-field schema diff, and a verification checklist. Verify volatile claims against the [#modkit channels on the official Discord](https://discord.gg/lastoasis).

The Modkit 2.0 release shipped alongside Season 6 ("Moving Forward"). It changed both **where mod source lives on disk** and **the shape of `modinfo.json`**. Old mods (`modKitVersion: 2`) won't load in the new editor until both are migrated.

This guide walks the migration end-to-end, with two starting points:

1. **You still have your old mod folder on disk** → start at [Step 1](#step-1-locate-the-old-mod).
2. **You lost the source but the mod is still on Steam Workshop** → start at [Recovering source from Workshop](#recovering-source-from-workshop), then return to Step 1.

> **The official manual flow below doesn't actually produce a working mod in the current Modkit version.** Several Modkit-side gaps trip migrated mods (the v3 GC wipes assets it doesn't recognise; Save Mod regenerates a blank manifest losing everything). The working recipe — derived empirically across three real mods — is implemented in the wizard at [`scripts/mod_workflow.py`](../../scripts/mod_workflow.py); see [Automating with mod_workflow.py](#automating-with-mod_workflowpy) at the bottom of this guide. The manual steps below are kept as reference for what the official porting guide describes; **don't follow them in isolation, you'll lose your source files**.

---

## Recovering source from Workshop

If your only copy of the mod is the cooked package on Steam Workshop, you can pull the assets back down:

1. Subscribe to your own mod on Workshop.
2. Open `<YourSteamFolder>/steamapps/workshop/content/903950/<YourModID>/` — `903950` is Last Oasis's app ID; `<YourModID>` is the long numeric Workshop ID.
3. Inside, you'll find a zip containing the `.uasset` files and `modinfo.json`. Unzip it somewhere outside the ModKit first (so you can review what's there before reimporting).

The recovered files are the **cooked** versions of your assets, but they're still loadable in the editor — they re-import as the same `.uasset` files. You won't get back any *uncooked-only* development scratch; if you stripped editor-only metadata at cook time, that's gone.

Once you have the assets, follow the migration steps below as if you'd never lost them.

> **Faster path: the Modkit may have already cached the Workshop download for you.** When you subscribe to a mod (or it's already loaded by the Modkit's mod manager), the cached assets land at `<ModkitRoot>/Game/Saved/Mods/<ModName>/<WORKSHOP_ID>.zip` alongside the v2 `modinfo.json`. The wizard at [`scripts/mod_workflow.py`](../../scripts/mod_workflow.py) auto-discovers and processes that state — see [Automating with mod_workflow.py](#automating-with-mod_workflowpy) below.

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

## Automating with mod_workflow.py

The repo ships an interactive wizard at [`scripts/mod_workflow.py`](../../scripts/mod_workflow.py) that walks a mod from any starting state through Cook + Upload to Steam Workshop. It's the canonical migration tool — the entire end-to-end flow distilled from many failed iterations into the one recipe that actually works.

```
python scripts/mod_workflow.py \
    --modkit "D:/Program Files/Epic Games/LastOasisModkit" \
    --mod BetterRupuSling \
    --author "yourname"
```

The wizard auto-detects what state your mod is in (Workshop-cached zip / partial prep / fully prepped / already-modkit-authored) and runs only the steps that are actually needed. It pauses for the steps that have to happen inside the Modkit (Cook, Upload) and verifies the result before moving on.

### Why a wizard, why this recipe

Earlier iterations of this guide proposed two simpler scripts (`migrate_mod_v2_to_v3.py` and `recover_mod_from_workshop.py`) that implemented the official porting guide as documented. **Both failed in the current Modkit version**, and the failures took several days to characterise. The wizard exists because the working recipe is genuinely non-obvious and has multiple cooperating constraints. Documenting them here so the constraints are visible:

1. **The Modkit's GC wipes anything in `Saved/Mods/<Mod>/Assets/` that isn't flagged in the v3 manifest's `assetHashes` field.** Empty `assetHashes` = "no flagged assets" = wipe everything in `Assets/` on load. Manifest version doesn't matter — even a v2 manifest at `Saved/Mods/<Mod>/` won't protect files at the v3 location.
2. **Save Mod produces a blank v3 manifest from a migrated mod.** It loses `steamId` (resets to 0), empties `assetsToCook` / `createdAssets` / `modifiedAssets` / `referencingAssets`, and leaves `assetHashes` empty. Cook then ships a 238-byte empty `.pak` from the empty manifest, and the Modkit's cleanup pass also wipes `Content/Mods/<Mod>/` because the manifest claims no assets exist there. So **don't click Save Mod** on a migrated mod — it actively destroys state.
3. **The Modkit's mod-selection screen scans `Saved/Mods/<Mod>/modinfo.json`** — moving the manifest to `Content/Mods/<Mod>/` makes the mod invisible.
4. **The cook step doesn't auto-stage to `Upload/`.** It produces `Pak/<Mod>.pak` + `.sig` but never builds `Upload/<steamId>.{pak,sig,zip}` for migrated mods, so Upload to Workshop fails with `Source Zip not found!`.

The wizard sidesteps every one of these:

- Mirrors source files at **both** `Content/Mods/<Mod>/<files>` AND `Saved/Mods/<Mod>/Assets/Mods/<Mod>/<files>` (Mist game-asset overrides go at both `Content/Mist/<rel>` and `Saved/Mods/<Mod>/Assets/Mist/<rel>`).
- Patches the v3 manifest with proper `steamId`, `active: true`, populated `assetsToCook` / `createdAssets` / `modifiedAssets` / `referencingAssets`. Other fields (`assetTree`, `assetHashes`, `modHash`) are left for the cooker.
- Writes `thumbnail.png` at `Saved/Mods/<Mod>/thumbnail.png` from the mod's `mod-image.png`.
- **`chmod -w` on every file we just wrote.** Read-only blocks the Modkit's destructive overwrite attempts (manifest regen, asset cleanup) silently — without errors that would break the cook.
- Tells you to **skip Save Mod** and go straight to Cook in the Modkit.
- Verifies `Pak/<Mod>.pak` looks reasonable (not 238 bytes), then builds `Upload/<steamId>.{pak,sig,zip}` + a manifest copy by hand. The source zip mirrors the original Workshop zip's layout so the upload accepts it as a same-shape replacement.
- Tells you to Upload to Workshop in the Modkit.
- Optionally `chmod +w` everything afterwards so you can edit again.

### What the wizard does NOT cover

- The Modkit-side steps themselves (the wizard pauses and tells you exactly what to click; you do those).
- A mod that's been freshly authored in the new Modkit (it'll have proper `assetHashes` from the start — the wizard recognises this state as `ALREADY_DONE` and steps aside; you use the Modkit's normal Cook + Upload flow).

### Two practices the wizard enforces

- **Restart the Modkit between switching between mods.** UE's asset registry caches stale state across runs; ghost entries from the previous mod can leak into the next mod's Content Browser. A clean restart fixes it. (Sometimes you need TWO restarts before the Content Browser is fully clean.)
- **Before cooking mod X, clean other mods' folders out of `Content/Mods/`** — but only after byte-comparing each to its `Saved/Mods/<other>/Assets/Mods/<other>/` mirror, so we don't lose any uncommitted edits. The wizard does this comparison automatically.

### Recovery if something goes wrong mid-flow

The wizard makes a backup zip at `<modkit>/<Mod>_workflow_backup_<timestamp>.zip` before any destructive action. If anything looks wrong:

1. Close the Modkit.
2. Unzip the backup back into the modkit root (overwriting any wrecked state).
3. Re-run the wizard — it'll re-diagnose and pick up cleanly.

If your source files have been wiped from disk entirely (e.g., the Modkit's GC fired before the wizard had a chance to lock things), the original Workshop zip at `Saved/Mods/<Mod>/<workshop-id>.zip` is the source of truth — the wizard re-extracts from it automatically when it sees no other source.

## Related guides

- [How to make and upload a mod](how-to-make-and-upload-a-mod.md) — Mod Manager, cooking, and Workshop upload from scratch.
- [Host a modded server](host-a-modded-server.md) — for verifying the migrated mod in a real server before re-publishing.
- [Mod references](mod-references.md) — if your old mod listed dependencies under v2, double-check they're still in `modDependencies` after the migration.
