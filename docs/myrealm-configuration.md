# MyRealm Configuration Reference

> Field-by-field reference for the **MyRealm** portal at <https://myrealm.lastoasis.gg/>, the official Donkey Crew interface for creating and managing Last Oasis private realms (vanilla and modded). Compiled from the official mod-hosting docs and from public hosting-provider knowledge bases — see [Sources](#sources). Verify volatile claims against the live MyRealm UI; settings names occasionally drift between Last Oasis seasons.

MyRealm is the control plane for any non-official Last Oasis server. It issues the credentials your dedicated server needs (`CustomerKey` / `ProviderKey`), holds the per-realm gameplay tuning (multipliers, decay, PvP rules, …), and — critical for modders — owns the **`Mods=`** list that tells the realm which Steam Workshop mods to load.

This doc walks the portal top-down: account → realm → oases → settings → mods → automation. The companion [host-a-modded-server.md](modkit-guides/host-a-modded-server.md) covers the *server-side* equivalent (binary install, command-line flags, dependency rules).

---

## 1. Account & key workflow

When you create a MyRealm account and add your first realm, the portal generates two credentials your dedicated server needs at boot:

| Credential | Where it goes | What it identifies |
| --- | --- | --- |
| **CustomerKey** | `-CustomerKey=...` on the server launch line | The realm-owner account. |
| **ProviderKey** | `-ProviderKey=...` on the server launch line | The hosting environment (one realm-owner can have multiple providers — e.g. local box vs. rented host). |

Both are required. The server will refuse to register with the matchmaker without them. They're long opaque strings; copy them out of the MyRealm portal and paste verbatim. **Treat them like passwords** — anyone with both can stand up a server claiming to be your realm.

If a key leaks or you suspect it has, **rotate it from MyRealm Settings → API Key Management**, then update every server launch script that uses it.

---

## 2. Top-level dashboard

The dashboard lists everything you own:

- **Realms** — your created realms, with active/inactive state.
- **Oases (servers)** — the per-map server instances inside each realm.
- **Pools** — groups of oases used to organise servers (e.g. `General`, `Backup`, `Event`).
- **Statistics** — current online players, queue depth, lifetime totals.

A *realm* is the persistent shard your players see in the realm list. An *oasis* is one running server instance inside that realm — typically one per playable map. A small realm has 1–2 oases; a large one can have many.

---

## 3. Realm-level settings

These apply to the whole realm and are inherited by every oasis underneath unless explicitly overridden.

### 3.1 Identity

| Field | Type | Purpose |
| --- | --- | --- |
| **Realm Name** | text | Shown in the realm browser. |
| **Description** | text | Shown on the realm's info panel. |
| **Message of the Day** | text | Greeting / patch notes shown on player join. |
| **Discord Link** | text (URL) | Surfaced to players for community contact. |
| **Password** | text | If non-empty, players need it to join. Useful for closed beta or staged launches. |

### 3.2 Access control

| Field | Type | Purpose |
| --- | --- | --- |
| **Allowed Platforms** | list (`PC`, `Cross`, `XboxOnly`) | Which client platforms can connect. `Cross` enables PC + console crossplay. |
| **Whitelist mode** | toggle | If on, only listed SteamIDs/accounts can join. |
| **Clan Cap** (`MaxClanSize`) | number | Maximum members per clan on the realm. |
| **Realm Admins** | list | SteamIDs with admin / cheat access in-game. Required to use admin commands (works with `-EnableCheats` server flag). |

### 3.3 Hosting mode

| Field | Type | Purpose |
| --- | --- | --- |
| **Hosting Mode** | list (`Single oasis` / `Multiple oasis`) | Single = one running server for the whole realm. Multiple = several servers, one per map, with travel between them. Multi-oasis is the standard for "real" realms. |

### 3.4 Events

The three live world events (Ancient City, Worm, Asteroid) each have:

| Field | Type | Purpose |
| --- | --- | --- |
| **Enabled** | toggle | Whether the event spawns at all. |
| **Lifetime when spawned** | number (seconds) | How long the event stays live once active. |
| **Activation time** | number (seconds) | Cool-down between potential spawns. |
| **Probability of spawning** | number (0.0–1.0) | Chance of spawning when the activation timer fires. |

Modded realms running custom maps will often disable some/all of these — the events have hardcoded references to vanilla content that won't make sense in custom geography.

---

## 4. Oasis (per-server) settings

Each oasis under the realm has its own row.

| Field | Type | Purpose |
| --- | --- | --- |
| **Oasis Name** | text | Internal name; not always shown to players. |
| **Map Selection** | list | Stock LO map. Custom maps are **not** in this dropdown — they're loaded via the server's `-MapPath=` command-line flag instead; see [load-custom-maps.md](modkit-guides/load-custom-maps.md). |
| **Activation** | toggle | Whether this oasis is currently running. Toggle off to take a single map down for maintenance without taking the whole realm offline. |
| **Server Pool** | list | Which named pool this oasis belongs to. Default is `General`. Custom pools (e.g. `Event`, `Backup`) are useful for batch operations and for isolating event maps. |

---

## 5. Gameplay tuning settings

Most of the meat of MyRealm. These can be set realm-wide and (typically) overridden per-oasis. Defaults below are the values widely documented by hosting providers — official values may have shifted across seasons; treat as a starting point and verify on the live UI.

### 5.1 Multipliers

| Setting | Default | What it scales |
| --- | --- | --- |
| `ExperienceGainMultiplier` | 1 | All XP gain. |
| `HarvestQuantityMultiplier` | 1 | Quantity per harvest action. |
| `FoliageRespawnRateMultiplier` | 1 | How quickly destroyed foliage returns. |
| `ItemWeightMultiplier` | 1 | Weight of every item (lower = carry more). |
| `DehydrationRate` | 1 | Thirst tick rate. |
| `MobsNumbersMultipliers` | 1 | Density of AI spawns. |
| `MobsRespawnTimeMultipliers` | 1 | Time between AI respawns. |

### 5.2 Claim / protection (oasis politics)

| Setting | Default (s) | Meaning |
| --- | --- | --- |
| `ClaimVulnerabilityDuration` | 10800 | Window during which a claim is attackable. |
| `ClaimProtectionDuration` | 75600 | Protection window after vulnerability ends. |
| `ClaimActivationDuration` | 3600 | Time required to activate a claim. |
| `ClaimCooldownBeforeDeploy` | 7200 | Cooldown before a new claim can be placed. |
| `ClaimChanceForBonus` | 0.2 | Probability of claim bonus drops. |

### 5.3 Combat cooldowns

| Setting | Default | Meaning |
| --- | --- | --- |
| `MinCombatCooldown` | 30 s | Lower bound on combat-state timer. |
| `MaxCombatCooldown` | 300 s | Upper bound on combat-state timer. |
| `CombatCooldownWallDamaged` | 300 s | Combat state extension when a wall is damaged. |
| `CombatCooldownWallDestroyed` | 900 s | Same, on wall destruction. |
| `OneSecondsCooldownDamage` | 25 | Damage threshold that adds 1s to combat cooldown. |
| `NoBonusAfterMurderDuration` | 43200 s | Window where murderer loses bonuses. |

### 5.4 Structure decay

| Setting | Default | Meaning |
| --- | --- | --- |
| `StructureDecayMinDamagePerHour` | 300 | Floor on per-hour decay damage. |
| `StructureDecayMaxDamagePerHour` | 700 | Ceiling on per-hour decay damage. |
| `StructureDailyMaintenanceFactor` | 0.125 | Daily maintenance cost factor for owned structures. |

### 5.5 Economy / taxes

| Setting | Default | Meaning |
| --- | --- | --- |
| `FlotillaTaxRate` | 0.05 | Tax on flotilla activity. |
| `ClaimTaxRate` | 0.05 | Tax on claim revenue. |
| `SellOrdersUpfrontTax` | 0.02 | Up-front tax on listing a sell order. |
| `AuctionProlongationOnNewBidSeconds` | 180 | Time added to an auction when a new bid arrives. |
| `AuctionStartingPriceMultiplier` | 1 | Scales auction starting prices. |
| `TimeBetweenAuctionsMultiplier` | 1 | Scales pacing of auction listings. |

### 5.6 Player mechanics

| Setting | Default | Meaning |
| --- | --- | --- |
| `MaxClanSize` | (set per realm) | Players per clan. |
| `SafeLogOutTimeout` | 120 s | Time required to safe-logout normally. |
| `QuickSafeLogOutTimeout` | 20 s | Quick logout (in safe zones). |
| `AutoLogoutPeriod` | 21600 s | Auto-logout after inactivity. |
| `LogoutEnemyWalkerPeriod` | 900 s | Logout delay while on an enemy walker. |
| `MaxPlayerStat` | 100 | Stat ceiling. |
| `PlayerWeightLimitMultiplier` | 1 | Carry-weight cap multiplier. |

### 5.7 Respawn

| Setting | Default | Meaning |
| --- | --- | --- |
| `RespawnCostMultiplier` | 1 | Resource cost per respawn. |
| `RespawnTimeMultiplier` | 1 | Time penalty per respawn. |
| `RespawnOnWalkerCostMultiplier` | 1 | Walker-respawn cost. |

### 5.8 PvP toggles

| Setting | Type | Effect |
| --- | --- | --- |
| `DisableRangedDamage` | 0/1 | Disables ranged-weapon PvP damage. |
| `DisablePvpDamageForPlayers` | 0/1 | No player-vs-player damage. |
| `DisablePvpDamageForWalkers` | 0/1 | No PvP walker damage. |
| `DisablePvpDamageForStructures` | 0/1 | No PvP structure damage (PvE-friendly). |
| `PublicKillMessages` | 0/1 | Show kill notifications globally. |

### 5.9 Walker mechanics

| Setting | Default | Meaning |
| --- | --- | --- |
| `GroundToWalkerTetherHealthMulti` | 0.15 | Tether health scaling between ground and walker. |
| `WalkerSpawnpointSwitchingCooldown` | 0 | Cooldown for switching walker spawn points. |
| `JumpingRupuChance` | 0 | Toggle for the jumping-Rupu spawn variant. |

### 5.10 Global features

| Setting | Type | Effect |
| --- | --- | --- |
| `DisableGlobalChat` | 0/1 | Turns off global chat realm-wide. |

> **Inheritance.** Per-oasis settings override realm-level settings on conflicts. A change made at the realm level applies to every oasis that hasn't overridden it. **Most setting changes require a server restart to take effect** — toggling a setting in MyRealm doesn't hot-patch the running server.

---

## 6. The `Mods=` field (modded realms)

For modded realms, this is the single most important field — and it lives in **Realm → Gameplay → `Mods=`**.

```
Mods=3120415400,3135800212,3197306614
```

### Rules

1. **Comma-separated Steam Workshop IDs.** No spaces, no quotes.
2. **Every dependency must be listed explicitly.** MyRealm does not auto-resolve dependency chains. If mod A depends on mod B, both IDs go in `Mods=`. See [mod-references.md](modkit-guides/mod-references.md) for why.
3. **The IDs in `Mods=` must also exist as folders on the server's filesystem** under `Mist/Content/Mods/<MOD_ID>/`. MyRealm publishes the list to clients but does not place the files on the server box — that's SteamCMD's job. See [host-a-modded-server.md](modkit-guides/host-a-modded-server.md) for the install/update workflow.
4. **`SDKTest` Steam branch on both client and server.** Modded play is incompatible with the live branch. Players who can't see the modded server are usually on the wrong branch.
5. **EAC must be off** on the server (`-noeac` launch flag). EAC and mods are mutually exclusive.

### Common failure patterns

| Symptom | Likely cause |
| --- | --- |
| Server boots but no mods load | `Mods=` empty in MyRealm, or files not on disk under `Mist/Content/Mods/`. |
| Server fails to boot with "missing mod" log line | Dependency missing from `Mods=`. Add the missing ID, restart. |
| Players see server but get version-mismatch on join | Workshop mod was updated; server hasn't pulled the new version. Run the SteamCMD updater, restart. |
| Modded realm doesn't appear in browser at all | Realm not active in MyRealm, or wrong branch on either side (must be `SDKTest` for modded). |

### Naming convention

There is currently no "modded servers" tab in the in-game browser — modded and vanilla realms appear in the same list. Convention: prefix `[MODDED]` to your realm or oasis name so players can tell them apart.

---

## 7. Automation tab

Per-oasis, the **Automation** tab schedules wipes and decay-related events.

| Field | Type | Notes |
| --- | --- | --- |
| **Decay time** | text (`YYYY-MM-DD HH:MM` UTC) | When the next decay tick / wipe runs. **UTC, 24-hour format.** Always specify in UTC even if your players are in another timezone — getting this wrong is the most common community-confusion bug. |

The field also drives wipe scheduling for realms that wipe on a cadence — set it to the next intended wipe timestamp. Restart the server (or wait for the natural restart cycle) for the change to register.

---

## 8. Server pool assignment

Pools are an organisational layer over oases.

- Default pool is `General`.
- Custom pools (`Event`, `Backup`, `Mods-PvE`, …) let you batch-manage related oases — apply multipliers across an event's worth of servers, or temporarily swap traffic to a backup pool.
- Pools have no in-game visibility; they're purely an admin convenience.

---

## 9. End-to-end checklist for a new modded realm

1. **MyRealm → New Realm.** Set name, description, password, allowed platforms, MOTD.
2. **Note the CustomerKey and ProviderKey.** Paste both into your server launch script.
3. **Choose hosting mode** (typically *Multiple oasis* for a real realm).
4. **Add at least one oasis.** Pick a stock map; for custom maps you'll set `-MapPath=` on the launch line instead and leave the map dropdown unused.
5. **Tune gameplay settings** — at minimum, set the multipliers (XP, harvest, foliage) and PvP toggles to your desired ruleset.
6. **Realm → Gameplay → `Mods=`** — list every Workshop mod ID, including transitive dependencies.
7. **Add realm admins** by SteamID for in-game commands.
8. **Server-side**: install dedicated server on `SDKTest` branch, place mod folders under `Mist/Content/Mods/<MOD_ID>/`, build a launch script with `CustomerKey`, `ProviderKey`, `-noeac`, ports, slots — see [host-a-modded-server.md](modkit-guides/host-a-modded-server.md).
9. **Set the realm to active**, boot the server, verify it appears in the in-game realm list (on `SDKTest`).
10. **Document the required mod list** in your community Discord and on the realm's description — server admins of mirrored realms need it, and players sometimes need it for troubleshooting.

---

## 10. Common pitfalls

- **Settings change doesn't take effect.** Most settings need a server restart. Toggling in MyRealm only updates the next-boot config.
- **CustomerKey/ProviderKey leaked.** Rotate immediately from MyRealm Settings; old keys keep working until rotated.
- **Wipe happened at the wrong time.** Decay time is **UTC**, not local. Convert before you set it.
- **Mods= is set but server still fails to boot.** Mod folders aren't on disk — `Mods=` is the *announce* list, not the *install* list. Run SteamCMD to fetch each ID, copy into `Mist/Content/Mods/`.
- **Custom map doesn't load.** The map dropdown only contains stock maps. Custom maps need `-MapPath="/Game/Mods/<YourMod>/<YourMap>"` on the server launch line, not a MyRealm setting.
- **Players say "[MODDED] xyz" doesn't appear in the list.** Wrong branch on the player's side. They need to switch to `SDKTest` (Steam → Last Oasis → Properties → Betas).
- **Per-oasis override "didn't apply"** — you saved a setting at the realm level, but the oasis already has an explicit override. Check the oasis's own settings tab; explicit overrides win.

---

## Sources

This reference is community-compiled. Last Oasis itself doesn't publish a single MyRealm settings spec; this doc consolidates from:

- The official Donkey Crew mod-hosting doc — [ModKit Guide — 1) Host a Modded Server](https://docs.google.com/document/d/1V8jJdzFYfUv4UTnQS7uEU99rdu9njwvoh4V5mn8L_7U/) (and its expanded variant in this repo: [host-a-modded-server.md](modkit-guides/host-a-modded-server.md)).
- [Pingperfect — MyRealm Explained](https://pingperfect.com/knowledgebase/926/Last-Oasis--MyRealm-Explained.html) — top-level UI structure, automation tab.
- [Pingperfect — Realm Setup and Configuration](https://pingperfect.com/knowledgebase/924/Last-Oasis--Realm-Setup-and-Configuration.html) — gameplay tuning settings, defaults.
- [GTXGaming — How to setup your Last Oasis Realm](https://www.gtxgaming.co.uk/clientarea/knowledgebase/746/How-to-setup-your-Last-Oasis-Realm.html) — credential workflow.
- [GPORTAL Wiki — Last Oasis](https://www.g-portal.com/wiki/en/last-oasis/) — provider-side setup notes.
- The [MyRealm portal](https://myrealm.lastoasis.gg/) itself — for any field the above didn't cover, refer to the live UI.

When the live UI and this doc disagree, the live UI wins. PR welcome.

---

## Related

- [Host a modded server](modkit-guides/host-a-modded-server.md) — server-side install, launch flags, dependency-list rules.
- [Loading custom maps](modkit-guides/load-custom-maps.md) — `-MapPath=` for maps that aren't in the dropdown.
- [Mod references](modkit-guides/mod-references.md) — why `Mods=` must list every dependency explicitly.
- [How to make and upload a mod](modkit-guides/how-to-make-and-upload-a-mod.md) — author side; this doc is the operator side.
- Hosting-provider-specific guides linked from the [main README](../README.md#hosting-provider-guides).
