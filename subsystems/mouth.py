import os
import subprocess
import threading
import time

class Mouth:
    def __init__(self):
        print("👄 嘴巴模块初始化 (V32 阻塞版)...")
        self.is_speaking = False 

    def _speak_thread(self, text):
        """后台说话线程"""
        # 🔥 1. 立刻锁死标志位
        self.is_speaking = True
        try:
            # 生成
            cmd_gen = f'edge-tts --text "{text}" --write-media /tmp/tts.mp3 --voice zh-CN-YunxiNeural --rate=+20%'
            subprocess.run(cmd_gen, shell=True, stderr=subprocess.DEVNULL)
            
            # 播放 (mpg123 会阻塞直到播放完毕)
            subprocess.run("mpg123 -q /tmp/tts.mp3", shell=True, stderr=subprocess.DEVNULL)
            
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            # 🔥 2. 只有播放彻底结束后，才释放标志位
            # 再多给 0.5 秒缓冲，防止音频设备延迟
            time.sleep(0.5) 
            self.is_speaking = False

    def speak(self, text):
        if not text: return
        # 启动线程，但标志位已经在 _speak_thread 里被接管
        self.is_speaking = True # 先置 True 防止线程启动延迟
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()
