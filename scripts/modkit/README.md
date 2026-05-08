# Editor-side Python scripts

These run **inside the Modkit's UE 4.25 editor** — they use the engine's `unreal` Python module to walk the Asset Registry and serialize Blueprint / Item / Recipe data.

For host-side scripts (mod migration, workshop recovery), see [`../`](../).

## One-time setup

1. Modkit → **Edit → Plugins** → enable **Python Editor Script Plugin** and **Editor Scripting Utilities**.
2. Restart the Modkit.
3. **Window → Developer Tools → Output Log** to see script output.

## Running a script

In the Output Log's bottom input box, set the dropdown to **Cmd** and run:

```
py "C:/path/to/scripts/modkit/<script>.py"
```

Or set it to **Python (REPL)** and paste code interactively.

> **Editor freezes during the run** — this is normal. Each script wraps long walks in `unreal.ScopedSlowTask` so you get an in-editor progress dialog with a Cancel button.

## At a glance

| Script | Output | What it dumps |
| --- | --- | --- |
| [`export_blueprint_api.py`](export_blueprint_api.py) | `C:/Temp/LastOasis_APIs.json` | Every Blueprint under `/Game/`, with all CDO-exposed members. |
| [`export_widget_blueprints.py`](export_widget_blueprints.py) | `C:/Temp/widget_bp_functions.txt` | Every `WidgetBlueprint`, with the stock `UserWidget` baseline subtracted. |
| [`dump_recipe_tree.py`](dump_recipe_tree.py) | `<ProjectSaved>/RecipeTree.json` | Curated recipe tree grouped by crafting category, designed for the HTML viewers in [`../../tools/`](../../tools/). |
| [`dump_recipes_raw.py`](dump_recipes_raw.py) | `<ProjectSaved>/Recipes/recipes.json` | Raw, lower-level CDO dump of every asset under `/Game/Mist/Data/{Items,Crafting,TechTree,Placeables,Walkers,Harvest}`. |

Default output paths are in constants near the top of each file (`save_path`, `OUT`, `OUTPUT_PATH`, `OUTPUT_JSON`) — edit them if you want output elsewhere. Curated outputs from the four scripts live in [`../../data/`](../../data/).

---

## `export_blueprint_api.py`

Walks every Blueprint asset under `/Game/`, loads its generated class (`<path>_C`), grabs the **Class Default Object**, and lists each member that survives the `_`/`k2_` filters. The CDO is the only place UE 4.25's Python wrapper materializes most BP members — `dir(cls)` directly is much sparser.

**Knobs:** `save_path` (line 6), the `_`/`k2_` filter (line 54).

---

## `export_widget_blueprints.py`

Same idea, scoped to `WidgetBlueprint` assets, with `set(dir(unreal.UserWidget))` subtracted as a baseline so you only see widget-specific additions (not the 200+ inherited UMG callables).

**Knobs:** `OUT` (line 3), the `baseline` set (line 10) — extend it with your project's intermediate widget base classes for tighter output.

---

## `dump_recipe_tree.py`

Opinionated recipe extractor. Knows the Mist schema:
- Items have `recipes[]` with `category`, `inputs` (`TMap<UClass*, int>`), `required_unlockable`, `experience_reward_crafting`, output `amount`.
- Placeables have a single `requirements` / `full_cost` struct → 'B' build menu entry.

Groups by category, sorts by name, emits both JSON for the [HTML viewers](../../tools/) and a chunked plaintext rendering in the Output Log.

**Knobs:** `ITEMS_PATH`, `PLACEABLES_PATH`, `CATEGORY_PATH`, `OUTPUT_JSON` (lines 36–40), `CATEGORY_LABELS` (line 334).

---

## `dump_recipes_raw.py`

General-purpose CDO serializer pointed at the Mist data roots — recursively dumps every editor-readable property (scalars, enums, structs, soft-refs, hard-refs, lists, **`unreal.Map`**, **`unreal.Set`**, `unreal.Text`). Use when reverse-engineering a system the curated dumper above hides too much of.

**Knobs:** `SCAN_ROOTS` (line 37), `MAX_DEPTH = 8` (line 48), `SKIP_NAMES` (line 50).

> **Why two recipe scripts?** The curated one feeds the HTML viewers (clean, opinionated). The raw one is for exploration — when you spot something weird in the curated output and need the underlying struct shape.

---

## UE 4.25 Python gotchas (the short list)

- **Generated class suffix is `_C`** — `unreal.load_class(path + "_C")`, or use `unreal.EditorAssetLibrary.load_blueprint_class(asset_path)`.
- **CDOs are where the data lives** — `unreal.get_default_object(cls).get_editor_property("name")`. Loading the asset directly returns `None` for gameplay properties.
- **`unreal.Map` iterates as keys-only** — you'll silently lose values. Use `m.keys()` then `m[k]`, or `m.items()`.
- **Asset Registry walks aren't free** — filter at the registry level (`get_assets_by_class`), don't load every asset.
- **`try/except` per asset** — Modkit content has a long tail of half-broken assets that crash on load.

Full setup, gotchas, and a "your own extractor" template: [docs/modkit-python-scripting.md](../../docs/modkit-python-scripting.md).
