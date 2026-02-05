import time
import random
import config
from subsystems.motion_planner import MotionPlanner

class ActionEngine:
    def __init__(self, driver):
        print("🎬 动作引擎初始化 (S-Curve 拟人化版)...")
        self.driver = driver
        self.current_pan = config.START_POSE[config.ID_PAN]
        self.current_tilt = config.START_POSE[config.ID_TILT]
        
        # 初始化 PDF 中提到的运动规划器 [cite: 85]
        self.planner = MotionPlanner(frequency=50)

    def _smooth_move(self, target_pan, target_tilt, duration=None):
        """
        执行符合 S 曲线的平滑运动
        """
        if not self.driver: return

        # 生成两个轴的轨迹生成器
        pan_gen = self.planner.calculate_sigmoid_trajectory(self.current_pan, target_pan, duration)
        tilt_gen = self.planner.calculate_sigmoid_trajectory(self.current_tilt, target_tilt, duration)
        
        # 同步执行 [cite: 145]
        # 使用 zip_longest 确保两个轴都走完，但在 Python 中 zip 也可以，因为 steps 通常一致
        # 为了简单，我们假设 duration 一致，步数一致
        
        start_time = time.time()
        for p, t in zip(pan_gen, tilt_gen):
            try:
                self.driver.write_pos(config.ID_PAN, int(p), 0) # 0 表示速度/时间由我们在外部控制
                self.driver.write_pos(config.ID_TILT, int(t), 0)
                
                self.current_pan = p
                self.current_tilt = t
                
                # 严格控制循环频率 50Hz [cite: 148]
                elapsed = time.time() - start_time
                expected = self.planner.dt
                if elapsed < expected:
                    time.sleep(expected - elapsed)
                start_time = time.time()
            except Exception as e:
                print(f"Servo Error: {e}")
                break
        
        # 确保最终归位
        try:
            self.driver.write_pos(config.ID_PAN, int(target_pan), 0)
            self.driver.write_pos(config.ID_TILT, int(target_tilt), 0)
        except: pass

    def reset(self):
        """回中"""
        self._smooth_move(config.START_POSE[config.ID_PAN], config.START_POSE[config.ID_TILT], 1.0)

    def scan_room(self):
        """开机环视动作"""
        print("👀 动作: 扫描房间 (S曲线)")
        # 依次看左、看右、回中
        pan_center = config.START_POSE[config.ID_PAN]
        tilt_center = config.START_POSE[config.ID_TILT]
        
        self._smooth_move(pan_center - 800, tilt_center, 1.5) # 左
        time.sleep(0.2)
        self._smooth_move(pan_center + 800, tilt_center - 200, 2.0) # 右上
        time.sleep(0.2)
        self._smooth_move(pan_center, tilt_center, 1.5) # 回中

    def scan_table(self):
        """看桌子"""
        pan_center = config.START_POSE[config.ID_PAN]
        self._smooth_move(pan_center, 1600, 1.0) # 假设 1600 是低头看桌子的角度

    def execute(self, action_name):
        """执行预设表情动作"""
        if action_name == "happy":
            # 快乐点头
            base = self.current_tilt
            self._smooth_move(self.current_pan, base - 300, 0.4)
            self._smooth_move(self.current_pan, base + 300, 0.4)
            self._smooth_move(self.current_pan, base, 0.4)
            
    def idle_behavior(self):
        """微动作 (Idling Motion) """
        # 模拟生物呼吸感，进行极其微小的随机运动
        if not self.driver: return
        
        pan_noise = random.randint(-50, 50)
        tilt_noise = random.randint(-50, 50)
        
        target_pan = config.START_POSE[config.ID_PAN] + pan_noise
        target_tilt = config.START_POSE[config.ID_TILT] + tilt_noise
        
        # 极慢速度
        self._smooth_move(target_pan, target_tilt, 2.0)
