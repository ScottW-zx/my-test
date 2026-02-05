import time
import sys
import serial
# 尝试引用您的驱动，如果报错则使用通用逻辑
try:
    from drivers.sts3215 import ServoDriver
except:
    print("找不到驱动文件，将使用原生串口扫描...")
    ServoDriver = None

def scan():
    # 常见波特率
    baudrates = [115200, 1000000, 500000, 57600]
    port = '/dev/ttyUSB0'
    
    print(f"⚡ 开始扫描串口: {port}")
    print("注意：请确保舵机已接 12V/7.4V 独立供电，并且开关已打开！")
    
    for baud in baudrates:
        print(f"\n📡 正在尝试波特率: {baud} ...")
        try:
            # 如果能用您的驱动就用，不能就用原生串口 Ping
            if ServoDriver:
                driver = ServoDriver(port, baud)
                found = []
                # 扫描 ID 0 - 20
                for id in range(21):
                    # 尝试读取位置 (Ping)
                    pos = driver.read_pos(id)
                    # 如果读回来的不是 -1 或 0 (且不报错)，说明舵机在线
                    if pos is not None and pos > -1:
                        found.append(f"ID={id} (位置={pos})")
                    # 稍微延时防止堵塞
                    time.sleep(0.01)
                
                if found:
                    print(f"✅ 在 {baud} 波特率下发现舵机: {found}")
                    print("👉 请根据此结果修改 config.py 中的 ID 和 BAUDRATE！")
                    return
                else:
                    print(f"❌ {baud}: 无响应")
                    
        except Exception as e:
            print(f"⚠️ 串口错误: {e}")

    print("\n💀 扫描结束，未发现任何舵机。")
    print("排查建议：")
    print("1. 检查 12V/电池 电源开关是否打开？(USB带不动)")
    print("2. 检查串口线 TX/RX 是否接反？")
    print("3. 舵机线是否松动？")

if __name__ == "__main__":
    scan()
