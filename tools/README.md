# Tools

Self-contained, offline HTML viewers for the recipe data in [`../data/`](../data/). **No build step, no server** — open the `.html` file directly in any modern browser.

## Files

| File | Description |
| --- | --- |
| [`recipe_viewer.html`](recipe_viewer.html) | Searchable, category-grouped recipe browser. Lists every recipe with its ingredients, output quantity, XP, and required tech-tree unlockable. Best for "what does it take to craft X?" lookups. |
| [`recipe_bubbles.html`](recipe_bubbles.html) | Interactive bubble / graph view of the recipe tree. Best for spotting ingredient chains and shared base resources at a glance. |

## How to use

Either page expects a sibling `RecipeTree.json`. The simplest way:

1. Make sure [`../data/RecipeTree.json`](../data/RecipeTree.json) exists. (It does in this repo.)
2. Either:
   - **Copy `RecipeTree.json` next to the HTML file**, then open the HTML file in a browser.
   - Or **open the HTML file** and use the in-page file picker (top header) to point it at any matching JSON.

## Refreshing the data

`RecipeTree.json` is produced by [`../scripts/modkit/Python_dump_recipes_for_tools.py`](../scripts/modkit/Python_dump_recipes_for_tools.py) — re-run that inside the Modkit editor after a Modkit update, then drop the new JSON into [`../data/`](../data/).

See [`../scripts/modkit/README.md`](../scripts/modkit/README.md) for how to run editor-side scripts.
