#!/usr/bin/env python3
"""
patch_struct_rename.py
======================

Recover a UE4 .uasset file whose serialized property data references a
struct that has since been renamed in C++ (i.e. an `OldStructName` ->
`NewStructName` rename in engine code, where the new struct keeps the
same field layout but lives under a different name).

When such a rename happens without a CoreRedirect, the editor can't
deserialize the struct on load and silently re-saves the asset with all
struct fields zeroed/defaulted — destroying the original data.

This patcher takes the *original* .uasset (e.g. extracted from a
workshop pak) and renames a single name-table entry in place. Because
property data references names by *index* (not by string), the rename
preserves all field values; only the struct's identifier changes. The
patched file then loads cleanly in the new engine version with all data
intact.

The two struct types must have identical fields and serialization
layout. If the new struct added/removed fields, this won't work — UE
will skip the unrecognised field tags on load.

Tested against the Last Oasis Modkit's UE 4.25 build. The header walk
hardcodes one Modkit-specific quirk: `FCompressedChunk` serializes as
20 bytes per entry instead of the documented 16.

Usage
-----

    python patch_struct_rename.py <input.uasset> <output.uasset> <old_name> <new_name>

Prints the offset shifts it applied. The output file is the same size
as the input minus `len(old_name) - len(new_name)` bytes.

Recipe (full asset recovery)
----------------------------

  1. Extract the original from the workshop pak:
       Add-Type -AssemblyName System.IO.Compression.FileSystem
       $z = [System.IO.Compression.ZipFile]::OpenRead('.../<id>.zip')
       $entry = $z.Entries | ? { $_.FullName -like '*Path/MyAsset.uasset' }
       [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, 'orig.uasset', $true)
       $z.Dispose()

  2. Patch the struct rename:
       python patch_struct_rename.py orig.uasset patched.uasset OldStruct NewStruct

  3. Verify with `dump_props.py` that the values are intact:
       python dump_props.py patched.uasset

  4. Close the editor (important — running editors will overwrite your
     patched file with their stale in-memory copy on close).

  5. Install patched.uasset in BOTH locations (the Modkit syncs from
     Saved/Mods/<Mod>/Assets/... -> Content/Mods/<Mod>/... on load):
       Game/Content/Mods/<Mod>/Path/MyAsset.uasset
       Game/Saved/Mods/<Mod>/Assets/Mods/<Mod>/Path/MyAsset.uasset

  6. Open the editor, verify the asset, and save it from inside the
     editor so it gets re-serialized with the new struct name as
     canonical.

Standard library only — no `pip install` step.
"""
import struct
import sys
from pathlib import Path


class Patcher:
    def __init__(self, path):
        self.data = bytearray(Path(path).read_bytes())

    def i32(self, pos): return struct.unpack_from("<i", self.data, pos)[0]
    def u32(self, pos): return struct.unpack_from("<I", self.data, pos)[0]
    def i64(self, pos): return struct.unpack_from("<q", self.data, pos)[0]
    def write_i32(self, pos, val): struct.pack_into("<i", self.data, pos, val)
    def write_i64(self, pos, val): struct.pack_into("<q", self.data, pos, val)

    def fstring_byte_len(self, pos):
        n = self.i32(pos)
        if n == 0: return 4
        if n > 0: return 4 + n
        return 4 + (-n) * 2

    def fstring_read(self, pos):
        n = self.i32(pos)
        if n == 0: return "", 4
        if n > 0:
            s = bytes(self.data[pos+4:pos+4+n-1]).decode("ascii", errors="replace")
            return s, 4 + n
        s = bytes(self.data[pos+4:pos+4+(-n-1)*2]).decode("utf-16-le", errors="replace")
        return s, 4 + (-n) * 2

    def parse_header(self):
        """Walk the header and record positions of all offset fields."""
        p = 0
        if self.u32(p) != 0x9E2A83C1:
            raise RuntimeError("Not a UAsset file (bad magic)")
        p += 4
        self.legacy_file_version = self.i32(p); p += 4
        if self.legacy_file_version != -4:
            p += 4  # LegacyUE3Version
        self.fv4 = self.i32(p); p += 4
        p += 4  # FileVersionLicenseeUE4
        if self.legacy_file_version <= -2:
            cv_count = self.i32(p); p += 4
            p += cv_count * 20  # 16-byte GUID + 4-byte version
        self.pos_total_header_size = p; p += 4
        p += self.fstring_byte_len(p)  # FolderName
        p += 4  # PackageFlags
        self.name_count = self.i32(p); p += 4
        self.pos_name_offset = p; p += 4
        if self.fv4 >= 518:
            p += self.fstring_byte_len(p)  # LocalizationId
        self.pos_gtd_offset = None
        if self.fv4 >= 459:
            p += 4  # GatherableTextDataCount
            self.pos_gtd_offset = p; p += 4
        self.export_count = self.i32(p); p += 4
        self.pos_export_offset = p; p += 4
        self.import_count = self.i32(p); p += 4
        self.pos_import_offset = p; p += 4
        self.pos_depends_offset = p; p += 4
        self.pos_soft_pkg_refs_offset = None
        if self.fv4 >= 459:  # VER_UE4_ADDED_SOFT_OBJECT_PATH
            p += 4  # SoftPackageReferencesCount
            self.pos_soft_pkg_refs_offset = p; p += 4
        self.pos_searchable_names_offset = None
        if self.fv4 >= 510:
            self.pos_searchable_names_offset = p; p += 4
        self.pos_thumbnail_offset = p; p += 4
        p += 16  # Guid
        gen_count = self.i32(p); p += 4
        p += gen_count * 8
        # SavedByEngineVersion: u16 major, u16 minor, u16 patch, u32 changelist, FString branch
        p += 2 + 2 + 2 + 4
        p += self.fstring_byte_len(p)
        if self.fv4 >= 433:
            p += 2 + 2 + 2 + 4
            p += self.fstring_byte_len(p)  # CompatibleWithEngineVersion
        p += 4  # CompressionFlags
        cc_count = self.i32(p); p += 4
        # FCompressedChunk in the Modkit's UE 4.25 build serializes as 20 bytes per entry
        # (not the documented 16). Empirically derived from header layout matching.
        p += cc_count * 20
        p += 4  # PackageSource
        ap_count = self.i32(p); p += 4
        for _ in range(ap_count):
            p += self.fstring_byte_len(p)
        self.pos_asset_registry_offset = p; p += 4
        self.pos_bulk_data_offset = p; p += 8  # int64
        self.pos_world_tile_offset = p; p += 4
        chunk_count = self.i32(p); p += 4
        p += chunk_count * 4
        self.pos_preload_dep_offset = None
        if self.fv4 >= 507:
            p += 4  # PreloadDependencyCount
            self.pos_preload_dep_offset = p; p += 4

    def find_name_entry(self, target):
        """Return (entry_start_pos, entry_total_size, fstring_len) for the named entry, or None."""
        p = self.i32(self.pos_name_offset)
        for _ in range(self.name_count):
            entry_start = p
            s, fstr_len = self.fstring_read(p)
            p += fstr_len
            if self.fv4 >= 504:
                p += 4  # uint16+uint16 hashes
            if s == target:
                return entry_start, (p - entry_start), fstr_len
        return None

    def parse_export_serial_offsets(self):
        """Return list of byte positions of each export's SerialOffset field."""
        p = self.i32(self.pos_export_offset)
        positions = []
        for _ in range(self.export_count):
            p += 4   # ClassIndex
            p += 4   # SuperIndex
            if self.fv4 >= 508:
                p += 4   # TemplateIndex
            p += 4   # OuterIndex
            p += 8   # ObjectName FName (idx + num)
            p += 4   # ObjectFlags
            p += 8   # SerialSize
            positions.append(p)
            p += 8   # SerialOffset
            p += 4 * 3   # bForcedExport + bNotForClient + bNotForServer
            p += 16      # PackageGuid
            p += 4       # PackageFlags
            p += 4 * 2   # bNotAlwaysLoadedForEditorGame + bIsAsset
            p += 4 * 5   # 5 dependency ints
        return positions

    def patch_rename(self, old_name, new_name):
        self.parse_header()

        loc = self.find_name_entry(old_name)
        if loc is None:
            raise RuntimeError(f"Name {old_name!r} not found in name table")
        entry_pos, entry_size, old_fstring_len = loc

        # Build the replacement entry (preserve the existing name hashes — UE recomputes on load).
        new_bytes = new_name.encode("ascii") + b"\x00"
        new_fstring = struct.pack("<i", len(new_bytes)) + new_bytes
        hash_bytes = bytes(self.data[entry_pos + old_fstring_len:entry_pos + entry_size])
        new_entry = new_fstring + hash_bytes
        delta = len(new_entry) - entry_size

        cutoff = entry_pos + entry_size  # in the original file, everything past this point shifts by `delta`

        print(f"Renaming '{old_name}' -> '{new_name}' (delta={delta} bytes)")
        print(f"  entry at offset {entry_pos}, size {entry_size}, cutoff {cutoff}")

        # Capture export SerialOffset positions BEFORE the splice (positions read here are in the original file).
        export_serial_positions = self.parse_export_serial_offsets()
        export_serials = [(pos, self.i64(pos)) for pos in export_serial_positions]

        # Read all header offset fields BEFORE the splice.
        offset_fields = []
        for desc, pos, size in [
            ("TotalHeaderSize",       self.pos_total_header_size,        4),
            ("NameOffset",            self.pos_name_offset,              4),
            ("GatherableTextOffset",  self.pos_gtd_offset,               4),
            ("ExportOffset",          self.pos_export_offset,            4),
            ("ImportOffset",          self.pos_import_offset,            4),
            ("DependsOffset",         self.pos_depends_offset,           4),
            ("SoftPkgRefsOffset",     self.pos_soft_pkg_refs_offset,     4),
            ("SearchableNamesOffset", self.pos_searchable_names_offset,  4),
            ("ThumbnailOffset",       self.pos_thumbnail_offset,         4),
            ("AssetRegistryOffset",   self.pos_asset_registry_offset,    4),
            ("BulkDataOffset",        self.pos_bulk_data_offset,         8),
            ("WorldTileOffset",       self.pos_world_tile_offset,        4),
            ("PreloadDepOffset",      self.pos_preload_dep_offset,       4),
        ]:
            if pos is None: continue
            val = self.i32(pos) if size == 4 else self.i64(pos)
            offset_fields.append((desc, pos, size, val))

        # Splice in the renamed entry.
        self.data[entry_pos:cutoff] = new_entry

        # Header positions (pos_*) are all before cutoff -- positions stay the same.
        # Update each header offset's value.
        for desc, pos, size, val in offset_fields:
            if desc == "TotalHeaderSize":
                new_val = val + delta
            elif val == 0:
                new_val = 0     # unset offsets remain unset
            elif val >= cutoff:
                new_val = val + delta
            else:
                new_val = val   # offset is before cutoff, no shift
            if size == 4:
                self.write_i32(pos, new_val)
            else:
                self.write_i64(pos, new_val)
            if new_val != val:
                print(f"  {desc:24s}: {val:>10} -> {new_val}")

        # Update each export's SerialOffset. The position itself shifts if the
        # export table is past cutoff, AND the value shifts if it points past cutoff.
        for orig_pos, orig_val in export_serials:
            new_pos = orig_pos + delta if orig_pos >= cutoff else orig_pos
            new_val = orig_val + delta if orig_val >= cutoff else orig_val
            self.write_i64(new_pos, new_val)
            if new_val != orig_val:
                print(f"  ExportSerialOffset@{orig_pos}: {orig_val} -> {new_val}")

        return bytes(self.data)


def main():
    if len(sys.argv) != 5:
        print(__doc__); sys.exit(1)
    inp, out, old_name, new_name = sys.argv[1:]
    p = Patcher(inp)
    patched = p.patch_rename(old_name, new_name)
    Path(out).write_bytes(patched)
    print(f"Wrote {out} ({len(patched)} bytes)")


if __name__ == "__main__":
    main()
