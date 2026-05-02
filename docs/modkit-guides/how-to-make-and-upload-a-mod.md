# How to Make and Upload a Last Oasis Mod

> **Source:** Variant of the official Donkey Crew doc [*ModKit Guide — How to make and upload a Mod*](https://docs.google.com/document/d/1ky_05DNiggXazqH-xL63oUMauZMX95rTejQdj0rVaQo/). Expanded with project-layout details, the Mod Manager workflow in depth, cook/upload pitfalls, and a publishing checklist. Verify volatile claims against the [#modkit channels on the official Discord](https://discord.gg/lastoasis).

The Last Oasis ModKit is the official Donkey Crew toolchain for authoring mods, built on **Unreal Engine 4.25.4** with the game's `Mist` project and a custom **Mod Manager** plugin. This guide walks the full loop: launching the editor → creating or selecting a mod → editing assets → cooking → uploading to Steam Workshop. It is the canonical "make a mod, ship it" reference; the other guides in this folder branch off from here.

---

## At a glance

```
RunDevKit.bat / Epic Launcher
        ↓
Mod selection screen  ──────► [+ Create New Mod]  or pick existing
        ↓
ModKit boots, mounts ONLY the selected mod's assets
        ↓
Edit assets in editor (Content/Mods/<YourMod>/)
        ↓
Mod Manager → Assets to Cook  ◄── controls what gets shipped
        ↓
Mod Manager → Cook and Package Mod (long the first time, fast after)
        ↓
Mod Manager → Upload to Workshop (with title, description, thumbnail, category)
        ↓
Steam Workshop item live
```

---

## 1. Launch the ModKit

Two equivalent entry points:

- From the **Epic Games Launcher** → Library → *Last Oasis ModKit* → **Launch**.
- From the **install directory** → run `RunDevKit.bat`.

Either way, the **mod selection screen** appears before the main editor. This is intentional: the ModKit boots scoped to **one mod at a time**, and the selection happens up front.

---

## 2. Create or select a mod

- **New mod** → click **+ Create New Mod** → type the mod's full display name → **Select**.
- **Existing mod** → pick it from the list → **Select**.

What happens next:

- The editor boots and mounts **only the selected mod's assets** plus the stock game content. You will *not* see other mods' assets at this stage (that's [Mod References](mod-references.md) territory).
- If the selected mod modifies original game assets, those modified versions **override** the originals during this session.
- If you later switch to a different mod (relaunch and pick another), the ModKit **automatically restores** any original assets that the previous mod had overridden, so the next mod sees a clean baseline.

> Switching mods *requires a ModKit restart*. The editor doesn't hot-swap mod scopes mid-session.

### Where your mod lives on disk (new ModKit)

```
ModKit/
├── Game/
│   ├── Content/
│   │   └── Mods/
│   │       └── <YourMod>/        ← editor-time content browser path: /Game/Mods/<YourMod>/
│   └── Saved/
│       └── Mods/
│           └── <YourMod>/
│               ├── modinfo.json  ← manifest
│               └── Assets/...    ← canonical source location for the new ModKit
```

If you're migrating an old mod from the previous layout (`Content/Mods/<YourMod>/modinfo.json`), see [Porting a mod from the old ModKit](porting-a-mod-from-old-modkit.md).

---

## 3. Use Mod Manager

**Mod Manager** is the plugin that drives every author-side task: tracking what you've changed, restoring originals, cooking, and uploading. Open it from the **main UE Editor toolbar** (its icon should sit alongside the standard Play / Build buttons).

The main panel shows:

| Section | What it's for |
| --- | --- |
| **Mod metadata** | Title, description, author, tag, version, thumbnail. These get written into `modinfo.json` and become the Workshop item's metadata. |
| **Assets to Cook** | The list of assets (relative to `Content/Mods/<YourMod>/` and any modified game assets) that will be packaged. **Only items checked here ship.** |
| **Restore Assets** | A list of stock assets your mod has modified. Selecting + **Restore Selected** reverts them on the next ModKit boot. |
| **Mod Dependencies / Import MOD** | Imports another Workshop mod as a reference. See [Mod References](mod-references.md). |
| **Save Mod** | Marks every asset in *Assets to Cook* as `ModifiedByModkit` so the editor preserves them across restarts. **Always click this after a working session** — without it, the editor's cleanup pass on next boot may delete your work. |
| **Cook and Package Mod** | Kicks off the cook → package pipeline (see §6). |
| **Upload to Workshop** | Pushes the cooked mod to Steam (see §7). |

### "Assets to Cook" — the canonical ship list

The cook pipeline only ships what's checked in *Assets to Cook*. Two implications:

1. **An asset that exists in your mod folder but isn't checked here will not be in the published mod**, even though it's on disk and visible in the editor.
2. Conversely, **checking an asset adds it to `assetsToCook` in `modinfo.json`** with its asset type (`Blueprint`, `Material`, `DataTable`, …). The cooker uses the type hint to choose the right cook path.

Get into the habit of glancing at *Assets to Cook* before every cook — it's the single place to confirm what's actually shipping.

---

## 4. Author your content

Place every new asset under:

```
Content/Mods/<YourMod>/...
```

You can mirror any internal substructure you want (`Blueprints/`, `Meshes/`, `Materials/`, `Data/`, …). Assets outside this folder are stock game assets; modifying them counts as overriding the original (allowed but use sparingly — overrides conflict with other mods that touch the same asset).

Some practical conventions:

- **Prefix Blueprint names** with something short and unique (`MM_` for "MyMod") to avoid name-collision confusion when looking at logs that mention class names.
- **Subclass over copy.** Subclassing a stock walker Blueprint is much lighter than duplicating it — your mod ships only the diff.
- **Use Data Tables / Data Assets for tunable values.** Easier to balance/patch later than hard-coded values in graphs.
- **Keep custom materials small.** The cook step bakes shader permutations; large material trees inflate cook time and `.pak` size noticeably.

### If you're building a custom map

Add the `.umap` to the **Maps to Cook** list in *Project Settings* (Edit → Project Settings → Packaging, or the dedicated Maps section depending on ModKit version). Cooked maps go into the same `.pak` as your other content. See [Loading custom maps](load-custom-maps.md) for the server-side load path.

---

## 5. Restore an asset you no longer want to override

If you modified a stock asset and want to back out:

1. Mod Manager → **Restore Assets**.
2. Select the assets to revert.
3. Click **Restore Selected**.
4. **Restart the ModKit** — the actual file restoration happens at the next boot, not immediately. Until you restart, the editor still has the modified versions in memory.

---

## 6. Cook and package

When the mod is ready to test or ship:

1. **Mod Manager → Cook and Package Mod.**
2. A **batch script window** opens and runs the UE cook + pak pipeline. This is the most important rule in the whole guide:

   > **NEVER CLOSE THE BATCH SCRIPT WINDOW MID-COOK.**
   >
   > Closing it loses the cook's intermediate state. Subsequent cooks have to re-cook everything from scratch — for a non-trivial mod, that's hours instead of minutes.

3. **First cook is slow** — up to ~2 hours depending on hardware and content volume. The cooker has to process every shader permutation and every dependent asset for the first time. Subsequent cooks are incremental and typically take a few minutes.
4. **Add custom maps to "Maps to Cook"** in *Project Settings* if your mod ships any — otherwise they won't be packaged even if they're in `assetsToCook`.

### What "cook" actually does

- Compiles every Blueprint to native bytecode.
- Bakes shader permutations for every material/usage combo.
- Strips editor-only data from each asset.
- Packages everything into a `.pak` file under your mod's `Saved/StagedBuilds/` directory (or similar — exact path varies by ModKit version).

When the script finishes successfully, the bottom of the log will show a summary line and the package path. **Don't move or rename anything in `Saved/StagedBuilds/`** — Mod Manager's upload step looks there by name.

---

## 7. Upload to Steam Workshop

Before clicking upload:

- [ ] **Title** is final (you can edit it later, but the URL slug derives from the first one).
- [ ] **Description** is detailed — list features, dependencies, server-side requirements, known issues. This is what server admins read before subscribing.
- [ ] **Thumbnail image** is selected. PNG/JPG, square aspect (Steam will crop). 512×512 is a safe minimum.
- [ ] **Category / tag** is set in the metadata.
- [ ] **Mod version** in `modinfo.json` is bumped if this is an update — Steam compares versions to decide whether subscribers get the new package.

Then **Mod Manager → Upload to Workshop**. Upload time is "a few seconds" for small mods, longer for large ones, bounded mostly by your upload bandwidth.

After upload, the Workshop item appears under your **Steam Workshop "Submissions" / "My files"** page. From there you can:

- Tweak the description and tags.
- Add screenshots and additional images.
- Manage visibility (Public / Friends-only / Hidden).
- Add **required items** (other mods players must subscribe to). This is the *display* counterpart to your `modDependencies` list in `modinfo.json`.

---

## 8. Test the cooked mod against a real server

A successful cook does not guarantee a working mod. Smoke-test it before announcing:

1. Spin up a local modded server with **only this mod** in `Mods=`. See [Host a modded server](host-a-modded-server.md).
2. Make sure your client is on the same Steam branch as the server (default for both, in current builds — no `SDKTest` opt-in required anymore).
3. Connect to the server and exercise every modded feature (placeables, items, walkers, recipes, map…).
4. Check the server log for warnings/errors during boot and during play. Things that look fine in the editor sometimes blow up on a dedicated server (`OnConstruction` ordering, replication, missing mobile/console-only fallbacks).

If something breaks: fix in the editor → cook → re-upload → bump version. Don't push fixes by overwriting the existing Workshop file silently; bumping `version` in `modinfo.json` ensures subscribers actually pull the update.

---

## 9. Publishing checklist

Before you announce a release in your community:

- [ ] Title, description, thumbnail, category set on the Workshop page.
- [ ] All required dependencies listed both as **Steam Workshop required items** *and* in your description (server admins need plain text).
- [ ] `modinfo.json` `version` bumped (and visible on the Workshop "Change Notes").
- [ ] At least one cooked → server-tested run passed for the new build.
- [ ] Screenshots / a short clip uploaded (Steam Workshop pages with media get vastly more subscribes).
- [ ] If the mod replaces or alters major game systems, **document conflicts** with other popular mods.

---

## Common pitfalls

- **"My change isn't in the cooked mod."** Asset wasn't checked in *Assets to Cook*, or you forgot to **Save Mod** before cooking. The cooker reads from the manifest, not from "what's currently dirty in the editor."
- **Cook takes hours every time.** You closed the cook window mid-cook on a previous run and lost incremental state. Run one full cook to completion to rebuild the cache, then incremental cooks will be fast again.
- **Mod uploads but subscribers don't get the update.** `version` in `modinfo.json` wasn't bumped. Steam treats same-version uploads as no-ops for subscriber clients.
- **Mod loads in editor but server fails to mount it.** Often a missing dependency (see [Mod references](mod-references.md)) or a path mismatch — the server folder under `Mist/Content/Mods/` must be named after the **Workshop ID**, not the mod's friendly name.
- **Players report missing assets after subscribing.** Custom maps not added to *Maps to Cook*, or assets present in editor but not in `assetsToCook`.
- **"Restore Assets" did nothing.** You didn't restart the ModKit afterwards — restoration is a boot-time operation.
- **Editor wipes your mod content on next launch.** You forgot to click **Save Mod**. Without the `ModifiedByModkit` flag, the editor's cleanup pass treats those assets as orphaned.

---

## Related guides

- [Mod references](mod-references.md) — using assets from another mod.
- [Loading custom maps](load-custom-maps.md) — server-side `-MapPath` setup for maps shipped in your mod.
- [Host a modded server](host-a-modded-server.md) — full server-side setup, including the `Mods=` list and dependency rules.
- [Porting a mod from the old ModKit](porting-a-mod-from-old-modkit.md) — `modKitVersion` 2 → 3 migration.
