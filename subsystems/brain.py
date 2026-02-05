import base64
import datetime
from zhipuai import ZhipuAI
import config
from subsystems.memory import PersistentMemory

class CognitiveSystem:
    def __init__(self):
        print("🧠 大脑模块初始化 (V36 RAG增强版)...")
        try: 
            self.client = ZhipuAI(api_key=config.ZHIPU_API_KEY)
        except: 
            self.client = None
            print("❌ API Key 异常")
        
        self.history = []
        # 🔥 核心升级: 接入持久化记忆库 [cite: 189]
        self.memory = PersistentMemory() 
        
        self.current_location = "未知位置"

    def chat(self, query, vision_context=None):
        if not self.client: return "大脑离线。"
        
        current_vision = f"【视觉情报】: {vision_context}" if vision_context else ""
        
        # 注入记忆上下文到 System Prompt
        rag_context = self.memory.retrieve_context()
        
        sys_prompt = f"""
        你叫 Friday，是钢铁侠的管家。
        当前时间: {datetime.datetime.now().strftime('%H:%M')}
        当前位置: 【{self.current_location}】
        
        {rag_context}
        {current_vision}
        
        【原则】
        1. 极简回答，像Jarvis一样干练。
        2. 如果用户问“我在哪”，请基于位置回答。
        3. 如果视觉情报里出现了【已知物品库】里的东西，请准确叫出它的名字！
        """
        
        if len(self.history) > 6: self.history = self.history[-6:]
        msgs = [{"role": "system", "content": sys_prompt}] + self.history + [{"role": "user", "content": query}]
        
        try:
            tools = [{"type": "web_search", "web_search": {"enable": True}}]
            res = self.client.chat.completions.create(
                model="glm-4-flash", messages=msgs, tools=tools,
                max_tokens=200, temperature=0.7
            )
            reply = res.choices[0].message.content
            self.history.append({"role": "user", "content": query})
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e: 
            print(f"Brain Error: {e}")
            return "思维受阻..."

    def learn_object(self, img_bytes, object_name):
        """
        学习新物品 
        """
        if not img_bytes: return False
        try:
            b64 = base64.b64encode(img_bytes).decode('utf-8')
            # 让大模型提取特征向量（这里用自然语言描述代替向量，适配轻量级架构）
            prompt = f"请仔细观察图片，用简练的语言描述这个'{object_name}'的视觉特征（颜色、形状、材质、Logo等），以便下次我只看描述就能认出它。"
            
            res = self.client.chat.completions.create(
                model="glm-4v", 
                messages=[{"role": "user", "content": [{"type":"text","text": prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}]
            )
            description = res.choices[0].message.content
            print(f"📝 习得特征: {description[:30]}...")
            
            # 存入 RAG 库
            self.memory.memorize(object_name, description)
            return True
        except Exception as e: 
            print(f"Learning Error: {e}")
            return False

    def see(self, img_bytes, prompt="描述画面"):
        """
        视觉分析 + RAG 检索 
        """
        if not img_bytes: return ""
        try:
            b64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # 检索本地记忆，增强 Prompt
            mem_ctx = self.memory.retrieve_context()
            
            final_prompt = f"""
            {prompt}
            
            请结合以下【已知物品库】进行识别。如果画面中的物体符合库中的描述，请直接使用库中的名字（例如“这是主人的水杯”），而不要说“这是一个红色的杯子”。
            
            {mem_ctx}
            """
            
            res = self.client.chat.completions.create(
                model="glm-4v", 
                messages=[{"role": "user", "content": [{"type":"text","text": final_prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}]
            )
            return res.choices[0].message.content
        except: return ""

    def localize(self, img_bytes):
        """视觉定位 (保持不变)"""
        if not img_bytes: return "未知领域"
        try:
            b64 = base64.b64encode(img_bytes).decode('utf-8')
            prompt = "请分析图片，只输出当前房间类型(卧室/办公室/客厅/厨房)。不要输出标点。"
            res = self.client.chat.completions.create(
                model="glm-4v", 
                messages=[{"role": "user", "content": [{"type":"text","text": prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}]
            )
            location = res.choices[0].message.content.strip()
            self.current_location = location
            return location
        except: return "未知位置"
