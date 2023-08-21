
# 쓰기 모드로 파일 열기
def filter_and_save_log(log_path):
        # 파일을 읽기 모드로 열어서 모든 줄을 lines에 저장
        with open(log_path, 'r') as f:
            lines = f.readlines()

        # "Import finished in"으로 시작하지 않는 줄만 filtered_lines에 저장
        filtered_lines = [line for line in lines if not line.startswith("Import finished in")]

        # 파일을 쓰기 모드로 열어서 filtered_lines를 다시 파일에 씀
        with open(log_path, 'w') as f:
            f.writelines(filtered_lines)

log_file_name = r'결과 txt\F7정규화하고돌려봄_F1버그 있음_0.01 볼륨차이로 해결해봄.txt'

# 함수 호출
filter_and_save_log(log_file_name)
    