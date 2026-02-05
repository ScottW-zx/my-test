import speech_recognition as sr

print("🔍 正在扫描所有音频设备...")
mics = sr.Microphone.list_microphone_names()

print(f"--------------------------------------------------")
print(f"{'索引 (Index)':<10} | {'设备名称 (Name)'}")
print(f"--------------------------------------------------")

for index, name in enumerate(mics):
    print(f"{index:<10} | {name}")
    
print(f"--------------------------------------------------")
print("💡 请寻找名字里带 'USB PnP' 或 'Webcam' 的设备。")
print("💡 推荐使用 'USB PnP' (如果有的话)，那个通常更清晰。")
