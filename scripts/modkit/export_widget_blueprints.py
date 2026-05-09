import json
import unreal

OUT = "C:/Temp/widget_bp_functions.json"

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_class("WidgetBlueprint", True)

# --- Baseline: subtract stock UserWidget so only widget-specific additions remain.
baseline = set(dir(unreal.UserWidget))

library = {}
collisions = 0
count = 0
for a in assets:
    path = str(a.package_name)
    try:
        gc = unreal.load_object(None, str(a.object_path) + "_C")
        if not gc:
            continue

        cdo = unreal.get_default_object(gc)
        if not cdo:
            continue

        members = sorted(set(dir(cdo)) - baseline)
        fns = [m for m in members
               if callable(getattr(cdo, m, None)) and not m.startswith("_")]

        leaf = path.rsplit("/", 1)[-1] or path
        key = leaf
        if key in library:
            # Disambiguate by full path on leaf-name collision.
            key = path
            collisions += 1
        library[key] = {"path": path, "exposed_members": fns}
        count += 1
    except Exception as e:
        unreal.log_warning("widget export error for {}: {}".format(path, e))

with open(OUT, "w") as f:
    json.dump(library, f, indent=2, separators=(",", ": "))
    f.write("\n")

unreal.log("Done. Wrote {} widgets ({} path-disambiguated) to {}".format(
    count, collisions, OUT))
