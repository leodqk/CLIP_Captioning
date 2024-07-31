import cv2
import os
import get_caption

def extract_key_frames(video_path, output_folder, delay_seconds):
    # Mở video bằng OpenCV
    cap = cv2.VideoCapture(video_path)
    
    # Kiểm tra xem video có mở được không
    if not cap.isOpened():
        print("Không thể mở video")
        return

    # Lấy frame rate của video
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Frame rate: {fps} fps")
    
    # Tính toán số frame tương ứng với khoảng thời gian delay
    frame_interval = int(fps * delay_seconds)
    print(f"Số frame tương ứng với {delay_seconds} giây: {frame_interval} frame")
    
    frame_number = 0
    key_frame_number = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_number % frame_interval == 0:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                
            key_frame_path = f"{output_folder}/key_frame_{key_frame_number}.jpg"
            cv2.imwrite(key_frame_path, frame)
            print(f"Đã trích xuất: {key_frame_path}")

            print(get_caption.generate_caption(key_frame_path))
            key_frame_number += 1
        
        frame_number += 1

    # Giải phóng video capture object
    cap.release()
    print("Hoàn tất trích xuất key frame")

# Đường dẫn đến video và thư mục lưu trữ frame
video_path = 'test3.mp4'
output_folder = 'keyframe'
delay_seconds = 2

extract_key_frames(video_path, output_folder, delay_seconds)
