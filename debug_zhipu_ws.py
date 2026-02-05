import websocket
import threading
import time
import json
import jwt
import sys
import base64

# ================= 配置区 =================
# 🔴 请务必替换为你真实的 API Key !!!
API_KEY = "6c2639adffec4a7f9c49d8061a4a32d8.IPnxt39txoRtaJwI" 

# 智谱 Realtime 地址
WS_URL = "wss://open.bigmodel.cn/api/paas/v4/realtime" 
# =========================================

# 状态标志
is_running = True

def generate_token(apikey: str, exp_seconds: int = 600):
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        print("❌ API Key 格式错误！应该是 'id.secret' 的形式")
        sys.exit(1)

    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }
    
    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )

def on_message(ws, message):
    try:
        data = json.loads(message)
        event_type = data.get('type')
        
        # --- 针对演示优化的日志输出 ---
        if event_type == 'response.audio.delta':
            # 音频流数据太长，不打印内容，只打印接收状态，证明流式成功
            print("🔊 [接收音频流] <Audio Chunk Received...>")
        elif event_type == 'response.text.delta':
            # 打印云端生成的文字
            content = data.get('delta', '')
            print(f"📝 [云端生成] {content}")
        elif event_type == 'response.audio.transcript.delta':
            # 打印音频对应的字幕
            transcript = data.get('delta', '')
            print(f"🔤 [音频字幕] {transcript}")
        elif event_type == 'error':
            print(f"❌ [服务端报错] {data}")
        elif event_type == 'session.created':
            print(f"✨ [会话创建] ID: {data.get('session', {}).get('id')}")
        else:
            # 其他控制类消息
            print(f"📩 [系统消息] Type: {event_type}")
            
    except Exception as e:
        print(f"⚠️ 解析消息失败: {e}")

def on_error(ws, error):
    print(f"❌ [连接报错] {error}")

def on_close(ws, close_status_code, close_msg):
    global is_running
    is_running = False
    print(f"👋 [连接断开] Code: {close_status_code} | Msg: {close_msg}")

# 模拟麦克风发送静音数据，防止连接被饿死
def keep_alive_audio(ws):
    print("💓 [心跳] 启动虚拟麦克风线程 (发送静音)...")
    # 模拟 24k 采样率的静音包 (PCM16)
    silence_chunk = base64.b64encode(b'\x00' * 2400).decode('utf-8')
    
    while is_running and ws.sock and ws.sock.connected:
        try:
            # 构造音频追加帧
            audio_event = {
                "type": "input_audio_buffer.append",
                "audio": silence_chunk
            }
            ws.send(json.dumps(audio_event))
            time.sleep(0.05) # 模拟真实发送频率
        except Exception:
            break

def on_open(ws):
    print("✅ WebSocket 连接成功！(鉴权通过)")
    
    # 1. 发送标准配置 (Audio + Text)
    config_event = {
        "type": "session.update",
        "session": {
            "modalities": ["audio", "text"], # 关键：必须请求音频
            "instructions": "你是Friday，请简短地用一句话介绍自己。", # 演示用的 Prompt
            "voice": "onyx",
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 200
            }
        }
    }
    ws.send(json.dumps(config_event))
    print("📤 [配置] 发送 Session Update")

    # 2. 启动静音发送线程 (保活关键)
    threading.Thread(target=keep_alive_audio, args=(ws,), daemon=True).start()

    # 3. 发送第一句指令 (模拟用户说话)
    # 这里直接发文本指令，服务端会以“语音+文字”流式返回
    msg_event = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Hello Friday, 我们的连接通了吗？"
                }
            ]
        }
    }
    ws.send(json.dumps(msg_event))
    print("📤 [指令] 发送测试文本: Hello Friday...")
    
    # 4. 触发回复
    ws.send(json.dumps({"type": "response.create"}))
    print("🚀 [触发] 请求云端生成回复 (Response Create)")

if __name__ == "__main__":
    # 检查 Key
    if "你的API_KEY" in API_KEY:
        print("❌ 错误：请先在代码里填入真实的 API_KEY！")
        sys.exit(1)

    token = generate_token(API_KEY)
    
    # 将 Token 放入 Header
    headers = [
        f"Authorization: {token}"
    ]
    
    print(f"🚀 正在连接智谱 Realtime V4: {WS_URL} ...")
    
    # 禁用详细的 debug dump，只看我们自定义的 print
    # websocket.enableTrace(True) 
    
    ws = websocket.WebSocketApp(
        WS_URL,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    ws.run_forever()
