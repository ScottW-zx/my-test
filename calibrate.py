import time
import sys
from drivers.sts3215 import ServoDriver
import config

def main():
    # 1. 连接舵机 (使用 config 中的配置)
    print(f"🔌 正在连接串口 {config.SERIAL_PORT} @ {config.BAUDRATE}...")
    try:
        driver = ServoDriver(config.SERIAL_PORT, config.BAUDRATE)
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    # 舵机 ID 列表 (根据您的 5 轴配置)
    ids = [1, 2, 3, 4, 5]

    print("\n" + "="*40)
    print("      🤖 LELAMP 姿态校准向导      ")
    print("="*40)
    print("在这个模式下，舵机会'卸力'（变软）。")
    print("请按照提示用手摆弄机器人，我们将记录数值。")
    print("="*40)

    input("\n👉 按 [回车键] 开始卸力，请扶好机器人防止摔倒！")

    # 2. 全身卸力 (Torque Off)
    print("🔓 正在卸力...")
    for i in ids:
        driver.enable_torque(i, 0) # 0 = 放松
        time.sleep(0.05)
    print("✅ 舵机已放松，您现在可以动手调节了。")

    # --- 校准站立姿态 ---
    print("\n" + "-"*30)
    print("【第一步：校准 站立/工作 姿态】")
    print("请用手将机器人摆成您认为最完美的【正视前方】姿态。")
    print("注意检查：头是否正？身体是否直？")
    input("👉 摆好后，请按 [回车键] 读取数值...")

    start_pose = {}
    print("📏 正在读取...")
    for i in ids:
        pos = driver.read_pos(i)
        if pos == -1:
            print(f"⚠️ 无法读取 ID {i}，请检查线缆！")
            pos = 2048 # 默认值兜底
        print(f"   ID {i}: {pos}")
        start_pose[i] = pos

    # --- 校准趴下姿态 ---
    print("\n" + "-"*30)
    print("【第二步：校准 趴下/关机 姿态】")
    print("请用手将机器人摆成您想要的【关机收纳】姿态（通常是低头折叠）。")
    input("👉 摆好后，请按 [回车键] 读取数值...")

    exit_pose = {}
    print("📏 正在读取...")
    for i in ids:
        pos = driver.read_pos(i)
        if pos == -1: pos = 2048
        print(f"   ID {i}: {pos}")
        exit_pose[i] = pos

    # 3. 恢复锁力 (Torque On)
    print("\n🔐 校准完成，正在重新锁死舵机...")
    for i in ids:
        driver.enable_torque(i, 1)
        time.sleep(0.05)

    # 4. 生成配置代码
    print("\n" + "="*40)
    print("🎉 校准成功！请复制下面的代码覆盖 config.py 中的对应部分：")
    print("="*40)
    
    print("\n# 复制这部分到 config.py:")
    print("-" * 20)
    print("START_POSE = {")
    for i in ids:
        print(f"    {i}: {start_pose[i]},")
    print("}")
    
    print("\nEXIT_POSE = {")
    for i in ids:
        print(f"    {i}: {exit_pose[i]},")
    print("}")
    print("-" * 20)

if __name__ == "__main__":
    main()
