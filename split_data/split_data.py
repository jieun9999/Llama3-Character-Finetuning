import os
import json
from collections import defaultdict
from math import floor

# 유동적으로 변경할 폴더명
folder_name = "0205_split_data"  

# 데이터 경로 설정
base_dir = f'/workspace/hdd/2.per_subject_text_daily_conversation_data/{folder_name}'
data_dir = os.path.join(base_dir, 'total')
train_dir = os.path.join(base_dir, '1.train')
val_dir = os.path.join(base_dir, '2.validation')
test_dir = os.path.join(base_dir, '3.test')

# train, validation, test 디렉토리 생성
os.makedirs(train_dir, exist_ok=True)
os.makedirs(val_dir, exist_ok=True)
os.makedirs(test_dir, exist_ok=True)

# 발화 전략별 데이터 개수 추적
overall_speech_act_counts = defaultdict(int)
speech_act_distribution = {
    "train": defaultdict(int),
    "validation": defaultdict(int),
    "test": defaultdict(int),
}

# 파일 분배 추적용 데이터 구조
allocated_files = set()

# 희귀 발화 전략 가진 데이터셋 먼저 저장
# train + validation 합산
speech_act_counts = {
    "위협하기": 40,
    "거절하기": 380,
    "사과하기": 449,
    "인사하기": 734,
    "감사하기": 1676,
    "반박하기": 2452,
    "부정감정 표현하기": 4571,
    "긍정감정 표현하기": 4650,
    "일상적으로 반응하기": 5025,
    "요구하기": 5837,
    "개인적으로 약속하기": 12285,
    "충고/제안하기": 24918,
    "질문하기": 174774,
    "정보 제공하기": 249110,
    "주장하기": 406198
}

def findRepSpeechAct(content):
    for speech_act, _ in speech_act_counts.items():
        if speech_act in content:
            return speech_act

# 데이터 읽기 및 발화 전략별 데이터 수 세기
speech_act_data = defaultdict(list)

for filename in os.listdir(data_dir):
    filepath = os.path.join(data_dir, filename)
    if not filepath.endswith(".json"):
        continue
    with open(filepath, 'r') as f:
        content = f.read()
        # speech_act_counts에서 위에서부터 포함되는 게 있나 봐야함
        speech_act = findRepSpeechAct(content)
        speech_act_data[speech_act].append((filename, content))
        overall_speech_act_counts[speech_act] += 1

        # speech_act_counts를 수정
        # 줄이고 0인 건 remove

        data = json.loads(content)

        for message in data['messages']:
            if message['role'] == 'system':
                continue

            speech_act = message['speechAct']

            if speech_act_counts[speech_act] <= 0:
                speech_act_counts.pop(speech_act, None)
            else:
                speech_act_counts[speech_act] -= 1


# 데이터 분배 함수 정의
def distribute_data(data_list, total_ratios):
    """각 발화 전략 데이터를 주어진 비율에 따라 분배."""
    total = len(data_list)
    train_size = floor(total * total_ratios["train"])
    val_size = floor(total * total_ratios["validation"])
    test_size = total - train_size - val_size

    train_data = data_list[:train_size]
    val_data = data_list[train_size:train_size + val_size]
    test_data = data_list[train_size + val_size:]

    return train_data, val_data, test_data

# 각 발화 전략에 대해 데이터 분배 및 파일 쓰기
ratios = {"train": 0.8, "validation": 0.1, "test": 0.1}

for speech_act, data_list in speech_act_data.items():
    # 데이터 분배
    train_data, val_data, test_data = distribute_data(data_list, ratios)

    # 분배 결과 저장
    for category, category_data in zip(["train", "validation", "test"], [train_data, val_data, test_data]):
        for filename, data in category_data:
            if filename in allocated_files:
                continue  # 이미 처리된 파일은 건너뛰기

            # 파일 쓰기
            dest_dir = {"train": train_dir, "validation": val_dir, "test": test_dir}[category]
            dest_path = os.path.join(dest_dir, filename)
            with open(dest_path, 'w', encoding='utf-8') as f:
                json_data = json.loads(data)
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            # 추적 정보 갱신
            allocated_files.add(filename)
            speech_act_distribution[category][speech_act] += 1

print("Dataset split and result saved!")
