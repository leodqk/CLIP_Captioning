from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import logging
import cv2
import get_caption_VIT32
import time
from threading import Thread, Event
from queue import Queue
import socket

application = Flask(__name__)
CORS(application)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Sử dụng dictionary để lưu trữ captions cho mỗi session
def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        # Connect to an external host to get the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(("8.8.8.8", 1))  # Example using Google DNS
        IP_CONNECT = s.getsockname()[0]
        s.close()
    except Exception:
        IP_CONNECT = "127.0.0.1"
    return IP_CONNECT

sessions = {}

def calculate_delay(frames_per_second):
    if frames_per_second <= 30:
        return 2
    elif frames_per_second <= 60:
        return 3
    else:
        return 4

def extract_key_frames(video_path, output_folder, session_id):
    video_capture = cv2.VideoCapture(video_path)
    if not video_capture.isOpened():
        logger.error("Không thể mở video")
        return

    frames_per_second = video_capture.get(cv2.CAP_PROP_FPS)
    delay_seconds = calculate_delay(frames_per_second)
    frame_interval = int(frames_per_second * delay_seconds)
    
    frame_number = 0
    key_frame_number = 0
    
    while video_capture.isOpened():
        return_value, frame = video_capture.read()
        if not return_value:
            break
        
        if frame_number % frame_interval == 0:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                
            key_frame_path = f"{output_folder}/key_frame_{key_frame_number}.jpg"
            cv2.imwrite(key_frame_path, frame)
            caption = get_caption_VIT32.generate_caption(key_frame_path)
            with application.app_context():
                sessions[session_id]["captions"].put(caption)
            logger.info(f"Generated caption for session {session_id}: {caption}") 
            key_frame_number += 1
        
        frame_number += 1

    video_capture.release()
    logger.info(f"Hoàn tất trích xuất key frame cho session {session_id}")
    sessions[session_id]["captions"].put("[DONE]")

@application.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({"error": "No video file selected"}), 400

    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({"error": "No session ID provided"}), 400

    video_path = f"temp_video_{session_id}.mp4"
    video_file.save(video_path)
    output_folder = f'result_{session_id}'

    sessions[session_id] = {
        "captions": Queue()
    }

    Thread(target=extract_key_frames, args=(video_path, output_folder, session_id)).start()
    return jsonify({"status": "Processing video", "session_id": session_id}), 202

@application.route('/get_captions/<session_id>', methods=['GET'])
def get_captions(session_id):
    if session_id not in sessions:
        return jsonify({"error": "Invalid session ID"}), 400

    try:
        caption = sessions[session_id]["captions"].get(timeout=30)  # Wait up to 30 seconds for a new caption
        if caption == "[DONE]":
            del sessions[session_id]
        return jsonify({"caption": caption})
    except:
        return jsonify({"caption": None}), 204  # No Content

if __name__ == '__main__':
    HOST_CONNECT = get_local_ip()
    PORT_CONNECT = 5000
    application.run(host= HOST_CONNECT, port=PORT_CONNECT, debug=True)
