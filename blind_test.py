import time
import serial

# 专门针对 STS3215 的盲发测试
def blind_move():
    # 两个最可能的波特率
    bauds = [1000000, 115200]
    ids_to_test = [1, 2, 3, 4, 5] # 根据您的表格测试所有ID
    
    port = '/dev/ttyUSB0'
    
    print(f"⚡ 开始盲动测试：{port}")
    print("⚠️ 注意：如果舵机动了，请立即记下是哪个波特率！")

    for bd in bauds:
        print(f"\n📡 正在尝试波特率: {bd} ...")
        try:
            ser = serial.Serial(port, bd, timeout=0.1)
        except:
            print("❌ 串口打开失败")
            continue
            
        # 尝试让 ID 1-5 动一下
        for id in ids_to_test:
            print(f"   👉 正在命令 ID {id} 归位 (2048)...")
            # 构造 STS 写入指令 (位置 2048, 速度 1000)
            # FF FF ID 07 03 2A 00 08 E8 03 CK
            pos = 2048
            spd = 1000
            
            pL = pos & 0xFF
            pH = (pos >> 8) & 0xFF
            sL = spd & 0xFF
            sH = (spd >> 8) & 0xFF
            
            # 校验和
            checksum = (~(id + 7 + 3 + 0x2A + pL + pH + sL + sH)) & 0xFF
            packet = [0xFF, 0xFF, id, 0x07, 0x03, 0x2A, pL, pH, sL, sH, checksum]
            
            ser.write(bytearray(packet))
            time.sleep(0.1)
            
            # 稍微动一点点 (2200) 看有没有反应
            print(f"   👉 正在命令 ID {id} 转动 (2200)...")
            pos = 2200
            pL = pos & 0xFF
            pH = (pos >> 8) & 0xFF
            checksum = (~(id + 7 + 3 + 0x2A + pL + pH + sL + sH)) & 0xFF
            packet = [0xFF, 0xFF, id, 0x07, 0x03, 0x2A, pL, pH, sL, sH, checksum]
            
            ser.write(bytearray(packet))
            time.sleep(0.5)
            
        ser.close()
        print(f"--- 波特率 {bd} 测试结束 ---")
        time.sleep(1)

if __name__ == "__main__":
    blind_move()
