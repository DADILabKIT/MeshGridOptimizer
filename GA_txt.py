# Ctrl + Shift + P
import sys
sys.path.append(r'C:\Users\User\Desktop\blender\decomposition grid\bpy_vscode') # 현재 폴더 경로(파이썬 파일이 있는 경로)

import datetime
import time
from FitnessEvaluator import FitnessEvaluator
from MeshAnalyzer import MeshAnalyzer

from deap import base, creator, tools, algorithms
import random


class GeneticAlgorithm:
    # 상수로 설정
    BOUNDS_XYZ = None
    BOUNDS_ANGLES = (0, 180)

    def __init__(self, stl_file_path, num_box=6, population_size=10, generations=100, cxpb=0.5, mutpb=0.2):
        self.stl_file_path = stl_file_path
        self.num_box = num_box
        self.population_size = population_size
        self.generations = generations
        self.cxpb = cxpb
        self.mutpb = mutpb

        self.mesh_analyzer = MeshAnalyzer(self.stl_file_path, self.num_box)
        bbox_data = self.mesh_analyzer.calculate_bbox()
        self.box_size = bbox_data[0]
        self.centroid_x = bbox_data[1]
        self.centroid_y = bbox_data[2]
        self.centroid_z = bbox_data[3]

        GeneticAlgorithm.BOUNDS_XYZ = (-self.box_size, self.box_size)  # 상수 업데이트

        self.fitness_evaluator = FitnessEvaluator(self.mesh_analyzer)

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        self.toolbox = base.Toolbox()
        self.setup_genetic_algorithm()

    def setup_genetic_algorithm(self):
        self.toolbox.register("attr_float_xyz", random.uniform, GeneticAlgorithm.BOUNDS_XYZ[0], GeneticAlgorithm.BOUNDS_XYZ[1])
        self.toolbox.register("attr_float_angles", random.uniform, GeneticAlgorithm.BOUNDS_ANGLES[0], GeneticAlgorithm.BOUNDS_ANGLES[1])
        self.toolbox.register("individual", tools.initCycle, creator.Individual, 
                              (self.toolbox.attr_float_xyz, self.toolbox.attr_float_angles), n=3)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self.fitness_evaluator.evaluate)
        self.toolbox.register("mate", tools.cxBlend, alpha=0.5)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        self.toolbox.register("initRepeat", tools.initRepeat, list)

    def run(self):
        population = self.toolbox.population(n=self.population_size)
        best_individual = None

        for generation in range(self.generations):
            offspring = algorithms.varAnd(population, self.toolbox, cxpb=self.cxpb, mutpb=self.mutpb)
            fits = self.toolbox.map(self.toolbox.evaluate, offspring)
            for fit, ind in zip(fits, offspring):
                ind.fitness.values = fit
            population = self.toolbox.select(offspring, k=len(population))
            best_individual = tools.selBest(population, k=1)[0]
            print(f"Generation: {generation+1} Best Fitness: {best_individual.fitness.values[0]}")

        print(f"Best individual: {best_individual}")
        print(f"Best genes: {best_individual.fitness.values}")
        return best_individual

# 이후에 GeneticAlgorithm 클래스의 인스턴스를 생성하고 실행할 수 있습니다.
# ga = GeneticAlgorithm(stl_file_path="path_to_stl_file")
# best_solution = ga.run()
if __name__ == "__main__":
    start = time.time()

    # 현재 날짜와 시간을 문자열로 변환
    current_time_str = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # 메모장 파일 이름에 현재 날짜와 시간을 포함
    log_file_name = f"log_{current_time_str}.txt"
    def filter_and_save_log(log_path):
        # 파일을 읽기 모드로 열어서 모든 줄을 lines에 저장
        with open(log_path, 'r') as f:
            lines = f.readlines()

        # "Import finished in"으로 시작하지 않는 줄만 filtered_lines에 저장
        filtered_lines = [line for line in lines if not line.startswith("Import finished in")]

        # 파일을 쓰기 모드로 열어서 filtered_lines를 다시 파일에 씀
        with open(log_path, 'w') as f:
            f.writelines(filtered_lines)

    print("start~!@@@@@@@@@@@@@@@@@@@@@@@")

    # 원래의 stdout 저장
    orig_stdout = sys.stdout

    # 쓰기 모드로 파일 열기
    with open(log_file_name, 'w') as f:
        sys.stdout = f # stdout을 파일로 리디렉션

        # 원래 코드
        stl_file_path = r"models\Stanford_bunny.stl"
        ga = GeneticAlgorithm(stl_file_path)
        best_solution = ga.run()
        print('걸린 시간: ', time.time()-start)
        sys.stdout = orig_stdout

    # 함수 호출
    filter_and_save_log(log_file_name)
        