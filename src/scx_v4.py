from pathlib import Path

import bmesh
import bpy
from .BinaryReader import BinaryReader

SKIP_DOUBLESIDE_FACES = True # I'm not sure we shouldn't skip such faces
RE_USE_MATERIALS = False # Don't use this. It's wrong. But if you know what you're doing, then please...
JOIN_MESHES = False # It can have destructive effects. But who gives a fuck?

class VertexTypeFlags():
    def __init__(self, int):
        self.int = int

        self.__vertex_type_flags__ = [
            ["Position", 0x1],
            ["BoneWeight0", 0x2],
            ["BoneWeight1", 0x4],
            ["BoneWeight2", 0x8],
            ["BoneWeight3", 0x10],
            ["BoneIndRef", 0x20],
            ["Normal", 0x40],
            ["VertexEmissive", 0x80],
            ["VertexColor", 0x100],
            ["UV1", 0x200],
            ["UV2", 0x400],
            ["UV3", 0x800],
            ["BumpMapNormal", 0x40000]
        ]

        for flag in self.__vertex_type_flags__:
            self.__setattr__(flag[0], (int & flag[1] & 0xFFFFFFFF) != 0)

    def __int__(self):
        return self.int

    def __str__(self):
        return f"< {' | '.join([x[0] for x in self.__vertex_type_flags__ if self.__getattribute__(x[0]) == True])} >"

def read_material_map(scx: BinaryReader):
    map = {}
    map["index"] = scx.ReadUInt32()
    map["channel"] = scx.ReadUInt32()
    map["tillingFlag"] = scx.ReadUInt32()
    map["tilling"] = [ scx.ReadSingle(), scx.ReadSingle() ]
    map["offset"] = [ scx.ReadSingle(), scx.ReadSingle() ]
    return map

def read_material_data(scx: BinaryReader):
    scx.seek(4 * 4)

    entries_count = scx.ReadUInt32()
    entries = {}

    for i in range(entries_count):
        entry_type = scx.ReadUInt32()

        match entry_type:
            case 0x00000000:
                entries["DiffuseColor"] = [ scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255 ]
            case 0x00000001:
                entries["SpecularColor"] = [ scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255 ]
            case 0x00000002:
                entries["EmissiveColor"] = [ scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255 ]

            case 0x01000000:
                entries["SpecularIntensity"] = scx.ReadSingle() / 100
            case 0x01000001:
                entries["ReflectionIntensity"] = scx.ReadSingle() / 100
            case 0x01000002:
                entries["BumpIntensity"] = scx.ReadSingle() / 100

            case 0x06000000:
                entries["DiffuseMap"] = read_material_map(scx)
            case 0x06000001:
                entries["DiffuseMixSecond"] = read_material_map(scx)
            case 0x06000002:
                entries["BumpMap"] = read_material_map(scx)
            case 0x06000003:
                entries["ReflectionMap"] = read_material_map(scx)
            case 0x06000004:
                entries["EmissiveMap"] = read_material_map(scx)

            case 0x08000000:
                entries["name"] = scx.ReadNullTerminatedSizedString(32)

    return entries

def read_vertex_data(scx: BinaryReader):
    scx.seek(4 * 2)

    vetrex_count = scx.ReadUInt32()
    vertex_type = scx.ReadUInt32()
    vertex_flags = VertexTypeFlags(vertex_type)

    data = {
        "type": vertex_flags,
        "count": vetrex_count,
        "Position": [],
        "BoneWeight0": [],
        "BoneWeight1": [],
        "BoneWeight2": [],
        "BoneWeight3": [],
        "BoneIndRef": [],
        "Normal": [],
        "Emissive": [],
        "Color": [],
        "UV1": [],
        "UV2": [],
        "UV3": [],
        "BumpMapNormal": []
    }

    for i in range(vetrex_count):
        if vertex_flags.Position:
            x, y, z = scx.ReadSingle() / 100, scx.ReadSingle() / 100, scx.ReadSingle() / 100
            data["Position"].append([ x, -z, y ])
        if vertex_flags.BoneWeight0:
            scx.seek(4)
        if vertex_flags.BoneWeight1:
            scx.seek(4)
        if vertex_flags.BoneWeight2:
            scx.seek(4)
        if vertex_flags.BoneWeight3:
            scx.seek(4)
        if vertex_flags.BoneIndRef:
            scx.seek(4)
        if vertex_flags.Normal:
            x, y, z = scx.ReadSingle(), scx.ReadSingle(), scx.ReadSingle()
            data["Normal"].append([ x, -z, y ])
        if vertex_flags.VertexEmissive:
            data["Emissive"].append([ scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255 ])
        if vertex_flags.VertexColor:
            data["Color"].append([ scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255 ])
        if vertex_flags.UV1:
            data["UV1"].append([ scx.ReadSingle(), 1 - scx.ReadSingle() ])
        if vertex_flags.UV2:
            data["UV2"].append([ scx.ReadSingle(), 1 - scx.ReadSingle() ])
        if vertex_flags.UV3:
            data["UV3"].append([ scx.ReadSingle(), 1 - scx.ReadSingle() ])
        if vertex_flags.BumpMapNormal:
            scx.seek(4 * 3)

    return data

def read_indices_data(scx: BinaryReader):
    scx.seek(4 * 2)

    indices_count = scx.ReadUInt32()
    triangles = []

    for i in range(int(indices_count / 3)):
        triangles.append([ scx.ReadUInt16(), scx.ReadUInt16(), scx.ReadUInt16() ])

    return triangles

def read_scx_data(scx: BinaryReader):
    header_entries_count = scx.ReadUInt32()

    mesh_num = -1
    meshes_data = []
    is_phys_mesh = False

    for i in range(header_entries_count):
        entry_type = scx.ReadUInt32()
        entry_offset = scx.ReadUInt32()

        pos = scx.tell()
        scx.seek(entry_offset, 0)

        if mesh_num == -1 and entry_type == 1:
            is_phys_mesh = True

        if (entry_type == 1 and is_phys_mesh) or entry_type == 0:
            mesh_num += 1
            meshes_data.append({})

        if entry_type == 0:
            meshes_data[mesh_num]["material"] = read_material_data(scx)
        elif entry_type == 4:
            meshes_data[mesh_num]["vertex"] = read_vertex_data(scx)
        elif entry_type == 5:
            meshes_data[mesh_num]["face"] = read_indices_data(scx)

        scx.seek(pos, 0)

    return {"meshes": meshes_data, "version": 4}

def get_material_texture(index: int, tex_list: list, material_name: str):
    texture_name = f"{material_name}_0x{index:08X}".lower()
    texture_path = ""

    if len(tex_list) > 0 and len(tex_list) > index:
        texture_path = tex_list[index]
        texture_name = Path(texture_path).stem

    image = bpy.data.images.get(texture_name)

    if not image:
        image = bpy.data.images.new(texture_name, 1, 1)
        image.filepath = texture_path
        image.source = "FILE"

    return image

def get_material(material_data: list, tex_list: list):
    if RE_USE_MATERIALS:
        material_node = bpy.data.materials.get(material_data["name"])
        if material_node:
            return material_node

    material_node = bpy.data.materials.new(name = material_data["name"])
    material_node.preview_render_type = "FLAT"
    material_node.use_nodes = True
    material_node.diffuse_color = material_data["DiffuseColor"]
    if material_data.get("SpecularColor"):
        material_node.specular_color = material_data["SpecularColor"][0:3]
    material_node.roughness = 0
    if material_data.get("SpecularIntensity"):
        material_node.specular_intensity = material_data["SpecularIntensity"]
    material_node.metallic = 0
    material_node.blend_method = 'BLEND'
    material_node.show_transparent_back = False

    material_nodes = material_node.node_tree.nodes

    material_bsdf = material_nodes["Principled BSDF"]
    material_bsdf.show_options = False
    material_bsdf.inputs[0].default_value = material_data["DiffuseColor"] # BaseColor
    material_bsdf.inputs[6].default_value = 0 # Metallic
    if material_data.get("SpecularIntensity"):
        material_bsdf.inputs[7].default_value = material_data["SpecularIntensity"] # Specular
    material_bsdf.inputs[9].default_value = 0 # Roughness

    image_node = material_nodes.new(type = "ShaderNodeTexImage")
    image_node.location = (-280, 300)
    image_node.interpolation = "Cubic"
    if material_data.get("DiffuseMap"):
        image_node.image = get_material_texture(material_data["DiffuseMap"]["index"], tex_list, material_data["name"])
        image_node.image.alpha_mode = "STRAIGHT"
    elif material_data.get("DiffuseMixSecond"):
        image_node.image = get_material_texture(material_data["DiffuseMixSecond"]["index"], tex_list, material_data["name"])
        image_node.image.alpha_mode = "STRAIGHT"

    material_links = material_node.node_tree.links

    material_links.new(
        image_node.outputs["Color"],
        material_bsdf.inputs["Base Color"]
    )

    material_links.new(
        image_node.outputs["Alpha"],
        material_bsdf.inputs["Alpha"]
    )

    return material_node

def build_mesh(scx_data: list, scx_name: str, tex_list: list):
    bpy.ops.object.empty_add(type="ARROWS")
    scx_empty = bpy.context.view_layer.objects.active
    scx_empty.name = scx_name

    for mesh_data in scx_data:
        material_data = mesh_data.get("material")

        if material_data:
            mesh_name = material_data["name"]
        else:
            mesh_name = scx_name

        bpy_mesh = bpy.data.meshes.new(mesh_name)
        bpy_obj = bpy.data.objects.new(mesh_name, bpy_mesh)
        bpy.context.scene.collection.objects.link(bpy_obj)
        bpy_obj.parent = scx_empty

        bm = bmesh.new()
        bm.from_mesh(bpy_mesh)

        vertex_data = mesh_data["vertex"]
        vertex_type: VertexTypeFlags = vertex_data["type"]

        print(scx_name, bpy_obj.name, vertex_type)

        if vertex_type.VertexEmissive:
            vertex_emissive = bm.loops.layers.color.new("Emissive")
        if vertex_type.VertexColor:
            vertex_color = bm.loops.layers.color.new("Color")
        if vertex_type.UV1:
            uv_layer1 = bm.loops.layers.uv.new("UV1")
        if vertex_type.UV2:
            uv_layer2 = bm.loops.layers.uv.new("UV2")
        if vertex_type.UV3:
            uv_layer3 = bm.loops.layers.uv.new("UV3")

        verts = []

        for i in range(vertex_data["count"]):
            vertex = bm.verts.new(vertex_data["Position"][i])
            vertex.index = i

            if vertex_type.Normal:
                vertex.normal = vertex_data["Normal"][i]

            verts.append(vertex)

        for indices in mesh_data["face"]:
            try:
                face = bm.faces.new([verts[indices[0]], verts[indices[1]], verts[indices[2]]])
                face.smooth = True
            except:
                if SKIP_DOUBLESIDE_FACES:
                    pass
                else:
                    face = bm.faces.get([verts[indices[0]], verts[indices[1]], verts[indices[2]]])
                    if face:
                        face = face.copy(verts=False, edges=True)
                        face.normal_flip()
                        face.smooth = True

        for face in bm.faces:
            for loop in face.loops:
                if vertex_type.VertexEmissive:
                    loop[vertex_emissive] = vertex_data["Emissive"][loop.vert.index]
                if vertex_type.VertexColor:
                    loop[vertex_color] = vertex_data["Color"][loop.vert.index]
                if vertex_type.UV1:
                    loop[uv_layer1].uv = vertex_data["UV1"][loop.vert.index]
                if vertex_type.UV2:
                    loop[uv_layer2].uv = vertex_data["UV2"][loop.vert.index]
                if vertex_type.UV3:
                    loop[uv_layer3].uv = vertex_data["UV3"][loop.vert.index]

        bm.to_mesh(bpy_mesh)
        bm.free()

        mesh_data["object"] = bpy_obj

        if material_data:
            bpy_mesh.materials.append(get_material(material_data, tex_list))

    if JOIN_MESHES:
        bpy_main_obj = scx_data[0]["object"]

        for i in range(1, len(scx_data)):
            bpy.ops.object.select_all(action = "DESELECT")
            scx_data[i]["object"].select_set(True)
            bpy_main_obj.select_set(True)
            bpy.context.view_layer.objects.active = bpy_main_obj
            bpy.ops.object.join()

        with bpy.context.temp_override(selected_objects=[scx_empty]):
            bpy.ops.object.delete()

        bpy_main_obj.name = scx_name
        bpy_main_obj.data.name = scx_name

def setup_flags(join_meshes = False, re_use_materials = False, skip_doubleside_faces = True):
    global JOIN_MESHES
    JOIN_MESHES = join_meshes
    global RE_USE_MATERIALS
    RE_USE_MATERIALS = re_use_materials
    global SKIP_DOUBLESIDE_FACES
    SKIP_DOUBLESIDE_FACES = skip_doubleside_faces
