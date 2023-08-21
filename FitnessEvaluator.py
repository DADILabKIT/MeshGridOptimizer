import bpy
import bmesh
import numpy as np

import math
from mathutils import Matrix, Vector
from deap import base, creator, tools, algorithms

from FitnessFunctions import FitnessFunctions
from MeshAnalyzer import MeshAnalyzer
from MeshRotator import MeshRotator
from Decomposer import Decomposer
from SupportChecker import MeshProcessor, SupportChecker, Tweak

class FitnessEvaluator:
    def __init__(self, mesh_analyzer):
        self.mesh_analyzer = mesh_analyzer
        self.mesh_rotator = MeshRotator()

    def evaluate(self, individual):
        self.mesh_analyzer.reload_mesh()
        co_x, x_angle, co_y, y_angle, co_z, z_angle = individual
        
        # 바운딩 박스 정보 가져오기
        box_size, centroid_x, centroid_y, centroid_z = self.mesh_analyzer.calculate_bbox()

        # 초기 좌표
        a = centroid_x + co_x
        b = centroid_y + co_y
        c = centroid_z + co_z
        
        # Mesh Rotation
        self.mesh_rotator.rotate(x_angle, y_angle, z_angle)

        
        num_boxes = math.ceil(self.mesh_analyzer.num_box/2)+1
        decomposed_list_0 = Decomposer().decompose(box_size, a, b, c, num_boxes)

        
        # FitnessFunctions 클래스의 메서드를 사용하여 F1 및 F2 값을 계산
        common_volume = box_size ** 3
        original_volume = self.mesh_analyzer.original_volume
        threshold_volume = 0.1 * common_volume
        Fitness_eval = FitnessFunctions(decomposed_list_0, common_volume, original_volume, threshold_volume)
        F1_value = Fitness_eval.F1()
        
        F3_value = Fitness_eval.F3()
        F4_value = Fitness_eval.F4()
        F5_value = Fitness_eval.F5()
        F6_value = Fitness_eval.F6()
        F7_value = Fitness_eval.F7() # 힘, 모멘트
        F8_value = Fitness_eval.F8() # 마찰면
        F2_value = Fitness_eval.F2()


        F = (F1_value + F2_value + F3_value + F4_value + F5_value + F6_value + F7_value + F8_value) / 8
        
        # 결과 출력
        print("x: ", co_x, "y: ", co_y, "z: ", co_z, "x_angle: ", x_angle, "y_angle: ", y_angle, "z_angle: ", z_angle)
        print("F1: ", F1_value,"F2: ", F2_value, "F3: ", F3_value, "F4: ", F4_value,"F5: ", F5_value,"F6: ", F6_value,"F7: ", F7_value,"F8: ", F8_value, "F: ", F)
        print("vol_customs: ", Fitness_eval.vol_of_customs, "vol_origin", Fitness_eval.original_volume)
        print("num_smalls: ", len(Fitness_eval.small_list),"num_modules: ", len(Fitness_eval.decomposed_list))    
        
        # 초기화
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()


        return F,


if __name__ == "__main__":
    # ... 메인 실행 코드
    pass