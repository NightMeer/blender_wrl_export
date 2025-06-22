# -*- coding: utf-8 -*-
bl_info = {
    "name": "Blender-WRL-Export",
    "author": "NightMeer",
    "version": (21, 0, 0), # Bugfix: Use correct, existing API call for normals
    "blender": (4, 0, 0),
    "location": "Datei > Export > Blender WRL Export (.wrl)",
    "description": "VRML 2.0 Exporteur",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

import bpy
if "bpy" in locals():
    import importlib
    if "operator" in locals():
        importlib.reload(operator)
from . import operator
def register():
    operator.register_classes()
    bpy.types.TOPBAR_MT_file_export.append(operator.menu_func_export)
def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(operator.menu_func_export)
    operator.unregister_classes()
if __name__ == "__main__":
    register()