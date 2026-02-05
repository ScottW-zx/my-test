import os
import urllib.request
import ssl

# 忽略 SSL 证书验证（防止网络报错）
ssl._create_default_https_context = ssl._create_unverified_context

# 目标路径
target_dir = "/home/scottwang/lelamp_v2/models"
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

save_path = os.path.join(target_dir, "yolov8n.onnx")

# 使用 GitHub Proxy 加速下载 (源文件来自著名的 ibaiGorordo YOLOv8-ONNX 仓库)
# 这是一个标准的、未经修改的 YOLOv8 Nano 模型，完美适配 OpenCV
url = "https://mirror.ghproxy.com/https://github.com/ibaiGorordo/ONNX-YOLOv8-Object-Detection/raw/main/models/yolov8n.onnx"

print(f"🚀 正在通过加速通道下载 YOLOv8n 模型...")
print(f"源地址: {url}")
print(f"目标位置: {save_path}")

try:
    # 添加 User-Agent 防止被拦截
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    
    urllib.request.urlretrieve(url, save_path)
    
    file_size = os.path.getsize(save_path) / 1024 / 1024
    if file_size < 1:
        print("❌ 下载文件过小，可能下载失败，请检查网络。")
    else:
        print(f"✅ 下载成功！")
        print(f"文件大小: {file_size:.2f} MB")
        
except Exception as e:
    print(f"❌ 下载失败: {e}")
    print("\n💡 备选方案: ")
    print("如果在树莓派上实在下载不下来，请在电脑上下载这个链接：")
    print("https://github.com/ibaiGorordo/ONNX-YOLOv8-Object-Detection/raw/main/models/yolov8n.onnx")
    print("然后用 MobaXterm 拖进 lelamp_v2/models/ 文件夹。")
