import pyaudio
import numpy as np
import time

def visualize_mic():
    p = pyaudio.PyAudio()
    device_index = None

    # 1. 自动找 USB 麦克风
    print("🔍 正在扫描音频设备...")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        name = info.get('name', '')
        if 'USB' in name or 'Webcam' in name:
            device_index = i
            print(f"✅ 选中设备 [{i}]: {name}")
            break
    
    if device_index is None:
        print("❌ 未找到 USB 麦克风！将使用默认设备。")

    # 2. 打开音频流
    try:
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=16000,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024)
    except Exception as e:
        print(f"❌ 打开麦克风失败: {e}")
        return

    print("\n🎤 麦克风测试开始！请对着麦克风说话...")
    print("--------------------------------------------------")

    try:
        while True:
            # 读取数据
            data = stream.read(1024, exception_on_overflow=False)
            samples = np.frombuffer(data, dtype=np.float32)
            
            # 计算音量 (RMS)
            volume = np.sqrt(np.mean(samples**2))
            
            # 放大显示 (只是为了视觉效果)
            bars = int(volume * 500) 
            
            # 打印音量条
            print(f"\r音量: {'|' * bars:<50} ({volume:.5f})", end="")
            
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n🛑 测试结束")
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    visualize_mic()
