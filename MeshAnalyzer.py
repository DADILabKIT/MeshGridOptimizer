import bpy
import bmesh
import random

class MeshAnalyzer:
    def __init__(self, stl_file_path, num_box):
        self.stl_file_path = stl_file_path
        self.num_box = num_box
        self.load_stl_file()
        self.original_vertices = [v.co for v in self.origin_mesh.data.vertices]
        self.bbox = self.calculate_bbox()
        self.bm = self.create_bmesh()
        self.original_volume = self.calculate_volume()

    # Reload the mesh using the original mesh name
    def reload_mesh(self):
        if "Mesh_1" in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects["Mesh_1"], do_unlink=True)
        self.load_stl_file()
        self.original_vertices = [v.co for v in self.origin_mesh.data.vertices]
        self.bbox = self.calculate_bbox()
        self.bm = self.create_bmesh()
        self.original_volume = self.calculate_volume()
        
    #STL File Load
    def load_stl_file(self):
        bpy.ops.import_mesh.stl(filepath=self.stl_file_path)
        mesh_obj = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.name = "Mesh_1"
        self.origin_mesh = mesh_obj
    
    def create_bmesh(self):
        bm = bmesh.new()
        bm.from_mesh(self.origin_mesh.data)
        return bm
        
    def calculate_volume(self):
        return self.bm.calc_volume()
        
    def calculate_bbox(self):
        vertices = self.original_vertices
        bbox = [self.origin_mesh.matrix_world @ v for v in vertices]

        min_x = min(v[0] for v in bbox)
        max_x = max(v[0] for v in bbox)
        min_y = min(v[1] for v in bbox)
        max_y = max(v[1] for v in bbox)
        min_z = min(v[2] for v in bbox)
        max_z = max(v[2] for v in bbox)
        
        length_x = max_x - min_x
        length_y = max_y - min_y
        length_z = max_z - min_z
        
        num_box = self.num_box
        max_length = max(length_x, length_y, length_z)
        box_size = max_length / num_box
        
        centroid_x = max_x - length_x / 2
        centroid_y = max_y - length_y / 2
        centroid_z = max_z - length_z / 2
        
        return box_size, centroid_x, centroid_y, centroid_z