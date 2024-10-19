import os
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
