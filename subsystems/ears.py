import sys
import os
import pyaudio
import numpy as np
import sherpa_onnx
import time
import glob
import re
from collections import deque

class Ear:
    def __init__(self):
        print("👂 耳朵模块初始化 (V33 语义垃圾过滤版)...")
        
        base_dir = "/home/scottwang/lelamp_v2/models/sherpa_paraformer"
        onnx_files = glob.glob(os.path.join(base_dir, "*.onnx"))
        tokens_file = os.path.join(base_dir, "tokens.txt")
        
        if not onnx_files:
            print("❌ 错误: 模型未找到")
            sys.exit(1)
            
        try:
            self.recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
                paraformer=onnx_files[0],
                tokens=tokens_file,
                num_threads=4,
                sample_rate=16000,
                decoding_method="greedy_search"
            )
        except Exception as e:
            print(f"❌ 引擎启动失败: {e}")
            sys.exit(1)

        self.p = pyaudio.PyAudio()
        self.device_index = None
        self.hardware_rate = 16000 
        
        for i in range(self.p.get_device_count()):
            try:
                info = self.p.get_device_info_by_index(i)
                name = info.get('name', '')
                if 'USB' in name and 'Webcam' not in name:
                    self.device_index = i
                    print(f"✅ 锁定独立麦克风: {name}")
                    break 
            except: pass
            
        for rate in [48000, 44100, 16000]:
            try:
                stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=rate,
                                   input=True, input_device_index=self.device_index, 
                                   frames_per_buffer=1024)
                stream.close()
                self.hardware_rate = rate
                break
            except: continue
        
        self.calibrate_noise()

    def calibrate_noise(self):
        print("🤫 校准底噪 (3.0x)...")
        self.gain = 3.0 
        try:
            stream = self.p.open(format=pyaudio.paFloat32, channels=1, 
                               rate=self.hardware_rate, input=True, 
                               input_device_index=self.device_index, frames_per_buffer=1024)
            noise_levels = []
            for _ in range(30):
                data = stream.read(1024, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.float32) * self.gain
                noise_levels.append(np.sqrt(np.mean(samples**2)))
            stream.close()
            avg = np.mean(noise_levels)
            self.dynamic_threshold = max(avg * 2.5, 0.10) 
            print(f"✅ 阈值设定: {self.dynamic_threshold:.4f}")
        except: self.dynamic_threshold = 0.10

    def _is_gibberish(self, text):
        """
        🔥 V33 核心算法：语义垃圾检测器
        """
        if not text: return True
        if len(text) < 2: return True # 过滤单字
        
        # 1. 绝对黑名单 (常见噪音幻觉)
        blacklist = [
            "the", "The", "嗯", "呃", "十以", "evidence", "Evidence",
            "没有没有", "谢谢观看", "不客气", "字幕",
            "我个一个", "这的一", "个一" # 针对您反馈的乱码
        ]
        for b in blacklist:
            if b in text: return True

        # 2. 重复度检测 (如: "对对对对", "啊啊啊")
        # 如果去重后的字数 < 总字数的一半，说明大量重复
        if len(set(text)) < len(text) * 0.5:
            return True

        # 3. 虚词密度检测 (检测 "我的一了个这" 这种无意义组合)
        # 这些词在正常句子中是连接词，但如果一句话里全都是这些词，那就是乱码
        stop_words = set("的了着是这个我你他它个一不")
        stop_count = sum(1 for char in text if char in stop_words)
        
        # 如果一句话超过4个字，且80%以上都是虚词 -> 判定为噪音生成的乱码
        if len(text) > 4 and (stop_count / len(text)) > 0.8:
            return True

        # 4. 纯非中文字符检测 (过滤 pure symbols)
        if not re.search(r'[\u4e00-\u9fa5]', text) and not re.search(r'[a-zA-Z]', text):
            return True

        return False

    def listen(self, mouth_ref=None):
        try:
            stream = self.p.open(format=pyaudio.paFloat32, channels=1, 
                               rate=self.hardware_rate, 
                               input=True, input_device_index=self.device_index, 
                               frames_per_buffer=1024)
        except: time.sleep(1); return ""

        print(f"\r🎤 聆听中...", end="", flush=True)
        frames = []
        pre_buffer = deque(maxlen=int(self.hardware_rate/1024*0.5))
        silence_chunks = 0
        is_speaking = False
        
        try:
            while True:
                # 硬件级静音
                if mouth_ref and mouth_ref.is_speaking:
                    if is_speaking: return ""
                    time.sleep(0.1); frames.clear(); pre_buffer.clear()
                    continue

                data = stream.read(1024, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.float32) * self.gain
                samples = np.clip(samples, -1.0, 1.0)
                vol = np.sqrt(np.mean(samples**2))
                
                if not is_speaking:
                    pre_buffer.append(samples)
                    if vol > self.dynamic_threshold:
                        is_speaking = True
                        silence_chunks = 0
                        frames.extend(pre_buffer)
                else:
                    frames.append(samples)
                    if vol > (self.dynamic_threshold * 0.7): silence_chunks = 0
                    else: silence_chunks += 1
                
                if is_speaking and silence_chunks > 15: break 
                if len(frames) > int(self.hardware_rate/1024*10): break 

            stream.stop_stream(); stream.close()
            if not is_speaking: return ""
            
            audio_data = np.concatenate(frames)
            if self.hardware_rate != 16000:
                n = int(len(audio_data) * 16000 / self.hardware_rate)
                audio_data = np.interp(np.linspace(0,1,n,endpoint=False), np.linspace(0,1,len(audio_data)), audio_data)
            
            s = self.recognizer.create_stream()
            s.accept_waveform(16000, audio_data)
            self.recognizer.decode_stream(s)
            text = s.result.text.strip()
            
            # 🔥 应用强力过滤器
            if self._is_gibberish(text): 
                print(f"🗑️ 过滤乱码: {text}")
                return ""
            
            if text:
                print(f"👂 听到: {text}")
                return text
        except: pass
        return ""
