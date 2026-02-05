import cv2
import numpy as np
import os
import time
import threading

class VisionSystem:
    def __init__(self):
        print("📷 视觉系统初始化 (标准稳定版)...")
        self.cap = cv2.VideoCapture(0)
        
        # 恢复标准分辨率，防止模型崩溃
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        model_path = "/home/scottwang/lelamp_v2/models/yolov8n.onnx"
        self.net = None
        if os.path.exists(model_path):
            try:
                self.net = cv2.dnn.readNetFromONNX(model_path)
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                print("✅ YOLOv8 加载成功")
            except: pass
        else:
            print("⚠️ 未找到 YOLO 模型")

        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.running = True
        
        threading.Thread(target=self._update_loop, daemon=True).start()

        self.last_offset = None
        self.frame_count = 0

    def _update_loop(self):
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.frame_lock:
                        self.current_frame = frame
                else:
                    time.sleep(0.1)
            time.sleep(0.01)

    def get_raw_frame(self):
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None

    def get_latest_jpeg(self):
        frame = self.get_raw_frame()
        if frame is not None:
            _, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            return buf.tobytes()
        return None

    def get_face_offset(self):
        if self.net is None: return None
        
        frame = self.get_raw_frame()
        if frame is None: return None

        self.frame_count += 1
        if self.frame_count % 5 != 0:
            return self.last_offset 

        h, w = frame.shape[:2]
        
        # 🔥 核心修复：改回 (640, 640) 以匹配标准模型
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward()
        
        outputs = np.array([cv2.transpose(outputs[0])])
        rows = outputs.shape[1]
        
        boxes = []
        scores = []
        
        x_factor = w / 640
        y_factor = h / 640

        for i in range(rows):
            classes_scores = outputs[0][i][4:]
            (minScore, maxScore, minClassLoc, (class_id, _)) = cv2.minMaxLoc(classes_scores)
            
            if maxScore >= 0.4 and class_id == 0:
                row = outputs[0][i]
                x_center, y_center, width, height = row[0], row[1], row[2], row[3]
                left = int((x_center - width * 0.5) * x_factor)
                top = int((y_center - height * 0.5) * y_factor)
                boxes.append([left, top, int(width*x_factor), int(height*y_factor)])
                scores.append(maxScore)

        indices = cv2.dnn.NMSBoxes(boxes, scores, 0.4, 0.45)
        
        target_center = None
        if len(indices) > 0:
            max_area = 0
            for i in indices.flatten():
                x, y, w_box, h_box = boxes[i]
                if (w_box * h_box) > max_area:
                    max_area = w_box * h_box
                    target_center = (x + w_box/2, y + h_box/2)
        
        if target_center:
            tx, ty = target_center
            offset_x = (w/2 - tx) / (w/2)
            offset_y = (h/2 - ty) / (h/2)
            
            if abs(offset_x) < 0.1: offset_x = 0
            if abs(offset_y) < 0.1: offset_y = 0
            
            self.last_offset = (offset_x, offset_y)
            return (offset_x, offset_y)
        
        self.last_offset = None
        return None

    def release(self):
        self.running = False
        self.cap.release()
