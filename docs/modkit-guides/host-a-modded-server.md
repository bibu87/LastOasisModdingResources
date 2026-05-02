# Hosting a Modded Last Oasis Server

> **Source:** Variant of the official Donkey Crew doc [*ModKit Guide — 1) Host a Modded Server*](https://docs.google.com/document/d/1V8jJdzFYfUv4UTnQS7uEU99rdu9njwvoh4V5mn8L_7U/). Expanded with platform-specific install paths, full command-line reference, dependency-list rules, and a daily mod-updater script for Linux. Verify volatile claims against the [#modkit channels on the official Discord](https://discord.gg/lastoasis).

Hosting a modded server is mechanically the same as hosting a normal Last Oasis private server — same binary, same MyRealm setup — with two extras:

1. The server must be on the **`SDKTest`** Steam branch (modded builds are not compatible with the live branch).
2. The server's mod files must be present on disk **before** it boots, and the corresponding mod IDs must be listed in the realm config (`Mods=` in MyRealm Gameplay) **plus** any transitive dependencies.

This guide covers Windows and Linux. For the realm-management side (creating the realm, getting your `CustomerKey` / `ProviderKey`), start at the **MyRealm portal**: <https://myrealm.lastoasis.gg/>.

---

## Prerequisites

- A MyRealm account with a created realm. From the realm panel you'll get:
  - **CustomerKey** and **ProviderKey** — your launch script needs both.
  - The **`Mods=` Gameplay setting** — comma-separated list of Workshop IDs the realm should load.
- The dedicated server installed via SteamCMD (app `920720`, beta branch `sdktest`).
- A way to run the server binary as long-lived process — Task Scheduler / NSSM on Windows, systemd on Linux, or a TTY/screen session if you're just testing.
- Inbound firewall holes for your chosen game and query ports (5911 / 5961 in the examples below).

### Install the dedicated server (Windows)

```
steamcmd.exe +force_install_dir "C:\Steam\LastOSDK" +login anonymous +app_update 920720 -beta sdktest validate +quit
```

(This is also documented in the repo [README](../../README.md#modded-server-hosting).)

### Install the dedicated server (Linux)

```
./steamcmd.sh +force_install_dir ./LastOSDK +login anonymous +app_update 920720 -beta sdktest validate +quit
```

### Switch your **client** to `SDKTest` to be able to join

In Steam, right-click *Last Oasis* → **Properties** → **Betas** → select `SDKTest`. The client and server branches must match for modded play.

---

## Launch script (Windows example)

The official sample, expanded for clarity:

```bat
@echo off
cd /d "Mist\Binaries\Win64\"

start MistServer-Win64-Shipping.exe ^
  -SteamDedicatedServerAppId=903950 ^
  -identifier="my server" ^
  -port=5911 ^
  -QueryPort=5961 ^
  -log -messaging -noupnp ^
  -NoLiveServer ^
  -EnableCheats ^
  -backendapiurloverride="backend.last-oasis.com" ^
  -CustomerKey=YourCustomerKey ^
  -ProviderKey=YourProviderKey ^
  -slots=100 ^
  -OverrideConnectionAddress=YourIP ^
  -noeac
```

> The original doc presents this as a single line; use either form. The carat (`^`) line continuations only work in `.bat`/`.cmd` files, not interactive PowerShell. If you copy-paste into a script, save with **CRLF line endings**.

### Linux equivalent

```bash
#!/usr/bin/env bash
cd "Mist/Binaries/Linux"
./MistServer-Linux-Shipping \
  -SteamDedicatedServerAppId=903950 \
  -identifier="my server" \
  -port=5911 \
  -QueryPort=5961 \
  -log -messaging -noupnp \
  -NoLiveServer \
  -EnableCheats \
  -backendapiurloverride="backend.last-oasis.com" \
  -CustomerKey=YourCustomerKey \
  -ProviderKey=YourProviderKey \
  -slots=100 \
  -OverrideConnectionAddress=YourIP \
  -noeac
```

On Linux you also need a `steam_appid.txt` file with the contents `903950` placed next to the server binary, otherwise SteamAPI startup fails. (Windows doesn't need this — the SteamCMD install handles it.)

```
echo 903950 > steam_appid.txt
```

---

## Command-line flags, explained

| Flag | What it does |
| --- | --- |
| `-SteamDedicatedServerAppId=903950` | The game's Steam app ID — required for SteamAPI registration. |
| `-identifier="my server"` | Internal server name; used for log files and as a stable identifier across restarts. |
| `-port=5911` | UDP game port. Players connect here. |
| `-QueryPort=5961` | UDP Steam query port. Required for Steam server browser visibility. |
| `-log` | Open a separate log window (Windows) / write logs to `Saved/Logs/` (both). |
| `-messaging` | Enables UE messaging bus — needed by some monitoring tools. |
| `-noupnp` | Skip UPnP port-forward attempts. Recommended on a real server with explicit firewall rules. |
| `-NoLiveServer` | Don't try to register with the *live* matchmaking — required for modded servers, which use a different list. |
| `-EnableCheats` | Enables admin commands; mandatory for modded testing/event realms. |
| `-backendapiurloverride="backend.last-oasis.com"` | Points the server at the production backend. Leave as shown unless an admin tells you otherwise. |
| `-CustomerKey=...` | From MyRealm. Identifies the realm-owner account. |
| `-ProviderKey=...` | From MyRealm. Identifies the hosting environment. |
| `-slots=100` | Max concurrent players. |
| `-OverrideConnectionAddress=YourIP` | The public IP/hostname players will be told to reconnect to. Required if the server's autodetected address is wrong (LAN, NAT, multi-homed). |
| `-noeac` | Disable Easy Anti-Cheat. **Required for any modded server** — EAC and mods don't coexist. |
| `-MapPath="/Game/Mods/.../..."` | *Optional.* Loads a custom map instead of the MyRealm-configured one. See [Loading custom maps](load-custom-maps.md). |

---

## Getting your mods onto the server

You have two paths, depending on whether the server box has a working Steam client signed into an account that owns Last Oasis.

### Path A — Windows host with a Steam client installed (easiest)

If Steam is running on the host and logged in as an account that **owns Last Oasis** (this can be a secondary / dedicated Steam account), the server uses SteamAPI to fetch and update mods automatically based on the `Mods=` list in MyRealm.

> **The Steam account must own LO**, not just have it installed. Family-sharing doesn't count for SteamAPI workshop downloads from a server context.

### Path B — Linux, or Windows without a Steam client (manual / scripted)

SteamAPI workshop downloads aren't available, so you install and update mods yourself with **SteamCMD**.

#### One-shot manual download

```
steamcmd.exe +force_install_dir "C:\Steam\LastOSDK" +login anonymous +"workshop_download_item 903950 <MOD_ID>" +quit
```

Then move the result from:

```
C:\Steam\LastOSDK\steamapps\workshop\content\903950\<MOD_ID>\
```

into:

```
C:\Steam\LastOSDK\Mist\Content\Mods\
```

#### Scripted daily updater

Create `mymods.txt` listing every mod the server needs (including transitive dependencies):

```
login anonymous
workshop_download_item 903950 3120415400
workshop_download_item 903950 3135800212
workshop_download_item 903950 3197306614
exit
```

Wrapper script (`update-mods.bat`):

```bat
cd ./SteamCMD/
steamcmd.exe +runscript mymods.txt
xcopy "./steamapps/workshop/content/903950" "%~dp0Mist/Content/Mods/" /e /c /i
```

Linux equivalent (`update-mods.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail
cd ./SteamCMD/
./steamcmd.sh +runscript mymods.txt
cp -r ./steamapps/workshop/content/903950/* "$(dirname "$0")/Mist/Content/Mods/"
```

Wire either of these into Task Scheduler (Windows) / cron (Linux) on a daily cadence so subscriptions stay current. **Restart the server after the copy step** — the server only mounts mod paks at boot.

> The `xcopy` / `cp` step is the part that bridges SteamCMD's workshop download location into the server's actual mod directory. Easy to forget; without it, your `mymods.txt` runs successfully but the server never sees the updated paks.

---

## Mods list and dependencies

Two places carry the mod list, and both have to agree:

1. **MyRealm → Realm → Gameplay → `Mods=`** — `Mods=3120415400,3135800212,3197306614`. This is what the server publishes to clients connecting to the realm.
2. **The server filesystem** — every ID in the list above must exist as a folder under `Mist/Content/Mods/<MOD_ID>/`.

> **Dependencies do not auto-install on the server.** If mod A depends on mod B (set in `modDependencies` in mod A's `modinfo.json`, or attached as a Steam Workshop required item), you must list **both** A and B in `Mods=` *and* download both via SteamCMD. The server will fail to boot if any referenced mod is missing — check the boot log for the missing ID. See [Mod references](mod-references.md) for how dependencies get added in the first place.

### Identifying your server in the browser

There's currently no separate "modded server" tab. Modded and vanilla servers appear in the same list. Convention: **prefix your server name with `[MODDED]`** so players can tell them apart:

```
-identifier="[MODDED] my event realm"
```

---

## Verification checklist after launch

- [ ] Server log shows `LogLoad: Game Engine Initialized.` and no `error: missing mod ...` lines.
- [ ] The server appears in Steam's server browser at `<YourIP>:<QueryPort>`.
- [ ] You can connect from a client running the **`SDKTest`** branch.
- [ ] Modded content (items, walkers, recipes) actually appears in-game — not just the realm boots.
- [ ] If using a custom map, `LogWorld: ... Loading map /Game/Mods/...` near the start of the boot log matches your `-MapPath`.

---

## Common pitfalls

- **"Failed to mount mod ID …" on boot.** Almost always a missing dependency. Add the missing ID to both `Mods=` and the SteamCMD download list, restart.
- **Server boots but no mods load.** `Mods=` is empty in MyRealm, or the file paths under `Mist/Content/Mods/` don't match the listed IDs (e.g. you copied the inner folder one level too deep — there should be one folder per mod ID directly under `Mods/`).
- **Players can see the server but can't join.** Wrong branch on either side. Both client and server must be on `SDKTest`.
- **Clients connect but immediately get "version mismatch" / kicked.** A mod was updated on Workshop and the server hasn't pulled the new version yet. Run the updater script and restart the server.
- **EAC kicks players off.** Forgot `-noeac` on the launch line. EAC is incompatible with modded play.
- **Server uses the wrong public IP.** Set `-OverrideConnectionAddress=YourPublicIP`. Without it, the server may report a private/LAN address to the matchmaker and players will see "connection failed" after the lobby.

---

## Related guides

- [Loading custom maps](load-custom-maps.md) — adds `-MapPath` on top of the launch line.
- [How to make and upload a mod](how-to-make-and-upload-a-mod.md) — author side; this guide is the operator side.
- [Mod references](mod-references.md) — explains why server-side dependency lists are not auto-resolved.
- Hosting-provider-specific guides linked from the [main README](../../README.md#hosting-provider-guides).
