import asyncio
import websockets
import pyaudio
import jwt
import time
import json
import base64
import threading
import queue
import numpy as np
import config

try:
    from scipy.signal import resample
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️ Scipy 未安装，使用简易降采样")

# GLM-4-Voice 配置
URL = "wss://open.bigmodel.cn/api/paas/v4/realtime"

class ZhipuRealtimeClient:
    def __init__(self, action_engine=None):
        print("🚀 初始化 GLM-4-Voice (V45 协议修正版)...")
        self.api_key = config.ZHIPU_API_KEY
        self.action_engine = action_engine 
        self.running = False
        
        # 队列
        self.mic_queue = queue.Queue(maxsize=200) 
        self.spk_queue = queue.Queue(maxsize=200)
        
        self.p = pyaudio.PyAudio()
        self._find_devices()
        
        # 🔥 严格的帧长对齐 (关键!)
        # API 要求: 24000Hz, Int16. 
        # 建议每包 60ms = 0.06s * 24000 = 1440 samples
        self.API_RATE = 24000
        self.API_CHUNK = 1440 
        
        # 硬件: 48000Hz
        self.HW_RATE = 48000
        self.HW_CHUNK = 2880 # 60ms @ 48k (正好是 API_CHUNK 的 2 倍)
        
        self.MIC_GAIN = 10.0 

    def _find_devices(self):
        self.input_index = None
        self.output_index = None
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            name = info.get('name', '')
            if info.get('maxInputChannels') > 0:
                if ('USB' in name or 'ReSpeaker' in name) and 'Webcam' not in name:
                    self.input_index = i
            if info.get('maxOutputChannels') > 0:
                if 'Headphones' in name or 'bcm2835' in name:
                    self.output_index = i
        
        if self.input_index is None: self.input_index = 2
        if self.output_index is None: self.output_index = 0
        print(f"✅ [Mic] ID:{self.input_index} | [Speaker] ID:{self.output_index}")

    def _generate_token(self):
        try:
            id, secret = self.api_key.split(".")
            payload = { "api_key": id, "exp": int(time.time()) + 3600, "timestamp": int(time.time()) } # 延长有效期
            return jwt.encode(payload, secret.encode("utf-8"), algorithm="HS256", headers={"alg": "HS256", "sign_type": "SIGN"})
        except: return ""

    # ---------------------------------------------------------
    # 🔩 硬件层 (永不停止)
    # ---------------------------------------------------------
    def _hardware_loop(self):
        input_stream = None
        output_stream = None
        try:
            input_stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=self.HW_RATE, input=True, input_device_index=self.input_index, frames_per_buffer=self.HW_CHUNK)
            output_stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.HW_RATE, output=True, output_device_index=self.output_index, frames_per_buffer=self.HW_CHUNK)
            print("✅ 硬件层就绪")

            while self.running:
                # A. 录音
                try:
                    data = input_stream.read(self.HW_CHUNK, exception_on_overflow=False)
                    samples = np.frombuffer(data, dtype=np.float32)
                    
                    # 简单静音门限 (Noise Gate)
                    # if np.mean(np.abs(samples)) < 0.01:
                    #     samples = np.zeros_like(samples)
                    
                    if self.mic_queue.full(): self.mic_queue.get_nowait()
                    self.mic_queue.put(samples)
                except: pass

                # B. 播放
                try:
                    if not self.spk_queue.empty():
                        pcm_data = self.spk_queue.get_nowait()
                        output_stream.write(pcm_data)
                    else:
                        time.sleep(0.005)
                except: pass

        except Exception as e:
            print(f"❌ 硬件错误: {e}")
        finally:
            if input_stream: input_stream.stop_stream(); input_stream.close()
            if output_stream: output_stream.stop_stream(); output_stream.close()

    # ---------------------------------------------------------
    # ☁️ 网络层
    # ---------------------------------------------------------
    async def _network_sender(self, ws):
        print("   -> 发送线程启动")
        # 清空积压
        while not self.mic_queue.empty(): self.mic_queue.get()
        
        while self.running and ws.open:
            try:
                # 🔥 关键策略：如果队列有数据，发送数据；如果没有，发送静音帧保活
                # 这比 WebSocket Ping 更管用，因为 API 期待的是音频流
                if not self.mic_queue.empty():
                    samples_48k = self.mic_queue.get()
                    # 增益
                    samples_48k = samples_48k * self.MIC_GAIN
                    samples_48k = np.clip(samples_48k, -1.0, 1.0)
                    
                    # 降采样 48k -> 24k
                    if SCIPY_AVAILABLE:
                        # 高质量重采样
                        samples_24k = resample(samples_48k, self.API_CHUNK)
                    else:
                        # 简易降采样
                        samples_24k = samples_48k[::2]

                    # 转 Int16
                    pcm_bytes = (samples_24k * 32767).astype(np.int16).tobytes()
                else:
                    # 🔥 发送静音帧保活 (60ms 的静音)
                    await asyncio.sleep(0.06) 
                    # 仅在长时间静默时偶尔发一个静音包防止断连? 
                    # 不，Realtime API 通常喜欢持续的数据流。
                    # 这里我们简单 sleep 等待硬件数据即可，因为硬件层是匀速生产的。
                    continue

                await ws.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": base64.b64encode(pcm_bytes).decode("utf-8")
                }))
                
            except Exception as e:
                print(f"发送异常: {e}")
                break

    async def _network_receiver(self, ws):
        print("   <- 接收线程启动")
        async for message in ws:
            try:
                msg = json.loads(message)
                if msg["type"] == "audio.delta":
                    print(".", end="", flush=True)
                    audio_data = base64.b64decode(msg["delta"])
                    
                    # 升采样 24k -> 48k
                    samples_24k = np.frombuffer(audio_data, dtype=np.int16)
                    # 线性插值升采样 (比 repeat 更平滑一点)
                    samples_48k = np.repeat(samples_24k, 2) 
                    
                    self.spk_queue.put(samples_48k.tobytes())
                    
                    if self.action_engine:
                         # 简单的 RMS 计算
                         rms = np.sqrt(np.mean(samples_24k.astype(float)**2))
                         if rms > 1000 and np.random.rand() < 0.1: pass

                elif msg["type"] == "input_audio_buffer.speech_started":
                    print("\n⚡ 打断!")
                    while not self.spk_queue.empty(): self.spk_queue.get()
                
                elif msg["type"] == "error":
                    print(f"\n⚠️ API Error: {msg}")

                elif msg["type"] == "session.created":
                    print("\n✅ 会话已建立")

            except: break
        print("\n👋 连接关闭")

    async def _run_network_loop(self):
        while self.running:
            token = self._generate_token()
            headers = { "Authorization": f"Bearer {token}" }
            
            try:
                print("🔄 连接智谱云端...")
                # 🔥 关键：ping_interval=None 禁用默认 ping，防止与音频流冲突
                async with websockets.connect(URL, extra_headers=headers, ping_interval=None) as ws:
                    
                    # 1. 建立会话
                    await ws.send(json.dumps({
                        "type": "session.update",
                        "session": { 
                            "voice": "Blue", 
                            "instructions": "你是Friday。请用中文简短回答。",
                            "turn_detection": {
                                "type": "server_vad" # 显式开启服务端 VAD
                            }
                        }
                    }))
                    
                    # 2. 并发读写
                    await asyncio.gather(
                        self._network_sender(ws),
                        self._network_receiver(ws)
                    )
            except Exception as e:
                print(f"⚠️ 网络异常: {e}")
                await asyncio.sleep(2)

    def start(self):
        if self.running: return
        self.running = True
        threading.Thread(target=self._hardware_loop, daemon=True).start()
        threading.Thread(target=lambda: asyncio.run(self._run_network_loop()), daemon=True).start()

    def stop(self):
        self.running = False
