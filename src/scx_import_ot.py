import os
import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from .scx_import import scx_import
from .scx_v4 import setup_flags as setup_flags_v4

empty_set = set()

class SCX_OT_import(Operator, ImportHelper):
    bl_idname = 'import_mesh.scx'
    bl_label = 'Import (.scx/.scy)'
    bl_options = {'INTERNAL', 'UNDO', 'PRESET'}

    __doc__ = 'Load a SCX file'

    filename_ext = '.scx'
    filter_glob: StringProperty(default='*.scx;*.scy', options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.PropertyGroup)

    join_meshes: BoolProperty(
        default = False,
        name = 'Join Meshes',
        options = empty_set,
        description = "It can have destructive effects. But who gives a fuck?"
    )

    re_use_materials: BoolProperty(
        default = False,
        name = 'Re-use Materials',
        options = empty_set,
        description = "Don't use this. It's wrong. But if you know what you're doing, then please..."
    )

    skip_doubleside_faces: BoolProperty(
        default = True,
        name = 'Skip Double-side Faces',
        options = empty_set,
        description = "I'm not sure we shouldn't skip such faces"
    )

    def execute(self, context):
        dir = os.path.dirname(self.filepath)
        files = [os.path.join(dir, i.name) for j, i in enumerate(self.files)]

        setup_flags_v4(
            self.join_meshes,
            self.re_use_materials,
            self.skip_doubleside_faces
        )

        scx_import(files)

        self.report({'INFO'}, f'SCX imported')

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'join_meshes')
        layout.prop(self, 're_use_materials')
        layout.prop(self, 'skip_doubleside_faces')

classes = (
    SCX_OT_import,
)
