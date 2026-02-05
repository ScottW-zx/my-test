import time
import math
import numpy as np

class MotionPlanner:
    """
    基于 PDF Section 4.3 的 S-Curve (Sigmoid) 平滑运动规划器
    用于生成符合生物运动特征的舵机轨迹，消除机械顿挫感。
    """
    def __init__(self, frequency=50):
        self.freq = frequency # 控制频率 50Hz (20ms周期) [cite: 94]
        self.dt = 1.0 / frequency

    def calculate_sigmoid_trajectory(self, start_pos, end_pos, duration=None, max_velocity=None):
        """
        生成从 start_pos 到 end_pos 的 S 型轨迹点 [cite: 96]
        """
        distance = end_pos - start_pos
        
        # 如果距离极小，直接返回目标点，避免计算开销 [cite: 105]
        if abs(distance) < 0.1:
            yield end_pos
            return

        # 自动计算持续时间
        if duration is None:
            if max_velocity is None:
                max_velocity = 120.0 # 默认最大速度
            # 引入 heuristic: 2.0 是 S 曲线相对于线性运动的时间膨胀系数 [cite: 114]
            duration = (abs(distance) / max_velocity) * 2.0
            duration = max(duration, 0.5) # 最少 0.5 秒，保证动作可见 [cite: 115]

        steps = int(duration * self.freq)
        
        # Sigmoid 核心映射: x 域从 -6 到 6 [cite: 124]
        # 这覆盖了 Logistic 曲线 0.002 到 0.998 的范围，实现“慢进慢出” [cite: 159]
        for step in range(steps + 1):
            progress = step / steps
            x = (progress * 12.0) - 6.0
            
            # Logistic 函数: f(x) = 1 / (1 + e^-x) [cite: 126]
            try:
                sigmoid_factor = 1.0 / (1.0 + math.exp(-x))
            except OverflowError:
                sigmoid_factor = 1.0 if x > 0 else 0.0

            # 映射回角度 [cite: 128]
            current_pos = start_pos + (distance * sigmoid_factor)
            yield current_pos
