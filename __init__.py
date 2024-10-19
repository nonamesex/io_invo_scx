bl_info = {
    "name": "Import Invictus SLRR SCX (.scx/.scy)",
    "author": "downsided",
    "description": "Import SCX v4 meshes",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "warning": "Using this tool causes autism. \nSCX v3 not supported yet.",
    "doc_url": "https://github.com/nonamesex/io_invo_scx",
    "tracker_url": "https://github.com/nonamesex/io_invo_scx/issues",
    "category": "Import"
}

if 'bpy' in locals():
    import importlib

    importlib.reload(scx_import_ot)
else:
    from .src import scx_import_ot

import bpy
from bpy.props import PointerProperty

classes = scx_import_ot.classes

def scx_import_menu_func(self, context):
    self.layout.operator(scx_import_ot.SCX_OT_import.bl_idname, text='Invictus SLRR SCX (.scx/.scy)')

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(scx_import_menu_func)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(scx_import_menu_func)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == '__main__':
    register()
