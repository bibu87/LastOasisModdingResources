"""
extract_lo_recipes.py  (v9 - Map serialization fixed)
======================================================

Debug on WoodenSlab revealed:
- A recipe's 'inputs' is a TMap, not a TArray.
  TMap<TSubclassOf<MistItemTemplate>, int32> -- keys are item classes,
  values are required quantities.
- v7's serializer iterated unreal.Map like a list (via __iter__) which
  yielded only the keys, dropping the counts. That's why WoodenSlab's
  inputs came out as ["Wood_C", "FiberCloth_C"] with no quantities.
- Confirmed structure on a recipe (MistItemCraftingRecipe):
    category            -> BlueprintGeneratedClass (crafting station class)
    crafting_time       -> float (seconds)
    inputs              -> Map<class, int> (ingredient -> count)
    quantity            -> int (output count)
    required_unlockable -> BlueprintGeneratedClass (tech tree node)
- Items can have multiple recipes (WoodenSlab has 6).

V9 FIX
------
Detect unreal.Map BEFORE the __iter__ fallback in serialize_value, and
iterate via .keys() so we serialize as {key: value} pairs.

Also: handle unreal.Set similarly for completeness.

OUTPUT: <ProjectSaved>/Recipes/recipes.json
"""

import unreal
import json
import os
import time

# -------- CONFIG ----------------------------------------------------------

SCAN_ROOTS = [
    "/Game/Mist/Data/Items",
    "/Game/Mist/Data/Crafting",
    "/Game/Mist/Data/TechTree",
    "/Game/Mist/Data/Placeables",
    "/Game/Mist/Data/Walkers",
    "/Game/Mist/Data/Harvest",
]

OUTPUT_PATH = unreal.Paths.project_saved_dir() + "Recipes/recipes.json"

MAX_DEPTH = 8

SKIP_NAMES = set([
    "cast", "modify", "rename", "static_class",
    "get_class", "get_default_object", "get_editor_property",
    "set_editor_property", "set_editor_properties",
    "get_fname", "get_full_name", "get_name", "get_outer",
    "get_outermost", "get_path_name", "get_typed_outer", "get_world",
    # MistItemTemplate-specific helpers (callables anyway, but defensive)
    "can_be_used", "get_additional_info_icon", "get_additional_schematic_icon",
    "get_display_mesh", "get_icon", "get_skin_template",
    "has_conditions", "is_release_approved", "is_unlocked_for_player",
    "on_item_used", "receive_item_used",
])

# --------------------------------------------------------------------------


def ensure_dir(path):
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise


def get_all_assets_under(roots):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    ar.scan_paths_synchronous(roots, force_rescan=False)
    out = []
    for root in roots:
        assets = ar.get_assets_by_path(root, recursive=True)
        unreal.log("  {} -> {} raw assets".format(root, len(assets)))
        out.extend(assets)
    return out


def safe_get_property(obj, prop_name):
    try:
        return obj.get_editor_property(prop_name)
    except Exception:
        return None


def get_property_names(uobject):
    names = []
    seen = set()
    try:
        for attr in dir(uobject):
            if attr.startswith("_"):
                continue
            if attr in SKIP_NAMES:
                continue
            if attr in seen:
                continue
            try:
                val = getattr(uobject, attr)
            except Exception:
                continue
            if callable(val):
                continue
            seen.add(attr)
            names.append(attr)
    except Exception:
        pass
    return names


def is_unreal_map(v):
    try:
        return isinstance(v, unreal.Map)
    except AttributeError:
        return False


def is_unreal_set(v):
    try:
        return isinstance(v, unreal.Set)
    except AttributeError:
        return False


def serialize_map(m, depth):
    """Serialize unreal.Map as a dict, keying by serialized form of each key.

    For TMap<UClass*, int32> (recipe inputs), keys serialize to path strings
    and values are ints, giving us {"path/to/Wood_C": 5, ...}.
    """
    out = {}
    try:
        keys = list(m.keys())
    except Exception:
        # Fallback: try iterating directly
        try:
            keys = list(iter(m))
        except Exception:
            return str(m)

    for k in keys:
        try:
            v = m[k]
        except Exception:
            v = "<map-lookup-failed>"
        # Serialize the key to something JSON-stringifiable
        ser_k = serialize_value(k, depth + 1)
        if not isinstance(ser_k, (str,)):
            try:
                ser_k = str(ser_k)
            except Exception:
                ser_k = repr(ser_k)
        out[ser_k] = serialize_value(v, depth + 1)
    return out


def serialize_value(v, depth=0):
    if depth > MAX_DEPTH:
        return "<max-depth>"
    if v is None:
        return None
    if isinstance(v, bool) or isinstance(v, int) or isinstance(v, float):
        return v

    try:
        if isinstance(v, basestring):  # noqa: F821 - Py2 only
            return v
    except NameError:
        if isinstance(v, str):
            return v

    # *** CRITICAL: Maps and Sets must be detected BEFORE the __iter__ branch.
    # Otherwise unreal.Map iterates as keys-only and we lose values.
    if is_unreal_map(v):
        return serialize_map(v, depth)
    if is_unreal_set(v):
        try:
            return [serialize_value(x, depth + 1) for x in v]
        except Exception:
            return str(v)

    # Lists, tuples
    if isinstance(v, (list, tuple)):
        return [serialize_value(x, depth + 1) for x in v]

    # unreal.Array and other iterables (after Map/Set check above)
    if hasattr(v, "__iter__") and not isinstance(v, dict):
        try:
            return [serialize_value(x, depth + 1) for x in v]
        except Exception:
            pass

    if isinstance(v, dict):
        return dict((str(k), serialize_value(val, depth + 1))
                    for k, val in v.items())

    # unreal.Text
    try:
        if isinstance(v, unreal.Text):
            try:
                return str(v)
            except Exception:
                return None
    except AttributeError:
        pass

    # Structs - recurse
    if isinstance(v, unreal.StructBase):
        result = {}
        for name in get_property_names(v):
            val = safe_get_property(v, name)
            if val is None:
                continue
            try:
                result[name] = serialize_value(val, depth + 1)
            except Exception:
                result[name] = "<serialize-failed>"
        return result if result else str(v)

    # Soft refs
    try:
        if isinstance(v, (unreal.SoftObjectPath, unreal.SoftClassPath)):
            try:
                return v.export_text()
            except Exception:
                return str(v)
    except AttributeError:
        pass

    # Hard refs
    if isinstance(v, (unreal.Class, unreal.Object)):
        try:
            return v.get_path_name()
        except Exception:
            return str(v)

    return str(v)


def serialize_object(uobject):
    out = {}
    for name in get_property_names(uobject):
        val = safe_get_property(uobject, name)
        if val is None:
            continue
        try:
            out[name] = serialize_value(val, depth=1)
        except Exception as e:
            out[name] = "<serialize-failed: {}>".format(e)
    return out


def get_target_object(asset_path):
    try:
        cls = unreal.EditorAssetLibrary.load_blueprint_class(asset_path)
    except Exception:
        cls = None
    if cls is not None:
        try:
            cdo = unreal.get_default_object(cls)
            if cdo is not None:
                return cdo, "blueprint_cdo"
        except Exception:
            pass
    try:
        obj = unreal.EditorAssetLibrary.load_asset(asset_path)
        if obj is not None:
            return obj, "native_object"
    except Exception:
        pass
    return None, "load_failed"


def main():
    t0 = time.time()
    unreal.log("Recipe extraction v9: scanning {}".format(SCAN_ROOTS))
    candidates = get_all_assets_under(SCAN_ROOTS)
    unreal.log("Total raw assets: {}".format(len(candidates)))

    results = []
    skipped = 0
    empty = 0
    by_source = {"blueprint_cdo": 0, "native_object": 0, "load_failed": 0}

    for i, asset_data in enumerate(candidates):
        if i % 100 == 0:
            unreal.log("  progress {}/{}".format(i, len(candidates)))

        asset_path = str(asset_data.object_path)
        try:
            target, source = get_target_object(asset_path)
            by_source[source] = by_source.get(source, 0) + 1
            if target is None:
                skipped += 1
                continue

            props = serialize_object(target)
            if not props:
                empty += 1

            entry = {
                "asset_path": asset_path,
                "asset_name": str(asset_data.asset_name),
                "asset_class": str(asset_data.asset_class),
                "target_class": target.get_class().get_path_name(),
                "source": source,
                "properties": props,
            }
            results.append(entry)

        except Exception as e:
            unreal.log_warning("Failed on {}: {}".format(asset_path, e))
            skipped += 1

    out_dir = os.path.dirname(OUTPUT_PATH)
    ensure_dir(out_dir)

    try:
        f = open(OUTPUT_PATH, "w", encoding="utf-8")
    except TypeError:
        import io
        f = io.open(OUTPUT_PATH, "w", encoding="utf-8")
    try:
        text = json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True)
        try:
            f.write(text)
        except TypeError:
            f.write(text.decode("utf-8") if isinstance(text, bytes) else text)
    finally:
        f.close()

    dt = time.time() - t0
    unreal.log("Done in {:.1f}s.".format(dt))
    unreal.log("  Entries:  {}".format(len(results)))
    unreal.log("  Empty:    {}".format(empty))
    unreal.log("  Skipped:  {}".format(skipped))
    unreal.log("  Sources:  {}".format(by_source))
    unreal.log("  Output:   {}".format(OUTPUT_PATH))


main()