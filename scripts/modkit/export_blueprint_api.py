import unreal
import json
import os

def get_blueprint_apis():
    save_path = "C:/Temp/LastOasis_APIs.json"
    if not os.path.exists("C:/Temp"):
        os.makedirs("C:/Temp")

    api_library = {}
    
    # 1. Get the Asset Registry
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    
    # 2. Get all Blueprint Assets in /Game/
    # We use a simpler approach to avoid the ARFilter read-only issue
    all_assets = asset_registry.get_assets_by_path("/Game", recursive=True)
    blueprint_assets = [a for a in all_assets if a.asset_class == 'Blueprint']
    
    unreal.log("--- Found {} Blueprints in /Game. Starting CDO Inspection ---".format(len(blueprint_assets)))

    with unreal.ScopedSlowTask(len(blueprint_assets), "Inspecting CDOs...") as slow_task:
        slow_task.make_dialog(True)
        
        for asset_data in blueprint_assets:
            if slow_task.should_cancel():
                break
                
            try:
                # Get the generated class path
                full_path = str(asset_data.object_path)
                class_path = full_path + "_C"
                
                # Load the Class
                cls = unreal.load_class(None, class_path)
                if not cls:
                    slow_task.enter_progress_frame(1)
                    continue
                
                # Get the Class Default Object (CDO)
                # In 4.25, inspecting the CDO is often the only way to see what's 'on' the class
                cdo = unreal.get_default_object(cls)
                
                if cdo:
                    bp_name = str(asset_data.asset_name)
                    # dir() on a CDO will show all properties and functions 
                    # that the Python wrapper has reflected.
                    attrs = dir(cdo)
                    
                    # Filter for functions/properties
                    # We look for things that are likely ModKit APIs (excluding standard Python/UE noise)
                    clean_api = []
                    for attr in attrs:
                        if not attr.startswith("_") and not attr.startswith("k2_"):
                            # Logic: If it's callable or a public property, we want it
                            clean_api.append(attr)
                    
                    if clean_api:
                        api_library[bp_name] = {
                            "path": full_path,
                            "exposed_members": clean_api
                        }
            except Exception as e:
                # Skip assets that fail to load
                pass
            
            slow_task.enter_progress_frame(1)

    # Final Save
    with open(save_path, "w") as f:
        json.dump(api_library, f, indent=4)
        
    unreal.log("SUCCESS: Saved {} Blueprints to {}".format(len(api_library), save_path))

if __name__ == "__main__":
    get_blueprint_apis()