import os

# 智谱 API Key
ZHIPU_API_KEY = "6c2639adffec4a7f9c49d8061a4a32d8.IPnxt39txoRtaJwI"

# 硬件配置
SERIAL_PORT = '/dev/ttyUSB0'
BAUDRATE = 1000000  # ✅ 已确认：您的舵机是 1M 波特率

# 舵机 ID 定义
ID_BASE_YAW   = 1  # 底座旋转
ID_BASE_PITCH = 2  # 底座俯仰
ID_ELBOW      = 3  # 肘部
ID_WRIST_ROLL = 4  # 手腕旋转
ID_HEAD_PITCH = 5  # 头灯俯仰

# 视觉追踪控制轴
ID_PAN = ID_BASE_YAW   # 1
ID_TILT = ID_HEAD_PITCH # 5

# 👇👇👇 您的真实校准数据 (已填入) 👇👇👇
# 开机姿态 (站立/工作)
START_POSE = {
    1: 847,
    2: 1396,
    3: 586,
    4: 4074,
    5: 1583
}

# 关机姿态 (收纳/趴下)
EXIT_POSE = {
    1: 1024,
    2: 895,
    3: 1005,
    4: 4074,
    5: 1807
}

# 运动参数
PAN_DIR = 1    
TILT_DIR = 1   
PID_KP = 0.05
DEADZONE = 5
MAX_SPEED = 60

# 视觉参数
CAMERA_ID = 0
SEARCH_SPEED = 0.5
SEARCH_AMP_PAN = 300
SEARCH_AMP_TILT = 150
SEARCH_TILT_OFFSET = -200
IDLE_TIMEOUT = 5

# 模型文件
DNN_MODEL = "face_detection_yunet_2023mar.onnx"
