# UAsset diagnostic + recovery tools

A small toolkit for inspecting and recovering UE4 `.uasset` files when the Modkit's load + re-save cycle damages assets. Built while recovering data from a workshop mod after a USTRUCT rename in the engine's C++ silently zeroed all serialized struct values on load.

Standard library Python only — no `pip install`. Targets the Modkit's UE 4.25 package format (file version 518).

## At a glance

| Script | Purpose |
| --- | --- |
| [`compare_workshop_pak.py`](compare_workshop_pak.py) | Compare every .uasset in a workshop pak against the live project files. Triages results into MISSING / SHRUNK / STRUCT_RENAMED / DIFF / IDENTICAL. **Start here** when a port looks wrong. |
| [`dump_header.py`](dump_header.py) | Dump the .uasset header (name table, imports, exports) as readable text. Diff two versions to see what was added or removed structurally. |
| [`dump_props.py`](dump_props.py) | Decode the tagged property bag of each export — actual field values, struct contents, array entries. Use this to see the data, not just the schema. |
| [`patch_struct_rename.py`](patch_struct_rename.py) | Recover an asset whose struct was renamed in C++ without a CoreRedirect. Renames a single name-table entry in the original .uasset and fixes all file offsets. |

---

## When to reach for these

The Modkit's editor will load assets that reference renamed/removed C++ types, but it can't deserialize the affected property data — so it loads the asset with default values and re-saves it that way. The original data is lost from the live file. A few common symptoms:

- A data asset opens with empty arrays where it used to have entries.
- A Blueprint loses inherited-component overrides (parent class still has the components, but the per-child tweaks are gone).
- File size dropped dramatically on a recent re-save.
- Editor logs warnings about unknown structs / missing classes.

The original `.uasset` data is usually still recoverable from the workshop pak archive (`Saved/Mods/<Mod>/<id>.zip`), which the Modkit downloads and keeps as a snapshot of the published version.

---

## The recovery workflow

### 1. Triage with `compare_workshop_pak.py`

```
python compare_workshop_pak.py \
    "D:/Program Files/Epic Games/LastOasisModkit/Game/Saved/Mods/<Mod>/<id>.zip" \
    "D:/Program Files/Epic Games/LastOasisModkit/Game"
```

Output groups every asset into one of:

- `MISSING` — the asset was published but is gone from the live project. Restore from the pak.
- `SHRUNK` — the live file is at least 10% smaller. Strong signal of property loss; needs investigation.
- `STRUCT_RENAMED` — the original referenced a known-renamed struct (set the marker via `--struct-marker`) that no longer appears in the live file. Almost always recoverable with `patch_struct_rename.py`.
- `DIFF` — files differ but sizes are close. Usually a benign editor re-save (slight format updates, normalised offsets).
- `IDENTICAL` — counted only.

Pass `--struct-marker <name>` (repeatable) to detect different rename patterns.

### 2. Inspect what was lost

For any flagged file, extract the original from the pak and dump both versions side-by-side:

```powershell
# Extract the original
Add-Type -AssemblyName System.IO.Compression.FileSystem
$z = [System.IO.Compression.ZipFile]::OpenRead('D:/.../<id>.zip')
$entry = $z.Entries | ? { $_.FullName -like '*Path/MyAsset.uasset' }
[System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, 'orig.uasset', $true)
$z.Dispose()
```

```bash
# Header diff (what tables/structs changed)
python dump_header.py orig.uasset curr.uasset
git diff --no-index orig.uasset.txt curr.uasset.txt

# Property bag diff (what field values were lost)
python dump_props.py orig.uasset > orig.props.txt
python dump_props.py curr.uasset > curr.props.txt
git diff --no-index orig.props.txt curr.props.txt
```

The header diff shows whether names/imports/exports were dropped. The property diff shows whether values inside surviving exports were defaulted (e.g. a `DeckLocation: Vector(370,-120,0)` becoming `Vector(0,0,0)`).

### 3. Recover

The recoverability depends on what kind of damage you're looking at:

#### STRUCT_RENAMED files — auto-recoverable

When a USTRUCT got renamed in C++ (e.g. `OldStructName` → `NewStructName`) and there's no CoreRedirect set up for the rename, the engine fails to deserialize affected property data and re-saves with defaults. As long as the new struct has the same field layout, `patch_struct_rename.py` recovers everything cleanly:

```
python patch_struct_rename.py orig.uasset patched.uasset OldStructName NewStructName
python dump_props.py patched.uasset    # verify values are preserved
```

Then **close the editor first** (running editors will overwrite the file with their stale in-memory copy) and install the patched file in **both** of these locations — the Modkit syncs from `Saved/.../Assets/...` to `Content/...` on load:

```
Game/Content/Mods/<Mod>/Path/MyAsset.uasset
Game/Saved/Mods/<Mod>/Assets/Mods/<Mod>/Path/MyAsset.uasset
```

Reopen the editor, verify in the asset inspector, then save from inside the editor so it gets re-serialized canonically.

#### Other shrunk files — usually not auto-recoverable

Other shrinkage patterns require manual fixes case by case:

- **Blueprint lost component overrides** (parent class still has them): the BP loads fine but uses parent defaults instead of variant-specific tweaks. Recovery: open the BP, select each inherited component, re-enter the override values from the dumped originals. Tedious.
- **Engine schema deprecated fields** (e.g. damage stats removed from a component class): not recoverable — the engine no longer has anywhere to store the values. Likely moved elsewhere in a newer system.
- **Function graphs lost K2Nodes** (referenced classes/assets moved or removed): may need a `PackageRedirects` entry in `Game/Config/DefaultEngine.ini`, or full graph rewrite if the dependencies are gone.
- **Material instance lost texture refs**: probably benign — current texture set works; only specific parameters are gone.

`dump_header.py` and `dump_props.py` are the right tools to figure out which of these patterns applies. Use the lost-imports / lost-properties information to decide whether to file an upstream issue, manually patch in the editor, or accept the loss.

---

## Notes on the Modkit's UE 4.25 package format

A few quirks you'll only hit if you read the parser code:

- `FCompressedChunk` serializes as **20 bytes** per entry in this build, not the documented 16. The patcher hardcodes this.
- The engine writes a `LocalizationId` FString right after `NameOffset` (added in `VER_UE4_ADDED_PACKAGE_OWNER` = 518). Easy to miss — without it the rest of the header walk drifts and reads garbage.
- `FName` hashes (`uint16` non-case-preserving + `uint16` case-preserving) sit after each name's FString from `VER_UE4_NAME_HASHES_SERIALIZED` = 504 onwards. The loader recomputes them from the string anyway, so wrong hashes are tolerated; the patcher leaves the originals in place after a rename.
- Property tags use FName *indices* (not strings), so renaming an entry in the name table preserves all references to that name. That's what makes `patch_struct_rename.py` viable: change the string at the index, the property bag still resolves correctly.

---

## Limitations

- These tools only target the Modkit's UE 4.25 package format. Older or newer engine versions need different header walks.
- The patcher only handles single-name renames where the new struct has identical field layout. If the new struct added/removed fields, UE will still skip those tags on load.
- The property dumper handles common types but not the entire UE4 property zoo. Unknown types are reported as raw byte hex dumps (which is usually enough to spot data presence vs. absence).
- These don't replace UE's built-in asset diff (`UE4Editor.exe Game.uproject -diff <left> <right>`) — that one understands BP graphs, materials, and other complex assets natively. But the built-in diff requires both files to load cleanly inside the project, which is exactly the situation that breaks down when assets are damaged.
