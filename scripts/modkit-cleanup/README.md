# Modkit Cleanup Launcher

Pre-launch cleanup for the Last Oasis Modkit. Resets the modkit to a pristine
state every time you open it, so the in-editor Mod Manager always loads your
selected mod from a clean slate — eliminating the "leftover assets from
the previously loaded mod" class of bugs.

## Why this exists

The Modkit's Mod Manager has a known inconsistency: when you swap from Mod A
to Mod B, sometimes Mod A's content (under `Game\Content\Mods\ModA\`) and its
overrides of Mist core assets are not fully removed. You then end up with
Mod A's leftover state polluting Mod B's editing session — phantom assets,
unexpected overrides on `Mist/...` files, and cook errors that don't match
what your mod actually contains.

This launcher fixes it by **always starting the editor in a pristine state**:

1. Restores every backed-up file in `Game\Content\OriginalAsset\` back to its
   original location under `Game\Content\Mist\`.
2. Removes every subfolder under `Game\Content\Mods\`.

After this runs, the editor opens with **no mod loaded**. You select your mod
inside the Mod Manager as normal — but because the disk is empty, the
manager's load runs from a clean baseline and the swap-bug can't fire.

The trade-off: you must re-select your mod in the Mod Manager every time you
open the modkit (it is no longer "remembered" between sessions).

Files about to be replaced or deleted are first moved into a timestamped
backup under `Game\Saved\ModkitCleanupBackups\` so you can recover prior
state if needed. The last 10 backup runs are kept; older ones are pruned
automatically.

## Files

| File | Purpose |
| --- | --- |
| `RunDevKit-Clean.bat` | Replacement launcher. Runs the cleanup, then starts the editor exactly as `RunDevKit.bat` does. |
| `Clean-ModkitLeftovers.ps1` | The cleanup itself. Standalone PowerShell. Defaults to dry-run; pass `-Apply` to commit. |

## Prerequisites

- Windows + PowerShell 5.1 or newer (ships with Windows 10/11).
- Last Oasis Modkit installed via Epic Games Launcher.
- The Modkit's stock `Game\RunDevKit.bat` works (you can launch the editor with it as-is).

No PowerShell execution policy change is required at the user level — the bat
invokes PowerShell with `-ExecutionPolicy Bypass` for the cleanup script only.

## Installation

1. Copy both files into the Modkit's `Game\` folder (next to the existing
   `RunDevKit.bat`):

   ```
   <Modkit install>\Game\Clean-ModkitLeftovers.ps1
   <Modkit install>\Game\RunDevKit-Clean.bat
   ```

   Default Epic install path:

   ```
   C:\Program Files\Epic Games\LastOasisModkit\Game\
   ```

2. (Recommended) Do a **dry-run first** to see what cleanup would do on your
   current state. Open PowerShell, then:

   ```powershell
   & 'C:\Program Files\Epic Games\LastOasisModkit\Game\Clean-ModkitLeftovers.ps1'
   ```

   Adjust the path for your install. You should see one or more `RESTORE`
   lines (Mist files that would be reverted) and `DELETE` lines (mod folders
   that would be removed). No changes are made — it is a dry-run.

3. If the output matches what you expect, point your desktop shortcut at
   `RunDevKit-Clean.bat` instead of `RunDevKit.bat`. Right-click your
   shortcut → Properties → change the Target to:

   ```
   C:\Program Files\Epic Games\LastOasisModkit\Game\RunDevKit-Clean.bat
   ```

   Or just double-click `RunDevKit-Clean.bat` directly when launching the
   modkit.

That's the whole installation. Every launch via `RunDevKit-Clean.bat` will
now run the cleanup automatically.

## What happens on each launch

```
RunDevKit-Clean.bat
  ├─ Detects whether UE4Editor.exe is already running. If so, skips cleanup.
  ├─ Calls Clean-ModkitLeftovers.ps1 -Apply
  │     ├─ Restores every Game\Content\OriginalAsset\* file to Game\Content\
  │     │   (modded version is moved into the timestamped backup folder)
  │     ├─ Moves every Game\Content\Mods\<X>\ folder into the backup
  │     └─ Prunes backup folders older than the most recent 10 runs
  ├─ Tees output to Game\Saved\Logs\ModkitCleanup.log
  └─ Launches UE4Editor.exe with the same args as RunDevKit.bat
```

Inside the editor: open the Mod Manager and select the mod you want to work
on. The manager will copy that mod's content out of `Saved\Mods\<Mod>\Assets\`
into `Content\Mods\<Mod>\` and apply any Mist overrides.

## Recovery

If a launch's cleanup did something unexpected, the backup folder under
`Game\Saved\ModkitCleanupBackups\<timestamp>\` mirrors the `Content\` paths
that were touched:

```
Game\Saved\ModkitCleanupBackups\2026-05-09_14-32-15\
  Mist\
    Logic\Game\OasisGameMode.uasset    <- the modded version that was replaced
  Mods\
    ModA\                              <- the entire folder that was removed
      Blueprints\...
```

Recovery is just a copy back into `Game\Content\`:

```powershell
Copy-Item -Recurse `
  'C:\Program Files\Epic Games\LastOasisModkit\Game\Saved\ModkitCleanupBackups\2026-05-09_14-32-15\*' `
  'C:\Program Files\Epic Games\LastOasisModkit\Game\Content\'
```

(Adjust the timestamp folder name and modkit path for your case.)

## PowerShell script options

`Clean-ModkitLeftovers.ps1` accepts the following parameters:

| Parameter | Default | Description |
| --- | --- | --- |
| `-ModkitRoot` | auto (parent folder of the script) | Path to the modkit install. Override if you place the script outside `Game\`. |
| `-KeepBackups` | `10` | Number of timestamped backup folders to retain. Older ones are pruned. |
| `-Apply` | (off) | Commit changes. Without this flag, the script runs in dry-run mode and only reports what it *would* do. The `RunDevKit-Clean.bat` wrapper always passes `-Apply`. |

Examples:

```powershell
# Dry-run from anywhere — uses default ModkitRoot (parent of script):
& 'C:\Program Files\Epic Games\LastOasisModkit\Game\Clean-ModkitLeftovers.ps1'

# Commit changes, keep only the last 3 backups:
& 'C:\Program Files\Epic Games\LastOasisModkit\Game\Clean-ModkitLeftovers.ps1' -Apply -KeepBackups 3

# Override the modkit path explicitly:
& 'C:\Path\To\Clean-ModkitLeftovers.ps1' -ModkitRoot 'D:\Games\LastOasisModkit' -Apply
```

## Caveats

- **Re-selection cost.** Every editor launch starts with no mod loaded. You
  must re-select your mod in the Mod Manager. This is the trade-off for
  bypassing the swap-bug.
- **Mid-session swaps.** If you swap mods *inside* a single editor session
  (without closing), this launcher cannot intercept that — only pre-launch
  cleanup runs. If you hit leftovers from a mid-session swap, close the
  editor and relaunch via `RunDevKit-Clean.bat`.
- **Editor must be closed.** The bat detects a running `UE4Editor.exe` and
  skips cleanup if found (file locks would prevent the moves anyway).
- **Multi-mod loads.** If you intentionally load multiple mods at once, you
  will need to re-select all of them after each launch.
- **Backups consume disk.** Each launch writes a new timestamped backup. The
  default `-KeepBackups 10` caps disk usage; reduce it if you launch
  frequently.
- **Files outside `Mist\` and `Mods\`.** This script does not touch any
  other folder (notably `Game\Saved\Mods\` is preserved entirely). If a mod
  modifies content elsewhere, it is out of scope.
