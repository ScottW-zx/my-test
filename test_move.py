import serial
import time

# ⚙️ 关键设置：STS3215 默认波特率是 1000000
BAUDRATE = 1000000
PORT = '/dev/ttyUSB0'

def checksum(packet):
    sum_val = 0
    for b in packet[2:]:
        sum_val += b
    return (~sum_val) & 0xFF

def write_packet(ser, id, instruction, params):
    length = len(params) + 2
    packet = [0xFF, 0xFF, id, length, instruction] + params
    packet.append(checksum(packet))
    ser.write(bytearray(packet))

def test():
    print(f"🔌 正在打开串口 {PORT} @ {BAUDRATE}...")
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
    except Exception as e:
        print(f"❌ 串口打开失败: {e}")
        return

    print("⚠️ 警告：准备测试 ID 1 (底座)！请确保电源已接好！")
    
    # 1. 发送锁力指令 (Enable Torque)
    # Reg 0x28, Val 1
    print("🔓 发送锁力指令...")
    write_packet(ser, 1, 0x03, [0x28, 1])
    time.sleep(0.1)
    
    # 2. 发送运动指令 (中位 2048)
    # Reg 0x2A, Pos 2048(00 08), Time 0, Speed 1000(E8 03)
    print("🤖 命令 ID 1 归位 (2048)...")
    write_packet(ser, 1, 0x03, [0x2A, 0x00, 0x08, 0xE8, 0x03])
    time.sleep(1)
    
    # 3. 发送运动指令 (转动到 2300)
    print("🤖 命令 ID 1 转动 (2300)...")
    write_packet(ser, 1, 0x03, [0x2A, 0xFC, 0x08, 0xE8, 0x03])
    time.sleep(1)
    
    # 4. 回中
    print("🤖 命令 ID 1 回中...")
    write_packet(ser, 1, 0x03, [0x2A, 0x00, 0x08, 0xE8, 0x03])
    
    ser.close()
    print("✅ 测试结束。")
    print("❓ 结果判定：")
    print("   - 如果舵机动了/变硬了：说明波特率是对的(1M)，只是之前的配置错了。")
    print("   - 如果完全没反应：请检查 12V 供电 和 TX/RX 接线。")

if __name__ == "__main__":
    test()
