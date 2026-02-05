import time
import threading
import sys
import os
import atexit
import cv2
import datetime
import random
from flask import Flask, Response, jsonify, render_template
import config
from drivers.sts3215 import ServoDriver
from subsystems.vision import VisionSystem
from subsystems.actions import ActionEngine
from subsystems.ears import Ear # 仅用于唤醒
from subsystems.zhipu_driver import ZhipuRealtimeClient # 新核心

app = Flask(__name__, static_folder='static')
PHOTO_DIR = "static/photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

running = True
SYSTEM_STATUS = {"chat_log": [], "latest_photo": None}

driver = None; vision = None; actor = None; ears = None
realtime_bot = None 

def emergency_shutdown():
    global driver, running
    print("\n🛑 安全停机...")
    running = False 
    if realtime_bot: realtime_bot.stop()
    if driver and actor:
        try:
            for i in config.EXIT_POSE.keys(): driver.enable_torque(i, 1)
            time.sleep(0.05)
            actor._smooth_move(config.EXIT_POSE[config.ID_PAN], config.EXIT_POSE[config.ID_TILT], 1.5)
        except: pass
atexit.register(emergency_shutdown)

# 📸 拍照函数
def perform_capture():
    if not vision: return None
    frame = None
    for _ in range(3):
        frame = vision.get_raw_frame()
        if frame is not None: break
        time.sleep(0.1)
    if frame is not None:
        ts = int(time.time())
        filename = f"photo_{ts}.jpg"
        filepath = os.path.join(PHOTO_DIR, filename)
        try: cv2.imwrite(filepath, frame)
        except: return None
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        SYSTEM_STATUS["latest_photo"] = {"id": str(ts), "url": f"/static/photos/{filename}", "time": time_str}
        return frame
    return None

@app.route('/')
def index(): return render_template('index.html')
@app.route('/video_feed')
def video_feed():
    def gen():
        while running:
            if vision:
                frame_bytes = vision.get_latest_jpeg()
                if frame_bytes: yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.04)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/get_status')
def get_status(): return jsonify(SYSTEM_STATUS)

def control_loop():
    while running:
        if actor: time.sleep(0.05)

def voice_loop():
    global realtime_bot
    print("👂 待机中... 请说 'Friday' 或 '管家' 唤醒")
    
    WAKE_WORDS = ["friday", "Friday", "管家", "星期五"]
    is_in_session = False
    
    while running:
        # 1. 如果不在通话中，使用 Ears 监听唤醒词
        if not is_in_session:
            if not ears: time.sleep(1); continue
            
            # 使用本地监听（这时候并不占线，因为 Realtime Client 还没启动）
            text = ears.listen()
            if not text: continue
            
            triggered = False
            for w in WAKE_WORDS:
                if w in text: triggered = True; break
            
            if triggered:
                print(f"✨ 唤醒成功! 连接云端大脑...")
                if actor: actor.execute("happy")
                
                # 启动全双工客户端
                # 注意：启动前需要释放 ears 对麦克风的占用？
                # PyAudio 通常允许多个流，如果报错可能需要 ears.close()
                realtime_bot = ZhipuRealtimeClient(action_engine=actor)
                realtime_bot.start()
                is_in_session = True
                
                # 通话限时 30秒 (演示用)
                # 在这30秒内，主线程只是在等待，实际交互在 ZhipuRealtimeClient 的后台线程中进行
                for _ in range(30):
                    if not running: break
                    time.sleep(1)
                
                print("💤 会话结束，回归待机。")
                realtime_bot.stop()
                realtime_bot = None
                is_in_session = False
                # 稍微冷却一下，防止立刻误触
                time.sleep(2)
        else:
            time.sleep(1)

def main():
    global driver, vision, actor, ears, running
    print("\n🚀 LELAMP V36 - GLM-4-Voice REALTIME")
    
    try: driver = ServoDriver(config.SERIAL_PORT, config.BAUDRATE)
    except: pass
    if driver:
        for i, pos in config.START_POSE.items():
            driver.enable_torque(i, 1); driver.write_pos(i, pos, 40); time.sleep(0.1)
    
    try: vision = VisionSystem()
    except: pass
    try: ears = Ear() # 唤醒监听专用
    except: pass
    actor = ActionEngine(driver)
    
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=control_loop, daemon=True).start()
    
    try:
        voice_loop()
    except KeyboardInterrupt: pass 

if __name__ == "__main__":
    main()
