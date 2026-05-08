# dump_recipes.py
# Builds a tree of every recipe in the Last Oasis modkit and prints it to the
# UE 4.25 Output Log.  Also writes the structured tree to Saved/RecipeTree.json.
#
# Schema (discovered by probing CDOs):
#   * Items   (/Game/Mist/Data/Items/...)      have a `recipes` array.
#                Each entry is a recipe struct with:
#                  - category              -> crafting category class
#                                             (e.g. Base_C = handcraft 'C',
#                                                  Smithing_C, Furnace_C, ...)
#                  - required_unlockable   -> tech-tree entry class
#                  - inputs                -> tuple of (item_class, amount)
#                  - experience_reward_crafting
#                  - amount / quantity (occasionally)
#   * Placeables (/Game/Mist/Data/Placeables/...) carry a single
#                MistCraftingRequirements struct named `requirements`
#                (or `full_cost`).  These are the 'B' build menu entries.
#
# How to run (UE 4.25 ships with Python 2.7, so this file is Py2/Py3-safe):
#   1. Edit -> Plugins -> Scripting -> "Python Editor Script Plugin" -> Enabled
#      (restart editor if you just enabled it).
#   2. Output Log -> bottom dropdown set to "Cmd":
#        py "D:/Program Files/Epic Games/LastOasisModkit/Game/Utils/dump_recipes.py"

from __future__ import print_function
import errno
import io
import json
import os
import unreal

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ITEMS_PATH      = "/Game/Mist/Data/Items"
PLACEABLES_PATH = "/Game/Mist/Data/Placeables"
CATEGORY_PATH   = "/Game/Mist/Data/Crafting/Categories"

OUTPUT_JSON = os.path.join(unreal.Paths.project_saved_dir(), "RecipeTree.json")

# Property names we use, in priority order.
ITEM_RECIPES_PROPS      = ["recipes"]
PLACEABLE_RECIPE_PROPS  = ["requirements", "full_cost"]

# Field names inside a single recipe / requirements struct.
RECIPE_INPUTS_FIELDS    = ["inputs"]
RECIPE_CATEGORY_FIELDS  = ["category"]
RECIPE_UNLOCKABLE_FIELDS= ["required_unlockable"]
RECIPE_EXP_FIELDS       = ["experience_reward_crafting"]
RECIPE_AMOUNT_FIELDS    = ["amount", "result_amount", "quantity"]

# Field names inside a single ingredient entry.  In Last Oasis the inputs
# array is a TPair<TSubclassOf<UMistItem>, int32>, so the fields are named
# `key` and `value` -- which is also why the entries render as plain tuples.
# We list a few alternatives in case sub-types deviate, and finally fall back
# to tuple indexing.
ING_ITEM_FIELDS         = ["key", "item", "item_class", "resource"]
ING_AMOUNT_FIELDS       = ["value", "amount", "count", "quantity"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ASSET_REG = unreal.AssetRegistryHelpers.get_asset_registry()


def log(msg):
    unreal.log(msg if isinstance(msg, str) else str(msg))


def makedirs_safe(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def write_json(path, obj):
    makedirs_safe(os.path.dirname(path))
    with io.open(path, "w", encoding="utf-8") as fh:
        data = json.dumps(obj, indent=2, default=str, ensure_ascii=False)
        if not isinstance(data, type(u"")):
            data = data.decode("utf-8")
        fh.write(data)


def safe_get(obj, name):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return None


def first_existing(obj, names):
    for n in names:
        v = safe_get(obj, n)
        if v is not None:
            return v
    return None


def list_assets(path):
    filt = unreal.ARFilter(package_paths=[path], recursive_paths=True,
                           include_only_on_disk_assets=False)
    return ASSET_REG.get_assets(filt)


def class_default_object(asset_data):
    pkg_path = str(asset_data.object_path).split(".")[0]
    try:
        gen = unreal.EditorAssetLibrary.load_blueprint_class(pkg_path)
    except Exception:
        gen = None
    if gen is not None:
        try:
            return unreal.get_default_object(gen)
        except Exception:
            pass

    obj = asset_data.get_asset()
    if obj is None:
        return None
    if isinstance(obj, unreal.Blueprint):
        gen = safe_get(obj, "generated_class")
        if gen:
            try:
                return unreal.get_default_object(gen)
            except Exception:
                return None
        return None
    if isinstance(obj, unreal.Class):
        return unreal.get_default_object(obj)
    return obj


def to_path_string(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return value.get_path_name()
    except Exception:
        pass
    try:
        return str(value)
    except Exception:
        return None


def short_name(value):
    p = to_path_string(value)
    if not p:
        return None
    # /Game/.../Foo.Foo_C  -> Foo
    tail = p.split("/")[-1]
    tail = tail.split(".")[-1]
    if tail.endswith("_C"):
        tail = tail[:-2]
    return tail or None


# ---------------------------------------------------------------------------
# Recipe extraction
# ---------------------------------------------------------------------------

def extract_ingredient(entry):
    """Pull (item, amount) out of one recipe input entry.

    The entries are MistCraftingInput-style structs which UE Python renders as
    plain tuples like (Class, 5) or (None, 1).  Accessor names work on the
    real struct, so we try those first; if that fails we treat the entry as a
    2-tuple.
    """
    if entry is None:
        return {"item": None, "path": None, "amount": 1}

    item = first_existing(entry, ING_ITEM_FIELDS)
    amt  = first_existing(entry, ING_AMOUNT_FIELDS)

    if item is None and amt is None:
        try:
            item = entry[0]
            amt  = entry[1]
        except Exception:
            pass

    return {
        "item":   short_name(item),
        "path":   to_path_string(item),
        "amount": amt if amt is not None else 1,
    }


def iterate_inputs(inputs_raw):
    # `inputs` is a TMap<TSubclassOf<UMistItem>, int32> in Last Oasis.
    # In UE Python, TMap renders as ((k,v),(k,v),...) but plain iteration
    # yields keys only.  Use .items() to get (item_class, amount) pairs;
    # fall back to treating each entry as a struct (older shapes) if needed.
    if inputs_raw is None:
        return
    items_method = getattr(inputs_raw, "items", None)
    if callable(items_method):
        try:
            for k, v in items_method():
                yield {
                    "item":   short_name(k),
                    "path":   to_path_string(k),
                    "amount": v if v is not None else 1,
                }
            return
        except Exception:
            pass
    try:
        for entry in inputs_raw:
            yield extract_ingredient(entry)
    except TypeError:
        yield extract_ingredient(inputs_raw)


def extract_recipe(struct, default_category=None):
    if struct is None:
        return None
    inputs_raw = first_existing(struct, RECIPE_INPUTS_FIELDS)
    ingredients = list(iterate_inputs(inputs_raw))

    cat = first_existing(struct, RECIPE_CATEGORY_FIELDS)
    return {
        "category":            short_name(cat) or default_category,
        "category_path":       to_path_string(cat),
        "required_unlockable": short_name(first_existing(struct, RECIPE_UNLOCKABLE_FIELDS)),
        "experience":          first_existing(struct, RECIPE_EXP_FIELDS),
        "result_amount":       first_existing(struct, RECIPE_AMOUNT_FIELDS),
        "ingredients":         ingredients,
    }


def display_name(cdo, asset_data):
    name = safe_get(cdo, "name")
    if name:
        try:
            txt = str(name)
            if txt and txt != "None":
                return txt
        except Exception:
            pass
    return str(asset_data.asset_name)


# ---------------------------------------------------------------------------
# Walks
# ---------------------------------------------------------------------------

def walk_items():
    log("[Recipes] Walking items under {}".format(ITEMS_PATH))
    out = []
    count = 0
    for ad in list_assets(ITEMS_PATH):
        cdo = class_default_object(ad)
        if cdo is None:
            continue
        recipes = first_existing(cdo, ITEM_RECIPES_PROPS)
        if not recipes:
            continue
        try:
            recipe_list = list(recipes)
        except TypeError:
            recipe_list = [recipes]
        if not recipe_list:
            continue
        item_name  = display_name(cdo, ad)
        asset_name = str(ad.asset_name)
        item_path  = str(ad.object_path)
        for r in recipe_list:
            recipe = extract_recipe(r)
            if recipe is None:
                continue
            recipe["result"]      = item_name
            recipe["result_id"]   = asset_name
            recipe["result_path"] = item_path
            out.append(recipe)
            count += 1
    log("[Recipes] Items contributed {} recipe(s)".format(count))
    return out


def walk_placeables():
    log("[Recipes] Walking placeables under {}".format(PLACEABLES_PATH))
    out = []
    for ad in list_assets(PLACEABLES_PATH):
        cdo = class_default_object(ad)
        if cdo is None:
            continue
        struct = first_existing(cdo, PLACEABLE_RECIPE_PROPS)
        if struct is None:
            continue
        recipe = extract_recipe(struct, default_category="Construction")
        if recipe is None:
            continue
        # Placeables are the 'B' build menu regardless of how the requirements
        # struct labels itself, since they're not crafted at a station.
        if not recipe["category"]:
            recipe["category"] = "Construction"
        recipe["result"]      = display_name(cdo, ad)
        recipe["result_id"]   = str(ad.asset_name)
        recipe["result_path"] = str(ad.object_path)
        out.append(recipe)
    log("[Recipes] Placeables contributed {} recipe(s)".format(len(out)))
    return out


def collect_category_metadata():
    """Pull display info for each category so we can label sections nicely."""
    out = {}
    for ad in list_assets(CATEGORY_PATH):
        cdo = class_default_object(ad)
        if cdo is None:
            continue
        out[str(ad.asset_name)] = {
            "techtree_name":   to_path_string(safe_get(cdo, "techtree_name")) or
                               str(safe_get(cdo, "techtree_name") or ""),
            "hidden":          bool(safe_get(cdo, "hidden_in_tech_tree")),
            "is_on_character": bool(safe_get(cdo, "is_on_character")),
        }
    return out


# ---------------------------------------------------------------------------
# Group + render
# ---------------------------------------------------------------------------

CATEGORY_LABELS = {
    "Base":         "'C' handcraft menu",
    "Construction": "'B' build menu (placeables)",
}


def group_by_category(recipes):
    groups = {}
    for r in recipes:
        key = r.get("category") or "(uncategorized)"
        groups.setdefault(key, []).append(r)
    for key in groups:
        groups[key].sort(key=lambda r: (r.get("result") or "").lower())
    return groups


def render_tree(groups, category_meta):
    lines = []
    lines.append("=" * 78)
    lines.append("RECIPE TREE  ({} categories, {} total recipes)".format(
        len(groups), sum(len(v) for v in groups.values())))
    lines.append("=" * 78)

    ordered = []
    for special in ("Base", "Construction"):
        if special in groups:
            ordered.append(special)
    for k in sorted(groups.keys()):
        if k not in ordered:
            ordered.append(k)

    for cat in ordered:
        recipes = groups[cat]
        label = cat
        if cat in CATEGORY_LABELS:
            label += "   <-- " + CATEGORY_LABELS[cat]
        lines.append("")
        lines.append("[{}]  ({} recipes)".format(label, len(recipes)))
        for r in recipes:
            qty = r.get("result_amount")
            head = "  - {}".format(r.get("result") or r.get("result_id") or "?")
            if qty:
                head += " x{}".format(qty)
            xp = r.get("experience")
            if xp:
                head += "   (xp {})".format(xp)
            unlock = r.get("required_unlockable")
            if unlock:
                head += "   [requires {}]".format(unlock)
            lines.append(head)
            for ing in r.get("ingredients", []):
                item = ing.get("item") or "<missing>"
                lines.append("      * {} x{}".format(item, ing.get("amount") or 1))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    log("[Recipes] Starting dump.  JSON output: {}".format(OUTPUT_JSON))

    item_recipes      = walk_items()
    placeable_recipes = walk_placeables()
    all_recipes       = item_recipes + placeable_recipes
    groups            = group_by_category(all_recipes)
    category_meta     = collect_category_metadata()

    payload = {
        "categories":  category_meta,
        "groups":      {k: v for k, v in groups.items()},
        "totals": {
            "item_recipes":      len(item_recipes),
            "placeable_recipes": len(placeable_recipes),
            "categories":        len(groups),
        },
    }
    try:
        write_json(OUTPUT_JSON, payload)
        log("[Recipes] JSON written to {}".format(OUTPUT_JSON))
    except Exception as e:
        log("[Recipes] Failed to write JSON: {}".format(e))

    text = render_tree(groups, category_meta)
    for chunk_start in range(0, len(text), 3500):
        log(text[chunk_start:chunk_start + 3500])

    log("[Recipes] Done. Items: {}, Placeables: {}, Categories: {}.".format(
        len(item_recipes), len(placeable_recipes), len(groups)))


main()
