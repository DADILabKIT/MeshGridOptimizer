initial_values_global = {}
initial_values_global['initial_F2_value'] = None
initial_values_global['initial_F3_value'] = None
initial_values_global['initial_F4_value'] = None
initial_values_global['initial_F5_value'] = None
initial_values_global['initial_F6_value'] = None
initial_values_global['initial_F7_value'] = None


import bpy
import bmesh
import numpy as np
from math import radians, degrees, cos, inf, sqrt
from mathutils import Vector
from SupportChecker import MeshProcessor, SupportChecker, Tweak


class FitnessFunctions:
    def __init__(self, decomposed_list_0, common_volume, original_volume, threshold_volume):
        self.decomposed_list_0 = decomposed_list_0
        self.common_volume = common_volume
        self.original_volume = original_volume
        self.threshold_volume = threshold_volume
        self.small_list, self.decomposed_list = self.calculate_small_and_decomposed_lists()
        self.vol_of_customs = self.calculate_vol_of_customs()
        self.contact_area_sum_below_threshold, self.interface_count = self.calculate_interface_data()

    def calculate_interface_angles(self): # cos theta 구해서 평균 낼거임. self 연결도 안함. 그냥 참고용.
        interface_angles = []

        for part in self.decomposed_list:
            bm = bmesh.new()
            bm.from_mesh(part.data)
            bm.faces.ensure_lookup_table()

            for f in bm.faces:
                p = (f.calc_center_median() - part.location) * 0.999
                hit_data = part.ray_cast(p, f.normal)
                
                if hit_data[0]: 
                    angle_with_xy = degrees(f.normal.angle(Vector((0, 0, 1))))
                    interface_angles.append(angle_with_xy)

            bm.free()

        return interface_angles


    def calculate_interface_data(self): # F5, F6
        THRESHOLD_AREA = 0.1 * (self.common_volume ** (2/3))
        contact_area_sum_below_threshold = 0
        interface_count = 0
        total_area = 0
        total_face_count = 0  # 전체 면 개수를 저장할 변수 추가

        for part in self.decomposed_list:
            bm = bmesh.new()
            bm.from_mesh(part.data)
            bm.faces.ensure_lookup_table()

            total_face_count += len(bm.faces)  # 현재 부품의 전체 면 개수를 더해줌

            for f in bm.faces:
                total_area += f.calc_area()
                p = (f.calc_center_median() - part.location) * 0.999
                hit_data = part.ray_cast(p, f.normal)
                
                if hit_data[0]: 
                    hitFaceIndex = hit_data[3]
                    bmPn = bmesh.new()
                    bmPn.from_mesh(part.data) 
                    bmPn.faces.ensure_lookup_table() 
                    face_area = bmPn.faces[hitFaceIndex].calc_area()
                    
                    if face_area < THRESHOLD_AREA:
                        contact_area_sum_below_threshold += face_area
                    bmPn.free()
                    
                    interface_count += 1
            bm.free()

        self.total_area = total_area
        contact_area_sum_below_threshold = contact_area_sum_below_threshold / 2  # 접촉 면적은 두 파트에 걸쳐 있으므로 2로 나눔
        interface_count = interface_count // 2  
        total_face_count -= interface_count  # 중복 제거, interface_count를 반으로 나눈 값을 전체 면 개수에서 빼줌
        self.total_face_count = total_face_count  # 전체 면 개수를 클래스 변수로 저장

        return contact_area_sum_below_threshold, interface_count

    def total_edge_length_for_part(self, part):
        bmPart = bmesh.new()
        bmPart.from_mesh(part.data)
        totalEdgeLength = sum(e.calc_length() for e in bmPart.edges)
        bmPart.free()
        return totalEdgeLength

    def length_of_sharp_edges_for_each_part(self, part):
        THRESHOLD_SHARP_EDGE = 30  # 원하는 각도로 설정
        bmPart = bmesh.new()
        bmPart.from_mesh(part.data)
        sharpEdgeLength = 0
        sharpVerts = []
        sharpEdges = []
        bmPart.edges.ensure_lookup_table() 
        for e in bmPart.edges:
            if len(e.link_faces) != 2:
                continue
            f1, f2 = e.link_faces
            if f1.normal != Vector((0,0,0)) and f2.normal != Vector((0,0,0)):
                theta = degrees(f1.normal.angle(f2.normal)) 
                if theta > THRESHOLD_SHARP_EDGE:
                    sharpEdgeLength += e.calc_length()
                    for v in e.verts:
                        if v.co not in sharpVerts:
                            sharpVerts.append(v.co)  # 버텍스 복사본 저장
                    sharpEdges.append([v.co for v in e.verts])  # 엣지 복사본 저장
        bmPart.free()
        return sharpVerts, sharpEdges, sharpEdgeLength

    def calculate_vol_of_customs(self):
        vol_of_customs = 0
        for obj in self.decomposed_list:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            volume = bm.calc_volume()
            if volume > 0.01 and volume < (self.common_volume-0.01):
                vol_of_customs += volume
        return vol_of_customs

    def calculate_small_and_decomposed_lists(self):
        small_list = []
        decomposed_list = []
        for obj in self.decomposed_list_0:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            volume = bm.calc_volume()
            if volume > 0.01:
                decomposed_list.append(obj)
                if volume < (self.threshold_volume-0.01):
                    small_list.append(obj)
        return small_list, decomposed_list

    def F1(self):
        return self.vol_of_customs / self.original_volume
    
    def F2(self):
        # 메시를 처리하고 방향을 최적화하려면:
        mesh_objects = self.decomposed_list
        processor = MeshProcessor()
        imported_meshes = processor.process_meshes(mesh_objects)

        # 서포트 부피를 계산하려면:
        checker = SupportChecker()
        total_support = checker.check_support(imported_meshes)
        print("Total Support Volume:", total_support)

        # 초기 서포트 부피 설정
        if initial_values_global['initial_F2_value'] is None:
            initial_values_global['initial_F2_value'] = total_support

        # 정규화된 서포트 부피 반환
        normalized_support = total_support / initial_values_global['initial_F2_value']
        return normalized_support
        
    # 임계 부피 이하 커스텀 모듈 개수 최소화
    def F3(self):
        current_F3 = len(self.small_list) / len(self.decomposed_list)

        # 초기값 설정
        if initial_values_global['initial_F3_value'] is None:
            initial_values_global['initial_F3_value'] = current_F3

        # 정규화된 값 반환
        return current_F3 / initial_values_global['initial_F3_value']
    
    def F4(self):
        # 날카로운 모서리의 총 길이 계산
        sharp_edge_length_sum = 0
        total_edge_length_sum = 0
        for obj in self.decomposed_list:
            _, _, length = self.length_of_sharp_edges_for_each_part(obj)
            total_length = self.total_edge_length_for_part(obj)
            sharp_edge_length_sum += length
            total_edge_length_sum += total_length

        current_F4 = sharp_edge_length_sum / total_edge_length_sum

        # 초기값 설정
        if initial_values_global['initial_F4_value'] is None:
            initial_values_global['initial_F4_value'] = current_F4

        # 정규화된 값 반환
        return current_F4 / initial_values_global['initial_F4_value']
    
    def F5(self): # 접촉 면 개수
        current_F5 = self.interface_count / self.total_face_count

        # 초기값 설정
        if initial_values_global['initial_F5_value'] is None:
            initial_values_global['initial_F5_value'] = current_F5

        # 정규화된 값 반환
        return current_F5 / initial_values_global['initial_F5_value']
    
    def F6(self): # 접촉 면 중 임계 면적 이하 합산
        current_F6 = self.contact_area_sum_below_threshold / self.total_area

        # 초기값 설정
        if initial_values_global['initial_F6_value'] is None:
            initial_values_global['initial_F6_value'] = current_F6

        # 정규화된 값 반환
        return current_F6 / initial_values_global['initial_F6_value']
    
    def F7(self):
        total_moment = 0
        count_floating_modules = 0

        for part in self.decomposed_list:
            bm = bmesh.new()
            bm.from_mesh(part.data)
            bm.faces.ensure_lookup_table()

            part_center = part.location
            hit_data = part.ray_cast(part_center, Vector((0, 0, -1)))

            # If there's no hit, then the part is floating
            if not hit_data[0]:
                count_floating_modules += 1
                interface_centers = []

                # Identifying the interface faces
                for f in bm.faces:
                    p = (f.calc_center_median() - part.location) * 0.999
                    hit_data_interface = part.ray_cast(p, f.normal)
                    if hit_data_interface[0]:
                        interface_centers.append(f.calc_center_median())

                # For each interface center, calculate the moment if it's in -z direction
                for interface_center in interface_centers:
                    vector_from_part_to_interface = interface_center - part_center
                    if vector_from_part_to_interface.z < 0:  # If the interface is in the -z direction
                        # Compute the horizontal distance
                        horizontal_distance = (Vector((part_center.x, part_center.y, 0)) - Vector((interface_center.x, interface_center.y, 0))).length
                        # Assuming the part's volume represents its weight
                        part_volume = part.dimensions.x * part.dimensions.y * part.dimensions.z
                        moment = horizontal_distance * part_volume
                        total_moment += moment

            bm.free()

        # Compute the average moment for all floating modules
        if count_floating_modules > 0:
            average_moment = total_moment / count_floating_modules
        else:
            average_moment = 0

        # 초기값 설정
        if initial_values_global['initial_F7_value'] is None:
            initial_values_global['initial_F7_value'] = average_moment

        # 정규화된 서포트 부피 반환
        normalized_moment = average_moment / initial_values_global['initial_F7_value']
        return normalized_moment
    
    def F8(self):
        weighted_normal_sum = Vector((0, 0, 0))
        total_area = 0

        for part in self.decomposed_list:
            bm = bmesh.new()
            bm.from_mesh(part.data)
            bm.faces.ensure_lookup_table()

            # Identifying the interface faces
            for f in bm.faces:
                p = (f.calc_center_median() - part.location) * 0.999
                hit_data = part.ray_cast(p, f.normal)
                if hit_data[0]:
                    # Normal vector of the interface
                    interface_normal = f.normal
                    # Weight the normal by the face area
                    weighted_normal_sum += interface_normal * f.calc_area()
                    total_area += f.calc_area()

            bm.free()

        # Calculate the average normal
        if total_area != 0:
            average_normal = weighted_normal_sum / total_area
        else:
            average_normal = Vector((0, 0, 0))

        # Compute the angle between the average normal and the +z axis
        dot_product = average_normal.dot(Vector((0, 0, 1)))
        angle_cosine = dot_product / (average_normal.length * Vector((0, 0, 1)).length)
        sin_theta = sqrt(1 - angle_cosine**2)

        return sin_theta