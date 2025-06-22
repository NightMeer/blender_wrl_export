# -*- coding: utf-8 -*-

import bpy
import bmesh
import math
from mathutils import Matrix
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy.types import Operator

# --- HELPER-FUNKTIONEN ---

def get_material_properties(material):
    if not material: return (0.8, 0.8, 0.8, 1.0), 0.5, (0.2, 0.2, 0.2)
    return material.diffuse_color, material.roughness, material.specular_color

def write_wrl_shape_from_bmesh(f, bm, material, global_transform):
    if not bm.verts or not bm.faces: return
    f.write(f"Shape # Material: {material.name if material else 'Default'}\n{{\n")
    f.write("\tgeometry IndexedFaceSet {\n")
    verts_in_shape = list(bm.verts)
    f.write("\t\tcoord Coordinate { point [\n")
    for v in verts_in_shape:
        world_co = global_transform @ v.co
        f.write(f"\t\t\t{world_co.x:.6f} {world_co.y:.6f} {world_co.z:.6f},\n")
    f.write("\t\t] }\n")
    v_index_map = {v.index: i for i, v in enumerate(verts_in_shape)}
    f.write("\t\tcoordIndex [\n")
    for face in bm.faces:
        v1_new_idx = v_index_map[face.verts[0].index]
        v2_new_idx = v_index_map[face.verts[1].index]
        v3_new_idx = v_index_map[face.verts[2].index]
        f.write(f"\t\t\t{v1_new_idx} {v2_new_idx} {v3_new_idx} -1,\n")
    f.write("\t\t]\n")
    f.write("\t\tnormal Normal { vector [\n")
    normal_matrix = global_transform.to_3x3().inverted_safe().transposed()
    for v in verts_in_shape:
        transformed_normal = normal_matrix @ v.normal
        transformed_normal.normalize()
        f.write(f"\t\t\t{transformed_normal.x:.6f} {transformed_normal.y:.6f} {transformed_normal.z:.6f},\n")
    f.write("\t\t] }\n")
    f.write("\t\tnormalPerVertex TRUE\n\t\tsolid TRUE\n\t}\n")
    
    base_color, roughness, spec_color = get_material_properties(material)
    f.write("\tappearance Appearance {\n")
    f.write("\t\tmaterial Material {\n")
    f.write(f"\t\t\tdiffuseColor {base_color[0]:.4f} {base_color[1]:.4f} {base_color[2]:.4f}\n")
    f.write(f"\t\t\ttransparency {1.0 - base_color[3]:.4f}\n")
    f.write(f"\t\t\tshininess {1.0 - roughness:.4f}\n")
    f.write("\t\t}\n\t}\n")
    f.write("}\n\n")

# --- HAUPT-OPERATOR-KLASSE ---

class EXPORT_OT_blender_wrl(Operator, ExportHelper):
    bl_idname = "export_scene.blender_wrl_export"
    bl_label = "Blender WRL Export (.wrl)"
    bl_options = {'PRESET'}
    filename_ext = ".wrl"
    filter_glob: StringProperty(default="*.wrl", options={'HIDDEN'}, maxlen=255)
    
    use_selection: BoolProperty(name="Nur Auswahl", default=True)
    apply_correction: BoolProperty(name="Blender-Einheitenfehler korrigieren", default=True)
    scale_factor: FloatProperty(name="Manueller Skalierungsfaktor", default=1.0)
    apply_axis_conversion: BoolProperty(name="Achsen für KiCad konvertieren", default=True)
    export_materials: BoolProperty(name="Materialien exportieren", default=True)
    apply_modifiers: BoolProperty(name="Modifier anwenden", default=True)
    recalculate_normals: BoolProperty(name="Normalen konsistent ausrichten", default=True)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "use_selection")
        box = layout.box(); box.label(text="CAD / KiCad Kompatibilität:")
        box.prop(self, "apply_correction"); box.prop(self, "scale_factor"); box.prop(self, "apply_axis_conversion")
        box = layout.box(); box.label(text="Daten-Optionen:")
        box.prop(self, "export_materials"); box.prop(self, "apply_modifiers"); box.prop(self, "recalculate_normals")

    def execute(self, context):
        filepath = self.filepath
        
        source_list = context.scene.objects
        if self.use_selection and context.selected_objects: source_list = context.selected_objects
        objects_to_export = [obj for obj in source_list if obj.type == 'MESH' and obj.visible_get()]
        
        if not objects_to_export:
            self.report({'WARNING'}, "Keine passenden sichtbaren Mesh-Objekte gefunden."); return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        
        base_transform_exporter = Matrix.Identity(4)
        if self.apply_axis_conversion: base_transform_exporter = Matrix.Rotation(math.radians(-90.0), 4, 'X')
        
        final_scale = self.scale_factor
        if self.apply_correction: final_scale *= 0.4
        if final_scale != 1.0: base_transform_exporter = Matrix.Scale(final_scale, 4) @ base_transform_exporter

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("#VRML V2.0 utf8\n# Exportiert mit Blender-WRL-Export (The Real API Fix)\n\n")

            for obj in objects_to_export:
                if self.apply_modifiers: eval_obj = obj.evaluated_get(depsgraph)
                else: eval_obj = obj
                
                try: source_mesh = eval_obj.to_mesh()
                except RuntimeError: continue
                
                source_bm = bmesh.new()
                source_bm.from_mesh(source_mesh)
                
                bmesh.ops.triangulate(source_bm, faces=source_bm.faces)
                
                if self.recalculate_normals:
                    bmesh.ops.recalc_face_normals(source_bm, faces=source_bm.faces)

                global_transform = base_transform_exporter @ obj.matrix_world
                
                has_materials = self.export_materials and obj.material_slots and any(s.material for s in obj.material_slots)

                if has_materials:
                    for slot_index, slot in enumerate(obj.material_slots):
                        mat = slot.material
                        if not mat: continue
                        bm_part = source_bm.copy()
                        faces_to_delete = [face for face in bm_part.faces if face.material_index != slot_index]
                        if faces_to_delete: bmesh.ops.delete(bm_part, geom=faces_to_delete, context='FACES')
                        verts_to_delete = [v for v in bm_part.verts if not v.link_faces]
                        if verts_to_delete: bmesh.ops.delete(bm_part, geom=verts_to_delete, context='VERTS')
                        if bm_part.faces: write_wrl_shape_from_bmesh(f, bm_part, mat, global_transform)
                        bm_part.free()
                else:
                    write_wrl_shape_from_bmesh(f, source_bm, None, global_transform)

                source_bm.free()

        self.report({'INFO'}, f"Erfolgreich {len(objects_to_export)} Objekt(e) exportiert."); return {'FINISHED'}

# --- REGISTRIERUNGSFUNKTIONEN ---
classes_to_register = (EXPORT_OT_blender_wrl,)
def menu_func_export(self, context): self.layout.operator(EXPORT_OT_blender_wrl.bl_idname, text=EXPORT_OT_blender_wrl.bl_label)
def register_classes():
    for cls in classes_to_register: bpy.utils.register_class(cls)
def unregister_classes():
    for cls in reversed(classes_to_register): bpy.utils.unregister_class(cls)