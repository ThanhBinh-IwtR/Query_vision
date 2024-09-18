import csv
import os
import random
from pathlib import Path

def generate_prompts(elements_folder, prompts_output_folder):
    # Tạo folder đầu ra nếu nó không tồn tại
    if not os.path.exists(prompts_output_folder):
        os.makedirs(prompts_output_folder)

    # Danh sách để lưu các đường dẫn tệp _prompts.txt được tạo ra
    generated_files = []

    # Định nghĩa các mẫu đa dạng cho các prompt
    templates = [
        "A {gender} with {color} is {action}",
        "A {gender} wearing {color} is {action}",
        "A {gender} dressed in {color} is {action}",
        "A {gender} who has {color} is {action}",
        "A {gender} having {color} is {action}"

        
    ]

    # Lấy danh sách tất cả các file .csv trong folder elements
    csv_files = [f for f in os.listdir(elements_folder) if f.endswith('.csv')]
    # Xử lý từng file CSV
    for elements_file in csv_files:
        prompts = []
        csv_path = os.path.join(elements_folder, elements_file)
        with open(csv_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                color = row.get('color', '').strip().lower()
                action = row.get('action', '').strip().lower()
                gender = row.get('gender', '').strip().lower()

                # Chọn ngẫu nhiên một template
                template = random.choice(templates)

                # Điền vào template với dữ liệu từ CSV
                prompt = template.format(color=color, action=action, gender=gender)
                if prompt not in prompts: 
                    prompts.append(prompt)

        # Lưu các prompt vào một file mới trong folder đầu ra
        prompts_file_name = f"{os.path.splitext(elements_file)[0]}_prompts.txt"
        prompts_file_path = os.path.join(prompts_output_folder, prompts_file_name)
        with open(prompts_file_path, mode='w') as file:
            for prompt in prompts:
                file.write(prompt + '\n')

        # Chuẩn hóa đường dẫn và in ra
        normalized_path = os.path.normpath(prompts_file_path)
        print(f"Generated prompts file at: {normalized_path}")

        # Thêm đường dẫn tệp đã tạo vào danh sách
        generated_files.append(normalized_path)

    # Trả về danh sách các đường dẫn tệp _prompts.txt đã được tạo
    return generated_files

# elements_folder = "elements"  # Đường dẫn đến thư mục elements
# prompts_output_folder = "prompt_gen"
# generate_prompts(elements_folder, prompts_output_folder)


