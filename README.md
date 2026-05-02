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

To host or join a modded server you must switch to the **`SDKTest`** Steam branch (right-click Last Oasis in Steam → Properties → Betas).

Self-host install (Windows steamcmd):
```
steamcmd.exe +force_install_dir "C:\Steam\LastOSDK" +login anonymous +app_update 920720 -beta sdktest validate +quit
```
Download a Workshop mod by ID:
```
steamcmd.exe +force_install_dir "C:\Steam\LastOSDK" +login anonymous +"workshop_download_item 903950 <MOD_ID>" +quit
```
Copy downloaded content from `C:\Steam\LastOSDK\steamapps\workshop\content\903950\` into `C:\Steam\LastOSDK\Mist\Content\Mods\`, then add `Mods=<id1>,<id2>` in your realm's Gameplay settings on MyRealm.

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

## Wikis & Reference

- [Last Oasis Fandom Wiki](https://lastoasis.fandom.com/wiki/Last_Oasis_Wiki) — game data, modules, walkers
- [Modules — Fandom Wiki](https://lastoasis.fandom.com/wiki/Modules)
- [Dedicated Server — Fandom Wiki](https://lastoasis.fandom.com/wiki/Last_Oasis_Dedicated_Server)
- [Donkey Crew — Fandom Wiki](https://lastoasis.fandom.com/wiki/Donkey_Crew)
- [PCGamingWiki — Last Oasis](https://www.pcgamingwiki.com/wiki/Last_Oasis)
- [SteamDB — Last Oasis](https://steamdb.info/app/903950/) · [Modkit 2.0 / Moving Forward patch notes](https://steamdb.info/patchnotes/14480222/)

## Community

- [Official Discord](https://discord.com/invite/lastoasis) — primary modding support venue
- [Steam Community Hub](https://steamcommunity.com/app/903950)

## Community Tools & Open Source

- [dm94/lastoasisbot](https://github.com/dm94/lastoasisbot) — Discord bot: crafting calculator, trade system, walker control, clan tech
- [Jamie96ITS/WindowsGSM.LastOasis](https://github.com/Jamie96ITS/WindowsGSM.LastOasis) — WindowsGSM plugin for dedicated server support

## Repository Contents

```
.
├── data/                                  # Extracted reference data from the Modkit
│   ├── LastOasis_APIs.json
│   ├── RecipeTree.json
│   └── widget_bp_functions.txt
├── llm/                                   # AI assistants & prompts for Modkit help
│   ├── claude/
│   │   └── claude-skill.zip               # Claude Skill bundle (SKILL.md + .skill file)
│   └── others/
│       └── last-oasis-modkit-system-prompt.zip   # Standalone system prompt for ChatGPT / any LLM
├── scripts/
│   └── modkit/                            # Editor-side Python scripts (run inside the Modkit's UE 4.25 editor)
│       ├── Python code to extract BPs and functions from the Modkit.py
│       ├── Python_Code_export_widget_bps.py
│       ├── Python_Extract_Recipes.py
│       └── Python_dump_recipes_for_tools.py
└── tools/                                 # Standalone offline HTML viewers (load JSON from data/)
    ├── recipe_bubbles.html
    └── recipe_viewer.html
```

### [data/](data/)

- [data/LastOasis_APIs.json](data/LastOasis_APIs.json) — every Blueprint in the Modkit, with all of its exposed functions (and other public members) listed for each one. Use it as a searchable reference of the full Blueprint API surface.
- [data/widget_bp_functions.txt](data/widget_bp_functions.txt) — the same idea, but for Widget Blueprints: every `WidgetBlueprint` in the Modkit and its exposed functions, with the stock `UserWidget` baseline subtracted so only the widget-specific additions remain.
- [data/RecipeTree.json](data/RecipeTree.json) — every craftable item and placeable in the Modkit, grouped by crafting category (`Base` = 'C' handcraft, `Construction` = 'B' build menu, plus stations like `Smithing`, `Furnace`, `PackageCrafting`, ...). Each entry lists ingredients (item + amount), result amount, XP reward, and the tech-tree node required to unlock it. Produced by [Python_dump_recipes_for_tools.py](scripts/modkit/Python_dump_recipes_for_tools.py); consumed by the viewers in [tools/](tools/).

### [scripts/modkit/](scripts/modkit/)

These run inside the Last Oasis Modkit editor (Window → Developer Tools → Output Log → Python). They write to `C:/Temp/` by default — edit the `save_path` / `OUT` constants if you want output elsewhere, then move the results into [data/](data/).

- [Python code to extract BPs and functions from the Modkit.py](scripts/modkit/Python%20code%20to%20extract%20BPs%20and%20functions%20from%20the%20Modkit.py) — produces `LastOasis_APIs.json`. Iterates every Blueprint asset under `/Game/`, loads its generated class, and dumps the CDO's exposed members. Filters out private (`_`) and stock K2 (`k2_`) entries.
- [Python_Code_export_widget_bps.py](scripts/modkit/Python_Code_export_widget_bps.py) — produces `widget_bp_functions.txt`. Same idea, scoped to `WidgetBlueprint` assets, and subtracts the `unreal.UserWidget` baseline so the listing only shows widget-specific callables.
- [Python_dump_recipes_for_tools.py](scripts/modkit/Python_dump_recipes_for_tools.py) — produces [`RecipeTree.json`](data/RecipeTree.json). Walks `/Game/Mist/Data/Items` (each item's `recipes` array) and `/Game/Mist/Data/Placeables` (each placeable's `requirements` / `full_cost` struct), groups everything by crafting category, and serializes a clean tree designed to feed the HTML viewers. Pretty-prints the tree to the editor's Output Log too.
- [Python_Extract_Recipes.py](scripts/modkit/Python_Extract_Recipes.py) — alternate, lower-level recipe dumper. Iterates the same data roots but serializes each asset's full CDO (every editor property, recursing through structs / `unreal.Map` / `unreal.Set`) into `<ProjectSaved>/Recipes/recipes.json`. Useful when you need the raw shape of a recipe struct rather than the curated tree above.

### [tools/](tools/)

Self-contained HTML pages — open directly in a browser, no server, no build step. Each one expects a sibling `RecipeTree.json` (or you can load any matching JSON via the file picker in the header).

- [tools/recipe_viewer.html](tools/recipe_viewer.html) — searchable, category-grouped recipe browser. Lists every recipe in the tree with its ingredients, output quantity, XP, and required tech-tree unlockable.
- [tools/recipe_bubbles.html](tools/recipe_bubbles.html) — interactive bubble / graph view of the recipe tree, useful for spotting ingredient chains and shared base resources at a glance.

### [llm/](llm/)

Drop-in prompts so you can spin up an AI assistant that already knows the Last Oasis Modkit (UE 4.25.4, `Mist` project, SDKTest branch, MyRealm, EAC quirks, etc.). Both bundles are snapshots from April 2026 — the Modkit moves quickly, so they tell users to verify volatile claims against the official Discord.

- [llm/claude/claude-skill.zip](llm/claude/claude-skill.zip) — **Claude Skill** bundle. Unzip to get `SKILL.md` (the skill instructions, with frontmatter triggers covering Modkit / SDKTest / Mist / Workshop / MyRealm / Blueprint API questions) and `last-oasis-modkit.skill` (the packaged skill file). Install in Claude Code or Claude Desktop and it auto-triggers on Last Oasis modding mentions, branching into four workflows: onboarding, reference Q&A, project coaching, and troubleshooting.
- [llm/others/last-oasis-modkit-system-prompt.zip](llm/others/last-oasis-modkit-system-prompt.zip) — **Generic system prompt** as a single Markdown file. Same domain knowledge as the Claude skill but in a portable form: paste it into a ChatGPT custom GPT's "Instructions," a Claude Project's custom instructions, the OpenAI Playground `system` message, or any other LLM that accepts a system prompt. The file's header explains each integration path.
