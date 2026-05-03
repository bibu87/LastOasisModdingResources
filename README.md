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
- [How to Play the Last Oasis Modded Branch](https://www.youtube.com/watch?v=3QYgWBzYzXI) — joining modded servers (predates the change that lifted the `SDKTest` Steam-branch requirement; the default branch is fine now)
- [Tutorial: How to create a server with mods on Linux](https://m.youtube.com/watch?v=4J5es7emLyc) — server-side mod setup
- [LAST OASIS — Modkit Announcement](https://www.youtube.com/watch?v=5iAl_bPbu4E)
- [Last Oasis Isn't Dead Yet — Season 6 and Modkit Announced](https://www.youtube.com/watch?v=54I2IwbrcjM)
- [Everything on Last Oasis Classic (LOC)](https://www.youtube.com/watch?v=VzUD4T5XmTs)
- [Last Oasis S6 playlist](https://www.youtube.com/playlist?list=PL8y1rb7wU7yYhcDH2_Fa_ZRazH5MYX4SA)

## Modded Server Hosting

To host or join a modded server: self-host the dedicated server (Steam app `920720`), drop your Workshop mods under `Mist/Content/Mods/`, and list their IDs in `Mods=` under your realm's Gameplay settings on MyRealm. The default branch supports modded play — no Beta/SDKTest opt-in needed. Full walkthrough — install, launch flags, dependency rules, daily mod-updater scripts — at [docs/modkit-guides/host-a-modded-server.md](docs/modkit-guides/host-a-modded-server.md). MyRealm field-by-field reference at [docs/myrealm-configuration.md](docs/myrealm-configuration.md).

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
├── data/             # Extracted reference data from the Modkit (JSON dumps)
├── docs/             # Guides & reference docs
├── llm/              # Drop-in AI assistant prompts
├── scripts/          # Host-side Python scripts (migration, Workshop recovery)
│   ├── modkit/       # Editor-side Python scripts (run inside the UE 4.25 editor)
│   └── uasset/       # UAsset header/property dumpers + struct-rename patcher
└── tools/            # Self-contained offline HTML viewers
```

Each folder has its own README with details. The summary below is just a pointer table.

| Folder | What's there | Details |
| --- | --- | --- |
| [`data/`](data/) | Extracted JSON dumps of the Modkit's Blueprints, Widgets, and recipes. | [`data/README.md`](data/README.md) |
| [`docs/`](docs/) | Modkit Python scripting guide, MyRealm configuration reference, plus expanded variants of the five official Donkey Crew guides under [`docs/modkit-guides/`](docs/modkit-guides/). | [`docs/README.md`](docs/README.md) |
| [`scripts/`](scripts/) | Interactive wizard ([`mod_workflow.py`](scripts/mod_workflow.py)) that walks a Last Oasis mod from any starting state through Cook + Upload to Steam Workshop. | [`scripts/README.md`](scripts/README.md) |
| [`scripts/modkit/`](scripts/modkit/) | Editor-side Python that runs inside the Modkit's UE 4.25 editor — walks the Asset Registry to produce the dumps in [`data/`](data/). | [`scripts/modkit/README.md`](scripts/modkit/README.md) |
| [`scripts/uasset/`](scripts/uasset/) | Diagnostic + recovery tools for `.uasset` files damaged by upstream renames or migration: workshop-pak triage, header/property dumpers, struct-rename binary patcher. | [`scripts/uasset/README.md`](scripts/uasset/README.md) |
| [`tools/`](tools/) | Self-contained offline HTML viewers for the recipe data. Open in any browser, no build step. | [`tools/README.md`](tools/README.md) |
| [`llm/`](llm/) | Drop-in prompts that pre-load an AI assistant with Modkit knowledge. Claude Skill bundle and a portable system prompt for any other LLM. | [`llm/README.md`](llm/README.md) |
