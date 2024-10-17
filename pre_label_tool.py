import cv2
import os
from ultralytics import YOLO
from pathlib import Path
from tqdm import tqdm

def extract_and_detect(video_path, frame_output_folder, label_output_folder, frame_interval=0.5):
    # Create directories if they don't exist
    if not os.path.exists(frame_output_folder):
        os.makedirs(frame_output_folder)
    if not os.path.exists(label_output_folder):
        os.makedirs(label_output_folder)

    # Open video
    cap = cv2.VideoCapture(str(video_path))  # Convert video_path to string
    fps = cap.get(cv2.CAP_PROP_FPS)  # Get frames per second of the video
    frame_count = 0
    save_count = 0
    frame_time = 1 / fps  # Time of each frame
    interval_frame_count = int(frame_interval / frame_time)  # Number of frames between each cut
    # Load YOLOv8 model
    model = YOLO('yolov8l.pt')  # You can replace this with a different model version (yolov8s.pt, yolov8m.pt,...)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Save frame every 0.5 seconds
        if frame_count % interval_frame_count == 0:
            # Save frame as an image
            frame_name = os.path.join(frame_output_folder, f"{save_count:06}.png")
            cv2.imwrite(frame_name, frame)
            print(f"Saved {frame_name}")
            
            # Run YOLOv8 model on the frame
            results = model(frame)
            
            # Create corresponding .txt file
            txt_path = os.path.join(label_output_folder, f"{save_count:06}.txt")

            # Save bounding box to .txt file in the required format
            with open(txt_path, 'w') as f:
                for result in results:
                    boxes = result.boxes  # Get bounding box results
                    for box in boxes:
                        cls = int(box.cls[0])  # Class ID
                        
                        # Only save bounding box for class "person" (ID = 0)
                        if cls == 0:
                            # Normalize coordinates: Divide values by the size of the image
                            img_h, img_w = frame.shape[:2]  # Get image height and width
                            x_center = box.xywh[0][0] / img_w
                            y_center = box.xywh[0][1] / img_h
                            width = box.xywh[0][2] / img_w
                            height = box.xywh[0][3] / img_h
                            
                            # Save to .txt file with format "0 class_id x_center y_center width height"
                            f.write(f"0 {cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            
            print(f"Saved {txt_path}")
            save_count += 1
        
        frame_count += 1

    cap.release()

def find_next_available_folder(base_folder):
    folder_index = 0
    while True:
        folder_name = os.path.join(base_folder, f"{folder_index:04}")
        if not os.path.exists(folder_name):
            return folder_name
        folder_index += 1

def process_all_videos(input_folder, frame_output_base, label_output_base, frame_interval=0.5):
    print("---PREPARING---")
    video_files = list(Path(input_folder).glob('*.mp4'))  # Get all .mp4 videos in the directory
    for video_path in tqdm(video_files, desc="Processing videos", unit="video"):
        # Find next available subfolder
        frame_output_folder = find_next_available_folder(frame_output_base)
        label_output_folder = find_next_available_folder(label_output_base)
        print((video_path.name).upper())
        # Call the processing function for each video
        extract_and_detect(video_path, frame_output_folder, label_output_folder, frame_interval)
        print("--------------------------------------------------")
        print(f"Video completed: {video_path.name}")
        print(f"Video path: {frame_output_folder} and {label_output_folder}")
        print("--------------------------------------------------")

# Paths to the input folder containing videos, and the base directories for saving frames and labels
input_folder = "video_data"
frame_output_base = "images"
label_output_base = "labels_with_ids"

# Call the function to process all videos in the input directory
process_all_videos(input_folder, frame_output_base, label_output_base, frame_interval=0.5)
