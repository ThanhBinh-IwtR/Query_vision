import cv2
import os
from ultralytics import YOLO
from pathlib import Path
from tqdm import tqdm




# Mở video
    # cap = cv2.VideoCapture(str(video_path))  # Chuyển đổi video_path thành chuỗi
    # fps = cap.get(cv2.CAP_PROP_FPS)  # Lấy số frame trên mỗi giây của video
    # frame_count = 0
    # save_count = 0
    # frame_time = 1 / fps  # Thời gian của mỗi frame
    # interval_frame_count = int(frame_interval / frame_time)  # Số frame giữa mỗi lần cắt
    # Load mô hình YOLOv8# Mở video
    # cap = cv2.VideoCapture(str(video_path))  # Chuyển đổi video_path thành chuỗi
    # fps = cap.get(cv2.CAP_PROP_FPS)  # Lấy số frame trên mỗi giây của video
    # frame_count = 0
    # save_count = 0
    # frame_time = 1 / fps  # Thời gian của mỗi frame
    # interval_frame_count = int(frame_interval / frame_time)  # Số frame giữa mỗi lần cắt
    # Load mô hình YOLOv8
def process_frames_in_folder(input_folder, frame_output_folder, label_output_folder):
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(frame_output_folder):
        os.makedirs(frame_output_folder)
    if not os.path.exists(label_output_folder):
        os.makedirs(label_output_folder)

    # Load mô hình YOLOv8
    model = YOLO('yolov8l.pt')  # Bạn có thể thay đổi sang các phiên bản khác (yolov8s.pt, yolov8m.pt,...)
    
    # Lấy tất cả ảnh trong thư mục con và sắp xếp chúng
    frame_files = sorted(Path(input_folder).glob('*.jpg'))  # Giả sử các frame có định dạng .png
    for i, frame_path in enumerate(tqdm(frame_files, desc="Processing frames", unit="frame")):
        # Đọc frame
        frame = cv2.imread(str(frame_path))
        if frame is None:
            print(f"Failed to read frame: {frame_path}")
            continue

        # Chạy mô hình YOLOv8 trên frame
        results = model(frame)
        
        # Tạo tên file .txt tương ứng và lưu thông tin bounding box vào file .txt theo định dạng yêu cầu
        txt_path = os.path.join(label_output_folder, f"{i:06}.txt")
        with open(txt_path, 'w') as f:
            for result in results:
                boxes = result.boxes  # Lấy kết quả bounding box
                for box in boxes:
                    cls = int(box.cls[0])  # Class ID
                    
                    # Chỉ lưu bounding box của class "person" (ID = 0)
                    if cls == 0:
                        # Chuẩn hóa tọa độ: Chia các giá trị cho kích thước của ảnh
                        img_h, img_w = frame.shape[:2]  # Lấy chiều cao và chiều rộng của ảnh
                        x_center = box.xywh[0][0] / img_w
                        y_center = box.xywh[0][1] / img_h
                        width = box.xywh[0][2] / img_w
                        height = box.xywh[0][3] / img_h
                        
                        # Lưu vào file .txt với định dạng "0 class_id x_center y_center width height"
                        f.write(f"0 {cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        print(f"Saved labels: {txt_path}")

        # Sau khi lưu kết quả YOLO, đổi tên và lưu frame vào thư mục đầu ra
        frame_name = os.path.join(frame_output_folder, f"{i:06}.png")
        cv2.imwrite(frame_name, frame)
        print(f"Saved frame: {frame_name}")

    

def get_next_available_folder(base_path):
    index = 0
    while True:
        folder_name = f"{index:04}"
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.exists(folder_path):
            return folder_path, folder_name
        index += 1

def process_all_folders(input_folder, frame_output_base, label_output_base):
    print("---PREPARING---")
    subfolders = [f for f in Path(input_folder).iterdir() if f.is_dir()]  # Lấy tất cả các thư mục con trong thư mục đầu vào
    for folder_path in tqdm(subfolders, desc="Processing folders", unit="folder"):
        # Tìm thư mục tiếp theo để lưu
        frame_output_folder, folder_name = get_next_available_folder(frame_output_base)
        label_output_folder = os.path.join(label_output_base, folder_name)

        print((folder_path.name).upper())
        # Gọi hàm xử lý cho từng tập frame
        process_frames_in_folder(folder_path, frame_output_folder, label_output_folder)
        print("--------------------------------------------------")
        print(f"Video completed: {folder_path.name}")
        print(f"Frame and bbox save in: {frame_output_folder} and {label_output_folder}")
        print("--------------------------------------------------")

# Đường dẫn tới thư mục chứa các thư mục con (mỗi thư mục con chứa các frame)
input_folder = "video_data"
frame_output_base = "images"
label_output_base = "labels_with_ids"

# Gọi hàm để xử lý tất cả các thư mục trong thư mục đầu vào
process_all_folders(input_folder, frame_output_base, label_output_base)
