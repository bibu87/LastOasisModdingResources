# Porting a Mod from the Old ModKit (`modKitVersion` 2 → 3)

> **Source:** Variant of the official Donkey Crew doc [*Porting a mod from old ModKit version to the new one*](https://docs.google.com/document/d/1VHZTpzI3CgacgyHTwb017DIjjKXGaa0vvQ3dygjl_HA/). Expanded with a recovery path for lost source, a field-by-field schema diff, and a verification checklist. Verify volatile claims against the [#modkit channels on the official Discord](https://discord.gg/lastoasis).

The Modkit 2.0 release shipped alongside Season 6 ("Moving Forward"). It changed both **where mod source lives on disk** and **the shape of `modinfo.json`**. Old mods (`modKitVersion: 2`) won't load in the new editor until both are migrated.

This guide walks the migration end-to-end, with two starting points:

1. **You still have your old mod folder on disk** → start at [Step 1](#step-1-locate-the-old-mod).
2. **You lost the source but the mod is still on Steam Workshop** → start at [Recovering source from Workshop](#recovering-source-from-workshop), then return to Step 1.

---

## Recovering source from Workshop

If your only copy of the mod is the cooked package on Steam Workshop, you can pull the assets back down:

1. Subscribe to your own mod on Workshop.
2. Open `<YourSteamFolder>/steamapps/workshop/content/903950/<YourModID>/` — `903950` is Last Oasis's app ID; `<YourModID>` is the long numeric Workshop ID.
3. Inside, you'll find a zip containing the `.uasset` files and `modinfo.json`. Unzip it somewhere outside the ModKit first (so you can review what's there before reimporting).

The recovered files are the **cooked** versions of your assets, but they're still loadable in the editor — they re-import as the same `.uasset` files. You won't get back any *uncooked-only* development scratch; if you stripped editor-only metadata at cook time, that's gone.

Once you have the assets, follow the migration steps below as if you'd never lost them.

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
3. Join the server in `SDKTest` Steam branch and verify the modded content loads, behaves as expected, and produces no errors in the server log.

If everything looks good, then upload from Mod Manager. **Bump `version.Minor` (or higher) before re-uploading**, so subscribers get the migrated build picked up by Steam.

---

## Common pitfalls

- **Mod doesn't appear in the selection screen.** `modKitVersion` is still `2`, or `folderName` is wrong, or `modinfo.json` is inside `Assets/` rather than next to it.
- **Mod appears but assets show as "missing" / red icons in Content Browser.** Path under `Assets/` doesn't mirror the original `Content/` path, or you copied instead of moved and the editor mounted the originals instead.
- **Editor "restores" your assets back to vanilla on next boot.** You forgot to *Save Mod* after resaving the assets. The ModKit garbage-collects anything not flagged `ModifiedByModkit`.
- **Cook silently strips assets you expect.** Check `assetsToCook` — it's the canonical "what gets shipped" list. If an asset isn't in there, it doesn't go into the `.pak`, regardless of whether it exists on disk.
- **Workshop subscribers get an old version after you re-upload.** Increment `version` in `modinfo.json`. Steam compares versions to decide whether to pull the update.

---

## Related guides

- [How to make and upload a mod](how-to-make-and-upload-a-mod.md) — Mod Manager, cooking, and Workshop upload from scratch.
- [Host a modded server](host-a-modded-server.md) — for verifying the migrated mod in a real server before re-publishing.
- [Mod references](mod-references.md) — if your old mod listed dependencies under v2, double-check they're still in `modDependencies` after the migration.
