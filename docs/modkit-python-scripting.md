# Modkit Python Scripting Guide

> Reference & how-to for the **editor-side Python scripts** in [scripts/modkit/](../scripts/modkit/), and for writing your own. Scoped to Last Oasis Modkit (Unreal Engine **4.25.4**, `Mist` project). Verify volatile Modkit-specific claims against the [#modkit channels on the official Discord](https://discord.gg/lastoasis).

The Modkit ships with the standard Unreal **Python Editor Script Plugin**, which gives you a real Python interpreter inside the editor with full access to the engine's reflection system. That's the lever that makes large-scale data extraction (Blueprints, recipes, widgets, items, placeables, …) tractable: instead of clicking through thousands of assets, you walk the Asset Registry and dump what you need.

This guide covers:

- One-time editor setup.
- Three ways to actually run a script.
- The 4 scripts in this repo, what they do, where they write, and how to point them at different output paths.
- The reflection patterns and gotchas you hit specifically in UE 4.25 (different from UE 5).
- A minimal template for writing your own extractor.
- How to feed extracted JSON into the [HTML viewers](../tools/) or the [LLM bundles](../llm/).

---

## 1. Enable Python in the Modkit (one-time)

1. Launch the Modkit and pick any mod (the Python plugin is editor-global, but the editor still needs to boot scoped to *some* mod).
2. **Edit → Plugins**.
3. Search for **Python**. Enable both:
    - **Python Editor Script Plugin**
    - **Editor Scripting Utilities** (usually already on; required by `unreal.EditorAssetLibrary`)
4. **Restart the Modkit.** Plugin enables don't take effect until restart.

Once back up, confirm Python is live:

- **Window → Developer Tools → Output Log**.
- At the bottom of the Output Log there's a small input box with a **mode dropdown** (`Cmd` / `Python` / `Python (REPL)`).
- Set it to **Python (REPL)** and type:

   ```python
   import unreal; unreal.log("hello from python")
   ```

   You should see the `hello from python` line appear in the log.

> **Python version.** UE 4.25 ships with **CPython 2.7** in its Python plugin (some patched 4.25.x builds include 3.7). The scripts in this repo are written **Py2/Py3-safe** — that's why you'll see `from __future__ import print_function`, `try/except basestring`, and `io.open(..., encoding="utf-8")` patterns. If you write your own scripts, prefer the same defensive style or you'll get nasty surprises across Modkit updates.

---

## 2. Three ways to run a script

### A) Paste into the Output Log REPL

Best for short experiments. Set the dropdown to **Python** (or **Python (REPL)**), paste lines, hit Enter. Multi-line blocks need to be wrapped in `exec(...)` or pasted as a single statement — the REPL doesn't have great multiline editing.

To run a script file from this mode, `exec` it directly:

```python
exec(open(r"C:/Users/you/Documents/Development/LastOasisModdingResources/scripts/modkit/dump_recipe_tree.py").read(), {"__name__": "__main__"})
```

The `{"__name__": "__main__"}` globals dict makes any `if __name__ == "__main__":` blocks fire. Don't pass `encoding="utf-8"` to `open()` — UE 4.25's bundled Python is 2.7 and its `open()` rejects that kwarg (use `io.open()` if you really need it; the scripts in this repo are plain ASCII, so plain `open()` is fine).

### B) Run a file via the `Cmd` mode

Best for running an existing script file without typing Python.

1. Set the Output Log dropdown to **Cmd**.
2. Type:

   ```
   py "C:/Users/you/Documents/Development/LastOasisModdingResources/scripts/modkit/dump_recipe_tree.py"
   ```

   (Note: `py` is the editor command, not the Windows `py.exe` launcher. The path is the absolute on-disk path. The dropdown **must** be on `Cmd` — pasting `py "..."` while the dropdown is on `Python` parses as Python source and raises `SyntaxError`.)

3. The script runs synchronously; the editor freezes until it's done. Watch the Output Log for progress.

### C) Run via the engine command line

Best for batch / CI-style runs (no editor UI).

```
UE4Editor.exe "<ProjectPath>\Mist.uproject" -ExecutePythonScript="C:\path\to\script.py" -unattended -nop4 -nosplash -log
```

Useful if you want to script "pull a fresh recipe dump every Modkit version bump" — but in practice most authors just use mode (B) interactively.

---

## 3. The repo's scripts, in plain English

All four live under [scripts/modkit/](../scripts/modkit/). All four default to writing to `C:/Temp/` or `<ProjectSaved>/`. **Edit the path constants near the top of each script** if you want output elsewhere; the canonical home for finished extracts is the repo's [data/](../data/) folder.

### 3.1 `export_blueprint_api.py`

**Produces:** `C:/Temp/blueprint_api.json` → curated to [data/blueprint_api.json](../data/blueprint_api.json).

**What it does.** Walks every Blueprint asset under `/Game/`, loads its generated class (the class produced when a Blueprint compiles, which carries all the runtime members), grabs the **Class Default Object (CDO)**, runs Python's `dir()` on it, and filters to public / non-`k2_` entries. For each Blueprint you get a list of the functions, properties, events, and delegates the Modkit's reflection layer exposes — the searchable Blueprint API surface.

**Knobs to know:**

- `save_path` (line 6) — where the JSON ends up.
- The `attr.startswith("_")` and `attr.startswith("k2_")` filters (line 54) — broaden these if you also want stock K2 helpers and private members.
- Wrapped in `unreal.ScopedSlowTask` so you get an in-editor cancel button (the asset count is in the thousands).

**Why CDO inspection?** In 4.25, the Python wrapper around Blueprint classes only reflects members that the engine has materialized for the default object. `dir(cls)` on the class itself is much sparser than `dir(unreal.get_default_object(cls))`. If you swap to inspecting the class directly you'll lose most of the API.

### 3.2 `export_widget_blueprints.py`

**Produces:** `C:/Temp/widget_bp_functions.json` → curated to [data/widget_bp_functions.json](../data/widget_bp_functions.json). Same shape as `blueprint_api.json` — `{ LeafName: { path, exposed_members } }`.

**What it does.** Same idea as #3.1 but scoped to **`WidgetBlueprint`** assets. Crucially, it **subtracts the `unreal.UserWidget` baseline** — `set(dir(cdo)) - set(dir(unreal.UserWidget))` — so the output only shows widget-specific additions, not the 200+ inherited UMG callables that would drown out signal.

**Knobs to know:**

- `OUT` (line 4) — output path.
- `baseline = set(dir(unreal.UserWidget))` (line 10) — if your widgets inherit from a custom intermediate base in the Mist project, expand the baseline by also subtracting `dir(<that_class>)` so its members get filtered too.
- Output is plain text grouped by widget package path, two-space-indented function names — designed for `grep`/eyeball use, not JSON processing.

### 3.3 `dump_recipes_raw.py` (low-level)

**Produces:** `<ProjectSaved>/Recipes/recipes.json` (i.e. `Mist/Saved/Recipes/recipes.json` inside the Modkit install).

**What it does.** A general-purpose CDO serializer pointed at the Mist data roots:

```
/Game/Mist/Data/Items
/Game/Mist/Data/Crafting
/Game/Mist/Data/TechTree
/Game/Mist/Data/Placeables
/Game/Mist/Data/Walkers
/Game/Mist/Data/Harvest
```

For each asset in those roots, it loads the CDO and recursively serializes every editor-readable property: scalars, enums, structs, soft-refs, hard-refs, lists, **`unreal.Map`** (handled correctly — see §4), **`unreal.Set`**, and `unreal.Text`. The output is a giant JSON blob with one entry per asset and the full property tree underneath.

**Use when:** You need the **raw shape** of an asset's data — recipe structs you've never seen before, undocumented walker stats, weird tech-tree references — and the curated dumper (#3.4) hides too much. This is the script to start from when you're reverse-engineering a new system.

**Knobs to know:**

- `SCAN_ROOTS` (line 37) — add or remove roots to broaden/narrow the walk.
- `MAX_DEPTH = 8` (line 48) — increase if deeply nested structs get truncated to `"<max-depth>"`; decrease if cycles are blowing up.
- `SKIP_NAMES` (line 50) — defensive deny-list of properties known to be expensive or recursive (`get_world`, `static_class`, …). Add to it when a new property triggers a 30-second hang.

### 3.4 `dump_recipe_tree.py` (curated)

**Produces:** `<ProjectSaved>/recipe_tree.json` → curated to [data/recipe_tree.json](../data/recipe_tree.json), consumed by [tools/recipe_viewer.html](../tools/recipe_viewer.html) and [tools/recipe_bubbles.html](../tools/recipe_bubbles.html). Also pretty-prints the full tree to the Output Log.

**What it does.** The opinionated, viewer-ready counterpart to #3.3. Knows the actual recipe schema:

| Source | Field | Meaning |
| --- | --- | --- |
| `/Game/Mist/Data/Items/...` | `recipes[]` | Each item has zero or more crafting recipes. |
| Recipe struct | `category` | Crafting-station class (`Base_C` = handcraft, `Smithing_C`, `Furnace_C`, etc.). |
| Recipe struct | `inputs` | `TMap<TSubclassOf<UMistItem>, int32>` — ingredient → required count. |
| Recipe struct | `required_unlockable` | Tech-tree node that unlocks this recipe. |
| Recipe struct | `experience_reward_crafting` | XP awarded per craft. |
| Recipe struct | `amount` / `quantity` | Output count per craft. |
| `/Game/Mist/Data/Placeables/...` | `requirements` / `full_cost` | Single `MistCraftingRequirements` struct → 'B' build menu entry. |

It groups everything by category, sorts by name, and emits both the JSON the HTML viewers expect and a chunked plaintext rendering in the Output Log.

**Knobs to know:**

- `ITEMS_PATH`, `PLACEABLES_PATH`, `CATEGORY_PATH` (lines 36–38) — change if Donkey Crew restructures `Mist/Data/`.
- `OUTPUT_JSON` (line 40) — output path.
- `CATEGORY_LABELS` (line 334) — friendly section names in the rendered output.

---

## 4. UE 4.25 Python — patterns and gotchas

These are the things that bite when writing your own scripts.

### 4.1 Generated class suffix is `_C`

A Blueprint asset at `/Game/Mist/Data/Items/Wood` has a generated class at `/Game/Mist/Data/Items/Wood.Wood_C`. Most Python helpers (`unreal.load_class`, `unreal.get_default_object`) want the **class** path, not the asset path. Append `_C` (or use `unreal.EditorAssetLibrary.load_blueprint_class(asset_path)` which does it for you).

### 4.2 CDOs are where the data lives

For Blueprint assets, *the asset itself* (`unreal.Blueprint`) carries metadata, not gameplay data. The properties you actually want are on the **Class Default Object** of the generated class:

```python
cls = unreal.EditorAssetLibrary.load_blueprint_class(asset_path)
cdo = unreal.get_default_object(cls)
value = cdo.get_editor_property("recipes")
```

This is true for items, placeables, walkers, AI, almost everything. If you load the asset directly with `load_asset` and try to read gameplay properties, you'll get `None`.

### 4.3 `unreal.Map` iterates as keys-only

The single nastiest gotcha. `TMap<K, V>` shows up as `unreal.Map` in Python. Iterating it the obvious way silently drops the values:

```python
# WRONG - yields keys only, you lose every count/amount/value
for entry in inputs:
    print(entry)

# RIGHT - explicit
for k in inputs.keys():
    v = inputs[k]
    print(k, v)

# ALSO RIGHT - if .items() is available on your build
for k, v in inputs.items():
    print(k, v)
```

This is exactly what the v9 fix in `dump_recipes_raw.py` is about: the older code iterated `unreal.Map` like a list and produced ingredient lists with no quantities. Always check for `unreal.Map` (and `unreal.Set`) **before** falling through to a generic iterable branch in your serializer — the order matters.

### 4.4 Asset Registry walks aren't free

`get_assets_by_path("/Game", recursive=True)` returns thousands of `AssetData` entries on the Modkit. Don't load every one — that's hours and gigabytes of memory. Filter first:

```python
# Filter at the registry level
all_assets = ar.get_assets_by_path("/Game/Mist/Data/Items", recursive=True)
items_only = [a for a in all_assets if a.asset_class == "Blueprint"]
```

If you need a class-based filter (e.g. only `WidgetBlueprint`), `get_assets_by_class("WidgetBlueprint", True)` is cheaper than walking everything and filtering in Python.

### 4.5 Use `ScopedSlowTask` for long walks

Long synchronous Python work freezes the editor with no feedback and no way to cancel. Wrap it:

```python
with unreal.ScopedSlowTask(len(items), "Doing the thing...") as task:
    task.make_dialog(True)  # show progress dialog with Cancel button
    for item in items:
        if task.should_cancel():
            break
        # work
        task.enter_progress_frame(1)
```

Costs nothing, gets you a real progress bar and cancel button.

### 4.6 Defensive `try/except` everywhere

The Modkit's content has a long tail of half-broken / experimental / unreferenceable assets that crash on load or property access. The repo's scripts wrap individual asset processing in `try/except` so one bad asset doesn't sink the whole walk. Do the same — log the failure, skip the asset, keep going.

### 4.7 `EditorAssetLibrary` paths are virtual, not on-disk

`/Game/Mist/Data/Items/Wood` is a content path, not a filesystem path. The on-disk file is something like `Mist/Content/Mist/Data/Items/Wood.uasset`. Don't pass on-disk paths to `load_asset` and don't expect virtual paths to work with `os.path.exists`.

### 4.8 `unreal.Text` needs special handling

Localised text properties come back as `unreal.Text`. Stringifying with `str()` works but if you skip the type check in a recursive serializer, you'll iterate the bytes of the rendered string and produce garbage.

### 4.9 Soft and hard references

- **Hard refs** (`unreal.Object`, `unreal.Class`) — `get_path_name()` is the canonical "what does this point to" string.
- **Soft refs** (`unreal.SoftObjectPath`, `unreal.SoftClassPath`) — `export_text()` gives you the canonical string form. `str()` on a soft path may produce `<wrappedstruct>`.

---

## 5. Minimal "your own extractor" template

Drop into a new `.py`, point at a Mist data root, set an output path, run via mode (B) above:

```python
# my_extractor.py - dump every asset under a /Game/Mist/Data/... root
# and for each, pull a few named properties off the CDO into JSON.

from __future__ import print_function
import io, json, os
import unreal

# --- CONFIG ----------------------------------------------------------
ROOT       = "/Game/Mist/Data/Items"          # what to walk
PROPS      = ["name", "description", "category", "weight"]  # what to pull
OUTPUT     = os.path.join(unreal.Paths.project_saved_dir(), "MyExtract.json")
# ---------------------------------------------------------------------

ar = unreal.AssetRegistryHelpers.get_asset_registry()


def safe_get(obj, name):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return None


def to_jsonable(v):
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    try:
        if isinstance(v, unreal.Text):
            return str(v)
    except AttributeError:
        pass
    try:
        return v.get_path_name()
    except Exception:
        return str(v)


def main():
    assets = ar.get_assets_by_path(ROOT, recursive=True)
    out = []

    with unreal.ScopedSlowTask(len(assets), "Extracting...") as task:
        task.make_dialog(True)
        for ad in assets:
            if task.should_cancel():
                break
            task.enter_progress_frame(1)
            try:
                cls = unreal.EditorAssetLibrary.load_blueprint_class(
                    str(ad.object_path).split(".")[0])
                if cls is None:
                    continue
                cdo = unreal.get_default_object(cls)
                if cdo is None:
                    continue
                row = {"asset": str(ad.asset_name)}
                for p in PROPS:
                    row[p] = to_jsonable(safe_get(cdo, p))
                out.append(row)
            except Exception as e:
                unreal.log_warning("skip {}: {}".format(ad.asset_name, e))

    with io.open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, indent=2, ensure_ascii=False))

    unreal.log("Wrote {} entries to {}".format(len(out), OUTPUT))


main()
```

What you'll typically swap:

- `ROOT` → another `/Game/Mist/Data/...` subtree, or `/Game/Mods/<YourMod>` to dump just your own content.
- `PROPS` → field names you've discovered with `dir(cdo)` in the REPL.
- `to_jsonable` → extend if you start hitting `unreal.Map` / `unreal.Set` / structs (copy the patterns from `dump_recipes_raw.py` §3.3).

---

## 6. Wiring extracted JSON into this repo

The end of every extractor is a JSON file in `C:/Temp/` or `<ProjectSaved>/`. To make it useful:

1. **Move it into [data/](../data/)** — that's the canonical location for extracted reference data.
2. **Update [README.md](../README.md)** with a one-line entry under the *data/* section, including how it was produced (which script, what root).
3. **If it's recipe-shaped**, the existing [tools/recipe_viewer.html](../tools/recipe_viewer.html) and [tools/recipe_bubbles.html](../tools/recipe_bubbles.html) will load it via the file picker in the header. Both expect a `recipe_tree.json`-shaped object (top-level `groups` keyed by category).
4. **If it's API/reference-shaped**, the [LLM bundles in llm/](../llm/) can be retrained on the new data — they currently consume `blueprint_api.json` and `widget_bp_functions.json` as their Blueprint surface.

---

## 7. Common pitfalls

- **"`py` is not a recognized command"** *or* **`SyntaxError: invalid syntax` on `py "..."`.** Output Log mode is set to *Python* / *Python (REPL)*, not *Cmd*. Either switch the dropdown to **Cmd**, or stay in Python mode and use `exec(open(r"...").read(), {"__name__": "__main__"})` instead — see §2.A.
- **`TypeError: 'encoding' is an invalid keyword argument for this function`.** UE 4.25 ships Python 2.7, where built-in `open()` doesn't take `encoding=`. Either drop the kwarg (the repo's scripts are plain ASCII), or use `io.open(path, encoding="utf-8")`.
- **Script runs to completion but the JSON is empty.** Almost always one of: walking the wrong root, filtering out everything (`asset_class` strings are case-sensitive in 4.25), or property names that don't match the actual struct field names. Use the REPL to `dir(cdo)` and `safe_get(cdo, "...")` interactively first.
- **Editor freezes for minutes with no feedback.** No `ScopedSlowTask`. Wrap the loop. If you must abort, the editor process can be killed safely — your script's only side effect is the JSON write at the end.
- **Recipe ingredients have items but no quantities.** Classic `unreal.Map` keys-only iteration bug. See §4.3.
- **Properties read back as `None` even though the asset clearly has them in the editor UI.** You're inspecting the asset, not the CDO. Load the generated class (`_C` suffix), then `get_default_object`.
- **Script works on first run, breaks after a Modkit update.** Donkey Crew renamed a property or moved a data root. The repo's existing scripts handle this with priority lists (e.g. `PLACEABLE_RECIPE_PROPS = ["requirements", "full_cost"]`) — copy the pattern in your own scripts.

---

## Related

- [scripts/modkit/](../scripts/modkit/) — the actual scripts.
- [data/](../data/) — outputs of the scripts, ready to consume.
- [tools/](../tools/) — HTML viewers that load the extracted JSON.
- [llm/](../llm/) — LLM bundles that cite the extracted reference data.
- [docs/modkit-guides/](modkit-guides/) — author-side guides (mod creation, packaging, hosting).
