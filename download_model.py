from modelscope import snapshot_download
import os

# 定义下载目录 (和之前保持一致)
target_dir = "/home/scottwang/lelamp_v2/models/sherpa_paraformer"

print(f"🚀 正在从阿里云魔搭社区下载模型到: {target_dir}")

# 下载 Paraformer 模型
try:
    model_dir = snapshot_download(
        'iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
        cache_dir=target_dir
    )
    print("\n✅ 下载成功！")
    print(f"原始下载路径: {model_dir}")
    
    # 提示用户下一步操作
    print("\n⚠️ 注意：下载的文件在 cache_dir 的子文件夹里，稍后我们需要把它移动出来。")
    
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
