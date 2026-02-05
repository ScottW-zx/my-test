#!/bin/bash
# 开启硬件噪声门 (Noise Gate) - 消除底噪
amixer -c 1 cset name='Noise Gate Switch' on
amixer -c 1 cset name='Noise Gate Threshold' 14  # 阈值 14 (-58.5dB)

# 开启 ALC (自动电平控制) - 增强远场拾音
amixer -c 1 cset name='ALC Function' 3       # 立体声模式
amixer -c 1 cset name='ALC Target' 11        # 目标电平 -12dB
amixer -c 1 cset name='ALC Max Gain' 5       # 最大增益 +24dB
amixer -c 1 cset name='ALC Attack' 2
amixer -c 1 cset name='ALC Decay' 3

echo "✅ WM8960 声学参数优化完成"
