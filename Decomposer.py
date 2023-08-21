import bpy
import bmesh
import numpy as np

class Decomposer:
    
    def duplicate_object(self, obj1_name, new_obj_name):
        mesh_obj = bpy.data.objects.get(obj1_name)
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        bpy.ops.object.duplicate()
        new_mesh_obj = bpy.context.selected_objects[0]
        new_mesh_obj.name = f"{obj1_name}_{new_obj_name}"
        new_mesh_obj.select_set(False)
        bpy.context.view_layer.objects.active = None
        return mesh_obj, new_mesh_obj

    def x(self, num_boxes, box_size, a, b, c):
        self.setting_duplicate_object("Mesh_1", "Mesh_2")
        self.bisect_object_positive_x("Mesh_2", "Mesh_1", 0, box_size, a, b, c)
        for x_n in range(num_boxes):
            self.duplicate_object("Mesh_1", x_n)
            self.bisect_object_positive_x(f"Mesh_1_{x_n}", "Mesh_1", x_n, box_size, a, b, c)
            self.duplicate_object("Mesh_2", x_n + 1)
            self.bisect_object_negative_x("Mesh_2", f"Mesh_2_{x_n+1}", -x_n-1, box_size, a, b, c)
        mesh_names = ["Mesh_1", "Mesh_1_0", "Mesh_2"]
        for name in mesh_names:
            mesh_obj = bpy.data.objects.get(name)
            if mesh_obj is not None:
                bpy.data.objects.remove(mesh_obj, do_unlink=True)

    def setting_duplicate_object(self, obj_name, new_obj_name):
        mesh_obj = bpy.data.objects.get(obj_name)
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        bpy.ops.object.duplicate()
        new_mesh_obj = bpy.context.selected_objects[0]
        new_mesh_obj.name = new_obj_name
        new_mesh_obj.select_set(False)
        bpy.context.view_layer.objects.active = None
        return mesh_obj, new_mesh_obj

    def bisect_object_positive_x(self, obj_name1, obj_name2, x_n, box_size, a, b, c):
        x_coordinate = (a + (box_size/2+box_size*x_n), b, c)
        mesh_obj1 = bpy.data.objects.get(obj_name1)
        bpy.context.view_layer.objects.active = mesh_obj1
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(x_coordinate), plane_no=(1, 0, 0), use_fill=True, clear_outer=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj1.select_set(False)
        bpy.context.view_layer.objects.active = None
        mesh_obj2 = bpy.data.objects.get(obj_name2)
        bpy.context.view_layer.objects.active = mesh_obj2
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(x_coordinate), plane_no=(1, 0, 0), use_fill=True, clear_inner=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj2.select_set(False)
        bpy.context.view_layer.objects.active = None
        return obj_name1, obj_name2
    
    def bisect_object_negative_x(self, obj_name1, obj_name2, x_n, box_size, a, b, c):
        x_coordinate = (a + (box_size/2 + box_size*x_n), b, c)
        mesh_obj1 = bpy.data.objects.get(obj_name1)
        bpy.context.view_layer.objects.active = mesh_obj1
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=x_coordinate, plane_no=(1, 0, 0), use_fill=True, clear_outer=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj1.select_set(False)
        bpy.context.view_layer.objects.active = None
        mesh_obj2 = bpy.data.objects.get(obj_name2)
        bpy.context.view_layer.objects.active = mesh_obj2
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=x_coordinate, plane_no=(1, 0, 0), use_fill=True, clear_inner=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj2.select_set(False)
        bpy.context.view_layer.objects.active = None
        return obj_name1, obj_name2

    # y-axis segmentation    
    def y(self, num_boxes, box_size, a, b, c):
        for x_n in range(1, num_boxes):
            self.setting_duplicate_object_y("Mesh_1", "Mesh_3", x_n)
            self.setting_duplicate_object_y("Mesh_2", "Mesh_4", x_n)
        for x_n in range(num_boxes, num_boxes + 1):
            mesh_obj = bpy.data.objects.get(f"Mesh_2_{x_n}")
            bpy.context.view_layer.objects.active = mesh_obj
            mesh_obj.select_set(True)
            bpy.ops.object.duplicate()
            new_mesh_obj = bpy.context.selected_objects[0]
            new_mesh_obj.name = f"Mesh_4_{x_n}"
            new_mesh_obj.select_set(False)
            bpy.context.view_layer.objects.active = None
        for x_n in range(1, num_boxes):
            for y_n in range(num_boxes):
                self.duplicate_object(f"Mesh_1_{x_n}", y_n)
                self.bisect_object_positive_y_1(f"Mesh_1_{x_n}_{y_n}", x_n, y_n, box_size, a, b, c)
                self.duplicate_object(f"Mesh_3_{x_n}", y_n)
                self.bisect_object_positive_y_2(f"Mesh_3_{x_n}_{y_n}", x_n, -y_n, box_size, a, b, c)
            mesh_names = [f"Mesh_1_{x_n}", f"Mesh_3_{x_n}"]
            for name in mesh_names:
                mesh_obj = bpy.data.objects.get(name)
                if mesh_obj is not None:
                    bpy.data.objects.remove(mesh_obj, do_unlink=True)
        for x_n in range(1, num_boxes + 1):
            for y_n in range(num_boxes):
                self.duplicate_object(f"Mesh_2_{x_n}", y_n)
                self.bisect_object_positive_y_1(f"Mesh_2_{x_n}_{y_n}", x_n, y_n, box_size, a, b, c)
                self.duplicate_object(f"Mesh_4_{x_n}", y_n)
                self.bisect_object_positive_y_2(f"Mesh_4_{x_n}_{y_n}", x_n, -y_n, box_size, a, b, c)
            mesh_names = [f"Mesh_2_{x_n}", f"Mesh_4_{x_n}"]
            for name in mesh_names:
                mesh_obj = bpy.data.objects.get(name)
                if mesh_obj is not None:
                    bpy.data.objects.remove(mesh_obj, do_unlink=True)

    def setting_duplicate_object_y(self, obj1_name, new_obj_name, x_n):
        mesh_obj = bpy.data.objects.get(f"{obj1_name}_{x_n}")
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        bpy.ops.object.duplicate()
        new_mesh_obj = bpy.context.selected_objects[0]
        new_mesh_obj.name = f"{new_obj_name}_{x_n}"
        new_mesh_obj.select_set(False)
        bpy.context.view_layer.objects.active = None
        return obj1_name, new_obj_name

    # Stanford_bunny_1_0 ~ Stanford_bunny_2_@
    def bisect_object_positive_y_1(self, obj_name, x_n, y_n, box_size,  a, b, c):
        y_coordinate = (a, b + (box_size/2+box_size*(y_n+1)), c)
        mesh_obj1 = bpy.data.objects.get(obj_name)
        bpy.context.view_layer.objects.active = mesh_obj1
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(y_coordinate), plane_no=(0, 1, 0), use_fill=True, clear_outer=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj1.select_set(False)
        bpy.context.view_layer.objects.active = None
        y_coordinate = (a, b + (box_size/2+box_size*(y_n)), c)
        mesh_obj2 = bpy.data.objects.get(obj_name)
        bpy.context.view_layer.objects.active = mesh_obj2
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(y_coordinate), plane_no=(0, 1, 0), use_fill=True, clear_inner=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj2.select_set(False)
        bpy.context.view_layer.objects.active = None    
        return mesh_obj1, mesh_obj2

    # Stanford_bunny_3_0 ~ Stanford_bunny_4_@
    def bisect_object_positive_y_2(self, obj_name, x_n, y_n, box_size,  a, b, c):
        y_coordinate = (a, b + (box_size/2+box_size*y_n), c)
        mesh_obj1 = bpy.data.objects.get(obj_name)
        bpy.context.view_layer.objects.active = mesh_obj1
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(y_coordinate), plane_no=(0, 1, 0), use_fill=True, clear_outer=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj1.select_set(False)
        bpy.context.view_layer.objects.active = None
        y_coordinate = (a, b + (box_size/2+box_size*(y_n-1)), c)
        mesh_obj2 = bpy.data.objects.get(obj_name)
        bpy.context.view_layer.objects.active = mesh_obj2
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(y_coordinate), plane_no=(0, 1, 0), use_fill=True, clear_inner=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj2.select_set(False)
        bpy.context.view_layer.objects.active = None
        return mesh_obj1, mesh_obj2
    
    def z(self, num_boxes, box_size,  a, b, c):
        for x_n in range(1, num_boxes):
            for y_n in range(num_boxes):
                self.setting_duplicate_object_z("Mesh_1", "Mesh_5", x_n, y_n)
                self.setting_duplicate_object_z("Mesh_2", "Mesh_6", x_n, y_n)
                self.setting_duplicate_object_z("Mesh_3", "Mesh_7", x_n, y_n)
                self.setting_duplicate_object_z("Mesh_4", "Mesh_8", x_n, y_n)  
        for x_n in range(1, num_boxes):
            for y_n in range(num_boxes):
                for z_n in range(num_boxes):
                    self.duplicate_object("Mesh_1"f"_{x_n}_{y_n}", z_n)
                    self.bisect_object_positive_z_1("Mesh_1"f"_{x_n}_{y_n}_{z_n}", z_n, box_size,  a, b, c)
                    self.duplicate_object("Mesh_3"f"_{x_n}_{y_n}", z_n)
                    self.bisect_object_positive_z_1("Mesh_3"f"_{x_n}_{y_n}_{z_n}", z_n, box_size,  a, b, c)
                    self.duplicate_object("Mesh_5"f"_{x_n}_{y_n}", z_n)
                    self.bisect_object_positive_z_2("Mesh_5"f"_{x_n}_{y_n}_{z_n}", -z_n-1, box_size,  a, b, c)
                    self.duplicate_object("Mesh_6"f"_{x_n}_{y_n}", z_n)
                    self.bisect_object_positive_z_2("Mesh_6"f"_{x_n}_{y_n}_{z_n}", -z_n-1, box_size,  a, b, c)
                    self.duplicate_object("Mesh_7"f"_{x_n}_{y_n}", z_n)
                    self.bisect_object_positive_z_2("Mesh_7"f"_{x_n}_{y_n}_{z_n}", -z_n-1, box_size,  a, b, c)
                    self.duplicate_object("Mesh_8"f"_{x_n}_{y_n}", z_n)
                    self.bisect_object_positive_z_2("Mesh_8"f"_{x_n}_{y_n}_{z_n}", -z_n-1, box_size,  a, b, c)
                mesh_names = ["Mesh_1"f"_{x_n}_{y_n}", "Mesh_3"f"_{x_n}_{y_n}", "Mesh_5"f"_{x_n}_{y_n}", "Mesh_6"f"_{x_n}_{y_n}", "Mesh_7"f"_{x_n}_{y_n}", "Mesh_8"f"_{x_n}_{y_n}"]
                for name in mesh_names:
                    mesh_obj = bpy.data.objects.get(name)
                    if mesh_obj is not None:
                        bpy.data.objects.remove(mesh_obj, do_unlink=True)        
        for x_n in range(1, num_boxes+1):
            for y_n in range(num_boxes):
                for z_n in range(num_boxes):
                    self.duplicate_object("Mesh_2"f"_{x_n}_{y_n}", z_n)
                    self.bisect_object_positive_z_1("Mesh_2"f"_{x_n}_{y_n}_{z_n}", z_n, box_size,  a, b, c)
                    self.duplicate_object("Mesh_4"f"_{x_n}_{y_n}", z_n)
                    self.bisect_object_positive_z_1("Mesh_4"f"_{x_n}_{y_n}_{z_n}", z_n, box_size,  a, b, c)
                mesh_names = ["Mesh_2"f"_{x_n}_{y_n}", "Mesh_4"f"_{x_n}_{y_n}"]
                for name in mesh_names:
                    mesh_obj = bpy.data.objects.get(name)
                    if mesh_obj is not None:
                        bpy.data.objects.remove(mesh_obj, do_unlink=True)


    # z axis Copy mesh (setting)
    def setting_duplicate_object_z(self, obj1_name, new_obj_name, x_n, y_n):
        mesh_obj = bpy.data.objects.get(f"{obj1_name}_{x_n}_{y_n}")
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        bpy.ops.object.duplicate()
        new_mesh_obj = bpy.context.selected_objects[0]
        new_mesh_obj.name = f"{new_obj_name}_{x_n}_{y_n}"
        new_mesh_obj.select_set(False)
        bpy.context.view_layer.objects.active = None
        return obj1_name, new_obj_name
    
    # Stanford_bunny_1_0 ~ Stanford_bunny_4_@
    def bisect_object_positive_z_1(self, obj1_name, z_n, box_size,  a, b, c):
        z_coordinate = (a, b, c + (box_size/2+box_size*z_n))
        mesh_obj11 = bpy.data.objects.get(obj1_name)
        bpy.context.view_layer.objects.active = mesh_obj11
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(z_coordinate), plane_no=(0, 0, 1), use_fill=True, clear_inner=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj11.select_set(False)
        bpy.context.view_layer.objects.active = None
        z_coordinate = (a, b, c + (box_size/2+box_size*(z_n+1)))
        mesh_obj12 = bpy.data.objects.get(obj1_name)
        bpy.context.view_layer.objects.active = mesh_obj12
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(z_coordinate), plane_no=(0, 0, 1), use_fill=True, clear_outer=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj12.select_set(False)
        bpy.context.view_layer.objects.active = None    
        return mesh_obj11, mesh_obj12
    
    # Stanford_bunny_5_0 ~ Stanford_bunny_8_@
    def bisect_object_positive_z_2(self, obj1_name, z_n, box_size,  a, b, c):
        z_coordinate = (a, b, c + (box_size/2+box_size*(z_n+1)))
        mesh_obj13 = bpy.data.objects.get(obj1_name)
        bpy.context.view_layer.objects.active = mesh_obj13
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(z_coordinate), plane_no=(0, 0, 1), use_fill=True,  clear_outer=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj13.select_set(False)
        bpy.context.view_layer.objects.active = None
        z_coordinate = (a, b, c + (box_size/2+box_size*z_n))
        mesh_obj14 = bpy.data.objects.get(obj1_name)
        bpy.context.view_layer.objects.active = mesh_obj14
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(z_coordinate), plane_no=(0, 0, 1), use_fill=True, clear_inner=True, flip=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh_obj14.select_set(False)
        bpy.context.view_layer.objects.active = None    
        return mesh_obj13, mesh_obj14
    
    
    # decompose 
    def decompose(self, box_size, a, b, c, num_boxes):
        decomposed_part_list = []
        self.x(num_boxes, box_size, a, b, c)
        print("x axis segmentation clear")
        self.y(num_boxes, box_size,  a, b, c)
        print("y axis segmentation clear")
        self.z(num_boxes, box_size,  a, b, c)
        print("z axis segmentation clear")
        
        scene = bpy.context.scene
        for obj in scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
                decomposed_part_list.append(obj)
        collection = bpy.context.collection
        for obj in collection.objects:
            obj.select_set(False)
        return decomposed_part_list