# Data

Extracted reference data from the Last Oasis Modkit (UE 4.25.4). All files in this folder are produced by the editor-side scripts in [`../scripts/modkit/`](../scripts/modkit/) — re-run those scripts inside the Modkit to refresh the dumps after a Modkit update.

## Files

All three are JSON, indent=2, snake_case names.

| File | Produced by | Description |
| --- | --- | --- |
| [`blueprint_api.json`](blueprint_api.json) | [`export_blueprint_api.py`](../scripts/modkit/export_blueprint_api.py) | Every Blueprint under `/Game/`, with all CDO-exposed members per class. Filters out private (`_`) and stock K2 (`k2_`) entries. Searchable Blueprint API surface. Shape: `{ ClassName: { path, exposed_members } }`. |
| [`widget_bp_functions.json`](widget_bp_functions.json) | [`export_widget_blueprints.py`](../scripts/modkit/export_widget_blueprints.py) | Every `WidgetBlueprint`, with the stock `unreal.UserWidget` baseline subtracted so only widget-specific additions remain. Same shape as `blueprint_api.json`. Leaf-name collisions are keyed by full path. |
| [`recipe_tree.json`](recipe_tree.json) | [`dump_recipe_tree.py`](../scripts/modkit/dump_recipe_tree.py) | Every craftable item & placeable, grouped by crafting category (`Base` = handcraft, `Construction` = build menu, plus stations like `Smithing`, `Furnace`, `PackageCrafting`). Each entry: ingredients (item + amount), output amount, XP reward, required tech-tree unlock. Consumed by the HTML viewers in [`../tools/`](../tools/). |

## Refreshing the data

The dumps reflect the Modkit version they were generated against. After a Modkit update:

1. Run the relevant script inside the Modkit editor (see [`../scripts/modkit/README.md`](../scripts/modkit/README.md)).
2. Move the output (default `C:/Temp/...` or `<ProjectSaved>/...`) into this folder, overwriting the old version.

Full setup, knobs, and gotchas: [`../docs/modkit-python-scripting.md`](../docs/modkit-python-scripting.md).
