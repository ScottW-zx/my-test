import json
import os
import time
from datetime import datetime

class PersistentMemory:
    """
    基于 PDF Section 5.3 的用户个性化库 (RAG 轻量版)
    负责将用户的教学内容持久化到本地存储，并在识别时检索。
    """
    def __init__(self, db_path="static/memory.json"):
        self.db_path = db_path
        self.memories = {} # { "物体名": { "desc": "特征描述", "time": "时间" } }
        self.load()

    def load(self):
        """从磁盘加载记忆"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.memories = json.load(f)
                print(f"🧠 [Memory] 已加载 {len(self.memories)} 条长期记忆")
            except Exception as e:
                print(f"⚠️ [Memory] 加载失败: {e}")
                self.memories = {}
        else:
            print("🧠 [Memory] 初始化新记忆库")

    def save(self):
        """持久化到磁盘"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
            # print("💾 [Memory] 记忆已固化")
        except Exception as e:
            print(f"❌ [Memory] 保存失败: {e}")

    def memorize(self, name, description):
        """
        写入记忆 [cite: 191]
        用户: "这是我的新水杯" -> 系统存入特征
        """
        self.memories[name] = {
            "description": description,
            "timestamp": int(time.time()),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.save() # 立即保存
        return True

    def retrieve_context(self):
        """
        检索上下文 
        将本地记忆转化为 Prompt 上下文，辅助大模型进行 Grounding
        """
        if not self.memories:
            return "【已知物品库】: (空)"
        
        # 构建 RAG 上下文块
        context = "【已知物品库 (用户教过的内容)】:\n"
        for name, data in self.memories.items():
            context += f"- {name}: {data['description']}\n"
        
        return context

    def forget(self, name):
        """遗忘指定物品"""
        if name in self.memories:
            del self.memories[name]
            self.save()
            return True
        return False
