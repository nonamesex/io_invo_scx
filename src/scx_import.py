import os
import bpy
from pathlib import Path
from .BinaryReader import BinaryReader

from .scx_v3 import (
    read_scx_data as read_scx_data_v3,
    build_mesh as build_mesh_v3
)

from .scx_v4 import (
    read_scx_data as read_scx_data_v4,
    build_mesh as build_mesh_v4
)

def read_tex_list(scx_path: str, encoding: str = "UTF-8"):
    tex_path = os.path.splitext(scx_path)[0] + ".tex"
    tex_list = []

    if os.path.isfile(tex_path):
        try:
            with open(tex_path, "rt", encoding = encoding) as tex:
                for line in tex.readlines():
                    tex_name = line.strip("\r\n").split(maxsplit = 1)

                    if len(tex_name) == 0:
                        break
                    else:
                        tex_name = tex_name[0]

                    tex_name = tex_name.split(">>>>>", 1)
                    if len(tex_name) > 1:
                        tex_name = tex_name[1]
                    else:
                        tex_name = tex_name[0]

                    tex_list.append(tex_name)
        except UnicodeDecodeError:
            if encoding == "UTF-8":
                tex_list = read_tex_list(scx_path, "ANSI")
            elif encoding == "ANSI":
                tex_list = read_tex_list(scx_path, "cp1251")
            else:
                tex_list = []

    return tex_list

def read_scx_data(scx_path: str):
    with BinaryReader(scx_path) as scx:
        signature = scx.ReadSizedString(4)
        if signature != "INVO":
            print("not invictus object")
            return

        version = scx.ReadUInt32()
        if version == 3:
            return read_scx_data_v3(scx)
        elif version == 4:
            return read_scx_data_v4(scx)
        else:
            print(f"SCX v{version} not supported")
            return

def import_scx(scx_path: str):
    print(f"Importing {scx_path}")
    scx_name = Path(scx_path).stem
    scx_data = read_scx_data(scx_path)
    tex_list = read_tex_list(scx_path)
    if scx_data:
        if scx_data["version"] == 3:
            build_mesh_v3()
        elif scx_data["version"] == 4:
            build_mesh_v4(scx_data["meshes"], scx_name, tex_list)

def scx_import(scx_paths: str):
    for scx_path in scx_paths:
        import_scx(scx_path)

def import_scx_from_dir(scx_dir_path: str):
    for root, dirs, files in os.walk(scx_dir_path, False):
        for file in files:
            if file.lower().endswith(".scx"):
                import_scx(os.path.join(root, file))

def clear_scene():
    for object in bpy.context.scene.objects:
        bpy.data.objects.remove(object, do_unlink=True)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    for texture in bpy.data.textures:
        bpy.data.textures.remove(texture)
    for image in bpy.data.images:
        bpy.data.images.remove(image)
    bpy.ops.outliner.orphans_purge(
        do_local_ids = True,
        do_linked_ids = True,
        do_recursive = True
    )

if __name__ == "__main__":
    clear_scene()
    #import_scx("X:\\scx\\chassis.scx")
    #import_scx("X:\\Downloads\\SLRR-LE\\SLRR Light Edition\\cars\\traffic\\Ambulance_data\\meshes\\chassis.scx")
    #import_scx("X:\\Downloads\\AutoSaloonMagicke TRACK DAY SPARES 9-4\\parts\\AutoSaloonMagicke_TrackDay_Spares\\meshes\\Work_VSSS.scx")
    #import_scx_from_dir("X:\\Downloads\\AutoSaloonMagicke TRACK DAY SPARES 9-4\\parts\\AutoSaloonMagicke_TrackDay_Spares\\meshes")

    # test all this shit
    #import_scx_from_dir("X:\\Downloads\\SLRR-LE\\SLRR Light Edition", True)
    #import_scx("X:\\Downloads\\SLRR-LE\\SLRR Light Edition\\objects\\meshes\\03x6_ajto\\phys_1.scx") # wow physmesh
    #import_scx("X:\\Downloads\\SLRR-LE\\SLRR Light Edition\\objects\\meshes\\area_96_egyedi_b\\area_96_egyedi_b.scx") # BMFace removed? wtf
    #import_scx_from_dir("X:\\Downloads\\SLRR-LE\\SLRR Light Edition", True)
    import_scx_from_dir("X:\\Program Files (User)\\qBittorrent Downloads\\slrr\\maps")
    #import_scx("X:\\Program Files (User)\\qBittorrent Downloads\\slrr\\cars\\racers\\AsconaC_data\\meshes\\R_headlights_4.scx") # mapIndex > mapCount
    #import_scx("X:\\Program Files (User)\\qBittorrent Downloads\\slrr\\cars\\racers\\Charger69_RT_data\\meshes\\chassis.scx") # texList encoding
