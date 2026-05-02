# Loading a Custom Map on a Modded Server

> **Source:** Variant of the official Donkey Crew doc [*ModKit Guide — Load Custom Maps*](https://docs.google.com/document/d/1JT5WoJM6BI9ayoYwCUXtdR7yvZs63WL8QRpQ_Cwtj9o/). Expanded with deployment workflow, client-side caveats, and authoring notes. Verify volatile claims against the [#modkit channels on the official Discord](https://discord.gg/lastoasis).

Custom maps are still flagged as **beta** in the Modkit. They work — communities run event realms on them regularly — but the join flow has rough edges that you need to design around.

---

## Beta caveats: read these first

Custom maps are not selectable from MyRealm's normal map dropdown. They live inside a mod's content (`/Game/Mods/<YourModFolder>/<YourMapName>`) and have to be loaded with a server command-line override.

Two consequences:

1. **Joining a custom map "cold" can fail.** The first time a player tries to join a server running a custom map, their client may not have the map mod fully installed/mounted yet. Symptoms: black screen, fall-through-the-world, or a kick back to the main menu.
2. **Workshop subscription does not equal "ready to join."** Even if the player is subscribed to your map mod, the file has to be downloaded and the asset paks have to be mounted before they can join a realm using it.

The recommended workaround is also the simplest:

> **Have players join a regular (vanilla map) modded realm first**, with the same custom-map mod in its `Mods=` list. That forces the client to download and mount the mod. After they've connected once and seen the lobby, they can join the custom-map realm cleanly.

This is also why custom maps are usually scheduled as **event realms** rather than persistent ones — you can warm players up on a "lobby" realm, then point them at the event realm at start time.

---

## The server-side override

To force a server to load a custom map instead of the one configured in MyRealm, add this to its launch command line:

```
-MapPath="/Game/Mods/<YourModFolder>/<YourMapName>"
```

- `<YourModFolder>` is the mod's folder name as it appears under `Content/Mods/` — same string as the `folderName` field in `modinfo.json`.
- `<YourMapName>` is the map asset name without the extension (no `.umap`).

### Example

```
start MistServer-Win64-Shipping.exe ^
  -SteamDedicatedServerAppId=903950 ^
  -identifier="event-realm" ^
  -port=5911 -QueryPort=5961 ^
  -log -messaging -noupnp -NoLiveServer -EnableCheats ^
  -backendapiurloverride="backend.last-oasis.com" ^
  -CustomerKey=YourCustomerKey ^
  -ProviderKey=YourProviderKey ^
  -slots=100 ^
  -OverrideConnectionAddress=YourIP ^
  -noeac ^
  -MapPath="/Game/Mods/MyEventMod/Maps/EventArena01"
```

(See [Host a modded server](host-a-modded-server.md) for what the rest of the flags mean and where the keys come from.)

### Multiple realms = multiple launch lines

There is currently no per-realm map override in MyRealm; the override is purely command-line. If you run several realms on one box and only some of them use a custom map, **each realm needs its own launch script** with its own `-MapPath` (or no `-MapPath`, to fall through to the MyRealm-configured map).

This is explicitly called out in the official doc as a temporary limitation.

---

## Pre-flight checklist

Before booting an event with a custom map, walk through:

- [ ] **The map mod is in the realm's `Mods=` list** (MyRealm → Realm → Gameplay), not just on the server's filesystem.
- [ ] **`-MapPath` matches the asset path exactly.** Capitalisation matters; `/Game/Mods/myEventMod/...` will not load `/Game/Mods/MyEventMod/...`.
- [ ] **No `.umap` suffix and no leading `Content/`** — the path is the in-engine virtual path, not the on-disk path.
- [ ] **The map is in the mod's `Maps to Cook` list** in the project settings, otherwise it won't be in the cooked package even if it builds locally.
- [ ] **Players have a "warm-up" realm** they can join first to populate the mod cache. Pin that realm in your community Discord with clear "join this first" instructions.
- [ ] **Server has been restarted** since the launch line was edited — `MapPath` is read once at boot.
- [ ] **EAC is off** (`-noeac`) for any modded session — modded play and Easy Anti-Cheat don't coexist.

---

## Authoring custom maps: the WorldMachine projects

If you want to build a brand-new island/region map (not just remix an existing one), the ModKit ships with **four WorldMachine project files** in:

```
ModKit/Game/Utils/
```

These are the same project templates Donkey Crew uses internally to author Last Oasis terrain — heightmap, splat, erosion, the lot. Open them in **WorldMachine** (commercial procedural-terrain tool by World Machine Software), tweak parameters, render heightmaps and texture splats, then import the results into a new `UWorld` (`.umap`) under your mod folder.

> **WorldMachine is paid software.** It requires a valid Professional license; the free version caps render resolution far below what's usable for an LO map. If you don't have a license, you can still build maps from scratch in the editor (or import third-party heightmaps), but you'll skip the WorldMachine pipeline entirely.

If you go this route, plan for:

- **Several iteration cycles** — heightmap → import → playtest → tweak in WorldMachine → reimport
- **Long bake times** — full LO-scale heightmaps can take many minutes to render
- **Map-specific cooking** — adding the new `.umap` to `Maps to Cook` (project settings) before packaging the mod

---

## Common pitfalls

- **"My custom map mod is published, players are subscribed, but they fall through the world on join."** Almost always the cold-join problem. Send them through a vanilla-map warm-up realm first.
- **Server boots into the wrong map.** `-MapPath` typo or missing the leading `/Game/`. The server log will show what map it actually loaded near the top of the boot output — search for `LogWorld` or `Loading map`.
- **Server boots, map loads, but player kick on join.** Check that the **map mod is in `Mods=` for the realm** in MyRealm. The server-side `-MapPath` override doesn't replace the per-realm mod list; it's strictly the map-selection step.
- **Map renders but is unreachable / no spawn.** Custom maps need to define spawn data (player starts, oasis spawns) the same way stock maps do. The four WorldMachine projects in `Game/Utils` won't help here — that's a Mist-side data step, not a terrain step.

---

## Related guides

- [Host a modded server](host-a-modded-server.md) — full launch command-line reference and `Mods=` setup.
- [How to make and upload a mod](how-to-make-and-upload-a-mod.md) — `Maps to Cook`, packaging, and Workshop publishing.
- [Mod references](mod-references.md) — if your map mod depends on assets from another mod.
