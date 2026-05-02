# Data

Extracted reference data from the Last Oasis Modkit (UE 4.25.4). All files in this folder are produced by the editor-side scripts in [`../scripts/modkit/`](../scripts/modkit/) — re-run those scripts inside the Modkit to refresh the dumps after a Modkit update.

## Files

| File | Produced by | Description |
| --- | --- | --- |
| [`LastOasis_APIs.json`](LastOasis_APIs.json) | [`Python code to extract BPs and functions from the Modkit.py`](../scripts/modkit/Python%20code%20to%20extract%20BPs%20and%20functions%20from%20the%20Modkit.py) | Every Blueprint under `/Game/`, with all CDO-exposed members per class. Filters out private (`_`) and stock K2 (`k2_`) entries. Searchable Blueprint API surface. |
| [`widget_bp_functions.txt`](widget_bp_functions.txt) | [`Python_Code_export_widget_bps.py`](../scripts/modkit/Python_Code_export_widget_bps.py) | Every `WidgetBlueprint`, with the stock `unreal.UserWidget` baseline subtracted so only widget-specific additions remain. Plain text, two-space-indented. |
| [`RecipeTree.json`](RecipeTree.json) | [`Python_dump_recipes_for_tools.py`](../scripts/modkit/Python_dump_recipes_for_tools.py) | Every craftable item & placeable, grouped by crafting category (`Base` = handcraft, `Construction` = build menu, plus stations like `Smithing`, `Furnace`, `PackageCrafting`). Each entry: ingredients (item + amount), output amount, XP reward, required tech-tree unlock. Consumed by the HTML viewers in [`../tools/`](../tools/). |

## Refreshing the data

The dumps reflect the Modkit version they were generated against. After a Modkit update:

1. Run the relevant script inside the Modkit editor (see [`../scripts/modkit/README.md`](../scripts/modkit/README.md)).
2. Move the output (default `C:/Temp/...` or `<ProjectSaved>/...`) into this folder, overwriting the old version.

Full setup, knobs, and gotchas: [`../docs/modkit-python-scripting.md`](../docs/modkit-python-scripting.md).
