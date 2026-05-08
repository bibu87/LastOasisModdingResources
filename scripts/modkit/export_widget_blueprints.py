import unreal

OUT = "C:/Temp/widget_bp_functions.txt"

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_class("WidgetBlueprint", True)

# --- Baseline: start with stock UserWidget, then widen it using a probe BP
# so we also subtract methods from the game's intermediate widget base class.
baseline = set(dir(unreal.UserWidget))

count = 0
with open(OUT, "w") as f:
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

            f.write(path + "\n")
            for fn in fns:
                f.write("    " + fn + "\n")
            f.write("\n")
            count += 1
        except Exception as e:
            f.write("{}: ERROR {}\n\n".format(path, e))

print("Done. Wrote {} widgets to {}".format(count, OUT))