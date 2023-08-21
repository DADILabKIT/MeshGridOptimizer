import bpy
import bmesh
import numpy as np
import math


class MeshRotator:
    def __init__(self, mesh_name="Mesh_1"):
        self.mesh_name = mesh_name
        self.mesh_obj = bpy.data.objects.get(self.mesh_name)
        bpy.context.view_layer.objects.active = self.mesh_obj
    
    def rotate(self, x_angle=0, y_angle=0, z_angle=0):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.rotate(value=math.radians(x_angle), orient_axis='X', constraint_axis=(True, False, False))
        bpy.ops.transform.rotate(value=math.radians(y_angle), orient_axis='Y', constraint_axis=(False, True, False))
        bpy.ops.transform.rotate(value=math.radians(z_angle), orient_axis='Z', constraint_axis=(False, False, True))
        bpy.ops.object.mode_set(mode='OBJECT')