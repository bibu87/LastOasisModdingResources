#!/usr/bin/env python3
"""
dump_props.py
=============

Decode the tagged property bag of each significant export in a UE4
.uasset file. Use this to see the *values* of fields stored on data
assets (positions, references, struct contents, array entries) without
opening the editor.

Particularly useful for:

  - Confirming what data a migration step lost (e.g. a Spots[] array
    that re-saved with default values).
  - Recovering field values from a workshop pak's original asset to
    re-enter them in the editor.
  - Verifying a binary patch (e.g. `patch_struct_rename.py`) preserved
    the data correctly before installing the file.

Decodes Bool, Int, Float, Name, Object, Str, Struct, Array (including
arrays of structs). Common math structs (Vector, Quat, Rotator, Guid,
Transform) are decoded inline; other structs recurse as nested tagged
properties.

Targets the Modkit's UE 4.25 package format (file version 518).

Usage
-----

    python dump_props.py <file.uasset> [<file2.uasset> ...]

Prints to stdout. Exports under 65 bytes (e.g. `PackageMetaData`) are
skipped — they don't carry interesting data.

Standard library only — no `pip install` step.
"""
import struct
import sys
from pathlib import Path


class Reader:
    def __init__(self, data, pos=0):
        self.data = data; self.pos = pos
    def i32(self):
        v = struct.unpack_from("<i", self.data, self.pos)[0]; self.pos += 4; return v
    def u32(self):
        v = struct.unpack_from("<I", self.data, self.pos)[0]; self.pos += 4; return v
    def i64(self):
        v = struct.unpack_from("<q", self.data, self.pos)[0]; self.pos += 8; return v
    def u8(self):
        v = self.data[self.pos]; self.pos += 1; return v
    def f32(self):
        v = struct.unpack_from("<f", self.data, self.pos)[0]; self.pos += 4; return v
    def f64(self):
        v = struct.unpack_from("<d", self.data, self.pos)[0]; self.pos += 8; return v
    def bytes(self, n):
        b = self.data[self.pos:self.pos+n]; self.pos += n; return b
    def fstring(self):
        n = self.i32()
        if n == 0: return ""
        if n > 0:
            s = self.data[self.pos:self.pos+n-1].decode("ascii", errors="replace"); self.pos += n; return s
        n = -n
        s = self.data[self.pos:self.pos+(n-1)*2].decode("utf-16-le", errors="replace"); self.pos += n*2; return s


def parse_uasset(path):
    """Walk the header to extract names, imports, exports. Returns (names, imports, exports, data)."""
    data = Path(path).read_bytes()
    r = Reader(data)
    if r.u32() != 0x9E2A83C1:
        raise ValueError("not a uasset")
    lfv = r.i32()
    if lfv != -4:
        r.i32()  # LegacyUE3Version
    fv4 = r.i32(); r.i32()
    if lfv <= -2:
        cvc = r.i32()
        for _ in range(cvc):
            r.bytes(16); r.i32()
    r.i32()             # TotalHeaderSize
    r.fstring()         # FolderName
    r.u32()             # PackageFlags
    name_count = r.i32(); name_offset = r.i32()
    if fv4 >= 518:
        r.fstring()     # LocalizationId
    if fv4 >= 459:
        r.i32(); r.i32()    # GatherableTextDataCount, GatherableTextDataOffset
    export_count = r.i32(); export_offset = r.i32()
    import_count = r.i32(); import_offset = r.i32()

    r.pos = name_offset
    names = []
    for _ in range(name_count):
        s = r.fstring()
        if fv4 >= 504:
            r.bytes(4)   # uint16+uint16 hashes
        names.append(s)

    r.pos = import_offset
    imports = []
    for _ in range(import_count):
        cp_idx = r.i32(); r.i32()
        cn_idx = r.i32(); r.i32()
        outer = r.i32()
        on_idx = r.i32(); r.i32()
        imports.append({
            "ClassPackage": names[cp_idx], "ClassName": names[cn_idx],
            "Outer": outer, "ObjectName": names[on_idx],
        })

    r.pos = export_offset
    exports = []
    for _ in range(export_count):
        r.i32()                                          # ClassIndex
        r.i32()                                          # SuperIndex
        if fv4 >= 508: r.i32()                           # TemplateIndex
        r.i32()                                          # OuterIndex
        on_idx = r.i32(); r.i32()                        # ObjectName FName
        r.u32()                                          # ObjectFlags
        size = r.i64()
        offset = r.i64()
        r.i32(); r.i32(); r.i32()                        # forced/notforclient/notforserver
        r.bytes(16); r.u32()                             # PackageGuid + PackageFlags
        r.i32(); r.i32()                                 # bNotAlwaysLoadedForEditorGame, bIsAsset
        r.i32(); r.i32(); r.i32(); r.i32(); r.i32()      # 5 dependency ints
        exports.append({
            "name": names[on_idx], "size": size, "offset": offset,
        })
    return names, imports, exports, data


INDENT = "  "


def fname(r, names):
    idx = r.i32(); num = r.i32()
    base = names[idx] if 0 <= idx < len(names) else f"<bad {idx}>"
    return base if num == 0 else f"{base}_{num-1}"


def parse_prop_value(r, names, imports, prop_type, size, depth, struct_name=None):
    pad = INDENT * depth
    if prop_type == "BoolProperty":
        return f"{r.u8() != 0}"
    if prop_type == "IntProperty":
        return str(r.i32())
    if prop_type == "FloatProperty":
        return f"{r.f32():g}"
    if prop_type == "NameProperty":
        return f"FName({fname(r, names)})"
    if prop_type == "ObjectProperty":
        idx = r.i32()
        if idx == 0: return "None"
        if idx < 0:
            i = -idx - 1
            return f"Import[{idx}] {imports[i]['ObjectName']} ({imports[i]['ClassName']})"
        return f"Export[{idx}]"
    if prop_type == "StrProperty":
        return repr(r.fstring())
    if prop_type == "StructProperty":
        if struct_name == "Vector":
            x, y, z = r.f32(), r.f32(), r.f32()
            return f"Vector({x:g}, {y:g}, {z:g})"
        if struct_name == "Quat":
            x, y, z, w = r.f32(), r.f32(), r.f32(), r.f32()
            return f"Quat({x:g}, {y:g}, {z:g}, {w:g})"
        if struct_name == "Rotator":
            p, y, ro = r.f32(), r.f32(), r.f32()
            return f"Rotator(P={p:g}, Y={y:g}, R={ro:g})"
        if struct_name == "Guid":
            g = r.bytes(16); return f"Guid({g.hex()})"
        if struct_name == "Transform":
            sub = parse_props(r, names, imports, depth + 1)
            return f"Transform {{\n{sub}{pad}}}"
        # Generic: recurse as tagged properties
        sub = parse_props(r, names, imports, depth + 1)
        return f"{struct_name} {{\n{sub}{pad}}}"
    # Unknown: dump bytes
    return f"<raw {size}b: {r.bytes(size).hex()[:64]}...>"


def parse_props(r, names, imports, depth=0):
    """Parse tagged properties until 'None' tag. Returns text."""
    pad = INDENT * depth
    out = []
    while True:
        name = fname(r, names)
        if name == "None":
            break
        prop_type = fname(r, names)
        size = r.i32()
        array_idx = r.i32()
        struct_name = None
        inner_type = None
        bool_value = None
        if prop_type == "StructProperty":
            struct_name = fname(r, names)
            r.bytes(16)  # struct guid
            r.u8()       # has_guid
        elif prop_type == "BoolProperty":
            bool_value = r.u8()
            r.u8()       # has_guid
        elif prop_type == "ArrayProperty":
            inner_type = fname(r, names)
            r.u8()       # has_guid
        elif prop_type == "ByteProperty" or prop_type == "EnumProperty":
            fname(r, names)  # enum name
            r.u8()
        else:
            r.u8()       # has_guid

        start = r.pos
        if prop_type == "BoolProperty":
            value = f"{bool_value != 0}"
        elif prop_type == "ArrayProperty":
            count = r.i32()
            elems = []
            if inner_type == "StructProperty":
                # Inner-struct preamble: name, type, size, idx, struct_name, guid, has_guid
                fname(r, names)                        # inner name
                fname(r, names)                        # inner prop type ("StructProperty")
                r.i32()                                # inner size
                r.i32()                                # inner array idx
                inner_struct_name = fname(r, names)
                r.bytes(16); r.u8()                    # struct guid + has_guid
                inline_structs = ("Vector", "Quat", "Rotator", "Guid")
                for ei in range(count):
                    if inner_struct_name in inline_structs:
                        elems.append(f"{pad}{INDENT}[{ei}] {parse_prop_value(r, names, imports, 'StructProperty', 0, depth+1, inner_struct_name)}")
                    else:
                        sub = parse_props(r, names, imports, depth + 2)
                        elems.append(f"{pad}{INDENT}[{ei}] {inner_struct_name} {{\n{sub}{pad}{INDENT}}}")
                value = f"Array<{inner_struct_name}>({count}) [\n" + "\n".join(elems) + f"\n{pad}]"
            else:
                for ei in range(count):
                    val = parse_prop_value(r, names, imports, inner_type, 0, depth + 1)
                    elems.append(f"{pad}{INDENT}[{ei}] {val}")
                value = f"Array<{inner_type}>({count}) [\n" + "\n".join(elems) + f"\n{pad}]"
        else:
            value = parse_prop_value(r, names, imports, prop_type, size, depth, struct_name)

        consumed = r.pos - start
        if prop_type != "BoolProperty" and consumed != size:
            if consumed < size:
                value += f"  <unparsed {size - consumed}b: {r.bytes(size - consumed).hex()[:32]}...>"
            else:
                value += f"  <OVERREAD by {consumed - size}b!>"
        idx_suffix = f"[{array_idx}]" if array_idx != 0 else ""
        out.append(f"{pad}{name}{idx_suffix}: {prop_type} = {value}")
    return "\n".join(out) + ("\n" if out else "")


def main_one(path):
    names, imports, exports, data = parse_uasset(path)
    print(f"=== PROPS: {Path(path).name} ===")
    for ex in exports:
        if ex["size"] > 65 and ex["name"] != "PackageMetaData":
            print(f"\n-- Export '{ex['name']}' (offset={ex['offset']}, size={ex['size']}) --")
            r = Reader(data, ex["offset"])
            try:
                print(parse_props(r, names, imports, 0))
            except Exception as e:
                print(f"  !! parse error at pos {r.pos}: {e}")
                end = ex["offset"] + ex["size"]
                rem = data[r.pos:end]
                print(f"  remaining {len(rem)}b: {rem[:128].hex()}")


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    for p in sys.argv[1:]:
        main_one(p)
        print()


if __name__ == "__main__":
    main()
