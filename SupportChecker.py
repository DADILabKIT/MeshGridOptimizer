import bpy
import bmesh
import sys, argparse, os
import shutil
import struct, time
import math
import mathutils
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
from mathutils import Vector 
from scipy.spatial import distance
from math import radians, degrees, cos, inf 
import random
import itertools
from collections import Counter
# class: Tweak, STLHander, MeshProcessor, SupportChecker
# Tweaker
class Tweak:
    def __init__(self, mesh, bi_algorithmic=False, CA=45, n=[0,0,-1]):  
        self.bi_algorithmic = bi_algorithmic   
        content = self.arrange_mesh(mesh)
        #print("Object has {} facets".format(len(content)))
        arcum_time = dialg_time = lit_time=0         
        ## Calculating initial printability
        amin = self.approachfirstvertex(content)
        bottomA, overhangA, lineL = self.lithograph(content,[0.0,0.0,1.0],amin,CA)
        liste = [[[0.0,0.0,1.0], bottomA, overhangA, lineL]]
        arcum_time = time.time()
        orientations = self.area_cumulation(content, n)
        arcum_time = time.time() - arcum_time
        if bi_algorithmic:
            dialg_time = time.time()
            orientations += self.egde_plus_vertex(mesh, 12)
            dialg_time = time.time() - dialg_time
            
            orientations = self.remove_duplicates(orientations)     
        lit_time = time.time()
        for side in orientations:
            orientation = [float("{:6f}".format(-i)) for i in side[0]]
            ## vector: sn, cum_A: side[1]
            amin=self.approachvertex(content, orientation)
            bottomA, overhangA, lineL = self.lithograph(content, orientation, amin, CA)
            liste.append([orientation, bottomA, overhangA, lineL])   #[Vector, touching area, Overhang, Touching_Line]
        # target function
        Unprintability = sys.maxsize
        for orientation, bottomA, overhangA, lineL in liste:
            F = self.target_function(bottomA, overhangA, lineL) # touching area: i[1], overhang: i[2], touching line i[3]
            if F<Unprintability - 0.05:
                Unprintability=F
                bestside = [orientation, bottomA, overhangA, lineL]
            time.sleep(0)  # Yield, so other threads get a bit of breathing space. 
        lit_time = time.time() - lit_time
           
        if bestside:
            [v,phi,R] = self.euler(bestside)
        self.v=v
        self.phi=phi
        self.R=R
        self.Unprintability = Unprintability
        self.Zn=bestside[0]
        return None
    def target_function(self, touching, overhang, line):
        '''This function returns the printability with the touching area and overhang given.'''
        ABSLIMIT=100             # Some values for scaling the printability
        RELLIMIT=1
        LINE_FAKTOR = 0.5
        touching_line = line * LINE_FAKTOR
        F = (overhang/ABSLIMIT) + (overhang / (touching+touching_line) /RELLIMIT)
        ret = float("{:f}".format(F))
        return ret
    def arrange_mesh(self, mesh):
        '''The Tweaker needs the mesh format of the object with the normals of the facetts.'''
        face=[]
        content=[]
        i=0
        for li in mesh:      
            face.append(li)
            i+=1
            if i%3==0:
                v=[face[1][0]-face[0][0],face[1][1]-face[0][1],face[1][2]-face[0][2]]
                w=[face[2][0]-face[0][0],face[2][1]-face[0][1],face[2][2]-face[0][2]]
                a=[round(v[1]*w[2]-v[2]*w[1],6), round(v[2]*w[0]-v[0]*w[2],6), round(v[0]*w[1]-v[1]*w[0],6)]
                content.append([a,face[0],face[1],face[2]])
                face=[]
            time.sleep(0)  # Yield, so other threads get a bit of breathing space.
        return content
    def approachfirstvertex(self,content):
        '''Returning the lowest z value'''
        amin=sys.maxsize
        for li in content:
            z=min([li[1][2],li[2][2],li[3][2]])
            if z<amin:
                amin=z
            time.sleep(0)  # Yield, so other threads get a bit of breathing space.
        return amin
    def approachvertex(self, content, n):
        '''Returning the lowest value regarding vector n'''
        amin=sys.maxsize
        for li in content:
            a1 = li[1][0]*n[0] +li[1][1]*n[1] +li[1][2]*n[2]
            a2 = li[2][0]*n[0] +li[2][1]*n[1] +li[2][2]*n[2]
            a3 = li[3][0]*n[0] +li[3][1]*n[1] +li[3][2]*n[2]          
            an=min([a1,a2,a3])
            if an<amin:
                amin=an
            time.sleep(0)  # Yield, so other threads get a bit of breathing space.
        return amin
    def lithograph(self, content, n, amin, CA):
        '''Calculating touching areas and overhangs regarding the vector n'''
        Overhang=1
        alpha=-math.cos((90-CA)*math.pi/180)
        bottomA=1
        LineL = 1
        touching_height = amin+0.15
        anti_n = [float(-i) for i in n]
        for li in content:
            time.sleep(0)  # Yield, so other threads get a bit of breathing space.
            a=li[0]
            norma=math.sqrt(a[0]*a[0] + a[1]*a[1] + a[2]*a[2])
            if norma < 2:
                continue
            if alpha > (a[0]*n[0] +a[1]*n[1] +a[2]*n[2])/norma:
                a1 = li[1][0]*n[0] +li[1][1]*n[1] +li[1][2]*n[2]
                a2 = li[2][0]*n[0] +li[2][1]*n[1] +li[2][2]*n[2]
                a3 = li[3][0]*n[0] +li[3][1]*n[1] +li[3][2]*n[2]
                an = min([a1,a2,a3])
                ali = float("{:1.4f}".format(abs(li[0][0]*n[0] +li[0][1]*n[1] +li[0][2]*n[2])/2))
                if touching_height < an:
                    if 0.00001 < math.fabs(a[0]-anti_n[0]) + math.fabs(a[1]-anti_n[1]) + math.fabs(a[2]-anti_n[2]):
                        ali = 0.8 * ali
                    Overhang += ali
                else:
                    bottomA += ali
                    LineL += self.get_touching_line([a1,a2,a3], li, touching_height)
                time.sleep(0)  # Yield, so other threads get a bit of breathing space.
        return bottomA, Overhang, LineL
    def get_touching_line(self, a, li, touching_height):
        touch_lst = list()
        for i in range(3):
            if a[i] < touching_height:
                touch_lst.append(li[1+i])
        combs = list(itertools.combinations(touch_lst, 2))
        if len(combs) <= 1:
            return 0
        length = 0
        for p1, p2 in combs:
            time.sleep(0)  # Yield, so other threads get a bit of breathing space.
            length += math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2)
        return length

    def area_cumulation(self, content, n):
        '''Searching best options out of the objects area vector field'''
        if self.bi_algorithmic: best_n = 7
        else: best_n = 5
        orient = Counter()
        for li in content:       # Cumulate areavectors
            an = li[0]
            A = math.sqrt(an[0]*an[0] + an[1]*an[1] + an[2]*an[2])
            
            if A > 0:
                an = [float("{:1.6f}".format(i/A, 6)) for i in an]
                orient[tuple(an)] += A

        time.sleep(0)  # Yield, so other threads get a bit of breathing space.
        top_n = orient.most_common(best_n)
        return [[[0.0,0.0,1.0], 0.0]] + [[list(el[0]), float("{:2f}".format(el[1]))] for el in top_n]
    def egde_plus_vertex(self, mesh, best_n):
        '''Searching normals or random edges with one vertice'''
        vcount = len(mesh)
        # Small files need more calculations
        if vcount < 10000: it = 5
        elif vcount < 25000: it = 2
        else: it = 1           
        self.mesh = mesh
        lst = map(self.calc_random_normal, list(range(vcount))*it)
        lst = filter(lambda x: x is not None, lst)
        
        time.sleep(0)  # Yield, so other threads get a bit of breathing space.
        orient = Counter(lst)
        
        top_n = orient.most_common(best_n)
        top_n = filter(lambda x: x[1]>2, top_n)

        return [[list(el[0]), el[1]] for el in top_n]

    def calc_random_normal(self, i):
        if i%3 == 0:
            v = self.mesh[i]
            w = self.mesh[i+1]
        elif i%3 == 1:
            v = self.mesh[i]
            w = self.mesh[i+1]
        else:
            v = self.mesh[i]
            w = self.mesh[i-2]
        r_v = random.choice(self.mesh)
        v = [v[0]-r_v[0], v[1]-r_v[1], v[2]-r_v[2]]
        w = [w[0]-r_v[0], w[1]-r_v[1], w[2]-r_v[2]]
        a=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
        n = math.sqrt(a[0]*a[0] + a[1]*a[1] + a[2]*a[2])
        if n != 0:
            return tuple([round(d/n, 6) for d in a])


    def remove_duplicates(self, o):
        '''Removing duplicates in orientation'''
        orientations = list()
        for i in o:
            duplicate = None
            for j in orientations:
                time.sleep(0)  # Yield, so other threads get a bit of breathing space.
                dif = math.sqrt( (i[0][0]-j[0][0])**2 + (i[0][1]-j[0][1])**2 + (i[0][2]-j[0][2])**2 )
                if dif < 0.001:
                    duplicate = True
                    break
            if duplicate is None:
                orientations.append(i)
        return orientations



    def euler(self, bestside):
        '''Calculating euler params and rotation matrix'''
        if bestside[0] == [0, 0, -1]:
            v = [1, 0, 0]
            phi = math.pi
        elif bestside[0]==[0,0,1]:
            v=[1,0,0]
            phi=0
        else:
            phi = float("{:2f}".format(math.pi - math.acos( -bestside[0][2] )))
            v = [-bestside[0][1] , bestside[0][0], 0]
            v = [i / math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]) for i in v]
            v = [float("{:2f}".format(i)) for i in v]

        R = [[v[0] * v[0] * (1 - math.cos(phi)) + math.cos(phi),
              v[0] * v[1] * (1 - math.cos(phi)) - v[2] * math.sin(phi),
              v[0] * v[2] * (1 - math.cos(phi)) + v[1] * math.sin(phi)],
             [v[1] * v[0] * (1 - math.cos(phi)) + v[2] * math.sin(phi),
              v[1] * v[1] * (1 - math.cos(phi)) + math.cos(phi),
              v[1] * v[2] * (1 - math.cos(phi)) - v[0] * math.sin(phi)],
             [v[2] * v[0] * (1 - math.cos(phi)) - v[1] * math.sin(phi),
              v[2] * v[1] * (1 - math.cos(phi)) + v[0] * math.sin(phi),
              v[2] * v[2] * (1 - math.cos(phi)) + math.cos(phi)]]
        R = [[float("{:2f}".format(val)) for val in row] for row in R] 
        return v,phi,R

class STLHander:
    def __init__(self):
        pass

    def loadMesh(self, inputfile):
        '''load meshs and object attributes from file'''
        ## loading mesh format
        
        filetype = os.path.splitext(inputfile)[1].lower()
        if filetype == ".stl":
            f=open(inputfile,"rb")
            if "solid" in str(f.read(5).lower()):
                f=open(inputfile,"r")
                objs = [{"Mesh": self.loadAsciiSTL(f)}]
                if len(objs[0]["Mesh"]) < 3:
                        f.seek(5, os.SEEK_SET)
                        objs = [{"Mesh": self.loadBinarySTL(f)}]
            else:
                objs = [{"Mesh": self.loadBinarySTL(f)}]
        else:
            print("File type is not supported.")
            sys.exit()

        return objs


    def loadAsciiSTL(self, f):
        '''Reading mesh data from ascii STL'''
        mesh=list()
        for line in f:
            if "vertex" in line:
                data=line.split()[1:]
                mesh.append([float(data[0]), float(data[1]), float(data[2])])
        return mesh

    def loadBinarySTL(self, f):
        '''Reading mesh data from binary STL'''
            #Skip the header
        f.read(80-5)
        faceCount = struct.unpack('<I', f.read(4))[0]
        mesh=list()
        for idx in range(0, faceCount):
            data = struct.unpack("<ffffffffffffH", f.read(50))
            mesh.append([data[3], data[4], data[5]])
            mesh.append([data[6], data[7], data[8]])
            mesh.append([data[9], data[10], data[11]])
        return mesh
        
                    
    def rotateSTL(self, R, content, filename):
        '''Rotate the object and save as ascii STL.'''
        face=[]
        mesh=[]
        i=0

        rotated_content=list(map(self.rotate_vert, content, [R]*len(content)))
        
        for li in rotated_content:      
            face.append(li)
            i+=1
            if i%3==0:
                mesh.append([face[0],face[1],face[2]])
                face=[]

        mesh = map(self.calc_nomal, mesh)

        tweaked = list("solid %s" % filename)
        tweaked += list(map(self.write_facett, mesh))
        tweaked.append("\nendsolid %s\n" % filename)
        tweaked = "".join(tweaked)
        
        return tweaked

    def rotate_vert(self, a, R):
        return [a[0]*R[0][0]+a[1]*R[1][0]+a[2]*R[2][0],
                                a[0]*R[0][1]+a[1]*R[1][1]+a[2]*R[2][1],
                                a[0]*R[0][2]+a[1]*R[1][2]+a[2]*R[2][2]]
    def calc_nomal(self, face):
        v=[face[1][0]-face[0][0],face[1][1]-face[0][1],face[1][2]-face[0][2]]
        w=[face[2][0]-face[0][0],face[2][1]-face[0][1],face[2][2]-face[0][2]]
        a=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]        
        return [[a[0],a[1],a[2]],face[0],face[1],face[2]]

    def write_facett(self, facett):
        return"""\nfacet normal %f %f %f
    outer loop
        vertex %f %f %f
        vertex %f %f %f
        vertex %f %f %f
    endloop
    endfacet""" % (facett[0][0], facett[0][1], facett[0][2], facett[1][0], 
                facett[1][1], facett[1][2], facett[2][0], facett[2][1], 
                facett[2][2], facett[3][0], facett[3][1], facett[3][2])

    def rotatebinSTL(self, R, content, filename):
        '''Rotate the object and save as binary STL. This module is currently replaced
        by the ascii version. If you want to use binary STL, please do the
        following changes in Tweaker.py: Replace "rotatebinSTL" by "rotateSTL"
        and set in the write sequence the open outfile option from "w" to "wb".
        However, the ascii version is much faster in Python 3.'''
        face=[]
        mesh=[]
        i=0

        rotated_content=list(map(self.rotate_vert, content, [R]*len(content)))
        
        for li in rotated_content:      
            face.append(li)
            i+=1
            if i%3==0:
                mesh.append([face[0],face[1],face[2]])
                face=[]

        mesh = map(self.calc_nomal, mesh)

        tweaked = "Tweaked on {}".format(time.strftime("%a %d %b %Y %H:%M:%S")
                                ).encode().ljust(79, b" ") + b"\n"
        tweaked += struct.pack("<I", int(len(content)/3)) #list("solid %s" % filename)
        #tweaked += list(map(self.write_bin_facett, mesh))
        for facett in mesh:
            tweaked += struct.pack("<fff", facett[0][0], facett[0][1], facett[0][2])
            tweaked += struct.pack("<fff", facett[1][0], facett[1][1], facett[1][2])
            tweaked += struct.pack("<fff", facett[2][0], facett[2][1], facett[2][2])
            tweaked += struct.pack("<fff", facett[3][0], facett[3][1], facett[3][2])
            tweaked += struct.pack("<H", 0)
            
        return tweaked          

class MeshProcessor:
    def __init__(self):
        self.THRESHOLD_OVERHANG = 45
        self.Buildsize_x = 100
        self.Buildsize_y = 100
        self.build_volume = None
    @staticmethod
    def remove_all_files(path):
        shutil.rmtree(path)
        os.makedirs(path)

    @staticmethod
    def load_stl_files_from_directory(stl_directory):
        return [f for f in os.listdir(stl_directory) if f.lower().endswith(".stl")]

    def process_meshes(self, mesh_objects, tweak_subfolder_name="tweaker"):
        # support 폴더 생성
        if not os.path.exists('support'):
            os.makedirs('support')

        path = r'support/'  # 상대경로로 support 폴더를 지정

        # 경로 내의 모든 파일 삭제 실행
        self.remove_all_files(path)

        # blender mesh 파일들 불러오기
        folder_path = path
        for obj in mesh_objects:
            file_path = folder_path + "/"+ obj.name + ".stl"
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.ops.object.convert(target='MESH')
            
            # STL 파일로 내보내기
            bpy.ops.export_mesh.stl(filepath=file_path, use_selection=True, use_mesh_modifiers=False)

        new_folder_path = os.path.join(folder_path, tweak_subfolder_name)
        os.makedirs(new_folder_path)

        stl_files = self.load_stl_files_from_directory(folder_path)

        for i in range(len(stl_files)):
            inputfile = folder_path + stl_files[i]
            objs = STLHander().loadMesh(inputfile)

            c = 0
            for obj in objs:
                mesh = obj["Mesh"]
                bi_algorithmic = False
                angle = 45
                x = Tweak(mesh, bi_algorithmic, angle)
                R = x.R

                file_name_without_extension, file_extension = os.path.splitext(os.path.basename(inputfile))
                outputfile = new_folder_path + "\\" + file_name_without_extension +"_tweaked"
                outputfile += ".stl"

                # Creating tweaked output file
                if os.path.splitext(outputfile)[1].lower() in ["stl", ".stl"]:
                    tweakedcontent = STLHander().rotateSTL(R, mesh, inputfile)
                    if len(objs) <= 1:
                        outfile = outputfile
                    else:
                        outfile = os.path.splitext(outputfile)[0]+" ({})".format(c)+os.path.splitext(outputfile)[1]
                    with open(outfile,'w') as outfile:
                        outfile.write(tweakedcontent)

        # 모든 메시(Mesh) 객체 선택 후 제거
        bpy.ops.object.select_all(action='DESELECT')
        for obj in mesh_objects:
            obj.select_set(True)
        bpy.ops.object.delete()

        imported_mesh_objects = []

        # 각 STL 파일을 Blender로 불러오기
        for stl_file in self.load_stl_files_from_directory(new_folder_path):
            stl_path = os.path.join(new_folder_path, stl_file)
            bpy.ops.import_mesh.stl(filepath=stl_path)

            # 불러온 메시 객체 저장
            obj_name = os.path.splitext(stl_file)[0]
            obj = bpy.data.objects.get(obj_name)
            if obj:
                imported_mesh_objects.append(obj)

        return imported_mesh_objects
    
# # 메시를 처리하고 방향을 최적화하려면:
# processor = MeshProcessor()
# folder_path = 'your_folder_path_here'  # STL 파일이 있는 폴더 경로
# tweaked_folder_path = processor.process_meshes(mesh_objects, folder_path)

class SupportChecker:
    def __init__(self):
        self.THRESHOLD_OVERHANG = 45
        self.Buildsize_x = 100
        self.Buildsize_y = 100
        self.build_volume = None

    @staticmethod
    def obj_alignment(obj):
        bpy.ops.object.mode_set(mode='OBJECT')
        original_location = obj.location.copy()
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        bpy.ops.object.location_clear()
        mx = obj.matrix_world
        minz = min((mx @ v.co)[2] for v in obj.data.vertices)
        maxz = max((mx @ v.co)[2] for v in obj.data.vertices)
        mx.translation.z -= minz
        return original_location, minz, maxz

    @staticmethod
    def get_bounding_box_center(mesh_object):
        min_vertex = Vector(mesh_object.bound_box[0])
        max_vertex = Vector(mesh_object.bound_box[6])
        bounding_box_center = (min_vertex + max_vertex) / 2
        return bounding_box_center

    def support_volume(self, part, buildVolume, mesh_name, minz, maxz):
        supportVolume = 0
        buildOrientationNormal = Vector((0.0, 0.0, 1.0))
        bmPart = bmesh.new()
        bmPart.from_mesh(part.data)
        bmPart.faces.ensure_lookup_table()
        for f in bmPart.faces:
            global_f_normal = f.normal
            if global_f_normal != Vector((0.0, 0.0, 0.0)):
                theta = global_f_normal.angle(-buildOrientationNormal)
                if 0 <= theta and theta < radians(90 - self.THRESHOLD_OVERHANG):
                    c = f.calc_center_median()
                    ray_begin_local_1 = part.matrix_world.inverted() @ c
                    direction_local_2 = buildVolume.matrix_world.inverted() @ c
                    ray_begin_local_1_z = ray_begin_local_1[2] - 1
                    ray_begin_local_2 = Vector((direction_local_2[0], direction_local_2[1], ray_begin_local_1_z))
                    source_object = bpy.data.objects.get(mesh_name)
                    ray_begin_local_3 = buildVolume.matrix_world.inverted() @ -source_object.matrix_world.translation
                    ray_begin_local_3_z = ray_begin_local_3[2]
                    ray_begin_local_4 = Vector((c[0], c[1], ray_begin_local_3_z))
                    direction_local_3 = c
                    hit_data_2 = part.ray_cast(ray_begin_local_2, direction_local_2)
                    hit_data_3 = part.ray_cast(ray_begin_local_4, direction_local_3)
                    if hit_data_3[0] and hit_data_2[0]:
                        sDistance_2 = round(distance.euclidean(direction_local_2, hit_data_2[1]) - 0.5, 2)
                        supportVolume += sDistance_2 * f.calc_area()
                    elif not hit_data_3[0]:
                        if direction_local_3[2] == minz:
                            pass
                        else:
                            sDistance_3 = round(distance.euclidean(direction_local_3, ray_begin_local_4) + 0.5, 2)
                            supportVolume += sDistance_3 * f.calc_area()
                    else:
                        pass
        bmPart.free()
        return supportVolume

    def check_support(self, imported_meshes):
        T_support = 0
        mesh_objects = imported_meshes
        if self.build_volume is None:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.5))
            box = bpy.context.active_object
            box.name = "BuildVolume"
            box.scale.x = self.Buildsize_x
            box.scale.y = self.Buildsize_y
            box.scale.z = 1
        else:
            pass
        for i in range(len(mesh_objects)):
            mesh_name = mesh_objects[i].name
            obj = bpy.data.objects.get(mesh_name)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bounding_box_center = self.get_bounding_box_center(obj)
            original_location, minz, maxz = self.obj_alignment(obj)
            obj.location = bounding_box_center
            obj.select_set(False)

        for i in range(len(mesh_objects)):
            buildVolume = bpy.context.scene.objects["BuildVolume"]

            mesh_name = mesh_objects[i].name
            obj = bpy.data.objects.get(mesh_name)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            original_location, minz, maxz = self.obj_alignment(obj)

            sv = self.support_volume(obj, buildVolume, mesh_name, minz, maxz)

            obj.location = original_location
            obj.select_set(False)
            T_support += sv
        return T_support

# SupportChecker를 테스트하기 위한 코드는 아래에 추가됩니다.
# 서포트 부피를 계산하려면:
# checker = SupportChecker()
# total_support = checker.check_support()
# print("Total Support Volume:", total_support)
if __name__ == '__main__':
    # 메시를 처리하고 방향을 최적화하려면:
    processor = MeshProcessor()
    mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
    processor.process_meshes(mesh_objects)
    # 서포트 부피를 계산하려면:
    checker = SupportChecker()
    total_support = checker.check_support()
    print("Total Support Volume:", total_support)