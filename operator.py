# -*- coding: utf-8 -*-

import bpy
import bmesh
import math
from mathutils import Matrix, Vector
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from bpy.types import Operator

# --- HELPER-FUNKTIONEN ---

def get_material_properties(material, color_source):
    """Liest Materialeigenschaften basierend auf der ausgewählten Quelle."""
    base_color = (0.8, 0.8, 0.8, 1.0) # Default Grau
    roughness = 0.5

    if not material:
        return base_color, roughness
    
    if color_source == 'SHADER' and material.use_nodes and material.node_tree:
        # Versuche, die Farbe aus dem Principled BSDF Shader zu lesen
        for node in material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                base_color_input = node.inputs.get('Base Color')
                if base_color_input:
                    if base_color_input.is_linked:
                        source_node = base_color_input.links[0].from_node
                        if source_node.type == 'RGB':
                            base_color = source_node.outputs['Color'].default_value
                    else:
                        base_color = base_color_input.default_value
                roughness_input = node.inputs.get('Roughness')
                if roughness_input: roughness = roughness_input.default_value
                return base_color, roughness
    
    # Fallback oder wenn 'VIEWPORT' ausgewählt ist
    return material.diffuse_color, material.roughness

def write_wrl_shape_from_bmesh(f, bm, material, global_transform, color_source):
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
        v1 = v_index_map[face.verts[0].index]
        v2 = v_index_map[face.verts[1].index]
        v3 = v_index_map[face.verts[2].index]
        f.write(f"\t\t\t{v1} {v2} {v3} -1,\n")
    f.write("\t\t]\n")
    f.write("\t\tnormal Normal { vector [\n")
    normal_matrix = global_transform.to_3x3().inverted_safe().transposed()
    for v in verts_in_shape:
        transformed_normal = (normal_matrix @ v.normal).normalized()
        f.write(f"\t\t\t{transformed_normal.x:.6f} {transformed_normal.y:.6f} {transformed_normal.z:.6f},\n")
    f.write("\t\t] }\n")
    f.write("\t\tnormalPerVertex TRUE\n\t\tsolid TRUE\n\t}\n")
    base_color, roughness = get_material_properties(material, color_source)
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
    center_object_origin: BoolProperty(name="Objektursprung zentrieren", description="Verschiebt das Objekt temporär in den Ursprung. Ersetzt manuelles Zentrieren und 'Apply Transforms'", default=True)
    
    export_materials: BoolProperty(name="Materialien exportieren", default=True)
    apply_modifiers: BoolProperty(name="Modifier anwenden", default=True)
    recalculate_normals: BoolProperty(name="Normalen konsistent ausrichten", default=True)
    color_source: EnumProperty(
        name="Farbquelle",
        description="Woher die Farbe für den Export gelesen werden soll",
        items=[('VIEWPORT', "Viewport Display", "Einfache Farbe aus dem Material-Tab (Ideal für CAD)"),
               ('SHADER', "Surface (Shader)", "Farbe aus dem 'Base Color'-Input des Principled BSDF Shaders")],
        default='VIEWPORT',
    )
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "use_selection")
        box = layout.box(); box.label(text="CAD / KiCad Kompatibilität:")
        box.prop(self, "center_object_origin")
        box.prop(self, "apply_correction")
        box.prop(self, "scale_factor")
        box.prop(self, "apply_axis_conversion")
        box = layout.box(); box.label(text="Daten-Optionen:")
        box.prop(self, "export_materials")
        box.prop(self, "apply_modifiers")
        box.prop(self, "recalculate_normals")
        if self.export_materials:
            box.prop(self, "color_source")

    def execute(self, context):
        filepath = self.filepath
        
        source_list = context.scene.objects
        if self.use_selection and context.selected_objects: source_list = context.selected_objects
        objects_to_export = [obj for obj in source_list if obj.type == 'MESH' and obj.visible_get()]
        
        if not objects_to_export:
            self.report({'WARNING'}, "Keine passenden sichtbaren Mesh-Objekte gefunden."); return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("#VRML V2.0 utf8\n# Exportiert mit Blender-WRL-Export (The Smart Assistant)\n\n")

            for obj in objects_to_export:
                if self.apply_modifiers: eval_obj = obj.evaluated_get(depsgraph)
                else: eval_obj = obj
                try: source_mesh = eval_obj.to_mesh()
                except RuntimeError: continue
                
                source_bm = bmesh.new(); source_bm.from_mesh(source_mesh)
                bmesh.ops.triangulate(source_bm, faces=source_bm.faces)
                if self.recalculate_normals: bmesh.ops.recalc_face_normals(source_bm, faces=source_bm.faces)
                
                # --- NEUE, AUTOMATISCHE TRANSFORMATIONSLOGIK ---
                base_transform_exporter = Matrix.Identity(4)
                if self.apply_axis_conversion: base_transform_exporter = Matrix.Rotation(math.radians(-90.0), 4, 'X')
                
                final_scale = self.scale_factor
                if self.apply_correction: final_scale *= 0.4
                if final_scale != 1.0: base_transform_exporter = Matrix.Scale(final_scale, 4) @ base_transform_exporter

                centering_matrix = Matrix.Identity(4)
                if self.center_object_origin:
                    # Berechne den Mittelpunkt der Bounding Box der Geometrie
                    center = sum((v.co for v in source_bm.verts), Vector()) / len(source_bm.verts)
                    centering_matrix = Matrix.Translation(-center)
                
                # Kombiniere alle Transformationen in der richtigen Reihenfolge
                # 1. Zentriere die Geometrie (verschiebt Vertices relativ zum Objektursprung)
                # 2. Wende die Objekt-Transformation an (verschiebt das Objekt in die Welt)
                # 3. Wende die Export-Transformation an (Achsen, Skalierung)
                global_transform = base_transform_exporter @ obj.matrix_world @ centering_matrix
                
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
                        if bm_part.faces: write_wrl_shape_from_bmesh(f, bm_part, mat, global_transform, self.color_source)
                        bm_part.free()
                else:
                    write_wrl_shape_from_bmesh(f, source_bm, None, global_transform, self.color_source)
                source_bm.free()

        self.report({'INFO'}, f"Erfolgreich {len(objects_to_export)} Objekt(e) exportiert."); return {'FINISHED'}

# --- REGISTRIERUNGSFUNKTIONEN ---
classes_to_register = (EXPORT_OT_blender_wrl,)
def menu_func_export(self, context): self.layout.operator(EXPORT_OT_blender_wrl.bl_idname, text=EXPORT_OT_blender_wrl.bl_label)
def register_classes():
    for cls in classes_to_register: bpy.utils.register_class(cls)
def unregister_classes():
    for cls in reversed(classes_to_register): bpy.utils.unregister_class(cls)