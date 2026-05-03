#!/usr/bin/env python3
"""
dump_header.py
==============

Dump the header of a UE4 .uasset file as readable text — name table,
import table, export table. Intended for diffing two versions of an
asset (e.g. broken current vs. workshop original) when investigating
what the editor or a migration step changed.

Targets the Modkit's UE 4.25 package format (file version 518). Object
data (the binary serialized property bytes) is not decoded here — see
`dump_props.py` for that.

Usage
-----

    python dump_header.py <file.uasset> [<file2.uasset> ...]

Writes `<file>.uasset.txt` next to each input. To diff two versions:

    python dump_header.py orig.uasset curr.uasset
    git diff --no-index orig.uasset.txt curr.uasset.txt

Standard library only — no `pip install` step.
"""
import struct
import sys
from pathlib import Path


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def seek(self, p): self.pos = p
    def tell(self): return self.pos

    def i32(self):
        v = struct.unpack_from("<i", self.data, self.pos)[0]; self.pos += 4; return v

    def u32(self):
        v = struct.unpack_from("<I", self.data, self.pos)[0]; self.pos += 4; return v

    def i64(self):
        v = struct.unpack_from("<q", self.data, self.pos)[0]; self.pos += 8; return v

    def u16(self):
        v = struct.unpack_from("<H", self.data, self.pos)[0]; self.pos += 2; return v

    def fstring(self):
        n = self.i32()
        if n == 0: return ""
        if n > 0:
            s = self.data[self.pos:self.pos + n - 1].decode("ascii", errors="replace")
            self.pos += n
            return s
        n = -n
        s = self.data[self.pos:self.pos + (n - 1) * 2].decode("utf-16-le", errors="replace")
        self.pos += n * 2
        return s

    def guid(self):
        g = self.data[self.pos:self.pos + 16]; self.pos += 16; return g.hex()


def parse(path: Path) -> str:
    data = path.read_bytes()
    r = Reader(data)

    out = []
    out.append(f"=== FILE: {path.name} ({len(data)} bytes) ===")

    magic = r.u32()
    out.append(f"Magic: 0x{magic:08X} (expected 0x9E2A83C1)")
    if magic != 0x9E2A83C1:
        out.append("!! Not a valid UAsset header")
        return "\n".join(out)

    legacy_file_version = r.i32()
    out.append(f"LegacyFileVersion: {legacy_file_version}")
    if legacy_file_version != -4:
        out.append(f"LegacyUE3Version: {r.i32()}")
    file_version_ue4 = r.i32()
    file_version_licensee_ue4 = r.i32()
    out.append(f"FileVersionUE4: {file_version_ue4}, Licensee: {file_version_licensee_ue4}")

    if legacy_file_version <= -2:
        cv_count = r.i32()
        out.append(f"CustomVersions: {cv_count}")
        for _ in range(cv_count):
            r.guid(); r.i32()

    total_header_size = r.i32()
    folder_name = r.fstring()
    package_flags = r.u32()
    name_count = r.i32()
    name_offset = r.i32()
    out.append(f"TotalHeaderSize={total_header_size}, FolderName='{folder_name}', PackageFlags=0x{package_flags:08X}")
    out.append(f"NameCount={name_count}, NameOffset={name_offset}")

    # LocalizationId added in VER_UE4_ADDED_PACKAGE_OWNER (518)
    if file_version_ue4 >= 518:
        out.append(f"LocalizationId={r.fstring()!r}")
    # GatherableTextData added in VER_UE4_SERIALIZE_TEXT_IN_PACKAGES (459)
    if file_version_ue4 >= 459:
        gtd_count = r.i32(); gtd_offset = r.i32()
        out.append(f"GatherableTextDataCount={gtd_count}, Offset={gtd_offset}")

    export_count = r.i32(); export_offset = r.i32()
    import_count = r.i32(); import_offset = r.i32()
    depends_offset = r.i32()
    out.append(f"ExportCount={export_count}, ExportOffset={export_offset}")
    out.append(f"ImportCount={import_count}, ImportOffset={import_offset}")
    out.append(f"DependsOffset={depends_offset}")

    # Read name table
    r.seek(name_offset)
    names = []
    for _ in range(name_count):
        s = r.fstring()
        if file_version_ue4 >= 504:  # VER_UE4_NAME_HASHES_SERIALIZED
            r.u16(); r.u16()
        names.append(s)

    out.append("")
    out.append("--- NAME TABLE ---")
    for i, n in enumerate(names):
        out.append(f"  [{i:3d}] {n!r}")

    def fname(reader: Reader) -> str:
        idx = reader.i32(); num = reader.i32()
        base = names[idx] if 0 <= idx < len(names) else f"<bad idx {idx}>"
        return base if num == 0 else f"{base}_{num - 1}"

    # Read import table
    r.seek(import_offset)
    imports = []
    for _ in range(import_count):
        class_package = fname(r)
        class_name = fname(r)
        outer_index = r.i32()
        object_name = fname(r)
        imports.append((class_package, class_name, outer_index, object_name))

    out.append("")
    out.append("--- IMPORT TABLE ---")
    for i, (cp, cn, oi, on) in enumerate(imports):
        # Imports are referenced via negative indices elsewhere in the file
        out.append(f"  [{-(i+1):3d}] ClassPackage={cp!r:40s} ClassName={cn!r:30s} Outer={oi:4d} ObjectName={on!r}")

    def resolve(idx: int) -> str:
        if idx == 0: return "<None>"
        if idx < 0:
            i = -idx - 1
            if 0 <= i < len(imports):
                cp, cn, oi, on = imports[i]
                return f"Import[{idx}]:{on}({cn})"
            return f"<bad import {idx}>"
        return f"Export[{idx}]:{idx - 1}"

    # Read export table
    r.seek(export_offset)
    exports = []
    for i in range(export_count):
        try:
            class_idx = r.i32()
            super_idx = r.i32()
            template_idx = r.i32() if file_version_ue4 >= 508 else 0  # VER_UE4_TEMPLATEINDEX_IN_COOKED_EXPORTS
            outer_idx = r.i32()
            object_name = fname(r)
            object_flags = r.u32()
            serial_size = r.i64()
            serial_offset = r.i64()
            r.i32(); r.i32(); r.i32()   # bForcedExport, bNotForClient, bNotForServer
            r.guid(); r.u32()           # PackageGuid + PackageFlags
            r.i32()                     # bNotAlwaysLoadedForEditorGame
            is_asset = r.i32()
            r.i32(); r.i32(); r.i32(); r.i32(); r.i32()  # 5 dependency ints
            exports.append({
                "name": object_name,
                "class": resolve(class_idx),
                "super": resolve(super_idx),
                "template": resolve(template_idx),
                "outer": resolve(outer_idx),
                "flags": object_flags,
                "serial_size": serial_size,
                "serial_offset": serial_offset,
                "is_asset": bool(is_asset),
            })
        except Exception as e:
            out.append(f"  !! export parse error at idx {i}: {e}")
            break

    out.append("")
    out.append("--- EXPORT TABLE ---")
    for i, e in enumerate(exports):
        out.append(f"  [{i+1:3d}] {e['name']!r}")
        out.append(f"        Class    = {e['class']}")
        out.append(f"        Super    = {e['super']}")
        out.append(f"        Template = {e['template']}")
        out.append(f"        Outer    = {e['outer']}")
        out.append(f"        Flags    = 0x{e['flags']:08X}, IsAsset={e['is_asset']}, SerialSize={e['serial_size']}")

    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    for p in sys.argv[1:]:
        path = Path(p)
        text = parse(path)
        out_path = path.with_suffix(".uasset.txt")
        out_path.write_text(text, encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
