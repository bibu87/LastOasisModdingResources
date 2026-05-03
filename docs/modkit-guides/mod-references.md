# Mod References — Using Assets From Another Mod

> **Source:** Variant of the official Donkey Crew doc [*ModKit Guide — Mods References*](https://docs.google.com/document/d/16OlJIVt5oMI5phAlqQNW070qHPVb9ajsixpNSHmyc40/). Expanded with practical workflow notes, dependency rules, and server-side caveats. Verify volatile claims against the [#modkit channels on the official Discord](https://discord.gg/lastoasis).

If you want to use, subclass, or remix an asset that ships in **another mod**, you don't copy its files — you import the whole mod into your ModKit as a **reference**. The Mod Manager pulls the cooked package down from Steam Workshop, mounts it under your editor, and lets you point Blueprints, materials, data assets, etc. at it.

This is the official, supported way to:

- Subclass a walker / item / building from another author's mod
- Re-skin or extend something without cloning the source repo
- Build a "compatibility patch" mod that depends on another mod
- Share base content (shared materials, meshes, data tables) across multiple of your own mods

---

## When to use this

| Goal | Approach |
| --- | --- |
| Use someone else's Blueprint as a parent class | **Import as reference** (this guide) |
| Make your own copy of an asset and modify it freely | Import as reference, then **clone** the asset into your own `Content/Mods/<YourMod>/` folder |
| Stop using the dependency entirely | Remove the reference from Mod Manager, then re-cook |

> **Don't** manually copy `.uasset` files out of someone else's mod into yours. They'll bring stale `Outer` paths and dependency chains that won't resolve at runtime, and you'll be redistributing their work without the cooked package metadata Steam Workshop expects.

---

## Step-by-step

1. **Find the mod's Steam Workshop ID.** Open its Workshop page; the URL ends in `?id=<MOD_ID>` (a long numeric string, e.g. `1234567890`). That number is what Mod Manager wants — not the title, not the URL.
2. **Open your mod in the ModKit.** From the launcher, pick (or create) the mod you're working on. Wait for the editor to finish loading — switching the active mod while assets are still streaming in can leave the import in a half state.
3. **Open Mod Manager.** Toolbar → **Mod Manager** icon (the plugin shipped with the ModKit). The main panel opens with your mod's metadata at the top and a *Mod Dependencies* / *Import MOD* section below.
4. **Paste the ID into "Import MOD"** and click **Add Reference**. The ModKit downloads the cooked Workshop package, unpacks it under a virtual mount point, and registers it as a dependency in your `modinfo.json` (`modDependencies` array).
5. **Use the imported assets.** They show up in the Content Browser under their original mod path (typically `Content/Mods/<OtherModName>/...`). You can:
    - Drag a Blueprint into your level / set it as a parent class
    - Reference a material, mesh, sound, or data asset
    - Right-click → **Asset Actions → Duplicate** to create your own modifiable copy under `Content/Mods/<YourMod>/`. The duplicate becomes a *modified* asset of your mod and the parent reference is preserved unless you explicitly reparent.

---

## What "reference" actually means

When Mod Manager adds a reference:

- The other mod's `.pak` is mounted **read-only** in your editor session. You see its assets but cannot save edits to them — the ModKit will reject the save and prompt you to duplicate first.
- An entry is added to `modDependencies` in your mod's `modinfo.json`. This is what tells the game (and other players) that your mod won't load without the dependency present.
- When you cook your mod, the referenced assets are **not** repackaged into your `.pak`. Only your own additions and modifications are cooked.

That last point is what makes references safe to use at scale: a 200 MB walker mod stays ~200 MB even if you depend on five other mods.

---

## Dependencies and what they mean for players & servers

### For players

Players who subscribe to your mod on Workshop will be **prompted by Steam to also subscribe to every dependency**, because the dependency IDs are written into the Workshop item metadata at upload time. They don't have to find the dependencies themselves.

If a dependency is delisted or unsubscribed later, your mod will fail to load until the chain is restored.

### For server owners

This is where things get sharper. **A server must explicitly list every mod in its `Mods=` list, including all transitive dependencies.** The server does not auto-resolve a dependency tree the way the Steam client does for subscribed players.

If your mod depends on `1234567890` and `1234567891`, and a server admin only lists your mod ID:

- The server will fail to boot
- The startup log will contain a "missing dependency" / "failed to mount referenced mod" error
- The fix is always: add the dependency IDs to `Mods=` (in MyRealm Gameplay settings, or in the server command line, depending on how the realm is launched)

When you publish a mod with dependencies, **document the full required mod list in your Workshop description** — server admins read that section before subscribing.

---

## Removing a reference

1. Open Mod Manager.
2. In the dependency list, find the imported mod and remove it.
3. **Recook your mod.** Stale dependencies left in `modinfo.json` will keep the dependency chain alive in the cooked package even if you've stopped using its assets in your editor.
4. Re-upload to Workshop (`Upload to Workshop`). The new package will have the dependency stripped from its metadata.

If you ripped a referenced asset out of your level/blueprints first but skipped recooking, your `.pak` will still advertise the dependency to Steam.

---

## Common pitfalls

- **"Add Reference does nothing."** Usually a network/SteamCMD issue. Check that Steam is running and logged in to an account that owns Last Oasis. Restart the ModKit after the reference is added — the asset mount only takes effect on the next editor boot in some versions.
- **You see the assets in Content Browser but can't drag them into a Blueprint.** Make sure the Blueprint you're editing is in your own mod's folder (`Content/Mods/<YourMod>/`) — Mod Manager scopes editing to the active mod. Editing inside another mod's folder is intentionally blocked.
- **Cooked mod is much larger than expected after adding a reference.** Likely you duplicated the dependency's assets into your mod folder instead of referencing them. Check `Assets to Cook` for unexpected `.uasset` paths and remove any you didn't intend to ship.
- **Server boot fails after you publish an update.** You added a new dependency but didn't update the server's `Mods=` list. Cross-reference the published Workshop item's required-items list against what the realm has configured.

---

## Related guides

- [How to make and upload a mod](how-to-make-and-upload-a-mod.md) — the end-to-end mod authoring loop, including where Mod Manager fits.
- [Host a modded server](host-a-modded-server.md) — how the `Mods=` list and dependency chain reach the dedicated server.
- [Porting a mod from the old ModKit](porting-a-mod-from-old-modkit.md) — `modDependencies` is one of the fields that changed shape between `modKitVersion` 2 and 3.
