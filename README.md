# LeLamp V36 - GLM-4-Voice 智能语音助手

基于智谱AI GLM-4-Voice模型的全双工实时语音交互机器人，具备人脸识别、语音识别、语音合成和动作控制功能。

## 功能特性

- 🗣️ **全双工实时对话**：基于智谱AI GLM-4-Voice模型，支持同时说话和倾听
- 👁️ **人脸识别追踪**：自动识别人脸并跟踪头部运动
- 🤖 **智能动作控制**：支持多种预设动作，如点头、摇头、环视等
- 🎧 **智能唤醒**：支持关键词唤醒（"Friday"或"管家"）
- 📸 **拍照记录**：对话过程中自动拍照记录
- 🌐 **Web界面监控**：通过浏览器实时查看摄像头画面

## 环境需求

### 硬件要求
- 树莓派4B或更高配置
- USB摄像头
- USB麦克风阵列（推荐ReSpeaker系列）
- I2S扬声器或3.5mm耳机输出
- STS3215舵机（用于头部运动）

### 软件依赖
- Python 3.8+
- Pip包管理器
- Git版本控制工具

## 安装配置

### 1. 克隆项目

```bash
git clone <repository-url>
cd lelamp_v2
```

### 2. 安装系统依赖

```bash
# 安装音频相关依赖
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio mpg123 libportaudio2 libportaudiocpp0

# 安装其他依赖
sudo apt-get install ffmpeg libavcodec-extra
```

### 3. 安装Python依赖

```bash
pip install -r requirements.txt
```

如果不存在requirements.txt文件，则手动安装以下包：

```bash
pip install flask pyaudio websockets numpy scipy opencv-python
pip install sherpa-onnx jwt
```

### 4. 配置API密钥

编辑[config.py](file:///root/workspace/LeLamp/lelamp_V5.1.3/config.py)文件，添加智谱AI API密钥：

```python
ZHIPU_API_KEY = "6c2639adffec4a7f9c49d8061a4a32d8.IPnxt39txoRtaJwI"

### 5. 下载语音识别模型

从智谱AI平台下载Paraformer语音识别模型，并放置到`models/sherpa_paraformer`目录下。

或者运行下载脚本（如果存在）：

```bash
python download_model.py
```

### 6. 音频设备校准

运行设备测试脚本确认音频输入输出设备：

```bash
python find_mic_index.py
```

记下麦克风和扬声器的设备索引号，如有需要可在[config.py](file:///root/workspace/LeLamp/lelamp_V5.1.3/config.py)中指定。

## 使用方法

### 启动机器人

```bash
python main.py
```

启动后系统将在终端显示状态信息，并在5000端口启动Web监控界面。

### 唤醒机器人

说出"Friday"或"管家"唤醒机器人，听到"滴"声后可以开始对话。

### Web监控

访问 `http://<raspberry_pi_ip>:5000` 查看实时视频流和系统状态。

## 配置选项

### [config.py](file:///root/workspace/LeLamp/lelamp_V5.1.3/config.py) 文件参数

- `SERIAL_PORT`: 串口设备路径（如'/dev/ttyUSB0'）
- `BAUDRATE`: 波特率设置
- `ID_PAN`, `ID_TILT`: 水平和垂直舵机ID
- `START_POSE`: 启动姿态
- `EXIT_POSE`: 关机姿态
- `ZHIPU_API_KEY`: 智谱AI API密钥

### 系统行为配置

- `SYSTEM_STATUS`: 存储聊天日志和最新照片信息
- `PHOTO_DIR`: 拍照保存目录

## 故障排除

### 音频问题

1. 检查音频设备是否正确连接：
   ```bash
   arecord -l  # 列出录音设备
   aplay -l    # 列出播放设备
   ```

2. 设置默认音频设备（如有需要）：
   ```bash
   alsamixer
   ```

### 摄像头问题

1. 测试摄像头是否正常工作：
   ```bash
   raspistill -o test.jpg
   ```

2. 检查摄像头权限和设置

### 网络问题

1. 确保网络连接正常
2. 检查防火墙设置是否阻止了5000端口
3. 确认智谱AI API密钥有效且网络可达

## 开发说明

### 项目结构

```
lelamp_v2/
├── main.py               # 主程序入口
├── config.py             # 配置文件
├── drivers/              # 硬件驱动
│   └── sts3215.py        # STS3215舵机驱动
├── subsystems/           # 功能模块
│   ├── actions.py        # 动作执行引擎
│   ├── ears.py           # 语音识别监听
│   ├── zhipu_driver.py   # 智谱AI驱动
│   ├── vision.py         # 视觉系统
│   └── ...               # 其他子系统
├── models/               # AI模型文件
│   └── sherpa_paraformer/ # Paraformer语音识别模型
├── static/               # 静态资源
├── templates/            # Web模板
└── README.md             # 本文件
```

### 核心模块

- **ActionEngine**: 实现S-Curve轨迹规划的平滑动作执行
- **ZhipuRealtimeClient**: 智谱AI全双工实时对话客户端
- **Ear**: 本地语音识别，包含语义垃圾过滤功能
- **VisionSystem**: 人脸检测与追踪系统

## 技术细节

### S-Curve轨迹规划

使用S-Curve运动规划算法实现平滑自然的动作过渡，避免突然启停造成的机械冲击。

### 语义垃圾过滤

在[ears.py](file:///root/workspace/LeLamp/lelamp_V5.1.3/subsystems/ears.py)中实现的V33语义垃圾检测算法，有效过滤语音识别中的无效内容。

### 全双工通信

基于WebSocket的实时双向通信，实现真正的全双工对话体验。

## 贡献

欢迎提交Issue和Pull Request帮助改进项目。

## 许可证

本项目遵循MIT许可证，详见[LICENSE](file:///root/workspace/LeLamp/lelamp_V5.1.3/LICENSE)文件。