from pathlib import Path

import bmesh
import bpy
from .BinaryReader import BinaryReader

SKIP_DOUBLESIDE_FACES = True # I'm not sure we shouldn't skip such faces
RE_USE_MATERIALS = False # Don't use this. It's wrong. But if you know what you're doing, then please...
JOIN_MESHES = False # It can have destructive effects. But who gives a fuck?

class MaterialFlags():
    def __init__(self, int):
        self.int = int

        self.__material_flags__ = [
            ["AlphaOpacity", 0x1],
            ["VecrtexColorBlend", 0x2],
            ["Layer2BlendByAlpha", 0x40],
            ["DiffuseBlend", 0x100],
            ["Layer2VertexColorBlend", 0x1000]
        ]

        for flag in self.__material_flags__:
            self.__setattr__(flag[0], (int & flag[1] & 0xFFFFFFFF) != 0)

    def __int__(self):
        return self.int

    def __str__(self):
        return f"< {' | '.join([x[0] for x in self.__material_flags__ if self.__getattribute__(x[0]) == True])} >"

def read_material_data(scx: BinaryReader):
    size = scx.ReadUInt32()

    if size == 0:
        return False

    material = {}

    material["size"] = size
    material["DiffuseColor"] = [ scx.ReadSingle(), scx.ReadSingle(), scx.ReadSingle(), scx.ReadSingle() ]
    material["SpecularColor"] = [ scx.ReadSingle(), scx.ReadSingle(), scx.ReadSingle() ]
    material["SpecularIntensity"] = scx.ReadSingle()
    material["GlossinesWeight"] = scx.ReadSingle()

    material["Flags"] = MaterialFlags(scx.ReadUInt32())

    material["DiffuseMapIndex"] = scx.ReadUInt16()
    material["BumpMapIndex"] = scx.ReadUInt16()
    material["SpecularMapIndex"] = scx.ReadUInt16()
    material["ReflectionMapIndex"] = scx.ReadUInt16()
    material["DiffuseLayer2MapIndex"] = scx.ReadUInt16()
    scx.seek(2)

    if size > 56:
        material["IlluninationMapIndex"] = scx.ReadUInt16()
        scx.seek(2)
        material["VertexSize"] = scx.ReadUInt32()
        scx.seek(4 + 2)
        material["DiffuseMix1MapChannel"] = scx.ReadUInt16()
        material["DiffuseMix2MapChannel"] = scx.ReadUInt16()
        material["BumpMapChannel"] = scx.ReadUInt16()
        material["SpecularMapChannel"] = scx.ReadUInt16()
        scx.seek(2 + 4 + 4 + 4)
        material["IlluminationColor"] = [ scx.ReadSingle(), scx.ReadSingle(), scx.ReadSingle() ]

    if size > 104:
        material["name"] = scx.ReadNullTerminatedSizedString(32)

    return material

def read_vertex_data(scx: BinaryReader, material_size):
    vertex_count = scx.ReadUInt32()

    data = {
        "count": vertex_count,
        "Position": [],
        "Normal": [],
        "UV1": [],
        "UV2": [],
        "Color": [],
        "UV3": []
    }

    for i in range(vertex_count):
        x, y, z = scx.ReadSingle() / 100, scx.ReadSingle() / 100, scx.ReadSingle() / 100
        data["Position"].append([ x, -z, y ])
        x, y, z = scx.ReadSingle(), scx.ReadSingle(), scx.ReadSingle()
        data["Normal"].append([ x, -z, y ])
        data["UV1"].append([ scx.ReadSingle(), 1 - scx.ReadSingle() ])
        data["UV2"].append([ scx.ReadSingle(), 1 - scx.ReadSingle() ])
        data["Color"].append([ scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255, scx.ReadByte() / 255 ])

        if material_size > 56:
            scx.seek(4 + 4)
            data["UV3"].append([ scx.ReadSingle(), 1 - scx.ReadSingle() ])
            scx.seek(4)

    return data

def read_indices_data(scx: BinaryReader):
    face_count = scx.ReadUInt32()

    triangles = []

    for i in range(face_count):
        triangles.append([ scx.ReadUInt32(), scx.ReadUInt32(), scx.ReadUInt32() ])

    return triangles

def read_scx_data(scx: BinaryReader):
    pos = scx.tell()
    scx.seek(0, 2)
    EOF = scx.tell()
    scx.seek(pos, 0)

    meshes_data = []

    while not (scx.tell() == EOF or 4 >= (EOF - scx.tell())):
        mesh_data = {}

        mesh_data["material"] = read_material_data(scx)
        if mesh_data["material"] == False:
            break
        else:
            mesh_data["vertex"] = read_vertex_data(scx, mesh_data["material"]["size"])
            mesh_data["face"] = read_indices_data(scx)

            meshes_data.append(mesh_data)

    return {"meshes": meshes_data, "version": 3}

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
    if material_data.get("DiffuseMapIndex"):
        if material_data["DiffuseMapIndex"] != 0xFFFF:
            image_node.image = get_material_texture(material_data["DiffuseMapIndex"], tex_list, material_data["name"])
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
            if not material_data.get("name"):
                material_data["name"] = scx_name

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

        uv_layer1 = bm.loops.layers.uv.new("UV1")
        uv_layer2 = bm.loops.layers.uv.new("UV2")
        vertex_color = bm.loops.layers.color.new("Color")
        if material_data["size"] > 56:
            uv_layer3 = bm.loops.layers.uv.new("UV3")

        verts = []

        for i in range(vertex_data["count"]):
            vertex = bm.verts.new(vertex_data["Position"][i])
            vertex.normal = vertex_data["Normal"][i]
            vertex.index = i

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
                loop[vertex_color] = vertex_data["Color"][loop.vert.index]
                loop[uv_layer1].uv = vertex_data["UV1"][loop.vert.index]
                loop[uv_layer2].uv = vertex_data["UV2"][loop.vert.index]
                if material_data["size"] > 56:
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
