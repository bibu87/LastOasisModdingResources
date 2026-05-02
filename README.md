# Last Oasis Modding Resources

A curated index of resources for modding [Last Oasis](https://store.steampowered.com/app/903950/Last_Oasis/) — the nomadic survival MMO by Donkey Crew. The official Modkit was released in April 2024 (with Modkit 2.0 following alongside Season 6) and is built on Unreal Engine 4.25.4.

## Official Links

- **Modkit Download (Free)** — [Last Oasis ModKit on Epic Games Store](https://store.epicgames.com/en-US/p/last-oasis-modkit)
- **Official Modkit Resources (Google Drive)** — [Modkit assets, samples & docs](https://drive.google.com/drive/folders/1QqS5Z32g07FLpTja2g6oCUJ3YeJnqND1)
- **Official Discord** — [discord.gg/lastoasis](https://discord.gg/lastoasis) — dedicated channels for ModKit assistance, mod development, and documentation
- **Modkit Announcement (Steam News)** — [Announcing the Last Oasis Modkit](https://store.steampowered.com/news/app/903950/view/4192362393727227355)
- **Dev Tracker** — [Modkit announcement on devtrackers.gg](https://devtrackers.gg/last-oasis/p/5481db21-announcing-the-last-oasis-modkit)
- **MyRealm Portal** — [myrealm.lastoasis.gg](https://myrealm.lastoasis.gg/) — manage custom realms (add `Mods=[id,id,...]` under Realm → Gameplay)
- **Official Support** — [Last Oasis Zendesk](https://lastoasis.zendesk.com/)

## Mod Distribution

- **Steam Workshop** — [Last Oasis Workshop hub](https://steamcommunity.com/app/903950/workshop/) · [About the Workshop](https://steamcommunity.com/workshop/about/?appid=903950)

## Video Tutorials

- [Last Oasis ModKit Tutorial — Creating a Walker](https://www.youtube.com/watch?v=4An9xyeI5Lc) — crash course on building a custom walker in the Modkit (note: the video calls it UE5; the Modkit is actually UE 4.25.4)
- [Last Oasis Modkit Guide — How to Download & Basic Tips](https://www.youtube.com/watch?v=ul0IOHPTYxw)
- [How to Play the Last Oasis Modded Branch](https://www.youtube.com/watch?v=3QYgWBzYzXI) — joining `SDKTest` modded servers
- [Tutorial: How to create a server with mods on Linux](https://m.youtube.com/watch?v=4J5es7emLyc) — server-side mod setup
- [LAST OASIS — Modkit Announcement](https://www.youtube.com/watch?v=5iAl_bPbu4E)
- [Last Oasis Isn't Dead Yet — Season 6 and Modkit Announced](https://www.youtube.com/watch?v=54I2IwbrcjM)
- [Everything on Last Oasis Classic (LOC)](https://www.youtube.com/watch?v=VzUD4T5XmTs)
- [Last Oasis S6 playlist](https://www.youtube.com/playlist?list=PL8y1rb7wU7yYhcDH2_Fa_ZRazH5MYX4SA)

## Modded Server Hosting

To host or join a modded server: switch to the **`SDKTest`** Steam branch (right-click Last Oasis in Steam → Properties → Betas), self-host the dedicated server (app `920720`, branch `sdktest`), drop your Workshop mods under `Mist/Content/Mods/`, and list their IDs in `Mods=` under your realm's Gameplay settings on MyRealm. Full walkthrough — install, launch flags, dependency rules, daily mod-updater scripts — at [docs/modkit-guides/host-a-modded-server.md](docs/modkit-guides/host-a-modded-server.md). MyRealm field-by-field reference at [docs/myrealm-configuration.md](docs/myrealm-configuration.md).

### Hosting provider guides
- [GTXGaming — How to install Workshop mods on a Last Oasis server](https://www.gtxgaming.co.uk/clientarea/index.php?rp=/knowledgebase/894/How-to-install-Workshop-mods-on-your-Last-Oasis-dedicated-game-server.html)
- [GTXGaming — How to setup your Last Oasis Realm](https://www.gtxgaming.co.uk/clientarea/knowledgebase/746/How-to-setup-your-Last-Oasis-Realm.html)
- [BisectHosting — Install mods on a Last Oasis server](https://www.bisecthosting.com/clients/index.php?rp=/knowledgebase/1770/How-to-install-mods-on-a-Last-Oasis-server.html)
- [ZAP-Hosting — Create a new Realm](https://zap-hosting.com/guides/docs/lastoasis-createrealm/)
- [Pingperfect — Realm Setup and Configuration](https://pingperfect.com/knowledgebase/924/Last-Oasis--Realm-Setup-and-Configuration.html)
- [Pingperfect — MyRealm Explained](https://pingperfect.com/knowledgebase/926/Last-Oasis--MyRealm-Explained.html)
- [GPORTAL Wiki — All Server Settings](https://www.g-portal.com/wiki/en/last-oasis/)
- [Survival Servers — How to Create a Last Oasis Server](https://www.survivalservers.com/wiki/index.php?title=How_to_Create_a_Last_Oasis_Server_Guide)
- [IONOS — Create a Last Oasis private server](https://www.ionos.com/digitalguide/server/know-how/create-last-oasis-private-server/)
- [Official — Dedicated Server Installation](https://lastoasis.zendesk.com/hc/en-us/articles/360043917851-Last-Oasis-Dedicated-Server-Server-Installation)

## Community

- [Official Discord](https://discord.com/invite/lastoasis) — primary modding support venue
- [Steam Community Hub](https://steamcommunity.com/app/903950)

## Community Tools & Open Source

- [dm94/lastoasisbot](https://github.com/dm94/lastoasisbot) — Discord bot: crafting calculator, trade system, walker control, clan tech
- [Jamie96ITS/WindowsGSM.LastOasis](https://github.com/Jamie96ITS/WindowsGSM.LastOasis) — WindowsGSM plugin for dedicated server support

## Repository Contents

```
.
├── data/         # Extracted reference data from the Modkit (JSON dumps)
├── docs/         # Guides & reference docs
├── llm/          # Drop-in AI assistant prompts
├── scripts/      # Host-side Python scripts (migration, Workshop recovery)
│   └── modkit/   # Editor-side Python scripts (run inside the UE 4.25 editor)
└── tools/        # Self-contained offline HTML viewers
```

### [`data/`](data/)

| File | Contents |
| --- | --- |
| [`LastOasis_APIs.json`](data/LastOasis_APIs.json) | Every Blueprint in the Modkit with its CDO-exposed members — searchable Blueprint API surface. |
| [`widget_bp_functions.txt`](data/widget_bp_functions.txt) | Every `WidgetBlueprint` with the stock `UserWidget` baseline subtracted (only widget-specific additions). |
| [`RecipeTree.json`](data/RecipeTree.json) | Every craftable item & placeable, grouped by crafting category (`Base` = handcraft, `Construction` = build menu, plus stations). Each entry: ingredients, output amount, XP, required tech-tree unlock. Consumed by [`tools/`](tools/). |

### [`docs/`](docs/)

Guides and reference docs not covered by the official Drive material.

- [`docs/modkit-python-scripting.md`](docs/modkit-python-scripting.md) — UE 4.25 Python plugin setup, the four extractor scripts in [`scripts/modkit/`](scripts/modkit/), reflection gotchas (CDOs, `unreal.Map` keys-only iteration, `_C` suffixes), and a "your own extractor" template.
- [`docs/myrealm-configuration.md`](docs/myrealm-configuration.md) — field-by-field reference for the [MyRealm portal](https://myrealm.lastoasis.gg/): identity, access, hosting mode, events, gameplay tuning (multipliers/claims/combat/decay/economy/PvP), the `Mods=` field, end-to-end checklist for a new modded realm.
- [`docs/modkit-guides/`](docs/modkit-guides/) — expanded community variants of the [five official Donkey Crew Modkit guides](https://drive.google.com/drive/folders/1QqS5Z32g07FLpTja2g6oCUJ3YeJnqND1) (mod authoring, hosting, custom maps, mod references, v2→v3 porting). [Index](docs/modkit-guides/README.md).

### [`scripts/`](scripts/)

Standalone Python 3 scripts that run **on the host** (not inside the Modkit's editor). Both default to dry-run and produce a backup zip before any change.

- [`scripts/migrate_mod_v2_to_v3.py`](scripts/migrate_mod_v2_to_v3.py) — stage an existing v2 mod (assets at `Content/Mods/<Mod>/`) for the new Modkit.
- [`scripts/recover_mod_from_workshop.py`](scripts/recover_mod_from_workshop.py) — recover a Workshop-cached mod (zip at `Saved/Mods/<Mod>/<ID>.zip`) into editable form.

Quick reference: [`scripts/README.md`](scripts/README.md). Full guide and GC-trap rationale: [`docs/modkit-guides/porting-a-mod-from-old-modkit.md`](docs/modkit-guides/porting-a-mod-from-old-modkit.md).

### [`scripts/modkit/`](scripts/modkit/)

Editor-side Python that walks the Modkit's Asset Registry and dumps Blueprint / Widget / Recipe data — the source of the JSON in [`data/`](data/). Run inside the editor via **Output Log → Cmd → `py "<path>"`**.

Quick reference (per-script knobs, output paths, gotchas): [`scripts/modkit/README.md`](scripts/modkit/README.md). Full setup, three ways to run, and a minimal extractor template: [`docs/modkit-python-scripting.md`](docs/modkit-python-scripting.md).

### [`tools/`](tools/)

Self-contained HTML pages — open directly in a browser, no server, no build step. Each loads a sibling `RecipeTree.json` (or any matching JSON via the in-page file picker).

- [`tools/recipe_viewer.html`](tools/recipe_viewer.html) — searchable, category-grouped recipe browser.
- [`tools/recipe_bubbles.html`](tools/recipe_bubbles.html) — interactive bubble/graph view of the recipe tree.

### [`llm/`](llm/)

Drop-in prompts that pre-load an AI assistant with Last Oasis Modkit knowledge (UE 4.25.4, `Mist`, `SDKTest`, MyRealm, EAC quirks). Snapshots from April 2026 — both prompts tell the LLM to verify volatile claims against the official Discord.

- [`llm/claude/claude-skill.zip`](llm/claude/claude-skill.zip) — **Claude Skill** bundle (`SKILL.md` + `.skill`). Auto-triggers on LO modding mentions in Claude Code or Claude Desktop.
- [`llm/others/last-oasis-modkit-system-prompt.zip`](llm/others/last-oasis-modkit-system-prompt.zip) — portable system prompt. Paste into a ChatGPT custom GPT, a Claude Project, the OpenAI Playground, or any LLM that accepts a system prompt.
